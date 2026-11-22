#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import html
import time
from datetime import datetime
from io import BytesIO

from telegram import Update
from telegram.constants import ParseMode, ChatType, ChatMemberStatus
from telegram.error import BadRequest, TelegramError, Forbidden
from telegram.ext import ContextTypes, CommandHandler, filters, MessageHandler
from telegram.helpers import mention_html

import MeowRobot.modules.sql.global_bans_sql as sql
from MeowRobot import (
    DEMONS,
    DEV_USERS,
    DRAGONS,
    EVENT_LOGS,
    OWNER_ID,
    STRICT_GBAN,
    SUPPORT_CHAT,
    TIGERS,
    WOLVES,
    application,
)
from MeowRobot.modules.helper_funcs.alternate import send_message
from MeowRobot.modules.helper_funcs.chat_status import (
    is_user_admin,
    support_plus,
    user_admin,
)
from MeowRobot.modules.helper_funcs.extraction import (
    extract_user,
    extract_user_and_text,
)
from MeowRobot.modules.helper_funcs.misc import send_to_list
from MeowRobot.modules.sql.users_sql import get_user_com_chats

GBAN_ENFORCE_GROUP = 6

GBAN_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Peer_id_invalid",
    "Group chat was deactivated",
    "Need to be inviter of a user to kick it from a basic group",
    "Chat_admin_required",
    "Only the creator of a basic group can kick group administrators",
    "Channel_private",
    "Not in the chat",
    "Can't remove chat owner",
}

UNGBAN_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Method is available for supergroup and channel chats only",
    "Not in the chat",
    "Channel_private",
    "Chat_admin_required",
    "Peer_id_invalid",
    "User not found",
}


