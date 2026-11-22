#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import html
import os
import re
import asyncio

import requests
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.constants import ParseMode, ChatType, MessageEntityType, ChatMemberStatus
from telegram.error import BadRequest
from telegram.ext import ContextTypes, CommandHandler
from telegram.helpers import escape_markdown, mention_html
from telethon import events
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.types import ChannelParticipantsAdmins

import MeowRobot.modules.sql.userinfo_sql as sql
from MeowRobot import (
    DEMONS,
    DEV_USERS,
    DRAGONS,
    INFOPIC,
    OWNER_ID,
    TIGERS,
    WOLVES,
    application,
    telethn,
)
from MeowRobot.__main__ import STATS, USER_INFO
from MeowRobot.modules.disable import DisableAbleCommandHandler
from MeowRobot.modules.helper_funcs.alternate import send_message
from MeowRobot.modules.helper_funcs.chat_status import sudo_plus
from MeowRobot.modules.helper_funcs.extraction import extract_user
from MeowRobot.modules.sql.global_bans_sql import is_user_gbanned
from MeowRobot.modules.sql.users_sql import get_user_num_chats


def no_by_per(totalhp, percentage):
    return totalhp * percentage / 100


def get_percentage(totalhp, earnedhp):
    matched_less = totalhp - earnedhp
    per_of_totalhp = 100 - matched_less * 100.0 / totalhp
    return str(int(per_of_totalhp))


async def hpmanager(user):
    total_hp = (get_user_num_chats(user.id) + 10) * 10

    if not is_user_gbanned(user.id):
        new_hp = total_hp

        if not user.username:
            new_hp -= no_by_per(total_hp, 25)
        try:
            photos = await application.bot.get_user_profile_photos(user.id)
            if not photos.photos:
                 new_hp -= no_by_per(total_hp, 25)
        except Exception:
            new_hp -= no_by_per(total_hp, 25)

        if not sql.get_user_me_info(user.id):
            new_hp -= no_by_per(total_hp, 20)
        if not sql.get_user_bio(user.id):
            new_hp -= no_by_per(total_hp, 10)
    else:
        new_hp = no_by_per(total_hp, 5)

    return {
        "earnedhp": int(new_hp),
        "totalhp": int(total_hp),
        "percentage": get_percentage(total_hp, new_hp),
    }


def make_bar(per):
    done = min(round(per / 10), 10)
    return "■" * done + "□" * (10 - done)


async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot, args = context.bot, context.args
    message = update.effective_message
    chat = update.effective_chat
    user_id = await extract_user(message, args)

    if user_id:
        if message.reply_to_message and message.reply_to_message.forward_origin:
            user1 = message.reply_to_message.from_user
            origin = message.reply_to_message.forward_origin

            user2_id = None
            user2_name = "Unknown"

            if origin.type == "user":
                 user2_id = origin.sender_user.id
                 user2_name = origin.sender_user.first_name
            elif origin.type == "hidden_user":
                 user2_name = origin.sender_user_name

            await send_message(
                message,
                f"<b>ᴛᴇʟᴇɢʀᴀᴍ ɪᴅ:</b>\n"
                f"• {html.escape(user2_name)} - <code>{user2_id or 'Hidden'}</code>.\n"
                f"• {html.escape(user1.first_name)} - <code>{user1.id}</code>.",
                parse_mode=ParseMode.HTML,
            )

        else:
            user_obj = await bot.get_chat(user_id)
            await send_message(
                message,
                f"{html.escape(user_obj.first_name)}'s ɪᴅ ɪs <code>{user_obj.id}</code>.",
                parse_mode=ParseMode.HTML,
            )

    else:
        if chat.type == ChatType.PRIVATE:
            await send_message(
                message,
                f"ʏᴏᴜʀ ᴜsᴇʀ ɪᴅ ɪs <code>{chat.id}</code>.", parse_mode=ParseMode.HTML
            )
        else:
            await send_message(
                message,
                f"ᴛʜɪs ɢʀᴏᴜᴩ's ɪᴅ ɪs <code>{chat.id}</code>.", parse_mode=ParseMode.HTML
            )


