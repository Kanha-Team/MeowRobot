#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import html

from telegram import ChatPermissions, Update
from telegram.constants import ChatType, ParseMode
from telegram.error import BadRequest
from telegram.ext import ContextTypes, CommandHandler, filters, MessageHandler
from telegram.helpers import mention_markdown

import MeowRobot.modules.sql.blsticker_sql as sql
from MeowRobot import LOGGER, application
from MeowRobot.modules.connection import connected
from MeowRobot.modules.disable import DisableAbleCommandHandler
from MeowRobot.modules.helper_funcs.alternate import send_message
from MeowRobot.modules.helper_funcs.chat_status import user_admin, user_not_admin
from MeowRobot.modules.helper_funcs.misc import split_message
from MeowRobot.modules.helper_funcs.string_handling import extract_time
from MeowRobot.modules.log_channel import loggable
from MeowRobot.modules.warns import warn


async def blackliststicker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    args = context.args
    conn = await connected(context.bot, update, chat, user.id, need_admin=False)
    if conn:
        chat_id = conn
        chat_obj = await context.bot.get_chat(conn)
        chat_name = chat_obj.title
    else:
        if chat.type == "private":
            return
        chat_id = update.effective_chat.id
        chat_name = chat.title

    sticker_list = "<b>List blacklisted stickers currently in {}:</b>\n".format(
        chat_name
    )

    all_stickerlist = sql.get_chat_stickers(chat_id)

    if len(args) > 0 and args[0].lower() == "copy":
        for trigger in all_stickerlist:
            sticker_list += "<code>{}</code>\n".format(html.escape(trigger))
    elif len(args) == 0:
        for trigger in all_stickerlist:
            sticker_list += " - <code>{}</code>\n".format(html.escape(trigger))

    split_text = split_message(sticker_list)
    for text in split_text:
        if sticker_list == "<b>List blacklisted stickers currently in {}:</b>\n".format(
            chat_name
        ):
            await send_message(
                update.effective_message,
                "There are no blacklist stickers in <b>{}</b>!".format(
                    html.escape(chat_name)
                ),
                parse_mode=ParseMode.HTML,
            )
            return
        await send_message(update.effective_message, text, parse_mode=ParseMode.HTML)


@user_admin
async def add_blackliststicker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    words = msg.text.split(None, 1)
    conn = await connected(bot, update, chat, user.id)
    if conn:
        chat_id = conn
        chat_obj = await bot.get_chat(conn)
        chat_name = chat_obj.title
    else:
        chat_id = update.effective_chat.id
        if chat.type == "private":
            return
        else:
            chat_name = chat.title

    if len(words) > 1:
        text = words[1].replace("https://t.me/addstickers/", "")
        to_blacklist = list(
            {trigger.strip() for trigger in text.split("\n") if trigger.strip()}
        )

        added = 0
        for trigger in to_blacklist:
            try:
                await bot.get_sticker_set(trigger)
                sql.add_to_stickers(chat_id, trigger.lower())
                added += 1
            except BadRequest:
                await send_message(
                    update.effective_message,
                    "Sticker `{}` can not be found!".format(trigger),
                    parse_mode=ParseMode.MARKDOWN,
                )

        if added == 0:
            return

        if len(to_blacklist) == 1:
            await send_message(
                update.effective_message,
                "Sticker <code>{}</code> added to blacklist stickers in <b>{}</b>!".format(
                    html.escape(to_blacklist[0]), html.escape(chat_name)
                ),
                parse_mode=ParseMode.HTML,
            )
        else:
            await send_message(
                update.effective_message,
                "<code>{}</code> stickers added to blacklist sticker in <b>{}</b>!".format(
                    added, html.escape(chat_name)
                ),
                parse_mode=ParseMode.HTML,
            )
    elif msg.reply_to_message and msg.reply_to_message.sticker:
        added = 0
        trigger = msg.reply_to_message.sticker.set_name
        if trigger is None:
            await send_message(update.effective_message, "Sticker is invalid!")
            return
        try:
            await bot.get_sticker_set(trigger)
            sql.add_to_stickers(chat_id, trigger.lower())
            added += 1
        except BadRequest:
            await send_message(
                update.effective_message,
                "Sticker `{}` can not be found!".format(trigger),
                parse_mode=ParseMode.MARKDOWN,
            )

        if added == 0:
            return

        await send_message(
            update.effective_message,
            "Sticker <code>{}</code> added to blacklist stickers in <b>{}</b>!".format(
                trigger, html.escape(chat_name)
            ),
            parse_mode=ParseMode.HTML,
        )
    else:
        await send_message(
            update.effective_message,
            "Tell me what stickers you want to add to the blacklist.",
        )


