import os

#CURRENT_PROFILE = 'local'
CURRENT_PROFILE = 'prod'
SCREEN_SHOT_ENABLED = False

CELERY_QUEUE_NAME = 'tasks'
CELERY_BROKER_URL = 'amqp://guest@%s//' % os.environ.get('RABBITMQ_SERVICE_SERVICE_HOST')
CELERY_BACKEND = 'amqp'

SQLALCHEMY_DATABASE_URI = os.environ.get('FBS_DATABASE_POSTGRESQL_SERVICE_HOST')

#APPLICATION_ROOT_PATH = '/usr/src/app' if (CURRENT_PROFILE == 'prod') else '/Users/ramin_novruzov/projects/other/fbs/worker/app'
APPLICATION_ROOT_PATH = 'C:/Users/ers' if (CURRENT_PROFILE == 'prod') else 'C:/Users/ers'
TASK_KEYWORD_ID = "task_keyword_id"
TASK_SOURCE_ID = "task_source_id"
TASK_WARM_ACCOUNT = "task_warm_account"
TASK_RE_LOGIN_ALL_DISABLED_ACCOUNTS = "task_re_login_all_disabled_accounts"
TASK_RE_ENABLE_ALL_DISABLED_PROXY = "task_re_enable_all_disabled_proxy"
SUB_TASK_POST_LIKES = "sub_task_post_likes"
SUB_TASK_POST_COMMENTS = "sub_task_post_comments"
SUB_TASK_POST_SHARES = "sub_task_post_shares"
SUB_TASK_PERSONAL_PAGE = "sub_task_personal_page"

FACEBOOK_URL_MOBILE = "https://m.facebook.com/"
FACEBOOK_URL_MOBILE_SEARCH_KEYWORD = "https://m.facebook.com/search/posts/?q="
FACEBOOK_URL_MOBILE_LIKE_LINK = "https://m.facebook.com/ufi/reaction/profile/browser/?ft_ent_identifier="

FACEBOOK_URL = "https://facebook.com/"
FACEBOOK_URL_WWW = "https://www.facebook.com/"
GOOGLE_URL_WWW = "https://www.google.com/"
FACEBOOK_URL_SETTINGS = "https://www.facebook.com/settings?tab=language"

TIMEOUT_FOR_BACK_TASK = 300
TIMEOUT_BETWEEN_ACCOUNTS_WORK = 3 if (CURRENT_PROFILE == 'prod') else 0
PROXY_BLOCK_ATTEMPTS = 10