import pickle

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

from .. import logger
from ..authentication.proxy import is_proxy_available
from ..constants import FACEBOOK_URL_WWW, FACEBOOK_URL_MOBILE, FACEBOOK_URL_WWW_NEW
from ..database import DBSession
from ..database.models import Cookies
from ..database.worker_credentials_dao import (block_account, block_proxy,
                                               enable_account, enable_proxy)
from ..parsing import patterns, js_scripts
from ..parsing.language import switch_language_to_english


def is_new_design(browser):
    """Проверка версии дизайна."""
    try:
        elem = WebDriverWait(browser, 20).until(
            ec.presence_of_element_located(
                (By.XPATH, patterns.XPATH_NEW_FB_LOGO))
        )
        if elem:
            return True
    except Exception as e:
        logger.log("Haven't found new logo, error is {0}".format(e))
        return False


def is_popup(browser):
    """
    Находится ли на странице нового дизайна
    всплывающее окно.
    """
    logger.log("Searching for popups")
    try:
        popup_one = WebDriverWait(browser, 20).until(
            ec.presence_of_element_located(
                (By.XPATH, patterns.XPATH_NEW_POPUP_ONE))
        )
        if popup_one:
            logger.log("Popup button found")
            return True
    except Exception as e:
        logger.exception("No popup button present", e)
        return False


def run_xpath_script(browser, script):
    script_func = "{0}\n{1}".format(
        js_scripts.XPATH_FUNC_DEF,
        script
    )
    logger.log("Executing: {0}".format(script_func))
    browser.execute_script(script_func)
    browser.implicitly_wait(2)


def click_popups(browser):
    """Нажатие на всплывающие после логина окна."""
    if is_popup(browser):
        try:
            btn_1 = browser.find_element_by_xpath(patterns.XPATH_NEW_POPUP_ONE)
            logger.log("Clicking first button")
            btn_1.click()
            browser.implicitly_wait(2)
        except Exception as e:
            logger.log("Error clicking first button {}".format(e))
            return False

        try:
            btn_2 = browser.find_element_by_xpath(patterns.XPATH_NEW_POPUP_TWO)
            logger.log("Clicking second button")
            btn_2.click()
            browser.implicitly_wait(2)
        except Exception as e:
            logger.log("Error clicking second button {0}".format(e))
            return False

        try:
            logger.log("Clicking cross")
            run_xpath_script(
                browser,
                js_scripts.CLICK_POPUP_CROSS
            )
            logger.log("Successfully clicked")
            return True
        except Exception as e:
            logger.exception("Error clicking cross {0}".format(e))
            return False


def click_switch_to_old_design(browser):
    """Нажатие кнопки выпадающего списка и перехода на старый дизайн."""
    logger.log("Trying to switch to old design...")

    try:
        logger.log("Finding dropdown button...")
        dropout_btn = WebDriverWait(browser, 10).until(
            ec.presence_of_element_located(
                (By.XPATH, patterns.XPATH_NEW_DROPOUT_ICON))
        )
        logger.log("Clicking dropdown button")
        run_xpath_script(
            browser,
            js_scripts.XPATH_CLICK.format(patterns.XPATH_NEW_DROPOUT_ICON)
        )
    except Exception as e:
        logger.log("Error finding dropdown button: {0}".format(e))
        return False

    try:
        logger.log("Finding switch to old design button...")
        switch_btn = WebDriverWait(browser, 10).until(
            ec.presence_of_element_located(
                (By.XPATH, patterns.XPATH_NEW_SWITCH_LOGO))
        )
        logger.log("Clicking switch button")
        run_xpath_script(
            browser,
            js_scripts.XPATH_CLICK.format(patterns.XPATH_NEW_SWITCH_LOGO)
        )
    except Exception as e:
        logger.log("Error finding switch to old design button: {0}".format(e))
        return False

    # TODO: ONLY NEW ACCS: Stars and continue
    try:
        logger.log("Finding help us improve popup")
        ad = WebDriverWait(browser, 10).until(
            ec.presence_of_element_located(
                (By.XPATH, patterns.XPATH_HELP_IMPROVE_AD))
        )
        if ad:
            try:
                logger.log("Popup found, clicking ad {0}".format(ad))
                run_xpath_script(
                    browser,
                    js_scripts.CLICK_FIVE_STAR
                )
                logger.log("Clicking Submit")
                run_xpath_script(
                    browser,
                    js_scripts.CLICK_HELP_US_IMPROVE_SUBMIT
                )
                return True
            except Exception as e:
                logger.log("Error clicking Help us improve popup {0}".format(e))
                return False

    except Exception as e:
        logger.log("Help us improve popup not found")
        return True


