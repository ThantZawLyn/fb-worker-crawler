from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait

from .. import logger
from ..constants import FACEBOOK_URL_SETTINGS

def is_english(browser):
    try:
        WebDriverWait(browser, 60).until(
            ec.presence_of_element_located((By.XPATH, "//a[@aria-label='Home']"))
        )
        return True
    except Exception as e:
        logger.exception("Language doesn't defined", e)
    return False


def switch_language_to_english(browser):
    if is_english(browser):
        logger.log("Language has already switched to english")
        return True

    browser.get(FACEBOOK_URL_SETTINGS)

    try:
        language_select = WebDriverWait(browser, 60).until(
            ec.presence_of_element_located((By.CSS_SELECTOR, ".fbSettingsListItemEditText"))
        )
        language_select.click()
    except Exception as e:
        logger.exception("Can't find edit button", e)
        return False

    try:
        language_select = WebDriverWait(browser, 60).until(
            ec.presence_of_element_located((By.XPATH, "//select[@name='new_language']"))
        )
        select = Select(language_select)
        select.select_by_value("en_US")

        submit_language = WebDriverWait(browser, 60).until(
            ec.presence_of_element_located((By.CSS_SELECTOR, "label.submit input"))
        )
        submit_language.submit()
    except Exception as e:
        logger.exception("Select language doesn't find", e)
        return False
    return True
