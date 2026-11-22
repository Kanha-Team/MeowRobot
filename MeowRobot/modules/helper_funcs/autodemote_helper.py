#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import time
from collections import defaultdict
from telegram.constants import ChatMemberStatus, ParseMode
from telegram.error import BadRequest
from telegram.helpers import mention_html
from telegram.ext import ContextTypes

from MeowRobot import (
    DEV_USERS,
    DRAGONS,
    DEMONS,
    TIGERS,
    WOLVES,
    OWNER_ID,
    LOGGER
)
from MeowRobot.modules.sql import autodemote_sql as sql

# Memory storage for ban tracking: {chat_id: {admin_id: [timestamp1, timestamp2, ...]}}
BAN_TRACKER = defaultdict(lambda: defaultdict(list))

async def record_ban(chat_id: int, admin_id: int, context: ContextTypes.DEFAULT_TYPE):
    is_enabled, limit, window = sql.get_autodemote_settings(chat_id)
    if not is_enabled:
        return

    LOGGER.info(f"Recording ban in {chat_id} by admin {admin_id}. Limit: {limit}, Window: {window}")

    # Exemption logic
    if admin_id == OWNER_ID or admin_id in DEV_USERS or admin_id in DRAGONS or admin_id in DEMONS or admin_id in TIGERS or admin_id in WOLVES:
        LOGGER.info(f"Admin {admin_id} is exempt from autodemote.")
        return

    # Check if admin is owner
    try:
        chat = await context.bot.get_chat(chat_id)
        member = await chat.get_member(admin_id)
        if member.status == ChatMemberStatus.OWNER:
            LOGGER.info(f"Admin {admin_id} is the chat owner, exempting.")
            return
    except BadRequest as e:
        LOGGER.error(f"Error getting member {admin_id} in {chat_id}: {e.message}")
        return

    now = time.time()
    chat_key = str(chat_id)
    admin_key = str(admin_id)

    chat_bans = BAN_TRACKER[chat_key][admin_key]

    # Clean up old timestamps
    chat_bans = [t for t in chat_bans if now - t <= window]
    chat_bans.append(now)
    BAN_TRACKER[chat_key][admin_key] = chat_bans

    LOGGER.info(f"Admin {admin_id} has {len(chat_bans)} bans in the last {window} seconds.")

    if len(chat_bans) >= limit:
        LOGGER.info(f"Autodemote threshold reached for admin {admin_id} in {chat_id}!")
        # Demote the admin
        try:
            # First check if bot has permission
            bot_member = await chat.get_member(context.bot.id)
            can_promote = (
                bot_member.status == ChatMemberStatus.OWNER or
                getattr(bot_member, 'can_promote_members', False)
            )

            if not can_promote:
                LOGGER.warning(f"Cannot demote admin {admin_id} in {chat_id}: Bot lacks can_promote_members permission.")
                return

            # Demote
            await context.bot.promote_chat_member(
                chat.id,
                admin_id,
                can_change_info=False,
                can_delete_messages=False,
                can_invite_users=False,
                can_restrict_members=False,
                can_pin_messages=False,
                can_promote_members=False,
                can_manage_video_chats=False,
                can_manage_chat=False,
                can_manage_topics=False,
            )

            admin_user = await context.bot.get_chat(admin_id)
            await context.bot.send_message(
                chat.id,
                f"<b>ᴀᴜᴛᴏᴅᴇᴍᴏᴛᴇ ᴇᴠᴇɴᴛ !</b>\n"
                f"<b>• ᴀᴅᴍɪɴ:</b> {mention_html(admin_id, admin_user.first_name)}\n"
                f"<b>• ʀᴇᴀsᴏɴ:</b> Banned {len(chat_bans)} users in {window} seconds.\n"
                f"<b>• ᴀᴄᴛɪᴏɴ:</b> Demoted to regular member.",
                parse_mode=ParseMode.HTML
            )
            # Clear tracker for this admin to avoid multiple notifications
            BAN_TRACKER[chat_key][admin_key] = []

        except BadRequest as e:
            LOGGER.error(f"Failed to autodemote {admin_id} in {chat.id}: {e.message}")
            if "Not enough rights" in e.message or "CHATMEMBER_PRIVILEGES_CONFIDENTIAL" in e.message:
                 await context.bot.send_message(
                     chat.id,
                     f"⚠️ <b>ᴀᴜᴛᴏᴅᴇᴍᴏᴛᴇ ғᴀɪʟᴇᴅ !</b>\n"
                     f"I tried to demote {mention_html(admin_id, 'Admin')} for mass banning, but I don't have the power to edit this admin.\n"
                     f"Make sure I was the one who promoted them, or I am the creator (and I have promote permissions).",
                     parse_mode=ParseMode.HTML
                 )
