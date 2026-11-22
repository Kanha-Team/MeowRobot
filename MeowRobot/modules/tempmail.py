#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team >.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import html
import random
import re
import string
import aiohttp
from pyrogram import filters
from pyrogram.enums import ChatType, ParseMode
from pyrogram.errors import MessageNotModified
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from MeowRobot import SUPPORT_CHAT, pbot as app
from MeowRobot.utils.mongo import db

BASE_URL = "https://api.mail.tm"
DOMAINS_API = f"{BASE_URL}/domains"
ACCOUNTS_API = f"{BASE_URL}/accounts"
TOKEN_API = f"{BASE_URL}/token"
MESSAGES_API = f"{BASE_URL}/messages"

# Local memory caches (backed up by MongoDB)
user_sessions = {}
msg_cache = {}

mail_db = db.tempmail


def generate_password() -> str:
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(12))


def generate_username() -> str:
    chars = string.ascii_lowercase + string.digits
    return "".join(random.choice(chars) for _ in range(8))


def get_powered_by() -> str:
    if app.me and app.me.username:
        return f"@{app.me.username}"
    return f"@{SUPPORT_CHAT}" if SUPPORT_CHAT else "@MeowRobot"


def clean_html_body(raw_html: str) -> str:
    if not raw_html:
        return ""
    # Strip script and style tags and their contents
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", raw_html)
    # Convert line breaks and paragraph tags to newlines
    text = re.sub(r"(?i)<(br\s*/?|/p|/div|/tr|/li|/h[1-6])>", "\n", text)
    # Strip remaining HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Decode HTML entities (&nbsp;, &amp;, &lt;, &gt;, etc.)
    text = html.unescape(text)
    # Collapse multiple whitespace and excessive blank lines
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def extract_otp(subject: str = "", intro: str = "", body: str = "") -> str:
    combined = f"{subject}\n{intro}\n{body}"
    patterns = [
        r"(?:verification\s*code|is\s*your\s*code|otp\s*is|code\s*is|your\s*otp|security\s*code|login\s*code|confirmation\s*code|passcode|one-time\s*password)[\s:=-]+([0-9]{4,8})\b",
        r"\b([0-9]{4,8})\s*(?:is\s*your\s*verification|is\s*your\s*code|is\s*your\s*otp|is\s*your\s*security\s*code)\b",
    ]
    for p in patterns:
        m = re.search(p, combined, re.IGNORECASE)
        if m:
            return m.group(1)

    # Secondary check in subject
    if subject:
        m = re.search(r"\b([0-9]{4,8})\b", subject)
        if m:
            return m.group(1)

    # Secondary check in intro
    if intro:
        m = re.search(r"\b([0-9]{4,8})\b", intro)
        if m:
            return m.group(1)

    return ""


async def save_session(email: str, password: str, token: str, user_id: int):
    user_sessions[email] = {"password": password, "token": token, "user_id": user_id}
    try:
        await mail_db.update_one(
            {"email": email},
            {"$set": {"password": password, "token": token, "user_id": user_id}},
            upsert=True,
        )
    except Exception:
        pass


async def get_session(email: str):
    if email in user_sessions:
        return user_sessions[email]
    try:
        data = await mail_db.find_one({"email": email})
        if data:
            user_sessions[email] = {
                "password": data.get("password"),
                "token": data.get("token"),
                "user_id": data.get("user_id"),
            }
            return user_sessions[email]
    except Exception:
        pass
    return None


async def fetch_json(url, method="GET", headers=None, json_data=None):
    try:
        timeout = aiohttp.ClientTimeout(total=20)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            if method == "GET":
                async with session.get(url, headers=headers) as resp:
                    if resp.status in [200, 201]:
                        return await resp.json()
            elif method == "POST":
                async with session.post(url, headers=headers, json=json_data) as resp:
                    if resp.status in [200, 201]:
                        return await resp.json()
    except Exception:
        pass
    return None


