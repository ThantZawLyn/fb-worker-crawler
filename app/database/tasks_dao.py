from datetime import datetime

from . import DBSession
from .. import logger
from .models import TaskKeyword, TaskSource, TaskStatus
from .worker_credentials_dao import complete_working_credentials_task


def get_task_keyword(task_id):
    task_keyword = DBSession.query(TaskKeyword).filter(TaskKeyword.task_id == task_id).first()
    if task_keyword is None:
        logger.log("Task with id={} not found".format(task_id))
        return False
    return task_keyword


def get_task_source(task_id):
    task_source = DBSession.query(TaskSource).filter(TaskSource.task_id == task_id).first()
    if task_source is None:
        logger.log("Task with id={} not found".format(task_id))
        return False
    return task_source


def complete_task(credentials, main_task):
    logger.log("complete task {}".format(main_task.id))
    main_task.task.status = TaskStatus.success
    main_task.task.enabled = True
    main_task.task.finish_time = datetime.now().isoformat()
    complete_working_credentials_task(credentials.id, main_task.task_id)
    DBSession.commit()


def fail_task(credentials, main_task):
    logger.log("fail task {}".format(main_task.id))
    # TODO: при любой ошибке задаче присваивается статус success
    main_task.task.status = TaskStatus.success
    main_task.task.finish_time = datetime.now().isoformat()
    complete_working_credentials_task(credentials.id, main_task.task_id)
    DBSession.commit()


def start_task(task):
    logger.log("start task {} ".format(task.id))
    task.received_time = datetime.now().isoformat()
    task.status = TaskStatus.in_progress
    DBSession.commit()


def back_to_queue_task(main_task):
    logger.log("send task {} back to queue".format(main_task.id))
    main_task.task.status = TaskStatus.retry
    main_task.task.received_time = datetime.now().isoformat()
    DBSession.commit()
