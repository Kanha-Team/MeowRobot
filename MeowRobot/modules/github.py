#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team >.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import asyncio
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
import zipfile

import aiohttp
from pyrogram import enums, filters
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from MeowRobot import LOGGER
from MeowRobot import pbot as bot

GITHUB_API_URL = "https://api.github.com"
BASE_HEADERS = {
    "User-Agent": "MeowRobot-TelegramBot",
    "Accept": "application/vnd.github.v3+json",
}

# -----------------------------------------------------------------------------
# Database Setup for User GitHub Tokens (Self-contained)
# -----------------------------------------------------------------------------
SQL_LOCK = threading.RLock()
try:
    from sqlalchemy import BigInteger, Column, UnicodeText
    from MeowRobot.modules.sql import BASE, SESSION, engine

    class UserGitHubToken(BASE):
        __tablename__ = "user_github_tokens"
        user_id = Column(BigInteger, primary_key=True)
        token = Column(UnicodeText, nullable=False)

        def __init__(self, user_id: int, token: str):
            self.user_id = user_id
            self.token = token

        def __repr__(self):
            return f"<UserGitHubToken {self.user_id}>"

    UserGitHubToken.__table__.create(bind=engine, checkfirst=True)

    def get_user_token(user_id: int) -> str | None:
        try:
            row = SESSION.get(UserGitHubToken, user_id)
            if row:
                return row.token
            return None
        finally:
            SESSION.close()

    def set_user_token(user_id: int, token: str) -> None:
        with SQL_LOCK:
            try:
                row = SESSION.get(UserGitHubToken, user_id)
                if row:
                    row.token = token
                else:
                    row = UserGitHubToken(user_id, token)
                SESSION.add(row)
                SESSION.commit()
            except Exception:
                SESSION.rollback()
                raise
            finally:
                SESSION.close()

    def del_user_token(user_id: int) -> bool:
        with SQL_LOCK:
            try:
                row = SESSION.get(UserGitHubToken, user_id)
                if row:
                    SESSION.delete(row)
                    SESSION.commit()
                    return True
                return False
            except Exception:
                SESSION.rollback()
                raise
            finally:
                SESSION.close()

except Exception as e:
    LOGGER.warning(f"[GitHub Module] SQL table init error: {e}")
    _MEM_TOKENS: dict[int, str] = {}

    def get_user_token(user_id: int):
        return _MEM_TOKENS.get(user_id)

    def set_user_token(user_id: int, token: str):
        _MEM_TOKENS[user_id] = token

    def del_user_token(user_id: int):
        return _MEM_TOKENS.pop(user_id, None) is not None


def auth_headers(token: str | None = None) -> dict:
    """Build request headers with optional GitHub authorization token."""
    h = dict(BASE_HEADERS)
    if token:
        h["Authorization"] = f"token {token}"
    return h


def parse_repo_input(raw: str):
    """Extract owner and repo name from URL or owner/repo format."""
    raw = raw.strip().rstrip("/")
    m = re.search(r"(?:https?://)?(?:www\.)?github\.com/([^/\s]+)/([^/\s?#]+)", raw)
    if m:
        owner, repo = m.group(1), m.group(2)
        if repo.endswith(".git"):
            repo = repo[:-4]
        return owner, repo
    m2 = re.match(r"^([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+)$", raw)
    if m2:
        owner, repo = m2.group(1), m2.group(2)
        if repo.endswith(".git"):
            repo = repo[:-4]
        return owner, repo
    return None, None


async def safe_edit_text(message: Message, text: str, reply_markup=None):
    """Safely edit message text ignoring Telegram identical message errors."""
    try:
        return await message.edit_text(
            text,
            reply_markup=reply_markup,
            disable_web_page_preview=True,
        )
    except Exception:
        pass


# -----------------------------------------------------------------------------
# Active Sessions Store for Interactive GitPush
# -----------------------------------------------------------------------------
GITPUSH_SESSIONS: dict[int, dict] = {}


# =============================================================================
# 1. TOKEN MANAGEMENT COMMANDS
# =============================================================================

@bot.on_message(filters.command(["setgitoken", "setgittoken", "gitoken"]))
async def set_git_token(_, message: Message):
    if message.chat.type != enums.ChatType.PRIVATE:
        try:
            await message.delete()
        except Exception:
            pass
        return await message.reply(
            "🔒 **Security Warning:** Please configure your GitHub Token in **Private Chat (PM)** to keep your token secure!"
        )

    if len(message.command) < 2:
        return await message.reply(
            "❌ **Please provide your GitHub Personal Access Token (PAT)!**\n\n"
            "**Usage:** `/setgitoken <your_token>`\n\n"
            "👉 **How to generate a token:**\n"
            "1. Visit [GitHub Token Settings](https://github.com/settings/tokens/new)\n"
            "2. Enable the **`repo`** scope (Full control of private repositories)\n"
            "3. Click **Generate Token** and send it here."
        )

    token = message.command[1].strip()
    status_msg = await message.reply("🔄 Verifying your GitHub Token...")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{GITHUB_API_URL}/user",
                headers=auth_headers(token),
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status != 200:
                    return await safe_edit_text(
                        status_msg,
                        "❌ **Invalid or expired GitHub Token!**\n"
                        "Please verify your token has valid `repo` scope permissions and try again.",
                    )
                user_data = await resp.json()
    except Exception as e:
        return await safe_edit_text(status_msg, f"⚠️ **Error connecting to GitHub:** `{e}`")

    login = user_data.get("login", "Unknown")
    name = user_data.get("name") or login
    set_user_token(message.from_user.id, token)

    await safe_edit_text(
        status_msg,
        f"✅ **GitHub Token saved successfully!**\n\n"
        f"👤 **Account:** `@{login}` ({name})\n"
        f"📦 **Public Repos:** `{user_data.get('public_repos', 0)}`\n"
        f"🔒 **Private Repos:** `{user_data.get('total_private_repos', 0)}`\n\n"
        f"You can now download private repos via `/dlrepo` and push projects via `/gitpush`!",
    )


