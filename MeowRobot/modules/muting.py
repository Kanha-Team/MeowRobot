#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import html

from telegram import Bot, Chat, ChatPermissions, Update
from telegram.constants import ParseMode, ChatMemberStatus
from telegram.error import BadRequest
from telegram.ext import ContextTypes, CommandHandler
from telegram.helpers import mention_html

from MeowRobot import LOGGER, TIGERS, application
from MeowRobot.modules.helper_funcs.alternate import send_message
from MeowRobot.modules.helper_funcs.chat_status import (
    bot_admin,
    can_restrict,
    connection_status,
    is_user_admin,
    user_admin,
)
from MeowRobot.modules.helper_funcs.extraction import (
    extract_user,
    extract_user_and_text,
)
from MeowRobot.modules.helper_funcs.string_handling import extract_time
from MeowRobot.modules.log_channel import loggable


async def check_user(user_id: int, bot: Bot, chat: Chat) -> str:
    if not user_id:
        return "You don't seem to be referring to a user or the ID specified is incorrect.."

    try:
        member = await chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            return "I can't seem to find this user"
        else:
            raise

    if user_id == bot.id:
        return "I'm not gonna MUTE myself, How high are you?"

    if await is_user_admin(chat, user_id, member) or user_id in TIGERS:
        return "Can't. Find someone else to mute but not this one."

    return ""


@connection_status
@bot_admin
@user_admin
@loggable
async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    bot = context.bot
    args = context.args

    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    user_id, reason = await extract_user_and_text(message, args)
    reply = await check_user(user_id, bot, chat)

    if reply:
        await send_message(message, reply)
        return ""

    member = await chat.get_member(user_id)

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#MUTE\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(member.user.id, member.user.first_name)}"
    )

    if reason:
        log += f"\n<b>Reason:</b> {reason}"

    if getattr(member, 'can_send_messages', True):
        chat_permissions = ChatPermissions(
            can_send_messages=False,
            can_send_photos=False,
            can_send_audios=False,
            can_send_videos=False,
            can_send_documents=False,
            can_send_video_notes=False,
            can_send_voice_notes=False,
            can_send_other_messages=False,
        )
        await bot.restrict_chat_member(chat.id, user_id, chat_permissions)
        await bot.send_message(
            chat.id,
            f"Muted <b>{html.escape(member.user.first_name)}</b> with no expiration date!",
            parse_mode=ParseMode.HTML,
        )
        return log

    else:
        await send_message(message, "This user is already muted!")

    return ""


@connection_status
@bot_admin
@user_admin
@loggable
async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    user_id = await extract_user(message, args)
    if not user_id:
        await send_message(
            message,
            "You'll need to either give me a username to unmute, or reply to someone to be unmuted."
        )
        return ""

    member = await chat.get_member(int(user_id))

    if member.status not in (ChatMemberStatus.LEFT, ChatMemberStatus.BANNED):
        if (
            getattr(member, 'can_send_messages', False)
            and getattr(member, 'can_send_photos', False)
            and getattr(member, 'can_send_audios', False)
            and getattr(member, 'can_send_videos', False)
            and getattr(member, 'can_send_documents', False)
            and getattr(member, 'can_send_video_notes', False)
            and getattr(member, 'can_send_voice_notes', False)
            and getattr(member, 'can_send_other_messages', False)
            and getattr(member, 'can_add_web_page_previews', False)
        ):
            await send_message(message, "This user already has the right to speak.")
        else:
            chat_permissions = ChatPermissions(
                can_send_messages=True,
                can_invite_users=True,
                can_pin_messages=True,
                can_send_polls=True,
                can_change_info=True,
                can_send_photos=True,
                can_send_audios=True,
                can_send_videos=True,
                can_send_documents=True,
                can_send_video_notes=True,
                can_send_voice_notes=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
            )
            try:
                await bot.restrict_chat_member(chat.id, int(user_id), chat_permissions)
            except BadRequest:
                pass
            await bot.send_message(
                chat.id,
                f"I shall allow <b>{html.escape(member.user.first_name)}</b> to text!",
                parse_mode=ParseMode.HTML,
            )
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#UNMUTE\n"
                f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                f"<b>User:</b> {mention_html(member.user.id, member.user.first_name)}"
            )
    else:
        await send_message(
            message,
            "This user isn't even in the chat, unmuting them won't make them talk more than they "
            "already do!"
        )

    return ""


@connection_status
@bot_admin
@can_restrict
@user_admin
@loggable
async def temp_mute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    user_id, reason = await extract_user_and_text(message, args)
    reply = await check_user(user_id, bot, chat)

    if reply:
        await send_message(message, reply)
        return ""

    member = await chat.get_member(user_id)

    if not reason:
        await send_message(message, "You haven't specified a time to mute this user for!")
        return ""

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    if len(split_reason) > 1:
        reason = split_reason[1]
    else:
        reason = ""

    mutetime = await extract_time(message, time_val)

    if not mutetime:
        return ""

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#TEMP MUTED\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(member.user.id, member.user.first_name)}\n"
        f"<b>Time:</b> {time_val}"
    )
    if reason:
        log += f"\n<b>Reason:</b> {reason}"

    try:
        if getattr(member, 'can_send_messages', True):
            chat_permissions = ChatPermissions(
                can_send_messages=False,
                can_send_photos=False,
                can_send_audios=False,
                can_send_videos=False,
                can_send_documents=False,
                can_send_video_notes=False,
                can_send_voice_notes=False,
                can_send_other_messages=False,
            )
            await bot.restrict_chat_member(
                chat.id, user_id, chat_permissions, until_date=mutetime
            )
            await bot.send_message(
                chat.id,
                f"Muted <b>{html.escape(member.user.first_name)}</b> for {time_val}!",
                parse_mode=ParseMode.HTML,
            )
            return log
        else:
            await message.reply_text("This user is already muted.")

    except BadRequest as excp:
        if excp.message in ("Reply message not found", "Message to be replied not found"):
            await send_message(message, f"Muted for {time_val}!", quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "ERROR muting user %s in chat %s (%s) due to %s",
                user_id,
                chat.title,
                chat.id,
                excp.message,
            )
            await send_message(message, "Well damn, I can't mute that user.")

    return ""


__help__ = """
*ᴀᴅᴍɪɴs ᴏɴʟʏ:*

 ❍ /mute <userhandle>*:* silences a user. Can also be used as a reply, muting the replied to user.
 ❍ /tmute <userhandle> x(m/h/d)*:* mutes a user for x time. (via handle, or reply). `m` = `minutes`, `h` = `hours`, `d` = `days`.
 ❍ /unmute <userhandle>*:* unmutes a user. Can also be used as a reply, muting the replied to user.
"""

MUTE_HANDLER = CommandHandler("mute", mute)
UNMUTE_HANDLER = CommandHandler("unmute", unmute)
TEMPMUTE_HANDLER = CommandHandler(["tmute", "tempmute"], temp_mute)

application.add_handler(MUTE_HANDLER)
application.add_handler(UNMUTE_HANDLER)
application.add_handler(TEMPMUTE_HANDLER)

__mod_name__ = "Mᴜᴛᴇ​"
__handlers__ = [MUTE_HANDLER, UNMUTE_HANDLER, TEMPMUTE_HANDLER]
