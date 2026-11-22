#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import html
import json
import os
from typing import Optional

from telegram import Update
from telegram.constants import ParseMode, ChatType
from telegram.error import BadRequest
from telegram.ext import ContextTypes, CommandHandler
from telegram.helpers import mention_html

from MeowRobot import (
    DEMONS,
    DEV_USERS,
    DRAGONS,
    OWNER_ID,
    SUPPORT_CHAT,
    TIGERS,
    WOLVES,
    application,
)
from MeowRobot.modules.helper_funcs.chat_status import (
    dev_plus,
    sudo_plus,
    whitelist_plus,
)
from MeowRobot.modules.helper_funcs.extraction import extract_user
from MeowRobot.modules.log_channel import gloggable

ELEVATED_USERS_FILE = os.path.join(os.getcwd(), "MeowRobot/elevated_users.json")


def check_user_id(user_id: int, bot) -> Optional[str]:
    if not user_id:
        reply = "That...is a chat! baka ka omae?"
    elif user_id == bot.id:
        reply = "This does not work that way."
    else:
        reply = None
    return reply


@dev_plus
@gloggable
async def addsudo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = await extract_user(message, args)

    reply = check_user_id(user_id, bot)
    if reply:
        await message.reply_text(reply)
        return ""

    try:
        user_member = await bot.get_chat(user_id)
    except BadRequest:
        await message.reply_text("Could not fetch user info.")
        return ""

    with open(ELEVATED_USERS_FILE, "r") as infile:
        data = json.load(infile)

    if user_id in DRAGONS:
        await message.reply_text("This member is already a Dragon Disaster")
        return ""

    if user_id in DEMONS:
        rt = "Requested HA to promote a Demon Disaster to Dragon."
        data["supports"].remove(user_id)
        DEMONS.remove(user_id)
    elif user_id in WOLVES:
        rt = "Requested HA to promote a Wolf Disaster to Dragon."
        data["whitelists"].remove(user_id)
        WOLVES.remove(user_id)
    else:
        rt = ""

    data["sudos"].append(user_id)
    DRAGONS.append(user_id)

    with open(ELEVATED_USERS_FILE, "w") as outfile:
        json.dump(data, outfile, indent=4)

    await update.effective_message.reply_text(
        rt
        + "\nSuccessfully set Disaster level of {} to Dragon!".format(
            user_member.first_name
        )
    )

    log_message = (
        f"#SUDO\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        f"<b>User:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
    )

    if chat.type != ChatType.PRIVATE:
        log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

    return log_message