async def get_domains():
    data = await fetch_json(DOMAINS_API)
    if data and "hydra:member" in data and data["hydra:member"]:
        return [domain["domain"] for domain in data["hydra:member"]]
    return ["euploading.com"]


async def create_account(email, password):
    data = {"address": email, "password": password}
    return await fetch_json(ACCOUNTS_API, method="POST", json_data=data)


async def get_token(email, password):
    data = {"address": email, "password": password}
    result = await fetch_json(TOKEN_API, method="POST", json_data=data)
    if result and "token" in result:
        return result["token"]
    return None


async def get_valid_token(email: str) -> str:
    session = await get_session(email)
    if not session:
        return None

    token = session.get("token")
    password = session.get("password")

    if token:
        headers = {"Authorization": f"Bearer {token}"}
        data = await fetch_json(MESSAGES_API, headers=headers)
        if data is not None and "hydra:member" in data:
            return token

    # If token failed or expired, re-login using saved password
    if password:
        new_token = await get_token(email, password)
        if new_token:
            await save_session(email, password, new_token, session.get("user_id", 0))
            return new_token

    return None


async def get_messages(token):
    headers = {"Authorization": f"Bearer {token}"}
    data = await fetch_json(MESSAGES_API, headers=headers)
    if data and "hydra:member" in data:
        return data["hydra:member"]
    return []


async def get_message(token, msg_id):
    headers = {"Authorization": f"Bearer {token}"}
    return await fetch_json(f"{MESSAGES_API}/{msg_id}", headers=headers)


@app.on_message(filters.command(["genmail", "tempmail"]))
async def fakemailgen(_, message: Message):
    if not message.from_user:
        return

    user_id = message.from_user.id
    loading = await message.reply_text("⏳ Creating temporary email...")

    domains = await get_domains()
    domain = random.choice(domains)

    username = generate_username()
    email = f"{username}@{domain}"
    password = generate_password()

    account = await create_account(email, password)
    if not account:
        return await loading.edit_text("❌ Failed to create account! Please try again.")

    token = await get_token(email, password)
    if not token:
        return await loading.edit_text("❌ Failed to authenticate! Please try again.")

    await save_session(email, password, token, user_id)

    powered_by = get_powered_by()
    email_safe = html.escape(str(email))
    pass_safe = html.escape(str(password))
    powered_safe = html.escape(str(powered_by))

    msg_text = (
        "📬 <b>Temp-Mail Created!</b>\n\n"
        f"📧 <b>Email:</b> <code>{email_safe}</code>\n"
        f"🔑 <b>Password:</b> <code>{pass_safe}</code>\n"
        "📨 <b>Mail Box:</b> <code>empty (0 messages)</code>\n\n"
        "💡 <i>Use this email on your site/app, then click 'Refresh' to check for OTP/emails.</i>\n\n"
        f"♨️ Powered by: {powered_safe}"
    )
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🔁 Refresh", callback_data=f"tmail_ref|{email}"),
                InlineKeyboardButton("❌ Close", callback_data=f"tmail_del|{email}"),
            ]
        ]
    )

    if message.chat.type == ChatType.PRIVATE:
        await loading.edit_text(msg_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    else:
        try:
            await app.send_message(user_id, text=msg_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
            pm_url = f"https://t.me/{app.me.username}" if (app.me and app.me.username) else "https://t.me/"
            await loading.edit_text(
                "📬 Temporary email has been sent to your PM!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📬 Check PM", url=pm_url)]]),
            )
        except Exception:
            await loading.edit_text(msg_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)


