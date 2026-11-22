#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import time
from collections import defaultdict, deque
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters, BaseHandler

import MeowRobot.modules.sql.blacklistusers_sql as sql
from MeowRobot import ALLOW_EXCL, DEMONS, DEV_USERS, DRAGONS, TIGERS, WOLVES

if ALLOW_EXCL:
    CMD_STARTERS = ("/", "!")
else:
    CMD_STARTERS = ("/",)


class AntiSpam:
    def __init__(self):
        self.whitelist = (
            list(DEV_USERS or [])
            + list(DRAGONS or [])
            + list(WOLVES or [])
            + list(DEMONS or [])
            + list(TIGERS or [])
        )
        # (max_requests, window_seconds)
        self.limits = [(6, 15), (20, 60), (100, 3600), (1000, 86400)]
        self.user_history = defaultdict(deque)

    def check_user(self, user):
        """
        Return True if user is to be ignored else False
        """
        if user in self.whitelist:
            return False
        now = time.time()
        history = self.user_history[user]
        while history and now - history[0] > 86400:
            history.popleft()

        for max_calls, window in self.limits:
            count = sum(1 for t in history if now - t <= window)
            if count >= max_calls:
                return True

        history.append(now)
        return False


SpamChecker = AntiSpam()
MessageHandlerChecker = AntiSpam()


class CustomCommandHandler(CommandHandler):
    def __init__(self, command, callback, admin_ok=False, allow_edit=False, **kwargs):
        super().__init__(command, callback, **kwargs)
        self.allow_edit = allow_edit

    def check_update(self, update):
        if isinstance(update, Update) and update.effective_message:
            message = update.effective_message

            if not self.allow_edit and (update.edited_message or update.edited_channel_post):
                return None

            try:
                user_id = update.effective_user.id
            except:
                user_id = None

            if user_id:
                if sql.is_user_blacklisted(user_id):
                    return None

            if message.text and len(message.text) > 1:
                fst_word = message.text.split(None, 1)[0]
                if len(fst_word) > 1 and any(
                    fst_word.startswith(start) for start in CMD_STARTERS
                ):
                    command_parts = fst_word[1:].split("@")

                    if user_id == 1087968824:
                        user_id = update.effective_chat.id

                    if command_parts[0].lower() not in [c.lower() for c in self.commands]:
                        return None

                    if len(command_parts) > 1 and command_parts[1].lower() != update.get_bot().username.lower():
                        return None

                    if SpamChecker.check_user(user_id):
                        return None

                    return super().check_update(update)


class CustomMessageHandler(MessageHandler):
    def __init__(self, filters, callback, friendly="", allow_edit=False, **kwargs):
        super().__init__(filters, callback, **kwargs)
        self.allow_edit = allow_edit

    def check_update(self, update):
        if isinstance(update, Update) and update.effective_message:
            if not self.allow_edit and (update.edited_message or update.edited_channel_post):
                return None
            return super().check_update(update)