@telethn.on(
    events.NewMessage(
        pattern="/ginfo ", from_users=list(TIGERS or []) + list(DRAGONS or []) + list(DEMONS or [])
    )
)
async def group_info(event) -> None:
    chat_val = event.text.split(" ", 1)[1]
    try:
        entity = await event.client.get_entity(chat_val)
        totallist = await event.client.get_participants(
            entity, filter=ChannelParticipantsAdmins
        )
        ch_full = await event.client(GetFullChannelRequest(channel=entity))
    except:
        await event.reply(
            "Can't for some reason, maybe it is a private one or that I am banned there."
        )
        return
    msg = f"**ɪᴅ**: `{entity.id}`"
    msg += f"\n**ᴛɪᴛʟᴇ**: `{entity.title}`"
    msg += f"\n**ᴅᴄ**: `{entity.photo.dc_id if entity.photo else 'None'}`"
    msg += f"\n**ᴠɪᴅᴇᴏ ᴩғᴩ**: `{entity.photo.has_video if entity.photo else 'None'}`"
    msg += f"\n**sᴜᴩᴇʀɢʀᴏᴜᴩ**: `{entity.megagroup if hasattr(entity, 'megagroup') else 'None'}`"
    msg += f"\n**ʀᴇsᴛʀɪᴄᴛᴇᴅ**: `{entity.restricted}`"
    msg += f"\n**sᴄᴀᴍ**: `{entity.scam}`"
    msg += f"\n**sʟᴏᴡᴍᴏᴅᴇ**: `{entity.slowmode_enabled if hasattr(entity, 'slowmode_enabled') else 'None'}`"
    if entity.username:
        msg += f"\n**ᴜsᴇʀɴᴀᴍᴇ**: {entity.username}"
    msg += "\n\n**ᴍᴇᴍʙᴇʀ sᴛᴀᴛs:**"
    msg += f"\nᴀᴅᴍɪɴs: `{len(totallist)}`"
    msg += f"\nᴜsᴇʀs: `{totallist.total}`"
    msg += "\n\n**ᴀᴅᴍɪɴs ʟɪsᴛ:**"
    for x in totallist:
        msg += f"\n• [{x.id}](tg://user?id={x.id})"
    msg += f"\n\n**ᴅᴇsᴄʀɪᴩᴛɪᴏɴ**:\n`{ch_full.full_chat.about}`"
    await event.reply(msg)


async def gifid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if msg.reply_to_message and msg.reply_to_message.animation:
        await send_message(
            update.effective_message,
            f"Gif ID:\n<code>{msg.reply_to_message.animation.file_id}</code>",
            parse_mode=ParseMode.HTML,
        )
    else:
        await send_message(update.effective_message, "Please reply to a gif to get its ID.")
                        
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot, args = context.bot, context.args
    message = update.effective_message
    chat = update.effective_chat

    user_id = await extract_user(message, args)

    if user_id:
        user = await bot.get_chat(user_id)
    elif not message.reply_to_message and not args:
        user = message.from_user
    else:
        await send_message(message, "I can't extract a user from this.")
        return

    rep = await send_message(
        message,
        "<code>ᴀᴩᴩʀᴀɪsɪɴɢ...</code>",
        parse_mode=ParseMode.HTML
    )

    text = (
        f"ㅤ ㅤㅤ      ✦ ᴜsᴇʀ ɪɴғᴏ ✦\n"
        f"•❅─────✧❅✦❅✧─────❅•\n"
        f"➻ <b>ᴜsᴇʀ ɪᴅ:</b> <code>{user.id}</code>\n"
        f"➻ <b>ғɪʀsᴛ ɴᴀᴍᴇ:</b> {html.escape(user.first_name)}"
    )

    if user.last_name:
        text += f"\n➻ <b>ʟᴀsᴛ ɴᴀᴍᴇ:</b> {html.escape(user.last_name)}"

    if user.username:
        text += f"\n➻ <b>ᴜsᴇʀɴᴀᴍᴇ:</b> @{html.escape(user.username)}"

    text += f"\n➻ <b>ʟɪɴᴋ:</b> {mention_html(user.id, 'link')}"

    if chat.type != ChatType.PRIVATE and user.id != bot.id:
        try:
            member = await bot.get_chat_member(chat.id, user.id)
            status = member.status

            if status in (ChatMemberStatus.LEFT, ChatMemberStatus.BANNED):
                text += "\n➻ <b>ᴩʀᴇsᴇɴᴄᴇ:</b> <code>ɴᴏᴛ ʜᴇʀᴇ</code>"
            elif status == ChatMemberStatus.MEMBER:
                text += "\n➻ <b>ᴩʀᴇsᴇɴᴄᴇ:</b> <code>ᴅᴇᴛᴇᴄᴛᴇᴅ</code>"
            elif status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
                text += "\n➻ <b>ᴩʀᴇsᴇɴᴄᴇ:</b> <code>ᴀᴅᴍɪɴ</code>"
        except:
            pass

    if user.id not in [bot.id, 777000, 1087968824]:
        userhp = await hpmanager(user)
        text += (
            f"\n\n<b>ʜᴇᴀʟᴛʜ:</b> "
            f"<code>{userhp['earnedhp']}/{userhp['totalhp']}</code>\n"
            f"[<i>{make_bar(int(userhp['percentage']))}</i> {userhp['percentage']}%]"
        )

    if user.id == OWNER_ID:
        text += "\n\nᴛʜɪs ᴜsᴇʀ ɪs <b>OWNER</b>\n"
    elif user.id in DEV_USERS:
        text += "\n\nᴛʜɪs ᴜsᴇʀ ɪs <b>DEV</b>\n"
    elif user.id in DRAGONS:
        text += "\n\nᴛʜɪs ᴜsᴇʀ ɪs <b>DRAGON</b>\n"
    elif user.id in DEMONS:
        text += "\n\nᴛʜɪs ᴜsᴇʀ ɪs <b>DEMON</b>\n"
    elif user.id in TIGERS:
        text += "\n\nᴛʜɪs ᴜsᴇʀ ɪs <b>TIGER</b>\n"
    elif user.id in WOLVES:
        text += "\n\nᴛʜɪs ᴜsᴇʀ ɪs <b>WOLF</b>\n"

    try:
        user_member = await chat.get_member(user.id)
        if user_member.status == ChatMemberStatus.ADMINISTRATOR:
            text += f"\n\n<b>Title:</b> {user_member.custom_title or 'None'}"
    except:
        pass

    for mod in USER_INFO:
        try:
            mod_info = mod.__user_info__(user.id).strip()
        except TypeError:
            mod_info = mod.__user_info__(user.id, chat.id).strip()

        if mod_info:
            text += "\n\n" + mod_info

    # ✅ SEND MESSAGE
    sent = await send_message(
        message,
        text,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )

    await rep.delete()

    # ✅ AUTO DELETE AFTER 60s
    await asyncio.sleep(60)

    try:
        await sent.delete()
        await message.delete()  # optional
    except:
        pass
