#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import html
import re
from typing import Optional

from telegram import (
    CallbackQuery,
    Chat,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    Update,
    User,
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
from telegram.helpers import mention_html

from MeowRobot import TIGERS, WOLVES, application
from MeowRobot.modules.disable import DisableAbleCommandHandler
from MeowRobot.modules.helper_funcs.chat_status import (
    bot_admin,
    can_restrict,
    is_user_admin,
    user_admin,
    user_admin_no_reply,
)
from MeowRobot.modules.helper_funcs.alternate import send_message
from MeowRobot.modules.helper_funcs.extraction import (
    extract_text,
    extract_user,
    extract_user_and_text,
)
from MeowRobot.modules.helper_funcs.filters import CustomFilters
from MeowRobot.modules.helper_funcs.misc import split_message
from MeowRobot.modules.helper_funcs.string_handling import split_quotes
from MeowRobot.modules.log_channel import loggable
from MeowRobot.modules.sql import warns_sql as sql
from MeowRobot.modules.sql.approve_sql import is_approved

WARN_HANDLER_GROUP = 9
CURRENT_WARNING_FILTER_STRING = "<b>Current warning filters in this chat:</b>\n"


async def warn(
    user: User,
    chat: Chat,
    reason: str,
    message: Message,
    warner: User = None,
) -> str:
    if await is_user_admin(chat, user.id):
        return ""

    if user.id in TIGERS:
        if warner:
            await send_message(message, "Tigers cant be warned.")
        else:
            await send_message(
                message,
                "Tiger triggered an auto warn filter!\n I can't warn tigers but they should avoid abusing this.",
            )
        return ""

    if user.id in WOLVES:
        if warner:
            await send_message(message, "Wolf disasters are warn immune.")
        else:
            await send_message(
                message,
                "Wolf Disaster triggered an auto warn filter!\nI can't warn wolves but they should avoid abusing this.",
            )
        return ""

    if warner:
        warner_tag = mention_html(warner.id, warner.first_name)
    else:
        warner_tag = "Automated warn filter."

    limit, soft_warn = sql.get_warn_setting(chat.id)
    num_warns, reasons = sql.warn_user(user.id, chat.id, reason)
    if num_warns >= limit:
        sql.reset_warns(user.id, chat.id)
        if soft_warn:  # punch
            await chat.unban_member(user.id)
            reply = (
                f"<code>❕</code><b>Punch Event</b>\n"
                f"<code> </code><b>•  User:</b> {mention_html(user.id, user.first_name)}\n"
                f"<code> </code><b>•  Count:</b> {limit}"
            )

        else:  # ban
            await chat.ban_member(user.id)
            reply = (
                f"<code>❕</code><b>Ban Event</b>\n"
                f"<code> </code><b>•  User:</b> {mention_html(user.id, user.first_name)}\n"
                f"<code> </code><b>•  Count:</b> {limit}"
            )

        for warn_reason in reasons:
            reply += f"\n - {html.escape(warn_reason)}"

        keyboard = None
        log_reason = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#WARN_BAN\n"
            f"<b>Admin:</b> {warner_tag}\n"
            f"<b>User:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>Reason:</b> {reason}\n"
            f"<b>Counts:</b> <code>{num_warns}/{limit}</code>"
        )

    else:
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "✨ ʀᴇᴍᴏᴠᴇ ✨",
                        callback_data="rm_warn({})".format(user.id),
                    ),
                ],
            ],
        )

        reply = (
            f"<code>❕</code><b>Warn Event</b>\n"
            f"<code> </code><b>•  User:</b> {mention_html(user.id, user.first_name)}\n"
            f"<code> </code><b>•  Count:</b> {num_warns}/{limit}"
        )
        if reason:
            reply += f"\n<code> </code><b>•  Reason:</b> {html.escape(reason)}"

        log_reason = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#WARN\n"
            f"<b>Admin:</b> {warner_tag}\n"
            f"<b>User:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>Reason:</b> {reason}\n"
            f"<b>Counts:</b> <code>{num_warns}/{limit}</code>"
        )

    await send_message(message, reply, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    return log_reason


@user_admin_no_reply
@bot_admin
@loggable
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    query: Optional[CallbackQuery] = update.callback_query
    user: Optional[User] = update.effective_user
    match = re.match(r"rm_warn\((.+?)\)", query.data)
    if match:
        user_id = match.group(1)
        chat: Optional[Chat] = update.effective_chat
        res = sql.remove_warn(user_id, chat.id)
        if res:
            await update.effective_message.edit_text(
                "Warn removed by {}.".format(mention_html(user.id, user.first_name)),
                parse_mode=ParseMode.HTML,
            )
            user_member = await chat.get_member(user_id)
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#UNWARN\n"
                f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                f"<b>User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
            )
        else:
            await update.effective_message.edit_text(
                "User already has no warns.",
                parse_mode=ParseMode.HTML,
            )

    return ""


