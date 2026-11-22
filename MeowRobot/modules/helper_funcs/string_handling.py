#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import html
import re
import time
from typing import Dict, List

import bleach
import markdown2
from emoji import unicode_codes
from telegram import MessageEntity
from telegram.helpers import escape_markdown

# NOTE: the url \ escape may cause double escape
# match * (bold) (don't escape if in url)
# match _ (italics) (don't escape if in url]
# match ` (code)
# match []() (markdown link)
# else, escape *, _, `, and [
MATCH_MD = re.compile(
    r"\*(.*?)\*|"
    r"_(.*?)_|"
    r"`(.*?)`|"
    r"(?<!\\)(\[.*?\])(\(.*?\))|"
    r"(?P<esc>[*_`\[])"
)

# regex to find []() links -> hyperlinks/buttons
LINK_REGEX = re.compile(r"(?<!\\)\[.+?\]\((.*?)\)")
BTN_URL_REGEX = re.compile(r"(\[([^\[]+?)\]\(buttonurl:(?:/{0,2})(.+?)(:same)?\))")
_EMOJI_REGEXP = None


def _selective_escape(to_parse: str) -> str:
    """
    Escape all invalid markdown

    :param to_parse: text to escape
    :return: valid markdown string
    """
    offset = 0  # offset to be used as adding a \ character causes the string to shift
    for match in MATCH_MD.finditer(to_parse):
        if match.group("esc"):
            ent_start = match.start()
            to_parse = (
                to_parse[: ent_start + offset] + "\\" + to_parse[ent_start + offset :]
            )
            offset += 1
    return to_parse


# This is a fun one.
def get_emoji_regexp():
    global _EMOJI_REGEXP
    if _EMOJI_REGEXP is None:
        emojis = sorted(unicode_codes.EMOJI_DATA, key=len, reverse=True)
        pattern = "(" + "|".join(re.escape(u) for u in emojis) + ")"
        _EMOJI_REGEXP = re.compile(pattern)
    return _EMOJI_REGEXP


