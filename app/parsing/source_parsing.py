import re
import json
import traceback
import os
from datetime import datetime, timedelta
from time import sleep
from random import randint

#from selenium.webdriver import ActionChains
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec

from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException

from .common_parsing import scroll_till_retro, get_date_time_from_post, get_fb_id
from .likes_parsing import trim_like_url
from ..database.posts_dao import get_post_by_fb_id, update_post_stat, update_task_id, get_post_by_date_and_task_id
from ..utils.count_utils import string_count_to_int
from ..utils.user_utils import trim_full_link
from .. import logger
from ..constants import *
from ..database import DBSession
from ..database.models import Post, Content, User, PostStat, Photo, Video, auto_post, auto_share, auto_report 
from ..database.users_dao import get_user_by_link, get_user_by_fb_id


def parse_source(credentials, browser, task_source):
    browser.maximize_window()    
    def get_source_posts(browser, retry=False):
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
                browser.execute_script("window.scrollTo(0,document.body.scrollHeight)")
                sleep(7)
                return get_source_posts(browser, True)
            else:
                logger.exception("not found posts", e)
        return []
        
    
    def post_to_facebook(credentials, browser, auto_post_entry):
        # Fetch the latest post_text and photo_path from the auto_post table
        #post_data = DBSession.query(auto_post).order_by(auto_post.id.desc()).first()
        logger.log("Trying auto post...")
        post_text = auto_post_entry.text
        if post_text:
            post_text = post_text + ' '
        logger.log(f"Post text: {post_text}")
        base_dir = "/usr/src/app/photos/"
        if auto_post_entry.path:
            # Assuming photo paths are comma-separated
            photo_paths = [os.path.join(base_dir, path.strip()) for path in auto_post_entry.path.split(',')]
        else:
            photo_paths = [] 
        logger.log("Photo path: {}". format(photo_paths))
        
        mp4_paths = [path for path in photo_paths if ".mp4" in path]
        logger.log("Filtered .mp4 paths: {}".format(mp4_paths))
        for path in mp4_paths:
            try:
                size = os.path.getsize(path)
                logger.log("File: {} Size: {} bytes".format(path, size))
            except:
                logger.log("Size not found: {}".format(path))

        try:
            link = "https://www.facebook.com/me"
            browser.get(link)
            sleep(5)

            # Locate the "What's on your mind?" div and click it
            logger.log("Clicking post box")
            post_box = WebDriverWait(browser, 30).until(
                ec.presence_of_element_located((By.XPATH, "//span[contains(text(),\"What's on your mind\")]")))
            post_box.click()          
            
            logger.log("Sending text")
            if post_text:
                # Wait for the text area to appear and be interactable
                text_area = WebDriverWait(browser, 30).until(
                    ec.element_to_be_clickable((By.XPATH, "//div[@class='x78zum5 xl56j7k']//div[@role='textbox']")))
                sleep(1)

                # Type the user's message
                text_area.send_keys(post_text)
                sleep(7)
            
            logger.log("Uploading photo")
            # Check if there are photo paths provided
            if photo_paths and any(photo_paths):
                # Locate the photo box and click it
                photo_box = WebDriverWait(browser, 30).until(
                    ec.presence_of_element_located((By.CSS_SELECTOR, "div[class='x6s0dn4 x78zum5 xl56j7k x1n2onr6 x5yr21d xh8yej3']>img"))
                )
                photo_box.click()

                # Locate the photo upload button (file input element)
                photo_button = WebDriverWait(browser, 30).until(
                    ec.presence_of_element_located((By.XPATH, "//input[@type='file' and @accept='image/*,image/heif,image/heic,video/*,video/mp4,video/x-m4v,video/x-matroska,.mkv']"))
                )

                # Create a single string of file paths separated by newlines
                file_paths_string = "\n".join(photo_paths)

                # Upload photos by sending file paths to the photo input
                photo_button.send_keys(file_paths_string)

                # Wait for photos to be uploaded
                sleep(10)  # Adjust this time depending on your network speed and photo size
            
            logger.log("Changing privacy")
            to_public = WebDriverWait(browser, 30).until(
                ec.element_to_be_clickable((By.XPATH, "//div[@class='x1n2onr6']//i[@class='x1b0d499 xep6ejk']")))
            to_public.click()
            sleep(3)
            
            to_public_anyone = WebDriverWait(browser, 30).until(
                ec.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Anyone')]")))
            to_public_anyone.click()
            sleep(3)
            
            to_public_done = WebDriverWait(browser, 30).until(
                ec.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Done')]")))
            to_public_done.click()
            sleep(3)
            if mp4_paths:
                logger.log("Waiting for video uploading...")
                sleep(45)
                if size>5242880:
                    logger.log("Still Waiting for video uploading...More than 5MB")
                    sleep(45)
                    if size>10485790:
                        logger.log("Still Waiting for video uploading...More than 10MB")
                        sleep(45)
                        if size>20971520:
                            logger.log("Still Waiting for video uploading...More than 20MB")
                            sleep(45)
                            if size>31457280:
                                logger.log("Still Waiting for video uploading...More than 30MB")
                                sleep(45)

            # Click the post button
            logger.log("Final click to post")
            post_button = WebDriverWait(browser, 30).until(
                ec.element_to_be_clickable((By.XPATH, "//div[@aria-label='Post'] | //div[@aria-label='Next'] ")))
            post_button.click()
            sleep(3)

            try:
                post_button_2 = WebDriverWait(browser, 30).until(ec.element_to_be_clickable((By.XPATH, "//div[@aria-label='Post']")))
                post_button_2.click()
            except:
                pass
                    
            if mp4_paths:
                sleep(10)
            # Wait for a few seconds to ensure the post is made
            sleep(10)
            credentials.auto_post_id = auto_post_entry.id  
            DBSession.commit()
            logger.log("Auto post : Done....")
        except:
            logger.log("ပို့စ်တင်ခြင်း မအောင်မြင်ပါ")
    
    credential_auto_post_id = credentials.auto_post_id
    logger.log(f"Credential acc_id: {format(credentials.account_id)}")
    auto_post_entry = DBSession.query(auto_post).filter(auto_post.id > credential_auto_post_id).order_by(auto_post.id.asc()).first()

    if auto_post_entry:
        post_to_facebook(credentials, browser, auto_post_entry)
        
    else:
        logger.log("ပို့စ်တင်ရန်မရှိသေးပါ")
        
    """def share_post_to_feed(credentials, browser, auto_share_entry):
        logger.log("Proceeding to share...")
        try:
                   
            share_text = auto_share_entry.text
            if share_text:
                share_text = share_text + ' '
            share_link = auto_share_entry.link

            # Navigate to the share link
            browser.get(share_link)
            sleep(3)

            # Locate and click the 'Share' button
            share_box = WebDriverWait(browser, 30).until(
                ec.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Share')]"))
            )
            share_box.click()
            sleep(5)

            try:
                share_to_feed_box = WebDriverWait(browser, 10).until(
                    ec.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Share to Feed')]"))
                )
                share_to_feed_box.click()
                sleep(5)
            except:
                print("'Share to Feed' option not found, continuing with the rest of the process.")

            if share_text:
                logger.log("Importing text...")
                # Locate the text area and type the share text
                text_area = WebDriverWait(browser, 30).until(
                    ec.element_to_be_clickable((By.XPATH, "//div[@class='x78zum5 xl56j7k']//div[@role='textbox'] | //div[@class='xvq8zen x19f6ikt']//div[@role='textbox']"))
                )
                sleep(1)
                text_area.send_keys(share_text)
                sleep(2)
                
            logger.log("Changing privacy")   
            to_public = WebDriverWait(browser, 30).until(
                ec.element_to_be_clickable((By.XPATH, "//div[@class='x1n2onr6']//i[@class='x1b0d499 xep6ejk']")))
            to_public.click()
            sleep(3)
            
            to_public_anyone = WebDriverWait(browser, 30).until(
                ec.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Anyone')]")))
            to_public_anyone.click()
            sleep(3)
            
            to_public_done = WebDriverWait(browser, 30).until(
                ec.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Done')]")))
            to_public_done.click()
            sleep(3)

            # Locate and click the final 'Share' button
            share_final_box = WebDriverWait(browser, 30).until(
                ec.presence_of_element_located((By.XPATH, "//div[@role='none']//span//span[contains(text(), 'Share')]"))
            )
            share_final_box.click()
            sleep(15)
            credentials.share_id = auto_share_entry.id  
            DBSession.commit()
            logger.log("Share Done.....")
    
        except:
            logger.log("Share ပြုလုပ်ခြင်း မအောင်မြင်ပါ")
        
    credential_auto_share_id = credentials.share_id
    auto_share_entry = DBSession.query(auto_share).filter(auto_share.id > credential_auto_share_id).order_by(auto_share.id.asc()).first()

    if auto_share_entry:
        share_post_to_feed(credentials, browser, auto_share_entry)
        
    else:
        logger.log("Share ပြုလုပ်ရန်ပို့စ် မရှိသေးပါ")"""
    
    
    def report_post(credentials, browser, auto_report_entry):
        logger.log("Proceeding report...")
        try:
            report_link = auto_report_entry.link
            report_option_1 = auto_report_entry.option_1
            report_option_2 = auto_report_entry.option_2
            report_option_3 = auto_report_entry.option_3

            # Navigate to the report link
            browser.get(report_link)
            sleep(3)

            report_box = WebDriverWait(browser, 30).until(
                ec.presence_of_element_located((
                    By.XPATH, 
                    "//div[@class='x78zum5 x1qughib']//div[@class='x6s0dn4 x78zum5 xl56j7k x1608yet xljgi0e x1e0frkt'] | "
                    "//div[@class='x78zum5']//div[@class='x6s0dn4 x78zum5 xl56j7k x1608yet xljgi0e x1e0frkt'] | "
                    "//div[@aria-label='Actions for this post'] | "
                    "//div[@aria-label='More']")))
            report_box.click()
            sleep(5)
            #//div[@class='x78zum5']//div[@class='x6s0dn4 x78zum5 xl56j7k x1608yet xljgi0e x1e0frkt']
            #//div[@class='x78zum5 x1qughib']//div[@class='x6s0dn4 x78zum5 xl56j7k x1608yet xljgi0e x1e0frkt']

            report_post = WebDriverWait(browser, 30).until(
                ec.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Report post')]|//span[contains(text(), 'Report video')]|//span[contains(text(), 'Report')]"))
            )
            report_post.click()
            sleep(5)
            logger.log("Choosing report option...")
            if report_option_1:
                option_box_1 = WebDriverWait(browser, 30).until(
                ec.presence_of_element_located((By.XPATH, f"//span[contains(text(), '{report_option_1}')]")))
                option_box_1.click()
                sleep(5)
                if report_option_2:
                    option_box_2 = WebDriverWait(browser, 30).until(
                    ec.presence_of_element_located((By.XPATH, f"//span[contains(text(), '{report_option_2}')]")))
                    option_box_2.click()
                    sleep(5)
                    if report_option_3:
                        option_box_3 = WebDriverWait(browser, 30).until(
                        ec.presence_of_element_located((By.XPATH, f"//span[contains(text(), '{report_option_3}')]")))
                        option_box_3.click()
                        sleep(5)
                Submit_box = WebDriverWait(browser, 30).until(
                ec.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Submit')] | //span[contains(text(), 'Next')] | //span[contains(text(), 'Done')]")))
                Submit_box.click()
                sleep(5)
                try:
                    Next_box = WebDriverWait(browser, 5).until(
                        ec.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Next')] | //span[contains(text(), 'Done')]"))
                    )
                    Next_box.click()
                    sleep(5)
                except:
                    logger.log("Next button not found, moving on.")

                # Third action: Done (if present)
                try:
                    Done_box = WebDriverWait(browser, 5).until(
                        ec.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Done')]"))
                    )
                    Done_box.click()
                    sleep(5)
                except:
                    logger.log("Done button not found, moving on.")
                credentials.report_id = auto_report_entry.id  
                DBSession.commit()
                logger.log("Report Done......")
            else:
                print("Report Option မတွေ့ပါ")
        except:
            logger.log("Report ပြုလုပ်ခြင်း မအောင်မြင်ပါ")
    credential_auto_report_id = credentials.report_id
    auto_report_entry = DBSession.query(auto_report).filter(auto_report.id > credential_auto_report_id).order_by(auto_report.id.asc()).first()

    if auto_report_entry:
        report_post(credentials, browser, auto_report_entry)
        
    else:
        logger.log("Report ပြုလုပ်ရန် မရှိသေးပါ")
        
        
    def remove_from_scope_source(browser, scrolled_posts):
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


    source_url = "https://www.facebook.com/" + task_source.source_name 
    browser.get(source_url)
    browser.execute_script("window.scrollBy(0, 1000);")    
    sleep(3)
    browser.execute_script("window.open('');")
    browser.switch_to.window(browser.window_handles[0])
    #browser.maximize_window()
    #browser.refresh()
    logger.log(f'Get {source_url}')    

    if browser.current_url != source_url:
        logger.log('Current url was redirected from {} to {}'.format(source_url, browser.current_url))

    scroll_till_retro(browser, task_source.task, get_source_posts, get_date_time_from_post, parse_source_post,
                      remove_from_scope_source)


def parse_source_post(browser, post, task_id):
    def get_fb_post_id(browser, post):
        try:
            logger.log("Getting post id..NLA")
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
            user_element_1 = post.find_element(By.CSS_SELECTOR, 'span>a>strong>span[class], span>a>span[class]')
            user.name = user_element_1.text
            user_element_2 = post.find_element(By.CSS_SELECTOR, "span[class='xt0psk2']>a[role='link'][tabindex='0'], span>a[role='link'][tabindex='0']")
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
        sleep(1)
        see_more_button_click(post)
        try:
            post_root = WebDriverWait(post, 10).until(
                ec.presence_of_element_located((By.CSS_SELECTOR, 'div[data-ad-preview="message"]'))
            )
            post_text_elements = post_root.find_elements(By.CSS_SELECTOR, 'div[dir="auto"]')
            post_text = "\n".join([element.text for element in post_text_elements])
            if len(post_text) > 16384:
                logger.log(f"Post text is longer than 16384 characters. Truncating.")
                post_text = post_text[:16384]
            logger.log("Post text: {}".format(post_text))
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
    
    def get_post_link_new(fb_post_id):
        try:
            logger.log("Getting post_source id")
            user_element_id = post.find_element_by_xpath("//div[@class='_67lm _77kc']")
            dataft = user_element_id.get_attribute("data-sigil")
            source_id  = dataft.replace('feed_story_ring', '')
#             dataft = post.get_attribute("data-ft")
#             features = eval(dataft)
#             source_id = features["content_owner_id_new"]
           # source_id = task_source.source_name
            logger.log("Source id: {}.".format(source_id))
            logger.log("Getting post target link")
            link = "https://m.facebook.com/profile.php?id=" + source_id +"/posts/"+fb_post_id 
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

    """def get_post_object(browser, post):
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
    fb_post_id = get_fb_post_id(browser, post)
    stat = PostStat(likes=get_likes_count(post),
                    comments=get_comments_count(post),
                    shares=get_shares_count(post),
                    views=get_views_count(post))
#     task_id = task_source.task_id
                    
    if not post_obj.id:
        post_obj.fb_post_link = get_post_link(post_obj.fb_post_id)
        #post_obj.fb_link_new = get_post_link_new(post_obj.fb_post_id)
        post_obj.fb_post_link_likes = get_likes_link(post_obj.fb_post_id)
        post_obj.user = get_user(post)
        post_obj.date = format(get_date_time_from_post(browser, post))
        post_obj.content = Content(text=get_text(post))
        #post_obj.content = Content(text=get_comment_text(post))
        post_obj.last_time_updated = datetime.now().isoformat()
        post_obj.task_id = task_id
        post_obj.stat = stat
        """fb_repost_id, fb_repost_link = get_repost_id(post)
        post_obj.fb_repost_id = fb_repost_id
        post_obj.fb_repost_link = fb_repost_link

        for v_link in get_videos(browser, post):
            Video(content=post_obj.content, video_link=v_link)"""

        for p_link in get_photos(post):
            Photo(content=post_obj.content, photo_link=p_link)
    else:
        update_post_stat(post_obj, stat)
        update_task_id(fb_post_id, task_id)
        

    return post_obj