@bot.on_message(filters.command(["mygitoken", "gitstatus"]))
async def my_git_token(_, message: Message):
    token = get_user_token(message.from_user.id)
    if not token:
        return await message.reply(
            "❌ **No GitHub Token configured.**\n"
            "Send `/setgitoken <token>` in **Private Chat (PM)** to configure your personal token."
        )

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{GITHUB_API_URL}/user",
                headers=auth_headers(token),
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    login = data.get("login")
                    hidden_token = token[:7] + "..." + token[-4:]
                    return await message.reply(
                        f"🔑 **GitHub Token Status**\n\n"
                        f"👤 **Connected as:** `@{login}`\n"
                        f"🔒 **Token Key:** `{hidden_token}`\n"
                        f"📦 **Private Repos Access:** Enabled",
                        reply_markup=InlineKeyboardMarkup(
                            [[InlineKeyboardButton("🗑️ Clear My Token", callback_data="clear_gitoken")]]
                        ),
                    )
    except Exception:
        pass

    await message.reply("⚠️ Token is saved in database but could not reach GitHub API.")


@bot.on_message(filters.command(["cleargitoken", "delgitoken"]))
async def clear_git_token(_, message: Message):
    if del_user_token(message.from_user.id):
        await message.reply("🗑️ **Your personal GitHub Token has been removed successfully.**")
    else:
        await message.reply("ℹ️ You do not have any saved GitHub Token.")


@bot.on_callback_query(filters.regex(r"^clear_gitoken$"))
async def cb_clear_gitoken(_, query: CallbackQuery):
    del_user_token(query.from_user.id)
    await query.answer("Token removed!")
    await safe_edit_text(query.message, "🗑️ **Your personal GitHub Token has been removed.**")


# =============================================================================
# 2. INTERACTIVE GITPUSH FEATURE
# =============================================================================

@bot.on_message(filters.command(["gitpush", "pushrepo"]))
async def gitpush_start(_, message: Message):
    reply = message.reply_to_message
    if not reply or not reply.document:
        return await message.reply(
            "❌ **Please reply to a `.zip` file to push it to GitHub!**\n\n"
            "**Usage:** Reply to a `.zip` archive with `/gitpush <reponame>`\n"
            "**Example:** `/gitpush MyAwesomeProject`"
        )

    doc = reply.document
    fname = doc.file_name or ""
    if not (fname.lower().endswith(".zip") or doc.mime_type == "application/zip"):
        return await message.reply("❌ The replied file must be a valid **.zip** archive.")

    if doc.file_size > 50 * 1024 * 1024:
        return await message.reply("❌ File is too large. Maximum supported archive size is 50MB.")

    token = get_user_token(message.from_user.id)
    if not token:
        return await message.reply(
            "❌ **GitHub Token Required!**\n\n"
            "A personal GitHub Access Token (PAT) is required to push code to GitHub.\n\n"
            "👉 **How to configure:**\n"
            "1. Generate a token on [GitHub Settings > Tokens](https://github.com/settings/tokens/new) with **`repo`** scope enabled.\n"
            "2. Send me this command in **Private Chat (PM)**:\n"
            "`/setgitoken <your_token>`"
        )

    # Validate token & fetch username
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{GITHUB_API_URL}/user",
                headers=auth_headers(token),
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status != 200:
                    return await message.reply(
                        "❌ **GitHub Token authentication failed!** Please update your token using `/setgitoken <token>` in PM."
                    )
                user_info = await resp.json()
    except Exception as e:
        return await message.reply(f"⚠️ **Error validating GitHub Token:** `{e}`")

    login = user_info.get("login")

    # Determine Repository Name
    if len(message.command) > 1:
        reponame = message.command[1].strip()
    else:
        reponame = os.path.splitext(fname)[0]

    reponame = re.sub(r"[^a-zA-Z0-9_.-]", "-", reponame)
    if not reponame:
        reponame = "MyProject"

    # Initialize Push Session
    user_id = message.from_user.id
    GITPUSH_SESSIONS[user_id] = {
        "reply_msg_id": reply.id,
        "chat_id": message.chat.id,
        "file_name": fname,
        "file_size": doc.file_size,
        "reponame": reponame,
        "login": login,
        "token": token,
        "visibility": "public",
        "branch": "main",
        "commit_msg": "feat: initial commit via MeowRobot",
        "waiting_custom": None,
        "prompt_msg_id": None,
    }

    # Step 1: Ask Visibility (Private or Public)
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔒 Private", callback_data=f"gpush_vis_private_{user_id}"),
            InlineKeyboardButton("🌍 Public", callback_data=f"gpush_vis_public_{user_id}"),
        ],
        [InlineKeyboardButton("❌ Cancel", callback_data=f"gpush_cancel_{user_id}")],
    ])

    prompt = await message.reply(
        f"🐙 **GitHub Push Setup**\n\n"
        f"📦 **Repository Name:** `{reponame}`\n"
        f"👤 **Target Account:** `@{login}`\n"
        f"📁 **Archive File:** `{fname}` ({round(doc.file_size / (1024 * 1024), 2)} MB)\n\n"
        f"🔒 **Step 1/3: Choose Repository Visibility:**",
        reply_markup=keyboard,
    )
    GITPUSH_SESSIONS[user_id]["prompt_msg_id"] = prompt.id


@bot.on_callback_query(filters.regex(r"^gpush_vis_(private|public)_(\d+)$"))
async def cb_gitpush_visibility(_, query: CallbackQuery):
    vis = query.matches[0].group(1)
    target_user_id = int(query.matches[0].group(2))

    if query.from_user.id != target_user_id:
        return await query.answer("❌ This is not your push session!", show_alert=True)

    session = GITPUSH_SESSIONS.get(target_user_id)
    if not session:
        return await query.answer("❌ Session expired. Please send /gitpush again.", show_alert=True)

    session["visibility"] = vis
    await query.answer(f"Visibility: {vis.capitalize()}")

    # Step 2: Ask Branch Name
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🌿 main", callback_data=f"gpush_br_main_{target_user_id}"),
            InlineKeyboardButton("🌿 master", callback_data=f"gpush_br_master_{target_user_id}"),
        ],
        [
            InlineKeyboardButton("✏️ Custom Branch", callback_data=f"gpush_br_custom_{target_user_id}"),
            InlineKeyboardButton("❌ Cancel", callback_data=f"gpush_cancel_{target_user_id}"),
        ],
    ])

    await safe_edit_text(
        query.message,
        f"🐙 **GitHub Push Setup**\n\n"
        f"📦 **Repository:** `{session['reponame']}` (`{vis.capitalize()}`)\n"
        f"👤 **Target Account:** `@{session['login']}`\n\n"
        f"🌿 **Step 2/3: Select or Enter Branch Name:**",
        reply_markup=keyboard,
    )