@app.on_message(filters.command(["set", "setmail"]))
async def setmailgen(_, message: Message):
    if not message.from_user:
        return

    user_id = message.from_user.id

    if len(message.command) < 2:
        return await message.reply_text("❌ Usage: `/set username`")

    username = message.command[1].strip().lower()
    loading = await message.reply_text("⏳ Creating custom email...")

    domains = await get_domains()
    domain = random.choice(domains)

    email = f"{username}@{domain}"
    password = generate_password()

    account = await create_account(email, password)
    if not account:
        return await loading.edit_text("❌ Failed to create account! Username might be taken.")

    token = await get_token(email, password)
    if not token:
        return await loading.edit_text("❌ Failed to authenticate! Please try again.")

    await save_session(email, password, token, user_id)

    powered_by = get_powered_by()
    email_safe = html.escape(str(email))
    pass_safe = html.escape(str(password))
    powered_safe = html.escape(str(powered_by))

    msg_text = (
        "📬 <b>Custom Temp-Mail Created!</b>\n\n"
        f"📧 <b>Email:</b> <code>{email_safe}</code>\n"
        f"🔑 <b>Password:</b> <code>{pass_safe}</code>\n"
        "📨 <b>Mail Box:</b> <code>empty (0 messages)</code>\n\n"
        "💡 <i>Use this email on your site/app, then click 'Refresh' to check for OTP/emails.</i>\n\n"
        f"♨️ Powered by: {powered_safe}"
    )
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🔁 Refresh", callback_data=f"tmail_ref|{email}"),
                InlineKeyboardButton("❌ Close", callback_data=f"tmail_del|{email}"),
            ]
        ]
    )

    if message.chat.type == ChatType.PRIVATE:
        await loading.edit_text(msg_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    else:
        try:
            await app.send_message(user_id, text=msg_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
            pm_url = f"https://t.me/{app.me.username}" if (app.me and app.me.username) else "https://t.me/"
            await loading.edit_text(
                "📬 Custom email has been sent to your PM!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📬 Check PM", url=pm_url)]]),
            )
        except Exception:
            await loading.edit_text(msg_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)


@app.on_callback_query(filters.regex(r"^tmail_ref"))
async def refresh_mailbox(_, query: CallbackQuery):
    parts = query.data.split("|", 1)
    if len(parts) < 2:
        return await query.answer("Invalid data", show_alert=True)

    email = parts[1]
    token = await get_valid_token(email)
    if not token:
        return await query.answer("❌ Session expired! Generate a new email.", show_alert=True)

    session = await get_session(email)
    password = session.get("password", "") if session else ""

    messages = await get_messages(token)
    powered_by = get_powered_by()

    email_safe = html.escape(str(email))
    pass_safe = html.escape(str(password))
    powered_safe = html.escape(str(powered_by))

    if not messages:
        text = (
            "📬 <b>Temp-Mail Inbox</b>\n\n"
            f"📧 <b>Email:</b> <code>{email_safe}</code>\n"
            f"🔑 <b>Password:</b> <code>{pass_safe}</code>\n"
            "📨 <b>Mail Box:</b> <code>empty (0 messages)</code>\n\n"
            "💡 <i>Use this email on your site/app, then click 'Refresh' to check for OTP/emails.</i>\n\n"
            f"♨️ Powered by: {powered_safe}"
        )
        try:
            await query.message.edit_text(
                text,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton("🔁 Refresh", callback_data=f"tmail_ref|{email}"),
                            InlineKeyboardButton("❌ Close", callback_data=f"tmail_del|{email}"),
                        ]
                    ]
                ),
                parse_mode=ParseMode.HTML,
            )
        except MessageNotModified:
            pass
        except Exception:
            pass
        return await query.answer("✅ Refreshed! No new mails yet.")

    # Messages found! Show latest message & detected OTP
    latest = messages[0]
    latest_id = latest.get("id")
    msg_cache[latest_id] = email

    from_addr = latest.get("from", {}).get("address", "Unknown")
    subject = latest.get("subject", "No Subject")
    intro = latest.get("intro", "")

    otp = extract_otp(subject, intro, "")
    otp_safe = html.escape(str(otp)) if otp else ""
    otp_line = f"\n🔢 <b>Detected OTP:</b> <code>{otp_safe}</code> <i>(Tap to copy)</i>\n" if otp_safe else ""

    from_safe = html.escape(str(from_addr))
    subject_safe = html.escape(str(subject))

    text = (
        f"📬 <b>Temp-Mail Inbox</b> ({len(messages)} messages)\n\n"
        f"📧 <b>Email:</b> <code>{email_safe}</code>\n"
        f"🔑 <b>Password:</b> <code>{pass_safe}</code>\n\n"
        "📩 <b>Latest Email:</b>\n"
        f"• <b>From:</b> <code>{from_safe}</code>\n"
        f"• <b>Subject:</b> <code>{subject_safe}</code>\n"
        f"{otp_line}\n"
        f"♨️ Powered by: {powered_safe}"
    )

    buttons = []
    for msg in messages[:5]:
        msg_id = msg.get("id")
        msg_cache[msg_id] = email
        subj = (msg.get("subject") or "No Subject")[:25]
        buttons.append([InlineKeyboardButton(f"✉️ {subj}", callback_data=f"tmail_msg|{msg_id}")])

    buttons.append(
        [
            InlineKeyboardButton("🔁 Refresh", callback_data=f"tmail_ref|{email}"),
            InlineKeyboardButton("❌ Close", callback_data=f"tmail_del|{email}"),
        ]
    )

    try:
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode=ParseMode.HTML)
    except MessageNotModified:
        pass
    except Exception:
        try:
            await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode=None)
        except MessageNotModified:
            pass
        except Exception:
            pass

    alert_msg = f"✅ OTP: {otp}" if otp else f"✅ Found {len(messages)} mail(s)!"
    await query.answer(alert_msg)


