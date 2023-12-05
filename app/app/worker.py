import traceback
from random import randint

from . import app, logger
from .authentication.authentication import is_proxy_available, open_fb
from .authentication.browser import browser_service
from .authentication.proxy import close_proxy_url
from .constants import *
from .database import DBSession
from .database.models import SubtaskType, TaskType
from .database.subtasks_dao import (back_to_queue_subtask, complete_subtask,
                                    complete_subtask_personal_data,
                                    fail_subtask, fail_subtask_personal_data,
                                    get_personal_data_subtask, get_subtask,
                                    start_subtask)
from .database.tasks_dao import (back_to_queue_task, complete_task, fail_task,
                                 get_task_keyword, get_task_source, start_task)
from .database.worker_credentials_dao import (add_working_credentials_task,
                                              create_working_credentials,
                                              enable_proxy, enable_wc_by_proxy,
                                              get_credentials, get_proxy,
                                              set_started)
from .parsing.comments_parsing import parse_comments
from .parsing.keyword_parsing import parse_keyword
from .parsing.likes_parsing import parse_likes
from .parsing.personal_page_parsing import parse_personal_page
from .parsing.shares_parsing import parse_shares
from .parsing.source_parsing import parse_source


@app.task(name=TASK_RE_ENABLE_ALL_DISABLED_PROXY)
def proxy_re_enabled(proxy_id):
    logger.log("Proxy {} re enable received".format(proxy_id))
    proxy = get_proxy(proxy_id)
    browser, proxy_url = browser_service.open_by_proxy(proxy)
    if not browser and not proxy_url:
        return False

    try:
        if is_proxy_available(browser):
            enable_proxy(proxy)
            enable_wc_by_proxy(proxy)
        else:
            logger.log("Proxy {} has not enabled".format(proxy.id))
    except Exception as e:
        logger.exception("Proxy re enable has finished with errors", e)
        return
    finally:
        close_proxy_url(proxy_url)

    logger.log("Proxy re enabling finished")


@app.task(name=TASK_RE_LOGIN_ALL_DISABLED_ACCOUNTS)
def accounts_relogin():
    logger.log("Account relogin received")
    # todo сделать логин без компромата


@app.task(name=TASK_WARM_ACCOUNT)
def account_warming():
    logger.log("Account warming received")
    credentials = create_working_credentials()
    if credentials is None:
        logger.log("All accounts are busy")
        return

    set_started(credentials)
    browser, proxy_url = browser_service.open(credentials)
    if not browser and not proxy_url:
        return False

    try:
        logger.log_alive()
        open_fb(browser, credentials)
    except:
        logger.log("Account warming has finished with errors")
        traceback.print_exc()
        DBSession.rollback()
    finally:
        browser_service.close()

    logger.log("Account warming finished")


@app.task(name=TASK_SOURCE_ID)
def source_task(task_id):
    print("Source task received: id={}".format(task_id))
    logger.clean()

    def get_task_function(task_id):
        task_source = get_task_source(task_id)
        if not task_source:
            return False
        start_task(task_source.task)
        logger.set_task_source(task_source)
        return task_source

    def send_back_to_queue(task):
        back_to_queue_task(task)
        # send_source(task.task_id, TIMEOUT_FOR_BACK_TASK)

    def credentials_task_function(credentials, task_keyword):
        add_working_credentials_task(credentials.id, task_keyword.task_id, TaskType.source)

    process(get_task_function(task_id),
            TaskType.source,
            complete_task,
            fail_task,
            send_back_to_queue,
            parse_source,
            credentials_task_function)


@app.task(name=TASK_KEYWORD_ID)
def keyword_task(task_id):
    print("Keyword task received: id={}".format(task_id))
    logger.clean()

    def get_task_function(task_id):
        task_keyword = get_task_keyword(task_id)
        if not task_keyword:
            return False
        start_task(task_keyword.task)
        logger.set_task_keyword(task_keyword)
        return task_keyword

    def send_back_to_queue(task):
        back_to_queue_task(task)
        # send_keyword(task.task_id, TIMEOUT_FOR_BACK_TASK)

    def credentials_task_function(credentials, task_keyword):
        add_working_credentials_task(credentials.id, task_keyword.task_id, TaskType.keyword)

    process(get_task_function(task_id),
            TaskType.keyword,
            complete_task,
            fail_task,
            send_back_to_queue,
            parse_keyword,
            credentials_task_function)


def credentials_task_function(credentials, subtask):
    add_working_credentials_task(credentials.id, subtask.id, subtask.subtask_type)


def get_subtask_function(subtask_id):
    subtask = get_subtask(subtask_id)
    if not subtask:
        return False
    logger.set_sub_task(subtask)
    start_subtask(subtask)
    return subtask


