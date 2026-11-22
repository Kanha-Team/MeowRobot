#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

from sqlalchemy import Column, String, select

from MeowRobot.modules.sql import BASE, SESSION


class Nightmode(BASE):
    __tablename__ = "nightmode"
    chat_id = Column(String(14), primary_key=True)

    def __init__(self, chat_id):
        self.chat_id = chat_id





def add_nightmode(chat_id: str):
    nightmoddy = Nightmode(str(chat_id))
    SESSION.add(nightmoddy)
    SESSION.commit()


def rmnightmode(chat_id: str):
    rmnightmoddy = SESSION.get(Nightmode, str(chat_id))
    if rmnightmoddy:
        SESSION.delete(rmnightmoddy)
        SESSION.commit()


def get_all_chat_id():
    stark = SESSION.scalars(select(Nightmode)).all()
    SESSION.close()
    return stark


def is_nightmode_indb(chat_id: str):
    try:
        s__ = SESSION.get(Nightmode, str(chat_id))
        if s__:
            return str(s__.chat_id)
    finally:
        SESSION.close()
