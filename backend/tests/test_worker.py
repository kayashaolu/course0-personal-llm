"""worker.py: run_once() claims a queued job, dispatches it by kind, and
always leaves the row in a terminal state, never stuck at 'running', whether
the handler succeeds, raises, or the kind has no handler registered at all.
"""
import pytest

from db import job
import worker


@pytest.fixture(autouse=True)
def restore_handlers():
    """Every test below replaces worker.HANDLERS; put the real dict back."""
    original = dict(worker.HANDLERS)
    yield
    worker.HANDLERS.clear()
    worker.HANDLERS.update(original)


def test_run_once_returns_false_when_the_queue_is_empty():
    assert worker.run_once("worker-a") is False


def test_run_once_runs_a_queued_jobs_handler_exactly_once_and_marks_it_done(monkeypatch):
    calls = []

    def fake_handler(current_job):
        calls.append(current_job.id)

    monkeypatch.setitem(worker.HANDLERS, "pull_model", fake_handler)
    created = job.create("pull_model", "gemma3:270m")

    ran = worker.run_once("worker-a")

    assert ran is True
    assert calls == [created.id]  # handler ran exactly once, on the right job
    finished = job.get(created.id)
    assert finished.status == "done"
    assert finished.progress == 100
    assert finished.owner == "worker-a"  # set by claim()
    assert finished.updated_at > created.updated_at  # claim() and finish() both stamped it

    # nothing left queued: a second call is a no-op, not a re-run
    assert worker.run_once("worker-a") is False


def test_run_once_catches_a_raising_handler_writes_failed_and_does_not_propagate(monkeypatch):
    def broken_handler(current_job):
        raise RuntimeError("model not found")

    monkeypatch.setitem(worker.HANDLERS, "pull_model", broken_handler)
    created = job.create("pull_model", "does-not-exist")

    ran = worker.run_once("worker-a")  # must not raise

    assert ran is True
    failed = job.get(created.id)
    assert failed.status == "failed"
    assert failed.error == "model not found"
    assert failed.status != "running"  # never left stuck mid-job
    # the loop keeps going afterward: no exception escaped into the caller
    assert worker.run_once("worker-a") is False


def test_run_once_fails_an_unregistered_kind_without_raising_or_stalling():
    created = job.create("mystery_kind", "payload")

    ran = worker.run_once("worker-a")  # no handler for "mystery_kind"; must not raise

    assert ran is True
    failed = job.get(created.id)
    assert failed.status == "failed"
    assert "mystery_kind" in failed.error
    # loop keeps running afterward: the unregistered kind did not escape the loop
    assert worker.run_once("worker-a") is False


def test_run_once_finds_nothing_when_the_job_was_already_claimed_before_it_looked():
    created = job.create("pull_model", "gemma3:270m")
    job.claim(created.id, "some-other-worker")  # already claimed before this worker looks

    ran = worker.run_once("worker-a")

    assert ran is False
    assert job.get(created.id).owner == "some-other-worker"


def test_run_once_does_not_rerun_a_job_another_owner_claims_in_the_race_window(monkeypatch):
    """Exercises the claim() == False branch directly: a job is still queued
    when next_queued() looks, but claim() loses (another owner won between
    the two calls). Without this, next_queued() finding nothing (the case
    above) is the only path ever reached, and the real race branch at
    worker.py's `if not job.claim(...)` has no coverage at all.
    """
    monkeypatch.setattr(worker.job, "claim", lambda job_id, owner: False)
    called = []
    monkeypatch.setitem(worker.HANDLERS, "pull_model", lambda current_job: called.append(current_job.id))
    created = job.create("pull_model", "gemma3:270m")

    ran = worker.run_once("worker-a")

    assert ran is False
    assert called == []  # the handler must never run for a job this worker didn't win
    assert job.get(created.id).status == "queued"  # row untouched by the loser


def test_run_stops_as_soon_as_should_stop_returns_true(monkeypatch):
    monkeypatch.setitem(worker.HANDLERS, "pull_model", lambda current_job: None)
    job.create("pull_model", "gemma3:270m")
    iterations = {"n": 0}

    def should_stop():
        iterations["n"] += 1
        return iterations["n"] > 1  # let run_once() fire once, then stop before the next poll

    worker.run("worker-a", poll_interval=0, should_stop=should_stop)

    assert job.list()[0].status == "done"
    assert iterations["n"] == 2  # loop exited on the second check, not a hang
