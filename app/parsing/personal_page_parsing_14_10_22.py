import re

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from .. import logger
from ..database import DBSession
from ..database.models import UserJob, UserUniversity
from ..utils.url_utils import get_param


class Organisation:
    def __init__(self, name, link, info):
        self.name = name
        self.link = link
        self.info = info



def parse_personal_page(browser, subtask_personal_data):
    user = subtask_personal_data.user
    x = user.link
    y = x.replace("//m.", "//www.")
    logger.log("Start parse personal data link: {}".format(y))
#     browser.get("https://www.facebook.com/youngjun.choi.31")
    browser.get(y)

    #user.fb_id = get_fb_id(browser)
    open_about_tab(browser, "about")
    sleep(2)
    open_about_tab(browser, "contact")
    sleep(2)

    user.sex = get_data_by_xpath(browser, "sex", "//div[contains(text(),'Gender')]/../../../../../../../.././div/span")
    birth_date = get_data_by_xpath(browser, "birthday", "//div[contains(text(),'Birth date')]/../../../../../../../.././div/span")
    birth_year = get_data_by_xpath(browser, "birthyear", "//div[contains(text(),'Birth year')]/../../../../../../../.././div/span")
    if birth_date is None or birth_year is None:
        user.birthday = None
    else:
        user.birthday = birth_date + '-' + birth_year
    open_about_tab(browser, "overview")
    sleep(2)
    user.current_city = get_data_by_xpath(browser, "current city", "//span[contains(text(), 'Lives in ')]//span//span")
    user.city_of_birth = get_data_by_xpath(browser, "home city", "//span[contains(text(), 'From')]//span//span")

    open_about_tab(browser, "education")
    sleep(2)
    jobs = parse_work(browser, "Work")
    for job in jobs:
        DBSession.add(UserJob(name=job.name, info=job.info, link=job.link, user=user))

    universities = parse_university(browser, "'University'")
    for university in universities:
        DBSession.add(UserUniversity(name=university.name, info=university.info, link=university.link, user=user))

    DBSession.commit()


def parse_work(browser, type):
    def get_links():
        try:
            logger.log("Search {}".format(type))
            links = WebDriverWait(browser, 5).until(
                ec.presence_of_all_elements_located(
                    (By.XPATH, "//span[text()='Work']/../../../.././div//span[contains(@class,'x193iq5w')]//a"))) 
            logger.log("find: {}".format(str(len(links))))
            return links
        except Exception as e:
            logger.exception("{} doesn't found".format(type), e)
            return []

    def get_organisation(link):
        try:
            info = link.find_element(By.XPATH, "//span[@class='xi81zsa x1nxh6w3 x1sibtaa']").text            
            logger.log("Work at: {}".format(link.text))
            logger.log("Info: {}".format(info))
            return Organisation(link=link.get_attribute("href"), name=link.text, info=info)
        except Exception as e:
            logger.exception("Info doesn't found", e)
            return None

    organisations = []
    for link in get_links():
        organisation = get_organisation(link)
        if organisation:
            organisations.append(organisation)
    return organisations

def parse_university(browser, type):
    def get_links():
        try:
            logger.log("Search {}".format(type))
            links = WebDriverWait(browser, 5).until(
                ec.presence_of_all_elements_located(
                    (By.XPATH, "//span[text()='University']/../../../.././div//span[contains(@class,'x193iq5w')]//a"))) 
            logger.log("find: {}".format(str(len(links))))
            return links
        except Exception as e:
            logger.exception("{} doesn't found".format(type), e)
            return []

    def get_organisation(link):
        try:
            info = link.find_element(By.XPATH, "//span[@class='xi81zsa x1nxh6w3 x1sibtaa']").text
            logger.log("Work at: {}".format(link.text))
            logger.log("Info: {}".format(info))
            return Organisation(link=link.get_attribute("href"), name=link.text, info=info)
        except Exception as e:
            logger.exception("Info doesn't found", e)
            return None

    organisations = []
    for link in get_links():
        organisation = get_organisation(link)
        if organisation:
            organisations.append(organisation)
    return organisations


def open_about_tab(browser, tab_name):
    try:
        logger.log_alive()
        logger.log("open {} tab".format(tab_name))
        WebDriverWait(browser, 3).until(ec.presence_of_element_located((By.CSS_SELECTOR, "a[href*=" + tab_name + "]")))
        browser.execute_script("document.querySelector('a[href*=" + tab_name + "]').click()")
    except Exception as e:
        logger.exception("{} doesn't found".format(tab_name), e)


def get_data_by_xpath(browser, label, xpath):
    try:
        logger.log("Search {}".format(label))
        item = WebDriverWait(browser, 3) \
            .until(ec.presence_of_element_located((By.XPATH, xpath))).text
        logger.log("{} find: {}".format(label, item))
        return item
    except Exception as e:
        logger.exception("{} doesn't found".format(label), e)
    return None


def get_fb_id(browser):
    def get_id_from_meta(browser):
        try:
            logger.log("Search user fb_id from meta")
            element_content = WebDriverWait(browser, 3) \
                .until(ec.presence_of_element_located((By.XPATH, "//meta[@property='al:ios:url']"))) \
                .get_attribute("content")
            fb_id = re.findall('\\d+', element_content)[0]
            logger.log("from link {} has extracted fb_id: {}".format(element_content, fb_id))
            return fb_id
        except Exception as e:
            logger.exception("Couldn't extract fb_id", e)
        return None

    def get_id_from_href(browser):
        try:
            logger.log("Search user fb_id from href")
            href = WebDriverWait(browser, 3) \
                .until(ec.presence_of_element_located((By.XPATH, "//a[contains(@href, '?page_id=')"))) \
                .get_attribute("href")

            fb_id = get_param(href, 'page_id')
            logger.log("from link {} has extracted fb_id: {}".format(href, fb_id))
            return fb_id
        except Exception as e:
            logger.exception("Couldn't extract fb_id", e)
        return None

    fb_id = get_id_from_meta(browser)
    if not fb_id:
        return get_id_from_href(browser)
    else:
        return fb_id
