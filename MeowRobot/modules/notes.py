#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import ast
import re
from io import BytesIO

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.constants import ChatType, ParseMode, ChatMemberStatus
from telegram.error import BadRequest
from telegram.ext import (
    ContextTypes,
    CallbackQueryHandler,
    CommandHandler,
    filters,
    MessageHandler,
)
from telegram.helpers import escape_markdown, mention_markdown

import MeowRobot.modules.sql.notes_sql as sql
from MeowRobot import DRAGONS, EVENT_LOGS, LOGGER, SUPPORT_CHAT, application
from MeowRobot.modules.helper_funcs.alternate import send_message
from MeowRobot.modules.disable import DisableAbleCommandHandler
from MeowRobot.modules.helper_funcs.chat_status import connection_status, user_admin
from MeowRobot.modules.helper_funcs.misc import build_keyboard, revert_buttons
from MeowRobot.modules.helper_funcs.msg_types import get_note_type
from MeowRobot.modules.helper_funcs.string_handling import (
    escape_invalid_curly_brackets,
)

FILE_MATCHER = re.compile(r"^###file_id(!photo)?###:(.*?)(?:\s|$)")
STICKER_MATCHER = re.compile(r"^###sticker(!photo)?###:")
BUTTON_MATCHER = re.compile(r"^###button(!photo)?###:(.*?)(?:\s|$)")
MYFILE_MATCHER = re.compile(r"^###file(!photo)?###:")
MYPHOTO_MATCHER = re.compile(r"^###photo(!photo)?###:")
MYAUDIO_MATCHER = re.compile(r"^###audio(!photo)?###:")
MYVOICE_MATCHER = re.compile(r"^###voice(!photo)?###:")
MYVIDEO_MATCHER = re.compile(r"^###video(!photo)?###:")
MYVIDEONOTE_MATCHER = re.compile(r"^###video_note(!photo)?###:")

JOIN_LOGGER = EVENT_LOGS # Assuming they are same if EVENT_LOGS is defined

ENUM_FUNC_MAP = {
    sql.Types.TEXT.value: "send_message",
    sql.Types.BUTTON_TEXT.value: "send_message",
    sql.Types.STICKER.value: "send_sticker",
    sql.Types.DOCUMENT.value: "send_document",
    sql.Types.PHOTO.value: "send_photo",
    sql.Types.AUDIO.value: "send_audio",
    sql.Types.VOICE.value: "send_voice",
    sql.Types.VIDEO.value: "send_video",
}


@connection_status
async def get(update: Update, context: ContextTypes.DEFAULT_TYPE, notename, show_none=True, no_format=False):
    bot = context.bot
    chat_id = update.effective_chat.id
    note = sql.get_note(chat_id, notename)
    message = update.effective_message

    if note:
        if message.reply_to_message:
            reply_id = message.reply_to_message.message_id
        else:
            reply_id = message.message_id

        if note.is_reply:
            if JOIN_LOGGER:
                try:
                    await bot.forward_message(
                        chat_id=chat_id, from_chat_id=JOIN_LOGGER, message_id=note.value
                    )
                except BadRequest as excp:
                    if excp.message == "Message to forward not found":
                        await send_message(
                            message,
                            "This message seems to have been lost - I'll remove it "
                            "from your notes list."
                        )
                        sql.rm_note(chat_id, notename)
                    else:
                        raise
            else:
                try:
                    await bot.forward_message(
                        chat_id=chat_id, from_chat_id=chat_id, message_id=note.value
                    )
                except BadRequest as excp:
                    if excp.message == "Message to forward not found":
                        await send_message(
                            message,
                            "Looks like the original sender of this note has deleted "
                            "their message - sorry! Get your bot admin to start using a "
                            "message dump to avoid this. I'll remove this note from "
                            "your saved notes."
                        )
                        sql.rm_note(chat_id, notename)
                    else:
                        raise
        else:
            VALID_NOTE_FORMATTERS = [
                "first",
                "last",
                "fullname",
                "username",
                "id",
                "chatname",
                "mention",
            ]
            valid_format = escape_invalid_curly_brackets(
                note.value, VALID_NOTE_FORMATTERS
            )
            if valid_format:
                text = valid_format.format(
                    first=escape_markdown(message.from_user.first_name),
                    last=escape_markdown(
                        message.from_user.last_name or message.from_user.first_name
                    ),
                    fullname=escape_markdown(
                        " ".join(
                            [message.from_user.first_name, message.from_user.last_name]
                            if message.from_user.last_name
                            else [message.from_user.first_name]
                        )
                    ),
                    username=(
                        "@" + message.from_user.username
                        if message.from_user.username
                        else mention_markdown(
                            message.from_user.id, message.from_user.first_name
                        )
                    ),
                    mention=mention_markdown(
                        message.from_user.id, message.from_user.first_name
                    ),
                    chatname=escape_markdown(
                        message.chat.title
                        if message.chat.type != ChatType.PRIVATE
                        else message.from_user.first_name
                    ),
                    id=message.from_user.id,
                )
            else:
                text = ""

            keyb = []
            parseMode = ParseMode.MARKDOWN
            buttons = sql.get_buttons(chat_id, notename)
            if no_format:
                parseMode = None
                text += revert_buttons(buttons)
            else:
                keyb = build_keyboard(buttons)

            keyboard = InlineKeyboardMarkup(keyb)

            try:
                if note.msgtype in (sql.Types.BUTTON_TEXT, sql.Types.TEXT):
                    await bot.send_message(
                        chat_id,
                        text,
                        reply_to_message_id=reply_id,
                        parse_mode=parseMode,
                        disable_web_page_preview=True,
                        reply_markup=keyboard,
                    )
                else:
                    method = getattr(bot, ENUM_FUNC_MAP[note.msgtype])
                    await method(
                        chat_id,
                        note.file,
                        caption=text,
                        reply_to_message_id=reply_id,
                        parse_mode=parseMode,
                        reply_markup=keyboard,
                    )

            except BadRequest as excp:
                if excp.message == "Entity_mention_user_invalid":
                    await send_message(
                        message,
                        "Looks like you tried to mention someone I've never seen before. If you really "
                        "want to mention them, forward one of their messages to me, and I'll be able "
                        "to tag them!"
                    )
                elif FILE_MATCHER.match(note.value):
                    await send_message(
                        message,
                        "This note was an incorrectly imported file from another bot - I can't use "
                        "it. If you really need it, you'll have to save it again. In "
                        "the meantime, I'll remove it from your notes list."
                    )
                    sql.rm_note(chat_id, notename)
                else:
                    await send_message(
                        message,
                        "This note could not be sent, as it is incorrectly formatted. Ask in "
                        f"@{SUPPORT_CHAT} if you can't figure out why!"
                    )
                    LOGGER.exception(
                        "Could not parse message #%s in chat %s", notename, str(chat_id)
                    )
                    LOGGER.warning("Message was: %s", str(note.value))
        return
    elif show_none:
        await send_message(message, "This note doesn't exist")


