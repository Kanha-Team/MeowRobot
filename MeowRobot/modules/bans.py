#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import html

from telegram import Update
from telegram.constants import ChatType, ParseMode, ChatMemberStatus
from telegram.error import BadRequest
from telegram.ext import ContextTypes, CommandHandler, filters
from telegram.helpers import mention_html

from MeowRobot import (
    DEV_USERS,
    LOGGER,
    OWNER_ID,
    TIGERS,
    DRAGONS,
    DEMONS,
    WOLVES,
    application,
)
from MeowRobot.modules.disable import DisableAbleCommandHandler
from MeowRobot.modules.helper_funcs.alternate import send_message
from MeowRobot.modules.helper_funcs.chat_status import (
    bot_admin,
    can_delete,
    can_restrict,
    connection_status,
    is_user_admin,
    is_user_ban_protected,
    is_user_in_chat,
    user_admin,
    user_can_ban,
)
from MeowRobot.modules.helper_funcs.extraction import extract_user_and_text
from MeowRobot.modules.helper_funcs.string_handling import extract_time
from MeowRobot.modules.log_channel import gloggable, loggable
from MeowRobot.modules.helper_funcs.autodemote_helper import record_ban


@connection_status
@bot_admin
@can_restrict
@user_admin
@user_can_ban
@loggable
async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    log_message = ""
    bot = context.bot
    args = context.args
    user_id, reason = await extract_user_and_text(message, args)

    if not user_id:
        await send_message(message, "I doubt that's a user.")
        return log_message
    try:
        member = await chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != "User not found":
            raise
        await send_message(message, "Can't seem to find this person.")
        return log_message
    if user_id == bot.id:
        await send_message(message, "Oh yeah, ban myself, noob!")
        return log_message

    if await is_user_ban_protected(chat, user_id, member) and user.id not in DEV_USERS:
        if user_id == OWNER_ID:
            await send_message(message, "Trying to put me against a God level disaster huh?")
        elif user_id in DEV_USERS:
            await send_message(message, "I can't act against our own.")
        elif user_id in DRAGONS:
            await send_message(
                message,
                "Fighting this Dragon here will put civilian lives at risk."
            )
        elif user_id in DEMONS:
            await send_message(
                message,
                "Bring an order from Heroes association to fight a Demon disaster."
            )
        elif user_id in TIGERS:
            await send_message(
                message,
                "Bring an order from Heroes association to fight a Tiger disaster."
            )
        elif user_id in WOLVES:
            await send_message(message, "Wolf abilities make them ban immune!")
        else:
            await send_message(message, "This user has immunity and cannot be banned.")
        return log_message

    silent = message.text.startswith("/s")
    if silent and not await can_delete(chat, context.bot.id):
        return ""

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#{'S' if silent else ''}ʙᴀɴɴᴇᴅ\n"
        f"<b>ʙᴀɴɴᴇᴅ ʙʏ:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        f"<b>ᴜsᴇʀ:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}"
    )
    if reason:
        log += "\n<b>ʀᴇᴀsᴏɴ:</b> {}".format(reason)

    try:
        await chat.ban_member(user_id)
        await record_ban(chat.id, user.id, context)

        if silent:
            if message.reply_to_message:
                await message.reply_to_message.delete()
            await message.delete()
            return log

        reply = (
            f"<code>❕</code><b>ʙᴀɴ ᴇᴠᴇɴᴛ</b>\n"
            f"<code> </code><b>•  ʙᴀɴɴᴇᴅ ʙʏ:</b> {mention_html(user.id, user.first_name)}\n"
            f"<code> </code><b>•  ᴜsᴇʀ:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}"
        )
        if reason:
            reply += f"\n<code> </code><b>•  ʀᴇᴀsᴏɴ:</b> \n{html.escape(reason)}"
        await bot.send_message(chat.id, reply, parse_mode=ParseMode.HTML)
        return log

    except BadRequest as excp:
        if excp.message in ("Reply message not found", "Message to be replied not found"):
            if silent:
                return log
            await send_message(message, "ʙᴀɴɴᴇᴅ !", quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "ERROR banning user %s in chat %s (%s) due to %s",
                user_id,
                chat.title,
                chat.id,
                excp.message,
            )
            await send_message(message, "Well damn, I can't ban that user.")

    return log_message