@bot.on_callback_query(filters.regex(r"^gpush_br_(main|master|custom)_(\d+)$"))
async def cb_gitpush_branch(_, query: CallbackQuery):
    br_choice = query.matches[0].group(1)
    target_user_id = int(query.matches[0].group(2))

    if query.from_user.id != target_user_id:
        return await query.answer("❌ This is not your push session!", show_alert=True)

    session = GITPUSH_SESSIONS.get(target_user_id)
    if not session:
        return await query.answer("❌ Session expired.", show_alert=True)

    if br_choice == "custom":
        session["waiting_custom"] = "branch"
        session["prompt_msg_id"] = query.message.id
        await query.answer()
        return await safe_edit_text(
            query.message,
            f"🐙 **Custom Branch Name**\n\n"
            f"Please **reply to this message** with your desired branch name (e.g. `develop` or `v2.0`).",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Cancel", callback_data=f"gpush_cancel_{target_user_id}")]
            ]),
        )

    session["branch"] = br_choice
    await query.answer(f"Branch: {br_choice}")
    await prompt_commit_step(query.message, session, target_user_id)


async def prompt_commit_step(message: Message, session: dict, target_user_id: int):
    # Step 3: Ask Commit Message
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "⚡ Default: Initial commit",
                callback_data=f"gpush_cm_default_{target_user_id}",
            )
        ],
        [
            InlineKeyboardButton(
                "✏️ Custom Commit Name",
                callback_data=f"gpush_cm_custom_{target_user_id}",
            )
        ],
        [InlineKeyboardButton("❌ Cancel", callback_data=f"gpush_cancel_{target_user_id}")],
    ])

    await safe_edit_text(
        message,
        f"🐙 **GitHub Push Setup**\n\n"
        f"📦 **Repository:** `{session['reponame']}` (`{session['visibility'].capitalize()}`)\n"
        f"👤 **Account:** `@{session['login']}`\n"
        f"🌿 **Branch:** `{session['branch']}`\n\n"
        f"💬 **Step 3/3: Select or Enter Commit Message:**",
        reply_markup=keyboard,
    )


@bot.on_callback_query(filters.regex(r"^gpush_cm_(default|custom)_(\d+)$"))
async def cb_gitpush_commit(_, query: CallbackQuery):
    cm_choice = query.matches[0].group(1)
    target_user_id = int(query.matches[0].group(2))

    if query.from_user.id != target_user_id:
        return await query.answer("❌ This is not your push session!", show_alert=True)

    session = GITPUSH_SESSIONS.get(target_user_id)
    if not session:
        return await query.answer("❌ Session expired.", show_alert=True)

    if cm_choice == "custom":
        session["waiting_custom"] = "commit"
        session["prompt_msg_id"] = query.message.id
        await query.answer()
        return await safe_edit_text(
            query.message,
            f"🐙 **Custom Commit Message**\n\n"
            f"Please **reply to this message** with your desired commit message (e.g. `feat: initial release`).",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Cancel", callback_data=f"gpush_cancel_{target_user_id}")]
            ]),
        )

    session["commit_msg"] = "feat: initial commit via MeowRobot"
    await query.answer("Starting push...")
    await execute_git_push(query.message, session, target_user_id)


@bot.on_callback_query(filters.regex(r"^gpush_cancel_(\d+)$"))
async def cb_gitpush_cancel(_, query: CallbackQuery):
    target_user_id = int(query.matches[0].group(1))
    if query.from_user.id != target_user_id:
        return await query.answer("❌ Action not permitted.", show_alert=True)

    GITPUSH_SESSIONS.pop(target_user_id, None)
    await query.answer("Cancelled!")
    await safe_edit_text(query.message, "❌ **GitHub Push operation cancelled.**")


@bot.on_message(filters.reply & ~filters.bot)
async def handle_custom_text_input(_, message: Message):
    """Listen for custom branch or commit text inputs."""
    user_id = message.from_user.id
    session = GITPUSH_SESSIONS.get(user_id)
    if not session or not session.get("waiting_custom"):
        return

    # Ensure reply is to the bot's prompt message
    if session.get("prompt_msg_id") and message.reply_to_message.id != session["prompt_msg_id"]:
        return

    text = message.text.strip()
    if session["waiting_custom"] == "branch":
        branch_clean = re.sub(r"[^a-zA-Z0-9_.-]", "-", text)
        session["branch"] = branch_clean or "main"
        session["waiting_custom"] = None
        prompt_msg = await message.reply("✅ Branch name registered!")
        session["prompt_msg_id"] = prompt_msg.id
        await prompt_commit_step(prompt_msg, session, user_id)

    elif session["waiting_custom"] == "commit":
        session["commit_msg"] = text or "feat: initial commit via MeowRobot"
        session["waiting_custom"] = None
        status_msg = await message.reply("✅ Commit message registered! Starting push...")
        await execute_git_push(status_msg, session, user_id)


