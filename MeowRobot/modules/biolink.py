#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import re
import asyncio
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatMemberStatus, ParseMode

from MeowRobot import pbot as bot, DRAGONS, DEV_USERS
from MeowRobot.utils.mongo import bio_db, auth_db

# Patterns
URL_PATTERN = re.compile(r"(https?://|www\.)\S+", re.IGNORECASE)
USERNAME_PATTERN = re.compile(r"@[\w_]+", re.IGNORECASE)

# Helpers
async def is_admin(message: Message, user_id: int):
    if user_id in DRAGONS or user_id in DEV_USERS:
        return True
    try:
        member = await bot.get_chat_member(message.chat.id, user_id)
        return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)
    except:
        return False

async def get_target_user(message: Message):
    if message.reply_to_message:
        return message.reply_to_message.from_user
    if len(message.command) > 1:
        user = message.command[1]
        try:
            return await bot.get_users(user)
        except:
            return None
    return None

def format_user(user):
    username = f"@{user.username}" if user.username else "No Username"
    return f"**Name:** {user.mention}\n**User ID:** `{user.id}`\n**Username:** `{username}`"

# Commands
@bot.on_message(filters.command("biolink") & filters.group)
async def biolink_toggle(_, message: Message):
    if not await is_admin(message, message.from_user.id):
        return await message.reply_text("❗ Only admins can use this command.")

    if len(message.command) < 2:
        return await message.reply_text("**Usage:**\n`/biolink on` – Enable Bio Filter\n`/biolink off` – Disable Bio Filter")

    state = message.command[1].lower()
    if state == "on":
        await bio_db.update_one({"chat_id": message.chat.id}, {"$set": {"enabled": True}}, upsert=True)
        await message.reply_text("✅ Bio Link Filter **Enabled**.")
    elif state == "off":
        await bio_db.update_one({"chat_id": message.chat.id}, {"$set": {"enabled": False}}, upsert=True)
        await message.reply_text("❌ Bio Link Filter **Disabled**.")
    else:
        await message.reply_text("Use: `/biolink on` or `/biolink off`")

@bot.on_message(filters.command("biofree") & filters.group)
async def bio_free_cmd(_, message: Message):
    if not await is_admin(message, message.from_user.id):
        return await message.reply_text("❗ Only admins can use this command.")

    user = await get_target_user(message)
    if not user:
        return await message.reply_text("📝 Reply to a user or give a valid username/user ID!")

    await auth_db.update_one(
        {"chat_id": message.chat.id, "user_id": user.id},
        {"$set": {"authorized": True}},
        upsert=True
    )
    await message.reply_text(f"✅ User has been **authorized**.\n\n{format_user(user)}")

@bot.on_message(filters.command("biounfree") & filters.group)
async def bio_unfree_cmd(_, message: Message):
    if not await is_admin(message, message.from_user.id):
        return await message.reply_text("❗ Only admins can use this command.")

    user = await get_target_user(message)
    if not user:
        return await message.reply_text("📝 Reply to a user or give a valid username/user ID!")

    await auth_db.delete_one({"chat_id": message.chat.id, "user_id": user.id})
    await message.reply_text(f"❌ User has been **unauthorized**.\n\n{format_user(user)}")

@bot.on_message(filters.command("biofreelist") & filters.group)
async def bio_freelist_cmd(_, message: Message):
    if not await is_admin(message, message.from_user.id):
        return await message.reply_text("❗ Only admins can use this command.")

    cursor = auth_db.find({"chat_id": message.chat.id})
    users = await cursor.to_list(length=100)

    if not users:
        return await message.reply_text("⚠️ No users have been authorized in this group.")

    text = "**Authorized users in this group:**\n\n"
    for i, data in enumerate(users, start=1):
        user_id = data["user_id"]
        try:
            user = await bot.get_users(user_id)
            name = user.mention
        except:
            name = f"`{user_id}`"
        text += f"{i}. {name}\n"

    await message.reply_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🗑 Close", callback_data="close")]]))

# Filter Handler
@bot.on_message(filters.group & ~filters.service & ~filters.me, group=1)
async def bio_filter_handler(client, message: Message):
    if not message.from_user:
        return

    chat_id = message.chat.id
    user_id = message.from_user.id

    # Check if enabled
    settings = await bio_db.find_one({"chat_id": chat_id})
    if not settings or not settings.get("enabled", False):
        return

    # Ignore admins
    if await is_admin(message, user_id):
        return

    # Ignore authorized users
    is_auth = await auth_db.find_one({"chat_id": chat_id, "user_id": user_id})
    if is_auth:
        return

    # Get bio
    try:
        user_info = await client.get_chat(user_id)
        bio = getattr(user_info, "bio", "") or ""
    except:
        return

    if not bio:
        return

    # Scan bio
    if URL_PATTERN.search(bio) or USERNAME_PATTERN.search(bio):
        try:
            await message.delete()
            warn = await message.reply_text(
                f"⚠️ {message.from_user.mention}, **Links or usernames are not allowed in bio!**\nYour message was removed.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Close", callback_data="close")]])
            )
            await asyncio.sleep(10)
            await warn.delete()
        except:
            pass

@bot.on_callback_query(filters.regex("^close$"))
async def close_query(_, query):
    await query.answer()
    await query.message.delete()

__mod_name__ = "Bɪᴏ-Lɪɴᴋ"
__help__ = """
Filter users with links or usernames in their bio.

 ❍ /biolink <on/off>*:* Enable or disable bio filter in group.
 ❍ /biofree*:* Authorize a user to bypass the filter.
 ❍ /biounfree*:* Deauthorize a user.
 ❍ /biofreelist*:* List all authorized users.
"""