def _calc_emoji_offset(to_calc) -> int:
    # Get all emoji in text.
    emoticons = get_emoji_regexp().finditer(to_calc)
    # Check the utf16 length of the emoji to determine the offset it caused.
    # Normal, 1 character emoji don't affect; hence sub 1.
    # special, eg with two emoji characters (eg face, and skin col) will have length 2, so by subbing one we
    # know we'll get one extra offset,
    return sum(len(e.group(0).encode("utf-16-le")) // 2 - 1 for e in emoticons)


def markdown_parser(
    txt: str, entities: Dict[MessageEntity, str] = None, offset: int = 0
) -> str:
    """
    Parse a string, converting Telegram entities to HTML tags.
    Supports nested entities and modern Telegram formatting.

    :param txt: text to parse
    :param entities: dict of message entities in text
    :param offset: message offset (UTF-16)
    :return: HTML string
    """
    if not txt:
        return ""
    if not entities:
        return html.escape(txt)

    # Convert UTF-16 text to a list of characters for easier indexing
    # Telegram offsets are based on UTF-16 code units.
    utf16_txt = txt.encode("utf-16-le")
    utf16_chars = [utf16_txt[i : i + 2] for i in range(0, len(utf16_txt), 2)]

    def _parse(start_offset: int, end_offset: int, sub_entities: List[MessageEntity]) -> str:
        res = ""
        current_offset = start_offset

        while current_offset < end_offset:
            # Find entities that start at current_offset
            ent = next((e for e in sub_entities if e.offset == current_offset), None)

            if ent:
                # Find all entities nested within this one
                inner_entities = [
                    e
                    for e in sub_entities
                    if e != ent
                    and e.offset >= ent.offset
                    and e.offset + e.length <= ent.offset + ent.length
                ]

                inner_text = _parse(ent.offset, ent.offset + ent.length, inner_entities)

                if ent.type == MessageEntity.BOLD:
                    res += f"<b>{inner_text}</b>"
                elif ent.type == MessageEntity.ITALIC:
                    res += f"<i>{inner_text}</i>"
                elif ent.type == MessageEntity.UNDERLINE:
                    res += f"<u>{inner_text}</u>"
                elif ent.type == MessageEntity.STRIKETHROUGH:
                    res += f"<s>{inner_text}</s>"
                elif ent.type == MessageEntity.SPOILER:
                    res += f'<span class="tg-spoiler">{inner_text}</span>'
                elif ent.type == MessageEntity.BLOCKQUOTE:
                    res += f"<blockquote>{inner_text}</blockquote>"
                elif ent.type == MessageEntity.EXPANDABLE_BLOCKQUOTE:
                    res += f"<blockquote expandable>{inner_text}</blockquote>"
                elif ent.type == MessageEntity.CODE:
                    res += f"<code>{inner_text}</code>"
                elif ent.type == MessageEntity.PRE:
                    res += f"<pre>{inner_text}</pre>"
                elif ent.type == MessageEntity.CUSTOM_EMOJI:
                    res += f'<tg-emoji emoji-id="{ent.custom_emoji_id}">{inner_text}</tg-emoji>'
                elif ent.type == MessageEntity.TEXT_LINK:
                    if ent.url.startswith("buttonurl:"):
                        res += f"[{inner_text}]({ent.url})"
                    else:
                        res += f'<a href="{html.escape(ent.url)}">{inner_text}</a>'
                elif ent.type == MessageEntity.URL:
                    # Avoid double-linking if it's already part of a Markdown link
                    # (This is a simplified check)
                    res += f'<a href="{inner_text}">{inner_text}</a>'
                else:
                    res += inner_text

                current_offset += ent.length
                # Remove this entity and its children from further processing in this loop
                sub_entities = [e for e in sub_entities if e.offset >= current_offset]
            else:
                # Append raw character
                char_data = utf16_chars[current_offset]
                unit = int.from_bytes(char_data, "little")
                if 0xD800 <= unit <= 0xDBFF and current_offset + 1 < end_offset:
                    # High surrogate, grab the low surrogate too
                    char_data += utf16_chars[current_offset + 1]
                    char = char_data.decode("utf-16-le")
                    current_offset += 2
                else:
                    char = char_data.decode("utf-16-le")
                    current_offset += 1
                res += html.escape(char)

        return res

    # Entities from Telegram are relative to the start of the message.
    # We adjust them by the provided offset.
    adjusted_entities = []
    for ent in entities.keys():
        new_ent = MessageEntity(
            type=ent.type,
            offset=ent.offset + offset,
            length=ent.length,
            url=ent.url,
            user=ent.user,
            language=ent.language,
            custom_emoji_id=ent.custom_emoji_id,
        )
        if new_ent.offset >= 0:
            adjusted_entities.append(new_ent)

    # Sort by offset (ascending) then length (descending) to handle nesting
    adjusted_entities.sort(key=lambda x: (x.offset, -x.length))

    return _parse(0, len(utf16_chars), adjusted_entities)


def button_markdown_parser(
    txt: str, entities: Dict[MessageEntity, str] = None, offset: int = 0
) -> (str, List):
    markdown_note = markdown_parser(txt, entities, offset)
    prev = 0
    note_data = ""
    buttons = []
    for match in BTN_URL_REGEX.finditer(markdown_note):
        # Check if btnurl is escaped
        n_escapes = 0
        to_check = match.start(1) - 1
        while to_check > 0 and markdown_note[to_check] == "\\":
            n_escapes += 1
            to_check -= 1

        # if even, not escaped -> create button
        if n_escapes % 2 == 0:
            # create a thruple with button label, url, and newline status
            # unescape label in case it was escaped by markdown_parser
            label = html.unescape(match.group(2))
            buttons.append((label, match.group(3), bool(match.group(4))))
            note_data += markdown_note[prev : match.start(1)]
            prev = match.end(1)
        # if odd, escaped -> move along
        else:
            note_data += markdown_note[prev:to_check]
            prev = match.start(1) - 1
    else:
        note_data += markdown_note[prev:]

    return note_data, buttons


def escape_invalid_curly_brackets(text: str, valids: List[str]) -> str:
    new_text = ""
    idx = 0
    while idx < len(text):
        if text[idx] == "{":
            if idx + 1 < len(text) and text[idx + 1] == "{":
                idx += 2
                new_text += "{{{{"
                continue
            else:
                success = False
                v_found = ""
                for v in valids:
                    if text[idx:].startswith("{" + v + "}"):
                        success = True
                        v_found = v
                        break
                if success:
                    new_text += text[idx : idx + len(v_found) + 2]
                    idx += len(v_found) + 2
                    continue
                else:
                    new_text += "{{"

        elif text[idx] == "}":
            if idx + 1 < len(text) and text[idx + 1] == "}":
                idx += 2
                new_text += "}}}}"
                continue
            else:
                new_text += "}}"

        else:
            new_text += text[idx]
        idx += 1

    return new_text


SMART_OPEN = "“"
SMART_CLOSE = "”"
START_CHAR = ("'", '"', SMART_OPEN)


def split_quotes(text: str) -> List:
    if not any(text.startswith(char) for char in START_CHAR):
        return text.split(None, 1)
    counter = 1  # ignore first char -> is some kind of quote
    while counter < len(text):
        if text[counter] == "\\":
            counter += 1
        elif text[counter] == text[0] or (
            text[0] == SMART_OPEN and text[counter] == SMART_CLOSE
        ):
            break
        counter += 1
    else:
        return text.split(None, 1)

    # 1 to avoid starting quote, and counter is exclusive so avoids ending
    key = remove_escapes(text[1:counter].strip())
    # index will be in range, or `else` would have been executed and returned
    rest = text[counter + 1 :].strip()
    if not key:
        key = text[0] + text[0]
    return list(filter(None, [key, rest]))


def remove_escapes(text: str) -> str:
    res = ""
    is_escaped = False
    for counter in range(len(text)):
        if is_escaped:
            res += text[counter]
            is_escaped = False
        elif text[counter] == "\\":
            is_escaped = True
        else:
            res += text[counter]
    return res


def escape_chars(text: str, to_escape: List[str]) -> str:
    to_escape.append("\\")
    new_text = ""
    for x in text:
        if x in to_escape:
            new_text += "\\"
        new_text += x
    return new_text


async def extract_time(message, time_val):
    if any(time_val.endswith(unit) for unit in ("m", "h", "d")):
        unit = time_val[-1]
        time_num = time_val[:-1]  # type: str
        if not time_num.isdigit():
            await message.reply_text("Invalid time amount specified.")
            return ""

        if unit == "m":
            bantime = int(time.time() + int(time_num) * 60)
        elif unit == "h":
            bantime = int(time.time() + int(time_num) * 60 * 60)
        elif unit == "d":
            bantime = int(time.time() + int(time_num) * 24 * 60 * 60)
        else:
            # how even...?
            return ""
        return bantime
    else:
        await message.reply_text(
            "Invalid time type specified. Expected m,h, or d, got: {}".format(
                time_val[-1]
            )
        )
        return ""


def markdown_to_html(text):
    if not text:
        return ""

    # Check if the unescaped text looks like HTML (contains our tags).
    # This ensures we detect tags even if they are currently escaped.
    unescaped = html.unescape(text)
    if any(
        tag in unescaped
        for tag in [
            "<b>",
            "<i>",
            "<u>",
            "<s>",
            "<code>",
            "<pre>",
            "<tg-emoji",
            "<a ",
            "<blockquote>",
            "<span",
        ]
    ):
        # Use the unescaped version to prevent double-escaping of & when bleach.clean runs
        text = unescaped
        # Just sanitize it
        return bleach.clean(
            text,
            tags=[
                "strong",
                "em",
                "a",
                "code",
                "pre",
                "strike",
                "u",
                "tg-emoji",
                "b",
                "i",
                "s",
                "blockquote",
                "span",
            ],
            attributes={
                "a": ["href"],
                "tg-emoji": ["emoji-id"],
                "blockquote": ["expandable"],
                "span": ["class"],
            },
            strip=False,
        ).strip()

    # Legacy/Manual markdown support
    text = text.replace("*", "**")
    text = text.replace("`", "```")
    text = text.replace("~", "~~")

    _html = markdown2.markdown(text, extras=["strike"])
    
    # markdown2 wraps in <p>, which Telegram doesn't like
    _html = _html.replace("<p>", "").replace("</p>", "\n")

    return bleach.clean(
        _html,
        tags=[
            "strong",
            "em",
            "a",
            "code",
            "pre",
            "strike",
            "u",
            "tg-emoji",
            "b",
            "i",
            "s",
            "blockquote",
            "span",
        ],
        attributes={
            "a": ["href"],
            "tg-emoji": ["emoji-id"],
            "blockquote": ["expandable"],
            "span": ["class"],
        },
        strip=True,
    ).strip()
