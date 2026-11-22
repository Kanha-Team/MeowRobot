#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

from telegram import Message
from telegram.ext.filters import MessageFilter

from MeowRobot import DEMONS, DEV_USERS, DRAGONS


class CustomFilters(object):
    class _Supporters(MessageFilter):
        def filter(self, message: Message):
            return bool(message.from_user and message.from_user.id in DEMONS)

    support_filter = _Supporters()

    class Sudoers(MessageFilter):
        def filter(self, message: Message):
            return bool(message.from_user and message.from_user.id in DRAGONS)

    sudo_filter = Sudoers()

    class Developers(MessageFilter):
        def filter(self, message: Message):
            return bool(message.from_user and message.from_user.id in DEV_USERS)

    dev_filter = Developers()

    class _MimeType(MessageFilter):
        def __init__(self, mimetype):
            super().__init__()
            self.mime_type = mimetype
            self.name = "CustomFilters.mime_type({})".format(self.mime_type)

        def filter(self, message: Message):
            return bool(
                message.document and message.document.mime_type == self.mime_type,
            )

    mime_type = _MimeType

    class _HasText(MessageFilter):
        def filter(self, message: Message):
            return bool(
                message.text
                or message.sticker
                or message.photo
                or message.document
                or message.video,
            )

    has_text = _HasText()
