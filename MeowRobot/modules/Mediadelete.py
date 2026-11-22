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
from MeowRobot.modules.sql import mediadelete_sql as sql

__mod_name__ = "Media-Del"

__help__ = """
*Media Auto Delete*

» /mediadelete on – Enable
» /mediadelete off – Disable
» /setmediadelay 5m / 1h
» /mediastatus

Deletes photos, videos, stickers & GIFs automatically.
"""


def parse(t):
    m = re.match(r"(\d+)([mh])", t)
    if not m:
        return None
    n = int(m.group(1))
    return n * 60 if m.group(2) == "m" else n * 3600


@user_admin
async def mediadelete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.effective_message.reply_text("Use: /mediadelete on/off")
        return

    chat = update.effective_chat.id

    if context.args[0].lower() == "on":
        sql.set_media(chat, 1)
        await update.effective_message.reply_text("✅ Media Auto Delete Enabled")

    elif context.args[0].lower() == "off":
        sql.set_media(chat, 0)
        await update.effective_message.reply_text("❌ Media Auto Delete Disabled")


@user_admin
async def setdelay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.effective_message.reply_text("Example: /setmediadelay 5m")
        return

    sec = parse(context.args[0])
    if not sec:
        await update.effective_message.reply_text("Use 5m or 1h")
        return

    sql.set_delay(update.effective_chat.id, sec)
    await update.effective_message.reply_text("⏱ Delay Updated")


async def mediastatus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat.id
    row = sql.get(chat)

    if not row:
        await update.effective_message.reply_text(
            "📥 Media Auto Delete: OFF ❌\n⏱ Delay: 5 Minutes (default)"
        )
        return

    status = "ON ✅" if row.enabled else "OFF ❌"
    delay = int(row.delay / 60)

    await update.effective_message.reply_text(
        f"📥 Media Auto Delete: {status}\n⏱ Delay: {delay} Minutes"
    )


async def delete_media_job(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    try:
        await context.bot.delete_message(chat_id=job.data['chat_id'], message_id=job.data['message_id'])
    except:
        pass


async def delete_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or not update.effective_message:
        return
    chat = update.effective_chat.id
    try:
        row = sql.get(chat)
    except Exception:
        return

    if not row or not row.enabled:
        return

    msg = update.effective_message.message_id
    delay = row.delay or 300

    context.job_queue.run_once(
        delete_media_job,
        delay,
        data={"chat_id": chat, "message_id": msg},
        name="mediadelete",
    )


MEDIA_HANDLER = MessageHandler(
    filters.PHOTO | filters.VIDEO | filters.ANIMATION | filters.Sticker.ALL,
    delete_media,
)

# Handlers add
application.add_handler(DisableAbleCommandHandler("mediadelete", mediadelete))
application.add_handler(DisableAbleCommandHandler("setmediadelay", setdelay))
application.add_handler(DisableAbleCommandHandler("mediastatus", mediastatus))
application.add_handler(MEDIA_HANDLER)
