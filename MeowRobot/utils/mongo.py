#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

from motor.motor_asyncio import AsyncIOMotorClient as MongoCli

from MeowRobot import MONGO_DB_URI

mongo = MongoCli(MONGO_DB_URI)
db = mongo.MeowRobot

coupledb = db.couple
nsfw_db = db.nsfw
nsfw_settings = db.nsfw_settings
bio_db = db.bio_filter
auth_db = db.auth_users
antiedit_db = db.antiedit
quiz_db = db.autoquiz_chats
chatbot_db = db.chatbot
join_req_db = db.join_req


async def _get_lovers(chat_id: int):
    lovers = await coupledb.find_one({"chat_id": chat_id})
    if lovers:
        lovers = lovers["couple"]
    else:
        lovers = {}
    return lovers


async def get_couple(chat_id: int, date: str):
    lovers = await _get_lovers(chat_id)
    if date in lovers:
        return lovers[date]
    else:
        return False


async def save_couple(chat_id: int, date: str, couple: dict):
    lovers = await _get_lovers(chat_id)
    lovers[date] = couple
    await coupledb.update_one(
        {"chat_id": chat_id},
        {"$set": {"couple": lovers}},
        upsert=True,
    )
