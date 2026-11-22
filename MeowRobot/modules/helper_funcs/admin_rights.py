#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

from telegram import Chat, User
from telegram.constants import ChatMemberStatus


async def user_can_promote(chat: Chat, user: User, bot_id: int) -> bool:
    member = await chat.get_member(user.id)
    return member.status == ChatMemberStatus.OWNER or getattr(member, 'can_promote_members', False)


async def user_can_ban(chat: Chat, user: User, bot_id: int) -> bool:
    member = await chat.get_member(user.id)
    return member.status == ChatMemberStatus.OWNER or getattr(member, 'can_restrict_members', False)


async def user_can_pin(chat: Chat, user: User, bot_id: int) -> bool:
    member = await chat.get_member(user.id)
    return member.status == ChatMemberStatus.OWNER or getattr(member, 'can_pin_messages', False)


async def user_can_changeinfo(chat: Chat, user: User, bot_id: int) -> bool:
    member = await chat.get_member(user.id)
    return member.status == ChatMemberStatus.OWNER or getattr(member, 'can_change_info', False)
