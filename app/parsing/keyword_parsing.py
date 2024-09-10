import re
import json
import traceback
import os
from datetime import datetime
from time import sleep
from dateutil import parser
from random import randint

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException


from .. import logger
from ..authentication.browser import close_tab, open_tab
from ..database.models import Content, Post, PostStat, User, Photo, auto_post, auto_share
from ..database import DBSession
from ..database.posts_dao import get_post_by_fb_id, update_post_stat, get_post_by_date_and_task_id
from ..database.users_dao import get_user_by_link, get_user_by_fb_id
from ..utils.count_utils import string_count_to_int
from ..utils.datetime_utils import parse_datetime
from ..utils.url_utils import get_param
from ..utils.user_utils import trim_full_link
from .common_parsing import get_fb_id, scroll_till_retro, scroll_till_the_end, get_date_time_from_post
from .likes_parsing import trim_like_url
from ..constants import *


def parse_keyword(credentials, browser, task_keyword):  
    browser.maximize_window()
    def get_keyword_posts(browser, retry=False):
        try:
            logger.log("Searching posts")
            wait_time = 7 if not retry else 30
            return WebDriverWait(browser, wait_time).until(
                ec.presence_of_all_elements_located(
                    (By.CSS_SELECTOR,  "div[class='x1n2onr6 x1ja2u2z']>div>div>div[aria-posinset]"))
            )
        except Exception as e:
            if not retry:
                logger.log("try to scroll up")
                browser.execute_script("window.scrollTo(0,0)")
                sleep(2)
                return get_keyword_posts(browser, True)
            else:
                logger.exception("not found posts", e)
        return []

    def remove_from_scope_keyword(browser, scrolled_posts):
        """
        Function to remove specific Facebook posts from the browser.

        Parameters:
        browser : webdriver instance
            The browser instance to execute the JavaScript.
        scrolled_posts : list
            A list of post elements to be removed.
        """
        try:
            post_selectors = []
            for post in scrolled_posts:
                post_id = post.get_attribute("id")
                if post_id:
                    post_selectors.append(f"div[id='{post_id}']")
                else:
                    # Fallback if no id, create a unique selector based on other attributes
                    post_class = post.get_attribute("class")
                    if post_class:
                        post_selectors.append(f"div[class='{post_class}']")

            if post_selectors:
                # Join the selectors into a JavaScript array format
                selectors_string = "[" + ", ".join([f'"{selector}"' for selector in post_selectors]) + "]"
            
                # JavaScript to remove posts
                script = f"""
                // Function to remove specific Facebook posts
                function removeSpecificPosts(postSelectors) {{
                    postSelectors.forEach(selector => {{
                        const post = document.querySelector(selector);
                        if (post) {{
                            post.remove();
                        }}
                    }});
                }}
            
                // List of post selectors to remove
                const postSelectors = {selectors_string};
            
                // Run the function to remove the posts
                removeSpecificPosts(postSelectors);
                """
            
                # Execute the JavaScript code
                browser.execute_script(script)
                print(f'Number of posts removed: {len(scrolled_posts)}')
            else:
                print('No posts found to remove.')

        except Exception as e:
            print(f"An error occurred: {e}")

    source_url = "https://www.facebook.com/search/posts/?q=" + task_keyword.keyword
    browser.get(source_url)    
    sleep(3)
    browser.execute_script("window.open('');")
    logger.log(f'Get {source_url}')     

    if browser.current_url != source_url:
        logger.log('Current url was redirected from {} to {}'.format(source_url, browser.current_url))

    scroll_till_retro(browser, task_keyword.task, get_keyword_posts, get_date_time_from_post, parse_post_keyword,
                      remove_from_scope_keyword)


