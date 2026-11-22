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
from telegram.ext import ContextTypes

from MeowRobot import application
from MeowRobot.modules.disable import DisableAbleCommandHandler


async def truth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loop = asyncio.get_event_loop()
    try:
        response = await loop.run_in_executor(None, requests.get, "https://api.truthordarebot.xyz/v1/truth")
        truth_val = response.json()["question"]
    except:
        truth_val = "Error fetching truth."
    await update.effective_message.reply_text(truth_val)


async def dare(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loop = asyncio.get_event_loop()
    try:
        response = await loop.run_in_executor(None, requests.get, "https://api.truthordarebot.xyz/v1/dare")
        dare_val = response.json()["question"]
    except:
        dare_val = "Error fetching dare."
    await update.effective_message.reply_text(dare_val)


TRUTH_HANDLER = DisableAbleCommandHandler("truth", truth)
DARE_HANDLER = DisableAbleCommandHandler("dare", dare)

application.add_handler(TRUTH_HANDLER)
application.add_handler(DARE_HANDLER)


__help__ = """
*Truth & Dare*

 ❍ /truth *:* Sends a random truth string.
 ❍ /dare *:* Sends a random dare string.
"""

__mod_name__ = "Tʀᴜᴛʜ-Dᴀʀᴇ"
__handlers__ = [TRUTH_HANDLER, DARE_HANDLER]
