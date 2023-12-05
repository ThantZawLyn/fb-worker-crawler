from datetime import datetime

from . import DBSession
from .. import logger
from ..database.subtasks_dao import save_subtasks
from .models import Post, All_content


# TODO remove
def save_posts(browser, posts, task_type, parse_post):
    logger.log("There are {} posts are found".format(len(posts)))
    index = 1
    task_id = task_type.task.id
    for post in posts:
        logger.log("Post process {} of {}".format(index, len(posts)))
        index += 1
        post_obj = parse_post(browser, post)
        post_obj.task_id = task_id
        if has_exits(post_obj):
            logger.log("Post has already added, skip")
        else:
            DBSession.add(post_obj)
            save_subtasks(post_obj)
            DBSession.commit()


def get_post_by_fb_id(fb_post_id):
    return DBSession.query(Post).filter(Post.fb_post_id == fb_post_id).first()


def update_post_stat(post_obj, stat):
    if post_obj.id:
        if post_obj.stat and stat:
            if post_obj.stat.is_equals(stat):
                logger.log("Post has already added, no update required")
            else:
                logger.log("Update existed post: {}".format(post_obj.fb_post_id))
                DBSession.delete(post_obj.stat)
                post_obj.stat = stat
                post_obj.last_time_updated = datetime.now().isoformat()
                DBSession.commit()
                # TODO start subtasks
def update_task_id(fb_post_id, task_id):
    id_update = DBSession.query(Post).filter(Post.fb_post_id == fb_post_id).first()
    id_update.task_id = task_id
    logger.log("Updated task_id {}".format(task_id))
    DBSession.commit()

def save_post(post_obj):
    try:
        logger.log("Save post fb_post_id: {}.".format(post_obj.fb_post_id))
        if not post_obj.id:
            logger.log("Save post fb_post_date: {}.".format(post_obj.date))
            DBSession.add(post_obj)
            save_subtasks(post_obj)
            DBSession.commit()
            add_id = All_content(content_id = post_obj.content_id, network_id =1) 
            DBSession.add(add_id)
            DBSession.commit() 
    except Exception as e:
        logger.exception("Couldn't save or update post: {}".format(post_obj.fb_post_id), e)


def has_exits(post):
    if post.fb_post_id is None:
        return False
    return DBSession.query(Post).filter(Post.fb_post_id == post.fb_post_id).first()