@support_plus
async def gban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot, args = context.bot, context.args
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    user_id, reason = await extract_user_and_text(message, args)

    if not user_id:
        await send_message(
            message,
            "You don't seem to be referring to a user or the ID specified is incorrect.."
        )
        return

    if int(user_id) in DEV_USERS:
        await send_message(
            message,
            "That user is part of the Association\nI can't act against our own."
        )
        return

    if int(user_id) in DRAGONS:
        await send_message(
            message,
            "I spy, with my little eye... a disaster! Why are you guys turning on each other?"
        )
        return

    if int(user_id) in DEMONS:
        await send_message(
            message,
            "OOOH someone's trying to gban a Demon Disaster! *grabs popcorn*"
        )
        return

    if int(user_id) in TIGERS:
        await send_message(message, "That's a Tiger! They cannot be banned!")
        return

    if int(user_id) in WOLVES:
        await send_message(message, "That's a Wolf! They cannot be banned!")
        return

    if user_id == bot.id:
        await send_message(message, "You uhh...want me to punch myself?")
        return

    if user_id in [777000, 1087968824]:
        await send_message(message, "Fool! You can't attack Telegram's native tech!")
        return

    try:
        user_chat = await bot.get_chat(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            await send_message(message, "I can't seem to find this user.")
            return
        else:
            return

    if user_chat.type == ChatType.CHANNEL:
        await send_message(message, "That's not a user!")
        return

    if sql.is_user_gbanned(user_id):
        if not reason:
            await send_message(
                message,
                "This user is already gbanned; I'd change the reason, but you haven't given me one..."
            )
            return

        old_reason = sql.update_gban_reason(
            user_id, user_chat.username or user_chat.first_name, reason
        )
        if old_reason:
            await send_message(
                message,
                "This user is already gbanned, for the following reason:\n"
                "<code>{}</code>\n"
                "I've gone and updated it with your new reason!".format(
                    html.escape(old_reason)
                ),
                parse_mode=ParseMode.HTML,
            )

        else:
            await send_message(
                message,
                "This user is already gbanned, but had no reason set; I've gone and updated it!"
            )

        return

    await send_message(message, "On it!")

    start_time = time.time()
    datetime_fmt = "%Y-%m-%dT%H:%M"
    current_time = datetime.utcnow().strftime(datetime_fmt)

    if chat.type != ChatType.PRIVATE:
        chat_origin = "<b>{} ({})</b>\n".format(html.escape(chat.title), chat.id)
    else:
        chat_origin = "<b>{}</b>\n".format(chat.id)

    log_message = (
        f"#GBANNED\n"
        f"<b>Originated from:</b> <code>{chat_origin}</code>\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>Banned User:</b> {mention_html(user_chat.id, user_chat.first_name)}\n"
        f"<b>Banned User ID:</b> <code>{user_chat.id}</code>\n"
        f"<b>Event Stamp:</b> <code>{current_time}</code>"
    )

    if reason:
        if chat.type == ChatType.SUPERGROUP and chat.username:
            log_message += f'\n<b>Reason:</b> <a href="https://telegram.me/{chat.username}/{message.message_id}">{reason}</a>'
        else:
            log_message += f"\n<b>Reason:</b> <code>{reason}</code>"

    if EVENT_LOGS:
        try:
            log = await bot.send_message(EVENT_LOGS, log_message, parse_mode=ParseMode.HTML)
        except BadRequest:
            log = await bot.send_message(
                EVENT_LOGS,
                log_message
                + "\n\nFormatting has been disabled due to an unexpected error.",
            )

    else:
        await send_to_list(bot, list(DRAGONS) + list(DEMONS), log_message, html=True)

    sql.gban_user(user_id, user_chat.username or user_chat.first_name, reason)

    com_chats = get_user_com_chats(user_id)
    gbanned_chats = 0

    for chat_id_str in com_chats:
        chat_id = int(chat_id_str)

        if not sql.does_chat_gban(chat_id):
            continue

        try:
            await bot.ban_chat_member(chat_id, user_id)
            gbanned_chats += 1

        except BadRequest as excp:
            if excp.message in GBAN_ERRORS:
                pass
            else:
                await send_message(message, f"Could not gban due to: {excp.message}")
                if EVENT_LOGS:
                    await bot.send_message(
                        EVENT_LOGS,
                        f"Could not gban due to {excp.message}",
                        parse_mode=ParseMode.HTML,
                    )
                else:
                    await send_to_list(
                        bot, list(DRAGONS) + list(DEMONS), f"Could not gban due to: {excp.message}"
                    )
                sql.ungban_user(user_id)
                return
        except TelegramError:
            pass

    if EVENT_LOGS:
        await log.edit_text(
            log_message + f"\n<b>Chats affected:</b> <code>{gbanned_chats}</code>",
            parse_mode=ParseMode.HTML,
        )
    else:
        await send_to_list(
            bot,
            list(DRAGONS) + list(DEMONS),
            f"Gban complete! (User banned in <code>{gbanned_chats}</code> chats)",
            html=True,
        )

    await send_message(message, "Done! Gbanned.", parse_mode=ParseMode.HTML)

    try:
        await bot.send_message(
            user_id,
            "#EVENT\n"
            "You have been marked as Malicious and as such have been banned from any future groups we manage."
            f"\n<b>Reason:</b> <code>{html.escape(reason or 'No reason')}</code>"
            f"\n<b>Appeal Chat:</b> @{SUPPORT_CHAT}",
            parse_mode=ParseMode.HTML,
        )
    except:
        pass


@support_plus
async def ungban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot, args = context.bot, context.args
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    user_id = await extract_user(message, args)

    if not user_id:
        await send_message(
            message,
            "You don't seem to be referring to a user or the ID specified is incorrect.."
        )
        return

    user_chat = await bot.get_chat(user_id)
    if user_chat.type == ChatType.CHANNEL:
        await send_message(message, "That's not a user!")
        return

    if not sql.is_user_gbanned(user_id):
        await send_message(message, "This user is not gbanned!")
        return

    await send_message(message, f"I'll give {user_chat.first_name} a second chance, globally.")

    start_time = time.time()
    datetime_fmt = "%Y-%m-%dT%H:%M"
    current_time = datetime.utcnow().strftime(datetime_fmt)

    if chat.type != ChatType.PRIVATE:
        chat_origin = f"<b>{html.escape(chat.title)} ({chat.id})</b>\n"
    else:
        chat_origin = f"<b>{chat.id}</b>\n"

    log_message = (
        f"#UNGBANNED\n"
        f"<b>Originated from:</b> <code>{chat_origin}</code>\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>Unbanned User:</b> {mention_html(user_chat.id, user_chat.first_name)}\n"
        f"<b>Unbanned User ID:</b> <code>{user_chat.id}</code>\n"
        f"<b>Event Stamp:</b> <code>{current_time}</code>"
    )

    if EVENT_LOGS:
        try:
            log = await bot.send_message(EVENT_LOGS, log_message, parse_mode=ParseMode.HTML)
        except BadRequest:
            log = await bot.send_message(
                EVENT_LOGS,
                log_message
                + "\n\nFormatting has been disabled due to an unexpected error.",
            )
    else:
        await send_to_list(bot, list(DRAGONS) + list(DEMONS), log_message, html=True)

    com_chats = get_user_com_chats(user_id)
    ungbanned_chats = 0

    for chat_id_str in com_chats:
        chat_id = int(chat_id_str)

        if not sql.does_chat_gban(chat_id):
            continue

        try:
            member = await bot.get_chat_member(chat_id, user_id)
            if member.status == ChatMemberStatus.BANNED:
                await bot.unban_chat_member(chat_id, user_id)
                ungbanned_chats += 1

        except BadRequest as excp:
            if excp.message in UNGBAN_ERRORS:
                pass
            else:
                await send_message(message, f"Could not un-gban due to: {excp.message}")
                if EVENT_LOGS:
                    await bot.send_message(
                        EVENT_LOGS,
                        f"Could not un-gban due to: {excp.message}",
                        parse_mode=ParseMode.HTML,
                    )
                else:
                    await bot.send_message(
                        OWNER_ID, f"Could not un-gban due to: {excp.message}"
                    )
                return
        except TelegramError:
            pass

    sql.ungban_user(user_id)

    if EVENT_LOGS:
        await log.edit_text(
            log_message + f"\n<b>Chats affected:</b> {ungbanned_chats}",
            parse_mode=ParseMode.HTML,
        )
    else:
        await send_to_list(bot, list(DRAGONS) + list(DEMONS), "un-gban complete!")

    await send_message(message, f"Person has been un-gbanned.")


@support_plus
async def gbanlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    banned_users = sql.get_gban_list()

    if not banned_users:
        await update.effective_message.reply_text(
            "There aren't any gbanned users! You're kinder than I expected..."
        )
        return

    banfile = "Screw these guys.\n"
    for user in banned_users:
        banfile += f"[x] {user['name']} - {user['user_id']}\n"
        if user["reason"]:
            banfile += f"Reason: {user['reason']}\n"

    with BytesIO(str.encode(banfile)) as output:
        output.name = "gbanlist.txt"
        await update.effective_message.reply_document(
            document=output,
            filename="gbanlist.txt",
            caption="Here is the list of currently gbanned users.",
        )


async def check_and_ban(update: Update, user_id, should_message=True):
    if sql.is_user_gbanned(user_id):
        try:
            await update.effective_chat.ban_member(user_id)
            if should_message:
                text = (
                    f"<b>Alert</b>: this user is globally banned.\n"
                    f"<code>*bans them from here*</code>.\n"
                    f"<b>Appeal chat</b>: @{SUPPORT_CHAT}\n"
                    f"<b>User ID</b>: <code>{user_id}</code>"
                )
                user = sql.get_gbanned_user(user_id)
                if user.reason:
                    text += f"\n<b>Ban Reason:</b> <code>{html.escape(user.reason)}</code>"
                await send_message(update.effective_message, text, parse_mode=ParseMode.HTML)
        except Exception:
            pass


async def enforce_gban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    try:
        member = await update.effective_chat.get_member(bot.id)
        restrict_permission = getattr(member, 'can_restrict_members', False) or member.status == ChatMemberStatus.OWNER
    except Exception:
        return

    if sql.does_chat_gban(update.effective_chat.id) and restrict_permission:
        user = update.effective_user
        chat = update.effective_chat
        msg = update.effective_message

        if user and not await is_user_admin(chat, user.id):
            await check_and_ban(update, user.id)
            return

        if msg.new_chat_members:
            for mem in msg.new_chat_members:
                await check_and_ban(update, mem.id)

        if msg.reply_to_message:
            user = msg.reply_to_message.from_user
            if user and not await is_user_admin(chat, user.id):
                await check_and_ban(update, user.id, should_message=False)


@user_admin
async def gbanstat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) > 0:
        if args[0].lower() in ["on", "yes"]:
            sql.enable_gbans(update.effective_chat.id)
            await send_message(
                update.effective_message,
                "Antispam is now enabled ✅ "
                "I am now protecting your group from potential remote threats!"
            )
        elif args[0].lower() in ["off", "no"]:
            sql.disable_gbans(update.effective_chat.id)
            await send_message(
                update.effective_message,
                "Antispam is now disabled ❌ " "Spamwatch is now disabled ❌"
            )
    else:
        await send_message(
            update.effective_message,
            "Give me some arguments to choose a setting! on/off, yes/no!\n\n"
            "Your current setting is: {}\n"
            "When True, any gbans that happen will also happen in your group. "
            "When False, they won't, leaving you at the possible mercy of "
            "spammers.".format(sql.does_chat_gban(update.effective_chat.id))
        )


