#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import asyncio
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from MeowRobot import BOT_NAME, BOT_USERNAME, application
from MeowRobot.modules.disable import DisableAbleCommandHandler


async def handwrite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if message.reply_to_message:
        text = message.reply_to_message.text
    else:
        try:
            text = update.effective_message.text.split(None, 1)[1]
        except IndexError:
            await message.reply_text("Provide some text to write!")
            return

    m = await message.reply_text("Writing the text...")

    loop = asyncio.get_event_loop()
    try:
        response = await loop.run_in_executor(None, requests.get, f"https://api.sdbots.tk/write?text={text}")
        req_url = response.url
        await message.reply_photo(
            photo=req_url,
            caption=f"""
Successfully Written Text 💘

✨ **Written By :** [{BOT_NAME}](https://t.me/{BOT_USERNAME})
🥀 **Requested by :** {update.effective_user.first_name}
❄ **Link :** `{req_url}`""",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("• ᴛᴇʟᴇɢʀᴀᴩʜ •", url=req_url),
                    ],
                ]
            ),
        )
    except Exception as e:
        await message.reply_text(f"Error: {e}")

    await m.delete()


__help__ = """
 Writes the given text on white page with a pen 🖊

❍ /write <text> *:*Writes the given text.
"""

WRITE_HANDLER = DisableAbleCommandHandler("write", handwrite)
application.add_handler(WRITE_HANDLER)

__mod_name__ = "WʀɪᴛᴇTᴏᴏʟ"

__command_list__ = ["write"]
__handlers__ = [WRITE_HANDLER]
