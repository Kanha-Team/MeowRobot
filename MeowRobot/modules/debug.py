#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import datetime
import os

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from telethon import events

from MeowRobot import application, telethn
from MeowRobot.modules.helper_funcs.chat_status import dev_plus

DEBUG_MODE = False


@dev_plus
async def debug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global DEBUG_MODE
    args = update.effective_message.text.split(None, 1)
    message = update.effective_message
    if len(args) > 1:
        if args[1] in ("yes", "on"):
            DEBUG_MODE = True
            await message.reply_text("Debug mode is now on.")
        elif args[1] in ("no", "off"):
            DEBUG_MODE = False
            await message.reply_text("Debug mode is now off.")
    else:
        if DEBUG_MODE:
            await message.reply_text("Debug mode is currently on.")
        else:
            await message.reply_text("Debug mode is currently off.")


@telethn.on(events.NewMessage(pattern="[/!].*"))
async def i_do_nothing_yes(event):
    if DEBUG_MODE:
        log_entry = f"- {event.sender_id} ({event.chat_id}) : {event.text} | {datetime.datetime.now()}\n"
        with open("updates.txt", "a+") as f:
            f.write(log_entry)


@dev_plus
async def logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if os.path.exists("log.txt"):
        with open("log.txt", "rb") as f:
            await context.bot.send_document(document=f, filename=f.name, chat_id=user.id)
    else:
        await update.effective_message.reply_text("Log file not found.")


LOG_HANDLER = CommandHandler("logs", logs)
DEBUG_HANDLER = CommandHandler("debug", debug)

application.add_handler(LOG_HANDLER)
application.add_handler(DEBUG_HANDLER)

__mod_name__ = "Debug"
__command_list__ = ["debug"]
__handlers__ = [DEBUG_HANDLER]
