from datetime import datetime

from .. import logger
from ..database import DBSession
from ..database.models import (Post, Subtask, SubtaskPersonalData, SubtaskType,
                               TaskStatus)
from .worker_credentials_dao import complete_working_credentials_task


def save_subtasks(post_obj):
    subtasks = []
    if post_obj.stat.likes:
        likes_subtask = Subtask(post=post_obj, subtask_type=SubtaskType.like)
        DBSession.add(likes_subtask)
        subtasks.append(likes_subtask)

    if post_obj.stat.comments:
        comments_subtask = Subtask(post=post_obj, subtask_type=SubtaskType.comment)
        DBSession.add(comments_subtask)
        subtasks.append(comments_subtask)

    if post_obj.stat.shares:
        shares_subtask = Subtask(post=post_obj, subtask_type=SubtaskType.share)
        DBSession.add(shares_subtask)
        subtasks.append(shares_subtask)

    if post_obj.user and not post_obj.user.id:
        subtasks.append(save_personal_page_subtask(post_obj, post_obj.user))

    logger.log("{} subtasks has saved".format(str(len(subtasks))))
    return subtasks


def save_personal_page_subtask(post, user):
    personal_page_subtask = Subtask(post=post, subtask_type=SubtaskType.personal_page)
    subtask_personal_data = SubtaskPersonalData(user=user, subtask=personal_page_subtask)
    DBSession.add(subtask_personal_data)
    DBSession.add(personal_page_subtask)
    return personal_page_subtask


def get_subtasks(subtask):
    return DBSession.query(Subtask). \
        join(Post, Post.id == Subtask.post_id). \
        filter(Post.task_id == subtask.post.task_id).all()


def get_subtask(subtask_id):
    return DBSession.query(Subtask).filter(Subtask.id == subtask_id).first()


def get_personal_data_subtask(subtask_id):
    return DBSession.query(SubtaskPersonalData).filter(SubtaskPersonalData.subtask_id == subtask_id).first()


def complete_subtask_personal_data(credentials, subtask_personal_data):
    complete_subtask(credentials, subtask_personal_data.subtask)


def fail_subtask_personal_data(credentials, subtask_personal_data):
    fail_subtask(credentials, subtask_personal_data.subtask)


def complete_subtask(credentials, subtask):
    logger.log("complete subtask {}".format(subtask.id))
    subtask.end_time = datetime.now().isoformat()
    subtask.status = TaskStatus.success
    complete_working_credentials_task(credentials.id, subtask.id)
    DBSession.commit()


def fail_subtask(credentials, subtask):
    logger.log("fail subtask {}".format(subtask.id))
    subtask.end_time = datetime.now().isoformat()
    # TODO: при любой ошибке задаче присваивается статус success
    subtask.status = TaskStatus.success
    complete_working_credentials_task(credentials.id, subtask.id)
    DBSession.commit()


def start_subtask(subtask):
    logger.log("start subtask {} ".format(subtask.id))
    subtask.start_time = datetime.now().isoformat()
    subtask.status = TaskStatus.in_progress
    DBSession.commit()


def back_to_queue_subtask(subtask):
    logger.log("send subtask {} back to queue".format(subtask.id))
    subtask.end_time = datetime.now().isoformat()
    subtask.status = TaskStatus.retry
    DBSession.commit()