@app.task(name=SUB_TASK_POST_LIKES)
def subtask_like(subtask_id):
    logger.clean()

    def send_back_to_queue(subtask):
        back_to_queue_subtask(subtask)
        # send_subtask_like(subtask.id, TIMEOUT_FOR_BACK_TASK)

    logger.log("Subtask likes parser with id: {} received".format(subtask_id))
    process(get_subtask_function(subtask_id),
            TaskType.like,
            complete_subtask,
            fail_subtask,
            send_back_to_queue,
            parse_likes,
            credentials_task_function)


@app.task(name=SUB_TASK_POST_COMMENTS)
def subtask_comment(subtask_id):
    logger.clean()

    def send_back_to_queue(subtask):
        back_to_queue_subtask(subtask)
        # send_subtask_comment(subtask.id, TIMEOUT_FOR_BACK_TASK)

    logger.log("Subtask comments parser with id: {} received".format(subtask_id))
    process(get_subtask_function(subtask_id),
            TaskType.comment,
            complete_subtask,
            fail_subtask,
            send_back_to_queue,
            parse_comments,
            credentials_task_function)


@app.task(name=SUB_TASK_POST_SHARES)
def subtask_share(subtask_id):
    logger.clean()

    def send_back_to_queue(subtask):
        back_to_queue_subtask(subtask)
        # send_subtask_share(subtask.id, TIMEOUT_FOR_BACK_TASK)

    logger.log("Subtask shares parser with id: {} received".format(subtask_id))
    process(get_subtask_function(subtask_id),
            TaskType.share,
            complete_subtask,
            fail_subtask,
            send_back_to_queue,
            parse_shares,
            credentials_task_function)


@app.task(name=SUB_TASK_PERSONAL_PAGE)
def subtask_personal_page(subtask_id):
    logger.clean()

    def get_subtask_function(subtask_id):
        personal_data_subtask = get_personal_data_subtask(subtask_id)
        if not personal_data_subtask:
            return False
        logger.set_sub_task(personal_data_subtask.subtask)
        start_subtask(personal_data_subtask.subtask)
        return personal_data_subtask

    def send_back_to_queue(personal_data_subtask):
        back_to_queue_subtask(personal_data_subtask.subtask)
        # send_subtask_personal_page(personal_data_subtask.subtask_id, TIMEOUT_FOR_BACK_TASK)

    def credentials_task_function(credentials, personal_data_subtask):
        add_working_credentials_task(credentials.id, personal_data_subtask.subtask_id, SubtaskType.personal_page)

    logger.log("Subtask personal page parser with id: {} received".format(subtask_id))
    process(get_subtask_function(subtask_id),
            TaskType.personal_page,
            complete_subtask_personal_data,
            fail_subtask_personal_data,
            send_back_to_queue,
            parse_personal_page,
            credentials_task_function)


def process(task, task_type, on_complete, on_fail, send_back_to_queue, parse_function, credentials_task_function):
    if not task:
        browser_service.close()
        logger.log("Task with not found in db. Parsing doesn't start")
        return False

    credentials = get_credentials(task_type)
    if credentials is None:
        logger.log("All accounts are busy. Send task back to queue")
        browser_service.close()
        send_back_to_queue(task)
        return False

    try:
        logger.log("start processing task id={}".format(task.id))
        browser, proxy_url = browser_service.open(credentials)
        logger.log_alive()
        if not browser and not proxy_url:
            send_back_to_queue(task)
            return False
    except Exception as e:
        logger.exception("Browser or proxy failed", e)
        send_back_to_queue(task)
        browser_service.close()
        return

    try:
        if not open_fb(browser, credentials):
            browser_service.close()
            send_back_to_queue(task)
            return
    except Exception as e:
        logger.exception("FB open error", e)
        browser_service.close()
        send_back_to_queue(task)
        return

    try:
        credentials_task_function(credentials, task)
        logger.log("parsing starts")
        logger.log_alive()
        parse_function(browser, task)
        logger.log("parsing has finished successfully")
        logger.log_alive()
        on_complete(credentials, task)
    except Exception as e:
        logger.exception("Parsing has finished with errors", e)
        traceback.print_exc()
        DBSession.rollback()
        on_fail(credentials, task)
    finally:
        browser_service.close()


#for debug purposes
if CURRENT_PROFILE == 'local':
    #keyword_task(89)
    #source_task(6)
    #subtask_personal_page(2830)
    #subtask_like(3463)
    #subtask_share(3465)
    #subtask_comment(2409) # беглов
    #subtask_comment(2572) # мадонна
    #subtask_personal_page(44)
    pass
