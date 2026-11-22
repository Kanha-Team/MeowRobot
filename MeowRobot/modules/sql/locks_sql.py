#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

# New chat added -> setup permissions
import threading

from sqlalchemy import Boolean, Column, String

from MeowRobot.modules.sql import BASE, SESSION


class Permissions(BASE):
    __tablename__ = "permissions"
    chat_id = Column(String(14), primary_key=True)
    # Booleans are for "is this locked", _NOT_ "is this allowed"
    audio = Column(Boolean, default=False)
    voice = Column(Boolean, default=False)
    contact = Column(Boolean, default=False)
    video = Column(Boolean, default=False)
    document = Column(Boolean, default=False)
    photo = Column(Boolean, default=False)
    sticker = Column(Boolean, default=False)
    gif = Column(Boolean, default=False)
    url = Column(Boolean, default=False)
    bots = Column(Boolean, default=False)
    forward = Column(Boolean, default=False)
    game = Column(Boolean, default=False)
    location = Column(Boolean, default=False)
    rtl = Column(Boolean, default=False)
    button = Column(Boolean, default=False)
    egame = Column(Boolean, default=False)
    inline = Column(Boolean, default=False)
    videonote = Column(Boolean, default=False)
    poll = Column(Boolean, default=False)
    spoiler = Column(Boolean, default=False)
    emojipack = Column(Boolean, default=False)
    invitelink = Column(Boolean, default=False)
    command = Column(Boolean, default=False)
    phone = Column(Boolean, default=False)
    email = Column(Boolean, default=False)
    anonchannel = Column(Boolean, default=False)
    text = Column(Boolean, default=False)
    mention = Column(Boolean, default=False)

    def __init__(self, chat_id):
        self.chat_id = str(chat_id)  # ensure string
        self.audio = False
        self.voice = False
        self.contact = False
        self.video = False
        self.document = False
        self.photo = False
        self.sticker = False
        self.gif = False
        self.url = False
        self.bots = False
        self.forward = False
        self.game = False
        self.location = False
        self.rtl = False
        self.button = False
        self.egame = False
        self.inline = False
        self.videonote = False
        self.poll = False
        self.spoiler = False
        self.emojipack = False
        self.invitelink = False
        self.command = False
        self.phone = False
        self.email = False
        self.anonchannel = False
        self.text = False
        self.mention = False

    def __repr__(self):
        return "<Permissions for %s>" % self.chat_id


class Restrictions(BASE):
    __tablename__ = "restrictions"
    chat_id = Column(String(14), primary_key=True)
    # Booleans are for "is this restricted", _NOT_ "is this allowed"
    messages = Column(Boolean, default=False)
    media = Column(Boolean, default=False)
    other = Column(Boolean, default=False)
    preview = Column(Boolean, default=False)

    def __init__(self, chat_id):
        self.chat_id = str(chat_id)  # ensure string
        self.messages = False
        self.media = False
        self.other = False
        self.preview = False

    def __repr__(self):
        return "<Restrictions for %s>" % self.chat_id


# For those who faced database error, Just uncomment the
# line below and run bot for 1 time & remove that line!


# Permissions.__table__.drop()


PERM_LOCK = threading.RLock()
RESTR_LOCK = threading.RLock()


def init_permissions(chat_id, reset=False):
    curr_perm = SESSION.get(Permissions, str(chat_id))
    if reset and curr_perm:
        SESSION.delete(curr_perm)
        SESSION.flush()
    perm = Permissions(str(chat_id))
    SESSION.add(perm)
    SESSION.commit()
    return perm


def init_restrictions(chat_id, reset=False):
    curr_restr = SESSION.get(Restrictions, str(chat_id))
    if reset and curr_restr:
        SESSION.delete(curr_restr)
        SESSION.flush()
    restr = Restrictions(str(chat_id))
    SESSION.add(restr)
    SESSION.commit()
    return restr


def update_lock(chat_id, lock_type, locked):
    with PERM_LOCK:
        curr_perm = SESSION.get(Permissions, str(chat_id))
        if not curr_perm:
            curr_perm = init_permissions(chat_id)

        if hasattr(curr_perm, lock_type):
            setattr(curr_perm, lock_type, locked)

        SESSION.add(curr_perm)
        SESSION.commit()


def update_restriction(chat_id, restr_type, locked):
    with RESTR_LOCK:
        curr_restr = SESSION.get(Restrictions, str(chat_id))
        if not curr_restr:
            curr_restr = init_restrictions(chat_id)

        if restr_type == "messages":
            curr_restr.messages = locked
        elif restr_type == "media":
            curr_restr.media = locked
        elif restr_type == "other":
            curr_restr.other = locked
        elif restr_type == "previews":
            curr_restr.preview = locked
        elif restr_type == "all":
            curr_restr.messages = locked
            curr_restr.media = locked
            curr_restr.other = locked
            curr_restr.preview = locked
        SESSION.add(curr_restr)
        SESSION.commit()


def is_locked(chat_id, lock_type):
    curr_perm = SESSION.get(Permissions, str(chat_id))
    SESSION.close()

    if not curr_perm:
        return False

    return bool(getattr(curr_perm, lock_type, False))


def is_restr_locked(chat_id, lock_type):
    curr_restr = SESSION.get(Restrictions, str(chat_id))
    SESSION.close()

    if not curr_restr:
        return False

    if lock_type == "messages":
        return curr_restr.messages
    elif lock_type == "media":
        return curr_restr.media
    elif lock_type == "other":
        return curr_restr.other
    elif lock_type == "previews":
        return curr_restr.preview
    elif lock_type == "all":
        return (
            curr_restr.messages
            and curr_restr.media
            and curr_restr.other
            and curr_restr.preview
        )


def get_locks(chat_id):
    try:
        return SESSION.get(Permissions, str(chat_id))
    finally:
        SESSION.close()


def get_restr(chat_id):
    try:
        return SESSION.get(Restrictions, str(chat_id))
    finally:
        SESSION.close()


def migrate_chat(old_chat_id, new_chat_id):
    with PERM_LOCK:
        perms = SESSION.get(Permissions, str(old_chat_id))
        if perms:
            perms.chat_id = str(new_chat_id)
        SESSION.commit()

    with RESTR_LOCK:
        rest = SESSION.get(Restrictions, str(old_chat_id))
        if rest:
            rest.chat_id = str(new_chat_id)
        SESSION.commit()