def switch_to_old_design(browser):
    """Переключение на старый дизайн."""
    logger.log("Checking design")
    if is_new_design(browser):
        logger.log("The design is NEW")
        click_popups(browser)
        swithed = click_switch_to_old_design(browser)
        if swithed:
                logger.log("Successfully switched to old design")
    else:
        logger.log("The design is old, continuing")


def open_fb(browser, credentials):
    if not is_proxy_available(browser):
        block_proxy(credentials)
        return False
    else:
        enable_proxy(credentials.proxy)

    logger.log("start opening URL: {}".format(FACEBOOK_URL_WWW))
    browser.get(FACEBOOK_URL_WWW)

    current_url = browser.current_url
    if current_url == FACEBOOK_URL_WWW or FACEBOOK_URL_WWW_NEW:
        authenticate(browser, credentials)

        if not is_valid(browser, credentials):
            block_account(credentials)
            return False
        else:
            enable_account(credentials)
            logger.log("Authenticated Successfully")
            save_cookies(browser, credentials)
            browser.execute_script("window.scrollTo(0,document.body.scrollHeight)")
            try:
                add_box = WebDriverWait(browser, 30).until(
                    ec.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Add friend')]")))
                add_box.click()
                logger.log("One friend request sent")
            except:
                pass
            try:
                add_box = WebDriverWait(browser, 30).until(
                    ec.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Add friend')]")))
                add_box.click()
                logger.log("Two friend request sent")
            except:
                pass
            try:
                add_box = WebDriverWait(browser, 30).until(
                    ec.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Add friend')]")))
                add_box.click()
                logger.log("Three friend request sent")
            except:
                pass
            #switch_to_old_design(browser)
            #switch_language_to_english(browser)
            return True
    elif current_url != FACEBOOK_URL_WWW_NEW:
        logger.log("Change to Mobile URL")
        browser.get(FACEBOOK_URL_MOBILE)
        authenticate_mob(browser, credentials)
        if not is_valid(browser, credentials):
            block_account(credentials)
            return False
        else:
            enable_account(credentials)
            logger.log("Authenticated Successfully")
            save_cookies(browser, credentials)
            switch_to_old_design(browser)
            switch_language_to_english(browser)
            return True
    else:
        logger.log("Browser opened other URL: {0}".format(current_url))
        return False


def authenticate(browser, credentials):
    logger.log("Start authentication")
    if credentials.account.cookies is None:
        logger.log("Auth by credentials")
        fb_desktop_auth(browser, credentials.account)
    else:
        logger.log("Auth by cookies")
        fb_cookie_auth(browser, credentials.account)
        if not check_only_log_visible_element(browser):
            logger.log('Cookies not valid. Using login and password')
            fb_desktop_auth(browser, credentials.account)

def authenticate_mob(browser, credentials):
    logger.log("Start authentication")
    if credentials.account.cookies is None:
        logger.log("Auth by credentials")
        fb_mobile_auth(browser, credentials.account)
    else:
        logger.log("Auth by cookies")
        fb_cookie_auth(browser, credentials.account)
        if not check_only_log_visible_element(browser):
            logger.log('Cookies not valid. Using login and password')
            fb_mobile_auth(browser, credentials.account)


def is_valid(browser, credentials):
    """Проверка аккаунта на работоспособность."""
    return not is_banned(browser, credentials.account) and check_only_log_visible_element(
        browser)


def is_banned(browser, account):
    """Проверка, забен ли аккаунт."""
    if 'checkpoint' in browser.current_url:
        logger.log("Account is banned! id: {0}, credentials: {1} {2}".format(
            account.id,
            account.login,
            account.password,
        ))
        return True
    else:
        logger.log("Link doesn't contain checkpoint keyword, moving on")
        return False


def check_only_log_visible_element(browser):
    """Проверка авторизации пользователя через наличие характерного элемента."""
    # TODO: fix target element
    PROFILE_PATTERNS = [
        (By.XPATH, patterns.XPATH_OLD_PROFILE_ICON),
        (By.XPATH, patterns.XPATH_NEW_FB_LOGO),
    ]
    for _by, pattern in PROFILE_PATTERNS:
        try:
            logger.log("Checking availability of pattern {0}".format(pattern))
            WebDriverWait(browser, 10).until(
                ec.presence_of_element_located((_by, pattern)))
            logger.log("Element found")
            return True
        except Exception as e:
            logger.log(
                "Can't find element by pattern {0}, error is {1}".format(pattern, e))
            continue
    return False


def fb_cookie_auth(browser, account):
    logger.log(
        "authenticate using cookies id={}".format(account.cookies.id)
    )

    if account.cookies.row_data is None:
        return False

    for cookie in pickle.loads(account.cookies.row_data):
        cook = {'name': cookie['name'],
                'value': cookie['value'],
                'domain': cookie['domain'],
                'path': cookie['path'],
                'secure': cookie['secure']}
        browser.add_cookie(cook)

    browser.refresh()
    browser.get(FACEBOOK_URL_WWW)
    


def save_cookies(browser, credentials):
    logger.log("Start dump cookies")
    browser_cookies = pickle.dumps(browser.get_cookies())

    if credentials.account.cookies:
        credentials.account.cookies.row_data = browser_cookies
    else:
        cookies = Cookies(account_id=credentials.account.id, row_data=browser_cookies)
        credentials.account.cookies = cookies
        DBSession.add(cookies)

    DBSession.commit()
    logger.log("Cookies with id={} are saved".format(credentials.account.cookies.id))


def find_and_click_login_btn(browser):
    """Поиск и нажатие на кнопку логина."""
    LOGIN_PATTERNS = [
        (By.CSS_SELECTOR,
         patterns.CSS_SEL_OLD_LOGIN_BTN,
         js_scripts.CLICK_OLD_DESIGN_BTN),
        (By.CSS_SELECTOR,
         patterns.CSS_SEL_NEW_LOGIN_BTN,
         js_scripts.CLICK_NEW_DESIGN_BTN),
    ]
    for _by, pattern, script in LOGIN_PATTERNS:
        try:
            logger.log("Trying to find login-button...")
            element = WebDriverWait(browser, 5).until(
                ec.presence_of_element_located((_by, pattern))
            )
            logger.log("Found {0}".format(element))
            if element:
                logger.log("Successfully found login by {0}".format(pattern))
                browser.execute_script(script)
                return True

        except Exception as e:
            logger.log(f"Login click error {e} for pattern {pattern}")
            continue
    return None


def selenium_send_key(browser, selector, key):
    logger.log("Sending {0} to {1}".format(key, selector))
    try:
        result = WebDriverWait(browser, 10).until(
            ec.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
        result.send_keys(key)
    except Exception as e:
        logger.exception("Send key error", e)


"""def fb_desktop_auth(browser, account):    
    logger.log("on Facebook")
    selenium_send_key(browser, '#email', account.login)
    selenium_send_key(browser, '#pass', account.password)
    find_and_click_login_btn(browser)"""
    
def fb_desktop_auth(browser, account):    
    logger.log("on Facebook")
    # Clear the email field before sending keys
    email_field = browser.find_element_by_css_selector('#email')
    email_field.clear()
    email_field.send_keys(account.login)    
    # Clear the password field before sending keys
    password_field = browser.find_element_by_css_selector('#pass')
    password_field.clear()
    password_field.send_keys(account.password)    
    find_and_click_login_btn(browser)

def fb_mobile_auth(browser, account):
    """Аутенфикация в десктопной версии сайта."""
    logger.log("on  mobile Facebook")
    selenium_send_key(browser, '#m_login_email', account.login)
    selenium_send_key(browser, '#m_login_password', account.password)
    find_and_click_login_btn(browser)
