#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import threading

from sqlalchemy import Column, String, UnicodeText, select

from MeowRobot.modules.sql import BASE, SESSION, engine


class BlacklistUsers(BASE):
    __tablename__ = "blacklistusers"
    user_id = Column(String(14), primary_key=True)
    reason = Column(UnicodeText)

    def __init__(self, user_id, reason=None):
        self.user_id = user_id
        self.reason = reason



BLACKLIST_LOCK = threading.RLock()
BLACKLIST_USERS = set()


def blacklist_user(user_id, reason=None):
    with BLACKLIST_LOCK:
        user = SESSION.get(BlacklistUsers, str(user_id))
        if not user:
            user = BlacklistUsers(str(user_id), reason)
        else:
            user.reason = reason

        SESSION.add(user)
        SESSION.commit()
        __load_blacklist_userid_list()


def unblacklist_user(user_id):
    with BLACKLIST_LOCK:
        user = SESSION.get(BlacklistUsers, str(user_id))
        if user:
            SESSION.delete(user)

        SESSION.commit()
        __load_blacklist_userid_list()


def get_reason(user_id):
    user = SESSION.get(BlacklistUsers, str(user_id))
    rep = ""
    if user:
        rep = user.reason

    SESSION.close()
    return rep


def is_user_blacklisted(user_id):
    return user_id in BLACKLIST_USERS


def __load_blacklist_userid_list():
    global BLACKLIST_USERS
    try:
        BLACKLIST_USERS = {int(x.user_id) for x in SESSION.scalars(select(BlacklistUsers)).all()}
    finally:
        SESSION.close()


BASE.metadata.create_all(engine)
__load_blacklist_userid_list()