def __stats__():
    return f"• {sql.num_gbanned_users()} gbanned users."


def __user_info__(user_id):
    is_gbanned = sql.is_user_gbanned(user_id)
    text = "Malicious: <b>{}</b>"
    if user_id in [777000, 1087968824]:
        return ""
    from MeowRobot import BOT_ID
    if user_id == BOT_ID:
        return ""
    if int(user_id) in list(DRAGONS) + list(TIGERS) + list(WOLVES):
        return ""
    if is_gbanned:
        text = text.format("ʏᴇs")
        user = sql.get_gbanned_user(user_id)
        if user.reason:
            text += f"\n<b>Reason:</b> <code>{html.escape(user.reason)}</code>"
        text += f"\n<b>Appeal Chat:</b> @{SUPPORT_CHAT}"
    else:
        text = text.format("ɴᴏ")
    return text


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    return f"This chat is enforcing *gbans*: `{sql.does_chat_gban(chat_id)}`."


GBAN_HANDLER = CommandHandler("gban", gban)
UNGBAN_HANDLER = CommandHandler("ungban", ungban)
GBAN_LIST = CommandHandler("gbanlist", gbanlist)
GBAN_STATUS = CommandHandler(
    "antispam", gbanstat, filters=filters.ChatType.GROUPS
)
GBAN_ENFORCER = MessageHandler(
    filters.ChatType.GROUPS, enforce_gban
)

application.add_handler(GBAN_HANDLER)
application.add_handler(UNGBAN_HANDLER)
application.add_handler(GBAN_LIST)
application.add_handler(GBAN_STATUS)

__mod_name__ = "Aɴᴛɪ-Sᴘᴀᴍ​"
__handlers__ = [GBAN_HANDLER, UNGBAN_HANDLER, GBAN_LIST, GBAN_STATUS]

if STRICT_GBAN:
    application.add_handler(GBAN_ENFORCER, GBAN_ENFORCE_GROUP)
    __handlers__.append((GBAN_ENFORCER, GBAN_ENFORCE_GROUP))
