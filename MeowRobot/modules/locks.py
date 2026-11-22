#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import html
import re
import unicodedata as ud

from telegram import ChatPermissions, MessageEntity, Update
from telegram.constants import ParseMode, ChatType, ChatMemberStatus
from telegram.error import BadRequest
from telegram.ext import ContextTypes, CommandHandler, filters, MessageHandler
from telegram.helpers import mention_html

import MeowRobot.modules.sql.locks_sql as sql
from MeowRobot import DRAGONS, LOGGER, application
from MeowRobot.modules.connection import connected
from MeowRobot.modules.disable import DisableAbleCommandHandler
from MeowRobot.modules.helper_funcs.alternate import send_message, typing_action
from MeowRobot.modules.helper_funcs.chat_status import (
    can_delete,
    is_bot_admin,
    is_user_admin,
    user_admin,
    user_not_admin,
)
from MeowRobot.modules.log_channel import loggable
from MeowRobot.modules.sql.approve_sql import is_approved


def al_detect(unistr):
    return set(ud.name(char).split(" ")[0] for char in unistr if char.isalpha())


LOCK_TYPES = {
    "anonchannel": "anonchannel",
    "audio": filters.AUDIO,
    "bots": filters.StatusUpdate.NEW_CHAT_MEMBERS,
    "button": "button",
    "command": "command",
    "contact": filters.CONTACT,
    "document": filters.Document.ALL,
    "egame": filters.Dice.ALL,
    "email": "email",
    "emojipack": "emojipack",
    "forward": filters.FORWARDED,
    "game": filters.GAME,
    "gif": filters.ANIMATION,
    "inline": "inline",
    "invitelink": "invitelink",
    "location": filters.LOCATION,
    "mention": "mention",
    "phone": "phone",
    "photo": filters.PHOTO,
    "poll": "poll",
    "rtl": "rtl",
    "spoiler": "spoiler",
    "sticker": filters.Sticker.ALL,
    "text": "text",
    "url": filters.Entity(MessageEntity.URL)
    | filters.CaptionEntity(MessageEntity.URL),
    "video": filters.VIDEO,
    "videonote": "videonote",
    "voice": filters.VOICE,
}

LOCK_CHAT_RESTRICTION = {
    "all": {
        "can_send_messages": False,
        "can_send_polls": False,
        "can_send_other_messages": False,
        "can_add_web_page_previews": False,
        "can_change_info": False,
        "can_invite_users": False,
        "can_pin_messages": False,
        "can_send_audios": False,
        "can_send_documents": False,
        "can_send_photos": False,
        "can_send_videos": False,
        "can_send_video_notes": False,
        "can_send_voice_notes": False,
        "can_manage_topics": False,
    },
    "messages": {"can_send_messages": False},
    "media": {
        "can_send_audios": False,
        "can_send_documents": False,
        "can_send_photos": False,
        "can_send_videos": False,
        "can_send_video_notes": False,
        "can_send_voice_notes": False,
    },
    "audios": {"can_send_audios": False},
    "documents": {"can_send_documents": False},
    "photos": {"can_send_photos": False},
    "videos": {"can_send_videos": False},
    "videonotes": {"can_send_video_notes": False},
    "voice": {"can_send_voice_notes": False},
    "polls": {"can_send_polls": False},
    "other": {"can_send_other_messages": False},
    "previews": {"can_add_web_page_previews": False},
    "info": {"can_change_info": False},
    "invite": {"can_invite_users": False},
    "pin": {"can_pin_messages": False},
    "topics": {"can_manage_topics": False},
}