async def execute_git_push(status_msg: Message, session: dict, user_id: int):
    """Download archive, extract, create GitHub repository, and push."""
    reponame = session["reponame"]
    login = session["login"]
    token = session["token"]
    visibility = session["visibility"]
    branch = session["branch"]
    commit_msg = session["commit_msg"]
    chat_id = session["chat_id"]
    reply_msg_id = session["reply_msg_id"]

    temp_dir = tempfile.mkdtemp(prefix=f"gitpush_{user_id}_")
    zip_path = os.path.join(temp_dir, "archive.zip")
    extract_dir = os.path.join(temp_dir, "extracted")

    try:
        await safe_edit_text(status_msg, "⏳ **[1/4]** Downloading `.zip` archive from Telegram...")
        source_msg = await bot.get_messages(chat_id, reply_msg_id)
        if not source_msg or not source_msg.document:
            return await safe_edit_text(status_msg, "❌ Could not retrieve original file from Telegram.")

        await source_msg.download(file_name=zip_path)

        await safe_edit_text(status_msg, "📦 **[2/4]** Extracting repository contents...")
        os.makedirs(extract_dir, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(extract_dir)

        # Handle nested single directory extraction
        items = [i for i in os.listdir(extract_dir) if not i.startswith(".")]
        root_dir = extract_dir
        if len(items) == 1 and os.path.isdir(os.path.join(extract_dir, items[0])):
            root_dir = os.path.join(extract_dir, items[0])

        # Remove existing .git folder to start clean
        existing_git = os.path.join(root_dir, ".git")
        if os.path.exists(existing_git):
            shutil.rmtree(existing_git, ignore_errors=True)

        await safe_edit_text(status_msg, f"🌐 **[3/4]** Creating/verifying repository `{reponame}` on GitHub...")
        async with aiohttp.ClientSession() as http_sess:
            check_url = f"{GITHUB_API_URL}/repos/{login}/{reponame}"
            async with http_sess.get(check_url, headers=auth_headers(token)) as r_chk:
                if r_chk.status == 404:
                    # Create new repository
                    create_url = f"{GITHUB_API_URL}/user/repos"
                    payload = {
                        "name": reponame,
                        "private": (visibility == "private"),
                        "description": "Uploaded via MeowRobot Telegram Bot",
                        "auto_init": False,
                    }
                    async with http_sess.post(create_url, json=payload, headers=auth_headers(token)) as r_cr:
                        if r_cr.status not in (200, 201):
                            err_resp = await r_cr.text()
                            return await safe_edit_text(
                                status_msg,
                                f"❌ **Failed to create GitHub repository:** HTTP {r_cr.status}\n`{err_resp[:200]}`",
                            )

        await safe_edit_text(status_msg, f"🚀 **[4/4]** Initializing git & pushing to branch `{branch}`...")

        def _run_git_commands():
            subprocess.run(["git", "init"], cwd=root_dir, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", login], cwd=root_dir, check=True)
            subprocess.run(["git", "config", "user.email", f"{login}@users.noreply.github.com"], cwd=root_dir, check=True)
            subprocess.run(["git", "checkout", "-B", branch], cwd=root_dir, check=True, capture_output=True)
            subprocess.run(["git", "add", "-A"], cwd=root_dir, check=True)
            subprocess.run(["git", "commit", "-m", commit_msg, "--allow-empty"], cwd=root_dir, check=True, capture_output=True)
            remote_url = f"https://{token}@github.com/{login}/{reponame}.git"
            subprocess.run(["git", "remote", "add", "origin", remote_url], cwd=root_dir, check=True)
            push_res = subprocess.run(
                ["git", "push", "-u", "origin", branch, "--force"],
                cwd=root_dir,
                capture_output=True,
                text=True,
            )
            if push_res.returncode != 0:
                clean_err = push_res.stderr.replace(token, "[REDACTED_TOKEN]")
                raise Exception(clean_err)

        await asyncio.to_thread(_run_git_commands)

        total_files = sum(len(files) for _, _, files in os.walk(root_dir) if ".git" not in _)
        repo_link = f"https://github.com/{login}/{reponame}"
        vis_icon = "🔒 Private" if visibility == "private" else "🌍 Public"

        await safe_edit_text(
            status_msg,
            f"✅ **Successfully Pushed to GitHub!** 🎉\n\n"
            f"📦 **Repository:** [{login}/{reponame}]({repo_link})\n"
            f"🔒 **Visibility:** `{vis_icon}`\n"
            f"🌿 **Branch:** `{branch}`\n"
            f"💬 **Commit:** `{commit_msg}`\n"
            f"📁 **Total Files:** `{total_files}`\n"
            f"👤 **Account:** `@{login}`\n\n"
            f"⚡ **Pushed via MeowRobot**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🌐 Open Repository", url=repo_link)]
            ]),
        )

    except Exception as e:
        safe_err = str(e).replace(token, "[TOKEN_REDACTED]") if token else str(e)
        LOGGER.error(f"[GitPush Error]: {safe_err}")
        await safe_edit_text(status_msg, f"❌ **Error during Git Push:**\n`{safe_err[:300]}`")

    finally:
        GITPUSH_SESSIONS.pop(user_id, None)
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)


# =============================================================================
# 3. GITHUB EXPLORATION & UTILITY COMMANDS (Supports Public & Private Repos)
# =============================================================================

@bot.on_message(filters.command(["git", "github"]))
async def git_user_info(_, message: Message):
    username = None
    if len(message.command) > 1:
        username = message.command[1].strip().lstrip("@")
    elif message.reply_to_message and message.reply_to_message.text:
        text = message.reply_to_message.text.strip()
        m = re.search(r"github\.com/([a-zA-Z0-9_.-]+)", text)
        if m:
            username = m.group(1)
        elif len(text.split()) == 1 and re.match(r"^[a-zA-Z0-9_.-]+$", text):
            username = text

    if not username:
        return await message.reply(
            "❌ **Please provide a GitHub username!**\n\n"
            "**Usage:** `/git <username>`\n"
            "**Example:** `/git torvalds`"
        )

    status_msg = await message.reply(f"🔍 Searching GitHub for `@{username}`...")
    token = get_user_token(message.from_user.id)
    url = f"{GITHUB_API_URL}/users/{username}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=auth_headers(token), timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 404:
                    return await safe_edit_text(status_msg, f"❌ **GitHub user** `@{username}` **not found.**")
                if resp.status != 200:
                    return await safe_edit_text(status_msg, f"⚠️ **GitHub API error:** HTTP {resp.status}")
                data = await resp.json()
    except Exception as e:
        return await safe_edit_text(status_msg, f"⚠️ **Error connecting to GitHub:** `{e}`")

    name = data.get("name") or username
    login = data.get("login", username)
    avatar_url = data.get("avatar_url")
    html_url = data.get("html_url", f"https://github.com/{username}")
    bio = data.get("bio") or "No bio available."
    company = data.get("company") or "N/A"
    location = data.get("location") or "N/A"
    blog = data.get("blog") or "N/A"
    public_repos = data.get("public_repos", 0)
    public_gists = data.get("public_gists", 0)
    followers = data.get("followers", 0)
    following = data.get("following", 0)
    created_at = data.get("created_at", "")[:10]
    updated_at = data.get("updated_at", "")[:10]

    caption = (
        f"🐙 **GitHub User Profile**\n\n"
        f"👤 **Name:** {name}\n"
        f"🏷️ **Username:** `@{login}`\n"
        f"📝 **Bio:** {bio}\n"
        f"🏢 **Company:** {company}\n"
        f"📍 **Location:** {location}\n"
        f"🌐 **Website:** {blog}\n\n"
        f"📦 **Public Repos:** `{public_repos}` | 📄 **Gists:** `{public_gists}`\n"
        f"👥 **Followers:** `{followers}` | **Following:** `{following}`\n"
        f"📅 **Joined:** `{created_at}` | 🔄 **Updated:** `{updated_at}`"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🌐 View Profile", url=html_url),
            InlineKeyboardButton("📦 Repositories", callback_data=f"allrepo_{login}"),
        ]
    ])

    await status_msg.delete()
    if avatar_url:
        try:
            return await message.reply_photo(photo=avatar_url, caption=caption, reply_markup=keyboard)
        except Exception:
            pass

    return await message.reply_text(caption, reply_markup=keyboard, disable_web_page_preview=True)


