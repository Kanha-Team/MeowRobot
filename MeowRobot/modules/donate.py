#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team >.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import hashlib
import time
from datetime import datetime
from html import escape

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
    Update,
)
from telegram.constants import ParseMode
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    PreCheckoutQueryHandler,
    filters,
)

from MeowRobot import (
    BOT_NAME,
    LOGGER,
    OWNER_ID,
    START_IMG,
    SUPPORT_CHAT,
    application,
)
from MeowRobot.modules.disable import DisableAbleCommandHandler

__mod_name__ = "Donate"

__help__ = f"""
*Donations & Telegram Stars 💝*

Support the bot's development, maintenance, and server uptime!

» /donate : Information about donating to support {BOT_NAME}.
» /pay `<amount>` : Donate via Telegram Stars (e.g. `/pay 10` or default `/pay 5`).
» /stars : Check current Telegram Stars balance (Bot Owner only).
"""

REFUND_CACHE = {}


def short_key(user_id: int, charge_id: str) -> str:
    return hashlib.sha1(f"{user_id}:{charge_id}".encode()).hexdigest()[:12]


DT_TEXT = f"""🙏 **Thank you for considering donating to help keep {BOT_NAME} alive and functioning!**

⚫ You can also donate Telegram Stars directly using the `/pay` command.
🙋 For queries or feedback, please reach out at @{SUPPORT_CHAT}."""


async def donate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [
        [
            InlineKeyboardButton("sυᴘᴘσꝛᴛ", url=f"https://t.me/{SUPPORT_CHAT}"),
            InlineKeyboardButton("⭐ ᴅσηᴧᴛє sᴛᴧꝛs", callback_data="donate_stars_prompt"),
        ]
    ]
    if START_IMG:
        try:
            await update.effective_message.reply_photo(
                photo=START_IMG,
                caption=DT_TEXT,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(buttons),
            )
            return
        except Exception:
            pass

    await update.effective_message.reply_text(
        text=DT_TEXT,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def donate_stars_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "⭐ **To donate Telegram Stars:**\n\n"
        "Use `/pay <amount>`\n\n"
        "**Examples:**\n"
        "• `/pay` — Donates 5 Stars\n"
        "• `/pay 10` — Donates 10 Stars\n"
        "• `/pay 50` — Donates 50 Stars\n"
        "• `/pay 100` — Donates 100 Stars",
        parse_mode=ParseMode.MARKDOWN,
    )


async def pay_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    amount = 5
    if args:
        if args[0].isdigit() and int(args[0]) > 0:
            amount = int(args[0])
        else:
            await update.effective_message.reply_text(
                "⚠️ Invalid amount. Use like: `/pay 10`",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

    user = update.effective_user
    try:
        await context.bot.send_invoice(
            chat_id=update.effective_chat.id,
            title="Donate 💝",
            description=(
                f"♻️ 💖 Support our mission and keep {BOT_NAME} alive! "
                f"Every donation makes a difference. 🌟 "
                f"Click to contribute and make an impact! 🙏✨ {amount} ⭐ via Telegram Stars."
            ),
            payload=f"star_payment_{user.id}_{int(time.time())}",
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice(label="♻️ Donation", amount=amount)],
        )
    except Exception as e:
        await update.effective_message.reply_text(
            f"❌ Failed to send invoice:\n<code>{escape(str(e))}</code>",
            parse_mode=ParseMode.HTML,
        )


async def pre_checkout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    try:
        await query.answer(ok=True)
        LOGGER.info(f"[✅ PreCheckout received from] {query.from_user.id}")
    except Exception as e:
        LOGGER.error(f"[❌ PreCheckout Error] {e}")
        try:
            await query.answer(ok=False, error_message="Payment failed, please try again.")
        except Exception:
            pass


async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    payment = message.successful_payment
    user = update.effective_user
    safe_name = escape(user.first_name or "User")
    html_mention = f'<a href="tg://user?id={user.id}">{safe_name}</a>'
    key = short_key(user.id, payment.telegram_payment_charge_id)
    REFUND_CACHE[key] = (user.id, payment.telegram_payment_charge_id)

    # Thank you reply to user
    await message.reply_text(
        (
            "✅ <b>Payment Successful!</b>\n"
            f"Thanks {html_mention} for your generous support! 🙏✨\n\n"
            f"💳 <b>Amount:</b> {payment.total_amount} {escape(payment.currency)} (⭐ Stars)\n"
            f"🧾 <b>Charge ID:</b> <code>{escape(payment.telegram_payment_charge_id)}</code>"
        ),
        parse_mode=ParseMode.HTML,
    )

    # Notification to bot owner
    try:
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=(
                "💰 <b>New Payment Received!</b>\n"
                f"👤 <b>From:</b> {html_mention} [<code>{user.id}</code>]\n"
                f"⭐ <b>Amount:</b> {payment.total_amount} {escape(payment.currency)}\n"
                f"🧾 <b>Charge ID:</b> <code>{escape(payment.telegram_payment_charge_id)}</code>"
            ),
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("💸 Refund", callback_data=f"refund|{key}")
                ]
            ]),
        )
    except Exception as e:
        LOGGER.error(f"[❌ Refund Notify Error] {e}")


