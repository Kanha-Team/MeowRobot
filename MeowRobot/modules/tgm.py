#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team >.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import asyncio
import os
import requests
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from MeowRobot import pbot as bot

ANUBOX_UPLOAD_URL = "https://anubox.vercel.app/upload"


def upload_anubox(file_path: str):
    try:
        with open(file_path, "rb") as f:
            r = requests.post(
                ANUBOX_UPLOAD_URL,
                files={"file": f},
                timeout=120,
            )
        if not r.text.strip():
            return False, "AnuBox: empty response"

        data = r.json()
        if r.status_code != 200:
            return False, f"AnuBox: {r.status_code} - {str(data)[:100]}"

        if isinstance(data, dict):
            link = data.get("url") or data.get("data", "")
            if link and link.startswith("http"):
                return True, link
            return False, f"AnuBox: {str(data)[:100]}"

        return False, f"AnuBox: unexpected response - {str(data)[:100]}"
    except Exception as e:
        return False, f"AnuBox error: {e}"


@bot.on_message(filters.command(["tgm", "tm", "telegraph"]))
async def telegraph_upload(_, message):
    reply = message.reply_to_message

    if not reply or not reply.media:
        return await message.reply("❌ Reply to a media file (photo, video, document, animation, sticker).")

    # File size check
    file_size = 0
    if reply.photo:
        file_size = reply.photo.file_size
    elif reply.video:
        file_size = reply.video.file_size
    elif reply.document:
        file_size = reply.document.file_size
    elif reply.animation:
        file_size = reply.animation.file_size
    elif reply.sticker:
        file_size = reply.sticker.file_size

    if file_size > 100 * 1024 * 1024:
        return await message.reply("❌ File must be under 100MB.")

    msg = await message.reply("📥 Downloading media...")

    try:
        path = await reply.download()
        await msg.edit("📤 Uploading to AnuBox...")

        success, result = await asyncio.to_thread(upload_anubox, path)

        if success:
            await msg.edit(
                f"✅ **Uploaded Successfully to AnuBox**\n\n🔗 `{result}`",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🌐 Open Link", url=result)]]
                ),
                disable_web_page_preview=False,
            )
        else:
            await msg.edit(f"❌ Upload failed: {result}")

    except Exception as e:
        await msg.edit(f"❌ Error:\n{e}")

    finally:
        if "path" in locals() and os.path.exists(path):
            os.remove(path)


__mod_name__ = "Tɢ-M"

__help__ = """
*Telegraph / Media Uploader (Powered by AnuBox) 🌐*

Reply to any media file to upload it and get a permanent direct link.

*Commands:*
 ❍ /tgm*:* Reply to media to get a direct permanent link.
 ❍ /tm*:* Same as /tgm.

*Supports:*
• Photo
• Video
• Document
• Animation
• Sticker

*Max Size:* 100MB
"""
