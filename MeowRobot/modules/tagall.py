#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import asyncio
import html

from telethon import events
from telethon.errors import (
    ChannelInvalidError,
    ChatAdminRequiredError,
    ChatWriteForbiddenError,
    FloodWaitError,
    UserNotParticipantError,
)
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.types import ChannelParticipantAdmin, ChannelParticipantCreator

from MeowRobot import DRAGONS, telethn as client

spam_chats = set()


async def is_admin(event) -> bool:
    """Checks whether the event sender is an admin or privileged user."""
    if not event.sender_id:
        return False

    # Anonymous admin sending as the group chat itself
    if event.sender_id == event.chat_id:
        return True

    # Bot Owner / Sudo / Dev
    if event.sender_id in DRAGONS:
        return True

    try:
        perms = await client.get_permissions(event.chat_id, event.sender_id)
        if perms and perms.is_admin:
            return True
    except Exception:
        pass

    try:
        partici_ = await client(GetParticipantRequest(event.chat_id, event.sender_id))
        if partici_ and isinstance(
            partici_.participant, (ChannelParticipantAdmin, ChannelParticipantCreator)
        ):
            return True
    except (UserNotParticipantError, ChannelInvalidError):
        return False
    except Exception:
        return False

    return False


@client.on(
    events.NewMessage(
        pattern=r"(?i)^[/!](?:tagall|all|mentionall)(?:@\w+)?(?:\s+([\s\S]+))?$"
    )
)
@client.on(events.NewMessage(pattern=r"(?i)^@all(?:\s+([\s\S]+))?$"))
async def mentionall(event):
    chat_id = event.chat_id
    if event.is_private:
        return await event.respond(
            "__This command can only be used in groups and channels!__"
        )

    if not await is_admin(event):
        return await event.respond("__Only admins can mention all members!__")

    if chat_id in spam_chats:
        return await event.respond(
            "__A tagall process is already running in this chat! Use /cancel to stop it.__"
        )

    reply_msg = None
    if event.is_reply:
        reply_msg = await event.get_reply_message()

    custom_text = event.pattern_match.group(1)
    if custom_text:
        custom_text = custom_text.strip()

    if not custom_text and not reply_msg:
        custom_text = "📢 Attention Everyone!"

    spam_chats.add(chat_id)
    usrnum = 0
    usrtxt = ""

    try:
        async for usr in client.iter_participants(chat_id):
            if chat_id not in spam_chats:
                break
            if usr.deleted or usr.bot:
                continue

            usrnum += 1
            safe_name = html.escape(usr.first_name or "User")
            usrtxt += f"<a href='tg://user?id={usr.id}'>{safe_name}</a>  "

            if usrnum == 5:
                if custom_text:
                    txt = f"{html.escape(custom_text)}\n\n{usrtxt}"
                else:
                    txt = usrtxt

                try:
                    if reply_msg:
                        await reply_msg.reply(txt, parse_mode="html")
                    else:
                        await client.send_message(chat_id, txt, parse_mode="html")
                except FloodWaitError as e:
                    await asyncio.sleep(e.seconds + 1)
                    try:
                        if reply_msg:
                            await reply_msg.reply(txt, parse_mode="html")
                        else:
                            await client.send_message(chat_id, txt, parse_mode="html")
                    except Exception:
                        pass
                except (ChatWriteForbiddenError, ChatAdminRequiredError):
                    break
                except Exception:
                    pass

                await asyncio.sleep(2.5)
                usrnum = 0
                usrtxt = ""

        # Send any leftover participants (e.g. member count not divisible by 5)
        if usrtxt and chat_id in spam_chats:
            if custom_text:
                txt = f"{html.escape(custom_text)}\n\n{usrtxt}"
            else:
                txt = usrtxt

            try:
                if reply_msg:
                    await reply_msg.reply(txt, parse_mode="html")
                else:
                    await client.send_message(chat_id, txt, parse_mode="html")
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds + 1)
                try:
                    if reply_msg:
                        await reply_msg.reply(txt, parse_mode="html")
                    else:
                        await client.send_message(chat_id, txt, parse_mode="html")
                except Exception:
                    pass
            except Exception:
                pass

    except ChatAdminRequiredError:
        await event.respond("__I need admin rights to fetch group members list!__")
    except Exception:
        pass
    finally:
        spam_chats.discard(chat_id)


@client.on(
    events.NewMessage(pattern=r"(?i)^[/!](?:cancel|stop|tagoff|canceltag)(?:@\w+)?$")
)
async def cancel_spam(event):
    if event.is_private:
        return

    if event.chat_id not in spam_chats:
        return await event.respond("__There is no ongoing tagall process in this chat.__")

    if not await is_admin(event):
        return await event.respond("__Only admins can stop the tagall process!__")

    spam_chats.discard(event.chat_id)
    return await event.respond("__Stopped tagall process.__")


__mod_name__ = "Tᴀɢ Aʟʟ"
__help__ = """
*Only for admins*

Mention all members in your group without exception.

❍ /tagall [message] : Mention all members in batches with custom message.
❍ /tagall (as reply) : Reply to any message to mention members to see it.
❍ /all or @all : Shortcut for tagall.
❍ /cancel or /stop : Stop an ongoing tagall process.
"""
