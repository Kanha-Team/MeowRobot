#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

from MeowRobot.modules.sql import BASE, SESSION, engine
from sqlalchemy import Column, String, Integer


class MsgDelete(BASE):
    __tablename__ = "msg_delete"

    chat_id = Column(String(14), primary_key=True)
    enabled = Column(Integer, default=0)
    delay = Column(Integer, default=300)


MsgDelete.__table__.create(engine, checkfirst=True)


def set_msg(chat, mode):
    try:
        row = SESSION.get(MsgDelete, str(chat))

        if not row:
            row = MsgDelete(chat_id=str(chat), enabled=mode)
        else:
            row.enabled = mode

        SESSION.add(row)
        SESSION.commit()
    except:
        SESSION.rollback()


def set_delay(chat, delay):
    try:
        row = SESSION.get(MsgDelete, str(chat))

        if not row:
            row = MsgDelete(chat_id=str(chat), delay=delay)
        else:
            row.delay = delay

        SESSION.add(row)
        SESSION.commit()
    except:
        SESSION.rollback()


def get(chat):
    return SESSION.get(MsgDelete, str(chat))