@connection_status
async def cmd_get(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) >= 2 and args[1].lower() == "noformat":
        await get(update, context, args[0].lower(), show_none=True, no_format=True)
    elif len(args) >= 1:
        await get(update, context, args[0].lower(), show_none=True)
    else:
        await send_message(update.effective_message, "Get rekt")


@connection_status
async def hash_get(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message.text
    fst_word = message.split()[0]
    no_hash = fst_word[1:].lower()
    await get(update, context, no_hash, show_none=False)


@connection_status
async def slash_get(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message, chat_id = update.effective_message.text, update.effective_chat.id
    no_slash = message[1:]
    note_list = sql.get_all_chat_notes(chat_id)

    try:
        noteid = note_list[int(no_slash) - 1]
        note_name = noteid.name.lower()
        await get(update, context, note_name, show_none=False)
    except (IndexError, ValueError):
        await send_message(update.effective_message, "Wrong Note ID 😾")


@user_admin
@connection_status
async def save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    msg = update.effective_message

    note_name, text, data_type, content, buttons = await get_note_type(msg)
    note_name = note_name.lower()
    if data_type is None:
        await send_message(msg, "Dude, there's no note")
        return

    sql.add_note_to_db(
        chat_id, note_name, text, data_type, buttons=buttons, file=content
    )

    await send_message(
        msg,
        f"Yas! Added `{note_name}`.\nGet it with /get `{note_name}`, or `#{note_name}`",
        parse_mode=ParseMode.MARKDOWN,
    )

    if msg.reply_to_message and msg.reply_to_message.from_user.is_bot:
        if text:
            await send_message(
                msg,
                "Seems like you're trying to save a message from a bot. Unfortunately, "
                "bots can't forward bot messages, so I can't save the exact message. "
                "\nI'll save all the text I can, but if you want more, you'll have to "
                "forward the message yourself, and then save it."
            )
        else:
            await send_message(
                msg,
                "Bots are kinda handicapped by telegram, making it hard for bots to "
                "interact with other bots, so I can't save this message "
                "like I usually would - do you mind forwarding it and "
                "then saving that new message? Thanks!"
            )
        return


@user_admin
@connection_status
async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    chat_id = update.effective_chat.id
    if len(args) >= 1:
        notename = args[0].lower()

        if sql.rm_note(chat_id, notename):
            await send_message(update.effective_message, "Successfully removed note.")
        else:
            await send_message(update.effective_message, "That's not a note in my database!")


async def clearall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    member = await chat.get_member(user.id)
    if member.status != ChatMemberStatus.OWNER and user.id not in DRAGONS:
        await send_message(
            update.effective_message,
            "Only the chat owner can clear all notes at once."
        )
    else:
        buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="Delete all notes", callback_data="notes_rmall"
                    )
                ],
                [InlineKeyboardButton(text="Cancel", callback_data="notes_cancel")],
            ]
        )
        await send_message(
            update.effective_message,
            f"Are you sure you would like to clear ALL notes in {chat.title}? This action cannot be undone.",
            reply_markup=buttons,
            parse_mode=ParseMode.MARKDOWN,
        )


