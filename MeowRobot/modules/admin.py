#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import html
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode, ChatMemberStatus, ChatType
from telegram.error import BadRequest
from telegram.ext import ContextTypes, CommandHandler
from telegram.helpers import mention_html

from MeowRobot import DRAGONS, application
from MeowRobot.modules.disable import DisableAbleCommandHandler
from MeowRobot.modules.helper_funcs.admin_rights import user_can_changeinfo
from MeowRobot.modules.helper_funcs.alternate import send_message
from MeowRobot.modules.helper_funcs.chat_status import (
    ADMIN_CACHE,
    bot_admin,
    can_pin,
    can_promote,
    connection_status,
    user_admin,
)
from MeowRobot.modules.helper_funcs.extraction import (
    extract_user,
    extract_user_and_text,
)
from MeowRobot.modules.log_channel import loggable
from MeowRobot.modules.helper_funcs.autodemote_helper import record_ban


@bot_admin
@user_admin
async def set_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if await user_can_changeinfo(chat, user, context.bot.id) is False:
        await send_message(msg,
            "» ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴩᴇʀᴍɪssɪᴏɴs ᴛᴏ ᴄʜᴀɴɢᴇ ɢʀᴏᴜᴩ ɪɴғᴏ ʙᴀʙʏ !"
        )
        return

    if msg.reply_to_message:
        if not msg.reply_to_message.sticker:
            await send_message(msg,
                "» ʀᴇᴩʟʏ ᴛᴏ ᴀ sᴛɪᴄᴋᴇʀ ᴛᴏ sᴇᴛ ɪᴛ ᴀs ɢʀᴏᴜᴩ sᴛɪᴄᴋᴇʀ ᴩᴀᴄᴋ !"
            )
            return
        stkr = msg.reply_to_message.sticker.set_name
        try:
            await context.bot.set_chat_sticker_set(chat.id, stkr)
            await send_message(msg, f"» sᴜᴄᴄᴇssғᴜʟʟʏ sᴇᴛ ɢʀᴏᴜᴩ sᴛɪᴄᴋᴇʀs ɪɴ {chat.title}!")
        except BadRequest as excp:
            if excp.message == "Participants_too_few":
                await send_message(msg,
                    "» ʏᴏᴜʀ ɢʀᴏᴜᴩ ɴᴇᴇᴅs ᴍɪɴɪᴍᴜᴍ 100 ᴍᴇᴍʙᴇʀs ғᴏʀ sᴇᴛᴛɪɴɢ ᴀ sᴛɪᴄᴋᴇʀ ᴩᴀᴄᴋ ᴀs ɢʀᴏᴜᴩ sᴛɪᴄᴋᴇʀ ᴩᴀᴄᴋ !"
                )
                return
            await send_message(msg, f"ᴇʀʀᴏʀ ! {excp.message}.")
    else:
        await send_message(msg, "» ʀᴇᴩʟʏ ᴛᴏ ᴀ sᴛɪᴄᴋᴇʀ ᴛᴏ sᴇᴛ ɪᴛ ᴀs ɢʀᴏᴜᴩ sᴛɪᴄᴋᴇʀ ᴩᴀᴄᴋ !")


@bot_admin
@user_admin
async def setchatpic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user

    if await user_can_changeinfo(chat, user, context.bot.id) is False:
        await send_message(msg, "» ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴩᴇʀᴍɪssɪᴏɴs ᴛᴏ ᴄʜᴀɴɢᴇ ɢʀᴏᴜᴩ ɪɴғᴏ ʙᴀʙʏ !")
        return

    if msg.reply_to_message:
        if msg.reply_to_message.photo:
            pic_id = msg.reply_to_message.photo[-1].file_id
        elif msg.reply_to_message.document:
            pic_id = msg.reply_to_message.document.file_id
        else:
            await send_message(msg, "» ʏᴏᴜ ᴄᴀɴ ᴏɴʟʏ sᴇᴛ ᴩʜᴏᴛᴏs ᴀs ɢʀᴏᴜᴩ ᴩғᴩ !")
            return
        dlmsg = await send_message(msg, "» ᴄʜᴀɴɢɪɴɢ ɢʀᴏᴜᴩ's ᴩʀᴏғɪʟᴇ ᴩɪᴄ...")
        tpic = await context.bot.get_file(pic_id)
        await tpic.download_to_drive("gpic.png")
        try:
            with open("gpic.png", "rb") as chatp:
                await context.bot.set_chat_photo(int(chat.id), photo=chatp)
                await send_message(msg, "» sᴜᴄᴄᴇssғᴜʟʟʏ sᴇᴛ ɢʀᴏᴜᴩ ᴩʀᴏғɪʟᴇ ᴩɪᴄ !")
        except BadRequest as excp:
            await send_message(msg, f"ᴇʀʀᴏʀ ! {excp.message}")
        finally:
            await dlmsg.delete()
            if os.path.isfile("gpic.png"):
                os.remove("gpic.png")
    else:
        await send_message(msg, "» ʀᴇᴩʟʏ ᴛᴏ ᴀ ᴩʜᴏᴛᴏ ᴏʀ ғɪʟᴇ ᴛᴏ sᴇᴛ ɪᴛ ᴀs ɢʀᴏᴜᴩ ᴩʀᴏғɪʟᴇ ᴩɪᴄ !")


@bot_admin
@user_admin
async def rmchatpic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user

    if await user_can_changeinfo(chat, user, context.bot.id) is False:
        await send_message(msg, "» ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴩᴇʀᴍɪssɪᴏɴs ᴛᴏ ᴄʜᴀɴɢᴇ ɢʀᴏᴜᴩ ɪɴғᴏ ʙᴀʙʏ !")
        return
    try:
        await context.bot.delete_chat_photo(int(chat.id))
        await send_message(msg, "» sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ ɢʀᴏᴜᴩ's ᴅᴇғᴀᴜʟᴛ ᴩʀᴏғɪʟᴇ ᴩɪᴄ !")
    except BadRequest as excp:
        await send_message(msg, f"ᴇʀʀᴏʀ ! {excp.message}.")
        return


