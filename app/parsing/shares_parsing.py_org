from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from .. import logger
from ..database import DBSession
from ..database.models import Share, User
from ..database.subtasks_dao import save_personal_page_subtask
from ..utils.user_utils import trim_full_link
from .common_parsing import get_fb_id


def parse_shares(browser, subtask):
    logger.log("Start parse shares")

    post = subtask.post
    browser.get(post.fb_post_link)

    try:
        WebDriverWait(browser, 10).until(
            ec.presence_of_element_located((By.CSS_SELECTOR, "a[href*=shares][rel=dialog]"))
        )
        browser.execute_script(f"document.querySelector('a[href*=shares][rel=dialog]').click()")
    except Exception as e:
        logger.exception("Shares", e)

    browser.implicitly_wait(1)
    shares_section = None
    shares = []
    try:
        shares_section = WebDriverWait(browser, 10).until(
            ec.presence_of_element_located(
                (By.XPATH, "//div[contains(@data-testid, 'repost_view_dialog')]/div[contains(@role, 'dialog')]"))
        )
    except Exception as e:
        logger.exception("Shares", e)

    try:
        logger.log("Begin loop of scroll")
        while True:
            logger.log_alive()
            scroll_to_end(browser, 30)
            try:
                logger.log("search more button")
                WebDriverWait(browser, 5).until(
                    ec.presence_of_element_located(
                        (By.XPATH, "//div[contains(@class, 'uiMorePager stat_elem async_saving')]"))
                )
            except Exception as e:
                logger.exception("more button doesn't find", e)
                break

        shares = []
        if shares_section:
            try:
                shares = shares_section.find_elements(By.XPATH, ".//h5/span/span/a")
            except Exception as e:
                logger.exception("Shares", e)
    except Exception as e:
        logger.exception("Exception", e)

    logger.log("Begin loop of share parse")

    def parse_share(share):
        author_name = share.text
        author_link = trim_full_link(share.get_attribute("href"))
        author_fb_id = get_fb_id(share, author_link)
        return author_name, author_link, author_fb_id

    profiles_data = []
    for share in shares:
        author_name, author_link, author_fb_id = parse_share(share)
        profiles_data.append((author_link, {"name": author_name, "fb_id": author_fb_id}))

    logger.log("Save shares to db")
    users = {u.link: u for u in DBSession.query(User).filter(User.link.in_([link for link, _ in profiles_data])).all()}
    added_shares = 0

    subtasks = []
    for key, pd in profiles_data:
        if key not in users:
            user = User(name=pd['name'], link=key, fb_id=pd['fb_id'])
            subtasks.append(save_personal_page_subtask(post, user))
            DBSession.add(user)
        else:
            user = users[key]

        share = Share(post=post, user=user)
        DBSession.add(share)
        added_shares += 1

    DBSession.commit()

    logger.log(f"Added to db {added_shares} shares")
    return added_shares


def scroll_to_end(browser, times):
    logger.log("Start scrolling")
    try:
        body = WebDriverWait(browser, 10).until(
            ec.presence_of_element_located((By.CSS_SELECTOR, 'body'))
        )
        for i in range(times):
            body.send_keys(Keys.END)

    except Exception as e:
        logger.log("Scrolling", e)

    logger.log("Finish scrolling")
