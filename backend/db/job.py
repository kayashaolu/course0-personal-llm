from peewee import CharField, AutoField, DateTimeField, IntegerField, Model
import logging
import datetime
from db import db_instance

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())

# Table Schema
class Job(Model):
    id = AutoField()
    kind = CharField()                       # e.g. "pull_model"
    payload = CharField()                    # model name to pull
    status = CharField(default='queued')     # queued | running | done | failed
    progress = IntegerField(default=0)       # 0-100 percent complete
    owner = CharField(null=True)             # which worker holds it
    error = CharField(null=True)
    created_at = DateTimeField(default=datetime.datetime.now)
    updated_at = DateTimeField(default=datetime.datetime.now)  # every write below stamps this explicitly; see note under Database Operations

    class Meta:
        database = db_instance

# Table Object
class JobObj():
    def __init__(self, job):
        self.id = job.id
        self.kind = job.kind
        self.payload = job.payload
        self.status = job.status
        self.progress = job.progress
        self.owner = job.owner
        self.error = job.error
        self.created_at = job.created_at
        self.updated_at = job.updated_at

    def toFrontEnd(self):
        return {
            'id': self.id,
            'kind': self.kind,
            'payload': self.payload,
            'status': self.status,
            'progress': self.progress,
            'owner': self.owner,
            'error': self.error,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

# Database Operations
#
# Peewee's `default=` (used on created_at/updated_at above) only fires on
# INSERT, not on UPDATE -- there is no auto_now on the pinned peewee version.
# So every mutation below stamps updated_at explicitly, inside the same
# statement as the rest of its write, rather than relying on the column to
# move itself. This module is the only place that writes a Job: nothing
# outside this file should call Job.update(...) or Job.create(...) directly,
# the same way db/chat.py and db/message.py are the only writers of their
# tables.

def create(kind, payload):
    job = Job.create(kind=kind, payload=payload)
    return JobObj(job)

def get(job_id):
    job = Job.get_or_none(Job.id == job_id)

    if job is None:
        return None

    return JobObj(job)

def list():
    jobs = Job.select()
    return [JobObj(job) for job in jobs]

def next_queued():
    job = Job.select().where(Job.status == 'queued').order_by(Job.created_at).first()

    if job is None:
        return None

    return JobObj(job)

def claim(job_id, owner):
    """Compare-and-swap: only succeeds if the job is still queued. Returns
    True if this call won the claim, False if someone else already had it
    (or the job doesn't exist). The WHERE clause checks status == 'queued'
    in the same statement that sets it to 'running', so the whole
    check-and-set is a single UPDATE the database executes atomically --
    two workers racing to claim the same row can never both win.
    """
    updated = (Job.update(status='running', owner=owner, updated_at=datetime.datetime.now())
                  .where((Job.id == job_id) & (Job.status == 'queued'))
                  .execute())
    return updated == 1

def set_progress(job_id, progress):
    Job.update(progress=progress, updated_at=datetime.datetime.now()).where(Job.id == job_id).execute()

def finish(job_id):
    Job.update(status='done', progress=100, updated_at=datetime.datetime.now()).where(Job.id == job_id).execute()

def fail(job_id, error):
    Job.update(status='failed', error=error, updated_at=datetime.datetime.now()).where(Job.id == job_id).execute()
