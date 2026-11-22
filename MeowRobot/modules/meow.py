#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import random
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import RPCError
from pyrogram.types import ChatPermissions, ChatPrivileges, Message

from MeowRobot import DEV_USERS, DRAGONS, OWNER_ID, pbot as app

SUDOERS = set(list(DRAGONS) + list(DEV_USERS) + [OWNER_ID])

shashank_text = [
    "hey please don't disturb me.",
    "who are you",
    "aap kon ho",
    "aap mere owner to nhi lgte ",
    "hey tum mera name kyu le rhe ho meko sone do",
    "ha bolo kya kaam hai ",
    "dekho abhi mai busy hu ",
    "hey i am busy",
    "aapko smj nhi aata kya ",
    "leave me alone",
    "dude what happend",
]

strict_txt = [
    "i can't restrict against my besties",
    "are you serious i am not restrict to my friends",
    "fuck you bsdk k mai apne dosto ko kyu kru",
    "hey stupid admin ",
    "ha ye phele krlo maar lo ek dusre ki gwaand",
    "i can't hi is my closest friend",
    "i love him please don't restict this user try to usertand ",
]

ban = ["ban", "boom"]
unban = ["unban"]
mute = ["mute", "silent", "shut"]
unmute = ["unmute", "speak", "free"]
kick = ["kick", "out", "nikaal", "nikal"]
promote = ["promote", "adminship"]
fullpromote = ["fullpromote", "fulladmin"]
demote = ["demote", "lelo"]
pin = ["pin"]
unpin = ["unpin"]


async def is_admin_check(_, __, message: Message) -> bool:
    if not message.from_user:
        return bool(message.sender_chat and message.sender_chat.id == message.chat.id)
    if message.from_user.id in SUDOERS:
        return True
    try:
        member = await app.get_chat_member(message.chat.id, message.from_user.id)
        return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)
    except Exception:
        return False


admin_filter = filters.create(is_admin_check)


@app.on_message(
    filters.command(
        ["kanha", "anu", "anupriya", "meow"],
        prefixes=["", "/", "!", "."],
    )
    & filters.group
    & admin_filter
)
async def restriction_app(client, message: Message):
    reply = message.reply_to_message
    chat_id = message.chat.id

    if not message.text:
        return

    tokens = message.text.split()
    if len(tokens) < 2:
        return await message.reply(random.choice(shashank_text))

    if not reply:
        return await message.reply("Kisi message par reply karke command do!")

    data = [word.lower() for word in tokens[1:]]

    try:
        # 1. Pin / Unpin message actions (work on any replied message)
        for pinned in data:
            if pinned in pin:
                await client.pin_chat_message(chat_id, reply.id)
                await message.reply("Pinned successfully! 📌")

        for unpinned in data:
            if unpinned in unpin:
                await client.unpin_chat_message(chat_id, reply.id)
                await message.reply("Unpinned successfully! 📌")

        # 2. User-specific restriction and promotion actions
        user_actions = set(
            ban + unban + kick + mute + unmute + promote + demote + fullpromote
        )
        needs_user_action = any(action in user_actions for action in data)

        if needs_user_action:
            if not reply.from_user:
                return await message.reply("Kisi user ke message par reply karke command do!")

            user_id = reply.from_user.id
            bot_user = await client.get_me()
            if user_id == bot_user.id:
                return await message.reply("Mai khud par action nahi le sakta!")

            for banned in data:
                if banned in ban:
                    if user_id in SUDOERS:
                        await message.reply(random.choice(strict_txt))
                    else:
                        await client.ban_chat_member(chat_id, user_id)
                        await message.reply("OK, Ban kar diya madrchod ko sala Chutiya tha !")

            for unbanned in data:
                if unbanned in unban:
                    await client.unban_chat_member(chat_id, user_id)
                    await message.reply("Ok, aap bolte hai to unban kar diya")

            for kicked in data:
                if kicked in kick:
                    if user_id in SUDOERS:
                        await message.reply(random.choice(strict_txt))
                    else:
                        await client.ban_chat_member(chat_id, user_id)
                        await client.unban_chat_member(chat_id, user_id)
                        await message.reply("get lost! bhga diya bhosdi wale ko")

            for muted in data:
                if muted in mute:
                    if user_id in SUDOERS:
                        await message.reply(random.choice(strict_txt))
                    else:
                        permissions = ChatPermissions(can_send_messages=False)
                        await client.restrict_chat_member(chat_id, user_id, permissions)
                        await message.reply("muted successfully! Disgusting people.")

            for unmuted in data:
                if unmuted in unmute:
                    permissions = ChatPermissions(can_send_messages=True)
                    await client.restrict_chat_member(chat_id, user_id, permissions)
                    await message.reply("Huh, OK, sir!")

            for promoted in data:
                if promoted in promote:
                    await client.promote_chat_member(
                        chat_id,
                        user_id,
                        privileges=ChatPrivileges(
                            can_change_info=False,
                            can_invite_users=True,
                            can_delete_messages=True,
                            can_restrict_members=False,
                            can_pin_messages=True,
                            can_promote_members=False,
                            can_manage_chat=True,
                            can_manage_video_chats=True,
                        ),
                    )
                    await message.reply("promoted !")

            for demoted in data:
                if demoted in demote:
                    await client.promote_chat_member(
                        chat_id,
                        user_id,
                        privileges=ChatPrivileges(
                            can_change_info=False,
                            can_invite_users=False,
                            can_delete_messages=False,
                            can_restrict_members=False,
                            can_pin_messages=False,
                            can_promote_members=False,
                            can_manage_chat=False,
                            can_manage_video_chats=False,
                        ),
                    )
                    await message.reply("demoted !")

            for fullpromoted in data:
                if fullpromoted in fullpromote:
                    await client.promote_chat_member(
                        chat_id,
                        user_id,
                        privileges=ChatPrivileges(
                            can_change_info=True,
                            can_invite_users=True,
                            can_delete_messages=True,
                            can_restrict_members=True,
                            can_pin_messages=True,
                            can_promote_members=True,
                            can_manage_chat=True,
                            can_manage_video_chats=True,
                        ),
                    )
                    await message.reply("fullpromoted !")

    except RPCError as e:
        await message.reply(f"Action failed: {e.MESSAGE or e}")
