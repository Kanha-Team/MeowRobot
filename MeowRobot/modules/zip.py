#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import os
import time
import zipfile
import asyncio
from datetime import datetime

from telethon import types, events
from telethon.tl import functions
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from telethon.tl.types import DocumentAttributeVideo

from MeowRobot import TEMP_DOWNLOAD_DIRECTORY
from MeowRobot import telethn as client


async def is_register_admin(chat, user):
    if isinstance(chat, (types.InputPeerChannel, types.InputChannel)):
        try:
            res = await client(functions.channels.GetParticipantRequest(chat, user))
            return isinstance(
                res.participant,
                (types.ChannelParticipantAdmin, types.ChannelParticipantCreator),
            )
        except:
             return False
    if isinstance(chat, types.InputPeerChat):
        try:
            ui = await client.get_peer_id(user)
            res = await client(functions.messages.GetFullChatRequest(chat.chat_id))
            ps = res.full_chat.participants.participants
            return isinstance(
                next((p for p in ps if p.user_id == ui), None),
                (types.ChatParticipantAdmin, types.ChatParticipantCreator),
            )
        except:
             return False
    return None


@client.on(events.NewMessage(pattern="^[!/]zip"))
async def zip_handler(event):
    if event.fwd_from:
        return

    if not event.is_reply:
        await event.reply("Reply to a file to compress it.")
        return
    if event.is_group:
        if not (await is_register_admin(event.input_chat, event.sender_id)):
            await event.reply(
                "Hey, you are not admin. You can't use this command, But you can use in my PM 🙂"
            )
            return

    mone = await event.reply("⏳️ Please wait...")
    if not os.path.isdir(TEMP_DOWNLOAD_DIRECTORY):
        os.makedirs(TEMP_DOWNLOAD_DIRECTORY)

    reply_message = await event.get_reply_message()
    if not reply_message.media:
         await mone.edit("Reply to a file.")
         return

    try:
        downloaded_file_name = await event.client.download_media(
            reply_message, TEMP_DOWNLOAD_DIRECTORY
        )
        if not downloaded_file_name:
             await mone.edit("Failed to download file.")
             return

        zip_file_name = downloaded_file_name + ".zip"
        with zipfile.ZipFile(zip_file_name, "w", zipfile.ZIP_DEFLATED) as zip_h:
             zip_h.write(downloaded_file_name, os.path.basename(downloaded_file_name))

        await event.client.send_file(
            event.chat_id,
            zip_file_name,
            force_document=True,
            allow_cache=False,
            reply_to=event.message.id,
        )
        await mone.delete()
        os.remove(downloaded_file_name)
        os.remove(zip_file_name)
    except Exception as e:
        await mone.edit(f"Error: {e}")


@client.on(events.NewMessage(pattern="^[!/]unzip"))
async def unzip_handler(event):
    if event.fwd_from:
        return

    if not event.is_reply:
        await event.reply("Reply to a zip file.")
        return
    if event.is_group:
        if not (await is_register_admin(event.input_chat, event.sender_id)):
            await event.reply(
                "Hey, You are not admin. You can't use this command, But you can use in my PM 🙂"
            )
            return

    mone = await event.reply("Processing...")
    if not os.path.isdir(TEMP_DOWNLOAD_DIRECTORY):
        os.makedirs(TEMP_DOWNLOAD_DIRECTORY)

    reply_message = await event.get_reply_message()
    if not (reply_message.media and hasattr(reply_message.media, 'document') and reply_message.media.document.mime_type == 'application/zip'):
         await mone.edit("Reply to a valid zip file.")
         return

    extracted_path = os.path.join(TEMP_DOWNLOAD_DIRECTORY, "extracted_" + str(event.sender_id))
    if not os.path.isdir(extracted_path):
        os.makedirs(extracted_path)

    try:
        downloaded_file_name = await client.download_media(
            reply_message, TEMP_DOWNLOAD_DIRECTORY
        )

        with zipfile.ZipFile(downloaded_file_name, "r") as zip_ref:
            zip_ref.extractall(extracted_path)

        await event.reply("Unzipping now 😌")

        for root, dirs, files in os.walk(extracted_path):
            for file in files:
                file_path = os.path.join(root, file)
                await client.send_file(event.chat_id, file_path, reply_to=event.message.id)
                os.remove(file_path)

        await mone.delete()
        os.remove(downloaded_file_name)
        import shutil
        shutil.rmtree(extracted_path)
    except Exception as e:
        await mone.edit(f"Error: {e}")


__mod_name__ = "Zɪᴘᴘᴇʀ"
__help__ = """
Hey I can convert files here.

 ❍ /zip*:* reply to a telegram file to compress it in .zip format
 ❍ /unzip*:* reply to a telegram file to decompress it from the .zip format
"""
