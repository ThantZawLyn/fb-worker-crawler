from datetime import datetime
from random import randint

from sqlalchemy import and_, desc, false, text, true

from .. import logger
from ..constants import PROXY_BLOCK_ATTEMPTS, TIMEOUT_BETWEEN_ACCOUNTS_WORK
from ..database import DBSession
from ..database.models import (FBAccount, Proxy, TaskType, UserAgent,
                               WorkerCredential, WorkingCredentialsTasks)


def create_working_credentials_ignore_availability():
    def get_unavailable_account():
        working_credentials_accounts = DBSession.query(WorkerCredential.account_id)
        account = DBSession.query(FBAccount). \
            filter((~FBAccount.id.in_(working_credentials_accounts)) & (FBAccount.available == false())). \
            filter(text('((accounts.availability_check + \'360 minute\'::interval) < \'' + str(datetime.now()) + "\' or accounts.availability_check is Null)")). \
            with_for_update(). \
            first()
        return account

    return create_working_credentials(get_unavailable_account)


def get_account():
    working_credentials_accounts = DBSession.query(WorkerCredential.account_id)
    account = DBSession.query(FBAccount). \
        filter((~FBAccount.id.in_(working_credentials_accounts)) & (FBAccount.available == true())). \
        with_for_update(). \
        first()
    return account


def create_working_credentials(account_function=get_account):
    account = account_function()

    if account is None:
        logger.log("Accounts are empty")
        return None

    working_credentials_proxy = DBSession.query(WorkerCredential.proxy_id)
    proxy = DBSession.query(Proxy). \
        filter((~Proxy.id.in_(working_credentials_proxy)) & (Proxy.available == true())). \
        with_for_update(). \
        first()

    if proxy is None:
        logger.log("Proxy are empty")
        return None

    working_credentials_user_agent = DBSession.query(WorkerCredential.user_agent_id)
    user_agent = DBSession.query(UserAgent). \
        filter(~UserAgent.id.in_(working_credentials_user_agent)). \
        with_for_update(). \
        first()
    if user_agent is None:
        logger.log("Agents are empty")
        return None

    try:
        working_credentials = WorkerCredential(account_id=account.id, proxy_id=proxy.id, user_agent_id=user_agent.id, locked=False)
        DBSession.add(working_credentials)
        DBSession.commit()
        logger.log("New working credentials have created id: {}".format(str(working_credentials.id)))
    except Exception as e:
        DBSession.rollback()
        logger.exception("Warning - WC add constraint violation", e)
        return None

    return working_credentials


def find_task_type_working_credentials(credentials, task_type):
    for c in credentials:
        types = [TaskType.keyword.value,
                 TaskType.source.value,
                 TaskType.like.value,
                 TaskType.comment.value,
                 TaskType.share.value,
                 TaskType.personal_page.value]

        wc_tasks = DBSession.query(WorkingCredentialsTasks). \
            filter(WorkingCredentialsTasks.worker_credentials_id == c.id). \
            order_by(desc(WorkingCredentialsTasks.finish_timestamp)). \
            limit(len(types) - 1). \
            all()

        print("Find wc_id: {} wc_tasks: {}".format(str(c.id), [task.type for task in wc_tasks]))
        for wc_t in wc_tasks:
            if wc_t.type in types:
                types.remove(wc_t.type)

        print("Current task: {} should be in list: {}".format(task_type, types))
        if task_type in types:
            print("Select wc_id: {} for worker".format(str(c.id)))
            return c
        else:
            print("Move to another worker")

    print("There are no worker_credentials with free type: {}".format(task_type))
    if len(credentials) == 0:
        print("There are no worker_credentials")
        return None
    else:
        random_credentials = credentials[randint(0, len(credentials) - 1)]
        print("Choose random credentials: There are no worker_credentials id: {}".format(random_credentials.id))
        return random_credentials


