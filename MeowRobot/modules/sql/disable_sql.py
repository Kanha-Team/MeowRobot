#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import threading

from sqlalchemy import Column, String, UnicodeText, distinct, func, select

from MeowRobot.modules.sql import BASE, SESSION, engine


class Disable(BASE):
    __tablename__ = "disabled_commands"
    chat_id = Column(String(14), primary_key=True)
    command = Column(UnicodeText, primary_key=True)

    def __init__(self, chat_id, command):
        self.chat_id = chat_id
        self.command = command

    def __repr__(self):
        return "Disabled cmd {} in {}".format(self.command, self.chat_id)



DISABLE_INSERTION_LOCK = threading.RLock()

DISABLED = {}


def disable_command(chat_id, disable):
    with DISABLE_INSERTION_LOCK:
        disabled = SESSION.get(Disable, (str(chat_id), disable))

        if not disabled:
            DISABLED.setdefault(str(chat_id), set()).add(disable)

            disabled = Disable(str(chat_id), disable)
            SESSION.add(disabled)
            SESSION.commit()
            return True

        SESSION.close()
        return False


def enable_command(chat_id, enable):
    with DISABLE_INSERTION_LOCK:
        disabled = SESSION.get(Disable, (str(chat_id), enable))

        if disabled:
            if enable in DISABLED.get(str(chat_id)):  # sanity check
                DISABLED.setdefault(str(chat_id), set()).remove(enable)

            SESSION.delete(disabled)
            SESSION.commit()
            return True

        SESSION.close()
        return False


def is_command_disabled(chat_id, cmd):
    return str(cmd).lower() in DISABLED.get(str(chat_id), set())


def get_all_disabled(chat_id):
    return DISABLED.get(str(chat_id), set())


def num_chats():
    try:
        return SESSION.scalar(select(func.count(distinct(Disable.chat_id))))
    finally:
        SESSION.close()


def num_disabled():
    try:
        return SESSION.scalar(select(func.count(Disable.chat_id)))
    finally:
        SESSION.close()


def migrate_chat(old_chat_id, new_chat_id):
    with DISABLE_INSERTION_LOCK:
        chats = SESSION.scalars(select(Disable).filter(Disable.chat_id == str(old_chat_id))).all()
        for chat in chats:
            chat.chat_id = str(new_chat_id)
            SESSION.add(chat)

        if str(old_chat_id) in DISABLED:
            DISABLED[str(new_chat_id)] = DISABLED.get(str(old_chat_id), set())

        SESSION.commit()


def __load_disabled_commands():
    global DISABLED
    try:
        all_chats = SESSION.scalars(select(Disable)).all()
        for chat in all_chats:
            DISABLED.setdefault(chat.chat_id, set()).add(chat.command)

    finally:
        SESSION.close()


BASE.metadata.create_all(engine)
__load_disabled_commands()
