#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import html
from telegram import Update
from telegram.constants import ParseMode, ChatType, ChatMemberStatus
from telegram.ext import ContextTypes, CommandHandler, ChatMemberHandler

from MeowRobot import (
    application,
)
from MeowRobot.modules.helper_funcs.chat_status import (
    connection_status,
    user_admin,
)
from MeowRobot.modules.sql import autodemote_sql as sql
from MeowRobot.modules.helper_funcs.autodemote_helper import record_ban

@connection_status
@user_admin
async def autodemote_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    args = context.args

    if not args:
        is_enabled, limit, window = sql.get_autodemote_settings(chat.id)
        status = "ENABLED" if is_enabled else "DISABLED"
        await update.effective_message.reply_text(
            f"<b>ᴀᴜᴛᴏᴅᴇᴍᴏᴛᴇ sᴛᴀᴛᴜs ɪɴ {html.escape(chat.title)}:</b>\n"
            f"<b>• sᴛᴀᴛᴜs:</b> {status}\n"
            f"<b>• ʟɪᴍɪᴛ:</b> {limit} bans in {window} seconds",
            parse_mode=ParseMode.HTML,
        )
        return

    toggle = args[0].lower()
    if toggle in ("on", "enable", "yes"):
        sql.set_autodemote(chat.id, True)
        await update.effective_message.reply_text(f"ᴀᴜᴛᴏᴅᴇᴍᴏᴛᴇ has been <b>ENABLED</b> in {html.escape(chat.title)}.", parse_mode=ParseMode.HTML)
    elif toggle in ("off", "disable", "no"):
        sql.set_autodemote(chat.id, False)
        await update.effective_message.reply_text(f"ᴀᴜᴛᴏᴅᴇᴍᴏᴛᴇ has been <b>DISABLED</b> in {html.escape(chat.title)}.", parse_mode=ParseMode.HTML)
    else:
        await update.effective_message.reply_text("Use 'on' or 'off' to enable/disable autodemote.")

@connection_status
@user_admin
async def set_autodemote_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    args = context.args

    if len(args) < 2:
        await update.effective_message.reply_text(
            "Usage: /setautodemote <limit> <time_window>\n"
            "Example: /setautodemote 3 10 (3 bans in 10 seconds)"
        )
        return

    try:
        limit = int(args[0])
        window = int(args[1])
    except ValueError:
        await update.effective_message.reply_text("Limit and time window must be integers.")
        return

    if limit < 1 or window < 1:
        await update.effective_message.reply_text("Limit and time window must be greater than 0.")
        return

    sql.set_autodemote_limit(chat.id, limit, window)
    await update.effective_message.reply_text(
        f"ᴀᴜᴛᴏᴅᴇᴍᴏᴛᴇ limit set to <b>{limit}</b> bans in <b>{window}</b> seconds for {html.escape(chat.title)}.",
        parse_mode=ParseMode.HTML
    )

async def ban_monitor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.chat_member or not update.chat_member.new_chat_member:
        return

    chat = update.effective_chat
    if not chat or chat.type == ChatType.PRIVATE:
        return

    new_member = update.chat_member.new_chat_member
    old_member = update.chat_member.old_chat_member

    # Check if it's a ban (status changed to BANNED)
    if new_member.status != ChatMemberStatus.BANNED:
        return

    # If it was already banned, it might just be an update of some other info
    if old_member and old_member.status == ChatMemberStatus.BANNED:
        return

    # Who did the banning?
    admin = update.chat_member.from_user
    if not admin or admin.is_bot:
        return

    await record_ban(chat.id, admin.id, context)

def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)

__help__ = """
• /autodemote: Check current autodemote status and settings
• /autodemote <on/off>: Enable or disable autodemote protection
• /setautodemote <limit> <time>: Set ban limits (e.g., /setautodemote 3 10 means demote if 3 bans in 10 seconds)

<b>Notes:</b>
• The bot needs "can_promote_members" permission to demote admins
• Chat owners and sudo users cannot be demoted
• Settings are per-chat
• Bot's own bans are not counted toward limits
• Default: 3 bans in 10 seconds
"""

__mod_name__ = "Auto-Demote"

AUTODEMOTE_HANDLER = CommandHandler("autodemote", autodemote_toggle)
SETAUTODEMOTE_HANDLER = CommandHandler("setautodemote", set_autodemote_limit)
BAN_MONITOR_HANDLER = ChatMemberHandler(ban_monitor, ChatMemberHandler.CHAT_MEMBER)

application.add_handler(AUTODEMOTE_HANDLER)
application.add_handler(SETAUTODEMOTE_HANDLER)
application.add_handler(BAN_MONITOR_HANDLER)

__handlers__ = [AUTODEMOTE_HANDLER, SETAUTODEMOTE_HANDLER, BAN_MONITOR_HANDLER]
