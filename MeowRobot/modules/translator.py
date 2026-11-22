#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

from gpytranslate import Translator
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from MeowRobot import application
from MeowRobot.modules.disable import DisableAbleCommandHandler

trans = Translator()


async def totranslate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    reply_msg = message.reply_to_message
    if not reply_msg:
        await message.reply_text(
            "Reply to messages or write messages from other languages for translating into the intended language\n\n"
            "Example: `/tr en-hi` to translate from English to Hindi\n"
            "Or use: `/tr en` for automatic detection and translating it into english.\n"
            "Click here to see [List of available Language Codes](https://te.legra.ph/LANGUAGE-CODES-05-23-2).",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )
        return

    to_translate = reply_msg.caption or reply_msg.text
    if not to_translate:
        return

    try:
        args = message.text.split()[1].lower()
        if "//" in args:
            source = args.split("//")[0]
            dest = args.split("//")[1]
        else:
            source = await trans.detect(to_translate)
            dest = args
    except IndexError:
        source = await trans.detect(to_translate)
        dest = "en"

    translation = await trans(to_translate, sourcelang=source, targetlang=dest)
    reply = (
        f"<b>ᴛʀᴀɴsʟᴀᴛᴇᴅ ғʀᴏᴍ {source} ᴛᴏ {dest}</b> :\n"
        f"<code>{translation.text}</code>"
    )

    await message.reply_text(reply, parse_mode=ParseMode.HTML)


__help__ = """
 ❍ /tr or /tl (language code) as reply to a long message
*Example:* 
 ❍ /tr en*:* translates something to english
 ❍ /tr hi-en*:* translates hindi to english

[ʟᴀɴɢᴜᴀɢᴇ ᴄᴏᴅᴇs](https://te.legra.ph/LANGUAGE-CODES-05-23-2)
"""
__mod_name__ = "Tʀᴀɴsʟᴀᴛᴏʀ"

TRANSLATE_HANDLER = DisableAbleCommandHandler(["tr", "tl"], totranslate)

application.add_handler(TRANSLATE_HANDLER)

__command_list__ = ["tr", "tl"]
__handlers__ = [TRANSLATE_HANDLER]