def parse_post_keyword(browser, post, task_id):
    def get_fb_post_id(browser, post):
        try:
            logger.log("Getting post id")
            #source post id rebuild in this function
            status_link = post.find_element(By.CSS_SELECTOR, "div[class='xu06os2 x1ok221b']>span>span>span>span>a[class][role='link'][tabindex='0'], div[class='xu06os2 x1ok221b']>span>div>span>span>a[class][role='link'][tabindex='0']")
            actions = ActionChains(browser)
            actions.move_to_element(status_link).perform()
            link = status_link.get_attribute("href")
            #logger.log(f"Link found: {link}.")
            post_id = extract_id_from_link(link)
            logger.log("Post_id: {}.".format(post_id))
            return post_id
        except:
            logger.log("Post id not found")
        return None
    
    def extract_id_from_link(link):
        """Extracts the post_id from the URL."""
        try:
            status = "NA"
            if "posts/" in link:
                status = link.split('/')[5].split('?')[0]
            elif "photos/" in link:
                status = link.split("/")[-2]
            elif "/videos/" in link:
                status = link.split("/")[5]
            elif "/reel/" in link:
                status = link.split("/")[4]
            elif "/groups/" in link:
                status = link.split("/")[4]
            elif "fbid=" in link:
                status = link.split("=")[1].split("&")[0]
            elif "group" in link:
                status = link.split("/")[6]
            return status
        except IndexError:
            return "NA"
        except Exception as ex:
            logger.exception(f'Error at extract_id_from_link: {ex}')
            return "NA"
        
    def get_user(post):
        user = User()
        try:
            logger.log("Getting user data")            
            try:
                user_element_1 = post.find_element(By.CSS_SELECTOR, 'span>a>strong>span[class], span>a>span[class]')
                user.name = user_element_1.text
                if not user.name:
                    raise NoSuchElementException
            except NoSuchElementException:
                user_element_1 = post.find_element(By.CSS_SELECTOR, 'strong>span[class]>a>span>span')
                user.name = user_element_1.text
            try:
                user_element_2 = post.find_element(By.CSS_SELECTOR, "span[class='xt0psk2']>a[role='link'][tabindex='0'], span>a[role='link'][tabindex='0']")
                user.link = trim_full_link(user_element_2.get_attribute("href"))
                if not user.link:
                    raise NoSuchElementException
            except NoSuchElementException:
                user_element_2 = post.find_element(By.CSS_SELECTOR, "strong>span>a")
                user.link = trim_full_link(user_element_2.get_attribute("href"))                
            
            user.fb_id = extract_user_id_from_link(user.link)            
            logger.log("User name: {} - link {} - fb_id: {}".format(user.name, user.link, user.fb_id))

            saved_user = get_user_by_fb_id(user.fb_id)
            if saved_user:
                return saved_user

            else:
                return user            
        except:
            logger.log("User not found")
    
    def extract_user_id_from_link(link):
        """Extracts the post_id from the URL."""
        try:
            status = "NA"
            if "profile.php?id" in link:
                status = link.split("=")[1].split("&")[0]
            else:
                status = link.split("/")[3].split("?")[0]        
            return status
        except IndexError:
            return "NA"
        except Exception as ex:
            logger.exception(f'Error at extract_id_from_link: {ex}')
            return "NA"
    
    def get_text(post):
        logger.log("Getting post text")
        sleep(3)
        see_more_button_click(post)
        try:
            post_root = WebDriverWait(post, 10).until(
                ec.presence_of_element_located((By.CSS_SELECTOR, 'div[data-ad-preview="message"]'))
            )
            post_text_elements = post_root.find_elements(By.CSS_SELECTOR, 'div[dir="auto"]')
            post_text = "\n".join([element.text for element in post_text_elements])
            logger.log("Post text: \033[34m{}\033[0m".format(post_text))
            return post_text
        except Exception as e:
            logger.log(f"Text not found: {e}")
        return None
    
            
    def see_more_button_click(post):
        try:
            more_link = post.find_element(By.CSS_SELECTOR, 'div[dir="auto"] > div[role]')
            logger.log("Click see more button")
            browser.execute_script("arguments[0].click();", more_link)
        except NoSuchElementException:
            logger.log("No 'See More' button found, proceeding without clicking.")
            #pass
            
    

    def get_videos(browser, post):
        try:
            logger.log("Getting post video")
            post_video_els = post.find_elements(By.XPATH, ".//video")

            result_video_list = []
            logger.log("Post count video {}".format(len(post_video_els)))
            for post_video_el in post_video_els:
                logger.log('Start sleeping for 2 seconds...')
                sleep(2)
                actionChains = ActionChains(browser)
                actionChains.context_click(post_video_el).perform()
                logger.log("Post link video {}".format(browser.current_url))

                video_link = WebDriverWait(browser, 2).until(
                    ec.presence_of_element_located((By.XPATH, './/*[text()=\'Copy video URL at current time\']/..'))
                ).get_attribute('value')

                actionChains.send_keys(Keys.ESCAPE)
                browser.execute_script("var video_link=document.querySelector('span[value=\"" + video_link + "\"]');"
                                                                                                             "if(video_link){video_link.remove();}")
                result_video_list.append(video_link)

            return result_video_list
        except Exception as e:
            actionChains = ActionChains(browser)
            actionChains.send_keys(Keys.ESCAPE)
            traceback.print_exc()
            logger.log("Video doesn't found")
        return []

    def get_photos(post):
        try:
            logger.log("Getting post photo")
            photo_links = post.find_elements(By.CSS_SELECTOR, "div[class='x10l6tqk x13vifvy'] > img[referrerpolicy]")
            result_photo_list = []
            for photo_link in photo_links:
                src = photo_link.get_attribute("src")
                if ".png" not in src and "www.facebook.com" not in src:
                    logger.log("Post link photo {}".format(src))
                    result_photo_list.append(src)
                else:
                    logger.log("Filtered out photo {}".format(src))

            return result_photo_list
        except:
            logger.log("Photo doesn't found")
        return []

    def get_likes_link(fb_post_id):
        try:
            logger.log("Getting likes link")            
            link = FACEBOOK_URL_MOBILE_LIKE_LINK + fb_post_id
            logger.log("Link: {}".format(link))
            return link
        except:
            logger.log("Likes count doesn't found")
        return None
    
    def get_likes_count(post):
        """Функция для сбора количества лайков под постом."""
        try:
            logger.log("Getting likes count")
            likes = post.find_element(By.XPATH, ".//span[@class='x1e558r4']").text
            likes_count = string_count_to_int(likes)
            logger.log("Likes count: {}".format(likes_count))
            return str(likes_count)
        except:
            logger.log("Likes count doesn't found")
        return None

    def extract_comments_str(post, fb_post_id):
        """Извлечение из поста элемента с количеством комментариев."""
        # TODO: refactor
        logger.log("WOW THIS IS ACTUALLY WORKS")
        COMMENTS_COUNT_PATTERNS = (
            ".//form//a[contains(@href,'posts/{0}') and @role='button']",
            ".//form//a[contains(@href,'story_fbid') and @role='button']",
            ".//form//a[contains(@href,'photo.php?fbid=') and @role='button']",
        )
        for pattern in COMMENTS_COUNT_PATTERNS:
            try:
                return post.find_element(
                    By.XPATH,
                    pattern.format(fb_post_id)
                ).text
            except:
                continue
        return None

    def get_comments_count_original(post, fb_post_id):
        """Функция для сбора количества комментариев под постом."""
        # TODO: fix issue
        logger.log("Getting comments count for post_id: {0}".format(fb_post_id))

        #comments_str = extract_comments_str(post, fb_post_id)
        try:
            logger.log("Getting comments count")
            comments = post.find_element(By.XPATH, ".//article/footer//a//div/div[2]/span[1]").text
            logger.log("Comments retrieved: {}".format(comments))
            comments_count = string_count_to_int(comments)
            logger.log("Comments count: {}".format(str(comments_count)))
            return str(comments_count)
        except:
            logger.log("Comments count doesn't found")
        return None        
    def get_comments_count(post):
        try:
            logger.log("Getting Comments count")
            comments = post.find_element(By.XPATH, ".//span[contains(text(), 'comment')]").text
            logger.log("Comments retrieved: {}".format(comments))
            comments_count = comments.split(" ")[0]
            comments_count = string_count_to_int(comments_count)
            logger.log("Comments count: {}".format(str(comments_count)))
            return str(comments_count)
        except:
            logger.log("Comments count doesn't found")
        return None 
    
     
    def get_post_link(fb_post_id):
        try:
            logger.log("Getting post_link")
            link = FACEBOOK_URL_WWW + fb_post_id
            logger.log("Link: {}".format(link))
            return link
                  
        except:
            logger.log("Link doesn't found")
        return None

    def get_shares_count(post):
        try:
            logger.log("Getting shares count")
            shares = post.find_element(By.XPATH, ".//span//div//span[contains(text(), 'share')]").text            
            logger.log("Shares retrieved: {}".format(shares))
            shares_count = shares.split(" ")[0]
            shares_count = string_count_to_int(shares_count)
            logger.log("Shares count: {}".format(str(shares_count)))
            return str(shares_count)
           
        except:
            logger.log("Shares count doesn't found")
        return None
    
    def get_views_count(post):
        try:
            #logger.log("Getting views count")            
            video_post = post.find_element_by_css_selector("span > a[aria-label][role='link']")
            if video_post:
                Video_url = video_post.get_attribute('href')
                Video_url = Video_url.split('?')[0]
