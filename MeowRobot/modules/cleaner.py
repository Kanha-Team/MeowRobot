#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import html

from telegram import Update
from telegram.constants import ParseMode, ChatType
from telegram.error import BadRequest
from telegram.ext import ContextTypes, CommandHandler, filters, MessageHandler

from MeowRobot import ALLOW_EXCL, application
from MeowRobot.modules.disable import DisableAbleCommandHandler
from MeowRobot.modules.helper_funcs.chat_status import (
    bot_can_delete,
    connection_status,
    dev_plus,
    user_admin,
)
from MeowRobot.modules.sql import cleaner_sql as sql
from telegram.constants import ChatMemberStatus 
CMD_STARTERS = ("/", "!") if ALLOW_EXCL else ("/",)
BLUE_TEXT_CLEAN_GROUP = 13

command_list = [
    "cleanblue",
    "ignoreblue",
    "unignoreblue",
    "listblue",
    "ungignoreblue",
    "gignoreblue",
    "start",
    "help",
    "settings",
    "donate",
    "stalk",
    "aka",
    "leaderboard",
]


# 🔥 MAIN FIXED FUNCTION
async def clean_blue_text_must_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    chat = update.effective_chat
    message = update.effective_message

    if not message or not message.text:
        return

    try:
        member = await chat.get_member(bot.id)
    except:
        return

    # ✅ SAFE CHECK (NO ERROR)
    if not (
        member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
        and getattr(member, "can_delete_messages", False)
        and sql.is_enabled(chat.id)
    ):
        return

    fst_word = message.text.strip().split(None, 1)[0]

    if len(fst_word) > 1 and any(
        fst_word.startswith(start) for start in CMD_STARTERS
    ):
        command = fst_word[1:].split("@")[0].lower()

        if sql.is_command_ignored(chat.id, command):
            return

        if command not in command_list:
            try:
                await message.delete()
            except BadRequest:
                pass


# ---------------- SETTINGS ---------------- #

@connection_status
@user_admin
async def set_blue_text_must_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    args = context.args

    if len(args) >= 1:
        val = args[0].lower()

        if val in ("off", "no"):
            sql.set_cleanbt(chat.id, False)
            await message.reply_text(
                f"Bluetext cleaning disabled for <b>{html.escape(chat.title)}</b>",
                parse_mode=ParseMode.HTML,
            )

        elif val in ("yes", "on"):
            sql.set_cleanbt(chat.id, True)
            await message.reply_text(
                f"Bluetext cleaning enabled for <b>{html.escape(chat.title)}</b>",
                parse_mode=ParseMode.HTML,
            )

        else:
            await message.reply_text("Use: on / off")

    else:
        status = "Enabled" if sql.is_enabled(chat.id) else "Disabled"
        await message.reply_text(
            f"Bluetext cleaning: <b>{status}</b>",
            parse_mode=ParseMode.HTML,
        )


@user_admin
async def add_bluetext_ignore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    args = context.args

    if not args:
        return await update.message.reply_text("Give command name")

    val = args[0].lower()

    if sql.chat_ignore_command(chat.id, val):
        await update.message.reply_text(f"{val} ignored")
    else:
        await update.message.reply_text("Already ignored")


@user_admin
async def remove_bluetext_ignore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    args = context.args

    if not args:
        return await update.message.reply_text("Give command name")

    val = args[0].lower()

    if sql.chat_unignore_command(chat.id, val):
        await update.message.reply_text(f"{val} removed")
    else:
        await update.message.reply_text("Not ignored")


