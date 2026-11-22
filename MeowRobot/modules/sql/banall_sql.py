#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

from sqlalchemy import Column, String, Boolean
from MeowRobot.modules.sql import SESSION, BASE, engine
import threading
from MeowRobot import LOGGER

class BanallLockdown(BASE):
    __tablename__ = "banall_lockdown"
    chat_id = Column(String(14), primary_key=True)
    is_locked = Column(Boolean, default=False)

    def __init__(self, chat_id, is_locked):
        self.chat_id = str(chat_id)
        self.is_locked = is_locked

BASE.metadata.create_all(engine)

LOCK = threading.RLock()

def set_lockdown(chat_id: int, status: bool):
    with LOCK:
        try:
            chat = SESSION.get(BanallLockdown, str(chat_id))
            if not chat:
                chat = BanallLockdown(str(chat_id), status)
                SESSION.add(chat)
            else:
                chat.is_locked = status
            SESSION.commit()
        except Exception as e:
            LOGGER.error(f"Error in set_lockdown: {e}")
            SESSION.rollback()
        finally:
            SESSION.close()

def is_lockdown(chat_id: int) -> bool:
    try:
        chat = SESSION.get(BanallLockdown, str(chat_id))
        if chat:
            return chat.is_locked
        return False
    except Exception as e:
        LOGGER.error(f"Error in is_lockdown: {e}")
        return False
    finally:
        SESSION.close()

def migrate_chat(old_chat_id, new_chat_id):
    with LOCK:
        try:
            chat = SESSION.get(BanallLockdown, str(old_chat_id))
            if chat:
                new_chat = BanallLockdown(str(new_chat_id), chat.is_locked)
                SESSION.add(new_chat)
                SESSION.delete(chat)
                SESSION.commit()
        except Exception as e:
            LOGGER.error(f"Error in migrate_chat (banall): {e}")
            SESSION.rollback()
        finally:
            SESSION.close()
