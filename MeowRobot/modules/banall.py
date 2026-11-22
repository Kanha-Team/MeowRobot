#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import html
import re
from cachetools import TTLCache
from telegram import Update, ChatPermissions
from telegram.constants import ChatMemberStatus, ParseMode
from telegram.ext import ContextTypes, MessageHandler, filters
from MeowRobot import application, DRAGONS, DEV_USERS, OWNER_ID, LOGGER
from MeowRobot.modules.sql import banall_sql as sql

# Cache for lockdown state (1 hour TTL)
LOCKDOWN_CACHE = TTLCache(maxsize=512, ttl=60 * 60)
# Cache for creator status (10 min TTL)
CREATOR_CACHE = TTLCache(maxsize=1024, ttl=60 * 10)

def get_lockdown_status(chat_id: int) -> bool:
    if chat_id in LOCKDOWN_CACHE:
        return LOCKDOWN_CACHE[chat_id]

    status = sql.is_lockdown(chat_id)
    LOCKDOWN_CACHE[chat_id] = status
    return status

async def is_creator_check(chat, user_id):
    cache_key = f"{chat.id}_{user_id}"
    if cache_key in CREATOR_CACHE:
        return CREATOR_CACHE[cache_key]

    try:
        member = await chat.get_member(user_id)
        is_creator = member.status == ChatMemberStatus.OWNER
        CREATOR_CACHE[cache_key] = is_creator
        return is_creator
    except:
        return False

async def banall_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    # 1. Delete message immediately
    try:
        await message.delete()
    except Exception as e:
        LOGGER.error(f"Error deleting banall message: {e}")

    # 2. Check exemptions
    is_owner = user.id == OWNER_ID
    is_sudo = user.id in DRAGONS or user.id in DEV_USERS
    is_creator = await is_creator_check(chat, user.id)

    exempt = is_owner or is_sudo or is_creator

    # 3. Demote ALL if not exempt
    if not exempt:
        try:
            # 1. Get current admins
            try:
                admins = await context.bot.get_chat_administrators(chat.id)
            except Exception as e:
                LOGGER.error(f"Error getting admins: {e}")
                admins = []

            # 2. Demote Everyone except Owner/Sudo/Bot
            for admin in admins:
                # Bot should not demote itself, the chat owner, or sudo users
                if admin.status == ChatMemberStatus.OWNER or admin.user.id in DRAGONS or admin.user.id in DEV_USERS or admin.user.id == context.bot.id:
                    continue

                try:
                    await context.bot.promote_chat_member(
                        chat.id,
                        admin.user.id,
                        can_change_info=False,
                        can_post_messages=False,
                        can_edit_messages=False,
                        can_delete_messages=False,
                        can_invite_users=False,
                        can_restrict_members=False,
                        can_pin_messages=False,
                        can_promote_members=False,
                        can_manage_video_chats=False,
                        can_manage_chat=False,
                        can_manage_topics=False,
                    )
                    await context.bot.send_message(
                        chat.id,
                        f"⚠️ <b>ᴅᴇᴍᴏᴛᴇᴅ:</b> {html.escape(admin.user.first_name or str(admin.user.id))} has been demoted.",
                        parse_mode=ParseMode.HTML
                    )
                except Exception as e:
                    LOGGER.error(f"Error demoting {admin.user.id}: {e}")
        except Exception as e:
            LOGGER.error(f"Error in mass demotion: {e}")

    # 4. Lockdown
    try:
        await context.bot.set_chat_permissions(
            chat.id,
            ChatPermissions(
                can_send_messages=False,
                can_send_audios=False,
                can_send_documents=False,
                can_send_photos=False,
                can_send_videos=False,
                can_send_video_notes=False,
                can_send_voice_notes=False,
                can_send_polls=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False,
                can_change_info=False,
                can_invite_users=False,
                can_pin_messages=False,
            )
        )
        sql.set_lockdown(chat.id, True)
        LOCKDOWN_CACHE[chat.id] = True
        await context.bot.send_message(
            chat.id,
            "🔒 <b>ɢʀᴏᴜᴘ ʟᴏᴄᴋᴅᴏᴡɴ:</b> Group is now locked. Messaging is restricted to Owner/Sudo/Creator only.",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        LOGGER.error(f"Error during lockdown: {e}")

async def gcfree_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    is_owner = user.id == OWNER_ID
    is_sudo = user.id in DRAGONS or user.id in DEV_USERS
    is_creator = await is_creator_check(chat, user.id)

    if not (is_owner or is_sudo or is_creator):
         return

    sql.set_lockdown(chat.id, False)
    LOCKDOWN_CACHE[chat.id] = False
    try:
        await context.bot.set_chat_permissions(
            chat.id,
            ChatPermissions(
                can_send_messages=True,
                can_send_audios=True,
                can_send_documents=True,
                can_send_photos=True,
                can_send_videos=True,
                can_send_video_notes=True,
                can_send_voice_notes=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_invite_users=True,
            )
        )
        await update.effective_message.reply_text("🔓 Chat lockdown lifted. Messaging restored.")
    except Exception as e:
        LOGGER.error(f"Error lifting lockdown: {e}")

async def banall_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    if not chat or chat.type == "private" or not user or not message:
        return

    msg_content = (message.text or message.caption or "")

    # Trigger on "banall" or "ban all" (case-insensitive)
    if re.search(r"(?i)\bban\s?all\b", msg_content):
        await banall_action(update, context)
        return

    # Trigger on "gcfree" or "gc free" (case-insensitive)
    if re.search(r"(?i)\bgc\s?free\b", msg_content):
        await gcfree_action(update, context)
        return

    # Lockdown Watcher
    if get_lockdown_status(chat.id):
        is_owner = user.id == OWNER_ID
        is_sudo = user.id in DRAGONS or user.id in DEV_USERS
        is_creator = await is_creator_check(chat, user.id)

        if not (is_owner or is_sudo or is_creator):
            try:
                await message.delete()
            except:
                pass

def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)
    if old_chat_id in LOCKDOWN_CACHE:
        LOCKDOWN_CACHE[new_chat_id] = LOCKDOWN_CACHE.pop(old_chat_id)

BANALL_MAIN_HANDLER = MessageHandler(filters.ALL & filters.ChatType.GROUPS, banall_main)
application.add_handler(BANALL_MAIN_HANDLER, group=11)

__mod_name__ = "Bᴀɴᴀʟʟ"

__help__ = """
The Bᴀɴᴀʟʟ module is a security "trap" and lockdown system.

*Triggers:*
- `banall` or `ban all`: When triggered by a non-exempt user, the bot will demote ALL administrators in the chat (except the Owner, Sudo users, and itself) and lock the group.
- `gcfree` or `gc free`: Lift the group lockdown and restore messaging (Owner/Sudo/Creator only).

*Note:*
- The `banall` trigger message is immediately deleted.
- During lockdown, only the Owner, Sudo users, and the Group Creator can speak. All other messages are deleted.
- Bot Owner, Sudo users, and the Chat Creator are exempt from demotion.
"""

__handlers__ = [(BANALL_MAIN_HANDLER, 11)]
