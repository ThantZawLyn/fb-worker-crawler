# likes_parsing.py

import re
import time
from random import randint
from time import sleep

from selenium.common.exceptions import (ElementClickInterceptedException,
                                        ElementNotInteractableException,
                                        StaleElementReferenceException)

from selenium.webdriver.common.keys import Keys
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
    browser.get(trim_like_url(post.fb_post_link_likes))

    buttons = object
    while buttons:
        try:
            buttons = WebDriverWait(browser, 10).until(
                ec.presence_of_all_elements_located((By.XPATH, "//a[contains(@href,'fetch')]")))
            for button in buttons:
                try:
                    old_link = button.get_attribute("href")
                    new_link = re.sub("limit=\d+", "limit=1000", old_link)
                    browser.execute_script(f"arguments[0].setAttribute('href','{new_link}')", button)
                    button.click()
                except StaleElementReferenceException as es:
                    logger.exception("Button is gone!", es)
                except ElementClickInterceptedException as ece:
                    # TODO: проблема с логами
                    logger.log("Button click is intercepted!")
                    link = button.get_attribute("href")
                    id = link[link.index("ft_ent_identifier"):]
                    browser.execute_script(f"document.querySelector('a[href*=\"{id}\"]').click()")
                except ElementNotInteractableException as en:
                    logger.exception("Button is not intractable!", en)

                random_sleep()
        except Exception as e:
            logger.log("New buttons not found")
            break

    logger.log("All likes are opened")
    subtasks = []
    def save_like(profiles, like_type):

        profiles_data = {}
        for profile in profiles:
            profile_link = trim_full_link(profile.get_attribute("href"))
            profiles_data.update({profile_link: {"name": profile.get_attribute("title"),
                                                 "fb_id": get_fb_id(profile, profile_link)}})

        users = {u.link: u for u in DBSession.query(User).filter(User.link.in_(profiles_data.keys())).all()}
        users_has_post_like = DBSession.query(Like.user_id).filter(Like.post == post).all()

        added_likes = 0
        for key in profiles_data:
            if key not in users:
                user = User(name=profiles_data[key]['name'], link=key, fb_id=profiles_data[key]['fb_id'])
                subtasks.append(save_personal_page_subtask(post, user))
                DBSession.add(user)
            else:
                user = users[key]

            if (user.id,) not in users_has_post_like:
                like = Like(post=post, user=user, like_type=like_type)
                DBSession.add(like)
                added_likes += 1

        return added_likes

    logger.log("Saving likes...")

    added_normal_likes = save_like(get_likes(browser, 'reaction_profile_browser1'), like_type=LikeType.like)
    added_love_likes = save_like(get_likes(browser, 'reaction_profile_browser2'), like_type=LikeType.love)
    added_haha_likes = save_like(get_likes(browser, 'reaction_profile_browser4'), like_type=LikeType.haha)
    added_wow_likes = save_like(get_likes(browser, 'reaction_profile_browser3'), like_type=LikeType.wow)
    added_sad_likes = save_like(get_likes(browser, 'reaction_profile_browser7'), like_type=LikeType.sad)
    added_angry_likes = save_like(get_likes(browser, 'reaction_profile_browser8'), like_type=LikeType.angry)

    logger.log("Added to database {} normal, {} love, {} haha, {} wow, {} sad, {} angry"
               .format(added_normal_likes, added_love_likes, added_haha_likes, added_wow_likes, added_sad_likes, added_angry_likes))

    DBSession.commit()

    logger.log("Clause likes tab")


def get_likes(browser, name):
    try:
        likes = browser.find_elements(By.XPATH, f"//ul[@id='{name}']//a[contains(@href,'fref=') and not(@data-gt)]//span/i/../../../..")
    except Exception as e:
        logger.exception("Likes", e)
        likes = []
    return likes


def trim_like_url(link):
    return link.split('&av=')[0]