UNLOCK_CHAT_RESTRICTION = {
    "all": {
        "can_send_messages": True,
        "can_send_polls": True,
        "can_send_other_messages": True,
        "can_add_web_page_previews": True,
        "can_invite_users": True,
        "can_send_audios": True,
        "can_send_documents": True,
        "can_send_photos": True,
        "can_send_videos": True,
        "can_send_video_notes": True,
        "can_send_voice_notes": True,
        "can_change_info": True,
        "can_pin_messages": True,
        "can_manage_topics": True,
    },
    "messages": {"can_send_messages": True},
    "media": {
        "can_send_audios": True,
        "can_send_documents": True,
        "can_send_photos": True,
        "can_send_videos": True,
        "can_send_video_notes": True,
        "can_send_voice_notes": True,
    },
    "audios": {"can_send_audios": True},
    "documents": {"can_send_documents": True},
    "photos": {"can_send_photos": True},
    "videos": {"can_send_videos": True},
    "videonotes": {"can_send_video_notes": True},
    "voice": {"can_send_voice_notes": True},
    "polls": {"can_send_polls": True},
    "other": {"can_send_other_messages": True},
    "previews": {"can_add_web_page_previews": True},
    "info": {"can_change_info": True},
    "invite": {"can_invite_users": True},
    "pin": {"can_pin_messages": True},
    "topics": {"can_manage_topics": True},
}

PERM_GROUP = 1
REST_GROUP = 2


async def locktypes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "\n • ".join(
            ["Locks available: "]
            + sorted(list(LOCK_TYPES) + list(LOCK_CHAT_RESTRICTION))
        )
    )


