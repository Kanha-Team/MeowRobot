#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import os
import textwrap
import asyncio
from functools import partial

from PIL import Image, ImageDraw, ImageFont
from telegram import Update
from telegram.ext import ContextTypes

from MeowRobot import application
from MeowRobot.modules.disable import DisableAbleCommandHandler


async def mmf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = context.args

    if not message.reply_to_message:
        await message.reply_text("Provide Some Text To Draw!")
        return

    reply_message = message.reply_to_message

    if not (reply_message.photo or (reply_message.sticker and not reply_message.sticker.is_animated)):
        await message.reply_text("Reply to a image/sticker.")
        return

    if not args:
        await message.reply_text("You might want to try `/mmf text` or `/mmf top;bottom`")
        return

    msg = await message.reply_text("Memifying this image! ✊🏻")

    # Download media
    if reply_message.photo:
         file_id = reply_message.photo[-1].file_id
    else:
         file_id = reply_message.sticker.file_id

    file_obj = await context.bot.get_file(file_id)
    file_path = f"temp_mmf_{message.from_user.id}"
    await file_obj.download_to_drive(file_path)

    text = " ".join(args)

    loop = asyncio.get_event_loop()
    try:
        meme_path = await loop.run_in_executor(None, partial(drawText, file_path, text, message.from_user.id))
        with open(meme_path, "rb") as f:
            await message.reply_sticker(sticker=f)
        await msg.delete()
        os.remove(meme_path)
    except Exception as e:
        await msg.edit_text(f"Error: {e}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


def drawText(image_path, text, user_id):
    img = Image.open(image_path)
    i_width, i_height = img.size

    fnt_path = "./MeowRobot/resources/default.ttf"
    if not os.path.exists(fnt_path):
         fnt = "arial.ttf" # Fallback
    else:
         fnt = fnt_path

    m_font = ImageFont.truetype(fnt, int((70 / 640) * i_width))

    if ";" in text:
        upper_text, lower_text = text.split(";", 1)
    else:
        upper_text = text
        lower_text = ""

    draw = ImageDraw.Draw(img)
    current_h, pad = 10, 5

    if upper_text:
        for u_text in textwrap.wrap(upper_text.strip(), width=15):
            lw, th, rw, bh = m_font.getbbox(u_text)
            u_width, u_height = rw - lw, bh - th

            positions = [
                (((i_width - u_width) / 2) - 2, int((current_h / 640) * i_width)),
                (((i_width - u_width) / 2) + 2, int((current_h / 640) * i_width)),
                ((i_width - u_width) / 2, int(((current_h / 640) * i_width)) - 2),
                (((i_width - u_width) / 2), int(((current_h / 640) * i_width)) + 2)
            ]
            for pos in positions:
                 draw.text(pos, text=u_text, font=m_font, fill=(0, 0, 0))

            draw.text(
                xy=((i_width - u_width) / 2, int((current_h / 640) * i_width)),
                text=u_text,
                font=m_font,
                fill=(255, 255, 255),
            )
            current_h += u_height + pad

    if lower_text:
        # Wrap from bottom
        wrapped_lower = textwrap.wrap(lower_text.strip(), width=15)
        current_h_bottom = i_height - int((20 / 640) * i_width)
        for l_text in reversed(wrapped_lower):
            lw, th, rw, bh = m_font.getbbox(l_text)
            l_width, l_height = rw - lw, bh - th

            positions = [
                (((i_width - l_width) / 2) - 2, current_h_bottom - l_height),
                (((i_width - l_width) / 2) + 2, current_h_bottom - l_height),
                ((i_width - l_width) / 2, current_h_bottom - l_height - 2),
                (((i_width - l_width) / 2), current_h_bottom - l_height + 2)
            ]
            for pos in positions:
                draw.text(pos, text=l_text, font=m_font, fill=(0, 0, 0))

            draw.text(
                xy=((i_width - l_width) / 2, current_h_bottom - l_height),
                text=l_text,
                font=m_font,
                fill=(255, 255, 255),
            )
            current_h_bottom -= l_height + pad

    meme_file = f"meme_{user_id}.webp"
    img.save(meme_file, "webp")
    return meme_file


__mod_name__ = "Mᴍғ"
__help__ = """
 ❍ /mmf <text>*:* reply to a photo or sticker to memify it.
 Use `;` to separate top and bottom text.
"""

MMF_HANDLER = DisableAbleCommandHandler("mmf", mmf)
application.add_handler(MMF_HANDLER)

__handlers__ = [MMF_HANDLER]
