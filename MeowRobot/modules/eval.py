#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import io
import os
import textwrap
import traceback
from contextlib import redirect_stdout

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CommandHandler

from MeowRobot import LOGGER, application
from MeowRobot.modules.helper_funcs.chat_status import dev_plus

namespaces = {}


def namespace_of(chat, update, bot):
    if chat not in namespaces:
        namespaces[chat] = {
            "__builtins__": globals()["__builtins__"],
            "bot": bot,
            "effective_message": update.effective_message,
            "effective_user": update.effective_user,
            "effective_chat": update.effective_chat,
            "update": update,
        }

    return namespaces[chat]


def log_input(update: Update):
    user = update.effective_user.id
    chat = update.effective_chat.id
    LOGGER.info(f"IN: {update.effective_message.text} (user={user}, chat={chat})")


async def send(msg, bot, update: Update):
    if len(str(msg)) > 2000:
        with io.BytesIO(str.encode(msg)) as out_file:
            out_file.name = "output.txt"
            await bot.send_document(chat_id=update.effective_chat.id, document=out_file)
    else:
        LOGGER.info(f"OUT: '{msg}'")
        await bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"`{msg}`",
            parse_mode=ParseMode.MARKDOWN,
        )


@dev_plus
async def evaluate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    result = await do(eval, bot, update)
    await send(result, bot, update)


@dev_plus
async def execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    result = await do(exec, bot, update)
    await send(result, bot, update)


def cleanup_code(code):
    if code.startswith("```") and code.endswith("```"):
        return "\n".join(code.split("\n")[1:-1])
    return code.strip("` \n")


async def do(func, bot, update: Update):
    log_input(update)
    content = update.message.text.split(" ", 1)[-1]
    body = cleanup_code(content)
    env = namespace_of(update.message.chat_id, update, bot)

    stdout = io.StringIO()
    to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

    try:
        exec(to_compile, env)
    except Exception as e:
        return f"{e.__class__.__name__}: {e}"

    func = env["func"]

    try:
        with redirect_stdout(stdout):
            func_return = await func()
    except Exception:
        value = stdout.getvalue()
        return f"{value}{traceback.format_exc()}"
    else:
        value = stdout.getvalue()
        result = None
        if func_return is None:
            if value:
                result = f"{value}"
            else:
                try:
                    result = f"{repr(eval(body, env))}"
                except:
                    pass
        else:
            result = f"{value}{func_return}"
        if result:
            return result
        return "No result"


@dev_plus
async def clear_locals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    log_input(update)
    if update.message.chat_id in namespaces:
        del namespaces[update.message.chat_id]
    await send("Cleared locals.", bot, update)


EVAL_HANDLER = CommandHandler(("e", "ev", "eva", "eval"), evaluate)
EXEC_HANDLER = CommandHandler(("x", "ex", "exe", "exec", "py"), execute)
CLEAR_HANDLER = CommandHandler("clearlocals", clear_locals)

application.add_handler(EVAL_HANDLER)
application.add_handler(EXEC_HANDLER)
application.add_handler(CLEAR_HANDLER)

__mod_name__ = "Eᴠᴀʟ"
__handlers__ = [EVAL_HANDLER, EXEC_HANDLER, CLEAR_HANDLER]