@user_admin
async def unblackliststicker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    words = msg.text.split(None, 1)
    conn = await connected(bot, update, chat, user.id)
    if conn:
        chat_id = conn
        chat_obj = await bot.get_chat(conn)
        chat_name = chat_obj.title
    else:
        chat_id = update.effective_chat.id
        if chat.type == "private":
            return
        else:
            chat_name = chat.title

    if len(words) > 1:
        text = words[1].replace("https://t.me/addstickers/", "")
        to_unblacklist = list(
            {trigger.strip() for trigger in text.split("\n") if trigger.strip()}
        )

        successful = 0
        for trigger in to_unblacklist:
            success = sql.rm_from_stickers(chat_id, trigger.lower())
            if success:
                successful += 1

        if len(to_unblacklist) == 1:
            if successful:
                await send_message(
                    update.effective_message,
                    "Removed <code>{}</code> from blacklist in <b>{}</b>!".format(
                        html.escape(to_unblacklist[0]), html.escape(chat_name)
                    ),
                    parse_mode=ParseMode.HTML,
                )
            else:
                await send_message(
                    update.effective_message, "This sticker is not on the blacklist...!"
                )

        elif successful == len(to_unblacklist):
            await send_message(
                update.effective_message,
                "Sticker <code>{}</code> deleted from blacklist in <b>{}</b>!".format(
                    successful, html.escape(chat_name)
                ),
                parse_mode=ParseMode.HTML,
            )

        elif not successful:
            await send_message(
                update.effective_message,
                "None of these stickers exist, so they cannot be removed.",
                parse_mode=ParseMode.HTML,
            )

        else:
            await send_message(
                update.effective_message,
                "Sticker <code>{}</code> deleted from blacklist. {} did not exist, so it's not deleted.".format(
                    successful, len(to_unblacklist) - successful
                ),
                parse_mode=ParseMode.HTML,
            )
    elif msg.reply_to_message and msg.reply_to_message.sticker:
        trigger = msg.reply_to_message.sticker.set_name
        if trigger is None:
            await send_message(update.effective_message, "Sticker is invalid!")
            return
        success = sql.rm_from_stickers(chat_id, trigger.lower())

        if success:
            await send_message(
                update.effective_message,
                "Sticker <code>{}</code> deleted from blacklist in <b>{}</b>!".format(
                    trigger, chat_name
                ),
                parse_mode=ParseMode.HTML,
            )
        else:
            await send_message(
                update.effective_message,
                "{} not found on blacklisted stickers...!".format(trigger),
            )
    else:
        await send_message(
            update.effective_message,
            "Tell me what stickers you want to add to the blacklist.",
        )


