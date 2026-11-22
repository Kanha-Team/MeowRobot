#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

from functools import wraps
from telegram import Update
from telegram.constants import ChatAction
from telegram.error import BadRequest
from telegram.ext import ContextTypes


async def send_message(message, text, *args, **kwargs):
    try:
        return await message.reply_text(text, *args, **kwargs)
    except BadRequest as err:
        if err.message in ("Reply message not found", "Message to be replied not found"):
            kwargs.pop("quote", None)
            kwargs.pop("reply_to_message_id", None)
            return await message.reply_text(text, quote=False, *args, **kwargs)
        raise


def typing_action(func):
    """Sends typing action while processing func command."""

    @wraps(func)
    async def command_func(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if update.effective_chat:
            await context.bot.send_chat_action(
                chat_id=update.effective_chat.id, action=ChatAction.TYPING
            )
        return await func(update, context, *args, **kwargs)

    return command_func
