#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

from io import BytesIO
from pyrogram import Client, filters
from pyrogram.types import Message
from httpx import AsyncClient, Timeout

from MeowRobot import pbot as app

# -----------------------------------------------------------------
try:
    fetch = AsyncClient(
        http2=True,
        verify=False,
        headers={
            "Accept-Language": "id-ID",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
                           AppleWebKit/537.36 (KHTML, like Gecko) \
                           Chrome/107.0.0.0 Safari/537.36 Edge/107.0.1418.42",
        },
        timeout=Timeout(20),
    )
except Exception:
    fetch = AsyncClient(
        http2=False,
        verify=False,
        headers={
            "Accept-Language": "id-ID",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
                           AppleWebKit/537.36 (KHTML, like Gecko) \
                           Chrome/107.0.0.0 Safari/537.36 Edge/107.0.1418.42",
        },
        timeout=Timeout(20),
    )

class QuotlyException(Exception):
    pass

async def get_message_sender_id(ctx: Message):
    if ctx.forward_date:
        if ctx.forward_sender_name:
            return 1
        elif ctx.forward_from:
            return ctx.forward_from.id
        elif ctx.forward_from_chat:
            return ctx.forward_from_chat.id
        else:
            return 1
    elif ctx.from_user:
        return ctx.from_user.id
    elif ctx.sender_chat:
        return ctx.sender_chat.id
    else:
        return 1

async def get_message_sender_name(ctx: Message):
    if ctx.forward_date:
        if ctx.forward_sender_name:
            return ctx.forward_sender_name
        elif ctx.forward_from:
            return (
                f"{ctx.forward_from.first_name} {ctx.forward_from.last_name}"
                if ctx.forward_from.last_name
                else ctx.forward_from.first_name
            )
        elif ctx.forward_from_chat:
            return ctx.forward_from_chat.title
        else:
            return ""
    elif ctx.from_user:
        if ctx.from_user.last_name:
            return f"{ctx.from_user.first_name} {ctx.from_user.last_name}"
        else:
            return ctx.from_user.first_name
    elif ctx.sender_chat:
        return ctx.sender_chat.title
    else:
        return ""

async def get_message_sender_username(ctx: Message):
    if ctx.forward_date:
        if (not ctx.forward_sender_name and not ctx.forward_from and
            ctx.forward_from_chat and ctx.forward_from_chat.username):
            return ctx.forward_from_chat.username
        elif (not ctx.forward_sender_name and not ctx.forward_from and ctx.forward_from_chat or
              ctx.forward_sender_name or not ctx.forward_from):
            return ""
        else:
            return ctx.forward_from.username or ""
    elif ctx.from_user and ctx.from_user.username:
        return ctx.from_user.username
    elif (ctx.from_user or ctx.sender_chat and not ctx.sender_chat.username or not ctx.sender_chat):
        return ""
    else:
        return ctx.sender_chat.username

async def get_message_sender_photo(ctx: Message):
    if ctx.forward_date:
        if (not ctx.forward_sender_name and not ctx.forward_from and
            ctx.forward_from_chat and ctx.forward_from_chat.photo):
            return {
                "small_file_id": ctx.forward_from_chat.photo.small_file_id,
                "small_photo_unique_id": ctx.forward_from_chat.photo.small_photo_unique_id,
                "big_file_id": ctx.forward_from_chat.photo.big_file_id,
                "big_photo_unique_id": ctx.forward_from_chat.photo.big_photo_unique_id,
            }
        elif (not ctx.forward_sender_name and not ctx.forward_from and ctx.forward_from_chat or
              ctx.forward_sender_name or not ctx.forward_from):
            return ""
        else:
            return (
                {
                    "small_file_id": ctx.forward_from.photo.small_file_id,
                    "small_photo_unique_id": ctx.forward_from.photo.small_photo_unique_id,
                    "big_file_id": ctx.forward_from.photo.big_file_id,
                    "big_photo_unique_id": ctx.forward_from.photo.big_photo_unique_id,
                }
                if ctx.forward_from.photo
                else ""
            )
    elif ctx.from_user and ctx.from_user.photo:
        return {
            "small_file_id": ctx.from_user.photo.small_file_id,
            "small_photo_unique_id": ctx.from_user.photo.small_photo_unique_id,
            "big_file_id": ctx.from_user.photo.big_file_id,
            "big_photo_unique_id": ctx.from_user.photo.big_photo_unique_id,
        }
    elif (ctx.from_user or ctx.sender_chat and not ctx.sender_chat.photo or not ctx.sender_chat):
        return ""
    else:
        return {
            "small_file_id": ctx.sender_chat.photo.small_file_id,
            "small_photo_unique_id": ctx.sender_chat.photo.small_photo_unique_id,
            "big_file_id": ctx.sender_chat.photo.big_file_id,
            "big_photo_unique_id": ctx.sender_chat.photo.big_photo_unique_id,
        }