@bot_admin
@user_admin
async def set_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if await user_can_changeinfo(chat, user, context.bot.id) is False:
        await send_message(msg,
            "» ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴩᴇʀᴍɪssɪᴏɴs ᴛᴏ ᴄʜᴀɴɢᴇ ɢʀᴏᴜᴩ ɪɴғᴏ ʙᴀʙʏ !"
        )
        return

    tesc = msg.text.split(None, 1)
    if len(tesc) >= 2:
        desc = tesc[1]
    else:
        await send_message(msg, "» ᴡᴛғ, ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ sᴇᴛ ᴀɴ ᴇᴍᴩᴛʏ ᴅᴇsᴄʀɪᴩᴛɪᴏɴ !")
        return
    try:
        if len(desc) > 255:
            await send_message(msg,
                "» ᴅᴇsᴄʀɪᴩᴛɪᴏɴ ᴍᴜsᴛ ʙᴇ ʟᴇss ᴛʜᴀɴ 255 ᴡᴏʀᴅs ᴏʀ ᴄʜᴀʀᴀᴄᴛᴇʀs !"
            )
            return
        await context.bot.set_chat_description(chat.id, desc)
        await send_message(msg, f"» sᴜᴄᴄᴇssғᴜʟʟʏ ᴜᴩᴅᴀᴛᴇᴅ ᴄʜᴀᴛ ᴅᴇsᴄʀɪᴩᴛɪᴏɴ ɪɴ {chat.title}!")
    except BadRequest as excp:
        await send_message(msg, f"ᴇʀʀᴏʀ ! {excp.message}.")


@bot_admin
@user_admin
async def setchat_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user
    args = context.args

    if await user_can_changeinfo(chat, user, context.bot.id) is False:
        await send_message(msg, "» ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴩᴇʀᴍɪssɪᴏɴs ᴛᴏ ᴄʜᴀɴɢᴇ ɢʀᴏᴜᴩ ɪɴғᴏ ʙᴀʙʏ !")
        return

    title = " ".join(args)
    if not title:
        await send_message(msg, "» ᴇɴᴛᴇʀ sᴏᴍᴇ ᴛᴇxᴛ ᴛᴏ sᴇᴛ ɪᴛ ᴀs ɴᴇᴡ ᴄʜᴀᴛ ᴛɪᴛʟᴇ !")
        return

    try:
        await context.bot.set_chat_title(int(chat.id), str(title))
        await send_message(msg,
            f"» sᴜᴄᴄᴇssғᴜʟʟʏ sᴇᴛ <b>{title}</b> ᴀs ɴᴇᴡ ᴄʜᴀᴛ ᴛɪᴛʟᴇ !",
            parse_mode=ParseMode.HTML,
        )
    except BadRequest as excp:
        await send_message(msg, f"ᴇʀʀᴏʀ ! {excp.message}.")
        return


@connection_status
@bot_admin
@can_promote
@user_admin
@loggable
async def promote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    bot = context.bot
    args = context.args

    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    promoter = await chat.get_member(user.id)

    if (
        not (getattr(promoter, 'can_promote_members', False) or promoter.status == ChatMemberStatus.OWNER)
        and user.id not in DRAGONS
    ):
        await send_message(message, "» ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴩᴇʀᴍɪssɪᴏɴs ᴛᴏ ᴀᴅᴅ ɴᴇᴡ ᴀᴅᴍɪɴs ʙᴀʙʏ !")
        return ""

    user_id, title = await extract_user_and_text(message, args)

    if not user_id:
        await send_message(message,
            "» ɪ ᴅᴏɴ'ᴛ ᴋɴᴏᴡ ᴡʜᴏ's ᴛʜᴀᴛ ᴜsᴇʀ, ɴᴇᴠᴇʀ sᴇᴇɴ ʜɪᴍ ɪɴ ᴀɴʏ ᴏғ ᴛʜᴇ ᴄʜᴀᴛs ᴡʜᴇʀᴇ ɪ ᴀᴍ ᴩʀᴇsᴇɴᴛ !",
        )
        return ""

    try:
        user_member = await chat.get_member(user_id)
    except:
        return ""

    if user_member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
        await send_message(message, "» ᴀᴄᴄᴏʀᴅɪɴɢ ᴛᴏ ᴍᴇ ᴛʜᴀᴛ ᴜsᴇʀ ɪs ᴀʟʀᴇᴀᴅʏ ᴀɴ ᴀᴅᴍɪɴ ʜᴇʀᴇ !")
        return ""

    if user_id == bot.id:
        await send_message(message,
            "» ɪ ᴄᴀɴ'ᴛ ᴩʀᴏᴍᴏᴛᴇ ᴍʏsᴇʟғ, ᴍʏ ᴏᴡɴᴇʀ ᴅɪᴅɴ'ᴛ ᴛᴏʟᴅ ᴍᴇ ᴛᴏ ᴅᴏ sᴏ."
        )
        return ""

    # set same perms as bot - bot can't assign higher perms than itself!
    bot_member = await chat.get_member(bot.id)

    try:
        await bot.promote_chat_member(
            chat.id,
            user_id,
            can_change_info=getattr(bot_member, "can_change_info", False),
            can_post_messages=getattr(bot_member, "can_post_messages", False),
            can_edit_messages=getattr(bot_member, "can_edit_messages", False),
            can_delete_messages=getattr(bot_member, "can_delete_messages", False),
            can_invite_users=getattr(bot_member, "can_invite_users", False),
            can_pin_messages=getattr(bot_member, "can_pin_messages", False),
            can_manage_video_chats=getattr(bot_member, "can_manage_video_chats", False),
            can_manage_chat=getattr(bot_member, "can_manage_chat", False),
            can_manage_topics=getattr(bot_member, "can_manage_topics", False),
            can_post_stories=getattr(bot_member, "can_post_stories", False),
            can_edit_stories=getattr(bot_member, "can_edit_stories", False),
            can_delete_stories=getattr(bot_member, "can_delete_stories", False),
        )
    except BadRequest as err:
        if err.message in ("User_not_mutual_contact", "User not mutual contact", "User not found"):
            await send_message(message, "» ᴀs ɪ ᴄᴀɴ sᴇᴇ ᴛʜᴀᴛ ᴜsᴇʀ ɪs ɴᴏᴛ ᴩʀᴇsᴇɴᴛ ʜᴇʀᴇ.")
        else:
            await send_message(message,
                "» sᴏᴍᴇᴛʜɪɴɢ ᴡᴇɴᴛ ᴡʀᴏɴɢ, ᴍᴀʏʙᴇ sᴏᴍᴇᴏɴᴇ ᴩʀᴏᴍᴏᴛᴇᴅ ᴛʜᴀᴛ ᴜsᴇʀ ʙᴇғᴏʀᴇ ᴍᴇ."
            )
        return ""

    if title:
        title = title.strip()
        try:
            await bot.set_chat_administrator_custom_title(chat.id, user_id, title[:16])
        except Exception:
            pass

    title_text = f"\nᴛɪᴛʟᴇ : <code>{html.escape(title[:16])}</code>" if title else ""
    await bot.send_message(
        chat.id,
        f"<b>» ᴩʀᴏᴍᴏᴛɪɴɢ ᴀ ᴜsᴇʀ ɪɴ</b> {chat.title}\n\nᴩʀᴏᴍᴏᴛᴇᴅ : {mention_html(user_member.user.id, user_member.user.first_name)}\nᴩʀᴏᴍᴏᴛᴇʀ : {mention_html(user.id, user.first_name)}{title_text}",
        parse_mode=ParseMode.HTML,
    )

    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#ᴩʀᴏᴍᴏᴛᴇᴅ\n"
        f"<b>ᴩʀᴏᴍᴏᴛᴇʀ :</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>ᴜsᴇʀ :</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
    )
    if title:
        log_message += f"\n<b>ᴛɪᴛʟᴇ :</b> {html.escape(title[:16])}"

    return log_message