async def about_me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot, args = context.bot, context.args
    message = update.effective_message
    user_id = await extract_user(message, args)

    if user_id:
        user = await bot.get_chat(user_id)
    else:
        user = message.from_user

    info_text = sql.get_user_me_info(user.id)

    if info_text:
        await send_message(
            update.effective_message,
            f"*{user.first_name}*:\n{escape_markdown(info_text)}",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )
    elif message.reply_to_message:
        username = message.reply_to_message.from_user.first_name
        await send_message(
            update.effective_message,
            f"{username} hasn't set an info message about themselves yet!"
        )
    else:
        await send_message(update.effective_message, "There isnt one, use /setme to set one.")


async def set_about_me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user_id = message.from_user.id
    if user_id in [777000, 1087968824]:
        await message.reply_text("Error! Forbidden")
        return
    bot = context.bot
    if message.reply_to_message:
        repl_message = message.reply_to_message
        repl_user_id = repl_message.from_user.id
        if repl_user_id in [bot.id, 777000, 1087968824] and (user_id in DEV_USERS):
            user_id = repl_user_id
    text = message.text
    info_parts = text.split(None, 1)
    if len(info_parts) == 2:
        if len(info_parts[1]) < 1000:
            sql.set_user_me_info(user_id, info_parts[1])
            if user_id in [777000, 1087968824]:
                await send_message(message, "Authorized...Information updated!")
            elif user_id == bot.id:
                await send_message(message, "I have updated my info with the one you provided!")
            else:
                await send_message(message, "Information updated!")
        else:
            await send_message(
                message,
                "The info needs to be under 1000 characters! You have {}.".format(
                    len(info_parts[1])
                )
            )


@sudo_plus
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats_text = "<b>🧐 ᴄᴜʀʀᴇɴᴛ sᴛᴀᴛs:</b>\n" + "\n".join([mod.__stats__() for mod in STATS])
    result = re.sub(r"(\d+)", r"<code>\1</code>", stats_text)
    await send_message(update.effective_message, result, parse_mode=ParseMode.HTML)


