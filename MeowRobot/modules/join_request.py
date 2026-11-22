#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import asyncio
from pyrogram import Client, filters, enums
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from MeowRobot import pbot as app, DRAGONS, DEV_USERS
from MeowRobot.utils.mongo import join_req_db as DB

active_requests = {}

# Helpers
async def is_admin(message: Message, user_id: int):
    if user_id in DRAGONS or user_id in DEV_USERS:
        return True
    try:
        member = await app.get_chat_member(message.chat.id, user_id)
        return member.status in (enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER)
    except:
        return False

@app.on_message(filters.command("joinrequest") & filters.group)
async def jr_toggle(_, message: Message):
    if not await is_admin(message, message.from_user.id):
        return await message.reply_text("❗ Only admins can use this command.")

    if len(message.command) < 2:
        return await message.reply_text("Usage:\n/joinrequest on\n/joinrequest off")

    arg = message.command[1].lower()
    if arg == "on":
        await DB.update_one({"chat_id": message.chat.id}, {"$set": {"enabled": True}}, upsert=True)
        await message.reply_text("✅ Join Request notifications ENABLED.")
    elif arg == "off":
        await DB.update_one({"chat_id": message.chat.id}, {"$set": {"enabled": False}}, upsert=True)
        await message.reply_text("❌ Join Request notifications DISABLED.")
    else:
        await message.reply_text("Use on or off.")

@app.on_chat_join_request()
async def handle_join_request(client, join_req):
    chat = join_req.chat
    user = join_req.from_user

    settings = await DB.find_one({"chat_id": chat.id})
    if not settings or not settings.get("enabled", False):
        return

    key = f"{chat.id}_{user.id}"
    if key in active_requests:
        return
    active_requests[key] = True

    message_text = (
        "🚨 ᴀ ɴᴇᴡ ᴊᴏɪɴ ʀᴇǫᴜᴇsᴛ ᴅᴇᴛᴇᴄᴛᴇᴅ!\n\n"
        f"👤 ᴜsᴇʀ: {user.mention}\n"
        f"🆔 ɪᴅ: `{user.id}`\n"
        f"🔗 ᴜsᴇʀɴᴀᴍᴇ: @{user.username if user.username else 'ɴᴏɴᴇ'}\n\n"
        "<i>📝 ɴᴏᴛᴇ: ᴍᴇssᴀɢᴇ ᴡɪʟʟ ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇ ɪɴ 10 ᴍɪɴᴜᴛᴇs</i>"
    )

    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ ᴀᴘᴘʀᴏᴠᴇ", callback_data=f"jr_approve:{chat.id}:{user.id}"),
                InlineKeyboardButton("❌ ᴅɪsᴍɪss", callback_data=f"jr_dismiss:{chat.id}:{user.id}")
            ]
        ]
    )

    sent_message = await client.send_message(chat.id, message_text, reply_markup=buttons)

    async def auto_delete():
        await asyncio.sleep(600)
        try:
            await client.delete_messages(chat.id, sent_message.id)
        except:
            pass
        active_requests.pop(key, None)

    asyncio.create_task(auto_delete())

@app.on_callback_query(filters.regex("^jr_(approve|dismiss):"))
async def handle_callback(client: Client, query: CallbackQuery):
    data = query.data.split(":")
    action = data[0].replace("jr_", "")
    chat_id = int(data[1])
    user_id = int(data[2])
    key = f"{chat_id}_{user_id}"

    try:
        member = await client.get_chat_member(chat_id, query.from_user.id)
        if member.status not in [enums.ChatMemberStatus.OWNER, enums.ChatMemberStatus.ADMINISTRATOR] and query.from_user.id not in DRAGONS:
            return await query.answer("⚠️ ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴅᴍɪɴ 😎", show_alert=True)
    except:
        return await query.answer("⚠️ ᴀᴅᴍɪɴ ᴄʜᴇᴄᴋ ғᴀɪʟᴇᴅ", show_alert=True)

    try:
        user_obj = await client.get_users(user_id)
        chat_obj = await client.get_chat(chat_id)

        if action == "approve":
            await client.approve_chat_join_request(chat_id, user_id)
            await query.edit_message_text(
                f"🎉 ʜᴇʏ {user_obj.mention}! ʏᴏᴜ ᴀʀᴇ ɴᴏᴡ ᴀᴘᴘʀᴏᴠᴇᴅ ɪɴ: `{chat_obj.title}` ✅"
            )
        else:
            await client.decline_chat_join_request(chat_id, user_id)
            await query.edit_message_text(
                f"❌ {user_obj.mention}, ʏᴏᴜʀ ᴊᴏɪɴ ʀᴇǫᴜᴇsᴛ ʜᴀs ʙᴇᴇɴ ᴅɪsᴍɪssᴇᴅ ɪɴ: `{chat_obj.title}`"
            )

    except Exception as e:
        msg = str(e)
        if "already handled" in msg.lower():
            await query.edit_message_text("⚠️ ʀᴇǫᴜᴇsᴛ ᴀʟʀᴇᴀᴅʏ ʜᴀɴᴅʟᴇᴅ")
        else:
            await query.answer(f"⚠️ ᴇʀʀᴏʀ: {msg}", show_alert=True)

    active_requests.pop(key, None)

__mod_name__ = "Jᴏɪɴ-Rᴇǫ"
__help__ = """
Manage join requests in groups.

 ❍ /joinrequest <on/off>*:* Toggle join request notifications.
"""
