#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatType, ParseMode
from telegram.ext import ContextTypes, CommandHandler, filters

from MeowRobot import application
from MeowRobot.modules.disable import DisableAbleCommandHandler
from MeowRobot.modules.helper_funcs.chat_status import user_admin

MARKDOWN_HELP = """
Markdown is a very powerful formatting tool supported by telegram. The bot has some enhancements, to make sure that \
saved messages are correctly parsed, and to allow you to create buttons.

• <code>_italic_</code>: wrapping text with '_' will produce italic text
• <code>*bold*</code>: wrapping text with '*' will produce bold text
• <code>`code`</code>: wrapping text with '`' will produce monospaced text, also known as 'code'
• <code>[sometext](someURL)</code>: this will create a link - the message will just show <code>sometext</code>, \
and tapping on it will open the page at <code>someURL</code>.
<b>Example:</b><code>[test](example.com)</code>

• <code>[buttontext](buttonurl:someURL)</code>: this is a special enhancement to allow users to have telegram \
buttons in their markdown. <code>buttontext</code> will be what is displayed on the button, and <code>someurl</code> \
will be the url which is opened.
<b>Example:</b> <code>[This is a button](buttonurl:example.com)</code>

If you want multiple buttons on the same line, use :same, as such:
<code>[one](buttonurl://example.com)
[two](buttonurl://google.com:same)</code>
This will create two buttons on a single line, instead of one button per line.

Keep in mind that your message <b>MUST</b> contain some text other than just a button!
"""


@user_admin
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg_parts = update.effective_message.text.split(None, 1)
    message = update.effective_message

    if len(msg_parts) < 2:
        return

    if message.reply_to_message:
        await message.reply_to_message.reply_text(
            msg_parts[1], parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True
        )
    else:
        await message.reply_text(
            msg_parts[1], quote=False, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True
        )
    await message.delete()


async def markdown_help_sender(update: Update):
    await update.effective_message.reply_text(MARKDOWN_HELP, parse_mode=ParseMode.HTML)
    await update.effective_message.reply_text(
        "Try forwarding the following message to me, and you'll see, and Use #test!"
    )
    await update.effective_message.reply_text(
        "/save test This is a markdown test. _italics_, *bold*, code, "
        "[URL](example.com) [button](buttonurl:github.com) "
        "[button2](buttonurl://google.com:same)"
    )


async def markdown_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != ChatType.PRIVATE:
        await update.effective_message.reply_text(
            "Contact me in pm",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "ϻᴧꝛᴋᴅσᴡη ʜєʟᴘ",
                            url=f"t.me/{context.bot.username}?start=markdownhelp",
                        )
                    ]
                ]
            ),
        )
        return
    await markdown_help_sender(update)


__help__ = """
*Available commands:*
*Markdown:*
 ❍ /markdownhelp*:* quick summary of how markdown works in telegram - can only be called in private chats
*React:*
 ❍ /react*:* Reacts with a random reaction 
*Urban Dictonary:*
 ❍ /ud <word>*:* Type the word or expression you want to search use
*Wikipedia:*
 ❍ /wiki <query>*:* wikipedia your query
"""

ECHO_HANDLER = DisableAbleCommandHandler(
    "echo", echo, filters=filters.ChatType.GROUPS
)
MD_HELP_HANDLER = CommandHandler("markdownhelp", markdown_help)

application.add_handler(ECHO_HANDLER)
application.add_handler(MD_HELP_HANDLER)

__mod_name__ = "Exᴛʀᴀs"
__command_list__ = ["id", "echo"]
__handlers__ = [
    ECHO_HANDLER,
    MD_HELP_HANDLER,
]