@user_admin
@loggable
@typing_action
async def lock(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    args = context.args
    chat = update.effective_chat
    user = update.effective_user

    if (
        await can_delete(chat, context.bot.id)
        or update.effective_message.chat.type == ChatType.PRIVATE
    ):
        if len(args) >= 1:
            ltype = args[0].lower()
            if ltype in LOCK_TYPES:
                # Connection check
                conn = await connected(context.bot, update, chat, user.id, need_admin=True)
                if conn:
                    chat_obj = await context.bot.get_chat(conn)
                    chat_id = conn
                    chat_name = chat_obj.title
                    text = "Locked {} for non-admins in {}!".format(ltype, chat_name)
                else:
                    if update.effective_message.chat.type == ChatType.PRIVATE:
                        await send_message(
                            update.effective_message,
                            "This command is meant to use in group not in PM",
                        )
                        return ""
                    chat_id = update.effective_chat.id
                    chat_name = update.effective_message.chat.title
                    text = "Locked {} for non-admins!".format(ltype)
                sql.update_lock(chat_id, ltype, locked=True)
                await send_message(update.effective_message, text, parse_mode=ParseMode.MARKDOWN)

                return (
                    "<b>{}:</b>"
                    "\n#LOCK"
                    "\n<b>Admin:</b> {}"
                    "\nLocked <code>{}</code>.".format(
                        html.escape(chat_name),
                        mention_html(user.id, user.first_name),
                        ltype,
                    )
                )

            elif ltype in LOCK_CHAT_RESTRICTION:
                # Connection check
                conn = await connected(context.bot, update, chat, user.id, need_admin=True)
                if conn:
                    chat_obj = await context.bot.get_chat(conn)
                    chat_id = conn
                    chat_name = chat_obj.title
                    text = "Locked {} for all non-admins in {}!".format(
                        ltype, chat_name
                    )
                else:
                    if update.effective_message.chat.type == ChatType.PRIVATE:
                        await send_message(
                            update.effective_message,
                            "This command is meant to use in group not in PM",
                        )
                        return ""
                    chat_id = update.effective_chat.id
                    chat_name = update.effective_message.chat.title
                    text = "Locked {} for all non-admins!".format(ltype)

                current_chat = await context.bot.get_chat(chat_id)
                current_permission = current_chat.permissions

                await context.bot.set_chat_permissions(
                    chat_id=chat_id,
                    permissions=get_permission_list(
                        current_permission.to_dict(),
                        LOCK_CHAT_RESTRICTION[ltype.lower()],
                    ),
                )

                await send_message(update.effective_message, text, parse_mode=ParseMode.MARKDOWN)
                return (
                    "<b>{}:</b>"
                    "\n#Permission_LOCK"
                    "\n<b>Admin:</b> {}"
                    "\nLocked <code>{}</code>.".format(
                        html.escape(chat_name),
                        mention_html(user.id, user.first_name),
                        ltype,
                    )
                )

            else:
                await send_message(
                    update.effective_message,
                    "What are you trying to lock...? Try /locktypes for the list of lockables",
                )
        else:
            await send_message(update.effective_message, "What are you trying to lock...?")

    else:
        await send_message(
            update.effective_message,
            "I am not administrator or haven't got enough rights.",
        )

    return ""


@user_admin
@loggable
@typing_action
async def unlock(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    args = context.args
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    if await is_user_admin(chat, message.from_user.id):
        if len(args) >= 1:
            ltype = args[0].lower()
            if ltype in LOCK_TYPES:
                # Connection check
                conn = await connected(context.bot, update, chat, user.id, need_admin=True)
                if conn:
                    chat_obj = await context.bot.get_chat(conn)
                    chat_id = conn
                    chat_name = chat_obj.title
                    text = "Unlocked {} for everyone in {}!".format(ltype, chat_name)
                else:
                    if update.effective_message.chat.type == ChatType.PRIVATE:
                        await send_message(
                            update.effective_message,
                            "This command is meant to use in group not in PM",
                        )
                        return ""
                    chat_id = update.effective_chat.id
                    chat_name = update.effective_message.chat.title
                    text = "Unlocked {} for everyone!".format(ltype)
                sql.update_lock(chat_id, ltype, locked=False)
                await send_message(update.effective_message, text, parse_mode=ParseMode.MARKDOWN)
                return (
                    "<b>{}:</b>"
                    "\n#UNLOCK"
                    "\n<b>Admin:</b> {}"
                    "\nUnlocked <code>{}</code>.".format(
                        html.escape(chat_name),
                        mention_html(user.id, user.first_name),
                        ltype,
                    )
                )

            elif ltype in UNLOCK_CHAT_RESTRICTION:
                # Connection check
                conn = await connected(context.bot, update, chat, user.id, need_admin=True)
                if conn:
                    chat_obj = await context.bot.get_chat(conn)
                    chat_id = conn
                    chat_name = chat_obj.title
                    text = "Unlocked {} for everyone in {}!".format(ltype, chat_name)
                else:
                    if update.effective_message.chat.type == ChatType.PRIVATE:
                        await send_message(
                            update.effective_message,
                            "This command is meant to use in group not in PM",
                        )
                        return ""
                    chat_id = update.effective_chat.id
                    chat_name = update.effective_message.chat.title
                    text = "Unlocked {} for everyone!".format(ltype)

                member = await chat.get_member(context.bot.id)
                if not getattr(member, 'can_change_info', False):
                    await send_message(
                        update.effective_message,
                        "I don't have permission to change group info.",
                        parse_mode=ParseMode.MARKDOWN,
                    )
                    return ""

                current_chat = await context.bot.get_chat(chat_id)
                current_permission = current_chat.permissions

                await context.bot.set_chat_permissions(
                    chat_id=chat_id,
                    permissions=get_permission_list(
                        current_permission.to_dict(),
                        UNLOCK_CHAT_RESTRICTION[ltype.lower()],
                    ),
                )

                await send_message(update.effective_message, text, parse_mode=ParseMode.MARKDOWN)

                return (
                    "<b>{}:</b>"
                    "\n#UNLOCK"
                    "\n<b>Admin:</b> {}"
                    "\nUnlocked <code>{}</code>.".format(
                        html.escape(chat_name),
                        mention_html(user.id, user.first_name),
                        ltype,
                    )
                )
            else:
                await send_message(
                    update.effective_message,
                    "What are you trying to unlock...? Try /locktypes for the list of lockables.",
                )

        else:
            await send_message(update.effective_message, "What are you trying to unlock...?")

    return ""


@user_not_admin
async def del_lockables(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user
    if not message or not chat:
        return
    if user and is_approved(chat.id, user.id):
        return

    async def _safe_delete(msg):
        try:
            await msg.delete()
        except BadRequest as excp:
            if excp.message != "Message to delete not found":
                LOGGER.exception("ERROR in lockables")

    for lockable, filter in LOCK_TYPES.items():
        if not sql.is_locked(chat.id, lockable):
            continue

        if not await can_delete(chat, context.bot.id):
            break

        if lockable == "rtl":
            if message.caption and "ARABIC" in al_detect(f"{message.caption}"):
                await _safe_delete(message)
                break
            if message.text and "ARABIC" in al_detect(f"{message.text}"):
                await _safe_delete(message)
                break
            continue

        if lockable == "button":
            if message.reply_markup and message.reply_markup.inline_keyboard:
                await _safe_delete(message)
                break
            continue

        if lockable == "inline":
            if message.via_bot:
                await _safe_delete(message)
                break
            continue

        if lockable == "anonchannel":
            if message.sender_chat and message.sender_chat.id != chat.id:
                await _safe_delete(message)
                break
            continue

        if lockable == "invitelink":
            text_content = f"{message.text or ''} {message.caption or ''}"
            if re.search(
                r"(?:t\.me|telegram\.me|telegram\.dog)/(?:joinchat/|\+)?([a-zA-Z0-9_\-]+)",
                text_content,
                re.IGNORECASE,
            ):
                await _safe_delete(message)
                break
            continue

        if lockable == "poll":
            if getattr(message, "poll", None) is not None:
                await _safe_delete(message)
                break
            continue

        if lockable == "videonote":
            if getattr(message, "video_note", None) is not None:
                await _safe_delete(message)
                break
            continue

        if lockable == "spoiler":
            entities = list(message.entities or []) + list(
                message.caption_entities or []
            )
            if any(
                getattr(e, "type", None) in (MessageEntity.SPOILER, "spoiler")
                for e in entities
            ) or getattr(message, "has_media_spoiler", False):
                await _safe_delete(message)
                break
            continue

        if lockable == "emojipack":
            entities = list(message.entities or []) + list(
                message.caption_entities or []
            )
            if any(
                getattr(e, "type", None)
                in (MessageEntity.CUSTOM_EMOJI, "custom_emoji")
                for e in entities
            ):
                await _safe_delete(message)
                break
            continue

        if lockable == "phone":
            entities = list(message.entities or []) + list(
                message.caption_entities or []
            )
            if any(
                getattr(e, "type", None)
                in (MessageEntity.PHONE_NUMBER, "phone_number")
                for e in entities
            ):
                await _safe_delete(message)
                break
            continue

        if lockable == "email":
            entities = list(message.entities or []) + list(
                message.caption_entities or []
            )
            if any(
                getattr(e, "type", None) in (MessageEntity.EMAIL, "email")
                for e in entities
            ):
                await _safe_delete(message)
                break
            continue

        if lockable == "mention":
            entities = list(message.entities or []) + list(
                message.caption_entities or []
            )
            if any(
                getattr(e, "type", None)
                in (
                    MessageEntity.MENTION,
                    MessageEntity.TEXT_MENTION,
                    "mention",
                    "text_mention",
                )
                for e in entities
            ):
                await _safe_delete(message)
                break
            continue

        if lockable == "command":
            entities = list(message.entities or [])
            if any(
                getattr(e, "type", None)
                in (MessageEntity.BOT_COMMAND, "bot_command")
                for e in entities
            ):
                await _safe_delete(message)
                break
            continue

        if lockable == "text":
            if message.text and not any(
                getattr(e, "type", None)
                in (MessageEntity.BOT_COMMAND, "bot_command")
                for e in (message.entities or [])
            ):
                await _safe_delete(message)
                break
            continue

        if isinstance(filter, filters.BaseFilter):
            res = filter.check_update(update)
        else:
            res = False

        if res:
            if lockable == "bots":
                new_members = update.effective_message.new_chat_members
                for new_mem in new_members:
                    if new_mem.is_bot:
                        if not await is_bot_admin(chat, context.bot.id):
                            await send_message(
                                update.effective_message,
                                "I see a bot and I've been told to stop them from joining..."
                                "but I'm not admin!",
                            )
                            return

                        await chat.ban_member(new_mem.id)
                        await send_message(
                            update.effective_message,
                            "Only admins are allowed to add bots in this chat! Get outta here.",
                        )
                        break
            else:
                await _safe_delete(message)
                break


async def build_lock_message(chat_id):
    locks = sql.get_locks(chat_id)
    res = ""
    locklist = []
    permslist = []
    if locks:
        res += "*" + "These are the current locks in this Chat:" + "*"
        for lockable in sorted(LOCK_TYPES.keys()):
            val = getattr(locks, lockable, False)
            locklist.append(f"{lockable} = `{val}`")

    chat = await application.bot.get_chat(chat_id)
    permissions = chat.permissions
    permslist.append("messages = `{}`".format(permissions.can_send_messages))
    permslist.append("audios = `{}`".format(permissions.can_send_audios))
    permslist.append("documents = `{}`".format(permissions.can_send_documents))
    permslist.append("photos = `{}`".format(permissions.can_send_photos))
    permslist.append("videos = `{}`".format(permissions.can_send_videos))
    permslist.append("video_notes = `{}`".format(permissions.can_send_video_notes))
    permslist.append("voice_notes = `{}`".format(permissions.can_send_voice_notes))
    permslist.append("polls = `{}`".format(permissions.can_send_polls))
    permslist.append("other = `{}`".format(permissions.can_send_other_messages))
    permslist.append("previews = `{}`".format(permissions.can_add_web_page_previews))
    permslist.append("info = `{}`".format(permissions.can_change_info))
    permslist.append("invite = `{}`".format(permissions.can_invite_users))
    permslist.append("pin = `{}`".format(permissions.can_pin_messages))
    permslist.append("topics = `{}`".format(getattr(permissions, "can_manage_topics", None)))

    if locklist:
        locklist.sort()
        for x in locklist:
            res += "\n • {}".format(x)
    res += "\n\n*" + "These are the current chat permissions:" + "*"
    for x in permslist:
        res += "\n • {}".format(x)
    return res


@user_admin
@typing_action
async def list_locks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    # Connection check
    conn = await connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat_obj = await context.bot.get_chat(conn)
        chat_name = chat_obj.title
    else:
        if update.effective_message.chat.type == ChatType.PRIVATE:
            await send_message(
                update.effective_message,
                "This command is meant to use in group not in PM",
            )
            return
        chat_name = update.effective_message.chat.title

    res = await build_lock_message(chat.id)
    if conn:
        res = res.replace("Locks in", "*{}*".format(chat_name))

    await send_message(update.effective_message, res, parse_mode=ParseMode.MARKDOWN)


def get_permission_list(current, new):
    permissions = {
        "can_send_messages": None,
        "can_send_audios": None,
        "can_send_documents": None,
        "can_send_photos": None,
        "can_send_videos": None,
        "can_send_video_notes": None,
        "can_send_voice_notes": None,
        "can_send_polls": None,
        "can_send_other_messages": None,
        "can_add_web_page_previews": None,
        "can_change_info": None,
        "can_invite_users": None,
        "can_pin_messages": None,
    }
    permissions.update(current)
    permissions.update(new)

    # Filter out obsolete keys
    allowed_keys = {
        "can_send_messages", "can_send_audios", "can_send_documents", "can_send_photos",
        "can_send_videos", "can_send_video_notes", "can_send_voice_notes", "can_send_polls",
        "can_send_other_messages", "can_add_web_page_previews", "can_change_info",
        "can_invite_users", "can_pin_messages", "can_manage_topics"
    }
    filtered_permissions = {k: v for k, v in permissions.items() if k in allowed_keys}

    new_permissions = ChatPermissions(**filtered_permissions)
    return new_permissions


def __import_data__(chat_id, data):
    # set chat locks
    locks = data.get("locks", {})
    for itemlock in locks:
        if itemlock in LOCK_TYPES:
            sql.update_lock(chat_id, itemlock, locked=True)
        elif itemlock in LOCK_CHAT_RESTRICTION:
            sql.update_restriction(chat_id, itemlock, locked=True)
        else:
            pass


async def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


async def __chat_settings__(chat_id, user_id):
    return await build_lock_message(chat_id)


__help__ = """
Do stickers annoy you? or want to avoid people sharing links? or pictures? \
You're in the right place!
The locks module allows you to lock away some common items in the \
telegram world; the bot will automatically delete them!

 ❍ /locktypes*:* Lists all possible locktypes
 
*Admins only:*
 ❍ /lock <type>*:* Lock items of a certain type (not available in private)
 ❍ /unlock <type>*:* Unlock items of a certain type (not available in private)
 ❍ /locks*:* The current list of locks in this chat.

*Available Lock Types:*
 • `anonchannel`: Messages sent by anonymous channels
 • `audio`: Audio files
 • `bots`: Stop bots from being added by non-admins
 • `button`: Messages containing inline buttons
 • `command`: Bot commands (/start, etc.)
 • `contact`: Shared contacts
 • `document`: Documents / files
 • `egame`: Dice, basketball, slot games
 • `email`: Email addresses
 • `emojipack`: Custom / animated emojis
 • `forward`: Forwarded messages
 • `game`: HTML5 games
 • `gif`: GIFs / Animations
 • `inline`: Messages sent via inline bots
 • `invitelink`: Telegram group / channel invite links
 • `location`: Location sharing
 • `mention`: @mentions and text mentions
 • `phone`: Phone numbers
 • `photo`: Photos / images
 • `poll`: Polls
 • `rtl`: Right-to-Left (Arabic / Persian) text
 • `spoiler`: Spoilers in text or media captions
 • `sticker`: Stickers (standard, animated, video)
 • `text`: Plain text messages
 • `url`: Links / URLs
 • `video`: Videos
 • `videonote`: Round video notes
 • `voice`: Voice notes

*Chat Permission Restrictions:*
 • `all`: Lock all chat permissions
 • `messages`, `media`, `photos`, `videos`, `audios`, `documents`, `voice`, `videonotes`, `polls`, `other`, `previews`, `info`, `invite`, `pin`, `topics`

*Note:*
 • Unlocking permission *info* will allow members (non-admins) to change the group information, such as the description or the group name
 • Unlocking permission *pin* will allow members (non-admins) to pin a message in a group
"""

__mod_name__ = "Lᴏᴄᴋs"

LOCKTYPES_HANDLER = DisableAbleCommandHandler("locktypes", locktypes)
LOCK_HANDLER = CommandHandler(
    "lock", lock
)
UNLOCK_HANDLER = CommandHandler(
    "unlock", unlock
)
LOCKED_HANDLER = CommandHandler(
    "locks", list_locks
)

application.add_handler(LOCK_HANDLER)
application.add_handler(UNLOCK_HANDLER)
application.add_handler(LOCKTYPES_HANDLER)
application.add_handler(LOCKED_HANDLER)

DEL_LOCKABLES_HANDLER = MessageHandler(
    filters.ALL & filters.ChatType.GROUPS, del_lockables
)
application.add_handler(DEL_LOCKABLES_HANDLER, PERM_GROUP)

__handlers__ = [
    LOCK_HANDLER,
    UNLOCK_HANDLER,
    LOCKTYPES_HANDLER,
    LOCKED_HANDLER,
    (DEL_LOCKABLES_HANDLER, PERM_GROUP),
]