async def refund_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id != OWNER_ID:
        await query.answer("🚫 Only the bot owner can refund!", show_alert=True)
        return
    try:
        _, key = query.data.split("|", 1)
        if key not in REFUND_CACHE:
            await query.answer("❌ Refund data expired or already refunded!", show_alert=True)
            return
        user_id, charge_id = REFUND_CACHE.pop(key)
        await context.bot.refund_star_payment(
            user_id=user_id,
            telegram_payment_charge_id=charge_id,
        )
        await query.message.edit_text("✅ <b>Refund successful!</b>", parse_mode=ParseMode.HTML)
        await query.answer("Refund successful!", show_alert=True)
    except Exception as e:
        await query.message.edit_text(
            f"❌ <b>Refund failed:</b>\n<code>{escape(str(e))}</code>",
            parse_mode=ParseMode.HTML,
        )
        await query.answer(f"Refund failed: {str(e)}", show_alert=True)


async def stars_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != OWNER_ID:
        await update.effective_message.reply_text("🚫 This command is owner-only!")
        return
    try:
        txs = await context.bot.get_star_transactions()
        balance = sum(t.amount for t in txs.transactions) if txs and txs.transactions else 0
        refreshed_at = datetime.now().strftime("%H:%M:%S")
        await update.effective_message.reply_text(
            f"⭐ <b>Current Stars Balance</b>\n\n"
            f"💰 <b>{balance}</b> Stars\n"
            f"⏰ Last checked: <i>{refreshed_at} UTC</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_stars")]
            ]),
        )
    except Exception as e:
        await update.effective_message.reply_text(
            f"❌ Could not fetch stars balance:\n<code>{escape(str(e))}</code>",
            parse_mode=ParseMode.HTML,
        )


async def refresh_stars(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id != OWNER_ID:
        await query.answer("🚫 Only owner can refresh!", show_alert=True)
        return
    await query.answer("🔁 Refreshing...")
    try:
        txs = await context.bot.get_star_transactions()
        balance = sum(t.amount for t in txs.transactions) if txs and txs.transactions else 0
        refreshed_at = datetime.now().strftime("%H:%M:%S")
        new_text = (
            f"⭐ <b>Current Stars Balance</b>\n\n"
            f"💰 <b>{balance}</b> Stars\n"
            f"⏰ Last checked: <i>{refreshed_at} UTC</i>"
        )
        current_text = query.message.text or ""
        if current_text != new_text:
            await query.message.edit_text(
                new_text,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_stars")]
                ]),
            )
        else:
            await query.answer("✅ Already up to date!", show_alert=False)
    except Exception as e:
        await query.answer(f"❌ Refresh failed: {str(e)}", show_alert=True)


DONATE_HANDLER = DisableAbleCommandHandler("donate", donate_cmd)
PAY_HANDLER = DisableAbleCommandHandler("pay", pay_cmd)
STARS_HANDLER = CommandHandler("stars", stars_balance)
PRECHECKOUT_HANDLER = PreCheckoutQueryHandler(pre_checkout_handler)
SUCCESS_PAY_HANDLER = MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment)
REFUND_CALLBACK_HANDLER = CallbackQueryHandler(refund_callback, pattern=r"^refund\|")
REFRESH_STARS_HANDLER = CallbackQueryHandler(refresh_stars, pattern=r"^refresh_stars$")
DONATE_PROMPT_HANDLER = CallbackQueryHandler(donate_stars_prompt, pattern=r"^donate_stars_prompt$")

application.add_handler(DONATE_HANDLER)
application.add_handler(PAY_HANDLER)
application.add_handler(STARS_HANDLER)
application.add_handler(PRECHECKOUT_HANDLER)
application.add_handler(SUCCESS_PAY_HANDLER)
application.add_handler(REFUND_CALLBACK_HANDLER)
application.add_handler(REFRESH_STARS_HANDLER)
application.add_handler(DONATE_PROMPT_HANDLER)

__command_list__ = ["donate", "pay", "stars"]
__handlers__ = [
    DONATE_HANDLER,
    PAY_HANDLER,
    STARS_HANDLER,
    PRECHECKOUT_HANDLER,
    SUCCESS_PAY_HANDLER,
    REFUND_CALLBACK_HANDLER,
    REFRESH_STARS_HANDLER,
    DONATE_PROMPT_HANDLER,
]