async def clearall_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat = update.effective_chat
    message = update.effective_message
    member = await chat.get_member(query.from_user.id)
    if query.data == "notes_rmall":
        if member.status == ChatMemberStatus.OWNER or query.from_user.id in DRAGONS:
            note_list = sql.get_all_chat_notes(chat.id)
            try:
                for notename in note_list:
                    note = notename.name.lower()
                    sql.rm_note(chat.id, note)
                await message.edit_text("Deleted all notes.")
            except BadRequest:
                return

        elif member.status == ChatMemberStatus.ADMINISTRATOR:
            await query.answer("Only owner of the chat can do this.")

        else:
            await query.answer("You need to be admin to do this.")
    elif query.data == "notes_cancel":
        if member.status == ChatMemberStatus.OWNER or query.from_user.id in DRAGONS:
            await message.edit_text("Clearing of all notes has been cancelled.")
            return
        if member.status == ChatMemberStatus.ADMINISTRATOR:
            await query.answer("Only owner of the chat can do this.")
        else:
            await query.answer("You need to be admin to do this.")


@connection_status
async def list_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    note_list = sql.get_all_chat_notes(chat_id)
    notes = len(note_list) + 1
    msg = "Get note by `/notenumber` or `#notename` \n\n  *ID*    *Note* \n"
    for note_id, note in zip(range(1, notes), note_list):
        if note_id < 10:
            note_name = f"`{note_id:2}.`  `#{(note.name.lower())}`\n"
        else:
            note_name = f"`{note_id}.`  `#{(note.name.lower())}`\n"
        if len(msg) + len(note_name) > 4096:
            await send_message(update.effective_message, msg, parse_mode=ParseMode.MARKDOWN)
            msg = ""
        msg += note_name

    if not note_list:
        await send_message(update.effective_message, "No notes in this chat!")

    elif len(msg) != 0:
        await send_message(update.effective_message, msg, parse_mode=ParseMode.MARKDOWN)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


async def __chat_settings__(chat_id, user_id):
    notes = sql.get_all_chat_notes(chat_id)
    return f"There are `{len(notes)}` notes in this chat."


__help__ = """

 ❍ `/get <notename>`*:* get the note with this notename
 ❍ `#<notename>`*:* same as /get
 ❍ `/notes` or `/saved`*:* list all saved notes in this chat
 ❍ `/number` *:* Will pull the note of that number in the list. 
If you would like to retrieve the contents of a note without any formatting, use `/get <notename> noformat`. This can \
be useful when updating a current note.

*Admins only:*
 ❍ `/save <notename> <notedata>`*:* saves notedata as a note with name notename
A button can be added to a note by using standard markdown link syntax - the link should just be prepended with a \
`buttonurl:` section, as such: `[somelink](buttonurl:example.com)`. Check `/markdownhelp` for more info.
 ❍ `/save <notename>`*:* save the replied message as a note with name notename
 ❍ `/clear <notename>`*:* clear note with this name
 ❍ `/removeallnotes`*:* removes all notes from the group
 *Note:* Note names are case-insensitive, and they are automatically converted to lowercase before getting saved.
"""

__mod_name__ = "Nᴏᴛᴇs"

GET_HANDLER = CommandHandler("get", cmd_get)
HASH_GET_HANDLER = MessageHandler(filters.Regex(r"^#[^\s]+"), hash_get)
SLASH_GET_HANDLER = MessageHandler(filters.Regex(r"^/\d+$"), slash_get)
SAVE_HANDLER = CommandHandler("save", save)
DELETE_HANDLER = CommandHandler("clear", clear)
LIST_HANDLER = DisableAbleCommandHandler(
    ["notes", "saved"], list_notes, admin_ok=True
)
CLEARALL = DisableAbleCommandHandler("removeallnotes", clearall)
CLEARALL_BTN = CallbackQueryHandler(clearall_btn, pattern=r"notes_.*")

application.add_handler(GET_HANDLER)
application.add_handler(SAVE_HANDLER)
application.add_handler(LIST_HANDLER)
application.add_handler(DELETE_HANDLER)
application.add_handler(HASH_GET_HANDLER)
application.add_handler(SLASH_GET_HANDLER)
application.add_handler(CLEARALL)
application.add_handler(CLEARALL_BTN)

__handlers__ = [
    GET_HANDLER,
    SAVE_HANDLER,
    LIST_HANDLER,
    DELETE_HANDLER,
    HASH_GET_HANDLER,
    SLASH_GET_HANDLER,
    CLEARALL,
    CLEARALL_BTN,
]