async def get_text_or_caption(ctx: Message):
    return ctx.text or ctx.caption or ""

async def pyrogram_to_quotly(messages, is_reply):
    if not isinstance(messages, list):
        messages = [messages]
    payload = {
        "type": "quote",
        "format": "png",
        "backgroundColor": "#1b1429",
        "messages": [],
    }
    for message in messages:
        the_message_dict_to_append = {}
        if message.entities:
            the_message_dict_to_append["entities"] = [
                {
                    "type": entity.type.name.lower(),
                    "offset": entity.offset,
                    "length": entity.length,
                }
                for entity in message.entities
            ]
        elif message.caption_entities:
            the_message_dict_to_append["entities"] = [
                {
                    "type": entity.type.name.lower(),
                    "offset": entity.offset,
                    "length": entity.length,
                }
                for entity in message.caption_entities
            ]
        else:
            the_message_dict_to_append["entities"] = []
        the_message_dict_to_append["chatId"] = await get_message_sender_id(message)
        the_message_dict_to_append["text"] = await get_text_or_caption(message)
        the_message_dict_to_append["avatar"] = True
        the_message_dict_to_append["from"] = {
            "id": await get_message_sender_id(message),
            "name": await get_message_sender_name(message),
            "username": await get_message_sender_username(message),
            "type": message.chat.type.name.lower(),
            "photo": await get_message_sender_photo(message)
        }
        if message.reply_to_message and is_reply:
            the_message_dict_to_append["replyMessage"] = {
                "name": await get_message_sender_name(message.reply_to_message),
                "text": await get_text_or_caption(message.reply_to_message),
                "chatId": await get_message_sender_id(message.reply_to_message),
            }
        else:
            the_message_dict_to_append["replyMessage"] = {}
        payload["messages"].append(the_message_dict_to_append)
    r = await fetch.post("https://bot.lyo.su/quote/generate.png", json=payload)
    if not r.is_error:
        return r.read()
    else:
        raise QuotlyException(r.json())

@app.on_message(filters.command("q") & filters.reply)
async def msg_quotly_cmd(self: Client, ctx: Message):
    args = ctx.text.split()[1:]
    is_reply = False
    count = 1
    for arg in args:
        if arg.lower() == 'r':
            is_reply = True
        elif arg.isdigit():
            count = int(arg)

    if count < 1 or count > 10:
        return await ctx.reply_text("Invalid range (1-10)", delete_after=6)

    processing_msg = await ctx.reply_text("❄️")
    try:
        if count == 1:
            messages = [ctx.reply_to_message]
        else:
            message_ids = range(ctx.reply_to_message.id, ctx.reply_to_message.id + count)
            messages = [
                i for i in await self.get_messages(chat_id=ctx.chat.id, message_ids=message_ids)
                if not i.empty and not i.media
            ]
    except Exception:
        await processing_msg.delete()
        return await ctx.reply_text("🤷🏻‍♂️")

    try:
        make_quotly = await pyrogram_to_quotly(messages, is_reply=is_reply)
        bio_sticker = BytesIO(make_quotly)
        bio_sticker.name = "quote.webp"
        await ctx.reply_sticker(bio_sticker)
    except Exception as e:
        await ctx.reply_text(f"ERROR: {e}")
    finally:
        await processing_msg.delete()

__mod_name__ = "Qᴜᴏᴛʟʏ"
__help__ = """
Create a sticker from messages using Quotly.

 ❍ /q*:* Reply to a message to create a sticker.
 ❍ /q <number>*:* Quote more than one message.
 ❍ /q r*:* Quote with reply.
"""
