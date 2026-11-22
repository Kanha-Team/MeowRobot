#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import unicodedata
from math import ceil
from typing import Dict, List
from uuid import uuid4

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InputTextMessageContent,
    Update,
)
from telegram.constants import ParseMode
from telegram.error import TelegramError
from telegram.ext import ContextTypes

from MeowRobot import NO_LOAD, OWNER_ID


NORM_TO_ASCII = {
    'ᴀ': 'a', 'ʙ': 'b', 'ᴄ': 'c', 'ᴅ': 'd', 'ᴇ': 'e', 'ꜰ': 'f', 'ғ': 'f', 'ɢ': 'g',
    'ʜ': 'h', 'ɪ': 'i', 'ᴊ': 'j', 'ᴋ': 'k', 'ʟ': 'l', 'ᴍ': 'm', 'ɴ': 'n', 'ᴏ': 'o',
    'ᴘ': 'p', 'ǫ': 'q', 'ʀ': 'r', 's': 's', 'ᴛ': 't', 'ᴜ': 'u', 'ᴠ': 'v', 'ᴡ': 'w',
    'х': 'x', 'ʏ': 'y', 'ᴢ': 'z',
    'ᴧ': 'a', 'є': 'e', 'ϻ': 'm', 'η': 'n', 'σ': 'o', 'ꝛ': 'r', 'υ': 'u',
}


def to_alpha_key(text: str) -> str:
    clean_text = (
        (text or "")
        .replace("\u200b", "")
        .replace("\ufeff", "")
        .replace("ǫ", "q")
    )
    decomposed = unicodedata.normalize("NFKD", clean_text)
    result = []
    for c in decomposed:
        low = c.lower()
        result.append(NORM_TO_ASCII.get(low, low))
    clean = "".join(result)
    return "".join(c for c in clean if c.isalnum() or c in ("-", "_")).strip().lower()


class EqInlineKeyboardButton(InlineKeyboardButton):
    def __eq__(self, other):
        return to_alpha_key(self.text) == to_alpha_key(getattr(other, "text", ""))

    def __lt__(self, other):
        return to_alpha_key(self.text) < to_alpha_key(getattr(other, "text", ""))

    def __gt__(self, other):
        return to_alpha_key(self.text) > to_alpha_key(getattr(other, "text", ""))


def split_message(msg: str) -> List[str]:
    # PTB v20+ doesn't have MAX_MESSAGE_LENGTH constant in telegram, it's 4096
    MAX_MESSAGE_LENGTH = 4096
    if len(msg) < MAX_MESSAGE_LENGTH:
        return [msg]

    lines = msg.splitlines(True)
    small_msg = ""
    result = []
    for line in lines:
        if len(small_msg) + len(line) < MAX_MESSAGE_LENGTH:
            small_msg += line
        else:
            result.append(small_msg)
            small_msg = line
    else:
        # Else statement at the end of the for loop, so append the leftover string.
        result.append(small_msg)

    return result


KANHA_FONT_MAP = {
    'a': 'ᴧ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'є', 'f': 'ғ', 'g': 'ɢ',
    'h': 'ʜ', 'i': 'ɪ', 'j': 'ᴊ', 'k': 'ᴋ', 'l': 'ʟ', 'm': 'ϻ', 'n': 'η',
    'o': 'σ', 'p': 'ᴘ', 'q': 'ǫ', 'r': 'ꝛ', 's': 's', 't': 'ᴛ', 'u': 'υ',
    'v': 'ᴠ', 'w': 'ᴡ', 'x': 'х', 'y': 'ʏ', 'z': 'ᴢ',
    'A': 'ᴧ', 'B': 'ʙ', 'C': 'ᴄ', 'D': 'ᴅ', 'E': 'є', 'F': 'ғ', 'G': 'ɢ',
    'H': 'ʜ', 'I': 'ɪ', 'J': 'ᴊ', 'K': 'ᴋ', 'L': 'ʟ', 'M': 'ϻ', 'N': 'η',
    'O': 'σ', 'P': 'ᴘ', 'Q': 'ǫ', 'R': 'ꝛ', 'S': 's', 'T': 'ᴛ', 'U': 'υ',
    'V': 'ᴠ', 'W': 'ᴡ', 'X': 'х', 'Y': 'ʏ', 'Z': 'ᴢ',
    'ᴀ': 'ᴧ', 'ʙ': 'ʙ', 'ᴄ': 'ᴄ', 'ᴅ': 'ᴅ', 'ᴇ': 'є', 'ꜰ': 'ғ', 'ғ': 'ғ', 'ɢ': 'ɢ',
    'ʜ': 'ʜ', 'ɪ': 'ɪ', 'ᴊ': 'ᴊ', 'ᴋ': 'ᴋ', 'ʟ': 'ʟ', 'ᴍ': 'ϻ', 'ɴ': 'η',
    'ᴏ': 'σ', 'ᴘ': 'ᴘ', 'ǫ': 'ǫ', 'ʀ': 'ꝛ', 'ᴛ': 'ᴛ', 'ᴜ': 'υ', 'ᴠ': 'ᴠ',
    'ᴡ': 'ᴡ', 'ʏ': 'ʏ', 'ᴢ': 'ᴢ',
}