@connection_status
@bot_admin
@can_promote
@user_admin
@loggable
async def lowpromote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    bot = context.bot
    args = context.args

    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    promoter = await chat.get_member(user.id)

    if (
        not (getattr(promoter, 'can_promote_members', False) or promoter.status == ChatMemberStatus.OWNER)
        and user.id not in DRAGONS
    ):
        await send_message(message, "» ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴩᴇʀᴍɪssɪᴏɴs ᴛᴏ ᴀᴅᴅ ɴᴇᴡ ᴀᴅᴍɪɴs ʙᴀʙʏ !")
        return ""

    user_id, title = await extract_user_and_text(message, args)

    if not user_id:
        await send_message(message,
            "» ɪ ᴅᴏɴ'ᴛ ᴋɴᴏᴡ ᴡʜᴏ's ᴛʜᴀᴛ ᴜsᴇʀ, ɴᴇᴠᴇʀ sᴇᴇɴ ʜɪᴍ ɪɴ ᴀɴʏ ᴏғ ᴛʜᴇ ᴄʜᴀᴛs ᴡʜᴇʀᴇ ɪ ᴀᴍ ᴩʀᴇsᴇɴᴛ !",
        )
        return ""

    try:
        user_member = await chat.get_member(user_id)
    except:
        return ""

    if user_member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
        await send_message(message, "» ᴀᴄᴄᴏʀᴅɪɴɢ ᴛᴏ ᴍᴇ ᴛʜᴀᴛ ᴜsᴇʀ ɪs ᴀʟʀᴇᴀᴅʏ ᴀɴ ᴀᴅᴍɪɴ ʜᴇʀᴇ !")
        return ""

    if user_id == bot.id:
        await send_message(message,
            "» ɪ ᴄᴀɴ'ᴛ ᴩʀᴏᴍᴏᴛᴇ ᴍʏsᴇʟғ, ᴍʏ ᴏᴡɴᴇʀ ᴅɪᴅɴ'ᴛ ᴛᴏʟᴅ ᴍᴇ ᴛᴏ ᴅᴏ sᴏ."
        )
        return ""

    # set same perms as bot - bot can't assign higher perms than itself!
    bot_member = await chat.get_member(bot.id)

    try:
        await bot.promote_chat_member(
            chat.id,
            user_id,
            can_delete_messages=getattr(bot_member, "can_delete_messages", False),
            can_invite_users=getattr(bot_member, "can_invite_users", False),
            can_pin_messages=getattr(bot_member, "can_pin_messages", False),
        )
    except BadRequest as err:
        if err.message in ("User_not_mutual_contact", "User not mutual contact", "User not found"):
            await send_message(message, "» ᴀs ɪ ᴄᴀɴ sᴇᴇ ᴛʜᴀᴛ ᴜsᴇʀ ɪs ɴᴏᴛ ᴩʀᴇsᴇɴᴛ ʜᴇʀᴇ.")
        else:
            await send_message(message,
                "» sᴏᴍᴇᴛʜɪɴɢ ᴡᴇɴᴛ ᴡʀᴏɴɢ, ᴍᴀʏʙᴇ sᴏᴍᴇᴏɴᴇ ᴩʀᴏᴍᴏᴛᴇᴅ ᴛʜᴀᴛ ᴜsᴇʀ ʙᴇғᴏʀᴇ ᴍᴇ."
            )
        return ""

    if title:
        title = title.strip()
        try:
            await bot.set_chat_administrator_custom_title(chat.id, user_id, title[:16])
        except Exception:
            pass

    title_text = f"\nᴛɪᴛʟᴇ : <code>{html.escape(title[:16])}</code>" if title else ""
    await bot.send_message(
        chat.id,
        f"<b>» ʟᴏᴡ ᴩʀᴏᴍᴏᴛɪɴɢ ᴀ ᴜsᴇʀ ɪɴ </b>{chat.title}\n\n<b>ᴩʀᴏᴍᴏᴛᴇᴅ :</b> {mention_html(user_member.user.id, user_member.user.first_name)}\n<b>ᴩʀᴏᴍᴏᴛᴇʀ :</b> {mention_html(user.id, user.first_name)}{title_text}",
        parse_mode=ParseMode.HTML,
    )

    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#ʟᴏᴡᴩʀᴏᴍᴏᴛᴇᴅ\n"
        f"<b>ᴩʀᴏᴍᴏᴛᴇʀ :</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>ᴜsᴇʀ :</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
    )
    if title:
        log_message += f"\n<b>ᴛɪᴛʟᴇ :</b> {html.escape(title[:16])}"

    return log_message