@user_admin
@can_restrict
@loggable
async def warn_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    args = context.args
    message: Optional[Message] = update.effective_message
    chat: Optional[Chat] = update.effective_chat
    warner: Optional[User] = update.effective_user

    user_id, reason = await extract_user_and_text(message, args)
    if message.text.startswith("/d") and message.reply_to_message:
        await message.reply_to_message.delete()
    if user_id:
        if (
            message.reply_to_message
            and message.reply_to_message.from_user.id == user_id
        ):
            return await warn(
                message.reply_to_message.from_user,
                chat,
                reason,
                message.reply_to_message,
                warner,
            )
        else:
            member = await chat.get_member(user_id)
            return await warn(member.user, chat, reason, message, warner)
    else:
        await send_message(message, "That looks like an invalid User ID to me.")
    return ""


@user_admin
@bot_admin
@loggable
async def reset_warns(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    args = context.args
    message: Optional[Message] = update.effective_message
    chat: Optional[Chat] = update.effective_chat
    user: Optional[User] = update.effective_user

    user_id = await extract_user(message, args)

    if user_id:
        sql.reset_warns(user_id, chat.id)
        await send_message(message, "Warns have been reset!")
        member = await chat.get_member(user_id)
        warned = member.user
        return (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#RESETWARNS\n"
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>User:</b> {mention_html(warned.id, warned.first_name)}"
        )
    else:
        await send_message(message, "No user has been designated!")
    return ""


async def warns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    message: Optional[Message] = update.effective_message
    chat: Optional[Chat] = update.effective_chat
    user_id = await extract_user(message, args) or update.effective_user.id
    result = sql.get_warns(user_id, chat.id)

    if result and result[0] != 0:
        num_warns, reasons = result
        limit, soft_warn = sql.get_warn_setting(chat.id)

        if reasons:
            text = (
                f"This user has {num_warns}/{limit} warns, for the following reasons:"
            )
            for reason in reasons:
                text += f"\n • {reason}"

            msgs = split_message(text)
            for msg in msgs:
                await send_message(update.effective_message, msg)
        else:
            await send_message(
                update.effective_message,
                f"User has {num_warns}/{limit} warns, but no reasons for any of them.",
            )
    else:
        await send_message(update.effective_message, "This user doesn't have any warns!")


@user_admin
async def add_warn_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat: Optional[Chat] = update.effective_chat
    msg: Optional[Message] = update.effective_message

    args = msg.text.split(
        None,
        1,
    )  # use python's maxsplit to separate Cmd, keyword, and reply_text

    if len(args) < 2:
        return

    extracted = split_quotes(args[1])

    if len(extracted) >= 2:
        # set trigger -> lower, so as to avoid adding duplicate filters with different cases
        keyword = extracted[0].lower()
        content = extracted[1]

    else:
        return

    sql.add_warn_filter(chat.id, keyword, content)

    await send_message(update.effective_message, f"Warn handler added for '{keyword}'!")


@user_admin
async def remove_warn_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat: Optional[Chat] = update.effective_chat
    msg: Optional[Message] = update.effective_message

    args = msg.text.split(
        None,
        1,
    )  # use python's maxsplit to separate Cmd, keyword, and reply_text

    if len(args) < 2:
        return

    extracted = split_quotes(args[1])

    if len(extracted) < 1:
        return

    to_remove = extracted[0]

    chat_filters = sql.get_chat_warn_triggers(chat.id)

    if not chat_filters:
        await send_message(msg, "No warning filters are active here!")
        return

    for filt in chat_filters:
        if filt == to_remove:
            sql.remove_warn_filter(chat.id, to_remove)
            await send_message(msg, "Okay, I'll stop warning people for that.")
            return

    await send_message(
        msg,
        "That's not a current warning filter - run /warnlist for all active warning filters.",
    )


async def list_warn_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat: Optional[Chat] = update.effective_chat
    all_handlers = sql.get_chat_warn_triggers(chat.id)

    if not all_handlers:
        await send_message(update.effective_message, "No warning filters are active here!")
        return

    filter_list = CURRENT_WARNING_FILTER_STRING
    for keyword in all_handlers:
        entry = f" - {html.escape(keyword)}\n"
        if len(entry) + len(filter_list) > 4096:
            await send_message(update.effective_message, filter_list, parse_mode=ParseMode.HTML)
            filter_list = entry
        else:
            filter_list += entry

    if filter_list != CURRENT_WARNING_FILTER_STRING:
        await send_message(update.effective_message, filter_list, parse_mode=ParseMode.HTML)


@loggable
async def reply_filter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    chat: Optional[Chat] = update.effective_chat
    message: Optional[Message] = update.effective_message
    user: Optional[User] = update.effective_user

    if not user:  # Ignore channel
        return ""

    if user.id == 777000:
        return ""
    if is_approved(chat.id, user.id):
        return ""
    chat_warn_filters = sql.get_chat_warn_triggers(chat.id)
    to_match = extract_text(message)
    if not to_match:
        return ""

    for keyword in chat_warn_filters:
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, to_match, flags=re.IGNORECASE):
            warn_filter = sql.get_warn_filter(chat.id, keyword)
            return await warn(user, chat, warn_filter.reply, message)
    return ""


