#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

from datetime import datetime
from pyrogram import filters
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from pyrogram.enums import ParseMode
from MeowRobot import pbot as app, OWNER_ID, SUPPORT_CHAT

def extract_bug_content(msg: Message) -> str or None:
    return msg.text.split(None, 1)[1] if msg.text and " " in msg.text else None

def escape_md(text: str) -> str:
    return text.replace('[', '\\[').replace(']', '\\]').replace('`', '\\`')

@app.on_message(filters.command("bug"))
async def report_bug(_, msg: Message):
    if msg.chat.type == msg.chat.type.PRIVATE:
        return await msg.reply_text("**ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ɪs ᴏɴʟʏ ғᴏʀ ɢʀᴏᴜᴘs.**")

    bug_description = extract_bug_content(msg)
    if not bug_description:
        return await msg.reply_text("**ɴᴏ ʙᴜɢ ᴅᴇsᴄʀɪᴘᴛɪᴏɴ ᴘʀᴏᴠɪᴅᴇᴅ. ᴘʟᴇᴀsᴇ sᴘᴇᴄɪғʏ ᴛʜᴇ ʙᴜɢ.**")

    user_id = msg.from_user.id
    user_name = escape_md(msg.from_user.first_name)
    mention = f"[{user_name}](tg://user?id={user_id})"

    chat_reference = (
        f"@{msg.chat.username}/`{msg.chat.id}`"
        if msg.chat.username
        else f"ᴘʀɪᴠᴀᴛᴇ ɢʀᴏᴜᴘ/`{msg.chat.id}`"
    )

    current_date = datetime.utcnow().strftime("%d-%m-%Y")

    bug_report = (
        f"**#ʙᴜɢ ʀᴇᴘᴏʀᴛ**\n"
        f"**ʀᴇᴘᴏʀᴛᴇᴅ ʙʏ:** {mention}\n"
        f"**ᴜsᴇʀ ɪᴅ:** `{user_id}`\n"
        f"**ᴄʜᴀᴛ:** {chat_reference}\n"
        f"**ʙᴜɢ ᴅᴇsᴄʀɪᴘᴛɪᴏɴ:** `{escape_md(bug_description)}`\n"
        f"**ᴅᴀᴛᴇ:** `{current_date}`"
    )

    if user_id == OWNER_ID:
        return await msg.reply_text(
            "**ʏᴏᴜ ᴀʀᴇ ᴛʜᴇ ᴏᴡɴᴇʀ ᴏғ ᴛʜᴇ ʙᴏᴛ. ᴘʟᴇᴀsᴇ ᴀᴅᴅʀᴇss ᴛʜᴇ ʙᴜɢ ᴅɪʀᴇᴄᴛʟʏ.**"
        )

    await msg.reply_text(
        "**ʙᴜɢ ʀᴇᴘᴏʀᴛᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!**",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]]
        ),
    )

    # Send report to support group or log
    buttons = [[InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]]
    if msg.chat.username:
        link = f"https://t.me/{msg.chat.username}/{msg.id}"
        buttons.insert(0, [InlineKeyboardButton("ᴠɪᴇᴡ ʙᴜɢ", url=link)])

    try:
        # Using the ID provided in snippet for report destination
        await app.send_message(
            -1002395523584,
            bug_report,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True
        )
    except:
        # Fallback to support chat if ID fails
        if SUPPORT_CHAT:
            try:
                await app.send_message(
                    f"@{SUPPORT_CHAT}",
                    bug_report,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(buttons),
                    disable_web_page_preview=True
                )
            except: pass

__mod_name__ = "Bᴜɢs"
__help__ = """
Report bugs to the developers.

 ❍ /bug <description>*:* Report a bug in the bot.
"""
