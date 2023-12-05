from datetime import datetime
from pathlib import Path

from ..constants import CURRENT_PROFILE, SCREEN_SHOT_ENABLED
from ..database import DBSession

SCREENSHOT_PATH = "./screenshots"


def log_subtask(task_id, subtask_id, subtask_type, message):
    print("task_{}, subtask_id_{}, {}, message: {}".format(task_id, subtask_id, subtask_type, message))


def log(task_id, task_type, value, message):
    print("task_{}, type_{}, value_{},message: {}".format(task_id, task_type, value, message))


def log_exception(task_id, message, e):
    print("task_{}, message: {}, exception: {}".format(task_id, message, e))


def screenshot(browser, task_id, type, message):
    def get_credentials():
        if browser.get_credentials():
            return "wc_id_" + str(browser.get_credentials().id)
        else:
            return ""

    if not browser or not browser.get_browser():
        print("Screenshot can't be taken without browser")
        return

    screenshot_path = SCREENSHOT_PATH + "/" + type + "/" + str(task_id)
    Path(screenshot_path).mkdir(parents=True, exist_ok=True)
    browser.get_browser().save_screenshot(screenshot_path + "/" + str(datetime.now().isoformat()) + "-" + get_credentials() + "-" + message.replace(" ", "_") + ".png")


class Log:
    def __init__(self):
        self.task_keyword = None
        self.task_source = None
        self.sub_task = None
        self.browser = None

    def set_task_keyword(self, task):
        self.task_keyword = task

    def set_task_source(self, task):
        self.task_source = task

    def set_sub_task(self, task):
        self.sub_task = task

    def set_browser(self, browser):
        self.browser = browser

    def log_screenshot(self, message):
        if CURRENT_PROFILE == 'local':
            return

        if not SCREEN_SHOT_ENABLED:
            return

        print("Start taking screenshot")
        try:
            if self.task_source:
                screenshot(self.browser, self.task_source.task_id, "task/source", message)
                return

            if self.task_keyword:
                screenshot(self.browser, self.task_keyword.task_id, "task/keyword", message)
                return

            if self.sub_task:
                subtask_type = str(self.sub_task.subtask_type).replace("SubtaskType.", "")
                screenshot(self.browser, self.sub_task.id,
                           "task/subtasks/" + subtask_type + "/" + str(self.sub_task.post.task_id), message)
                return

            screenshot(self.browser, "no_task", "authentication", message)
        except Exception as e:
            print("Exception: {}".format(str(e)))
        print(message)

    def log(self, message):
        try:
            if self.task_source:
                log(self.task_source.task_id, "source", self.task_source.source_id, message)
                return

            if self.task_keyword:
                log(self.task_keyword.task_id, "keyword", self.task_keyword.keyword, message)
                return

            if self.sub_task:
                subtask_type = str(self.sub_task.subtask_type).replace("SubtaskType.", "")
                log_subtask(self.sub_task.post.task_id, self.sub_task.id, subtask_type, message)
                return
        except Exception as e:
            print("Exception: {}".format(str(e)))
        print(message)

    def exception(self, message, e):
        self.log_screenshot(message)
        try:
            if self.task_source:
                log_exception(self.task_source.task_id, message, e)
                return

            if self.task_keyword:
                log_exception(self.task_keyword.task_id, message, e)
                return

            if self.sub_task:
                log_exception(self.sub_task.post.task_id, message, e)
                return
        except Exception as ex:
            print("Exception: {}".format(str(ex)))
        print(message + " " + str(e))

    def clean(self):
        self.task_keyword = None
        self.task_source = None
        self.sub_task = None

    def log_alive(self):
        if self.browser and self.browser.get_credentials():
            wc = self.browser.get_credentials()
            wc.alive_timestamp = datetime.now().isoformat()
            DBSession.commit()
