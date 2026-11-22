#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import re
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from MeowRobot import application
from MeowRobot.modules.helper_funcs.chat_status import user_admin
from MeowRobot.modules.disable import DisableAbleCommandHandler
from MeowRobot.modules.sql import msgdelete_sql as sql

__mod_name__ = "Msg-Del"

__help__ = """
*Message Auto-Delete*

» /msgdelete on – Enable
» /msgdelete off – Disable
» /setmsgdelay 5m / 1h
» /msgstatus

Deletes ALL messages automatically (admins included).
"""


def parse(t):
    m = re.match(r"(\d+)([mh])", t)
    if not m:
        return None
    n = int(m.group(1))
    return n * 60 if m.group(2) == "m" else n * 3600


# ================= COMMANDS ================= #

@user_admin
async def msgdelete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.effective_message.reply_text("Use /msgdelete on/off")
        return

    chat = update.effective_chat.id

    if context.args[0].lower() == "on":
        sql.set_msg(chat, 1)
        await update.effective_message.reply_text("✅ Message Auto Delete Enabled")

    elif context.args[0].lower() == "off":
        sql.set_msg(chat, 0)
        await update.effective_message.reply_text("❌ Message Auto Delete Disabled")


@user_admin
async def setdelay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.effective_message.reply_text("Use /setmsgdelay 5m")
        return

    sec = parse(context.args[0])
    if not sec:
        await update.effective_message.reply_text("Use 5m or 1h")
        return

    sql.set_delay(update.effective_chat.id, sec)
    await update.effective_message.reply_text("⏱ Delay Updated")


async def msgstatus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat.id
    row = sql.get(chat)

    if not row:
        await update.effective_message.reply_text(
            "💬 Msg Auto Delete: OFF ❌\n⏱ Delay: 5 Minutes"
        )
        return

    status = "ON ✅" if row.enabled else "OFF ❌"
    delay = int(row.delay / 60)

    await update.effective_message.reply_text(
        f"💬 Msg Auto Delete: {status}\n⏱ Delay: {delay} Minutes"
    )


# ================= AUTO DELETE ================= #

async def delete_job(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id, msg_id = job.data

    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
    except:
        pass


async def auto_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or not update.effective_message:
        return
    chat = update.effective_chat.id
    try:
        row = sql.get(chat)
    except Exception:
        return

    if not row or not row.enabled:
        return

    delay = row.delay or 300

    context.job_queue.run_once(
        delete_job,
        delay,
        data=(chat, update.effective_message.message_id),
    )


# ================= HANDLERS ================= #

application.add_handler(DisableAbleCommandHandler("msgdelete", msgdelete))
application.add_handler(DisableAbleCommandHandler("setmsgdelay", setdelay))
application.add_handler(DisableAbleCommandHandler("msgstatus", msgstatus))

application.add_handler(
    MessageHandler(filters.ALL, auto_delete),
    group=20,
)