@connection_status
@bot_admin
@can_promote
@user_admin
@loggable
async def fullpromote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    bot = context.bot
    args = context.args

    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    promoter = await chat.get_member(user.id)

    if (
        not (getattr(promoter, 'can_promote_members', False) or promoter.status == ChatMemberStatus.OWNER)
        and user.id not in DRAGONS
    ):
        await send_message(message, "» ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴩᴇʀᴍɪssɪᴏɴs ᴛᴏ ᴀᴅᴅ ɴᴇᴡ ᴀᴅᴍɪɴs ʙᴀʙʏ !")
        return ""

    user_id, title = await extract_user_and_text(message, args)

    if not user_id:
        await send_message(message,
            "» ɪ ᴅᴏɴ'ᴛ ᴋɴᴏᴡ ᴡʜᴏ's ᴛʜᴀᴛ ᴜsᴇʀ, ɴᴇᴠᴇʀ sᴇᴇɴ ʜɪᴍ ɪɴ ᴀɴʏ ᴏғ ᴛʜᴇ ᴄʜᴀᴛs ᴡʜᴇʀᴇ ɪ ᴀᴍ ᴩʀᴇsᴇɴᴛ !",
        )
        return ""

    try:
        user_member = await chat.get_member(user_id)
    except:
        return ""

    if user_member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
        await send_message(message, "» ᴀᴄᴄᴏʀᴅɪɴɢ ᴛᴏ ᴍᴇ ᴛʜᴀᴛ ᴜsᴇʀ ɪs ᴀʟʀᴇᴀᴅʏ ᴀɴ ᴀᴅᴍɪɴ ʜᴇʀᴇ !")
        return ""

    if user_id == bot.id:
        await send_message(message,
            "» ɪ ᴄᴀɴ'ᴛ ᴩʀᴏᴍᴏᴛᴇ ᴍʏsᴇʟғ, ᴍʏ ᴏᴡɴᴇʀ ᴅɪᴅɴ'ᴛ ᴛᴏʟᴅ ᴍᴇ ᴛᴏ ᴅᴏ sᴏ."
        )
        return ""

    # set same perms as bot - bot can't assign higher perms than itself!
    bot_member = await chat.get_member(bot.id)

    try:
        await bot.promote_chat_member(
            chat.id,
            user_id,
            can_change_info=getattr(bot_member, "can_change_info", False),
            can_post_messages=getattr(bot_member, "can_post_messages", False),
            can_edit_messages=getattr(bot_member, "can_edit_messages", False),
            can_delete_messages=getattr(bot_member, "can_delete_messages", False),
            can_invite_users=getattr(bot_member, "can_invite_users", False),
            can_promote_members=getattr(bot_member, "can_promote_members", False),
            can_restrict_members=getattr(bot_member, "can_restrict_members", False),
            can_pin_messages=getattr(bot_member, "can_pin_messages", False),
            can_manage_video_chats=getattr(bot_member, "can_manage_video_chats", False),
            can_manage_chat=getattr(bot_member, "can_manage_chat", False),
            can_manage_topics=getattr(bot_member, "can_manage_topics", False),
            can_post_stories=getattr(bot_member, "can_post_stories", False),
            can_edit_stories=getattr(bot_member, "can_edit_stories", False),
            can_delete_stories=getattr(bot_member, "can_delete_stories", False),
        )
    except BadRequest as err:
        if err.message in ("User_not_mutual_contact", "User not mutual contact", "User not found"):
            await send_message(message, "» ᴀs ɪ ᴄᴀɴ sᴇᴇ ᴛʜᴀᴛ ᴜsᴇʀ ɪs ɴᴏᴛ ᴩʀᴇsᴇɴᴛ ʜᴇʀᴇ.")
        else:
            await send_message(message,
                "» sᴏᴍᴇᴛʜɪɴɢ ᴡᴇɴᴛ ᴡʀᴏɴɢ, ᴍᴀʏʙᴇ sᴏᴍᴇᴏɴᴇ ᴩʀᴏᴍᴏᴛᴇᴅ ᴛʜᴀᴛ ᴜsᴇʀ ʙᴇғᴏʀᴇ ᴍᴇ."
            )
        return ""

    if title:
        title = title.strip()
        try:
            await bot.set_chat_administrator_custom_title(chat.id, user_id, title[:16])
        except Exception:
            pass

    title_text = f"\n<b>ᴛɪᴛʟᴇ :</b> <code>{html.escape(title[:16])}</code>" if title else ""
    await bot.send_message(
        chat.id,
        f"» ғᴜʟʟᴩʀᴏᴍᴏᴛɪɴɢ ᴀ ᴜsᴇʀ ɪɴ <b>{chat.title}</b>\n\n<b>ᴜsᴇʀ : {mention_html(user_member.user.id, user_member.user.first_name)}</b>\n<b>ᴩʀᴏᴍᴏᴛᴇʀ : {mention_html(user.id, user.first_name)}</b>{title_text}",
        parse_mode=ParseMode.HTML,
    )

    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#ғᴜʟʟᴩʀᴏᴍᴏᴛᴇᴅ\n"
        f"<b>ᴩʀᴏᴍᴏᴛᴇʀ :</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>ᴜsᴇʀ :</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
    )
    if title:
        log_message += f"\n<b>ᴛɪᴛʟᴇ :</b> {html.escape(title[:16])}"

    return log_message


