#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import asyncio
from pyrogram import enums, filters
from pyrogram.errors import FloodWait

from MeowRobot import pbot as app

@app.on_message(filters.command("bots") & filters.group)
async def bots(client, message):
    try:
        botList = []
        async for bot in app.get_chat_members(
            message.chat.id, filter=enums.ChatMembersFilter.BOTS
        ):
            botList.append(bot.user)

        if not botList:
            return await message.reply_text("No bots found in this group.")

        lenBotList = len(botList)
        text3 = f"**ʙᴏᴛ ʟɪsᴛ - {message.chat.title}**\n\n🤖 ʙᴏᴛs\n"

        for i, bot in enumerate(botList):
            symbol = "└" if i == lenBotList - 1 else "├"
            text3 += f"{symbol} @{bot.username}\n"

        text3 += f"\n**ᴛᴏᴛᴀʟ ɴᴜᴍʙᴇʀ ᴏғ ʙᴏᴛs**: {lenBotList}"
        await app.send_message(message.chat.id, text3)
    except FloodWait as e:
        await asyncio.sleep(e.value)

__mod_name__ = "Bᴏᴛs"
__help__ = """
Lists all bots in a group.

 ❍ /bots*:* Get a list of all bots in the group.
"""
