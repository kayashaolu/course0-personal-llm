"""Background worker: polls the jobs table and drives each job's handler.

Runs as its own OS process, separate from the Eel backend (`main.py`). Start
it alongside `npm run start`, in a second terminal, with `npm run worker`.
It's a separate process (not a thread or greenlet inside the app) so a long
job -- e.g. a multi-minute model pull -- can never block the app's own
event loop from serving requests.
"""
import logging
import os
import signal
import time

from db import job
from db.utils import setup as db_setup

logger = logging.getLogger(__name__)

# time.sleep() does NOT return early when a signal arrives mid-sleep: PEP 475
# has CPython retry the sleep with the recomputed remaining delay as long as
# the handler doesn't raise, so a flag-setting handler like request_stop()
# below has no effect on an in-progress sleep. Measured on this box: a SIGINT
# delivered 0.50s into a `time.sleep(3)` call still returns right at 3.00s.
# Consequence: after Ctrl-C, the loop doesn't notice should_stop() until the
# current sleep finishes, so shutdown can lag by up to one full poll
# interval. POLL_INTERVAL_SECONDS is kept short (1s) specifically to bound
# that latency.
POLL_INTERVAL_SECONDS = 1

_stop_requested = False


def pull_model(current_job):
    """Handler for the "pull_model" job kind.

    TODO: not implemented in this skeleton. This is the seam Challenge 3
    asks you to fill in: call ollama.pull(current_job.payload, stream=True),
    and write progress back onto the row as each streamed chunk arrives with
    job.set_progress(current_job.id, progress), so the CAS in job.claim(...)
    is still the only thing that ever puts a row into 'running'.
    """
    raise NotImplementedError("pull_model is not implemented yet")


# Job.kind -> handler function. Add an entry here for each new kind of job
# the app needs to run in the background. A kind with no entry fails the job
# with a clear error instead of crashing the worker process (see run_once
# below).
HANDLERS = {
    "pull_model": pull_model,
}


def request_stop(*_signal_args):
    """SIGINT handler: sets a flag the loop checks between iterations. Does
    not interrupt a job handler already running -- a long handler (e.g. a
    290MB ollama.pull) can make the first Ctrl-C look like nothing happened.

    On a second SIGINT, restore the default handler and re-raise so it fires
    immediately -- the first press is graceful, the second always works even
    while a handler is running.
    """
    global _stop_requested
    if _stop_requested:
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        os.kill(os.getpid(), signal.SIGINT)
        return
    _stop_requested = True


def run_once(owner):
    """Claim and run at most one queued job.

    Returns True if a job was claimed and run (regardless of whether it
    ended in 'done' or 'failed'), False if there was nothing to do.
    """
    next_job = job.next_queued()
    if next_job is None:
        return False

    if not job.claim(next_job.id, owner):
        # Another worker claimed it between next_queued() and claim(). Not
        # an error: just try again next iteration.
        return False

    try:
        handler = HANDLERS.get(next_job.kind)
        if handler is None:
            raise ValueError(f"no handler registered for job kind {next_job.kind!r}")
        # Re-read after the claim wins: next_job is a pre-claim snapshot
        # (status='queued', owner=None). Handing that stale object to the
        # handler would make the CAS's effect invisible to it.
        current_job = job.get(next_job.id)
        handler(current_job)
        job.finish(next_job.id)
    except Exception as error:
        # Whatever went wrong (an unregistered kind, ollama unreachable, the
        # NotImplementedError above), the row must not stay at 'running'
        # forever: write the failure and move on, rather than letting the
        # exception kill the process and strand the row.
        logger.exception("job %s (kind=%s) failed", next_job.id, next_job.kind)
        job.fail(next_job.id, str(error))

    return True


def run(owner, poll_interval=POLL_INTERVAL_SECONDS, should_stop=lambda: _stop_requested):
    """Poll for queued jobs until should_stop() returns True.

    should_stop is an injectable seam: production code leaves it as the
    module-level SIGINT flag; tests pass their own callable so they can stop
    the loop deterministically after a fixed number of iterations, with no
    real signal and no reliance on wall-clock timing.
    """
    logger.info("worker %s started, polling every %s second(s)", owner, poll_interval)
    while not should_stop():
        ran = run_once(owner)
        if not ran:
            time.sleep(poll_interval)
    logger.info("worker %s stopped", owner)


def main():
    logging.basicConfig(level=logging.INFO)
    logger.info("setting up the database")
    db_setup()

    owner = f"worker-{os.getpid()}"
    signal.signal(signal.SIGINT, request_stop)
    run(owner)


if __name__ == "__main__":
    main()
