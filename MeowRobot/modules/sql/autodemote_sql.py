#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import threading
from sqlalchemy import Column, String, Integer, Boolean
from MeowRobot.modules.sql import BASE, SESSION, engine

class AutodemoteSettings(BASE):
    __tablename__ = "autodemote_settings"
    chat_id = Column(String(14), primary_key=True)
    is_enabled = Column(Boolean, default=False)
    ban_limit = Column(Integer, default=3)
    time_window = Column(Integer, default=10)

    def __init__(self, chat_id, is_enabled=False, ban_limit=3, time_window=10):
        self.chat_id = str(chat_id)
        self.is_enabled = is_enabled
        self.ban_limit = ban_limit
        self.time_window = time_window

    def __repr__(self):
        return f"<AutodemoteSettings({self.chat_id}, {self.is_enabled}, {self.ban_limit}, {self.time_window})>"

BASE.metadata.create_all(engine)

INSERTION_LOCK = threading.RLock()

def set_autodemote(chat_id, is_enabled):
    with INSERTION_LOCK:
        curr = SESSION.get(AutodemoteSettings, str(chat_id))
        if not curr:
            curr = AutodemoteSettings(str(chat_id), is_enabled=is_enabled)
        else:
            curr.is_enabled = is_enabled
        SESSION.add(curr)
        SESSION.commit()

def set_autodemote_limit(chat_id, ban_limit, time_window):
    with INSERTION_LOCK:
        curr = SESSION.get(AutodemoteSettings, str(chat_id))
        if not curr:
            curr = AutodemoteSettings(str(chat_id), ban_limit=ban_limit, time_window=time_window)
        else:
            curr.ban_limit = ban_limit
            curr.time_window = time_window
        SESSION.add(curr)
        SESSION.commit()

def get_autodemote_settings(chat_id):
    try:
        curr = SESSION.get(AutodemoteSettings, str(chat_id))
        if curr:
            return curr.is_enabled, curr.ban_limit, curr.time_window
        return False, 3, 10
    finally:
        SESSION.close()

def migrate_chat(old_chat_id, new_chat_id):
    with INSERTION_LOCK:
        curr = SESSION.get(AutodemoteSettings, str(old_chat_id))
        if curr:
            curr.chat_id = str(new_chat_id)
            SESSION.commit()
        SESSION.close()