@loggable
@user_admin
async def blacklist_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message
    bot, args = context.bot, context.args
    conn = await connected(bot, update, chat, user.id, need_admin=True)
    if conn:
        chat_id = conn
        chat_obj = await bot.get_chat(conn)
        chat_name = chat_obj.title
    else:
        if update.effective_message.chat.type == "private":
            await send_message(
                update.effective_message, "You can do this command in groups, not PM"
            )
            return ""
        chat_id = update.effective_chat.id
        chat_name = update.effective_message.chat.title

    if args:
        if args[0].lower() in ["off", "nothing", "no"]:
            settypeblacklist = "turn off"
            sql.set_blacklist_strength(chat_id, 0, "0")
        elif args[0].lower() in ["del", "delete"]:
            settypeblacklist = "left, the message will be deleted"
            sql.set_blacklist_strength(chat_id, 1, "0")
        elif args[0].lower() == "warn":
            settypeblacklist = "warned"
            sql.set_blacklist_strength(chat_id, 2, "0")
        elif args[0].lower() == "mute":
            settypeblacklist = "muted"
            sql.set_blacklist_strength(chat_id, 3, "0")
        elif args[0].lower() == "kick":
            settypeblacklist = "kicked"
            sql.set_blacklist_strength(chat_id, 4, "0")
        elif args[0].lower() == "ban":
            settypeblacklist = "banned"
            sql.set_blacklist_strength(chat_id, 5, "0")
        elif args[0].lower() == "tban":
            if len(args) == 1:
                teks = """It looks like you are trying to set a temporary value to blacklist, but has not determined the time; use `/blstickermode tban <timevalue>`.
                                          Examples of time values: 4m = 4 minute, 3h = 3 hours, 6d = 6 days, 5w = 5 weeks."""
                await send_message(update.effective_message, teks, parse_mode=ParseMode.MARKDOWN)
                return ""
            settypeblacklist = "temporary banned for {}".format(args[1])
            sql.set_blacklist_strength(chat_id, 6, str(args[1]))
        elif args[0].lower() == "tmute":
            if len(args) == 1:
                teks = """It looks like you are trying to set a temporary value to blacklist, but has not determined the time; use `/blstickermode tmute <timevalue>`.
                                          Examples of time values: 4m = 4 minute, 3h = 3 hours, 6d = 6 days, 5w = 5 weeks."""
                await send_message(update.effective_message, teks, parse_mode=ParseMode.MARKDOWN)
                return ""
            settypeblacklist = "temporary muted for {}".format(args[1])
            sql.set_blacklist_strength(chat_id, 7, str(args[1]))
        else:
            await send_message(
                update.effective_message,
                "I only understand off/del/warn/ban/kick/mute/tban/tmute!",
            )
            return ""
        if conn:
            text = "Blacklist sticker mode changed, users will be `{}` at *{}*!".format(
                settypeblacklist, chat_name
            )
        else:
            text = "Blacklist sticker mode changed, users will be `{}`!".format(
                settypeblacklist
            )
        await send_message(update.effective_message, text, parse_mode=ParseMode.MARKDOWN)
        return (
            "<b>{}:</b>\n"
            "<b>Admin:</b> {}\n"
            "Changed sticker blacklist mode. users will be {}.".format(
                html.escape(chat.title),
                mention_markdown(user.id, html.escape(user.first_name)),
                settypeblacklist,
            )
        )
    else:
        getmode, getvalue = sql.get_blacklist_setting(chat.id)
        if getmode == 0:
            settypeblacklist = "not active"
        elif getmode == 1:
            settypeblacklist = "delete"
        elif getmode == 2:
            settypeblacklist = "warn"
        elif getmode == 3:
            settypeblacklist = "mute"
        elif getmode == 4:
            settypeblacklist = "kick"
        elif getmode == 5:
            settypeblacklist = "ban"
        elif getmode == 6:
            settypeblacklist = "temporarily banned for {}".format(getvalue)
        elif getmode == 7:
            settypeblacklist = "temporarily muted for {}".format(getvalue)
        else:
            settypeblacklist = "None"

        if conn:
            text = "Blacklist sticker mode is currently set to *{}* in *{}*.".format(
                settypeblacklist, chat_name
            )
        else:
            text = "Blacklist sticker mode is currently set to *{}*.".format(
                settypeblacklist
            )
        await send_message(update.effective_message, text, parse_mode=ParseMode.MARKDOWN)
    return ""


