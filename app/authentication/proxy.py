import requests

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

from .. import logger
from ..constants import FACEBOOK_URL_WWW, GOOGLE_URL_WWW

LOCAL_PROXY_URL = 'http://localhost:3000'
GOOGLE_TXT_URL = 'http://www.google.com/humans.txt'

def get_proxy_url(proxy):
    real_proxy = proxy_string(proxy)
    proxy_url_response = requests.get(LOCAL_PROXY_URL + '/open/' + real_proxy)
    forward_proxy = proxy_url_response.json()["url"]
    real_proxy = "http://" + real_proxy
    logger.log("Proxy address: {} forwards into address: {}".format(real_proxy, forward_proxy))
    return forward_proxy


def close_proxy_url(proxy_url):
    request_string = LOCAL_PROXY_URL + '/close/' + proxy_url.replace("http://", '')
    logger.log("Send request to close proxy " + request_string)
    proxy_url_response = requests.get(request_string)
    logger.log("Proxy close response: {}".format(proxy_url_response.json()["message"]))


def proxy_string(proxy):
    return proxy.login + ":" + proxy.password + "@" + proxy.host + ":" + str(proxy.port)


def is_proxy_available(browser):
    google_lazy_proxy_check()
    if facebook_proxy_check(browser):
        logger.log("Check passed. Proxy is available")
        return True
    else:
        # Removed google proxy check
        # return google_proxy_check(browser)
        return False


def facebook_proxy_check(browser):
    browser.get(FACEBOOK_URL_WWW)
    try:
        logger.log("Check proxy available on {}".format(FACEBOOK_URL_WWW))
        WebDriverWait(browser, 50).until(ec.presence_of_element_located((By.CSS_SELECTOR, "#facebook")))
    except Exception as e:
        logger.exception("Facebook is not available", e)
        return False
    return True

def google_lazy_proxy_check():
    try:
        response = requests.get(GOOGLE_TXT_URL)
        logger.log("Loaded google text, length is 286 {0}".format(len(response.text)==286))
    except Exception as e:
        logger.log("Error loading google text {0}".format(e))

def google_proxy_check(browser):
    browser.get(GOOGLE_URL_WWW)
    try:
        logger.log("Check proxy available on: {}".format(GOOGLE_URL_WWW))
        WebDriverWait(browser, 30).until(ec.presence_of_element_located((By.XPATH, "//input[@type='submit']")))
    except Exception as e:
        logger.exception("Google is not available", e)
        return False

    logger.log("Check passed. Proxy is available")
    return True
