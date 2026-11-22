#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import os
import subprocess
import sys
import asyncio
from contextlib import suppress

from telegram import Update
from telegram.error import Forbidden
from telegram.ext import ContextTypes, CommandHandler

import MeowRobot
from MeowRobot import application
from MeowRobot.modules.helper_funcs.chat_status import dev_plus


@dev_plus
async def allow_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.effective_message.reply_text(f"Current state: {MeowRobot.ALLOW_CHATS}")
        return
    if args[0].lower() in ["off", "no"]:
        MeowRobot.ALLOW_CHATS = True
    elif args[0].lower() in ["yes", "on"]:
        MeowRobot.ALLOW_CHATS = False
    else:
        await update.effective_message.reply_text("Format: /lockdown Yes/No or Off/On")
        return
    await update.effective_message.reply_text("Done! Lockdown value toggled.")


@dev_plus
async def leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    args = context.args
    if args:
        chat_id = str(args[0])
        try:
            await bot.leave_chat(int(chat_id))
        except Exception:
            await update.effective_message.reply_text(
                "Beep boop, I could not leave that group(dunno why tho)."
            )
            return
        with suppress(Forbidden):
            await update.effective_message.reply_text("Beep boop, I left that soup!.")
    else:
        await update.effective_message.reply_text("Send a valid chat ID")


@dev_plus
async def gitpull(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sent_msg = await update.effective_message.reply_text(
        "Pulling all changes from remote and then attempting to restart."
    )
    subprocess.Popen("git pull", stdout=subprocess.PIPE, shell=True)

    sent_msg_text = sent_msg.text + "\n\nChanges pulled...I guess.. Restarting in "

    for i in reversed(range(5)):
        await sent_msg.edit_text(sent_msg_text + str(i + 1))
        await asyncio.sleep(1)

    await sent_msg.edit_text("Restarted.")
    os.execv(sys.executable, ['python3'] + sys.argv)


@dev_plus
async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "Starting a new instance and shutting down this one"
    )
    os.execv(sys.executable, ['python3'] + sys.argv)


LEAVE_HANDLER = CommandHandler("leave", leave)
GITPULL_HANDLER = CommandHandler("gitpull", gitpull)
RESTART_HANDLER = CommandHandler("reboot", restart)
ALLOWGROUPS_HANDLER = CommandHandler("lockdown", allow_groups)


application.add_handler(ALLOWGROUPS_HANDLER)
application.add_handler(LEAVE_HANDLER)
application.add_handler(GITPULL_HANDLER)
application.add_handler(RESTART_HANDLER)

__mod_name__ = "Dᴇᴠ"

__handlers__ = [LEAVE_HANDLER, GITPULL_HANDLER, RESTART_HANDLER, ALLOWGROUPS_HANDLER]
