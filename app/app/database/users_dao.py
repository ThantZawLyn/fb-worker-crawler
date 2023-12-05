from . import DBSession
from .models import User


def get_user_by_link(link):
    return DBSession.query(User).filter(User.link == link).first()

def get_user_by_fb_id(fb_id):
    return DBSession.query(User).filter(User.fb_id == fb_id).first()