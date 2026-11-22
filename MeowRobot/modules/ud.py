#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import asyncio
import requests
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from MeowRobot import application
from MeowRobot.modules.disable import DisableAbleCommandHandler


async def ud(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    text = message.text[len("/ud ") :]
    if not text:
        return

    loop = asyncio.get_event_loop()
    try:
        response = await loop.run_in_executor(None, requests.get, f"https://api.urbandictionary.com/v0/define?term={text}")
        results = response.json()
        reply_text = f'*{text}*\n\n{results["list"][0]["definition"]}\n\n_{results["list"][0]["example"]}_'
    except:
        reply_text = "No results found."
    await message.reply_text(reply_text, parse_mode=ParseMode.MARKDOWN)


UD_HANDLER = DisableAbleCommandHandler(["ud"], ud)

application.add_handler(UD_HANDLER)

__help__ = """
» /ud (text) *:* Searchs the given text on Urban Dictionary and sends you the information.
"""
__mod_name__ = "Urban-D"

__command_list__ = ["ud"]
__handlers__ = [UD_HANDLER]
