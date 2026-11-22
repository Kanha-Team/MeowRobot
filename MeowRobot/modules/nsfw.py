#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import os
import asyncio
import subprocess
import httpx
from pyrogram import filters, Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import RPCError, MessageDeleteForbidden
from pyrogram.enums import ChatMemberStatus

from MeowRobot import pbot as bot, NSFW_LOG_CHANNEL as LOG_CHANNEL, NSFW_STORAGE, DRAGONS, DEV_USERS
from MeowRobot.utils.mongo import nsfw_db as NSFW, nsfw_settings as groups

os.makedirs("temp", exist_ok=True)

# Global timeout for HTTP requests
TIMEOUT = httpx.Timeout(20.0, connect=10.0)
HF_NSFW_API = "https://nexacoders-nexa-api.hf.space/scan"
API4AI_URL = "https://demo.api4ai.cloud/nsfw/v1/results"
API4AI_KEY = "a4a-p3htHPSXFeCnvAZ21nLkRtRPGUFFTaJV"

# Helpers for Pyrogram
async def is_admin(message: Message, user_id: int):
    if user_id in DRAGONS or user_id in DEV_USERS:
        return True
    try:
        member = await bot.get_chat_member(message.chat.id, user_id)
        return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)
    except:
        return False

async def get_target_user(message: Message):
    if message.reply_to_message:
        return message.reply_to_message.from_user.id
    if len(message.command) > 1:
        user = message.command[1]
        try:
            if user.isdigit():
                return int(user)
            u = await bot.get_users(user)
            return u.id
        except:
            return None
    return None

async def scan_hf(image_path: str):
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        with open(image_path, "rb") as f:
            r = await client.post(
                HF_NSFW_API,
                files={"file": ("scan.jpg", f, "image/jpeg")}
            )
    if r.status_code != 200:
        raise RuntimeError("HF API failed")
    s = r.json()["scores"]
    porn, hentai, sexy = s["porn"] * 100, s["hentai"] * 100, s["sexy"] * 100
    return {
        "porn": round(porn, 2), "hentai": round(hentai, 2), "sexy": round(sexy, 2),
        "neutral": round(s["neutral"] * 100, 2), "drawings": round(s["drawings"] * 100, 2),
        "sfw": (porn + hentai + sexy) < 60
    }

async def scan_api4ai(image_path: str):
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        with open(image_path, "rb") as f:
            r = await client.post(
                API4AI_URL,
                headers={"A4AI-KEY": API4AI_KEY},
                files={"image": f}
            )
    if r.status_code != 200:
        raise RuntimeError("API4AI failed")
    data = r.json()
    results = data.get("results", [])
    if not results: raise RuntimeError("API4AI empty results")
    classes = results[0].get("entities", [])[0].get("classes", {})
    scores = {k: round(v * 100, 2) for k, v in classes.items()}
    return {
        "porn": scores.get("porn", 0), "hentai": scores.get("hentai", 0), "sexy": scores.get("sexual", 0),
        "neutral": scores.get("neutral", 0), "drawings": scores.get("drawing", 0),
        "sfw": scores.get("nsfw", 0) < 60
    }

