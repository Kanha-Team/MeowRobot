#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team >.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import math
from pyrogram import filters, errors
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
    Message,
)

from MeowRobot import pbot as app

prefix_cmds = ["/", "!", "."]

__mod_name__ = "Calculator"
__module__ = "Calculator"

__help__ = """
**Calculator 🧮**

**Description:**
Perform calculations directly using the bot with standard and scientific modes.

**Commands:**
❂ `/calc`, `/calculate` or `/calculator` – Open interactive calculator
❂ `/calc <expression>` – Directly calculate mathematical expression
"""

calc_states = {}


def calcExpression(text: str) -> str:
    try:
        if not text or not text.strip():
            return ""
        if len(text) > 100:
            return ""

        expr = (
            text.replace("×", "*")
            .replace("÷", "/")
            .replace("^", "**")
            .replace("π", f"({math.pi})")
            .replace("e", f"({math.e})")
            .replace("√", "math.sqrt")
            .replace("sin", "math.sin")
            .replace("cos", "math.cos")
            .replace("tan", "math.tan")
            .replace("log", "math.log10")
            .replace("ln", "math.log")
        )

        safe_dict = {
            "math": math,
            "abs": abs,
            "round": round,
        }

        res = eval(expr, {"__builtins__": {}}, safe_dict)
        if isinstance(res, (int, float)):
            if isinstance(res, float) and res.is_integer():
                return str(int(res))
            return str(round(res, 8))
        return str(res)
    except (SyntaxError, ZeroDivisionError, TypeError, NameError, ValueError, OverflowError):
        return ""
    except Exception:
        return ""


def calc_btn(uid: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("7", callback_data=f"c|{uid}|7"),
            InlineKeyboardButton("8", callback_data=f"c|{uid}|8"),
            InlineKeyboardButton("9", callback_data=f"c|{uid}|9"),
            InlineKeyboardButton("÷", callback_data=f"c|{uid}|/"),
            InlineKeyboardButton("DEL", callback_data=f"c|{uid}|D"),
        ],
        [
            InlineKeyboardButton("4", callback_data=f"c|{uid}|4"),
            InlineKeyboardButton("5", callback_data=f"c|{uid}|5"),
            InlineKeyboardButton("6", callback_data=f"c|{uid}|6"),
            InlineKeyboardButton("×", callback_data=f"c|{uid}|*"),
            InlineKeyboardButton("AC", callback_data=f"c|{uid}|A"),
        ],
        [
            InlineKeyboardButton("1", callback_data=f"c|{uid}|1"),
            InlineKeyboardButton("2", callback_data=f"c|{uid}|2"),
            InlineKeyboardButton("3", callback_data=f"c|{uid}|3"),
            InlineKeyboardButton("-", callback_data=f"c|{uid}|-"),
            InlineKeyboardButton("(", callback_data=f"c|{uid}|("),
        ],
        [
            InlineKeyboardButton("0", callback_data=f"c|{uid}|0"),
            InlineKeyboardButton(".", callback_data=f"c|{uid}|."),
            InlineKeyboardButton("=", callback_data=f"c|{uid}|="),
            InlineKeyboardButton("+", callback_data=f"c|{uid}|+"),
            InlineKeyboardButton(")", callback_data=f"c|{uid}|)"),
        ],
        [
            InlineKeyboardButton("🧮 Scientific", callback_data=f"c|{uid}|S"),
            InlineKeyboardButton("❌ Close", callback_data=f"c|{uid}|C"),
        ],
    ])


