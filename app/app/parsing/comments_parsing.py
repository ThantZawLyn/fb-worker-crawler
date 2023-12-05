from datetime import datetime
from random import randint
from time import sleep

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from .. import logger
from ..database import DBSession
from ..database.models import Comment, Content, Photo, User, Video, All_comment
from ..database.subtasks_dao import save_personal_page_subtask
from ..utils.count_utils import string_count_to_int
from ..utils.user_utils import trim_full_link
from .common_parsing import get_fb_id, open_post
from ..utils.datetime_utils import parse_datetime
from ..utils.date_time_comment import convert_date_comment



class CommentData:

    def __init__(self, author_name, author_link, author_fb_id, image, video, text, comment_id, date, likes_count,
                 class_name):
        self.author_name = author_name
        self.author_link = author_link
        self.author_fb_id = author_fb_id
        self.image = image
        self.video = video
        self.text = text
        self.comment_id = comment_id
        self.date = date
        self.likes_count = likes_count
        self.children = []
        self.class_name = class_name

    def add_children(self, children):
        for child in children or []:
            self.children.append(child)


def parse_comment(comment):
    def hasXpath(xpath):
        try:
            comment.find_element(By.XPATH, xpath).get_attribute("src")
            return True
        except:
            return False

    def get_image_link(comment):
        xpath = ".//div[@class='_2b1t attachment']/a"
        if (hasXpath(xpath) == True):
            photo_data = comment.find_element(By.XPATH, ".//div[@class='_2b1t attachment']/a/i")
            photo_store = photo_data.get_attribute("data-store")
            features = eval(photo_store)
            photo_link = features["imgsrc"]
            new_link = re.sub('\/', '', photo_link)
            logger.log("Photo Link: {} ".format(new_link))
            # new_link = re.sub("limit=\d+", "limit=1000", photo_link)
            return new_link
        else:
            logger.log("Author image parse")
            return None

    def get_video_link(comment):
        return ''

    def get_comment_id(comment):
        try:
            comment_url = comment.get_attribute('id')
            #             logger.log("Comment_Id is => {}".format(comment_url))
            logger.log("Comment id: {} ".format(comment_url))
            return comment_url
        except Exception as e:
            logger.exception("Comment id parse", e)
        return None

    def get_comment_date(comment):
        try:
            comment_date_timestamp = comment.find_element(By.XPATH, ".//abbr[@class='_4ghv _2b0a']").text
            #             logger.log("Comment date is - {}".format(comment_date_timestamp))
            return parse_datetime(comment_date_timestamp)
        except Exception as e:
            logger.log("Comment date parse")
        return None

    def get_comments_like_count(comment):
        try:
            text = comment.find_element(By.XPATH, ".//span[@class='_14va']").text
            #             logger.log("Comment first like count = {}".format(text))
            logger.log("Comment like: {} ".format(text))
            return string_count_to_int(text)
        except Exception as e:
            logger.log("Comment like count not found in parse")
        return 0

    def get_comment_text(comment):
        try:
            ff = comment.find_element(By.XPATH,
                                      ".//div[@data-sigil='comment-body']").text
            logger.log("Comment text: {} ".format(ff))
            #             logger.log("Get Text Coment - {}".format(ff))
            return ff
        except Exception as e:
            logger.log("Comment text count parse")
        return None

    def get_author_data(comment):
        try:
            logger.log("Start get_author_data")
            author_element = comment.find_element(By.XPATH,
                                                  ".//div[@class='_2b05']/a")
            name_author = author_element.text
            name = name_author.replace('Top fan', '')
            logger.log("Name: {} ".format(name))
            ggg = author_element.get_attribute("href")
            link = trim_full_link(ggg)
            logger.log("Link: {} ".format(link))
            fb_id_xpath = comment.find_element(By.XPATH,
                                               ".//div[contains(@class,'_2a_j')]").get_attribute("data-sigil")

            fb_id = fb_id_xpath.replace('feed_story_ring', '')
            logger.log("ID: {} ".format(fb_id))
            return name, link, fb_id
        except Exception as e:
            logger.exception("Author data parse", e)
        return None, None

    def get_class_name(comment):
        try:
            classes = comment.get_attribute("class")
            classes = classes.split(" ")
            if "clearfix" in classes:
                classes.remove("clearfix")
            if len(classes) > 0:
                return classes[0]
            else:
                return None

        except Exception as e:
            logger.exception("Comment class name", e)
        return None

    author_name, author_link, author_fb_id = get_author_data(comment)
    comment_text = get_comment_text(comment)
    image_link = get_image_link(comment)
    video_link = get_video_link(comment)
    comment_id = get_comment_id(comment)
    comment_date = get_comment_date(comment)
    comment_likes_count = get_comments_like_count(comment)
    class_name = get_class_name(comment)

    return CommentData(author_name, author_link, author_fb_id, image_link, video_link, comment_text, comment_id,
                       comment_date,
                       comment_likes_count, class_name)


