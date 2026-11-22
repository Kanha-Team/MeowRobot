#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import asyncio
import random
import requests
import html
from pyrogram import filters
from pyrogram.enums import PollType, ChatMemberStatus
from pyrogram.types import Message

from MeowRobot import pbot as app, LOGGER, DRAGONS, DEV_USERS
from MeowRobot.utils.mongo import quiz_db as DB

async def is_admin(message: Message, user_id: int):
    if user_id in DRAGONS or user_id in DEV_USERS:
        return True
    try:
        member = await app.get_chat_member(message.chat.id, user_id)
        return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)
    except:
        return False

# ================= ENABLE ================= #
@app.on_message(filters.command("quizon") & filters.group)
async def quiz_on(client, message: Message):
    if not await is_admin(message, message.from_user.id):
        return await message.reply_text("❗ Admins only.")

    await DB.update_one(
        {"chat_id": message.chat.id},
        {"$set": {"chat_id": message.chat.id, "quiz": True}},
        upsert=True
    )
    await message.reply("✅ Auto Quiz ENABLED in this group")

# ================= DISABLE ================= #
@app.on_message(filters.command("quizoff") & filters.group)
async def quiz_off(client, message: Message):
    if not await is_admin(message, message.from_user.id):
        return await message.reply_text("❗ Admins only.")

    await DB.update_one(
        {"chat_id": message.chat.id},
        {"$set": {"quiz": False}},
        upsert=True
    )
    await message.reply("❌ Auto Quiz DISABLED in this group")

# ================= SEND QUIZ ================= #
async def send_quiz(chat_id):
    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, requests.get, "https://opentdb.com/api.php?amount=1&type=multiple")
        data = response.json()

        if data["response_code"] != 0:
            return

        q = data["results"][0]
        question = html.unescape(q["question"])
        correct = html.unescape(q["correct_answer"])
        incorrect = [html.unescape(i) for i in q["incorrect_answers"]]

        options = incorrect + [correct]
        random.shuffle(options)
        correct_id = options.index(correct)

        await app.send_poll(
            chat_id=chat_id,
            question=f"🧠 AUTO QUIZ\n\n{question}",
            options=options,
            type=PollType.QUIZ,
            correct_option_id=correct_id,
        )
    except Exception as e:
        LOGGER.error(f"Error sending quiz to {chat_id}: {e}")

# ================= AUTO LOOP ================= #
async def auto_quiz_loop():
    await asyncio.sleep(15)
    while True:
        try:
            chats = []
            async for doc in DB.find({"quiz": True}):
                chats.append(doc["chat_id"])

            if not chats:
                await asyncio.sleep(60)
                continue

            for chat_id in chats:
                await send_quiz(chat_id)
                await asyncio.sleep(5)

            await asyncio.sleep(3600)  # 1 hour gap
        except Exception as e:
            LOGGER.error(f"Error in quiz loop: {e}")
            await asyncio.sleep(60)

# ================= START ================= #
async def start_auto():
    await asyncio.sleep(20)
    LOGGER.info("Auto Quiz System Started")
    asyncio.create_task(auto_quiz_loop())

# Force start on import
asyncio.get_event_loop().create_task(start_auto())

__mod_name__ = "Qᴜɪᴢ"
__help__ = """
Automatically sends trivia quizzes every hour.

 ❍ /quizon*:* Enable auto quiz in group.
 ❍ /quizoff*:* Disable auto quiz in group.
"""
