#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import threading

from sqlalchemy import Column, String, distinct, func, select

from MeowRobot.modules.sql import BASE, SESSION, engine


class GroupLogs(BASE):
    __tablename__ = "log_channels"
    chat_id = Column(String(14), primary_key=True)
    log_channel = Column(String(14), nullable=False)

    def __init__(self, chat_id, log_channel):
        self.chat_id = str(chat_id)
        self.log_channel = str(log_channel)



LOGS_INSERTION_LOCK = threading.RLock()

CHANNELS = {}


def set_chat_log_channel(chat_id, log_channel):
    with LOGS_INSERTION_LOCK:
        res = SESSION.get(GroupLogs, str(chat_id))
        if res:
            res.log_channel = log_channel
        else:
            res = GroupLogs(chat_id, log_channel)
            SESSION.add(res)

        CHANNELS[str(chat_id)] = log_channel
        SESSION.commit()


def get_chat_log_channel(chat_id):
    return CHANNELS.get(str(chat_id))


def stop_chat_logging(chat_id):
    with LOGS_INSERTION_LOCK:
        res = SESSION.get(GroupLogs, str(chat_id))
        if res:
            if str(chat_id) in CHANNELS:
                del CHANNELS[str(chat_id)]

            log_channel = res.log_channel
            SESSION.delete(res)
            SESSION.commit()
            return log_channel


def num_logchannels():
    try:
        return SESSION.scalar(select(func.count(distinct(GroupLogs.chat_id))))
    finally:
        SESSION.close()


def migrate_chat(old_chat_id, new_chat_id):
    with LOGS_INSERTION_LOCK:
        chat = SESSION.get(GroupLogs, str(old_chat_id))
        if chat:
            chat.chat_id = str(new_chat_id)
            SESSION.add(chat)
            if str(old_chat_id) in CHANNELS:
                CHANNELS[str(new_chat_id)] = CHANNELS.get(str(old_chat_id))

        SESSION.commit()


def __load_log_channels():
    global CHANNELS
    try:
        all_chats = SESSION.scalars(select(GroupLogs)).all()
        CHANNELS = {chat.chat_id: chat.log_channel for chat in all_chats}
    finally:
        SESSION.close()


BASE.metadata.create_all(engine)
__load_log_channels()