@user_not_admin
async def del_blackliststicker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user
    to_match = message.sticker
    if not to_match or not to_match.set_name:
        return
    getmode, value = sql.get_blacklist_setting(chat.id)

    chat_filters = sql.get_chat_stickers(chat.id)
    for trigger in chat_filters:
        if to_match.set_name.lower() == trigger.lower():
            try:
                if getmode == 0:
                    return
                elif getmode == 1:
                    await message.delete()
                elif getmode == 2:
                    await message.delete()
                    await warn(
                        user,
                        chat,
                        "Using sticker '{}' which in blacklist stickers".format(
                            trigger
                        ),
                        message,
                        user,
                    )
                    return
                elif getmode == 3:
                    await message.delete()
                    await bot.restrict_chat_member(
                        chat.id,
                        user.id,
                        permissions=ChatPermissions(
                            can_send_messages=False,
                            can_send_photos=False,
                            can_send_audios=False,
                            can_send_videos=False,
                            can_send_documents=False,
                            can_send_video_notes=False,
                            can_send_voice_notes=False,
                            can_send_other_messages=False,
                        ),
                    )
                    await bot.send_message(
                        chat.id,
                        "{} muted because using '{}' which in blacklist stickers".format(
                            mention_markdown(user.id, user.first_name), trigger
                        ),
                        parse_mode=ParseMode.MARKDOWN,
                    )
                    return
                elif getmode == 4:
                    await message.delete()
                    res = await chat.unban_member(user.id)
                    if res:
                        await bot.send_message(
                            chat.id,
                            "{} kicked because using '{}' which in blacklist stickers".format(
                                mention_markdown(user.id, user.first_name), trigger
                            ),
                            parse_mode=ParseMode.MARKDOWN,
                        )
                    return
                elif getmode == 5:
                    await message.delete()
                    await chat.ban_member(user.id)
                    await bot.send_message(
                        chat.id,
                        "{} banned because using '{}' which in blacklist stickers".format(
                            mention_markdown(user.id, user.first_name), trigger
                        ),
                        parse_mode=ParseMode.MARKDOWN,
                    )
                    return
                elif getmode == 6:
                    await message.delete()
                    bantime = await extract_time(message, value)
                    await chat.ban_member(user.id, until_date=bantime)
                    await bot.send_message(
                        chat.id,
                        "{} banned for {} because using '{}' which in blacklist stickers".format(
                            mention_markdown(user.id, user.first_name), value, trigger
                        ),
                        parse_mode=ParseMode.MARKDOWN,
                    )
                    return
                elif getmode == 7:
                    await message.delete()
                    mutetime = await extract_time(message, value)
                    await bot.restrict_chat_member(
                        chat.id,
                        user.id,
                        permissions=ChatPermissions(
                            can_send_messages=False,
                            can_send_photos=False,
                            can_send_audios=False,
                            can_send_videos=False,
                            can_send_documents=False,
                            can_send_video_notes=False,
                            can_send_voice_notes=False,
                            can_send_other_messages=False,
                        ),
                        until_date=mutetime,
                    )
                    await bot.send_message(
                        chat.id,
                        "{} muted for {} because using '{}' which in blacklist stickers".format(
                            mention_markdown(user.id, user.first_name), value, trigger
                        ),
                        parse_mode=ParseMode.MARKDOWN,
                    )
                    return
            except BadRequest as excp:
                if excp.message != "Message to delete not found":
                    LOGGER.exception("Error while deleting blacklist message.")
                break


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    blacklisted = sql.num_stickers_chat_filters(chat_id)
    return "There are `{} `blacklisted stickers.".format(blacklisted)


def __stats__():
    return "• {} blacklist stickers, across {} chats.".format(
        sql.num_stickers_filters(), sql.num_stickers_filter_chats()
    )


__help__ = """
Blacklist sticker is used to stop certain stickers. Whenever a sticker is sent, the message will be deleted immediately.
*NOTE:* Blacklist stickers do not affect the group admin
 ❍ /blsticker*:* See current blacklisted sticker
*Only admin:*
 ❍ /addblsticker <sticker link>*:* Add the sticker trigger to the black list. Can be added via reply sticker
 ❍ /unblsticker <sticker link>*:* Remove triggers from blacklist. The same newline logic applies here, so you can delete multiple triggers at once
 ❍ /rmblsticker <sticker link>*:* Same as above
 ❍ /blstickermode <ban/tban/mute/tmute>*:* sets up a default action on what to do if users use blacklisted stickers
Note:
 ❍ <sticker link> can be `https://t.me/addstickers/<sticker>` or just `<sticker>` or reply to the sticker message
"""

__mod_name__ = "Bʟ-Sᴛɪᴄᴋ"

BLACKLIST_STICKER_HANDLER = DisableAbleCommandHandler(
    "blsticker", blackliststicker, admin_ok=True
)

ADDBLACKLIST_STICKER_HANDLER = DisableAbleCommandHandler(
    "addblsticker", add_blackliststicker
)

UNBLACKLIST_STICKER_HANDLER = CommandHandler(
    ["unblsticker", "rmblsticker"], unblackliststicker
)

BLACKLISTMODE_HANDLER = CommandHandler("blstickermode", blacklist_mode)

BLACKLIST_STICKER_DEL_HANDLER = MessageHandler(
    filters.Sticker.ALL & filters.ChatType.GROUPS, del_blackliststicker
)


application.add_handler(BLACKLIST_STICKER_HANDLER)
application.add_handler(ADDBLACKLIST_STICKER_HANDLER)
application.add_handler(UNBLACKLIST_STICKER_HANDLER)
application.add_handler(BLACKLISTMODE_HANDLER)
application.add_handler(BLACKLIST_STICKER_DEL_HANDLER)

__handlers__ = [
    BLACKLIST_STICKER_HANDLER,
    ADDBLACKLIST_STICKER_HANDLER,
    UNBLACKLIST_STICKER_HANDLER,
    BLACKLISTMODE_HANDLER,
    BLACKLIST_STICKER_DEL_HANDLER,
]