@connection_status
@bot_admin
@can_promote
@user_admin
@loggable
async def demote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    bot = context.bot
    args = context.args

    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user

    user_id = await extract_user(message, args)
    if not user_id:
        await send_message(message,
            "» ɪ ᴅᴏɴ'ᴛ ᴋɴᴏᴡ ᴡʜᴏ's ᴛʜᴀᴛ ᴜsᴇʀ, ɴᴇᴠᴇʀ sᴇᴇɴ ʜɪᴍ ɪɴ ᴀɴʏ ᴏғ ᴛʜᴇ ᴄʜᴀᴛs ᴡʜᴇʀᴇ ɪ ᴀᴍ ᴩʀᴇsᴇɴᴛ !",
        )
        return ""

    try:
        user_member = await chat.get_member(user_id)
    except:
        return ""

    if user_member.status == ChatMemberStatus.OWNER:
        await send_message(message,
            "» ᴛʜᴀᴛ ᴜsᴇʀ ɪs ᴏᴡɴᴇʀ ᴏғ ᴛʜᴇ ᴄʜᴀᴛ ᴀɴᴅ ɪ ᴅᴏɴ'ᴛ ᴡᴀɴᴛ ᴛᴏ ᴩᴜᴛ ᴍʏsᴇʟғ ɪɴ ᴅᴀɴɢᴇʀ."
        )
        return ""

    # 🤖 BOT DEMOTE → REMOVE (BAN-LIKE BEHAVIOUR)
    if user_member.user.is_bot:
        try:
            await chat.ban_member(user_member.user.id)
            await record_ban(chat.id, user.id, context)

            await send_message(message,
                f"» ⚠️ <b>ʙᴏᴛ ᴅᴇᴍᴏᴛᴇᴅ & ʀᴇᴍᴏᴠᴇᴅ</b>\n\n"
                f"• <b>ʙᴏᴛ :</b> {mention_html(user_member.user.id, user_member.user.first_name)}\n"
                f"• <b>ᴀᴄᴛɪᴏɴ :</b> ʀᴇᴍᴏᴠᴇᴅ ғʀᴏᴍ ɢʀᴏᴜᴘ\n"
                f"• <b>ʙʏ :</b> {mention_html(user.id, user.first_name)}",
                parse_mode=ParseMode.HTML,
            )

        except BadRequest:
            await send_message(message,
                "» ɪ ᴄᴀɴ'ᴛ ʀᴇᴍᴏᴠᴇ ᴛʜɪs ʙᴏᴛ.\n"
                "» ᴍᴀᴋᴇ sᴜʀᴇ ɪ ʜᴀᴠᴇ ʀᴇᴍᴏᴠᴇ ᴘᴇʀᴍɪssɪᴏɴ."
            )

        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#ʙᴏᴛ_ʀᴇᴍᴏᴠᴇᴅ\n"
            f"<b>ʙᴏᴛ :</b> {mention_html(user_member.user.id, user_member.user.first_name)}\n"
            f"<b>ʙʏ :</b> {mention_html(user.id, user.first_name)}"
        )
        return log_message

    if not user_member.status == ChatMemberStatus.ADMINISTRATOR:
        await send_message(message, "» ᴀᴄᴄᴏʀᴅɪɴɢ ᴛᴏ ᴍᴇ ᴛʜᴀᴛ ᴜsᴇʀ ɪs ɴᴏᴛ ᴀɴ ᴀᴅᴍɪɴ ʜᴇʀᴇ !")
        return ""

    if getattr(user_member, "can_be_edited", True) is False:
        await send_message(message, "» ɪ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ʀɪɢʜᴛs ᴛᴏ ᴅᴇᴍᴏᴛᴇ ᴛʜᴀᴛ ᴜsᴇʀ, ᴍᴀʏʙᴇ ʜᴇ ᴡᴀs ᴩʀᴏᴍᴏᴛᴇᴅ ʙʏ ᴛʜᴇ ᴄʜᴀᴛ ᴏᴡɴᴇʀ.")
        return ""

    if user_id == bot.id:
        await send_message(message, "» ɪ ᴄᴀɴ'ᴛ ᴅᴇᴍᴏᴛᴇ ᴍʏsᴇʟғ, ʙᴜᴛ ɪғ ʏᴏᴜ ᴡᴀɴᴛ ɪ ᴄᴀɴ ʟᴇᴀᴠᴇ.")
        return ""

    try:
        if chat.type == ChatType.CHANNEL:
            await bot.promote_chat_member(
                chat.id,
                user_id,
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
                can_post_stories=False,
                can_edit_stories=False,
                can_delete_stories=False,
            )
        else:
            await bot.promote_chat_member(
                chat.id,
                user_id,
                can_change_info=False,
                can_delete_messages=False,
                can_invite_users=False,
                can_restrict_members=False,
                can_pin_messages=False,
                can_promote_members=False,
                can_manage_video_chats=False,
                can_manage_chat=False,
                can_manage_topics=False,
                can_post_stories=False,
                can_edit_stories=False,
                can_delete_stories=False,
            )

        await bot.send_message(
            chat.id,
            f"» sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇᴍᴏᴛᴇᴅ ᴀ ᴀᴅᴍɪɴ ɪɴ <b>{chat.title}</b>\n\nᴅᴇᴍᴏᴛᴇʀ : {mention_html(user.id, user.first_name)}\nᴅᴇᴍᴏᴛᴇᴅ : <b>{mention_html(user_member.user.id, user_member.user.first_name)}</b>",
            parse_mode=ParseMode.HTML,
        )

        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#ᴅᴇᴍᴏᴛᴇᴅ\n"
            f"<b>ᴅᴇᴍᴏᴛᴇʀ :</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>ᴅᴇᴍᴏᴛᴇᴅ :</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
        )

        return log_message
    except BadRequest as err:
        await send_message(message,
            f"» ғᴀɪʟᴇᴅ ᴛᴏ ᴅᴇᴍᴏᴛᴇ !\n<b>ᴇʀʀᴏʀ:</b> <code>{err.message}</code>",
            parse_mode=ParseMode.HTML
        )
        return ""


@user_admin
async def refresh_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        ADMIN_CACHE.pop(update.effective_chat.id)
    except KeyError:
        pass

    await send_message(update.effective_message, "» sᴜᴄᴄᴇssғᴜʟʟʏ ʀᴇғʀᴇsʜᴇᴅ ᴀᴅᴍɪɴ ᴄᴀᴄʜᴇ !")


