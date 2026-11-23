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
import tempfile
import aiohttp
from pyrogram import filters
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    CallbackQuery,
)

from MeowRobot import pbot as bot

GITHUB_API_URL = "https://api.github.com"
HEADERS = {
    "User-Agent": "MeowRobot-TelegramBot",
    "Accept": "application/vnd.github.v3+json",
}


def parse_repo_input(raw: str):
    """Extract owner and repo name from a URL or owner/repo format."""
    raw = raw.strip().rstrip("/")
    m = re.search(r"(?:https?://)?(?:www\.)?github\.com/([^/\s]+)/([^/\s?#]+)", raw)
    if m:
        owner = m.group(1)
        repo = m.group(2)
        if repo.endswith(".git"):
            repo = repo[:-4]
        return owner, repo
    m2 = re.match(r"^([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+)$", raw)
    if m2:
        owner = m2.group(1)
        repo = m2.group(2)
        if repo.endswith(".git"):
            repo = repo[:-4]
        return owner, repo
    return None, None


@bot.on_message(filters.command(["git", "github"]))
async def git_user_info(_, message: Message):
    username = None
    if len(message.command) > 1:
        username = message.command[1].strip().lstrip("@")
    elif message.reply_to_message and message.reply_to_message.text:
        text = message.reply_to_message.text.strip()
        # Check if replied text contains a github link or username
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

    url = f"{GITHUB_API_URL}/users/{username}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 404:
                    return await status_msg.edit(f"❌ **GitHub user** `@{username}` **not found.**")
                if resp.status != 200:
                    return await status_msg.edit(f"⚠️ **GitHub API error:** HTTP {resp.status}")
                data = await resp.json()
    except Exception as e:
        return await status_msg.edit(f"⚠️ **Error connecting to GitHub:** `{e}`")

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
            return await message.reply_photo(
                photo=avatar_url,
                caption=caption,
                reply_markup=keyboard,
            )
        except Exception:
            pass

    return await message.reply_text(
        caption,
        reply_markup=keyboard,
        disable_web_page_preview=True,
    )


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
    url = f"{GITHUB_API_URL}/users/{username}/repos?per_page=100&sort=updated"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                if resp.status == 404:
                    text = f"❌ **GitHub user** `@{username}` **not found.**"
                    if status_msg:
                        return await status_msg.edit(text)
                    return await message.reply(text)
                if resp.status != 200:
                    text = f"⚠️ **GitHub API error:** HTTP {resp.status}"
                    if status_msg:
                        return await status_msg.edit(text)
                    return await message.reply(text)
                repos = await resp.json()
    except Exception as e:
        text = f"⚠️ **Error connecting to GitHub:** `{e}`"
        if status_msg:
            return await status_msg.edit(text)
        return await message.reply(text)

    if not repos:
        text = f"ℹ️ **User** `@{username}` **has no public repositories.**"
        if status_msg:
            return await status_msg.edit(text)
        return await message.reply(text)

    total_count = len(repos)
    display_limit = 12
    output_lines = [
        f"📦 **Public Repositories of [{username}](https://github.com/{username})** ({total_count} total):\n"
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
        output_lines.append(
            f"ℹ️ _Showing top {display_limit} most recently updated repos._"
        )

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
        await status_msg.edit(
            text_body,
            reply_markup=keyboard,
            disable_web_page_preview=True,
        )
    else:
        await message.reply(
            text_body,
            reply_markup=keyboard,
            disable_web_page_preview=True,
        )


@bot.on_callback_query(filters.regex(r"^allrepo_(.+)"))
async def allrepo_callback(_, query: CallbackQuery):
    username = query.matches[0].group(1)
    await query.answer("Fetching repositories...")
    await send_user_repositories(query.message, username)


@bot.on_message(filters.command(["dlrepo", "gitdl", "repopack"]))
async def dlrepo_handler(_, message: Message):
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
            "❌ **Please provide a GitHub repository link or owner/repo!**\n\n"
            "**Usage:** `/dlrepo <repo_url or owner/repo>`\n"
            "**Examples:**\n"
            "• `/dlrepo Kanha-Team/MeowRobot`\n"
            "• `/dlrepo https://github.com/Kanha-Team/MeowRobot`"
        )

    owner, repo = parse_repo_input(raw_target)
    if not owner or not repo:
        return await message.reply(
            "❌ **Invalid repository format!**\n"
            "Please provide a valid URL like `https://github.com/owner/repo` or `owner/repo`."
        )

    status_msg = await message.reply(f"🔍 Fetching repository details for `{owner}/{repo}`...")

    # Fetch repo details from GitHub API
    repo_url = f"{GITHUB_API_URL}/repos/{owner}/{repo}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(repo_url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 404:
                    return await status_msg.edit(f"❌ **Repository** `{owner}/{repo}` **not found or is private.**")
                if resp.status != 200:
                    return await status_msg.edit(f"⚠️ **GitHub API error:** HTTP {resp.status}")
                repo_data = await resp.json()
    except Exception as e:
        return await status_msg.edit(f"⚠️ **Error fetching repository details:** `{e}`")

    default_branch = repo_data.get("default_branch", "master")
    full_name = repo_data.get("full_name", f"{owner}/{repo}")
    stars = repo_data.get("stargazers_count", 0)
    forks = repo_data.get("forks_count", 0)
    desc = repo_data.get("description") or "No description provided."
    size_kb = repo_data.get("size", 0)

    # Sanity check on repo size: if > 300MB, warn user
    if size_kb > 300 * 1024:
        return await status_msg.edit(
            f"⚠️ **Repository is too large** (~{round(size_kb / 1024, 1)} MB).\n"
            f"Telegram upload limit for bot accounts is 50MB."
        )

    await status_msg.edit(f"⏳ Downloading `{full_name}` (Branch: `{default_branch}`)...")

    zip_url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/zipball/{default_branch}"
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, f"{owner}_{repo}_{default_branch}.zip")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                zip_url,
                headers=HEADERS,
                allow_redirects=True,
                timeout=aiohttp.ClientTimeout(total=180),
            ) as resp:
                if resp.status != 200:
                    return await status_msg.edit(f"❌ **Failed to download archive:** HTTP {resp.status}")

                with open(file_path, "wb") as f:
                    while True:
                        chunk = await resp.content.read(64 * 1024)
                        if not chunk:
                            break
                        f.write(chunk)

        file_size = os.path.getsize(file_path)
        # Check if file exceeds 50MB (Telegram standard bot API document upload threshold)
        if file_size > 50 * 1024 * 1024:
            size_mb = round(file_size / (1024 * 1024), 2)
            return await status_msg.edit(
                f"❌ **Archive is too large ({size_mb} MB).**\n"
                f"Telegram bots cannot send documents exceeding 50 MB."
            )

        await status_msg.edit("📤 Uploading zip archive to Telegram...")

        caption = (
            f"📦 **Repository:** [{full_name}](https://github.com/{owner}/{repo})\n"
            f"🌿 **Branch:** `{default_branch}`\n"
            f"⭐ **Stars:** `{stars}` | 🍴 **Forks:** `{forks}`\n"
            f"📝 **Description:** _{desc}_\n\n"
            f"⚡ **Downloaded via MeowRobot**"
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 View on GitHub", url=f"https://github.com/{owner}/{repo}")]
        ])

        await message.reply_document(
            document=file_path,
            file_name=f"{repo}-{default_branch}.zip",
            caption=caption,
            reply_markup=keyboard,
        )
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit(f"❌ **Error while downloading/uploading archive:**\n`{e}`")

    finally:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass


__mod_name__ = "Github"

__help__ = """
*GitHub Tools & Downloader 🐙*

View GitHub profiles, list public repositories, and download repository zip archives directly!

*Commands:*
 ❍ /git : ғɪηᴅ ɢɪᴛʜᴜʙ ᴀᴄᴄᴏᴜɴᴛ.
 ❍ /allrepo : ᴧʟʟ ʀєᴘᴏ ʙʏ ɢɪᴛ ᴜsєʀηᴧϻє.
 ❍ /dlrepo : ᴅσᴡηʟσᴧᴅ ᴢɪᴘ ʙʏ ʀєᴘᴏ ᴜʀʟ.

*Examples:*
• `/git torvalds`
• `/allrepo Kanha-Team`
• `/dlrepo Kanha-Team/MeowRobot`
"""