@app.on_callback_query(filters.regex(r"^tmail_msg"))
async def show_mail(_, query: CallbackQuery):
    parts = query.data.split("|", 1)
    if len(parts) < 2:
        return await query.answer("Invalid data", show_alert=True)

    msg_id = parts[1]
    email = msg_cache.get(msg_id)

    if not email:
        return await query.answer("Session expired! Please generate a new email.", show_alert=True)

    token = await get_valid_token(email)
    if not token:
        return await query.answer("Session expired! Please generate a new email.", show_alert=True)

    await query.answer("Loading email...")

    mail = await get_message(token, msg_id)
    if not mail:
        return await query.answer("Failed to fetch email!", show_alert=True)

    from_addr = mail.get("from", {}).get("address", "Unknown")
    subject = mail.get("subject", "No Subject")
    date = mail.get("createdAt", "Unknown")[:19]
    intro = mail.get("intro", "")

    # Safely handle text and html (mail.tm returns html as a list of strings)
    text_content = mail.get("text")
    html_content = mail.get("html")

    if text_content and isinstance(text_content, str) and text_content.strip():
        body = clean_html_body(text_content)
    elif html_content:
        if isinstance(html_content, list):
            html_raw = "\n".join(str(h) for h in html_content if h)
        else:
            html_raw = str(html_content)
        body = clean_html_body(html_raw)
    elif intro and intro.strip():
        body = clean_html_body(intro)
    else:
        body = "No content"

    otp = extract_otp(subject, intro, body)
    otp_safe = html.escape(str(otp)) if otp else ""
    otp_line = f"\n🔢 <b>Detected OTP:</b> <code>{otp_safe}</code> <i>(Tap to copy)</i>\n" if otp_safe else ""

    if len(body) > 2500:
        body = body[:2500] + "\n\n... (message truncated)"

    body_safe = html.escape(body)
    from_safe = html.escape(str(from_addr))
    subject_safe = html.escape(str(subject))
    date_safe = html.escape(str(date))

    text = (
        "✉️ <b>Email Details</b>\n\n"
        f"👤 <b>From:</b> <code>{from_safe}</code>\n"
        f"📌 <b>Subject:</b> <code>{subject_safe}</code>\n"
        f"🕒 <b>Date:</b> <code>{date_safe}</code>\n"
        f"{otp_line}\n"
        f"📝 <b>Content:</b>\n{body_safe}"
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🔙 Back to Inbox", callback_data=f"tmail_ref|{email}"),
                InlineKeyboardButton("❌ Close", callback_data=f"tmail_del|{email}"),
            ]
        ]
    )

    try:
        await query.message.edit_text(
            text, reply_markup=keyboard, disable_web_page_preview=True, parse_mode=ParseMode.HTML
        )
    except MessageNotModified:
        pass
    except Exception:
        try:
            await query.message.edit_text(
                text, reply_markup=keyboard, disable_web_page_preview=True, parse_mode=None
            )
        except MessageNotModified:
            pass
        except Exception:
            pass


