#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import asyncio
from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus

from MeowRobot import pbot as bot, DRAGONS, DEV_USERS
from MeowRobot.utils.mongo import antiedit_db

CACHE = {}

# Helpers
async def is_admin(message: Message, user_id: int):
    if user_id in DRAGONS or user_id in DEV_USERS:
        return True
    try:
        member = await bot.get_chat_member(message.chat.id, user_id)
        return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)
    except:
        return False

@bot.on_message(filters.command("antiedit") & filters.group)
async def antiedit_toggle(_, message: Message):
    if not await is_admin(message, message.from_user.id):
        return await message.reply_text("❗ Only admins can use this command.")

    if len(message.command) < 2:
        return await message.reply_text("Usage:\n/antiedit on\n/antiedit off")

    arg = message.command[1].lower()
    if arg == "on":
        await antiedit_db.update_one({"chat_id": message.chat.id}, {"$set": {"enabled": True}}, upsert=True)
        await message.reply_text("✅ Anti-Edit Enabled")
    elif arg == "off":
        await antiedit_db.update_one({"chat_id": message.chat.id}, {"$set": {"enabled": False}}, upsert=True)
        await message.reply_text("❌ Anti-Edit Disabled")
    else:
        await message.reply_text("Use /antiedit on or off")

@bot.on_message(filters.group & ~filters.bot, group=2)
async def save_message(_, message: Message):
    if message.text and message.text.startswith("/"):
        return

    content = message.text or message.caption
    if content:
        CACHE[(message.chat.id, message.id)] = content

@bot.on_edited_message(filters.group & ~filters.bot, group=3)
async def anti_edit_handler(_, message: Message):
    chat_id = message.chat.id

    settings = await antiedit_db.find_one({"chat_id": chat_id})
    if not settings or not settings.get("enabled", False):
        return

    # Ignore admins
    if await is_admin(message, message.from_user.id):
        return

    key = (chat_id, message.id)
    old = CACHE.get(key)
    new = message.text or message.caption

    # reaction edit or no content change ignore
    if old and new and old.strip() == new.strip():
        return

    try:
        await message.delete()
    except:
        return

    user = message.from_user
    tag = user.mention if user else "Someone"

    report = await bot.send_message(
        chat_id,
        f"🚫 **Edited Message Deleted**"
        f"👤 **User:** {tag}"
        f"📌 **Original:**{old or 'Not Cached'}"
        f"✏️ **Edited:**{new}"
    )

    CACHE[key] = new
    await asyncio.sleep(120)
    try:
        await report.delete()
    except:
        pass

__mod_name__ = "Aɴᴛɪ-Eᴅɪᴛ"
__help__ = """
Automatically deletes edited messages and shows the original content.

 ❍ /antiedit <on/off>*:* Toggle anti-edit in group (Admins only).
"""