async def get_media_result(message: Message):
    media = (message.photo or message.video or message.animation or message.sticker or
             (message.document if message.document and message.document.mime_type == "image/gif" else None))
    if not media: return {"error": "Unsupported media type"}

    unique_file_id = media.file_unique_id
    cached = await NSFW.find_one({"unique_file_id": unique_file_id})
    if cached: return cached

    local_path = None
    try:
        if message.photo:
            local_path = await message.download(f"temp/{unique_file_id}.jpg")
        else:
            tmp = await message.download(f"temp/{unique_file_id}")
            local_path = f"temp/{unique_file_id}.jpg"
            subprocess.run(["ffmpeg", "-i", tmp, "-frames:v", "1", "-q:v", "3", local_path],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            if os.path.exists(tmp): os.remove(tmp)
            if not os.path.exists(local_path): return {"error": "ffmpeg failed to extract frame"}

        hf_task = asyncio.create_task(scan_hf(local_path))
        api4ai_task = asyncio.create_task(scan_api4ai(local_path))
        hf_result, api4ai_result = await asyncio.gather(hf_task, api4ai_task, return_exceptions=True)

        if isinstance(hf_result, Exception): hf_result = None
        if isinstance(api4ai_result, Exception): api4ai_result = None
        if not hf_result and not api4ai_result: return {"error": "All NSFW engines failed"}

        def best(key):
            return max((hf_result.get(key, 0) if hf_result else 0), (api4ai_result.get(key, 0) if api4ai_result else 0))

        results = {"porn": best("porn"), "hentai": best("hentai"), "sexy": best("sexy"),
                   "neutral": best("neutral"), "drawings": best("drawings")}
        sfw = True
        if hf_result and not hf_result["sfw"]: sfw = False
        if api4ai_result and not api4ai_result["sfw"]: sfw = False

        doc = {"unique_file_id": unique_file_id, "results": results, "sfw": sfw}
        await NSFW.insert_one(doc)
        if not sfw and NSFW_STORAGE:
            try: await message.forward(NSFW_STORAGE)
            except: pass
        return doc
    finally:
        if local_path and os.path.exists(local_path): os.remove(local_path)

@bot.on_message(filters.command("nsfw") & filters.group)
async def nsfw_cmd(client: bot, message: Message):
    if not await is_admin(message, message.from_user.id):
        return await message.reply_text("❗ You must be an admin to use this command.")

    if len(message.command) != 2:
        return await message.reply("❗ **Usage:**\n`/nsfw enable` – Turn ON NSFW scan\n`/nsfw disable` – Turn OFF NSFW scan")

    arg = message.command[1].lower()
    if arg == "enable":
        await groups.update_one({"_id": message.chat.id}, {"$set": {"toggle_scan": True}}, upsert=True)
        await message.reply("✔️ **NSFW Protection Enabled**")
    elif arg == "disable":
        await groups.update_one({"_id": message.chat.id}, {"$set": {"toggle_scan": False}}, upsert=True)
        await message.reply("🛑 **NSFW Protection Disabled**")
    else:
        await message.reply("❗ Use only `enable` or `disable`")

@bot.on_message(filters.command("nsfwmsg") & filters.group)
async def nsfw_msg_cmd(client: bot, message: Message):
    if not await is_admin(message, message.from_user.id):
        return await message.reply_text("❗ You must be an admin to use this command.")

    if len(message.command) != 2:
        return await message.reply("❗ **Usage:**\n`/nsfwmsg enable` – NSFW alert ON\n`/nsfwmsg disable` – NSFW alert OFF")

    arg = message.command[1].lower()
    if arg == "enable":
        await groups.update_one({"_id": message.chat.id}, {"$set": {"toggle_notify": True}}, upsert=True)
        await message.reply("🔔 **NSFW Notification Enabled**")
    elif arg == "disable":
        await groups.update_one({"_id": message.chat.id}, {"$set": {"toggle_notify": False}}, upsert=True)
        await message.reply("🔕 **NSFW Notification Disabled**")
    else:
        await message.reply("❗ Use only `enable` or `disable`")

@bot.on_message(filters.command("nsfwadmin") & filters.group)
async def nsfw_admin_cmd(client: bot, message: Message):
    if not await is_admin(message, message.from_user.id):
        return await message.reply_text("❗ You must be an admin to use this command.")

    if len(message.command) != 2:
        return await message.reply("❗ **Usage:**\n`/nsfwadmin on` – Scan admins too\n`/nsfwadmin off` – Skip admins")

    arg = message.command[1].lower()
    if arg == "on":
        await groups.update_one({"_id": message.chat.id}, {"$set": {"scan_admins": True}}, upsert=True)
        await message.reply("🔞 **NSFW Scan for Admins: ENABLED**")
    elif arg == "off":
        await groups.update_one({"_id": message.chat.id}, {"$set": {"scan_admins": False}}, upsert=True)
        await message.reply("🛡️ **NSFW Scan for Admins: DISABLED**")
    else:
        await message.reply("❗ Use only `on` or `off`")

@bot.on_message(filters.command("nsfwstats") & filters.group)
async def nsfw_stats_cmd(client: bot, message: Message):
    if not await is_admin(message, message.from_user.id):
        return await message.reply("❗ You must be an admin to view group status.")

    doc = await groups.find_one({"_id": message.chat.id}) or {}
    def icon(v: bool): return "✅" if v else "❌"
    text = (f"⚙️ **Group Security Status**\n\n"
            f"🔍 NSFW Scan        : {icon(doc.get('toggle_scan', False))}\n"
            f"📢 NSFW Alert       : {icon(doc.get('toggle_notify', False))}\n"
            f"👑 Scan Admins      : {icon(doc.get('scan_admins', False))}\n")
    await message.reply(text)

@bot.on_message(filters.command("scan"))
async def scan_cmd(client: bot, message: Message):
    if not message.reply_to_message:
        return await message.reply("⚠️ Reply to a media (image, video, GIF, sticker).")

    doc = await get_media_result(message.reply_to_message)
    if "error" in doc: return await message.reply(f"❌ Error: {doc['error']}")

    results, sfw = doc["results"], doc["sfw"]
    header = "**✅ The Content Is Safe.**" if sfw else "**NSFW DETECTED 🔞**"
    await message.reply(f"{header}\n\n**Details:**\n"
                         f"Drawings: {results.get('drawings',0):.2f}%\n"
                         f"Neutral: {results.get('neutral',0):.2f}%\n"
                         f"P*rn: {results.get('porn',0):.2f}%\n"
                         f"Hentai: {results.get('hentai',0):.2f}%\n"
                         f"Sexy: {results.get('sexy',0):.2f}%\n")

@bot.on_message((filters.photo | filters.video | filters.animation | filters.sticker) & filters.group, group=-1)
async def auto_scan_handler(client: bot, message: Message):
    if not message.from_user: return
    chat_id = message.chat.id
    user_id = message.from_user.id

    grp = await groups.find_one({"_id": chat_id})
    if not grp or not grp.get("toggle_scan", False): return

    # Skip approved users
    if user_id in grp.get("users", []):
        return

    # Skip admins unless scan_admins is True
    if await is_admin(message, user_id) and not grp.get("scan_admins", False):
        return

    doc = await get_media_result(message)
    if "error" in doc or doc.get("sfw", True): return

    try: await message.delete()
    except (MessageDeleteForbidden, RPCError):
        await groups.update_one({"_id": chat_id}, {"$set": {"toggle_scan": False}})
        await message.reply_text("⚠️ I can't delete messages here. NSFW scanning disabled.")
        return

    if grp.get("toggle_notify", False):
        warn = await message.reply_text(f"🔞 NSFW content detected & removed, {message.from_user.mention}!")
        await asyncio.sleep(10)
        try: await warn.delete()
        except: pass

    if LOG_CHANNEL:
        log_text = (f"**NSFW DETECTED 🔞**\n\n"
                    f"User: {message.from_user.mention} ({user_id})\n"
                    f"Chat: {message.chat.title} ({chat_id})\n")
        try: await client.send_message(LOG_CHANNEL, log_text)
        except: pass

@bot.on_message(filters.command("marknsfw") & filters.group)
async def mark_as_nsfw(client: bot, message: Message):
    if message.from_user.id not in DRAGONS and message.from_user.id not in DEV_USERS:
        return
    if not message.reply_to_message: return await message.reply("⚠️ Reply to a media message.")
    media = (message.reply_to_message.photo or message.reply_to_message.video or
             message.reply_to_message.animation or message.reply_to_message.sticker)
    if not media: return await message.reply("❌ No media.")
    await NSFW.update_one({"unique_file_id": media.file_unique_id}, {"$set": {"sfw": False}}, upsert=True)
    await message.reply("🔞 Marked as NSFW.")

@bot.on_message(filters.command("marksfw") & filters.group)
async def mark_as_sfw(client: bot, message: Message):
    if message.from_user.id not in DRAGONS and message.from_user.id not in DEV_USERS:
        return
    if not message.reply_to_message: return await message.reply("⚠️ Reply to a media message.")
    media = (message.reply_to_message.photo or message.reply_to_message.video or
             message.reply_to_message.animation or message.reply_to_message.sticker)
    if not media: return await message.reply("❌ No media.")
    await NSFW.update_one({"unique_file_id": media.file_unique_id}, {"$set": {"sfw": True}}, upsert=True)
    await message.reply("🟢 Marked as SFW.")

@bot.on_message(filters.command("nsfwfree") & filters.group)
async def approve_user(client: bot, message: Message):
    if not await is_admin(message, message.from_user.id):
        return await message.reply_text("❗ Admins only.")

    target_id = await get_target_user(message)
    if not target_id:
        return await message.reply("📝 Usage: `/nsfwfree @username` or reply to a user.")

    try:
        target = await bot.get_users(target_id)
    except:
        return await message.reply("❌ Invalid user.")

    await groups.update_one({"_id": message.chat.id}, {"$addToSet": {"users": target.id}}, upsert=True)
    await message.reply(f"🔖 `{target.first_name}` is now approved and ignored from NSFW scanning.")

@bot.on_message(filters.command("nsfwunfree") & filters.group)
async def disapprove_user(client: bot, message: Message):
    if not await is_admin(message, message.from_user.id):
        return await message.reply_text("❗ Admins only.")

    target_id = await get_target_user(message)
    if not target_id:
        return await message.reply("📝 Usage: `/nsfwunfree @username` or reply to a user.")

    await groups.update_one({"_id": message.chat.id}, {"$pull": {"users": target_id}})
    await message.reply(f"🔖 User `{target_id}` will now be scanned normally again.")

@bot.on_message(filters.command("nsfwlist") & filters.group)
async def list_approved(client: bot, message: Message):
    if not await is_admin(message, message.from_user.id):
        return await message.reply_text("❗ Admins only.")

    doc = await groups.find_one({"_id": message.chat.id})
    if not doc or not doc.get("users"):
        return await message.reply("📌 No approved users in this group.")

    text = f"📌 **Approved Users**:\n\n"
    for uid in doc["users"]:
        try:
            u = await bot.get_users(uid)
            text += f"• [{u.first_name}](tg://user?id={uid}) (`{uid}`)\n"
        except:
            text += f"• `{uid}`\n"
    await message.reply(text)

@bot.on_message(filters.command("nsfwunfeeall") & filters.group)
async def disapprove_all(client: bot, message: Message):
    if not await is_admin(message, message.from_user.id):
        return await message.reply_text("❗ Admins only.")

    await groups.update_one({"_id": message.chat.id}, {"$set": {"users": []}})
    await message.reply("🗑️ All approved users have been removed.")

__mod_name__ = "NSFW"
__help__ = """
NSFW detection using AI.

 ❍ /scan*:* Scan the replied media.
 ❍ /nsfw <enable/disable>*:* Toggle auto scanning in group (Admins only).
 ❍ /nsfwmsg <enable/disable>*:* Toggle notifications when NSFW is removed.
 ❍ /nsfwadmin <on/off>*:* Toggle whether admins are scanned too.
 ❍ /nsfwstats*:* View group NSFW security status.
 ❍ /nsfwfree*:* Approve a user to skip scanning.
 ❍ /nsfwunfree*:* Unapprove a user.
 ❍ /nsfwlist*:* List all approved users.
 ❍ /nsfwunfeeall*:* Remove all approved users.
 ❍ /marknsfw*:* Manually mark media as NSFW (Sudo only).
 ❍ /marksfw*:* Manually mark media as SFW (Sudo only).
"""
