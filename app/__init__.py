from celery import Celery
from .constants import CELERY_QUEUE_NAME, CELERY_BROKER_URL, CELERY_BACKEND
from .utils.logging import Log

app = Celery(
    CELERY_QUEUE_NAME,
    broker=CELERY_BROKER_URL,
    backend=CELERY_BACKEND
)
app.conf.task_routes = ([('task.*', {'queue': 'tasks'}), ('sub_task.*', {'queue': 'sub_tasks'})],)

logger = Log()

from . import worker