@bot.on_message(filters.command(["allrepo", "allrepos", "repos"]))
async def all_repos_handler(_, message: Message):
    username = None
    if len(message.command) > 1:
        username = message.command[1].strip().lstrip("@")
    elif message.reply_to_message and message.reply_to_message.text:
        text = message.reply_to_message.text.strip()
        m = re.search(r"github\.com/([a-zA-Z0-9_.-]+)", text)
        if m:
            username = m.group(1)
        elif len(text.split()) == 1 and re.match(r"^[a-zA-Z0-9_.-]+$", text):
            username = text

    if not username:
        return await message.reply(
            "❌ **Please provide a GitHub username!**\n\n"
            "**Usage:** `/allrepo <username>`\n"
            "**Example:** `/allrepo torvalds`"
        )

    status_msg = await message.reply(f"🔍 Fetching repositories for `@{username}`...")
    await send_user_repositories(message, username, status_msg)


async def send_user_repositories(message: Message, username: str, status_msg=None):
    token = get_user_token(message.from_user.id)
    url = f"{GITHUB_API_URL}/users/{username}/repos?per_page=100&sort=updated"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=auth_headers(token), timeout=aiohttp.ClientTimeout(total=20)) as resp:
                if resp.status == 404:
                    text = f"❌ **GitHub user** `@{username}` **not found.**"
                    if status_msg:
                        return await safe_edit_text(status_msg, text)
                    return await message.reply(text)
                if resp.status != 200:
                    text = f"⚠️ **GitHub API error:** HTTP {resp.status}"
                    if status_msg:
                        return await safe_edit_text(status_msg, text)
                    return await message.reply(text)
                repos = await resp.json()
    except Exception as e:
        text = f"⚠️ **Error connecting to GitHub:** `{e}`"
        if status_msg:
            return await safe_edit_text(status_msg, text)
        return await message.reply(text)

    if not repos:
        text = f"ℹ️ **User** `@{username}` **has no public repositories.**"
        if status_msg:
            return await safe_edit_text(status_msg, text)
        return await message.reply(text)

    total_count = len(repos)
    display_limit = 12
    output_lines = [
        f"📦 **Repositories of [{username}](https://github.com/{username})** ({total_count} total):\n"
    ]

    for idx, r in enumerate(repos[:display_limit], 1):
        r_name = r.get("name")
        r_url = r.get("html_url")
        r_desc = r.get("description") or "No description provided."
        if len(r_desc) > 65:
            r_desc = r_desc[:62] + "..."
        r_stars = r.get("stargazers_count", 0)
        r_forks = r.get("forks_count", 0)
        r_lang = r.get("language") or "Other"

        output_lines.append(
            f"**{idx}.** [{r_name}]({r_url})\n"
            f"   ⭐ `{r_stars}` | 🍴 `{r_forks}` | 💻 `{r_lang}`\n"
            f"   _{r_desc}_\n"
        )

    if total_count > display_limit:
        output_lines.append(f"ℹ️ _Showing top {display_limit} most recently updated repos._")

    text_body = "\n".join(output_lines)
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🌐 View All Repositories",
                url=f"https://github.com/{username}?tab=repositories",
            )
        ]
    ])

    if status_msg:
        await safe_edit_text(status_msg, text_body, reply_markup=keyboard)
    else:
        await message.reply(text_body, reply_markup=keyboard, disable_web_page_preview=True)


@bot.on_callback_query(filters.regex(r"^allrepo_(.+)"))
async def cb_allrepo_fetch(_, query: CallbackQuery):
    username = query.matches[0].group(1)
    await query.answer("Fetching repositories...")
    await send_user_repositories(query.message, username)


