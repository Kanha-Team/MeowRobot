#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import html
import io
import random
import sys
import traceback

import pretty_errors
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CommandHandler

from MeowRobot import DEV_USERS, OWNER_ID, application

pretty_errors.mono()


class ErrorsDict(dict):
    "A custom dict to store errors and their count"

    def __init__(self, *args, **kwargs):
        self.raw = []
        super().__init__(*args, **kwargs)

    def __contains__(self, error):
        self.raw.append(error)
        error.identifier = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=5))
        for e in self:
            if type(e) is type(error) and e.args == error.args:
                self[e] += 1
                return True
        self[error] = 0
        return False

    def __len__(self):
        return len(self.raw)


errors = ErrorsDict()


async def error_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update:
        return
    if context.error in errors:
        return
    try:
        stringio = io.StringIO()
        pretty_errors.output_stderr = stringio
        pretty_errors.excepthook(
            type(context.error), context.error, context.error.__traceback__
        )
        pretty_errors.output_stderr = sys.stderr
        pretty_error = stringio.getvalue()
        stringio.close()
    except Exception:
        pretty_error = "Failed to create pretty error."
    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__
    )
    tb = "".join(tb_list)
    pretty_message = (
        "{}\n"
        "-------------------------------------------------------------------------------\n"
        "An exception was raised while handling an update\n"
        "User: {}\n"
        "Chat: {} {}\n"
        "Callback data: {}\n"
        "Message: {}\n\n"
        "Full Traceback: {}"
    ).format(
        pretty_error,
        update.effective_user.id if update.effective_user else "Unknown",
        update.effective_chat.title if update.effective_chat else "",
        update.effective_chat.id if update.effective_chat else "",
        update.callback_query.data if update.callback_query else "None",
        update.effective_message.text if update.effective_message else "No message",
        tb,
    )

    try:
        key = requests.post(
            "https://nekobin.com/api/documents", json={"content": pretty_message}, timeout=10
        ).json()
    except Exception:
        key = {}

    e = html.escape(f"{context.error}")
    if not key.get("result", {}).get("key"):
        with open("error.txt", "w+") as f:
            f.write(pretty_message)
        with open("error.txt", "rb") as f:
            await context.bot.send_document(
                OWNER_ID,
                f,
                caption=f"#{context.error.identifier}\n<b>An unknown error occured:</b>\n<code>{e}</code>",
                parse_mode=ParseMode.HTML,
            )
        return

    key = key.get("result").get("key")
    url = f"https://nekobin.com/{key}.py"
    await context.bot.send_message(
        OWNER_ID,
        text=f"#{context.error.identifier}\n<b>An unknown error occured:</b>\n<code>{e}</code>",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ɴᴇᴋᴏʙɪɴ", url=url)]]),
        parse_mode=ParseMode.HTML,
    )


async def list_errors(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in DEV_USERS:
        return
    e = {
        k: v for k, v in sorted(errors.items(), key=lambda item: item[1], reverse=True)
    }
    msg = "<b>Errors List:</b>\n"
    for x in e:
        msg += f"• <code>{x}:</code> <b>{e[x]}</b> #{x.identifier}\n"
    msg += f"{len(errors)} have occurred since startup."
    if len(msg) > 4096:
        with open("errors_msg.txt", "w+") as f:
            f.write(msg)
        with open("errors_msg.txt", "rb") as f:
            await context.bot.send_document(
                update.effective_chat.id,
                f,
                caption="Too many errors have occured..",
                parse_mode=ParseMode.HTML,
            )
        return
    await update.effective_message.reply_text(msg, parse_mode=ParseMode.HTML)


application.add_error_handler(error_callback)
application.add_handler(CommandHandler("errors", list_errors))
