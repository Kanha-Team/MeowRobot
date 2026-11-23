#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team >.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import os
import re
import tempfile
import time

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


# =============================================================================
# GITHUB EXPLORATION & UTILITY COMMANDS
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
    url = f"{GITHUB_API_URL}/users/{username}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=BASE_HEADERS, timeout=aiohttp.ClientTimeout(total=15)) as resp:
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
    url = f"{GITHUB_API_URL}/users/{username}/repos?per_page=100&sort=updated"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=BASE_HEADERS, timeout=aiohttp.ClientTimeout(total=20)) as resp:
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
    """Download repository archive as .zip."""
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
            "**Example:** `/dlrepo Kanha-Team/MeowRobot`"
        )

    owner, repo = parse_repo_input(raw_target)
    if not owner or not repo:
        return await message.reply("❌ Invalid format! Provide `owner/repo` or a valid GitHub URL.")

    status_msg = await message.reply(f"🔍 Fetching repository details for `{owner}/{repo}`...")
    repo_url = f"{GITHUB_API_URL}/repos/{owner}/{repo}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(repo_url, headers=BASE_HEADERS, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 404:
                    return await safe_edit_text(status_msg, f"❌ Repository `{owner}/{repo}` not found.")
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
                headers=BASE_HEADERS,
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

    status_msg = await message.reply(f"🔍 Fetching `{owner}/{repo}`...")
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=BASE_HEADERS, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 404:
                    return await safe_edit_text(
                        status_msg,
                        f"❌ Repository `{owner}/{repo}` not found.",
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
    url = f"{GITHUB_API_URL}/search/repositories?q={query}&per_page=7&sort=stars"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=BASE_HEADERS, timeout=aiohttp.ClientTimeout(total=15)) as resp:
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

    status_msg = await message.reply(f"🔍 Fetching `{file_path}` from `{owner}/{repo}`...")
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/contents/{file_path}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=BASE_HEADERS, timeout=aiohttp.ClientTimeout(total=15)) as resp:
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
            async with session.get(download_url, headers=BASE_HEADERS, timeout=aiohttp.ClientTimeout(total=20)) as resp:
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

    status_msg = await message.reply(f"🔍 Fetching latest release for `{owner}/{repo}`...")
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/releases/latest"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=BASE_HEADERS, timeout=aiohttp.ClientTimeout(total=15)) as resp:
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

    status_msg = await message.reply(f"🔍 Fetching recent commits for `{owner}/{repo}`...")
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/commits?per_page=6"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=BASE_HEADERS, timeout=aiohttp.ClientTimeout(total=15)) as resp:
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
    url = f"{GITHUB_API_URL}/users/{username}/events/public?per_page=7"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=BASE_HEADERS, timeout=aiohttp.ClientTimeout(total=15)) as resp:
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
    url = f"{GITHUB_API_URL}/orgs/{org_name}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=BASE_HEADERS, timeout=aiohttp.ClientTimeout(total=15)) as resp:
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
# MODULE DEFINITION & HELP DOCUMENTATION
# =============================================================================

__mod_name__ = "Github"

__help__ = """
*GitHub Power Suite & Downloader 🐙*

Complete GitHub toolkit to inspect profiles, explore repositories, download source code, and track activity directly from Telegram!

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

*Download:*
 ❍ /dlrepo <repo_url>*:* Download repository archive as .zip.
"""