@connection_status
@bot_admin
@can_promote
@user_admin
async def set_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    args = context.args

    chat = update.effective_chat
    message = update.effective_message

    user_id, title = await extract_user_and_text(message, args)

    if not user_id:
        await send_message(
            message,
            "» ɪ ᴅᴏɴ'ᴛ ᴋɴᴏᴡ ᴡʜᴏ's ᴛʜᴀᴛ ᴜsᴇʀ, ɴᴇᴠᴇʀ sᴇᴇɴ ʜɪᴍ ɪɴ ᴀɴʏ ᴏғ ᴛʜᴇ ᴄʜᴀᴛs ᴡʜᴇʀᴇ ɪ ᴀᴍ ᴩʀᴇsᴇɴᴛ !",
        )
        return

    try:
        user_member = await chat.get_member(user_id)
    except:
        await send_message(message, "» ᴛʜᴀᴛ ᴜsᴇʀ ᴅᴏᴇsɴ'ᴛ sᴇᴇᴍ ᴛᴏ ʙᴇ ɪɴ ᴛʜɪs ᴄʜᴀᴛ.")
        return

    if user_member.status == ChatMemberStatus.OWNER:
        await send_message(
            message,
            "» ᴛʜᴀᴛ ᴜsᴇʀ ɪs ᴏᴡɴᴇʀ ᴏғ ᴛʜᴇ ᴄʜᴀᴛ ᴀɴᴅ ɪ ᴅᴏɴ'ᴛ ᴡᴀɴᴛ ᴛᴏ ᴩᴜᴛ ᴍʏsᴇʟғ ɪɴ ᴅᴀɴɢᴇʀ.",
        )
        return

    if user_member.status != ChatMemberStatus.ADMINISTRATOR:
        await send_message(
            message,
            "» ɪ ᴄᴀɴ ᴏɴʟʏ sᴇᴛ ᴛɪᴛʟᴇ ғᴏʀ ᴀᴅᴍɪɴs !",
        )
        return

    if user_id == bot.id:
        await send_message(
            message,
            "» ɪ ᴄᴀɴ'ᴛ sᴇᴛ ᴛɪᴛʟᴇ ғᴏʀ ᴍʏsᴇʟғ, ᴍʏ ᴏᴡɴᴇʀ ᴅɪᴅɴ'ᴛ ᴛᴏʟᴅ ᴍᴇ ᴛᴏ ᴅᴏ sᴏ.",
        )
        return

    if not title:
        await send_message(
            message,
            "» ᴘʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴛɪᴛʟᴇ/ᴛᴀɢ ғᴏʀ ᴛʜᴇ ᴀᴅᴍɪɴ !\n<b>ᴇxᴀᴍᴘʟᴇ :</b> <code>/title @username Admin</code> ᴏʀ ʀᴇᴘʟʏ ᴡɪᴛʜ <code>/title Admin</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    title = title.strip()
    if len(title) > 16:
        await send_message(
            message,
            "» ᴛʜᴇ ᴛɪᴛʟᴇ ʟᴇɴɢᴛʜ ɪs ʟᴏɴɢᴇʀ ᴛʜᴀɴ 16 ᴄʜᴀʀᴀᴄᴛᴇʀs sᴏ ᴛʀᴜɴᴄᴀᴛɪɴɢ ɪᴛ ᴛᴏ 16 ᴄʜᴀʀᴀᴄᴛᴇʀs.",
        )

    try:
        await bot.set_chat_administrator_custom_title(chat.id, user_id, title[:16])
    except BadRequest as err:
        if "not promoted by" in err.message.lower() or "right" in err.message.lower():
            await send_message(
                message,
                "» ɪ ᴄᴀɴ ᴏɴʟʏ sᴇᴛ ᴛɪᴛʟᴇ ғᴏʀ ᴀᴅᴍɪɴs ᴩʀᴏᴍᴏᴛᴇᴅ ʙʏ ᴍᴇ !",
            )
        else:
            await send_message(
                message,
                f"» ғᴀɪʟᴇᴅ ᴛᴏ sᴇᴛ ᴛɪᴛʟᴇ : <code>{err.message}</code>",
                parse_mode=ParseMode.HTML,
            )
        return

    await bot.send_message(
        chat.id,
        f"» sᴜᴄᴄᴇssғᴜʟʟʏ sᴇᴛ ᴛɪᴛʟᴇ ғᴏʀ <code>{user_member.user.first_name or user_id}</code> "
        f"ᴛᴏ <code>{html.escape(title[:16])}</code>!",
        parse_mode=ParseMode.HTML,
    )


@bot_admin
@can_pin
@user_admin
@loggable
async def pin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    bot, args = context.bot, context.args
    user = update.effective_user
    chat = update.effective_chat
    msg = update.effective_message
    msg_id = msg.reply_to_message.message_id if msg.reply_to_message else msg.message_id

    if msg.chat.username:
        # If chat has a username, use this format
        link_chat_id = msg.chat.username
        message_link = f"https://t.me/{link_chat_id}/{msg_id}"
    elif (str(msg.chat.id)).startswith("-100"):
        # If chat does not have a username, use this
        link_chat_id = (str(msg.chat.id)).replace("-100", "")
        message_link = f"https://t.me/c/{link_chat_id}/{msg_id}"
    else:
        message_link = ""

    is_group = chat.type not in (ChatType.PRIVATE, ChatType.CHANNEL)
    prev_message = update.effective_message.reply_to_message

    if prev_message is None:
        await send_message(msg, "» ʀᴇᴩʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ᴩɪɴ ɪᴛ !")
        return ""

    is_silent = True
    if len(args) >= 1:
        is_silent = (
            args[0].lower() != "notify"
            or args[0].lower() == "loud"
            or args[0].lower() == "violent"
        )

    if prev_message and is_group:
        try:
            await bot.pin_chat_message(
                chat.id, prev_message.message_id, disable_notification=is_silent
            )
            await send_message(msg,
                f"» sᴜᴄᴄᴇssғᴜʟʟʏ ᴩɪɴɴᴇᴅ ᴛʜᴀᴛ ᴍᴇssᴀɢᴇ.\nᴄʟɪᴄᴋ ᴏɴ ᴛʜᴇ ʙᴜᴛᴛᴏɴ ʙᴇʟᴏᴡ ᴛᴏ sᴇᴇ ᴛʜᴇ ᴍᴇssᴀɢᴇ.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("ᴍᴇssᴀɢᴇ", url=f"{message_link}")]]
                ),
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
        except BadRequest as excp:
            if excp.message != "Chat_not_modified":
                raise

        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"ᴩɪɴɴᴇᴅ-ᴀ-ᴍᴇssᴀɢᴇ\n"
            f"<b>ᴩɪɴɴᴇᴅ ʙʏ :</b> {mention_html(user.id, html.escape(user.first_name))}"
        )

        return log_message
    return ""


