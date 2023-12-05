import re

from selenium.common.exceptions import (ElementClickInterceptedException,
                                        ElementNotInteractableException,
                                        StaleElementReferenceException)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from .. import logger
from ..database import DBSession
from ..database.models import Like, LikeType, User
from ..database.subtasks_dao import save_personal_page_subtask
from ..utils.user_utils import trim_full_link
from .common_parsing import get_fb_id, random_sleep

def parse_likes(browser, subtask):
    logger.log("Start parse likes")

    post = subtask.post
    browser.get(post.fb_post_link)

    try:
        WebDriverWait(browser, 10).until(
            ec.presence_of_element_located((By.CSS_SELECTOR, "a[href*=reaction]"))
        )
        browser.execute_script(f"document.querySelector('a[href*=reaction]').click()")
    except Exception as e:
        logger.exception("Likes", e)

    browser.implicitly_wait(99)
    likes_section = None
    likes = []
    try:
        likes_section = WebDriverWait(browser, 10).until(
            ec.presence_of_element_located(
                (By.XPATH, "//div[@id='reaction_profile_browser']"))
        )
    except Exception as e:
        logger.exception("Likes", e)

    try:
        logger.log("Begin loop of scroll")
        while True:
            logger.log_alive()
            scroll_to_end(browser, 99)
            try:
                logger.log("search more button")
                WebDriverWait(browser, 99).until(
                    ec.presence_of_element_located(
                        (By.XPATH, ".//div[@class='title mfsm fcl']"))
                ).click()
            except Exception as e:
                logger.exception("more button doesn't find", e)
                break

        likes = []
        if likes_section:
            try:
                likes = likes_section.find_elements(By.XPATH, ".//div[@class='_4mn c']//a")
            except Exception as e:
                logger.exception("Likes", e)
    except Exception as e:
        logger.exception("Exception", e)

    logger.log("Begin loop of like parse")

    def parse_like(like):
        author_name = like.text
        logger.log("Res Author = {}".format(author_name))
#         author_link = trim_full_link(share.find_elements(By.XPATH, ".//div[@class='_4mn c']//a").get_attribute("href"))
        author_link = trim_full_link(like.get_attribute("href"))
        logger.log("Res Author Link= {}".format(author_link))
        author_fb_id = get_fb_id(like, author_link)
        logger.log("Res Author id= {}".format(author_fb_id))
        return author_name, author_link, author_fb_id

    profiles_data = []
    for like in likes:
        author_name, author_link, author_fb_id = parse_like(like)
        profiles_data.append((author_link, {"name": author_name, "fb_id": author_fb_id}))

    logger.log("Save likes to db")
    users = {u.link: u for u in DBSession.query(User).filter(User.link.in_([link for link, _ in profiles_data])).all()}
    added_likes = 0

    subtasks = []
    for key, pd in profiles_data:
        if key not in users:
            user = User(name=pd['name'], link=key, fb_id=pd['fb_id'])
            subtasks.append(save_personal_page_subtask(post, user))
            DBSession.add(user)
        else:
            user = users[key]

        like = Like(post=post, user=user)
        DBSession.add(like)
        added_likes += 1

    DBSession.commit()

    logger.log(f"Added to db {added_likes} likes")
    return added_likes

    logger.log("Saving likes...")
    added_normal_likes = save_like(get_likes(browser, '{"reactionID":1635855486666999}'), like_type=LikeType.like)
    logger.log("normal_likes= {}".format(added_normal_likes))
    added_love_likes = save_like(get_likes(browser, '{"reactionID":1678524932434102}'), like_type=LikeType.love)
    added_haha_likes = save_like(get_likes(browser, '{"reactionID":115940658764963}'), like_type=LikeType.haha)
    added_wow_likes = save_like(get_likes(browser, '{"reactionID":478547315650144}'), like_type=LikeType.wow)
    added_sad_likes = save_like(get_likes(browser, '{"reactionID":908563459236466}'), like_type=LikeType.sad)
    added_angry_likes = save_like(get_likes(browser, '{"reactionID":444813342392137}'), like_type=LikeType.angry)
    

def get_likes(browser, name):
    try:        
        #likes = browser.find_elements(By.XPATH, f"//ul[@id='{name}']//a[contains(@href,'fref=') and not(@data-gt)]//span/i/../../../..")
        likes = browser.find_elements(By.XPATH, f"//div[@class='scrollAreaColumn']//span[@data-store='{name}']/span/span")
        for like in likes:
            like = like.text
    except Exception as e:
        logger.exception("Likes", e)
        likes = []
    return like
                                   
    #added_normal_likes = save_like(browser.find_elements(By.XPATH,f"//div[@class='scrollAreaColumn']//span[@data-store='{"reactionID":1635855486666999}']//span[@aria-label=contains(text(),'')]/span".text, like_type=LikeType.like)
    #added_normal_likes = save_like(browser.find_elements(By.XPATH,f"//div[@class='scrollAreaColumn']//span[@data-store='{"reactionID":1678524932434102}']//span[@aria-label=contains(text(),'')]/span".text, like_type=LikeType.love)
    #added_normal_likes = save_like(browser.find_elements(By.XPATH,f"//div[@class='scrollAreaColumn']//span[@data-store='{"reactionID":115940658764963}']//span[@aria-label=contains(text(),'')]/span".text, like_type=LikeType.haha)
    #added_normal_likes = save_like(browser.find_elements(By.XPATH,f"//div[@class='scrollAreaColumn']//span[@data-store='{"reactionID":478547315650144}']//span[@aria-label=contains(text(),'')]/span".text, like_type=LikeType.wow)
    #added_normal_likes = save_like(browser.find_elements(By.XPATH,f"//div[@class='scrollAreaColumn']//span[@data-store='{"reactionID":908563459236466}']//span[@aria-label=contains(text(),'')]/span".text, like_type=LikeType.sad)
    #added_normal_likes = save_like(browser.find_elements(By.XPATH,f"//div[@class='scrollAreaColumn']//span[@data-store='{"reactionID":1635855486666999}']//span[@aria-label=contains(text(),'')]/span".text, like_type=LikeType.like)
                              
    logger.log("Added to database {} normal, {} love, {} haha, {} wow, {} sad, {} angry"
               .format(added_normal_likes, added_love_likes, added_haha_likes, added_wow_likes, added_sad_likes, added_angry_likes))

def scroll_to_end(browser, times):
    logger.log("Start scrolling")
    try:
        body = WebDriverWait(browser, 99).until(
            ec.presence_of_element_located((By.CSS_SELECTOR, 'body'))
        )
        for i in range(times):
            body.send_keys(Keys.END)

    except Exception as e:
        logger.log("Scrolling", e)

    logger.log("Finish scrolling")


def trim_like_url(link):
    return link.split('&av=')[0]
