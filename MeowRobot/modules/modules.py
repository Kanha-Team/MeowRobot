#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import importlib
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CommandHandler

from MeowRobot import application, telethn
from MeowRobot.__main__ import (
    CHAT_SETTINGS,
    DATA_EXPORT,
    DATA_IMPORT,
    HELPABLE,
    IMPORTED,
    MIGRATEABLE,
    STATS,
    USER_INFO,
    USER_SETTINGS,
)
from MeowRobot.modules.helper_funcs.chat_status import dev_plus, sudo_plus


@dev_plus
async def load(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if len(message.text.split()) < 2:
        await message.reply_text("Please specify a module name to load.")
        return

    text = message.text.split(" ", 1)[1]
    load_messasge = await message.reply_text(
        f"Attempting to load module : <b>{text}</b>", parse_mode=ParseMode.HTML
    )

    try:
        imported_module = importlib.import_module("MeowRobot.modules." + text)
    except:
        await load_messasge.edit_text("Does that module even exist?")
        return

    if not hasattr(imported_module, "__mod_name__"):
        imported_module.__mod_name__ = imported_module.__name__

    if imported_module.__mod_name__.lower() not in IMPORTED:
        IMPORTED[imported_module.__mod_name__.lower()] = imported_module
    else:
        await load_messasge.edit_text("Module already loaded.")
        return

    if "__handlers__" in dir(imported_module):
        handlers = imported_module.__handlers__
        for handler in handlers:
            if not isinstance(handler, tuple):
                application.add_handler(handler)
            else:
                if len(handler) == 2 and callable(handler[0]):
                    callback, telethon_event = handler
                    telethn.add_event_handler(callback, telethon_event)
                else:
                    handler_obj, priority = handler
                    application.add_handler(handler_obj, priority)
    else:
        IMPORTED.pop(imported_module.__mod_name__.lower())
        await load_messasge.edit_text("The module cannot be loaded.")
        return

    if hasattr(imported_module, "__help__") and imported_module.__help__:
        HELPABLE[imported_module.__mod_name__.lower()] = imported_module

    if hasattr(imported_module, "__migrate__"):
        MIGRATEABLE.append(imported_module)

    if hasattr(imported_module, "__stats__"):
        STATS.append(imported_module)

    if hasattr(imported_module, "__user_info__"):
        USER_INFO.append(imported_module)

    if hasattr(imported_module, "__import_data__"):
        DATA_IMPORT.append(imported_module)

    if hasattr(imported_module, "__export_data__"):
        DATA_EXPORT.append(imported_module)

    if hasattr(imported_module, "__chat_settings__"):
        CHAT_SETTINGS[imported_module.__mod_name__.lower()] = imported_module

    if hasattr(imported_module, "__user_settings__"):
        USER_SETTINGS[imported_module.__mod_name__.lower()] = imported_module

    await load_messasge.edit_text(
        "Successfully loaded module : <b>{}</b>".format(text), parse_mode=ParseMode.HTML
    )


@dev_plus
async def unload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if len(message.text.split()) < 2:
        await message.reply_text("Please specify a module name to unload.")
        return

    text = message.text.split(" ", 1)[1]
    unload_messasge = await message.reply_text(
        f"Attempting to unload module : <b>{text}</b>", parse_mode=ParseMode.HTML
    )

    try:
        imported_module = importlib.import_module("MeowRobot.modules." + text)
    except:
        await unload_messasge.edit_text("Does that module even exist?")
        return

    if not hasattr(imported_module, "__mod_name__"):
        imported_module.__mod_name__ = imported_module.__name__

    if imported_module.__mod_name__.lower() in IMPORTED:
        IMPORTED.pop(imported_module.__mod_name__.lower())
    else:
        await unload_messasge.edit_text("Can't unload something that isn't loaded.")
        return

    if "__handlers__" in dir(imported_module):
        handlers = imported_module.__handlers__
        for handler in handlers:
            if isinstance(handler, bool):
                await unload_messasge.edit_text("This module can't be unloaded!")
                return
            elif not isinstance(handler, tuple):
                application.remove_handler(handler)
            else:
                if len(handler) == 2 and callable(handler[0]):
                    callback, telethon_event = handler
                    telethn.remove_event_handler(callback, telethon_event)
                else:
                    handler_obj, priority = handler
                    application.remove_handler(handler_obj, priority)
    else:
        await unload_messasge.edit_text("The module cannot be unloaded.")
        return

    if hasattr(imported_module, "__help__") and imported_module.__help__:
        HELPABLE.pop(imported_module.__mod_name__.lower(), None)

    if hasattr(imported_module, "__migrate__") and imported_module in MIGRATEABLE:
        MIGRATEABLE.remove(imported_module)

    if hasattr(imported_module, "__stats__") and imported_module in STATS:
        STATS.remove(imported_module)

    if hasattr(imported_module, "__user_info__") and imported_module in USER_INFO:
        USER_INFO.remove(imported_module)

    if hasattr(imported_module, "__import_data__") and imported_module in DATA_IMPORT:
        DATA_IMPORT.remove(imported_module)

    if hasattr(imported_module, "__export_data__") and imported_module in DATA_EXPORT:
        DATA_EXPORT.remove(imported_module)

    CHAT_SETTINGS.pop(imported_module.__mod_name__.lower(), None)
    USER_SETTINGS.pop(imported_module.__mod_name__.lower(), None)

    await unload_messasge.edit_text(
        f"Successfully unloaded module : <b>{text}</b>", parse_mode=ParseMode.HTML
    )


@sudo_plus
async def listmodules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    module_list = []

    for helpable_module in HELPABLE:
        helpable_module_info = IMPORTED.get(helpable_module)
        if not helpable_module_info:
            continue
        file_name = helpable_module_info.__name__.rsplit("MeowRobot.modules.", 1)[1]
        mod_name = helpable_module_info.__mod_name__
        module_list.append(f"- <code>{mod_name} ({file_name})</code>\n")

    module_list_text = "Following modules are loaded : \n\n" + "".join(module_list)
    await message.reply_text(module_list_text, parse_mode=ParseMode.HTML)


LOAD_HANDLER = CommandHandler("load", load)
UNLOAD_HANDLER = CommandHandler("unload", unload)
LISTMODULES_HANDLER = CommandHandler("listmodules", listmodules)

application.add_handler(LOAD_HANDLER)
application.add_handler(UNLOAD_HANDLER)
application.add_handler(LISTMODULES_HANDLER)

__mod_name__ = "Modules"