async def about_bio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot, args = context.bot, context.args
    message = update.effective_message

    user_id = await extract_user(message, args)
    if user_id:
        user = await bot.get_chat(user_id)
    else:
        user = message.from_user

    info_text = sql.get_user_bio(user.id)

    if info_text:
        await send_message(
            update.effective_message,
            "*{}*:\n{}".format(user.first_name, escape_markdown(info_text)),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )
    elif message.reply_to_message:
        username = user.first_name
        await send_message(
            update.effective_message,
            f"{username} hasn't had a message set about themselves yet!\nSet one using /setbio"
        )
    else:
        await send_message(
            update.effective_message,
            "You haven't had a bio set about yourself yet!"
        )


async def set_about_bio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    sender_id = update.effective_user.id
    bot = context.bot

    if message.reply_to_message:
        repl_message = message.reply_to_message
        user_id = repl_message.from_user.id

        if user_id == update.effective_user.id:
            await send_message(
                message,
                "Ha, you can't set your own bio! You're at the mercy of others here..."
            )
            return

        if user_id in [777000, 1087968824] and sender_id not in DEV_USERS:
            await send_message(message, "You are not authorised")
            return

        if user_id == bot.id and sender_id not in DEV_USERS:
            await send_message(
                message,
                "Umm... yeah, I only trust Anon Association to set my bio."
            )
            return

        text = message.text
        bio_parts = text.split(None, 1)

        if len(bio_parts) == 2:
            if len(bio_parts[1]) < 1000:
                sql.set_user_bio(user_id, bio_parts[1])
                await send_message(
                    message,
                    "Updated {}'s bio!".format(repl_message.from_user.first_name)
                )
            else:
                await send_message(
                    message,
                    "Bio needs to be under 1000 characters! You tried to set {}.".format(
                        len(bio_parts[1])
                    )
                )
    else:
        await send_message(message, "Reply to someone to set their bio!")


def __user_info__(user_id):
    bio = html.escape(sql.get_user_bio(user_id) or "")
    me = html.escape(sql.get_user_me_info(user_id) or "")
    result = ""
    if me:
        result += f"<b>ᴀʙᴏᴜᴛ ᴜsᴇʀ:</b>\n{me}\n"
    if bio:
        result += f"<b>ᴏᴛʜᴇʀs sᴀʏ ᴛʜᴀᴛ:</b>\n{bio}\n"
    result = result.strip("\n")
    return result


__help__ = """
*ID:*
 ❍ /id*:* get the current group id. If used by replying to a message, gets that user's id.
 ❍ /gifid*:* reply to a gif to me to tell you its file ID.

*Self added information:* 
 ❍ /setme <text>*:* will set your info
 ❍ /me*:* will get your or another user's info.
*Examples:* 💡
 ➩ /setme I am a wolf.
 ➩ /me @username(defaults to yours if no user specified)

*Information others add on you:* 
 ❍ /bio*:* will get your or another user's bio. This cannot be set by yourself.
 ❍ /setbio <text>*:* while replying, will save another user's bio 
*Examples:* 💡
 ➩ /bio @username(defaults to yours if not specified).`
 ➩ /setbio This user is a wolf` (reply to the user)

*Overall Information about you:*
 ❍ /info*:* get information about a user. 
 ❍ /myinfo*:* Shows info about the user who sent this command.
"""

SET_BIO_HANDLER = DisableAbleCommandHandler("setbio", set_about_bio)
GET_BIO_HANDLER = DisableAbleCommandHandler("bio", about_bio)

STATS_HANDLER = CommandHandler("stats", stats_command)
ID_HANDLER = DisableAbleCommandHandler("id", get_id)
GIFID_HANDLER = DisableAbleCommandHandler("gifid", gifid)
INFO_HANDLER = DisableAbleCommandHandler(("info", "book"), info)

SET_ABOUT_HANDLER = DisableAbleCommandHandler("setme", set_about_me)
GET_ABOUT_HANDLER = DisableAbleCommandHandler("me", about_me)

application.add_handler(STATS_HANDLER)
application.add_handler(ID_HANDLER)
application.add_handler(GIFID_HANDLER)
application.add_handler(INFO_HANDLER)
application.add_handler(SET_BIO_HANDLER)
application.add_handler(GET_BIO_HANDLER)
application.add_handler(SET_ABOUT_HANDLER)
application.add_handler(GET_ABOUT_HANDLER)

__mod_name__ = "Iɴꜰᴏs"
__command_list__ = ["setbio", "bio", "setme", "me", "info"]
__handlers__ = [
    ID_HANDLER,
    GIFID_HANDLER,
    INFO_HANDLER,
    SET_BIO_HANDLER,
    GET_BIO_HANDLER,
    SET_ABOUT_HANDLER,
    GET_ABOUT_HANDLER,
    STATS_HANDLER,
]
