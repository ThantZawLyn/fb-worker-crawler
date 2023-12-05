# likes_parsing.py

import re

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
#     post_fb_link = post.fb_post_link
#     x = post_fb_link.replace("www", "m", 1)
#     browser.get(trim_like_url(post.fb_post_link_likes))
    browser.get(post.fb_post_link)
    
    try:
        WebDriverWait(browser, 10).until(
            ec.presence_of_element_located((By.CSS_SELECTOR, "a[href*=reaction]"))
        )
        browser.execute_script("document.querySelector('a[href*=reaction]').click()")
        logger.log("All likes are opened")
    except Exception as e:
        logger.exception("Likes button not found or canot click.")
        
    browser.implicitly_wait(10)
    
#     def get_fb_id(user_element, link):
#         try:
#             if "profile.php" in link:
#                 fb_id = get_param(link, "id")
#                 logger.log("FB_id found: {}".format(fb_id))
#                 return fb_id
#             else:
#                 fb_id = link.split("/")
#                 fb_id= fb_id[3].strip()
#                 logger.log("FB_id found: {}".format(fb_id))
#                 return fb_id
#         except:
#             logger.log("FB_id not found in attribute data-hovercard")
#             fb_id = None
#             return fb_id

    subtasks = []
    def save_like(profiles, like_type):

        profiles_data = {}
        for profile in profiles:
            profile_link = trim_full_link(profile.get_attribute("href"))
            profiles_data.update({profile_link: {"name": profile.text,
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
#     logger.log("Saving likes...")
    
    added_normal_likes = save_like(get_likes(browser, '{"reactionID":1635855486666999}', 1635855486666999, "Like"), like_type=LikeType.like)
#     logger.log("normal_likes= {}".format(added_normal_likes))
    added_love_likes = save_like(get_likes(browser, '{"reactionID":1678524932434102}', 1678524932434102,"Love"), like_type=LikeType.love)
    added_haha_likes = save_like(get_likes(browser, '{"reactionID":115940658764963}', 115940658764963,"haha"), like_type=LikeType.haha)
    added_wow_likes = save_like(get_likes(browser, '{"reactionID":478547315650144}', 478547315650144,"wow"), like_type=LikeType.wow)
    added_sad_likes = save_like(get_likes(browser, '{"reactionID":908563459236466}', 908563459236466,"sad"), like_type=LikeType.sad)
    added_angry_likes = save_like(get_likes(browser, '{"reactionID":444813342392137}', 444813342392137,"angry"), like_type=LikeType.angry)
    logger.log("Saving likes...")
    logger.log("Added to database {} normal, {} love, {} haha, {} wow, {} sad, {} angry"
               .format(added_normal_likes, added_love_likes, added_haha_likes, added_wow_likes, added_sad_likes, added_angry_likes))
    
    DBSession.commit()
def see_more_like(browser,name):
    try:
        logger.log_alive()
        logger.log("Search See More like button")
        more_button = WebDriverWait(browser, 10).until(ec.presence_of_element_located((By.XPATH,f"//div[@id='reaction_profile_pager{name}']//div[@class='title mfsm fcl']")))            
        more_button.click()            
    except Exception as e:
        logger.log("No see more button found. Finish clicking see more button.")
        return False
    return True
    
def check_error_see_more_like(browser,name):
    try:
        check_buttonee = WebDriverWait(browser, 10).until(
        ec.presence_of_element_located((By.XPATH,
                                                 f"//div[@id='reaction_profile_pager{name}']//div[@class='title mfsm fcl']/preceding::div[@class='_1uja'][1]//div[@class='_4mn c']//a")))
        check_user_link = check_buttonee.get_attribute("href")
#         check_user_id = check_error_id(browser, check_user_link)
#                 logger.log("FB_id found: {}".format(check_user_link))
        return check_user_link
    except Exception as e:
        logger.log("No See More like.")
        return None
            
def get_likes(browser, name1, name2, react):
    try:
 #       name1 = '{"reactionID":1678524932434102}'
        logger.log("name1 : ".format(name1))
        gg = f".//span[@data-store='{name1}']"
        logger.log(" x path name : ".format(gg))
        reaction_button = browser.find_element(By.XPATH,gg)
        logger.log(" x path found ")
 #       reaction_button = browser.find_element(By.XPATH,f".//span[@data-store='{name1}']")
        sleep(randint(3, 7))
        reaction_button.click()
    except:
        logger.log(" No {} reaction on post.".format(react))
        likes = []
        return likes
    sleep(randint(3, 7))
    
    check_error_likeview = check_error_see_more_like(browser,name2)
    check_error_likeview2 = ""
    count_error = 1
    while see_more_like(browser,name2) and count_error==1:
        sleep(randint(3, 7))
        check_error_likeview2 = check_error_see_more_like(browser,name2)           
        if(check_error_likeview == check_error_likeview2):
            count_error = 2
        check_error_likeview = check_error_likeview2
        if not see_more_like(browser,name2) or not count_error ==1:
            break
                
    try:
#         i = 0
        likes = browser.find_elements(By.XPATH,f"//div[@id='reaction_profile_browser{name2}']//div[@class='_4mn c']//a")
#         for ff in likes:
#             i += 1
#         logger.log("like count = {}".format(i))    
        return likes
    except:
        logger.log("Like User cannot get.")
        likes = []
        return likes
        

def trim_like_url(link):
    return link.split('&av=')[0]