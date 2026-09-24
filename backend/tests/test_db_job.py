"""db/job.py: create / claim / progress / finish / fail against a temporary database.

updated_at only moves on INSERT by default on the pinned peewee version (no
auto_now), so every mutation below is also the regression test that each one
stamps it explicitly: this must fail if that stamp is ever dropped.
"""
import datetime
import time

from db import job


def test_create_returns_a_queued_job_with_zero_progress():
    created = job.create("pull_model", "gemma3:270m")

    assert created.id is not None
    assert created.kind == "pull_model"
    assert created.payload == "gemma3:270m"
    assert created.status == "queued"
    assert created.progress == 0
    assert created.owner is None
    assert created.error is None
    assert isinstance(created.created_at, datetime.datetime)
    assert isinstance(created.updated_at, datetime.datetime)


def test_get_returns_none_for_unknown_id():
    assert job.get(9999) is None


def test_list_returns_every_job():
    job.create("pull_model", "a")
    job.create("pull_model", "b")

    assert [j.payload for j in job.list()] == ["a", "b"]


def test_next_queued_returns_the_oldest_queued_job():
    job.create("pull_model", "first")
    job.create("pull_model", "second")

    assert job.next_queued().payload == "first"


def test_next_queued_ignores_jobs_that_are_not_queued():
    created = job.create("pull_model", "only one")
    job.claim(created.id, "worker-a")

    assert job.next_queued() is None


def test_next_queued_returns_none_on_an_empty_table():
    assert job.next_queued() is None


def test_claim_wins_once_and_loses_the_second_time():
    created = job.create("pull_model", "gemma3:270m")

    won = job.claim(created.id, "worker-a")
    lost = job.claim(created.id, "worker-b")

    assert won is True
    assert lost is False
    claimed = job.get(created.id)
    assert claimed.status == "running"
    assert claimed.owner == "worker-a"  # the loser never overwrote the winner's owner


def test_claim_returns_false_for_a_job_that_does_not_exist():
    assert job.claim(9999, "worker-a") is False


def test_claim_moves_updated_at_strictly_forward():
    created = job.create("pull_model", "gemma3:270m")
    time.sleep(0.01)

    job.claim(created.id, "worker-a")

    assert job.get(created.id).updated_at > created.updated_at


def test_set_progress_updates_progress_and_moves_updated_at_forward():
    created = job.create("pull_model", "gemma3:270m")
    job.claim(created.id, "worker-a")
    before = job.get(created.id).updated_at
    time.sleep(0.01)

    job.set_progress(created.id, 42)

    updated = job.get(created.id)
    assert updated.progress == 42
    assert updated.updated_at > before


def test_finish_marks_the_job_done_at_full_progress_and_moves_updated_at_forward():
    created = job.create("pull_model", "gemma3:270m")
    job.claim(created.id, "worker-a")
    before = job.get(created.id).updated_at
    time.sleep(0.01)

    job.finish(created.id)

    finished = job.get(created.id)
    assert finished.status == "done"
    assert finished.progress == 100
    assert finished.updated_at > before


def test_fail_records_the_error_and_moves_updated_at_forward():
    created = job.create("pull_model", "gemma3:270m")
    job.claim(created.id, "worker-a")
    before = job.get(created.id).updated_at
    time.sleep(0.01)

    job.fail(created.id, "connection refused")

    failed = job.get(created.id)
    assert failed.status == "failed"
    assert failed.error == "connection refused"
    assert failed.updated_at > before


def test_to_front_end_shape():
    created = job.create("pull_model", "gemma3:270m")

    data = created.toFrontEnd()

    assert set(data) == {
        "id", "kind", "payload", "status", "progress", "owner", "error",
        "created_at", "updated_at",
    }
    assert data["kind"] == "pull_model"
    assert data["payload"] == "gemma3:270m"
    assert data["status"] == "queued"
    assert data["progress"] == 0
    assert data["owner"] is None
    assert data["error"] is None
    # created_at/updated_at are sent to the browser as ISO-8601 strings
    assert datetime.datetime.fromisoformat(data["created_at"]) == created.created_at
    assert datetime.datetime.fromisoformat(data["updated_at"]) == created.updated_at