@user_admin
@loggable
async def set_warn_limit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    args = context.args
    chat: Optional[Chat] = update.effective_chat
    user: Optional[User] = update.effective_user
    msg: Optional[Message] = update.effective_message

    if args:
        if args[0].isdigit():
            if int(args[0]) < 3:
                await send_message(msg, "The minimum warn limit is 3!")
            else:
                sql.set_warn_limit(chat.id, int(args[0]))
                await send_message(msg, "Updated the warn limit to {}".format(args[0]))
                return (
                    f"<b>{html.escape(chat.title)}:</b>\n"
                    f"#SET_WARN_LIMIT\n"
                    f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                    f"Set the warn limit to <code>{args[0]}</code>"
                )
        else:
            await send_message(msg, "Give me a number as an arg!")
    else:
        limit, soft_warn = sql.get_warn_setting(chat.id)

        await send_message(msg, "The current warn limit is {}".format(limit))
    return ""


@user_admin
async def set_warn_strength(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    chat: Optional[Chat] = update.effective_chat
    user: Optional[User] = update.effective_user
    msg: Optional[Message] = update.effective_message

    if args:
        if args[0].lower() in ("on", "yes"):
            sql.set_warn_strength(chat.id, False)
            await send_message(msg, "Too many warns will now result in a Ban!")
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                f"Has enabled strong warns. Users will be seriously punched.(banned)"
            )

        elif args[0].lower() in ("off", "no"):
            sql.set_warn_strength(chat.id, True)
            await send_message(
                msg,
                "Too many warns will now result in a normal punch! Users will be able to join again after.",
            )
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                f"Has disabled strong punches. I will use normal punch on users."
            )

        else:
            await send_message(msg, "I only understand on/yes/no/off!")
    else:
        limit, soft_warn = sql.get_warn_setting(chat.id)
        if soft_warn:
            await send_message(
                msg,
                "Warns are currently set to *punch* users when they exceed the limits.",
                parse_mode=ParseMode.MARKDOWN,
            )
        else:
            await send_message(
                msg,
                "Warns are currently set to *Ban* users when they exceed the limits.",
                parse_mode=ParseMode.MARKDOWN,
            )
    return ""


def __stats__():
    return (
        f"• {sql.num_warns()} overall warns, across {sql.num_warn_chats()} chats.\n"
        f"• {sql.num_warn_filters()} warn filters, across {sql.num_warn_filter_chats()} chats."
    )


