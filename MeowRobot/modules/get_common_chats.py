#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import os
import asyncio

from telegram import Update
from telegram.constants import ParseMode
from telegram.error import BadRequest, Forbidden
from telegram.ext import ContextTypes, CommandHandler, filters

from MeowRobot import OWNER_ID, application
from MeowRobot.modules.helper_funcs.extraction import extract_user
from MeowRobot.modules.sql.users_sql import get_user_com_chats


async def get_user_common_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot, args = context.bot, context.args
    msg = update.effective_message
    user_id = await extract_user(msg, args)
    if not user_id:
        await msg.reply_text("I share no common chats with the void.")
        return

    common_list = get_user_com_chats(user_id)
    if not common_list:
        await msg.reply_text("No common chats with this user!")
        return

    try:
        user_chat = await bot.get_chat(user_id)
        name = user_chat.first_name
    except:
        name = "User"

    text = f"<b>Common chats with {name}</b>\n"
    for chat_id in common_list:
        try:
            chat = await bot.get_chat(chat_id)
            await asyncio.sleep(0.3)
            text += f"• <code>{chat.title}</code>\n"
        except (BadRequest, Forbidden):
            pass

    if len(text) < 4096:
        await msg.reply_text(text, parse_mode=ParseMode.HTML)
    else:
        with open("common_chats.txt", "w") as f:
            f.write(text)
        with open("common_chats.txt", "rb") as f:
            await msg.reply_document(f)
        os.remove("common_chats.txt")


COMMON_CHATS_HANDLER = CommandHandler(
    "getchats", get_user_common_chats, filters=filters.User(OWNER_ID)
)

application.add_handler(COMMON_CHATS_HANDLER)

__handlers__ = [COMMON_CHATS_HANDLER]
