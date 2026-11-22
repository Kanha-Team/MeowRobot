#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

class Config(object):
    LOGGER = True

    # Get this value from my.telegram.org/apps
    API_ID = 6
    API_HASH = "eb06d4abfb49dc3eeb1aeb98ae0f581e"

    CASH_API_KEY = ""  # Get this value for currency converter from https://www.alphavantage.co/support/#api-key

    DATABASE_URL = ""  # A sql database url from elephantsql.com

    EVENT_LOGS = ()  # Event logs channel to note down important bot level events

    MONGO_DB_URI = ""  # Get ths value from cloud.mongodb.com

    # Telegraph link of the image which will be shown at start command.
    START_IMG = "https://files.catbox.moe/4ntzos.jpg"

    SUPPORT_CHAT = "MeowClone"  # Your Telegram support group chat username where your users will go and bother you
    SUPPORT_CHANNEL = "MeowCloner"  # Your Telegram channel username for bot updates

    TOKEN = ""  # Get bot token from @BotFather on Telegram

    TIME_API_KEY = ""  # Get this value from https://timezonedb.com/api

    CHATBOT_API_URL = "https://chatbot.riteshyt.in/api/chat"
    CHATBOT_API_KEY = "ritesh-8179b3a5da99f300be2d50e1e9789729"
    GEMINI_API_KEY = "AQ.Ab8RN6JUjDD0qAWnbMf2lG7vmiToQqmX7Xi1-MMgyH45kIJCtg"

    OWNER_ID = 8617644501  # User id of your telegram account (Must be integer)

    # Optional fields
    NSFW_LOG_CHANNEL = None
    NSFW_STORAGE = None
    BL_CHATS = []  # List of groups that you want blacklisted.
    DRAGONS = []  # User id of sudo users
    DEV_USERS = []  # User id of dev users
    DEMONS = []  # User id of support users
    TIGERS = []  # User id of tiger users
    WOLVES = []  # User id of whitelist users

    ALLOW_CHATS = True
    ALLOW_EXCL = True
    DEL_CMDS = True
    INFOPIC = True
    LOAD = []
    NO_LOAD = []
    STRICT_GBAN = True
    TEMP_DOWNLOAD_DIRECTORY = "./"
    WORKERS = 8


class Production(Config):
    LOGGER = True


class Development(Config):
    LOGGER = True
