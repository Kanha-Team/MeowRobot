#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode, ChatType
from telegram.error import BadRequest
from telegram.ext import ContextTypes, CommandHandler
from telegram.helpers import escape_markdown

import MeowRobot.modules.sql.rules_sql as sql
from MeowRobot import application
from MeowRobot.modules.helper_funcs.chat_status import connection_status, user_admin
from MeowRobot.modules.helper_funcs.string_handling import markdown_parser


@connection_status
async def get_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    here = args and args[0] == "here"
    chat_id = update.effective_chat.id
    # connection_status sets update.effective_chat
    real_chat = update.effective_message.chat
    dest_chat = real_chat.id if here else None
    await send_rules(update, context, chat_id, real_chat.type == ChatType.PRIVATE or here, dest_chat)


async def send_rules(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, from_pm: bool = False, dest_chat: int = None):
    bot = context.bot
    user = update.effective_user
    reply_msg = update.effective_message.reply_to_message
    dest_chat = dest_chat or user.id
    try:
        chat = await bot.get_chat(chat_id)
    except BadRequest as excp:
        if excp.message == "Chat not found" and from_pm:
            await bot.send_message(
                dest_chat,
                "The rules shortcut for this chat hasn't been set properly! Ask admins to "
                "fix this.\nMaybe they forgot the hyphen in ID",
            )
            return
        else:
            raise

    rules = sql.get_rules(chat_id)
    text = f"The rules for *{escape_markdown(chat.title)}* are:\n\n{rules}"

    if from_pm and rules:
        await bot.send_message(
            dest_chat,
            text,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )
    elif from_pm:
        await bot.send_message(
            dest_chat,
            "The group admins haven't set any rules for this chat yet. "
            "This probably doesn't mean it's lawless though...!",
        )
    elif rules and reply_msg:
        await reply_msg.reply_text(
            "ᴄʟɪᴄᴋ ᴏɴ ᴛʜᴇ ʙᴜᴛᴛᴏɴ ʙᴇʟᴏᴡ ᴛᴏ ɢᴇᴛ ʀᴜʟᴇs.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="• ʀᴜʟᴇs •",
                            url=f"t.me/{(await bot.get_me()).username}?start={chat_id}",
                        ),
                    ],
                ],
            ),
        )
    elif rules:
        await update.effective_message.reply_text(
            "ᴄʟɪᴄᴋ ᴏɴ ᴛʜᴇ ʙᴜᴛᴛᴏɴ ʙᴇʟᴏᴡ ᴛᴏ ɢᴇᴛ ʀᴜʟᴇs.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="• ʀᴜʟᴇs •",
                            url=f"t.me/{(await bot.get_me()).username}?start={chat_id}",
                        ),
                    ],
                ],
            ),
        )
    else:
        await update.effective_message.reply_text(
            "The group admins haven't set any rules for this chat yet. "
            "This probably doesn't mean it's lawless though...!",
        )


@connection_status
@user_admin
async def set_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    msg = update.effective_message
    raw_text = msg.text
    args = raw_text.split(None, 1)  # use python's maxsplit to separate cmd and args
    txt = entities = None
    if len(args) == 2:
        txt = args[1]
        entities = msg.parse_entities()
    elif msg.reply_to_message:
        txt = msg.reply_to_message.text
        entities = msg.reply_to_message.parse_entities()
    if txt:
        offset = len(txt) - len(raw_text)  # set correct offset relative to command
        markdown_rules = markdown_parser(
            txt,
            entities=entities,
            offset=offset,
        )

        sql.set_rules(chat_id, markdown_rules)
        await update.effective_message.reply_text("Successfully set rules for this group.")
    else:
        await update.effective_message.reply_text("There's... no rules?")


@connection_status
@user_admin
async def clear_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    sql.set_rules(chat_id, "")
    await update.effective_message.reply_text("Successfully cleared rules!")


def __stats__():
    return f"• {sql.num_chats()} groups have rules."


def __import_data__(chat_id, data):
    # set chat rules
    rules = data.get("info", {}).get("rules", "")
    sql.set_rules(chat_id, rules)


async def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    return f"This chat has had it's rules set: `{bool(sql.get_rules(chat_id))}`"


__help__ = """
 ‣ `/rules`*:* get the rules for this chat.
 ‣ `/rules here`*:* get the rules for this chat but send it in the chat.
*Admins only:*
 ‣ `/setrules <your rules here>`*:* set the rules for this chat.
 ‣ `/clearrules`*:* clear the rules for this chat.
"""

__mod_name__ = "Rᴜʟᴇs"

GET_RULES_HANDLER = CommandHandler("rules", get_rules)
SET_RULES_HANDLER = CommandHandler("setrules", set_rules)
RESET_RULES_HANDLER = CommandHandler("clearrules", clear_rules)

application.add_handler(GET_RULES_HANDLER)
application.add_handler(SET_RULES_HANDLER)
application.add_handler(RESET_RULES_HANDLER)

__handlers__ = [GET_RULES_HANDLER, SET_RULES_HANDLER, RESET_RULES_HANDLER]
