#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import asyncio
from pyrogram import filters
from pyrogram.types import ChatMemberUpdated, InlineKeyboardMarkup, InlineKeyboardButton

from MeowRobot import pbot as app, OWNER_ID, LOGGER

@app.on_chat_member_updated(filters.group)
async def owner_welcome(_, member: ChatMemberUpdated):
    try:
        # Only when someone joins
        if not member.new_chat_member or member.old_chat_member:
            return

        user = member.new_chat_member.user
        chat_id = member.chat.id
        chat_name = member.chat.title

        # Only OWNER
        if user.id != OWNER_ID:
            return

        text = f"""
👑 <b>My Owner Has Arrived!</b>

✨ {user.mention}

🏰 <b>Group:</b> {chat_name}

<b>The Boss Is Here!</b> 🔥
"""

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🥀 ᴅᴇᴠᴇʟᴏᴩᴇʀ 🥀",
                        user_id=OWNER_ID
                    )
                ]
            ]
        )

        await asyncio.sleep(2)
        await app.send_message(chat_id, text, reply_markup=keyboard)

    except Exception as e:
        LOGGER.error(f"Error in owner welcome: {e}")

__mod_name__ = "Oᴡɴᴇʀ-Wᴇʟᴄᴏᴍᴇ"