@bot.on_message(filters.command(["dlrepo", "gitdl"]))
async def dlrepo_handler(_, message: Message):
    """Download entire repository as .zip (Supports both Public and Private repositories via user token)."""
    raw_target = None
    if len(message.command) > 1:
        raw_target = message.command[1].strip()
    elif message.reply_to_message and message.reply_to_message.text:
        text = message.reply_to_message.text.strip()
        m = re.search(r"((?:https?://)?(?:www\.)?github\.com/[^\s]+)", text)
        if m:
            raw_target = m.group(1)
        elif "/" in text and len(text.split()) == 1:
            raw_target = text

    if not raw_target:
        return await message.reply(
            "❌ **Please provide a repository URL or owner/repo!**\n\n"
            "**Usage:** `/dlrepo <repo_url or owner/repo>`\n"
            "**Example:** `/dlrepo Kanha-Team/MeowRobot`\n\n"
            "💡 **Tip:** Set your GitHub token via `/setgitoken` in PM to download **private repositories** too!"
        )

    owner, repo = parse_repo_input(raw_target)
    if not owner or not repo:
        return await message.reply("❌ Invalid format! Provide `owner/repo` or a valid GitHub URL.")

    token = get_user_token(message.from_user.id)
    status_msg = await message.reply(f"🔍 Fetching repository details for `{owner}/{repo}`...")
    repo_url = f"{GITHUB_API_URL}/repos/{owner}/{repo}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(repo_url, headers=auth_headers(token), timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 404:
                    if not token:
                        return await safe_edit_text(
                            status_msg,
                            f"❌ Repository `{owner}/{repo}` not found.\n\n"
                            f"🔒 If this is a **Private Repository**, please configure your token via `/setgitoken <token>` in PM first.",
                        )
                    return await safe_edit_text(
                        status_msg,
                        f"❌ Repository `{owner}/{repo}` not found or your token lacks permission to access it.",
                    )
                if resp.status != 200:
                    return await safe_edit_text(status_msg, f"⚠️ GitHub API error: HTTP {resp.status}")
                repo_data = await resp.json()
    except Exception as e:
        return await safe_edit_text(status_msg, f"⚠️ Error: `{e}`")

    default_branch = repo_data.get("default_branch", "master")
    full_name = repo_data.get("full_name", f"{owner}/{repo}")
    stars = repo_data.get("stargazers_count", 0)
    forks = repo_data.get("forks_count", 0)
    desc = repo_data.get("description") or "No description provided."
    is_private = repo_data.get("private", False)
    size_kb = repo_data.get("size", 0)

    if size_kb > 300 * 1024:
        return await safe_edit_text(status_msg, f"⚠️ Repository archive is too large (~{round(size_kb / 1024, 1)} MB).")

    vis_label = "🔒 Private" if is_private else "🌍 Public"
    await safe_edit_text(status_msg, f"⏳ Downloading `{full_name}` ({vis_label}, Branch: `{default_branch}`)...")

    zip_url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/zipball/{default_branch}"
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, f"{owner}_{repo}_{default_branch}.zip")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                zip_url,
                headers=auth_headers(token),
                allow_redirects=True,
                timeout=aiohttp.ClientTimeout(total=180),
            ) as resp:
                if resp.status != 200:
                    return await safe_edit_text(status_msg, f"❌ Failed to download archive: HTTP {resp.status}")
                with open(file_path, "wb") as f:
                    while True:
                        chunk = await resp.content.read(64 * 1024)
                        if not chunk:
                            break
                        f.write(chunk)

        file_size = os.path.getsize(file_path)
        if file_size > 50 * 1024 * 1024:
            return await safe_edit_text(
                status_msg,
                f"❌ Archive is too large ({round(file_size / (1024 * 1024), 2)} MB) for Telegram upload.",
            )

        await safe_edit_text(status_msg, "📤 Uploading repository archive to Telegram...")

        caption = (
            f"📦 **Repository:** [{full_name}](https://github.com/{owner}/{repo})\n"
            f"🔒 **Visibility:** `{vis_label}`\n"
            f"🌿 **Branch:** `{default_branch}`\n"
            f"⭐ **Stars:** `{stars}` | 🍴 **Forks:** `{forks}`\n"
            f"📝 **Description:** _{desc}_\n\n"
            f"⚡ **Downloaded via MeowRobot**"
        )

        await message.reply_document(
            document=file_path,
            file_name=f"{repo}-{default_branch}.zip",
            caption=caption,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 View on GitHub", url=f"https://github.com/{owner}/{repo}")]
            ]),
        )
        await status_msg.delete()

    except Exception as e:
        await safe_edit_text(status_msg, f"❌ Error: `{e}`")

    finally:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass


@bot.on_message(filters.command(["repo", "gitrepo"]))
async def repo_info_handler(_, message: Message):
    if len(message.command) < 2:
        return await message.reply(
            "❌ **Please provide a repository!**\n\n"
            "**Usage:** `/repo <owner/repo>`\n"
            "**Example:** `/repo Kanha-Team/MeowRobot`"
        )

    owner, repo = parse_repo_input(message.command[1])
    if not owner or not repo:
        return await message.reply("❌ Invalid format! Please use `/repo <owner/repo>`.")

    token = get_user_token(message.from_user.id)
    status_msg = await message.reply(f"🔍 Fetching `{owner}/{repo}`...")
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=auth_headers(token), timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 404:
                    return await safe_edit_text(
                        status_msg,
                        f"❌ Repository `{owner}/{repo}` not found.\n(If private, configure token via `/setgitoken`).",
                    )
                data = await resp.json()
    except Exception as e:
        return await safe_edit_text(status_msg, f"⚠️ Error: `{e}`")

    full_name = data.get("full_name")
    html_url = data.get("html_url")
    desc = data.get("description") or "No description provided."
    stars = data.get("stargazers_count", 0)
    forks = data.get("forks_count", 0)
    issues = data.get("open_issues_count", 0)
    watchers = data.get("subscribers_count", 0)
    lang = data.get("language") or "N/A"
    branch = data.get("default_branch", "main")
    license_info = data.get("license", {}).get("name") if data.get("license") else "No License"
    size_mb = round(data.get("size", 0) / 1024, 2)
    created = data.get("created_at", "")[:10]
    updated = data.get("updated_at", "")[:10]
    clone_url = data.get("clone_url")
    vis = "🔒 Private" if data.get("private") else "🌍 Public"

    text = (
        f"📦 **Repository Information**\n\n"
        f"🏷️ **Name:** [{full_name}]({html_url})\n"
        f"🔒 **Visibility:** `{vis}`\n"
        f"📝 **Description:** _{desc}_\n\n"
        f"⭐ **Stars:** `{stars}` | 🍴 **Forks:** `{forks}`\n"
        f"🐛 **Open Issues:** `{issues}` | 👁️ **Watchers:** `{watchers}`\n"
        f"💻 **Language:** `{lang}` | ⚖️ **License:** `{license_info}`\n"
        f"🌿 **Default Branch:** `{branch}` | 📊 **Size:** `{size_mb} MB`\n"
        f"📅 **Created:** `{created}` | 🔄 **Updated:** `{updated}`\n\n"
        f"📥 **Clone URL:**\n`{clone_url}`"
    )

    await safe_edit_text(
        status_msg,
        text,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🌐 View on GitHub", url=html_url),
                InlineKeyboardButton("📥 Download Zip", callback_data=f"dlrepo_{owner}_{repo}"),
            ]
        ]),
    )


@bot.on_callback_query(filters.regex(r"^dlrepo_([^_]+)_(.+)$"))
async def cb_quick_dlrepo(_, query: CallbackQuery):
    owner = query.matches[0].group(1)
    repo = query.matches[0].group(2)
    await query.answer("Preparing download...")
    query.message.command = ["dlrepo", f"{owner}/{repo}"]
    await dlrepo_handler(_, query.message)