def parse_comments(browser, subtask):
    def remove_from_scope(browser, comment_objects):
        comment_classes = []
        for co in comment_objects:
            if co.class_name is not None:
                comment_classes.append("." + co.class_name)
        try:
            if comment_classes and len(comment_classes) > 0:
                selectors = ', '.join(map(str, comment_classes))
                browser.execute_script(
                    "var comments=document.querySelectorAll('" + selectors + "');for(var i = 0; i < comments.length; i++){comments[i].removeAttribute('class')}")
                sleep(randint(5, 7))
        except Exception as e:
            logger.exception("post_ids couldn't be parsed", e)

    def search_comments(browser):
        try:
            more_buttonee = WebDriverWait(browser, 30).until(
                ec.presence_of_all_elements_located((By.XPATH,
                                                     "//div[contains(@class,'_2a_i')]")))
            return more_buttonee
        except Exception as e:
            logger.exception("Comments parse", e)
        return []

    def search_view_more(browser):
        try:
            logger.log_alive()
            logger.log("Search view N more comments button")
            more_button = WebDriverWait(browser, 10).until(
                ec.presence_of_element_located((By.XPATH, "//a[contains(text(),'View')]")))
            more_button.click()
        except:
            logger.log("No view more button found. Finish parsing")
            return False
        return True

    def check_error_view_more(browser):
        try:
            check_buttonee = WebDriverWait(browser, 30).until(
                ec.presence_of_all_elements_located((By.XPATH,
                                                     "//a[contains(text(),'View')]//..//..//div[contains(@class,'_2a_j')]")))
            for my_check in check_buttonee:
                gg = my_check.get_attribute("data-sigil")
            fb_id_check = gg.replace('feed_story_ring', '')
            logger.log("Found it")
            return fb_id_check
        except Exception as e:
            logger.log("No View More")
        return None

    post = subtask.post
    url = post.fb_post_link + '&eav=AfYh0ZkrINA8eTKTKQAyRigdwzJY1ZmqYrDluCcqejQrrS32qWuU_ISO610pn4w8J_E&m_entstream_source=feed_mobile&paipv=0'
#     source = post.task_source
#     source_id = source.source_name
#     url = 'https://m.facebook.com/story.php?story_fbid=' + post.fb_post_id +'&id='+source_id
#     open_post(browser, url) 
    open_post(browser, url) 

    check_error_view = check_error_view_more(browser)
    check_error_view2 = ""
    countt = 1
    while (search_view_more(browser) and countt == 1):
        sleep(randint(3, 7))
        check_error_view2 = check_error_view_more(browser)
        if (check_error_view == check_error_view2):
            countt = 2
        check_error_view = check_error_view2

    while True:
        logger.log_alive()
        comments = search_comments(browser)
        comment_objects = collect_root_comments(comments, browser)
        save_users = {u.link: u for u in
                      DBSession.query(User).filter(User.link.in_(get_distinct_authors(comment_objects))).all()}
        saved_comments = {c.fb_comment_id: c for c in DBSession.query(Comment).filter(
            Comment.fb_comment_id.in_(get_comments_fb_ids(comment_objects))).all()}
        #      logger.log("Being Save Comments")
        save_comments(None, comment_objects, save_users, saved_comments, post)
        #      logger.log("Finish Save Comments")
        # remove_from_scope(browser, comment_objects)

        if not search_view_more(browser) or not countt == 1:
            return