#                 Video_url = json.loads(Video_url)
#                 Video_url = Video_url["videoURL"]
                logger.log("video url is {}".format(Video_url))                
                views = get_views(Video_url)
            return str(views)
        except:
            logger.log("Not video post")
        return None
    
    def get_views(url):
        logger.log("Getting views count")
        views_count = 0
        try:            
            #browser.execute_script("window.open('');")
            browser.switch_to.window(browser.window_handles[1])
            browser.get(url)
            sleep(1)
            try:
                live_view = browser.find_element(By.XPATH, "//div[@aria-label= 'Leave a comment']")
                live_view.click()
                sleep(1)
            except:
                logger.log(f"Error clicking the element")
            views = WebDriverWait(browser, 10).until(
                ec.presence_of_element_located((By.XPATH, "//div[contains(@class, 'x8cjs6t')]//div//div//div//span[contains(text(),'views')]|//div[@class='x1n2onr6']//div//div//div//span//span//div//div//span[contains(@class,'x193iq5w')]|//div[contains(@class, 'x8cjs6t x13fuv20 x178xt8z')]//span[contains(text(), 'lay')]|//i[@class='x1b0d499 x1d69dk1']/../../../../span[@class='_26fq']//div//div//span")))        
            views_count = (views.text).split(" ")[0]
            views_count = string_count_to_int(views_count)
            logger.log("Views count: {}".format(str(views_count)))
            #browser.close()
        except:
            logger.log("Views couldn't be parsed")                                                                     
        
        browser.switch_to.window(browser.window_handles[0])
        return str(views_count)

    def get_repost_id(post):
        try:
            logger.log('Getting repost id by data-testid="story-subtitle"')
            story_subtitles = post.find_elements(By.XPATH, ".//div[@data-testid='story-subtitle']//a")
            if len(story_subtitles) == 2:
                repost = story_subtitles[1].get_attribute('href')
                logger.log("repost link: {}".format(repost))
                fb_repost_id = None
                try:
                    fb_repost_id = repost.split('fbid=')[1].split('&')[0]
                except:
                    logger.log("Couldn't parse repost_fb_id from fb_id")

                try:
                    fb_repost_id = repost.split('/permalink/')[1].split('/')[0]
                except:
                    logger.log("Couldn't parse repost_fb_id from permalink")

                try:
                    fb_repost_id = repost.split('/posts/')[1].split('/')[0]
                except:
                    logger.log("Couldn't parse repost_fb_id from posts")

                if not fb_repost_id:
                    return None, repost

                logger.log("repost_id found: {}".format(fb_repost_id))
                return fb_repost_id, repost
        except:
            logger.log("fb repost id coudn't parse")

        try:
            logger.log("Getting repost id by permalink")
            repost = post.find_element(By.XPATH, ".//a[contains(@href, '/permalink/')]").get_attribute('href')
            if not repost:
                logger.log("no repost found")
                return None, None

            logger.log("repost link: {}".format(repost))
            fb_repost_id = None
            try:
                fb_repost_id = repost.split('/permalink/')[1].split('/')[0]
            except:
                logger.log("Couldn't parse repost_fb_id")

            if not fb_repost_id:
                return None, repost

            logger.log("repost_id found: {}".format(fb_repost_id))
            return fb_repost_id, repost
        except:
            logger.log("fb repost id coudn't parse")
        return None, None

    """def get_post_object(post):
        fb_post_id = get_fb_post_id(browser, post)
        if fb_post_id:
            post_obj = get_post_by_fb_id(fb_post_id)
            if not post_obj:
                return Post(fb_post_id=fb_post_id, fb_post_id_new=fb_post_id)
            else:
                return post_obj
        else:
            logger.log("FB post id not found")

    post_obj = get_post_object(browser, post)"""
    def get_post_object(browser, post, task_id):
        fb_post_id = get_fb_post_id(browser, post)
        logger.log("Task_id: {}".format(task_id))
        if fb_post_id:
            post_obj = get_post_by_fb_id(fb_post_id)
            if not post_obj:
                dt = get_date_time_from_post(browser, post)
                post_obj = get_post_by_date_and_task_id(dt, task_id)                
            if not post_obj:
                logger.log("\033[92mPost is New\033[0m")
                return Post(fb_post_id=fb_post_id, fb_post_id_new=fb_post_id)
            else:
                return post_obj
        else:
            logger.log("FB post id not found")       

    post_obj = get_post_object(browser, post, task_id)

    if not post_obj:
        return None

    stat = PostStat(likes=get_likes_count(post),                    
                    comments=get_comments_count(post),
                    shares=get_shares_count(post),
                    views = get_views_count(post))
    if not post_obj.id:
        post_obj.fb_post_link = get_post_link(post_obj.fb_post_id)
        post_obj.fb_post_link_likes = get_likes_link(post_obj.fb_post_id)
        post_obj.user = get_user(post)
        post_obj.date = format(get_date_time_from_post(browser, post))
        post_obj.content = Content(text=get_text(post))
        #post_obj.content = Content(text=get_comment_text(post))
        post_obj.last_time_updated = datetime.now().isoformat()
        post_obj.task_id = task_id
        post_obj.stat = stat

#         fb_repost_id, fb_repost_link = get_repost_id(post)
#         post_obj.fb_repost_id = fb_repost_id
#         post_obj.fb_repost_link = fb_repost_link

#         for v_link in get_videos(browser, post):
#             Video(content=post_obj.content, video_link=v_link)

        for p_link in get_photos(post):
            Photo(content=post_obj.content, photo_link=p_link)
    else:
        update_post_stat(post_obj, stat)

    return post_obj