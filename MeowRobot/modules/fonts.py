#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import math

from pyrogram import Client, filters
from pyrogram.types import (CallbackQuery, InlineKeyboardButton,
                            InlineKeyboardMarkup, Message)

from MeowRobot import pbot as app
from MeowRobot import pbot
from MeowRobot.utils.fonts import Fonts

# Font styles mapping
FONT_STYLES = {
    "typewriter": Fonts.typewriter,
    "outline": Fonts.outline,
    "serif": Fonts.serief,
    "bold_cool": Fonts.bold_cool,
    "cool": Fonts.cool,
    "small_cap": Fonts.smallcap,
    "script": Fonts.script,
    "script_bolt": Fonts.bold_script,
    "tiny": Fonts.tiny,
    "comic": Fonts.comic,
    "sans": Fonts.san,
    "slant_sans": Fonts.slant_san,
    "slant": Fonts.slant,
    "sim": Fonts.sim,
    "circles": Fonts.circles,
    "circle_dark": Fonts.dark_circle,
    "gothic": Fonts.gothic,
    "gothic_bolt": Fonts.bold_gothic,
    "cloud": Fonts.cloud,
    "happy": Fonts.happy,
    "sad": Fonts.sad,
    "special": Fonts.special,
    "squares": Fonts.square,
    "squares_bold": Fonts.dark_square,
    "andalucia": Fonts.andalucia,
    "manga": Fonts.manga,
    "stinky": Fonts.stinky,
    "bubbles": Fonts.bubbles,
    "underline": Fonts.underline,
    "ladybug": Fonts.ladybug,
    "rays": Fonts.rays,
    "birds": Fonts.birds,
    "slash": Fonts.slash,
    "stop": Fonts.stop,
    "skyline": Fonts.skyline,
    "arrows": Fonts.arrows,
    "qvnes": Fonts.rvnes,
    "strike": Fonts.strike,
    "frozen": Fonts.frozen,
}

PER_PAGE = 6  # 6 fonts per page


# Main /font command
@pbot.on_message(filters.command(["font", "fonts"]))
async def font_command(c: Client, message: Message):
    if message.reply_to_message:
        text = message.reply_to_message.text
    else:
        if len(message.command) < 2:
            return await message.reply("Please provide some text to style.")
        text = message.text.split(None, 1)[1]

    keyboard = get_font_keyboard(0, text)
    await message.reply("Select a font style to apply:", reply_markup=keyboard)


# Generate font selection buttons
def get_font_keyboard(page: int, text: str) -> InlineKeyboardMarkup:
    styles = list(FONT_STYLES.keys())
    total_pages = math.ceil(len(styles) / PER_PAGE)
    page = max(0, min(page, total_pages - 1))
    start = page * PER_PAGE
    end = start + PER_PAGE
    style_buttons = []

    # Use first word or first few chars for preview to avoid encoding issues
    preview_text = text.split()[0] if text.split() else text
    preview_text = preview_text[:8] if len(preview_text) > 8 else preview_text

    # Add style buttons (2 per row)
    for i in range(start, min(end, len(styles)), 2):
        row = []
        for j in range(2):  # 2 buttons per row
            if i + j < len(styles):
                style = styles[i + j]
                # Store only style and page in callback data
                callback_data = f"font+{style}+{page}"

                try:
                    # Create preview with the font style
                    styled_preview = FONT_STYLES[style](preview_text)
                    button_text = f"{styled_preview}"
                except Exception:
                    # Fallback to style name if font conversion fails
                    button_text = style.replace("_", " ").title()

                row.append(InlineKeyboardButton(button_text, callback_data=callback_data))
        if row:  # Only add non-empty rows
            style_buttons.append(row)

    # Add navigation buttons
    nav_buttons = []
    if total_pages > 1:
        # Back and Next buttons in one row
        nav_row = []
        if page > 0:
            nav_row.append(InlineKeyboardButton("⬅️ Back", callback_data=f"font_nav+{page - 1}"))
        if page < total_pages - 1:
            nav_row.append(InlineKeyboardButton("➡️ Next", callback_data=f"font_nav+{page + 1}"))

        if nav_row:
            nav_buttons.append(nav_row)

    # Close button in separate row below navigation
    nav_buttons.append([InlineKeyboardButton("❌ Close", callback_data="font_close")])

    style_buttons.extend(nav_buttons)
    return InlineKeyboardMarkup(style_buttons)


def extract_original_text(query: CallbackQuery) -> str:
    """Helper to extract the original text the user wanted to style."""
    msg = query.message.reply_to_message
    if not msg:
        return ""
    if msg.reply_to_message:
        return msg.reply_to_message.text or ""
    elif len(msg.command) > 1:
        return msg.text.split(None, 1)[1]
    return ""


# Handle font style button clicks
@pbot.on_callback_query(filters.regex("^font\\+"))
async def apply_font_style(c: Client, query: CallbackQuery):
    try:
        parts = query.data.split("+", 2)  # Split into 3 parts: 'font', style, page
        if len(parts) < 3:
            await query.answer("Invalid data format!", show_alert=True)
            return

        style = parts[1]

        text = extract_original_text(query)
        if not text:
            await query.answer("Could not extract original text!", show_alert=True)
            return

        if style in FONT_STYLES:
            styled = FONT_STYLES[style](text)
            await query.edit_message_text(styled, reply_markup=query.message.reply_markup)
        else:
            await query.answer("Unknown style!", show_alert=True)
    except Exception:
        await query.answer("Error applying style!", show_alert=True)


# Handle pagination
@pbot.on_callback_query(filters.regex("^font_nav\\+"))
async def paginate_fonts(c: Client, query: CallbackQuery):
    try:
        parts = query.data.split("+", 1)  # Split into 2 parts: 'font_nav', page
        if len(parts) < 2:
            await query.answer("Invalid navigation data!", show_alert=True)
            return

        page = int(parts[1])

        text = extract_original_text(query)
        if not text:
            await query.answer("Could not extract original text!", show_alert=True)
            return

        keyboard = get_font_keyboard(page, text)
        await query.edit_message_reply_markup(reply_markup=keyboard)
        await query.answer()  # Acknowledge the callback
    except Exception:
        await query.answer("Unable to paginate.", show_alert=True)


# Handle close button
@pbot.on_callback_query(filters.regex("^font_close$"))
async def close_fonts(c: Client, query: CallbackQuery):
    try:
        await query.message.delete()
    except Exception:
        await query.message.edit_text("Font selector closed.")
        await query.answer()

__help__ = """
 ❍ /font <text> *:* ᴄᴏɴᴠᴇʀᴛs sɪᴍᴩʟᴇ ᴛᴇxᴛ ᴛᴏ ʙᴇᴀᴜᴛɪғᴜʟ ᴛᴇxᴛ ʙʏ ᴄʜᴀɴɢɪɴɢ ɪᴛ's ғᴏɴᴛ.
 """

__mod_name__ = "Fᴏɴᴛs"