@bot.on_message(filters.command(["searchrepo", "gitsearch"]))
async def search_repo_handler(_, message: Message):
    if len(message.command) < 2:
        return await message.reply(
            "❌ **Please provide search query!**\n\n"
            "**Usage:** `/searchrepo <keyword>`\n"
            "**Example:** `/searchrepo telegram bot python`"
        )

    query = " ".join(message.command[1:]).strip()
    status_msg = await message.reply(f"🔍 Searching GitHub for `{query}`...")
    token = get_user_token(message.from_user.id)
    url = f"{GITHUB_API_URL}/search/repositories?q={query}&per_page=7&sort=stars"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=auth_headers(token), timeout=aiohttp.ClientTimeout(total=15)) as resp:
                data = await resp.json()
    except Exception as e:
        return await safe_edit_text(status_msg, f"⚠️ Error: `{e}`")

    items = data.get("items", [])
    if not items:
        return await safe_edit_text(status_msg, f"ℹ️ No repositories found for `{query}`.")

    text_lines = [f"🔍 **GitHub Search Results for:** `{query}`\n"]
    for i, r in enumerate(items, 1):
        r_name = r.get("full_name")
        r_url = r.get("html_url")
        r_stars = r.get("stargazers_count", 0)
        r_forks = r.get("forks_count", 0)
        r_lang = r.get("language") or "Other"
        r_desc = r.get("description") or "No description."
        if len(r_desc) > 55:
            r_desc = r_desc[:52] + "..."

        text_lines.append(
            f"**{i}.** [{r_name}]({r_url})\n"
            f"   ⭐ `{r_stars}` | 🍴 `{r_forks}` | 💻 `{r_lang}`\n"
            f"   _{r_desc}_\n"
        )

    await safe_edit_text(
        status_msg,
        "\n".join(text_lines),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🌐 Open Search on GitHub", url=f"https://github.com/search?q={query}")]
        ]),
    )


@bot.on_message(filters.command(["gitfile", "rawfile"]))
async def git_file_handler(_, message: Message):
    if len(message.command) < 3:
        return await message.reply(
            "❌ **Please provide repository and file path!**\n\n"
            "**Usage:** `/gitfile <owner/repo> <filepath>`\n"
            "**Example:** `/gitfile Kanha-Team/MeowRobot app.json`"
        )

    owner, repo = parse_repo_input(message.command[1])
    file_path = message.command[2].strip().lstrip("/")
    if not owner or not repo:
        return await message.reply("❌ Invalid repository format!")

    token = get_user_token(message.from_user.id)
    status_msg = await message.reply(f"🔍 Fetching `{file_path}` from `{owner}/{repo}`...")
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/contents/{file_path}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=auth_headers(token), timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 404:
                    return await safe_edit_text(status_msg, f"❌ File `{file_path}` not found in `{owner}/{repo}`.")
                data = await resp.json()
    except Exception as e:
        return await safe_edit_text(status_msg, f"⚠️ Error: `{e}`")

    download_url = data.get("download_url")
    if not download_url:
        return await safe_edit_text(status_msg, "❌ Could not obtain raw file download URL.")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(download_url, headers=auth_headers(token), timeout=aiohttp.ClientTimeout(total=20)) as resp:
                content = await resp.read()

        if len(content) < 3500:
            try:
                text_content = content.decode("utf-8")
                await safe_edit_text(
                    status_msg,
                    f"📄 **File:** `{file_path}` ([{owner}/{repo}](https://github.com/{owner}/{repo}))\n\n"
                    f"```\n{text_content}\n```",
                )
                return
            except UnicodeDecodeError:
                pass

        temp_file = os.path.join(tempfile.gettempdir(), os.path.basename(file_path))
        with open(temp_file, "wb") as f:
            f.write(content)

        await message.reply_document(
            document=temp_file,
            caption=f"📄 **File:** `{file_path}` from [{owner}/{repo}](https://github.com/{owner}/{repo})",
        )
        await status_msg.delete()
        if os.path.exists(temp_file):
            os.remove(temp_file)

    except Exception as e:
        await safe_edit_text(status_msg, f"⚠️ Failed to send file: `{e}`")


@bot.on_message(filters.command(["release", "gitrelease"]))
async def release_handler(_, message: Message):
    if len(message.command) < 2:
        return await message.reply(
            "❌ **Please provide a repository!**\n\n"
            "**Usage:** `/release <owner/repo>`\n"
            "**Example:** `/release telegramdesktop/tdesktop`"
        )

    owner, repo = parse_repo_input(message.command[1])
    if not owner or not repo:
        return await message.reply("❌ Invalid repository format.")

    token = get_user_token(message.from_user.id)
    status_msg = await message.reply(f"🔍 Fetching latest release for `{owner}/{repo}`...")
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/releases/latest"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=auth_headers(token), timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 404:
                    return await safe_edit_text(status_msg, f"ℹ️ No public releases found for `{owner}/{repo}`.")
                data = await resp.json()
    except Exception as e:
        return await safe_edit_text(status_msg, f"⚠️ Error: `{e}`")

    tag = data.get("tag_name")
    rel_name = data.get("name") or tag
    html_url = data.get("html_url")
    published = data.get("published_at", "")[:10]
    body = data.get("body") or "No changelog provided."
    if len(body) > 400:
        body = body[:397] + "..."

    assets = data.get("assets", [])
    asset_lines = []
    for a in assets[:5]:
        a_name = a.get("name")
        a_dl = a.get("browser_download_url")
        a_size = round(a.get("size", 0) / (1024 * 1024), 2)
        asset_lines.append(f"• [{a_name}]({a_dl}) ({a_size} MB)")

    asset_text = "\n".join(asset_lines) if asset_lines else "No direct assets attached."

    text = (
        f"🚀 **Latest Release for [{owner}/{repo}](https://github.com/{owner}/{repo})**\n\n"
        f"🏷️ **Version:** `{tag}` ({rel_name})\n"
        f"📅 **Published On:** `{published}`\n\n"
        f"📝 **Changelog:**\n{body}\n\n"
        f"📦 **Downloads / Assets:**\n{asset_text}"
    )

    await safe_edit_text(
        status_msg,
        text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🌐 View Release Page", url=html_url)]]),
    )