@sudo_plus
@gloggable
async def addsupport(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = await extract_user(message, args)

    reply = check_user_id(user_id, bot)
    if reply:
        await message.reply_text(reply)
        return ""

    try:
        user_member = await bot.get_chat(user_id)
    except BadRequest:
        await message.reply_text("Could not fetch user info.")
        return ""

    with open(ELEVATED_USERS_FILE, "r") as infile:
        data = json.load(infile)

    if user_id in DRAGONS:
        rt = "Requested HA to demote this Dragon to Demon"
        data["sudos"].remove(user_id)
        DRAGONS.remove(user_id)
    elif user_id in DEMONS:
        await message.reply_text("This user is already a Demon Disaster.")
        return ""
    elif user_id in WOLVES:
        rt = "Requested HA to promote this Wolf Disaster to Demon"
        data["whitelists"].remove(user_id)
        WOLVES.remove(user_id)
    else:
        rt = ""

    data["supports"].append(user_id)
    DEMONS.append(user_id)

    with open(ELEVATED_USERS_FILE, "w") as outfile:
        json.dump(data, outfile, indent=4)

    await update.effective_message.reply_text(
        rt + f"\n{user_member.first_name} was added as a Demon Disaster!"
    )

    log_message = (
        f"#SUPPORT\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        f"<b>User:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
    )

    if chat.type != ChatType.PRIVATE:
        log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

    return log_message


@sudo_plus
@gloggable
async def addwhitelist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = await extract_user(message, args)

    reply = check_user_id(user_id, bot)
    if reply:
        await message.reply_text(reply)
        return ""

    try:
        user_member = await bot.get_chat(user_id)
    except BadRequest:
        await message.reply_text("Could not fetch user info.")
        return ""

    with open(ELEVATED_USERS_FILE, "r") as infile:
        data = json.load(infile)

    if user_id in DRAGONS:
        rt = "This member is a Dragon Disaster, Demoting to Wolf."
        data["sudos"].remove(user_id)
        DRAGONS.remove(user_id)
    elif user_id in DEMONS:
        rt = "This user is already a Demon Disaster, Demoting to Wolf."
        data["supports"].remove(user_id)
        DEMONS.remove(user_id)
    elif user_id in WOLVES:
        await message.reply_text("This user is already a Wolf Disaster.")
        return ""
    else:
        rt = ""

    data["whitelists"].append(user_id)
    WOLVES.append(user_id)

    with open(ELEVATED_USERS_FILE, "w") as outfile:
        json.dump(data, outfile, indent=4)

    await update.effective_message.reply_text(
        rt + f"\nSuccessfully promoted {user_member.first_name} to a Wolf Disaster!"
    )

    log_message = (
        f"#WHITELIST\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))} \n"
        f"<b>User:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
    )

    if chat.type != ChatType.PRIVATE:
        log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

    return log_message


@sudo_plus
@gloggable
async def addtiger(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = await extract_user(message, args)

    reply = check_user_id(user_id, bot)
    if reply:
        await message.reply_text(reply)
        return ""

    try:
        user_member = await bot.get_chat(user_id)
    except BadRequest:
        await message.reply_text("Could not fetch user info.")
        return ""

    with open(ELEVATED_USERS_FILE, "r") as infile:
        data = json.load(infile)

    if user_id in DRAGONS:
        rt = "This member is a Dragon Disaster, Demoting to Tiger."
        data["sudos"].remove(user_id)
        DRAGONS.remove(user_id)
    elif user_id in DEMONS:
        rt = "This user is already a Demon Disaster, Demoting to Tiger."
        data["supports"].remove(user_id)
        DEMONS.remove(user_id)
    elif user_id in WOLVES:
        rt = "This user is already a Wolf Disaster, Demoting to Tiger."
        data["whitelists"].remove(user_id)
        WOLVES.remove(user_id)
    else:
        rt = ""

    if user_id in TIGERS:
        await message.reply_text("This user is already a Tiger.")
        return ""

    data["tigers"].append(user_id)
    TIGERS.append(user_id)

    with open(ELEVATED_USERS_FILE, "w") as outfile:
        json.dump(data, outfile, indent=4)

    await update.effective_message.reply_text(
        rt + f"\nSuccessfully promoted {user_member.first_name} to a Tiger Disaster!"
    )

    log_message = (
        f"#TIGER\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))} \n"
        f"<b>User:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
    )

    if chat.type != ChatType.PRIVATE:
        log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

    return log_message


@dev_plus
@gloggable
async def removesudo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = await extract_user(message, args)

    reply = check_user_id(user_id, bot)
    if reply:
        await message.reply_text(reply)
        return ""

    try:
        user_member = await bot.get_chat(user_id)
    except BadRequest:
        await message.reply_text("Could not fetch user info.")
        return ""

    with open(ELEVATED_USERS_FILE, "r") as infile:
        data = json.load(infile)

    if user_id in DRAGONS:
        await message.reply_text("Requested HA to demote this user to Civilian")
        DRAGONS.remove(user_id)
        data["sudos"].remove(user_id)

        with open(ELEVATED_USERS_FILE, "w") as outfile:
            json.dump(data, outfile, indent=4)

        log_message = (
            f"#UNSUDO\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            f"<b>User:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
        )

        if chat.type != ChatType.PRIVATE:
            log_message = "<b>{}:</b>\n".format(html.escape(chat.title)) + log_message

        return log_message

    else:
        await message.reply_text("This user is not a Dragon Disaster!")
        return ""


@sudo_plus
@gloggable
async def removesupport(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = await extract_user(message, args)

    reply = check_user_id(user_id, bot)
    if reply:
        await message.reply_text(reply)
        return ""

    try:
        user_member = await bot.get_chat(user_id)
    except BadRequest:
        await message.reply_text("Could not fetch user info.")
        return ""

    with open(ELEVATED_USERS_FILE, "r") as infile:
        data = json.load(infile)

    if user_id in DEMONS:
        await message.reply_text("Requested HA to demote this user to Civilian")
        DEMONS.remove(user_id)
        data["supports"].remove(user_id)

        with open(ELEVATED_USERS_FILE, "w") as outfile:
            json.dump(data, outfile, indent=4)

        log_message = (
            f"#UNSUPPORT\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            f"<b>User:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
        )

        if chat.type != ChatType.PRIVATE:
            log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

        return log_message

    else:
        await message.reply_text("This user is not a Demon level Disaster!")
        return ""


@sudo_plus
@gloggable
async def removewhitelist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = await extract_user(message, args)

    reply = check_user_id(user_id, bot)
    if reply:
        await message.reply_text(reply)
        return ""

    try:
        user_member = await bot.get_chat(user_id)
    except BadRequest:
        await message.reply_text("Could not fetch user info.")
        return ""

    with open(ELEVATED_USERS_FILE, "r") as infile:
        data = json.load(infile)

    if user_id in WOLVES:
        await message.reply_text("Demoting to normal user")
        WOLVES.remove(user_id)
        data["whitelists"].remove(user_id)

        with open(ELEVATED_USERS_FILE, "w") as outfile:
            json.dump(data, outfile, indent=4)

        log_message = (
            f"#UNWHITELIST\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            f"<b>User:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
        )

        if chat.type != ChatType.PRIVATE:
            log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

        return log_message
    else:
        await message.reply_text("This user is not a Wolf Disaster!")
        return ""


@sudo_plus
@gloggable
async def removetiger(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = await extract_user(message, args)

    reply = check_user_id(user_id, bot)
    if reply:
        await message.reply_text(reply)
        return ""

    try:
        user_member = await bot.get_chat(user_id)
    except BadRequest:
        await message.reply_text("Could not fetch user info.")
        return ""

    with open(ELEVATED_USERS_FILE, "r") as infile:
        data = json.load(infile)

    if user_id in TIGERS:
        await message.reply_text("Demoting to normal user")
        TIGERS.remove(user_id)
        data["tigers"].remove(user_id)

        with open(ELEVATED_USERS_FILE, "w") as outfile:
            json.dump(data, outfile, indent=4)

        log_message = (
            f"#UNTIGER\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            f"<b>User:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
        )

        if chat.type != ChatType.PRIVATE:
            log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

        return log_message
    else:
        await message.reply_text("This user is not a Tiger Disaster!")
        return ""


@whitelist_plus
async def whitelistlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply = "<b>Known Wolf Disasters 🐺:</b>\n"
    m = await update.effective_message.reply_text(
        "<code>Gathering intel..</code>", parse_mode=ParseMode.HTML
    )
    bot = context.bot
    for each_user in WOLVES:
        user_id = int(each_user)
        try:
            user_chat = await bot.get_chat(user_id)
            reply += f"• {mention_html(user_id, html.escape(user_chat.first_name))}\n"
        except Exception:
            pass
    await m.edit_text(reply, parse_mode=ParseMode.HTML)


@whitelist_plus
async def tigerlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply = "<b>Known Tiger Disasters 🐯:</b>\n"
    m = await update.effective_message.reply_text(
        "<code>Gathering intel..</code>", parse_mode=ParseMode.HTML
    )
    bot = context.bot
    for each_user in TIGERS:
        user_id = int(each_user)
        try:
            user_chat = await bot.get_chat(user_id)
            reply += f"• {mention_html(user_id, html.escape(user_chat.first_name))}\n"
        except Exception:
            pass
    await m.edit_text(reply, parse_mode=ParseMode.HTML)


@whitelist_plus
async def supportlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    m = await update.effective_message.reply_text(
        "<code>Gathering intel..</code>", parse_mode=ParseMode.HTML
    )
    reply = "<b>Known Demon Disasters 👹:</b>\n"
    for each_user in DEMONS:
        user_id = int(each_user)
        try:
            user_chat = await bot.get_chat(user_id)
            reply += f"• {mention_html(user_id, html.escape(user_chat.first_name))}\n"
        except Exception:
            pass
    await m.edit_text(reply, parse_mode=ParseMode.HTML)


@whitelist_plus
async def sudolist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    m = await update.effective_message.reply_text(
        "<code>Gathering intel..</code>", parse_mode=ParseMode.HTML
    )
    true_sudo = list(set(DRAGONS) - set(DEV_USERS))
    reply = "<b>Known Dragon Disasters 🐉:</b>\n"
    for each_user in true_sudo:
        user_id = int(each_user)
        try:
            user_chat = await bot.get_chat(user_id)
            reply += f"• {mention_html(user_id, html.escape(user_chat.first_name))}\n"
        except Exception:
            pass
    await m.edit_text(reply, parse_mode=ParseMode.HTML)


@whitelist_plus
async def devlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    m = await update.effective_message.reply_text(
        "<code>Gathering intel..</code>", parse_mode=ParseMode.HTML
    )
    true_dev = list(set(DEV_USERS) - {OWNER_ID})
    reply = "✨ <b>Dev users list :</b>\n"
    for each_user in true_dev:
        user_id = int(each_user)
        try:
            user_chat = await bot.get_chat(user_id)
            reply += f"• {mention_html(user_id, html.escape(user_chat.first_name))}\n"
        except Exception:
            pass
    await m.edit_text(reply, parse_mode=ParseMode.HTML)


__help__ = f"""
*Devs & Special Access Only:*
 ❍ /sudolist*:* Lists Dragon disasters.
 ❍ /supportlist*:* Lists Demon disasters.
 ❍ /devlist*:* List Hero Association.
 ❍ /addsudo*:* Add Dragon user.
 ❍ /adddemon*:* Add Demon user.
 ❍ /broadcastall*:* Broadcast everywhere.
 ❍ /groups*:* List all bot groups.
 ❍ /leave <ID>*:* Leave a group.
 ❍ /stats*:* Overall bot statistics.
 ❍ /ignore*:* Blacklist a user.
 ❍ /lockdown*:* Toggle bot adding.
 ❍ /speedtest*:* Check bot speed.
 ❍ /load/unload*:* Module control.
 ❍ /reboot/gitpull*:* Service control.
 ❍ /eval/sh/py*:* Execute code/shell.
 ❍ /gban/ungban*:* Global ban management.

`Visit @{SUPPORT_CHAT} for info.`
"""

SUDO_HANDLER = CommandHandler("addsudo", addsudo)
SUPPORT_HANDLER = CommandHandler(("addsupport", "adddemon"), addsupport)
TIGER_HANDLER = CommandHandler(("addtiger"), addtiger)
WHITELIST_HANDLER = CommandHandler(
    ("addwhitelist", "addwolf"), addwhitelist
)
UNSUDO_HANDLER = CommandHandler(("removesudo", "rmsudo"), removesudo)
UNSUPPORT_HANDLER = CommandHandler(
    ("removesupport", "removedemon"), removesupport
)
UNTIGER_HANDLER = CommandHandler(("removetiger"), removetiger)
UNWHITELIST_HANDLER = CommandHandler(
    ("removewhitelist", "removewolf"), removewhitelist
)
WHITELISTLIST_HANDLER = CommandHandler(
    ["whitelistlist", "wolves"], whitelistlist
)
TIGERLIST_HANDLER = CommandHandler(["tigers"], tigerlist)
SUPPORTLIST_HANDLER = CommandHandler("supportlist", supportlist)
SUDOLIST_HANDLER = CommandHandler("sudolist", sudolist)
DEVLIST_HANDLER = CommandHandler("devlist", devlist)

application.add_handler(SUDO_HANDLER)
application.add_handler(SUPPORT_HANDLER)
application.add_handler(TIGER_HANDLER)
application.add_handler(WHITELIST_HANDLER)
application.add_handler(UNSUDO_HANDLER)
application.add_handler(UNSUPPORT_HANDLER)
application.add_handler(UNTIGER_HANDLER)
application.add_handler(UNWHITELIST_HANDLER)
application.add_handler(WHITELISTLIST_HANDLER)
application.add_handler(TIGERLIST_HANDLER)
application.add_handler(SUPPORTLIST_HANDLER)
application.add_handler(SUDOLIST_HANDLER)
application.add_handler(DEVLIST_HANDLER)

__mod_name__ = "Dᴇᴠs"
__handlers__ = [
    SUDO_HANDLER,
    SUPPORT_HANDLER,
    TIGER_HANDLER,
    WHITELIST_HANDLER,
    UNSUDO_HANDLER,
    UNSUPPORT_HANDLER,
    UNTIGER_HANDLER,
    UNWHITELIST_HANDLER,
    WHITELISTLIST_HANDLER,
    TIGERLIST_HANDLER,
    SUPPORTLIST_HANDLER,
    SUDOLIST_HANDLER,
    DEVLIST_HANDLER,
]
