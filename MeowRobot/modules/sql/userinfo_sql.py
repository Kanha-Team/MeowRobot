#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import threading

from sqlalchemy import BigInteger, Column, UnicodeText

from MeowRobot.modules.sql import BASE, SESSION


class UserInfo(BASE):
    __tablename__ = "userinfo"
    user_id = Column(BigInteger, primary_key=True)
    info = Column(UnicodeText)

    def __init__(self, user_id, info):
        self.user_id = user_id
        self.info = info

    def __repr__(self):
        return "<User info %d>" % self.user_id


class UserBio(BASE):
    __tablename__ = "userbio"
    user_id = Column(BigInteger, primary_key=True)
    bio = Column(UnicodeText)

    def __init__(self, user_id, bio):
        self.user_id = user_id
        self.bio = bio

    def __repr__(self):
        return "<User info %d>" % self.user_id



INSERTION_LOCK = threading.RLock()


def get_user_me_info(user_id):
    try:
        userinfo = SESSION.get(UserInfo, user_id)
        if userinfo:
            return userinfo.info
        return None
    finally:
        SESSION.close()


def set_user_me_info(user_id, info):
    with INSERTION_LOCK:
        try:
            userinfo = SESSION.get(UserInfo, user_id)
            if userinfo:
                userinfo.info = info
            else:
                userinfo = UserInfo(user_id, info)
            SESSION.add(userinfo)
            SESSION.commit()
        except Exception:
            SESSION.rollback()
            raise
        finally:
            SESSION.close()


def get_user_bio(user_id):
    try:
        userbio = SESSION.get(UserBio, user_id)
        if userbio:
            return userbio.bio
        return None
    finally:
        SESSION.close()


def set_user_bio(user_id, bio):
    with INSERTION_LOCK:
        try:
            userbio = SESSION.get(UserBio, user_id)
            if userbio:
                userbio.bio = bio
            else:
                userbio = UserBio(user_id, bio)

            SESSION.add(userbio)
            SESSION.commit()
        except Exception:
            SESSION.rollback()
            raise
        finally:
            SESSION.close()