@app.on_callback_query(filters.regex(r"^tmail_del"))
async def delete_message(_, query: CallbackQuery):
    parts = query.data.split("|", 1)
    if len(parts) > 1:
        email = parts[1]
        user_sessions.pop(email, None)

    try:
        await query.message.delete()
    except Exception:
        pass
    await query.answer("Deleted!", show_alert=False)


@app.on_message(filters.command(["domains", "maildomains"]))
async def list_domains(_, message: Message):
    loading = await message.reply_text("⏳ Fetching domains...")
    domains = await get_domains()
    domains_list = "\n".join(f"• <code>{html.escape(d)}</code>" for d in domains)
    text = (
        "📋 <b>Available Domains:</b>\n\n"
        f"{domains_list}\n\n"
        "💡 <i>Use <code>/set username</code> to create a custom email with these domains.</i>"
    )
    await loading.edit_text(text, parse_mode=ParseMode.HTML)


@app.on_message(filters.command(["login", "maillogin"]))
async def login_mail(_, message: Message):
    if not message.from_user:
        return

    user_id = message.from_user.id

    if len(message.command) < 3:
        return await message.reply_text("❌ Usage: `/login email@domain.com password`")

    email = message.command[1].strip()
    password = message.command[2].strip()

    loading = await message.reply_text("⏳ Logging in...")

    token = await get_token(email, password)
    if not token:
        return await loading.edit_text("❌ Failed to login! Check email and password.")

    await save_session(email, password, token, user_id)

    powered_by = get_powered_by()
    email_safe = html.escape(str(email))
    pass_safe = html.escape(str(password))
    powered_safe = html.escape(str(powered_by))

    msg_text = (
        "✅ <b>Logged In Successfully!</b>\n\n"
        f"📧 <b>Email:</b> <code>{email_safe}</code>\n"
        f"🔑 <b>Password:</b> <code>{pass_safe}</code>\n\n"
        "💡 <i>Click the 'Refresh' button below to check your mailbox.</i>\n\n"
        f"♨️ Powered by: {powered_safe}"
    )
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🔁 Refresh", callback_data=f"tmail_ref|{email}"),
                InlineKeyboardButton("❌ Close", callback_data=f"tmail_del|{email}"),
            ]
        ]
    )

    if message.chat.type == ChatType.PRIVATE:
        await loading.edit_text(msg_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    else:
        try:
            await app.send_message(user_id, text=msg_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
            pm_url = f"https://t.me/{app.me.username}" if (app.me and app.me.username) else "https://t.me/"
            await loading.edit_text(
                "✅ Login details have been sent to your PM!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📬 Check PM", url=pm_url)]]),
            )
        except Exception:
            await loading.edit_text(msg_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)


__mod_name__ = "Tᴇᴍᴘ-Mᴀɪʟ"
__help__ = """
*Temporary Disposable Email Generator 📧*

Create disposable temporary email inboxes to protect your personal email from spam and receive OTP or verification codes.

*Commands:*
 • /genmail: Generate a random disposable temporary email.
 • /set <username>: Create custom temporary email with chosen username.
 • /login <email> <password>: Log in to an existing temp mail inbox.
 • /domains: View available active email domains.
"""
