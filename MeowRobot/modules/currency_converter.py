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
from telegram.ext import ContextTypes, CommandHandler

from MeowRobot import CASH_API_KEY, application


async def convert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = update.effective_message.text.split(" ")

    if len(args) == 4:
        try:
            orig_cur_amount = float(args[1])
        except ValueError:
            await update.effective_message.reply_text("Invalid Amount Of Currency")
            return

        orig_cur = args[2].upper()
        new_cur = args[3].upper()

        request_url = (
            f"https://www.alphavantage.co/query"
            f"?function=CURRENCY_EXCHANGE_RATE"
            f"&from_currency={orig_cur}"
            f"&to_currency={new_cur}"
            f"&apikey={CASH_API_KEY}"
        )

        loop = asyncio.get_event_loop()
        try:
            response = await loop.run_in_executor(None, requests.get, request_url)
            data = response.json()
            current_rate = float(
                data["Realtime Currency Exchange Rate"]["5. Exchange Rate"]
            )
        except (KeyError, Exception):
            await update.effective_message.reply_text("Currency Not Supported or API error.")
            return

        new_cur_amount = round(orig_cur_amount * current_rate, 5)
        await update.effective_message.reply_text(
            f"{orig_cur_amount} {orig_cur} = {new_cur_amount} {new_cur}"
        )

    elif len(args) == 1:
        await update.effective_message.reply_text(__help__, parse_mode=ParseMode.MARKDOWN)

    else:
        await update.effective_message.reply_text(
            f"*Invalid Args!!:* Required 3 But Passed {len(args) - 1}",
            parse_mode=ParseMode.MARKDOWN,
        )


__mod_name__ = "Cᴀsʜ"

__help__ = """
Converts money from one exchange to another

Usage: /cash amount from to
Example: /cash 20 USD INR
"""

CONVERTER_HANDLER = CommandHandler("cash", convert)
application.add_handler(CONVERTER_HANDLER)
__command_list__ = ["cash"]

__handlers__ = [CONVERTER_HANDLER]