def sci_btn(uid: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("sin", callback_data=f"c|{uid}|sin("),
            InlineKeyboardButton("cos", callback_data=f"c|{uid}|cos("),
            InlineKeyboardButton("tan", callback_data=f"c|{uid}|tan("),
            InlineKeyboardButton("π", callback_data=f"c|{uid}|π"),
            InlineKeyboardButton("DEL", callback_data=f"c|{uid}|D"),
        ],
        [
            InlineKeyboardButton("√", callback_data=f"c|{uid}|√("),
            InlineKeyboardButton("^", callback_data=f"c|{uid}|^"),
            InlineKeyboardButton("log", callback_data=f"c|{uid}|log("),
            InlineKeyboardButton("ln", callback_data=f"c|{uid}|ln("),
            InlineKeyboardButton("AC", callback_data=f"c|{uid}|A"),
        ],
        [
            InlineKeyboardButton("7", callback_data=f"c|{uid}|7"),
            InlineKeyboardButton("8", callback_data=f"c|{uid}|8"),
            InlineKeyboardButton("9", callback_data=f"c|{uid}|9"),
            InlineKeyboardButton("÷", callback_data=f"c|{uid}|/"),
            InlineKeyboardButton("(", callback_data=f"c|{uid}|("),
        ],
        [
            InlineKeyboardButton("4", callback_data=f"c|{uid}|4"),
            InlineKeyboardButton("5", callback_data=f"c|{uid}|5"),
            InlineKeyboardButton("6", callback_data=f"c|{uid}|6"),
            InlineKeyboardButton("×", callback_data=f"c|{uid}|*"),
            InlineKeyboardButton(")", callback_data=f"c|{uid}|)"),
        ],
        [
            InlineKeyboardButton("1", callback_data=f"c|{uid}|1"),
            InlineKeyboardButton("2", callback_data=f"c|{uid}|2"),
            InlineKeyboardButton("3", callback_data=f"c|{uid}|3"),
            InlineKeyboardButton("-", callback_data=f"c|{uid}|-"),
            InlineKeyboardButton("e", callback_data=f"c|{uid}|e"),
        ],
        [
            InlineKeyboardButton("0", callback_data=f"c|{uid}|0"),
            InlineKeyboardButton(".", callback_data=f"c|{uid}|."),
            InlineKeyboardButton("=", callback_data=f"c|{uid}|="),
            InlineKeyboardButton("+", callback_data=f"c|{uid}|+"),
            InlineKeyboardButton("%", callback_data=f"c|{uid}|%"),
        ],
        [
            InlineKeyboardButton("🔢 Basic", callback_data=f"c|{uid}|B"),
            InlineKeyboardButton("❌ Close", callback_data=f"c|{uid}|C"),
        ],
    ])


@app.on_message(filters.command(["calc", "calculate", "calculator"], prefix_cmds) & ~filters.forwarded, group=25)
async def calculate_handler(client, message: Message):
    if not message.from_user:
        return

    uid = message.from_user.id
    init_text = ""
    display_text = "0"

    if len(message.command) > 1:
        expr = "".join(message.command[1:])
        res = calcExpression(expr)
        if res:
            init_text = res
            display_text = res
        else:
            init_text = expr
            display_text = expr

    calc_states[uid] = {"text": init_text, "mode": "basic"}

    await message.reply_text(
        text=f"```\n{display_text}\n```",
        reply_markup=calc_btn(uid),
        disable_web_page_preview=True,
        quote=True,
    )


@app.on_callback_query(filters.regex(r"^c\|"))
async def calc_cb(client, query: CallbackQuery):
    try:
        parts = query.data.split("|", 2)
        if len(parts) < 3:
            return await query.answer()

        uid = int(parts[1])
        data = parts[2]

        if query.from_user.id != uid:
            return await query.answer("⚠️ This is not your calculator!", show_alert=True)

        if uid not in calc_states:
            calc_states[uid] = {"text": "", "mode": "basic"}

        state = calc_states[uid]
        text = state["text"]

        if data == "A":
            text = ""
        elif data == "D":
            if text:
                for fn in ("sin(", "cos(", "tan(", "log(", "ln(", "√("):
                    if text.endswith(fn):
                        text = text[:-len(fn)]
                        break
                else:
                    text = text[:-1]
        elif data == "=":
            result = calcExpression(text)
            text = result if result else ""
        elif data == "C":
            calc_states.pop(uid, None)
            await query.message.delete()
            return await query.answer()
        elif data == "S":
            state["mode"] = "scientific"
        elif data == "B":
            state["mode"] = "basic"
        else:
            text += data

        state["text"] = text
        markup = sci_btn(uid) if state["mode"] == "scientific" else calc_btn(uid)

        try:
            display = f"```\n{text if text else '0'}\n```"
            await query.message.edit_text(
                text=display,
                reply_markup=markup,
                disable_web_page_preview=True,
            )
        except errors.MessageNotModified:
            pass

        await query.answer()

    except Exception:
        await query.answer("Error!", show_alert=False)