@bot_admin
@can_pin
@user_admin
@loggable
async def unpin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message
    msg_id = msg.reply_to_message.message_id if msg.reply_to_message else msg.message_id
    unpinner = await chat.get_member(user.id)

    if (
        not (getattr(unpinner, 'can_pin_messages', False) or unpinner.status == ChatMemberStatus.OWNER)
        and user.id not in DRAGONS
    ):
        await send_message(msg,
            "» ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴩᴇʀᴍɪssɪᴏɴs ᴛᴏ ᴩɪɴ/ᴜɴᴩɪɴ ᴍᴇssᴀɢᴇs ɪɴ ᴛʜɪs ᴄʜᴀᴛ !"
        )
        return ""

    if msg.chat.username:
        # If chat has a username, use this format
        link_chat_id = msg.chat.username
        message_link = f"https://t.me/{link_chat_id}/{msg_id}"
    elif (str(msg.chat.id)).startswith("-100"):
        # If chat does not have a username, use this
        link_chat_id = (str(msg.chat.id)).replace("-100", "")
        message_link = f"https://t.me/c/{link_chat_id}/{msg_id}"
    else:
        message_link = ""

    is_group = chat.type not in (ChatType.PRIVATE, ChatType.CHANNEL)
    prev_message = update.effective_message.reply_to_message

    if prev_message and is_group:
        try:
            await context.bot.unpin_chat_message(chat.id, prev_message.message_id)
            await send_message(msg,
                f"» sᴜᴄᴄᴇssғᴜʟʟʏ ᴜɴᴩɪɴɴᴇᴅ <a href='{message_link}'> ᴛʜɪs ᴩɪɴɴᴇᴅ ᴍᴇssᴀɢᴇ</a>.",
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
        except BadRequest as excp:
            if excp.message != "Chat_not_modified":
                raise

    if not prev_message and is_group:
        try:
            await context.bot.unpin_chat_message(chat.id)
            await send_message(msg, "» sᴜᴄᴄᴇssғᴜʟʟʏ ᴜɴᴩɪɴɴᴇᴅ ᴛʜᴇ ʟᴀsᴛ ᴩɪɴɴᴇᴅ ᴍᴇssᴀɢᴇ.")
        except BadRequest as excp:
            if excp.message == "Message to unpin not found":
                await send_message(msg,
                    "» ɪ ᴄᴀɴ'ᴛ ᴜɴᴩɪɴ ᴛʜᴀᴛ ᴍᴇssᴀɢᴇ, ᴍᴀʏʙᴇ ᴛʜᴀᴛ ᴍᴇssᴀɢᴇ ɪs ᴛᴏᴏ ᴏʟᴅ ᴏʀ ᴍᴀʏʙᴇ sᴏᴍᴇᴏɴᴇ ᴀʟʀᴇᴀᴅʏ ᴜɴᴩɪɴɴᴇᴅ ɪᴛ."
                )
            else:
                raise

    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"ᴜɴᴩɪɴɴᴇᴅ-ᴀ-ᴍᴇssᴀɢᴇ\n"
        f"<b>ᴜɴᴩɪɴɴᴇᴅ ʙʏ :</b> {mention_html(user.id, html.escape(user.first_name))}"
    )

    return log_message


@bot_admin
async def pinned(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    bot = context.bot
    msg = update.effective_message
    msg_id = (
        update.effective_message.reply_to_message.message_id
        if update.effective_message.reply_to_message
        else update.effective_message.message_id
    )

    chat = await bot.get_chat(chat_id=msg.chat.id)
    if chat.pinned_message:
        pinned_id = chat.pinned_message.message_id
        if msg.chat.username:
            link_chat_id = msg.chat.username
            message_link = f"https://t.me/{link_chat_id}/{pinned_id}"
        elif (str(msg.chat.id)).startswith("-100"):
            link_chat_id = (str(msg.chat.id)).replace("-100", "")
            message_link = f"https://t.me/c/{link_chat_id}/{pinned_id}"
        else:
             message_link = ""

        await send_message(msg,
            f"ᴩɪɴɴᴇᴅ ᴏɴ {html.escape(chat.title)}.",
            reply_to_message_id=msg_id,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="ᴍᴇssᴀɢᴇ",
                            url=message_link,
                        )
                    ]
                ]
            ),
        )

    else:
        await send_message(msg,
            f"» ᴛʜᴇʀᴇ's ɴᴏ ᴩɪɴɴᴇᴅ ᴍᴇssᴀɢᴇ ɪɴ <b>{html.escape(chat.title)}!</b>",
            parse_mode=ParseMode.HTML,
        )


@bot_admin
@user_admin
@connection_status
async def invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    chat = update.effective_chat

    if chat.username:
        await send_message(update.effective_message, f"https://t.me/{chat.username}")
    elif chat.type in (ChatType.SUPERGROUP, ChatType.CHANNEL):
        bot_member = await chat.get_member(bot.id)
        if getattr(bot_member, 'can_invite_users', False):
            invitelink = await bot.export_chat_invite_link(chat.id)
            await send_message(update.effective_message, invitelink)
        else:
            await send_message(update.effective_message,
                "» ɪ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴩᴇʀᴍɪssɪᴏɴs ᴛᴏ ᴀᴄᴄᴇss ɪɴᴠɪᴛᴇ ʟɪɴᴋs !",
            )
    else:
        await send_message(update.effective_message,
            "» ɪ ᴄᴀɴ ᴏɴʟʏ ɢɪᴠᴇ ɪɴᴠɪᴛᴇ ʟɪɴᴋs ғᴏʀ ɢʀᴏᴜᴩs ᴀɴᴅ ᴄʜᴀɴɴᴇʟs !",
        )