def get_credentials(task_type):
    logger.log("find free credentials")
    credentials = DBSession.query(WorkerCredential).\
        filter(and_(WorkerCredential.attemp <= 10, WorkerCredential.inProgress == false())). \
        filter(text('((worker_credentials.last_time_finished + \'' + str(TIMEOUT_BETWEEN_ACCOUNTS_WORK) +
                    ' minute\'::interval) < \'' + str(datetime.now()) +
                    "\' or worker_credentials.last_time_finished is Null)")). \
        with_for_update(). \
        all()

    print("Find {} working credentials: ".format(str(len(credentials))))
    if len(credentials) == 0:
        logger.log("There are no free credentials. Create new working credentials")
        credentials = create_working_credentials()
    else:
        credentials = find_task_type_working_credentials(credentials, task_type)

    if credentials is None:
        logger.log("credentials is empty")
        return None

    if credentials.account is None:
        logger.log("credentials account is empty")
        return None

    set_started(credentials)
    return credentials


def get_working_credentials_task(wc_id, task_id):
    return DBSession.query(WorkingCredentialsTasks).\
        filter(WorkingCredentialsTasks.worker_credentials_id == wc_id).\
        filter(WorkingCredentialsTasks.task_id == task_id).\
        first()


def add_working_credentials_task(wc_id, task_id, task_type):
    wc_task = WorkingCredentialsTasks(worker_credentials_id=wc_id,
                                      task_id=task_id,
                                      type=task_type,
                                      start_timestamp=datetime.now())
    DBSession.add(wc_task)
    DBSession.commit()


def set_started(credentials):
    logger.log("set credentials inProgress=true")
    credentials.inProgress = True
    credentials.inProgressTimeStamp = datetime.now()
    credentials.alive_timestamp = datetime.now()
    DBSession.commit()


def set_finished(credentials):
    logger.log("set credentials inProgress=false")
    credentials.inProgress = False
    credentials.last_time_finished = datetime.now()
    DBSession.commit()


def complete_working_credentials_task(wc_id, task_id):
    wc_task = get_working_credentials_task(wc_id, task_id)
    if wc_task:
        logger.log("Complete working_credentials task id: {}".format(wc_task.id))
        wc_task.finish_timestamp = datetime.now()
        DBSession.commit()


def update_worker_credential(data):
    account_id = data['account_id']
    proxy_id = data['proxy_id']
    user_agent_id = data['user_agent_id']
    worker_credential = DBSession. \
        query(WorkerCredential). \
        filter((WorkerCredential.account_id == account_id) &
               (WorkerCredential.proxy_id == proxy_id) &
               (WorkerCredential.user_agent_id == user_agent_id)).with_for_update().first()

    worker_credential.locked = True

    DBSession.commit()
    return worker_credential


def block_proxy(credentials):
    if credentials.proxy.attempts >= PROXY_BLOCK_ATTEMPTS:
        logger.log("Blocking proxy id: {} set available False".format(credentials.proxy.id))
        credentials.proxy.available = False
        #DBSession.delete(credentials)
    else:
        logger.log("Proxy id: {} attempts to connect: {}".format(credentials.proxy.id, credentials.proxy.attempts))
        credentials.proxy.attempts = credentials.proxy.attempts + 1

    credentials.proxy.last_time_checked = datetime.now()
    DBSession.commit()


def block_account(credentials):
    logger.log("Blocking account id: {} set available False".format(credentials.account.id))
    credentials.account.available = False
    credentials.locked = True
    credentials.attemp = credentials.attemp + 1
    credentials.account.availability_check = datetime.now()
    DBSession.commit()


def enable_account(credentials):
    if not credentials.account.available:
        logger.log("Enable account id: {} set available True".format(credentials.account.id))
        credentials.account.available = True
        credentials.locked = False
        credentials.attemp = 0
        credentials.account.availability_check = datetime.now()
        DBSession.commit()


def enable_proxy(proxy):
    logger.log("Proxy {} has successfully enabled".format(proxy.id))
    proxy.available = True
    proxy.attempts = 0
    DBSession.commit()


def enable_wc_by_proxy(proxy):
    wc = DBSession.query(WorkerCredential).\
        join(FBAccount, FBAccount.id == WorkerCredential.account_id).\
        filter(FBAccount.available == true()).\
        filter(WorkerCredential.proxy_id == proxy.id).\
        filter(WorkerCredential.locked == true()).\
        first()
    if wc:
        logger.log("Worker credentials {} has successfully enabled".format(wc.id))
        wc.locked = False
        DBSession.commit()


def get_proxy(proxy_id):
    return DBSession.query(Proxy).filter(Proxy.id == proxy_id).first()
