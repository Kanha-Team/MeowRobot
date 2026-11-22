#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import random
import asyncio
import requests
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from MeowRobot import pbot


@pbot.on_message(filters.command(["wall", "wallpaper"]))
async def wall(_, message: Message):
    try:
        text = message.text.split(None, 1)[1]
    except IndexError:
        text = None
    if not text:
        return await message.reply_text("`Please give some query to search.`")

    m = await message.reply_text("`Searching for wallpapers...`")

    loop = asyncio.get_event_loop()
    try:
        response = await loop.run_in_executor(None, requests.get, f"https://api.safone.me/wall?query={text}")
        results = response.json().get("results", [])
        if not results:
             await m.edit_text(f"`ᴡᴀʟʟᴘᴀᴘᴇʀ ɴᴏᴛ ғᴏᴜɴᴅ ғᴏʀ : `{text}`")
             return

        ran = random.randint(0, min(len(results) - 1, 5))
        image_url = results[ran]["imageUrl"]

        await message.reply_photo(
            photo=image_url,
            caption=f"🥀 **ʀᴇǫᴜᴇsᴛᴇᴅ ʙʏ :** {message.from_user.mention}",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("ʟɪɴᴋ", url=image_url)],
                ]
            ),
        )
        await m.delete()
    except Exception as e:
        await m.edit_text(f"Error searching wallpaper: {e}")


__mod_name__ = "Wᴀʟʟᴘᴀᴘᴇʀ"
__help__ = """
 ❍ /wall <query>*:* Search for wallpapers
"""