@connection_status
async def adminlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    bot = context.bot

    if update.effective_message.chat.type == ChatType.PRIVATE:
        await send_message(
            update.effective_message,
            "» ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ᴄᴀɴ ᴏɴʟʏ ʙᴇ ᴜsᴇᴅ ɪɴ ɢʀᴏᴜᴩ's ɴᴏᴛ ɪɴ ᴩᴍ.",
        )
        return

    chat_id = update.effective_chat.id

    try:
        msg = await send_message(update.effective_message,
            "» ғᴇᴛᴄʜɪɴɢ ᴀᴅᴍɪɴs ʟɪsᴛ...",
            parse_mode=ParseMode.HTML,
        )
    except BadRequest:
        msg = await send_message(update.effective_message,
            "» ғᴇᴛᴄʜɪɴɢ ᴀᴅᴍɪɴs ʟɪsᴛ...",
            quote=False,
            parse_mode=ParseMode.HTML,
        )

    administrators = await bot.get_chat_administrators(chat_id)
    text = "ᴀᴅᴍɪɴs ɪɴ <b>{}</b>:".format(html.escape(update.effective_chat.title))

    for admin in administrators:
        user = admin.user
        status = admin.status
        custom_title = getattr(admin, 'custom_title', None)

        if user.first_name == "":
            name = "☠ ᴅᴇʟᴇᴛᴇᴅ ᴀᴄᴄᴏᴜɴᴛ"
        else:
            name = "{}".format(
                mention_html(
                    user.id,
                    html.escape(user.first_name + " " + (user.last_name or "")),
                ),
            )

        if user.is_bot:
            continue

        if status == ChatMemberStatus.OWNER:
            text += "\n 🥀 ᴏᴡɴᴇʀ :"
            text += "\n<code> • </code>{}\n".format(name)

            if custom_title:
                text += f"<code> ┗━ {html.escape(custom_title)}</code>\n"

    text += "\n💫 ᴀᴅᴍɪɴs :"

    custom_admin_list = {}
    normal_admin_list = []

    for admin in administrators:
        user = admin.user
        status = admin.status
        custom_title = getattr(admin, 'custom_title', None)

        if user.first_name == "":
            name = "☠ ᴅᴇʟᴇᴛᴇᴅ ᴀᴄᴄᴏᴜɴᴛ"
        else:
            name = "{}".format(
                mention_html(
                    user.id,
                    html.escape(user.first_name + " " + (user.last_name or "")),
                ),
            )

        if status == ChatMemberStatus.ADMINISTRATOR:
            if custom_title:
                try:
                    custom_admin_list[custom_title].append(name)
                except KeyError:
                    custom_admin_list.update({custom_title: [name]})
            else:
                normal_admin_list.append(name)

    for admin in normal_admin_list:
        text += "\n<code> • </code>{}".format(admin)

    for admin_group in custom_admin_list.copy():
        if len(custom_admin_list[admin_group]) == 1:
            text += "\n<code> • </code>{} | <code>{}</code>".format(
                custom_admin_list[admin_group][0],
                html.escape(admin_group),
            )
            custom_admin_list.pop(admin_group)

    text += "\n"
    for admin_group, value in custom_admin_list.items():
        text += "\n🔮 <code>{}</code>".format(admin_group)
        for admin in value:
            text += "\n<code> • </code>{}".format(admin)
        text += "\n"

    try:
        await msg.edit_text(text, parse_mode=ParseMode.HTML)
    except BadRequest:  # if original message is deleted
        return


__help__ = """
*User Commands*:
❍ /admins*:* List admins in group.
 ❍ /pinned*:* Current pinned message.

*Admins only:*
 ❍ /pin*:* Pin message (use 'loud').
 ❍ /unpin*:* Unpin current message.
 ❍ /invitelink*:* Gets group invite link.
 ❍ /promote [user] [title]*:* Promote user to admin (with optional custom title/tag).
 ❍ /fullpromote [user] [title]*:* Promote with full rights (with optional title/tag).
 ❍ /lowpromote [user] [title]*:* Promote with limited rights (with optional title/tag).
 ❍ /demote*:* Demote user to member.
 ❍ /title [user] <title>*:* Set or change admin title/tag (aliases: /settitle, /admintag, /tag).
 ❍ /admincache*:* Refresh admin list.
 ❍ /del*:* Delete replied message.
 ❍ /purge*:* Purge messages between two.
 ❍ /setgtitle <text>*:* Set group title.
 ❍ /setgpic*:* Reply to photo to set as pfp.
 ❍ /setdesc*:* Set group description.
 ❍ /setsticker*:* Set group sticker pack.
"""

SET_DESC_HANDLER = CommandHandler("setdesc", set_desc)
SET_STICKER_HANDLER = CommandHandler("setsticker", set_sticker)
SETCHATPIC_HANDLER = CommandHandler("setgpic", setchatpic)
RMCHATPIC_HANDLER = CommandHandler("delgpic", rmchatpic)
SETCHAT_TITLE_HANDLER = CommandHandler("setgtitle", setchat_title)

ADMINLIST_HANDLER = DisableAbleCommandHandler(
    ["admins", "staff"], adminlist
)

PIN_HANDLER = CommandHandler("pin", pin)
UNPIN_HANDLER = CommandHandler("unpin", unpin)
PINNED_HANDLER = CommandHandler("pinned", pinned)

INVITE_HANDLER = DisableAbleCommandHandler("invitelink", invite)

PROMOTE_HANDLER = DisableAbleCommandHandler("promote", promote)
FULLPROMOTE_HANDLER = DisableAbleCommandHandler(
    "fullpromote", fullpromote
)
LOW_PROMOTE_HANDLER = DisableAbleCommandHandler(
    "lowpromote", lowpromote
)
DEMOTE_HANDLER = DisableAbleCommandHandler("demote", demote)

SET_TITLE_HANDLER = CommandHandler(
    ["title", "settitle", "admintag", "settag", "tag"], set_title
)
ADMIN_REFRESH_HANDLER = CommandHandler(
    ["admincache", "reload", "refresh"],
    refresh_admin,
)

application.add_handler(SET_DESC_HANDLER)
application.add_handler(SET_STICKER_HANDLER)
application.add_handler(SETCHATPIC_HANDLER)
application.add_handler(RMCHATPIC_HANDLER)
application.add_handler(SETCHAT_TITLE_HANDLER)
application.add_handler(ADMINLIST_HANDLER)
application.add_handler(PIN_HANDLER)
application.add_handler(UNPIN_HANDLER)
application.add_handler(PINNED_HANDLER)
application.add_handler(INVITE_HANDLER)
application.add_handler(PROMOTE_HANDLER)
application.add_handler(FULLPROMOTE_HANDLER)
application.add_handler(LOW_PROMOTE_HANDLER)
application.add_handler(DEMOTE_HANDLER)
application.add_handler(SET_TITLE_HANDLER)
application.add_handler(ADMIN_REFRESH_HANDLER)

__mod_name__ = "Aᴅᴍɪɴs"
__command_list__ = [
    "setdesc", "setsticker", "setgpic", "delgpic", "setgtitle", "adminlist",
    "admins",
    "invitelink",
    "promote",
    "fullpromote",
    "lowpromote",
    "demote",
    "title",
    "settitle",
    "admintag",
    "tag",
    "admincache",
]
__handlers__ = [
    SET_DESC_HANDLER,
    SET_STICKER_HANDLER,
    SETCHATPIC_HANDLER,
    RMCHATPIC_HANDLER,
    SETCHAT_TITLE_HANDLER,
    ADMINLIST_HANDLER,
    PIN_HANDLER,
    UNPIN_HANDLER,
    PINNED_HANDLER,
    INVITE_HANDLER,
    PROMOTE_HANDLER,
    FULLPROMOTE_HANDLER,
    LOW_PROMOTE_HANDLER,
    DEMOTE_HANDLER,
    SET_TITLE_HANDLER,
    ADMIN_REFRESH_HANDLER,
]