@bot.on_message(filters.command(["commits", "gitcommits"]))
async def commits_handler(_, message: Message):
    if len(message.command) < 2:
        return await message.reply(
            "❌ **Please provide a repository!**\n\n"
            "**Usage:** `/commits <owner/repo>`\n"
            "**Example:** `/commits Kanha-Team/MeowRobot`"
        )

    owner, repo = parse_repo_input(message.command[1])
    if not owner or not repo:
        return await message.reply("❌ Invalid repository format.")

    token = get_user_token(message.from_user.id)
    status_msg = await message.reply(f"🔍 Fetching recent commits for `{owner}/{repo}`...")
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/commits?per_page=6"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=auth_headers(token), timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 404:
                    return await safe_edit_text(status_msg, f"❌ Repository `{owner}/{repo}` not found.")
                commits = await resp.json()
    except Exception as e:
        return await safe_edit_text(status_msg, f"⚠️ Error: `{e}`")

    if not commits or not isinstance(commits, list):
        return await safe_edit_text(status_msg, f"ℹ️ No commits found for `{owner}/{repo}`.")

    lines = [f"📜 **Recent Commits in [{owner}/{repo}](https://github.com/{owner}/{repo})**:\n"]
    for c in commits:
        sha = c.get("sha", "")[:7]
        c_url = c.get("html_url")
        c_author = c.get("commit", {}).get("author", {}).get("name", "Unknown")
        c_date = c.get("commit", {}).get("author", {}).get("date", "")[:10]
        c_msg = c.get("commit", {}).get("message", "").split("\n")[0]
        if len(c_msg) > 45:
            c_msg = c_msg[:42] + "..."

        lines.append(f"• [`{sha}`]({c_url}) - **{c_msg}**\n  👤 _{c_author}_ ({c_date})\n")

    await safe_edit_text(
        status_msg,
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🌐 View All Commits", url=f"https://github.com/{owner}/{repo}/commits")]
        ]),
    )


@bot.on_message(filters.command(["gitstalk", "stalk"]))
async def gitstalk_handler(_, message: Message):
    if len(message.command) < 2:
        return await message.reply(
            "❌ **Please provide a GitHub username!**\n\n"
            "**Usage:** `/gitstalk <username>`\n"
            "**Example:** `/gitstalk torvalds`"
        )

    username = message.command[1].strip().lstrip("@")
    status_msg = await message.reply(f"🔍 Stalking GitHub activity for `@{username}`...")
    token = get_user_token(message.from_user.id)
    url = f"{GITHUB_API_URL}/users/{username}/events/public?per_page=7"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=auth_headers(token), timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 404:
                    return await safe_edit_text(status_msg, f"❌ GitHub user `@{username}` not found.")
                events = await resp.json()
    except Exception as e:
        return await safe_edit_text(status_msg, f"⚠️ Error: `{e}`")

    if not events or not isinstance(events, list):
        return await safe_edit_text(status_msg, f"ℹ️ No recent public activity found for `@{username}`.")

    lines = [f"🕵️ **Recent Activity for [{username}](https://github.com/{username})**:\n"]
    for ev in events:
        ev_type = ev.get("type", "Event").replace("Event", "")
        repo_name = ev.get("repo", {}).get("name", "")
        repo_link = f"https://github.com/{repo_name}"
        ev_date = ev.get("created_at", "")[:10]

        lines.append(f"• **{ev_type}** in [{repo_name}]({repo_link}) ({ev_date})")

    await safe_edit_text(
        status_msg,
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🌐 Open Profile", url=f"https://github.com/{username}")]
        ]),
    )


@bot.on_message(filters.command(["org", "gitorg"]))
async def org_info_handler(_, message: Message):
    if len(message.command) < 2:
        return await message.reply(
            "❌ **Please provide an organization name!**\n\n"
            "**Usage:** `/org <org_name>`\n"
            "**Example:** `/org google`"
        )

    org_name = message.command[1].strip().lstrip("@")
    status_msg = await message.reply(f"🔍 Fetching organization `@{org_name}`...")
    token = get_user_token(message.from_user.id)
    url = f"{GITHUB_API_URL}/orgs/{org_name}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=auth_headers(token), timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 404:
                    return await safe_edit_text(status_msg, f"❌ GitHub organization `@{org_name}` not found.")
                data = await resp.json()
    except Exception as e:
        return await safe_edit_text(status_msg, f"⚠️ Error: `{e}`")

    name = data.get("name") or org_name
    login = data.get("login", org_name)
    html_url = data.get("html_url")
    desc = data.get("description") or "No description."
    blog = data.get("blog") or "N/A"
    location = data.get("location") or "N/A"
    repos = data.get("public_repos", 0)
    created = data.get("created_at", "")[:10]

    text = (
        f"🏢 **GitHub Organization: [{name}]({html_url})**\n\n"
        f"📝 **Description:** _{desc}_\n"
        f"📍 **Location:** `{location}`\n"
        f"🌐 **Website:** `{blog}`\n"
        f"📦 **Public Repositories:** `{repos}`\n"
        f"📅 **Created On:** `{created}`"
    )

    await safe_edit_text(
        status_msg,
        text,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🌐 View Organization", url=html_url),
                InlineKeyboardButton("📦 Repositories", url=f"https://github.com/orgs/{login}/repositories"),
            ]
        ]),
    )


# =============================================================================
# 4. MODULE DEFINITION & COMPLETE HELP DOCUMENTATION
# =============================================================================

__mod_name__ = "Github"

__help__ = """
*GitHub Power Suite & Downloader 🐙*

Complete GitHub toolkit to inspect profiles, explore repositories, download source code (public & private), and push projects directly from Telegram!

*Account & Token:*
 ❍ /setgitoken <token>*:* Set your personal GitHub token in PM (enables push & private repos).
 ❍ /mygitoken*:* Check your current saved token & linked account.
 ❍ /cleargitoken*:* Remove your saved GitHub token.

*Profile & Users:*
 ❍ /git <user>*:* View user profile, bio, stats & avatar.
 ❍ /allrepo <user>*:* List all repositories of a user.
 ❍ /gitstalk <user>*:* Track recent GitHub activity & events.
 ❍ /org <org>*:* View GitHub organization details & repos.

*Repositories & Code:*
 ❍ /repo <owner/repo>*:* Detailed repo stats (stars, forks, issues).
 ❍ /searchrepo <query>*:* Search GitHub repositories by keyword.
 ❍ /gitfile <owner/repo> <path>*:* View or download a single file.
 ❍ /commits <owner/repo>*:* View recent commit history.
 ❍ /release <owner/repo>*:* View latest release & download assets.

*Download & Push:*
 ❍ /dlrepo <repo_url>*:* Download entire repo as .zip (supports private repos if token is set).
 ❍ /gitpush <reponame>*:* Reply to any .zip to push to GitHub (interactively chooses private/public, branch, and commit).

*Interactive Push Flow:*
Reply to any `.zip` file with `/gitpush <reponame>`.
Bot will interactively prompt:
 1. 🔒 Private or 🌍 Public
 2. 🌿 Branch name (`main`, `master` or custom)
 3. 💬 Commit name (default or custom)
Then automatically create & push to your GitHub!
"""
