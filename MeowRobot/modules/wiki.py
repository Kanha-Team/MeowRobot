#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import asyncio
import wikipedia
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from wikipedia.exceptions import DisambiguationError, PageError

from MeowRobot import application
from MeowRobot.modules.disable import DisableAbleCommandHandler


async def wiki(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        update.effective_message.reply_to_message
        if update.effective_message.reply_to_message
        else update.effective_message
    )
    res = ""
    if msg == update.effective_message:
        parts = msg.text.split(" ", maxsplit=1)
        if len(parts) < 2:
            return
        search = parts[1]
    else:
        search = msg.text

    loop = asyncio.get_event_loop()
    try:
        res = await loop.run_in_executor(None, wikipedia.summary, search)
    except DisambiguationError as e:
        await update.message.reply_text(
            "Disambiguated pages found! Adjust your query accordingly.\n<i>{}</i>".format(
                e
            ),
            parse_mode=ParseMode.HTML,
        )
    except PageError as e:
        await update.message.reply_text(
            "<code>{}</code>".format(e), parse_mode=ParseMode.HTML
        )
    if res:
        result = f"<b>{search}</b>\n\n"
        result += f"<i>{res}</i>\n"
        result += f"""<a href="https://en.wikipedia.org/wiki/{search.replace(" ", "%20")}">Read more...</a>"""
        if len(result) > 4000:
            with open("result.txt", "w") as f:
                f.write(f"{result}\n\nUwU OwO OmO UmU")
            with open("result.txt", "rb") as f:
                await context.bot.send_document(
                    document=f,
                    filename=f.name,
                    reply_to_message_id=update.message.message_id,
                    chat_id=update.effective_chat.id,
                )
        else:
            await update.message.reply_text(
                result, parse_mode=ParseMode.HTML, disable_web_page_preview=True
            )


WIKI_HANDLER = DisableAbleCommandHandler("wiki", wiki)

application.add_handler(WIKI_HANDLER)

__help__ = """
» /wiki (text) *:* Searchs about the given text on wikipedia.
"""
__mod_name__ = "Wɪᴋɪ"