def __import_data__(chat_id, data):
    for user_id, count in data.get("warns", {}).items():
        for x in range(int(count)):
            sql.warn_user(user_id, chat_id)


async def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    num_warn_filters = sql.num_warn_chat_filters(chat_id)
    limit, soft_warn = sql.get_warn_setting(chat_id)
    return (
        f"This chat has `{num_warn_filters}` warn filters. "
        f"It takes `{limit}` warns before the user gets *{'kicked' if soft_warn else 'banned'}*."
    )


__help__ = """
 ❍ `/warns <userhandle>`*:* get a user's number, and reason, of warns.
 ❍ `/warnlist`*:* list of all current warning filters

*Admins only:*
 ❍ `/warn <userhandle>`*:* warn a user. After 3 warns, the user will be banned from the group. Can also be used as a reply.
 ❍ `/dwarn <userhandle>`*:* warn a user and delete the message. After 3 warns, the user will be banned from the group. Can also be used as a reply.
 ❍ `/resetwarn <userhandle>`*:* reset the warns for a user. Can also be used as a reply.
 ❍ `/addwarn <keyword> <reply message>`*:* set a warning filter on a certain keyword. If you want your keyword to \
be a sentence, encompass it with quotes, as such: `/addwarn "very angry" This is an angry user`.
 ❍ `/nowarn <keyword>`*:* stop a warning filter
 ❍ `/warnlimit <num>`*:* set the warning limit
 ❍ `/strongwarn <on/yes/off/no>`*:* If set to on, exceeding the warn limit will result in a ban. Else, will just punch.
"""

__mod_name__ = "Wᴀʀɴs"

WARN_HANDLER = CommandHandler(
    ["warn", "dwarn"], warn_user, filters=filters.ChatType.GROUPS
)
RESET_WARN_HANDLER = CommandHandler(
    ["resetwarn", "resetwarns"],
    reset_warns,
    filters=filters.ChatType.GROUPS,
)
CALLBACK_QUERY_HANDLER = CallbackQueryHandler(
    button, pattern=r"rm_warn"
)
MYWARNS_HANDLER = DisableAbleCommandHandler(
    "warns", warns, filters=filters.ChatType.GROUPS
)
ADD_WARN_HANDLER = CommandHandler(
    "addwarn", add_warn_filter, filters=filters.ChatType.GROUPS
)
RM_WARN_HANDLER = CommandHandler(
    ["nowarn", "stopwarn"],
    remove_warn_filter,
    filters=filters.ChatType.GROUPS,
)
LIST_WARN_HANDLER = DisableAbleCommandHandler(
    ["warnlist", "warnfilters"],
    list_warn_filters,
    filters=filters.ChatType.GROUPS,
    admin_ok=True,
)
WARN_FILTER_HANDLER = MessageHandler(
    CustomFilters.has_text & filters.ChatType.GROUPS,
    reply_filter,
)
WARN_LIMIT_HANDLER = CommandHandler(
    "warnlimit", set_warn_limit, filters=filters.ChatType.GROUPS
)
WARN_STRENGTH_HANDLER = CommandHandler(
    "strongwarn",
    set_warn_strength,
    filters=filters.ChatType.GROUPS,
)

application.add_handler(WARN_HANDLER)
application.add_handler(CALLBACK_QUERY_HANDLER)
application.add_handler(RESET_WARN_HANDLER)
application.add_handler(MYWARNS_HANDLER)
application.add_handler(ADD_WARN_HANDLER)
application.add_handler(RM_WARN_HANDLER)
application.add_handler(LIST_WARN_HANDLER)
application.add_handler(WARN_LIMIT_HANDLER)
application.add_handler(WARN_STRENGTH_HANDLER)
application.add_handler(WARN_FILTER_HANDLER, WARN_HANDLER_GROUP)

__handlers__ = [
    WARN_HANDLER,
    CALLBACK_QUERY_HANDLER,
    RESET_WARN_HANDLER,
    MYWARNS_HANDLER,
    ADD_WARN_HANDLER,
    RM_WARN_HANDLER,
    LIST_WARN_HANDLER,
    WARN_LIMIT_HANDLER,
    WARN_STRENGTH_HANDLER,
    (WARN_FILTER_HANDLER, WARN_HANDLER_GROUP),
]