@connection_status
@bot_admin
@can_restrict
@user_admin
@user_can_ban
@loggable
async def temp_ban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    log_message = ""
    bot, args = context.bot, context.args
    user_id, reason = await extract_user_and_text(message, args)

    if not user_id:
        await send_message(message, "I doubt that's a user.")
        return log_message

    try:
        member = await chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != "User not found":
            raise
        await send_message(message, "I can't seem to find this user.")
        return log_message
    if user_id == bot.id:
        await send_message(message, "I'm not gonna BAN myself, are you crazy?")
        return log_message

    if await is_user_ban_protected(chat, user_id, member):
        await send_message(message, "I don't feel like it.")
        return log_message

    if not reason:
        await send_message(message, "You haven't specified a time to ban this user for!")
        return log_message

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    reason = split_reason[1] if len(split_reason) > 1 else ""
    bantime = await extract_time(message, time_val)

    if not bantime:
        return log_message

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        "ᴛᴇᴍᴩ ʙᴀɴ\n"
        f"<b>ʙᴀɴɴᴇᴅ ʙʏ:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        f"<b>ᴜsᴇʀ:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}\n"
        f"<b>ᴛɪᴍᴇ:</b> {time_val}"
    )
    if reason:
        log += "\n<b>ʀᴇᴀsᴏɴ:</b> {}".format(reason)

    try:
        await chat.ban_member(user_id, until_date=bantime)
        await record_ban(chat.id, user.id, context)
        await bot.send_message(
            chat.id,
            f"ʙᴀɴɴᴇᴅ! ᴜsᴇʀ {mention_html(member.user.id, html.escape(member.user.first_name))} "
            f"ɪs ɴᴏᴡ ʙᴀɴɴᴇᴅ ғᴏʀ {time_val}.",
            parse_mode=ParseMode.HTML,
        )
        return log

    except BadRequest as excp:
        if excp.message in ("Reply message not found", "Message to be replied not found"):
            await send_message(
                message,
                f"Banned! User will be banned for {time_val}.", quote=False
            )
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "ERROR banning user %s in chat %s (%s) due to %s",
                user_id,
                chat.title,
                chat.id,
                excp.message,
            )
            await send_message(message, "Well damn, I can't ban that user.")

    return log_message


@connection_status
@bot_admin
@can_restrict
@user_admin
@user_can_ban
@loggable
async def kick(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    log_message = ""
    bot, args = context.bot, context.args
    user_id, reason = await extract_user_and_text(message, args)

    if not user_id:
        await send_message(message, "I doubt that's a user.")
        return log_message

    try:
        member = await chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != "User not found":
            raise

        await send_message(message, "I can't seem to find this user.")
        return log_message
    if user_id == bot.id:
        await send_message(message, "Yeahhh I'm not gonna do that.")
        return log_message

    if await is_user_ban_protected(chat, user_id):
        await send_message(message, "I really wish I could kick this user....")
        return log_message

    res = await chat.unban_member(user_id)  # unban on current user = kick
    if res:
        await record_ban(chat.id, user.id, context)
        await bot.send_message(
            chat.id,
            f"One Kicked! {mention_html(member.user.id, html.escape(member.user.first_name))}.",
            parse_mode=ParseMode.HTML,
        )
        log = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"ᴋɪᴄᴋᴇᴅ\n"
            f"<b>ᴋɪᴄᴋᴇᴅ ʙʏ:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            f"<b>ᴜsᴇʀ:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}"
        )
        if reason:
            log += f"\n<b>ʀᴇᴀsᴏɴ:</b> {reason}"

        return log

    else:
        await send_message(message, "Well damn, I can't kick that user.")

    return log_message