def save_comments(parent_comment, comments, save_users, saved_comments, post):
    logger.log("Being Save Comments")

    def save_comment(c, parent_comment, post, save_users):
        logger.log("Start author_link Save ")
        if c.author_link not in save_users:
            logger.log("Author link: {}".format(c.author_link))
            user = User(name=c.author_name, link=c.author_link, fb_id=c.author_fb_id)
            save_personal_page_subtask(post, user)
            DBSession.add(user)
            DBSession.commit()

        else:
            logger.log("User already in DB")
            user = save_users[c.author_link]

        content = Content(text=c.text)
        add_id = All_comment(content = content, network_id =1)
        DBSession.add(add_id)
        DBSession.commit()
        logger.log("Start image Save")
        if c.image is not None:
            photo = Photo(photo_link=c.image, content=content)
            DBSession.add(photo)
            DBSession.commit()

        if c.video is not None:
            video = Video(video_link=c.video, content=content)
            DBSession.add(video)
            DBSession.commit()

        comment = Comment(post=post, user=user, content=content, fb_comment_id=c.comment_id, date=c.date,
                          likes_count=c.likes_count)
        logger.log("Start parent_comment Save ")
        if parent_comment:
            comment.parent_comment = parent_comment
        DBSession.add(comment)
        DBSession.commit()
        logger.log("Save comment id: {} to db".format(comment.fb_comment_id))
        return comment

    def get_saved_comment(c, parent_comment, post, save_users, saved_comments):
        if c.comment_id in saved_comments:
            logger.log("Get Save Comments ID: {}".format(c.comment_id))
            return saved_comments[c.comment_id]
        else:
            logger.log("Start Get Save Comments")
            return save_comment(c, parent_comment, post, save_users)

    for c in comments:
        comment = get_saved_comment(c, parent_comment, post, save_users, saved_comments)
        if len(c.children) > 0:
            logger.log("Len of childres: {}".format(len(c.children)))
            save_comments(comment, c.children, save_users, saved_comments, post)


def collect_root_comments(comments, browser):
    logger.log("Begin loop of comment parse {}".format(str(len(comments))))
    index = 1
    comment_objects = []
    for comment in comments:
        logger.log("Parse {} from {}".format(str(index), str(len(comments))))
        index += 1

        root_comment = parse_comment(comment)
        root_comment.add_children(collect_child_comments(comment, browser))
        comment_objects.append(root_comment)
    return comment_objects


def collect_child_comments(comment, browser):
    child_comments_data = []
    try:

        reply_button = browser.find_element(By.XPATH, "//div[contains(@class,'_2a_i')]//a[text()[contains(.,'replied')]]")
        reply_button.click()
        sleep(randint(3, 7))
        child_comments = comment.find_elements(By.XPATH, ".//div[@class='_2b1k']//div[@class='_2a_i']")

        logger.log("Parse child comments")
        index = 1
        for child_comment in child_comments:
            logger.log("Parse: {} child comment from: {}".format(index, len(child_comments)))
            index += 1
            child_comments_data.append(parse_comment(child_comment))
    except Exception as e:
        logger.log("Post has no comment replies")


def get_distinct_authors(comment_objects):
    def get_authors(comments):
        for c in comments:
            authors.add(c.author_link)
            if len(c.children) > 0:
                get_authors(c.children)

    authors = set()
    get_authors(comment_objects)
    logger.log("Author Check - {}".format(authors))
    return authors


def get_comments_fb_ids(comment_objects):
    def get_comments(comments):
        for c in comments:
            comments_fb_ids.add(c.comment_id)
            if len(c.children) > 0:
                get_comments(c.children)

    comments_fb_ids = set()
    get_comments(comment_objects)
    logger.log("ID Check - {}".format(comments_fb_ids))
    return comments_fb_ids

    