@dev_plus
async def add_bluetext_ignore_global(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args

    if not args:
        return await update.message.reply_text("Give command")

    val = args[0].lower()

    if sql.global_ignore_command(val):
        await update.message.reply_text(f"{val} globally ignored")
    else:
        await update.message.reply_text("Already ignored")


@dev_plus
async def remove_bluetext_ignore_global(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args

    if not args:
        return await update.message.reply_text("Give command")

    val = args[0].lower()

    if sql.global_unignore_command(val):
        await update.message.reply_text(f"{val} removed globally")
    else:
        await update.message.reply_text("Not ignored")


@dev_plus
async def bluetext_ignore_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat

    global_list, local_list = sql.get_all_ignored(chat.id)

    text = ""

    if global_list:
        text += "Global ignored:\n"
        for x in global_list:
            text += f" - {x}\n"

    if local_list:
        text += "\nLocal ignored:\n"
        for x in local_list:
            text += f" - {x}\n"

    if not text:
        text = "No ignored commands"

    await update.message.reply_text(text)
    
__help__ = """
*ʙʟᴜᴇ ᴛᴇxᴛ ᴄʟᴇᴀɴᴇʀ* ʀᴇᴍᴏᴠᴇᴅ ᴀɴʏ ᴍᴀᴅᴇ ᴜᴘ ᴄᴏᴍᴍᴀɴᴅs ᴛʜᴀᴛ ᴘᴇᴏᴘʟᴇ sᴇɴᴅ ɪɴ ʏᴏᴜʀ ᴄʜᴀᴛ
.
 ❍ /cleanblue <on/off/yes/no>*:* clean commands after sending
 ❍ /ignoreblue <word>*:* prevent auto cleaning of the command
 ❍ /unignoreblue <word>*:* remove prevent auto cleaning of the command
 ❍ /listblue*:* list currently whitelisted commands
"""

SET_CLEAN_BLUE_TEXT_HANDLER = CommandHandler(
    "cleanblue", set_blue_text_must_click
)
ADD_CLEAN_BLUE_TEXT_HANDLER = CommandHandler(
    "ignoreblue", add_bluetext_ignore
)
REMOVE_CLEAN_BLUE_TEXT_HANDLER = CommandHandler(
    "unignoreblue", remove_bluetext_ignore
)
ADD_CLEAN_BLUE_TEXT_GLOBAL_HANDLER = CommandHandler(
    "gignoreblue", add_bluetext_ignore_global
)
REMOVE_CLEAN_BLUE_TEXT_GLOBAL_HANDLER = CommandHandler(
    "ungignoreblue", remove_bluetext_ignore_global
)
LIST_CLEAN_BLUE_TEXT_HANDLER = CommandHandler(
    "listblue", bluetext_ignore_list
)
CLEAN_BLUE_TEXT_HANDLER = MessageHandler(
    filters.COMMAND & filters.ChatType.GROUPS,
    clean_blue_text_must_click,
)

application.add_handler(SET_CLEAN_BLUE_TEXT_HANDLER)
application.add_handler(ADD_CLEAN_BLUE_TEXT_HANDLER)
application.add_handler(REMOVE_CLEAN_BLUE_TEXT_HANDLER)
application.add_handler(ADD_CLEAN_BLUE_TEXT_GLOBAL_HANDLER)
application.add_handler(REMOVE_CLEAN_BLUE_TEXT_GLOBAL_HANDLER)
application.add_handler(LIST_CLEAN_BLUE_TEXT_HANDLER)
application.add_handler(CLEAN_BLUE_TEXT_HANDLER, BLUE_TEXT_CLEAN_GROUP)

__mod_name__ = "Bʟᴜᴇᴛᴇxᴛ"
__handlers__ = [
    SET_CLEAN_BLUE_TEXT_HANDLER,
    ADD_CLEAN_BLUE_TEXT_HANDLER,
    REMOVE_CLEAN_BLUE_TEXT_HANDLER,
    ADD_CLEAN_BLUE_TEXT_GLOBAL_HANDLER,
    REMOVE_CLEAN_BLUE_TEXT_GLOBAL_HANDLER,
    LIST_CLEAN_BLUE_TEXT_HANDLER,
    (CLEAN_BLUE_TEXT_HANDLER, BLUE_TEXT_CLEAN_GROUP),
]