@bot_admin
@can_restrict
async def kickme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_message.from_user.id
    if await is_user_admin(update.effective_chat, user_id):
        await send_message(update.effective_message, "I wish I could... but you're an admin.")
        return

    res = await update.effective_chat.unban_member(user_id)  # unban on current user = kick
    if res:
        await send_message(update.effective_message, "*kicks you out of the group*")
    else:
        await send_message(update.effective_message, "Huh? I can't :/")


@connection_status
@bot_admin
@can_restrict
@user_admin
@user_can_ban
@loggable
async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    log_message = ""
    bot, args = context.bot, context.args
    user_id, reason = await extract_user_and_text(message, args)

    if not user_id:
        await send_message(message, "I doubt that's a user.")
        return log_message

    try:
        member = await chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != "User not found":
            raise
        await send_message(message, "I can't seem to find this user.")
        return log_message
    if user_id == bot.id:
        await send_message(message, "How would I unban myself if I wasn't here...?")
        return log_message

    if await is_user_in_chat(chat, user_id):
        await send_message(message, "Isn't this person already here??")
        return log_message

    await chat.unban_member(user_id)
    await send_message(message, "Yep, this user can join!")

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"ᴜɴʙᴀɴɴᴇᴅ\n"
        f"<b>ᴜɴʙʙᴀɴɴᴇᴅ ʙʏ:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        f"<b>ᴜsᴇʀ:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}"
    )
    if reason:
        log += f"\n<b>ʀᴇᴀsᴏɴ:</b> {reason}"

    return log


@connection_status
@bot_admin
@can_restrict
@gloggable
async def selfunban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    message = update.effective_message
    user = update.effective_user
    bot, args = context.bot, context.args
    if user.id not in DRAGONS and user.id not in TIGERS:
        return ""

    try:
        chat_id = int(args[0])
    except:
        await send_message(message, "Give a valid chat ID.")
        return ""

    chat = await bot.get_chat(chat_id)

    try:
        member = await chat.get_member(user.id)
    except BadRequest as excp:
        if excp.message == "User not found":
            await send_message(message, "I can't seem to find this user.")
            return ""
        else:
            raise

    if await is_user_in_chat(chat, user.id):
        await send_message(message, "Aren't you already in the chat??")
        return ""

    await chat.unban_member(user.id)
    await send_message(message, "Yep, I have unbanned you.")

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"ᴜɴʙᴀɴɴᴇᴅ\n"
        f"<b>ᴜɴʙᴀɴɴᴇᴅ ʙʏ:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>ᴜsᴇʀ:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}"
    )

    return log


__help__ = """
 ❍ /kickme*:* kicks the user who issued the command

*Admins only:*
 ❍ /ban <userhandle>*:* bans a user. (via handle, or reply)
 ❍ /sban <userhandle>*:* Silently ban a user. Deletes command, Replied message and doesn't reply. (via handle, or reply)
 ❍ /tban <userhandle> x(m/h/d)*:* bans a user for `x` time. (via handle, or reply). `m` = `minutes`, `h` = `hours`, `d` = `days`.
 ❍ /unban <userhandle>*:* unbans a user. (via handle, or reply)
 ❍ /kick <userhandle>*:* kicks a user out of the group, (via handle, or reply)
"""

BAN_HANDLER = CommandHandler(["ban", "sban"], ban)
TEMPBAN_HANDLER = CommandHandler(["tban"], temp_ban)
KICK_HANDLER = CommandHandler("kick", kick)
UNBAN_HANDLER = CommandHandler("unban", unban)
ROAR_HANDLER = CommandHandler("roar", selfunban)
KICKME_HANDLER = DisableAbleCommandHandler(
    "kickme", kickme, filters=filters.ChatType.GROUPS
)

application.add_handler(BAN_HANDLER)
application.add_handler(TEMPBAN_HANDLER)
application.add_handler(KICK_HANDLER)
application.add_handler(UNBAN_HANDLER)
application.add_handler(ROAR_HANDLER)
application.add_handler(KICKME_HANDLER)

__mod_name__ = "Bᴀɴs"
__handlers__ = [
    BAN_HANDLER,
    TEMPBAN_HANDLER,
    KICK_HANDLER,
    UNBAN_HANDLER,
    ROAR_HANDLER,
    KICKME_HANDLER,
]