# Support mathematical bold letters (e.g. 𝐇, 𝐖 in couples module)
for _i in range(26):
    KANHA_FONT_MAP[chr(0x1D400 + _i)] = KANHA_FONT_MAP[chr(ord('A') + _i)]
    KANHA_FONT_MAP[chr(0x1D41A + _i)] = KANHA_FONT_MAP[chr(ord('a') + _i)]


def to_kanha_font(text: str) -> str:
    clean_text = (text or "").replace("\u200b", "").replace("\ufeff", "")
    return "".join(KANHA_FONT_MAP.get(c, c) for c in clean_text)


def paginate_modules(page_n: int, module_dict: Dict, prefix, chat=None) -> List:
    sorted_mods = sorted(
        module_dict.values(),
        key=lambda x: to_alpha_key(getattr(x, "__mod_name__", ""))
    )
    if not chat:
        modules = [
            EqInlineKeyboardButton(
                to_kanha_font(x.__mod_name__),
                callback_data="{}_module({})".format(
                    prefix, x.__mod_name__.lower()
                ),
            )
            for x in sorted_mods
        ]
    else:
        modules = [
            EqInlineKeyboardButton(
                to_kanha_font(x.__mod_name__),
                callback_data="{}_module({},{})".format(
                    prefix, chat, x.__mod_name__.lower()
                ),
            )
            for x in sorted_mods
        ]

    pairs = [modules[i * 3 : (i + 1) * 3] for i in range((len(modules) + 3 - 1) // 3)]

    round_num = len(modules) / 3
    calc = len(modules) - round(round_num)
    if calc in [1, 2]:
        pairs.append((modules[-1],))

    max_num_pages = ceil(len(pairs) / 4)
    modulo_page = page_n % max_num_pages

    # can only have a certain amount of buttons side by side
    if len(pairs) > 3:
        pairs = pairs[modulo_page * 4 : 4 * (modulo_page + 1)] + [
            [
                EqInlineKeyboardButton(
                    "◁", callback_data="{}_prev({})".format(prefix, modulo_page)
                ),
                EqInlineKeyboardButton("• ʜσϻє •", callback_data="MeowRoBot_back"),
                EqInlineKeyboardButton(
                    "▷", callback_data="{}_next({})".format(prefix, modulo_page)
                ),
            ]
        ]

    else:
        pairs += [[EqInlineKeyboardButton("• ʙᴧᴄᴋ •", callback_data="MeowRoBot_back")]]

    return pairs


def article(
    title: str = "",
    description: str = "",
    message_text: str = "",
    thumb_url: str = None,
    reply_markup: InlineKeyboardMarkup = None,
    disable_web_page_preview: bool = False,
) -> InlineQueryResultArticle:
    return InlineQueryResultArticle(
        id=str(uuid4()),
        title=title,
        description=description,
        thumb_url=thumb_url,
        input_message_content=InputTextMessageContent(
            message_text=message_text,
            disable_web_page_preview=disable_web_page_preview,
        ),
        reply_markup=reply_markup,
    )


async def send_to_list(
    bot, send_to: list, message: str, markdown=False, html=False
) -> None:
    if html and markdown:
        raise Exception("Can only send with either markdown or HTML!")
    for user_id in set(send_to):
        try:
            if markdown:
                await bot.send_message(user_id, message, parse_mode=ParseMode.MARKDOWN)
            elif html:
                await bot.send_message(user_id, message, parse_mode=ParseMode.HTML)
            else:
                await bot.send_message(user_id, message)
        except TelegramError:
            pass  # ignore users who fail


def build_keyboard(buttons):
    keyb = []
    for btn in buttons:
        url = btn.url
        if url.startswith("@"):
            url = "https://t.me/{}".format(url[1:])
        if btn.same_line and keyb:
            keyb[-1].append(InlineKeyboardButton(btn.name, url=url))
        else:
            keyb.append([InlineKeyboardButton(btn.name, url=url)])

    return keyb


def revert_buttons(buttons):
    res = ""
    for btn in buttons:
        if btn.same_line:
            res += "\n[{}](buttonurl://{}:same)".format(btn.name, btn.url)
        else:
            res += "\n[{}](buttonurl://{})".format(btn.name, btn.url)

    return res


def build_keyboard_parser(bot, chat_id, buttons):
    keyb = []
    for btn in buttons:
        url = btn.url
        if url == "{rules}":
            url = "http://t.me/{}?start={}".format(bot.username, chat_id)
        if url.startswith("@"):
            url = "https://t.me/{}".format(url[1:])
        if btn.same_line and keyb:
            keyb[-1].append(InlineKeyboardButton(btn.name, url=url))
        else:
            keyb.append([InlineKeyboardButton(btn.name, url=url)])

    return keyb


def build_keyboard_alternate(buttons):
    keyb = []
    for btn in buttons:
        url = btn[1]
        if url.startswith("@"):
            url = "https://t.me/{}".format(url[1:])
        if btn[2] and keyb:
            keyb[-1].append(InlineKeyboardButton(btn[0], url=url))
        else:
            keyb.append([InlineKeyboardButton(btn[0], url=url)])

    return keyb


def is_module_loaded(name):
    return name not in NO_LOAD
