#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import os
import asyncio
try:
    import cv2
except ImportError:
    cv2 = None
from PIL import Image
from telethon import events
from telethon.tl.types import DocumentAttributeFilename

from MeowRobot import telethn as tbot
from MeowRobot import TEMP_DOWNLOAD_DIRECTORY


@tbot.on(events.NewMessage(pattern="^[!/]tiny ?(.*)"))
async def tiny_handler(event):
    reply = await event.get_reply_message()
    if not (reply and reply.media):
        await event.reply("`Please reply to a sticker/image`")
        return

    kontol = await event.reply("`Processing tiny...`")
    ik = await tbot.download_media(reply, TEMP_DOWNLOAD_DIRECTORY)

    if not ik:
         await kontol.edit("`Failed to download media.`")
         return

    im1 = Image.open("MeowRobot/resources/blank_background.png")

    file_to_send = None

    try:
        if ik.endswith(".tgs"):
            # Lottie conversion is complex, skipping re-implementation but keeping logic
            await kontol.edit("`Animated stickers are not supported for tiny yet in this version.`")
            os.remove(ik)
            return

        elif ik.endswith((".gif", ".mp4")):
            iik = cv2.VideoCapture(ik)
            success, frame = iik.read()
            if success:
                cv2.imwrite("i.png", frame)
                fil = "i.png"
                im = Image.open(fil)
                z, d = im.size
                if z == d:
                    xxx, yyy = 200, 200
                else:
                    t = z + d
                    a = z / t
                    b = d / t
                    aa = (a * 100) - 50
                    bb = (b * 100) - 50
                    xxx = 200 + 5 * aa
                    yyy = 200 + 5 * bb
                k = im.resize((int(xxx), int(yyy)))
                k.save("k.png", format="PNG", optimize=True)
                im2 = Image.open("k.png")
                back_im = im1.copy()
                back_im.paste(im2, (150, 0))
                back_im.save("o.webp", "WEBP", quality=95)
                file_to_send = "o.webp"
                os.remove(fil)
                os.remove("k.png")
            iik.release()
        else:
            im = Image.open(ik)
            z, d = im.size
            if z == d:
                xxx, yyy = 200, 200
            else:
                t = z + d
                a = z / t
                b = d / t
                aa = (a * 100) - 50
                bb = (b * 100) - 50
                xxx = 200 + 5 * aa
                yyy = 200 + 5 * bb
            k = im.resize((int(xxx), int(yyy)))
            k.save("k.png", format="PNG", optimize=True)
            im2 = Image.open("k.png")
            back_im = im1.copy()
            back_im.paste(im2, (150, 0))
            back_im.save("o.webp", "WEBP", quality=95)
            file_to_send = "o.webp"
            os.remove("k.png")

        if file_to_send:
            await tbot.send_file(event.chat_id, file_to_send, reply_to=reply.id)
            os.remove(file_to_send)

        await kontol.delete()
    except Exception as e:
        await kontol.edit(f"Error: {e}")
    finally:
        if os.path.exists(ik):
            os.remove(ik)


__mod_name__ = "Tɪɴʏ"
__help__ = """
❍ /tiny*:* reply a sticker and see magic
"""
