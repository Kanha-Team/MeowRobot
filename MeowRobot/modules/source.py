#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

from platform import python_version as y

from pyrogram import __version__ as z
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from telegram import __version__ as o
from telethon import __version__ as s

from MeowRobot import BOT_NAME, BOT_USERNAME, OWNER_ID, START_IMG, pbot


@pbot.on_message(filters.command(["repo", "source"]))
async def repo(client, message: Message):
    bot_user = client.me or await client.get_me()
    bot_name = bot_user.first_name
    bot_username = bot_user.username
    await message.reply_photo(
        photo=START_IMG,
        caption=f"""**ʜᴇʏ {message.from_user.mention},

ɪ ᴀᴍ [{bot_name}](https://t.me/{bot_username})**

**» ᴍʏ ᴅᴇᴠᴇʟᴏᴘᴇʀ :** 𝐊ᴧηʜᴧ ꭙ 𝐓єᴧϻ
**» ᴩʏᴛʜᴏɴ ᴠᴇʀsɪᴏɴ :** `{y()}`
**» ʟɪʙʀᴀʀʏ ᴠᴇʀsɪᴏɴ :** `{o}` 
**» ᴛᴇʟᴇᴛʜᴏɴ ᴠᴇʀsɪᴏɴ :** `{s}` 
**» ᴘʏʀᴏɢʀᴀᴍ ᴠᴇʀsɪᴏɴ :** `{z}`
""",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("ᴅєᴠєʟσᴘєꝛ", user_id=OWNER_ID),
                    InlineKeyboardButton(
                        "sσυꝛᴄє",
                        url="https://github.com/Kanha-Team/MeowRobot",
                    ),
                ]
            ]
        ),
    )


__mod_name__ = "Rᴇᴩᴏ"
