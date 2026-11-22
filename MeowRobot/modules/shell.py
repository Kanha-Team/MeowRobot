#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import asyncio
import subprocess

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CommandHandler

from MeowRobot import LOGGER, application
from MeowRobot.modules.helper_funcs.chat_status import dev_plus


@dev_plus
async def shell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    cmd = message.text.split(" ", 1)
    if len(cmd) == 1:
        await message.reply_text("No command to execute was given.")
        return
    cmd = cmd[1]

    loop = asyncio.get_event_loop()
    process = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()

    reply = ""
    stderr_str = stderr.decode()
    stdout_str = stdout.decode()
    if stdout_str:
        reply += f"*Stdout*\n`{stdout_str}`\n"
        LOGGER.info(f"Shell - {cmd} - {stdout_str}")
    if stderr_str:
        reply += f"*Stderr*\n`{stderr_str}`\n"
        LOGGER.error(f"Shell - {cmd} - {stderr_str}")

    if not reply:
        await message.reply_text("No output.")
        return

    if len(reply) > 3000:
        with open("shell_output.txt", "w") as file:
            file.write(reply)
        with open("shell_output.txt", "rb") as doc:
            await context.bot.send_document(
                document=doc,
                filename=doc.name,
                reply_to_message_id=message.message_id,
                chat_id=message.chat_id,
            )
    else:
        await message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)


SHELL_HANDLER = CommandHandler(["sh"], shell)

application.add_handler(SHELL_HANDLER)

__mod_name__ = "Shell"

__command_list__ = ["sh"]
__handlers__ = [SHELL_HANDLER]
