#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import asyncio
import speedtest
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CallbackQueryHandler

from MeowRobot import DEV_USERS, application
from MeowRobot.modules.disable import DisableAbleCommandHandler
from MeowRobot.modules.helper_funcs.chat_status import dev_plus


def convert(speed):
    return round(int(speed) / 1048576, 2)


@dev_plus
async def speedtestxyz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [
        [
            InlineKeyboardButton("ɪᴍᴀɢᴇ", callback_data="speedtest_image"),
            InlineKeyboardButton("ᴛᴇxᴛ", callback_data="speedtest_text"),
        ]
    ]
    await update.effective_message.reply_text(
        "sᴩᴇᴇᴅᴛᴇsᴛ ᴍᴏᴅᴇ", reply_markup=InlineKeyboardMarkup(buttons)
    )


async def speedtestxyz_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if query.from_user.id in DEV_USERS:
        msg = await update.effective_message.edit_text("ʀᴜɴɴɪɴɢ ᴀ sᴩᴇᴇᴅᴛᴇsᴛ...")

        loop = asyncio.get_event_loop()
        try:
            speed = await loop.run_in_executor(None, speedtest.Speedtest)
            await loop.run_in_executor(None, speed.get_best_server)
            await loop.run_in_executor(None, speed.download)
            await loop.run_in_executor(None, speed.upload)
            results = speed.results
        except Exception as e:
            await msg.edit_text(f"Speedtest failed: {e}")
            return

        replymsg = "sᴩᴇᴇᴅᴛᴇsᴛ ʀᴇsᴜʟᴛ"

        if query.data == "speedtest_image":
            speedtest_image = await loop.run_in_executor(None, results.share)
            await update.effective_message.reply_photo(
                photo=speedtest_image, caption=replymsg
            )
            await msg.delete()

        elif query.data == "speedtest_text":
            result_dict = results.dict()
            replymsg += f"\nDownload: `{convert(result_dict['download'])}Mb/s`\nUpload: `{convert(result_dict['upload'])}Mb/s`\nPing: `{result_dict['ping']}`"
            await update.effective_message.edit_text(replymsg, parse_mode=ParseMode.MARKDOWN)
    else:
        await query.answer("You are not allowed to use this.", show_alert=True)


SPEED_TEST_HANDLER = DisableAbleCommandHandler(
    "speedtest", speedtestxyz
)
SPEED_TEST_CALLBACKHANDLER = CallbackQueryHandler(
    speedtestxyz_callback, pattern="speedtest_.*"
)

application.add_handler(SPEED_TEST_HANDLER)
application.add_handler(SPEED_TEST_CALLBACKHANDLER)

__help__ = """
» /speedtest *:* Runs a speedtest and check the server speed.
"""

__mod_name__ = "SᴘᴇᴇᴅTᴇsᴛ"

__command_list__ = ["speedtest"]
__handlers__ = [SPEED_TEST_HANDLER, SPEED_TEST_CALLBACKHANDLER]
