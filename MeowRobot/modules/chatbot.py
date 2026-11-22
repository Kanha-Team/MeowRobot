#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import os
import re
import random
import asyncio
from io import BytesIO
from collections import OrderedDict

import requests
from functools import partial

try:
    import edge_tts
except ImportError:
    edge_tts = None

try:
    from gtts import gTTS
except ImportError:
    gTTS = None

try:
    import speech_recognition as sr
except ImportError:
    sr = None

try:
    from pydub import AudioSegment
except ImportError:
    AudioSegment = None

from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus, ChatAction

from MeowRobot import pbot as app, DRAGONS, DEV_USERS, LOGGER, CHATBOT_API_URL, CHATBOT_API_KEY
from MeowRobot.utils.mongo import chatbot_db as DB

API_URL = os.environ.get("CHATBOT_API_URL", CHATBOT_API_URL or "https://chatbot.riteshyt.in/api/chat")
API_KEY = os.environ.get("CHATBOT_API_KEY", CHATBOT_API_KEY or "ritesh-8179b3a5da99f300be2d50e1e9789729")
CUTE_GIRL_VOICE = os.environ.get("CHATBOT_VOICE", "hi-IN-SwaraNeural")
TRIGGERS = ["hi", "hello", "hey", "baby", "meow", "kanha", "anu"]

class LRUCache:
    def __init__(self, capacity: int):
        self.cache = OrderedDict()
        self.capacity = capacity
        
    def get(self, key):
        if key not in self.cache:
            return []
        self.cache.move_to_end(key)
        return self.cache[key]
        
    def put(self, key, value):
        self.cache[key] = value
        self.cache.move_to_end(key)
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)

# Conversation history tracking (chat_id -> list of messages)
# Max 1000 chats in memory to prevent leaks
chat_histories = LRUCache(1000)
HISTORY_LIMIT = 30

async def is_admin(message: Message, user_id: int):
    if user_id in DRAGONS or user_id in DEV_USERS:
        return True
    try:
        member = await app.get_chat_member(message.chat.id, user_id)
        return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)
    except:
        return False

def load_prompt():
    try:
        path = os.path.join(os.path.dirname(__file__), "prompt.txt")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()
    except:
        pass
    return "You are a sweet, friendly girl chatting naturally in Hinglish and English. Keep replies very short and human-like. User is {user_name}. Never admit you are an AI."

SYSTEM_PROMPT = load_prompt()

@app.on_message(filters.command("chatbot") & filters.group)
async def chatbot_toggle(_, message: Message):
    if not await is_admin(message, message.from_user.id):
        return await message.reply_text("❗ Only admins can use this command.")

    if len(message.command) < 2:
        return await message.reply_text("Usage:\n/chatbot on - Enable\n/chatbot off - Disable")

    arg = message.command[1].lower()
    if arg == "on":
        await DB.update_one({"chat_id": message.chat.id}, {"$set": {"enabled": True}}, upsert=True)
        await message.reply_text("✅ Chatbot is now ENABLED in this group.")
    elif arg == "off":
        await DB.update_one({"chat_id": message.chat.id}, {"$set": {"enabled": False}}, upsert=True)
        await message.reply_text("❌ Chatbot is now DISABLED in this group.")
    else:
        await message.reply_text("Invalid argument. Use `on` or `off`.")

@app.on_message(filters.command("voice") & filters.group)
async def voice_toggle(_, message: Message):
    if not await is_admin(message, message.from_user.id):
        return await message.reply_text("❗ Only admins can use this command.")

    if len(message.command) < 2:
        return await message.reply_text("Usage:\n/voice on - Enable Voice Mode (Bot will reply with Audio)\n/voice off - Disable Voice Mode (Bot will reply with Text)")

    arg = message.command[1].lower()
    if arg == "on":
        await DB.update_one({"chat_id": message.chat.id}, {"$set": {"voice_enabled": True}}, upsert=True)
        await message.reply_text("🎙 Voice Mode is now ENABLED. I will reply with audio notes!")
    elif arg == "off":
        await DB.update_one({"chat_id": message.chat.id}, {"$set": {"voice_enabled": False}}, upsert=True)
        await message.reply_text("📝 Voice Mode is now DISABLED. I will reply with text.")
    else:
        await message.reply_text("Invalid argument. Use `on` or `off`.")

def clean_text_for_tts(text: str) -> str:
    # Remove code blocks or file tags
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"`[^`]*`", "", text)
    # Remove markdown symbols and links
    text = re.sub(r"[\*\_~]", "", text)
    text = re.sub(r"https?://\S+", "", text)
    # Clean emojis/symbols that TTS might read literally
    # Keep Hindi (\u0900-\u097F), English, numbers, spaces, and basic punctuation
    text = re.sub(r"[^\w\s\.,!\?\"\u0900-\u097F]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

async def text_to_speech(text: str) -> BytesIO:
    clean = clean_text_for_tts(text)
    if not clean:
        clean = "Hie!"

    mp3_fp = BytesIO()
    generated = False

    # 1. Primary: Microsoft Edge Neural Voice (ultra realistic cute girl voice)
    if edge_tts:
        try:
            communicate = edge_tts.Communicate(
                clean,
                voice="hi-IN-SwaraNeural",
                rate="+5%",
                pitch="+12Hz"
            )
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    mp3_fp.write(chunk["data"])
            if mp3_fp.tell() > 0:
                mp3_fp.seek(0)
                generated = True
        except Exception as e:
            LOGGER.warning(f"edge-tts error: {e}, falling back to gTTS")
            mp3_fp = BytesIO()

    # 2. Fallback: gTTS if edge-tts failed
    if not generated and gTTS:
        loop = asyncio.get_event_loop()
        def _gtts():
            fp = BytesIO()
            tts = gTTS(clean, lang="hi")
            tts.write_to_fp(fp)
            fp.seek(0)
            return fp
        mp3_fp = await loop.run_in_executor(None, _gtts)
    elif not generated and not gTTS:
        raise RuntimeError("No TTS engine available (neither edge-tts nor gTTS).")

    # 3. Convert mp3 to Telegram ogg opus via pydub
    if AudioSegment:
        try:
            loop = asyncio.get_event_loop()
            def _convert():
                audio = AudioSegment.from_file(mp3_fp, format="mp3")
                ogg_fp = BytesIO()
                ogg_fp.name = "voice.ogg"
                audio.export(ogg_fp, format="ogg", codec="libopus")
                ogg_fp.seek(0)
                return ogg_fp
            return await loop.run_in_executor(None, _convert)
        except Exception as e:
            LOGGER.error(f"Pydub audio export error: {e}")
            mp3_fp.name = "voice.mp3"
            return mp3_fp
    else:
        mp3_fp.name = "voice.mp3"
        return mp3_fp

async def fetch_chat_response(payload: dict) -> dict:
    loop = asyncio.get_event_loop()
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    max_retries = 3

    for attempt in range(max_retries):
        try:
            response = await loop.run_in_executor(
                None,
                lambda: requests.post(API_URL, json=payload, headers=headers, timeout=60),
            )
            if response.status_code == 200:
                data = response.json()
                reply = data.get("response") or data.get("reply") or data.get("message")
                if isinstance(reply, dict):
                    reply = reply.get("content", "")
                if reply and "503" not in reply and "系统通知" not in reply:
                    return {"response": reply}
                elif attempt < max_retries - 1:
                    await asyncio.sleep(2)
                    continue
            elif response.status_code in [429, 500, 502, 503] and attempt < max_retries - 1:
                await asyncio.sleep(2)
                continue
            else:
                break
        except (requests.exceptions.RequestException, asyncio.TimeoutError):
            if attempt < max_retries - 1:
                await asyncio.sleep(2)
                continue
            break
        except Exception as e:
            LOGGER.error(f"Chatbot request error: {e}")
            break

    # Offline Cute Fallback Messages
    fallbacks = [
        "Aww thoda connection issue ho raha hai mera, ek baar fir bolo na? 💕",
        "Hmm suno na, thoda network glitch aa gaya... fir se kehna! 🥺",
        "Arey internet thoda nakhre dikha raha hai, kya kaha aapne? 🙈",
        "Main sun rahi hoon! Thodi awaaz kat gayi, ek baar dobara bolna please? ✨",
    ]
    return {"response": random.choice(fallbacks)}

async def transcribe_voice(file_path: str) -> str:
    loop = asyncio.get_event_loop()
    def _transcribe():
        if not AudioSegment or not sr:
            LOGGER.error("Voice transcription requires pydub and speech_recognition.")
            return ""
        wav_path = file_path + ".wav"
        try:
            # Convert OGG to WAV using pydub (requires ffmpeg installed on host)
            audio = AudioSegment.from_ogg(file_path)
            audio.export(wav_path, format="wav")
            
            recognizer = sr.Recognizer()
            with sr.AudioFile(wav_path) as source:
                audio_data = recognizer.record(source)
                # Use Google STT with hi-IN language to catch both Hindi and English
                text = recognizer.recognize_google(audio_data, language="hi-IN")
            
            return text
        except Exception as e:
            LOGGER.error(f"STT Error: {e}")
            return ""
        finally:
            if os.path.exists(wav_path):
                os.remove(wav_path)
            
    return await loop.run_in_executor(None, _transcribe)

@app.on_message((filters.text | filters.caption | filters.voice) & ~filters.regex(r"^/") & ~filters.bot, group=10)
async def chatbot_handler(_, message: Message):
    chat_id = message.chat.id
    voice_enabled = False

    # Check database early so we don't process voice/text if bot is disabled in this group
    if message.chat.type != message.chat.type.PRIVATE:
        settings = await DB.find_one({"chat_id": chat_id})
        if not settings or not settings.get("enabled", False):
            return
        voice_enabled = settings.get("voice_enabled", False)

    input_text = message.text or message.caption

    # Handle incoming voice messages
    if message.voice:
        try:
            await app.send_chat_action(chat_id, ChatAction.TYPING)
            downloaded_file = await message.download()
            input_text = await transcribe_voice(downloaded_file)
            if os.path.exists(downloaded_file):
                os.remove(downloaded_file)
            if not input_text:
                return
        except Exception as e:
            LOGGER.error(f"Voice handling error: {e}")
            if "ffprobe" in str(e).lower() or "ffmpeg" in str(e).lower():
                await message.reply_text("❗ Voice feature requires `ffmpeg` installed on the server.")
            return

    if not input_text:
        return

    text_lower = input_text.lower().strip()

    # Fetch dynamic bot information (whichever bot is hosting this repo)
    bot = app.me or (await app.get_me())
    bot_username = (bot.username or "").lower() if bot else ""
    bot_id = bot.id if bot else 0

    is_reply_to_bot = bool(
        message.reply_to_message and message.reply_to_message.from_user and
        message.reply_to_message.from_user.id == bot_id
    )

    is_mentioned = False
    if bot_username:
        if f"@{bot_username}" in text_lower:
            is_mentioned = True
        elif message.entities:
            for ent in message.entities:
                if ent.type.name == "MENTION":
                    mention_text = input_text[ent.offset:ent.offset + ent.length].lower()
                    if mention_text == f"@{bot_username}":
                        is_mentioned = True
                        break

    # In groups: ONLY reply when user tags THIS specific bot or replies to THIS bot
    if message.chat.type != message.chat.type.PRIVATE:
        if not (is_mentioned or is_reply_to_bot):
            return

    # Clean the bot username tag from input_text
    if bot_username:
        input_text = re.sub(rf"(?i)@{re.escape(bot_username)}\b", "", input_text).strip()

    # Handle "single tag": user just sent @botusername without any extra prompt text
    if not input_text:
        single_tag_prompts = [
            "meow",
            "hey",
            "haan bolo",
            "hi",
            "suno na"
        ]
        input_text = random.choice(single_tag_prompts)

    user_name = message.from_user.first_name if message.from_user else "Friend"
    group_name = message.chat.title if message.chat else "Private Chat"
    
    prompt = SYSTEM_PROMPT.replace("{user_name}", user_name)
    prompt += f"\n\nYou are talking in a group named: {group_name}. Be helpful and engaging."

    # Update history
    history = chat_histories.get(chat_id)
    history.append({"role": "user", "content": f"{user_name}: {input_text}"})
    if len(history) > HISTORY_LIMIT:
        history = history[-HISTORY_LIMIT:]
    chat_histories.put(chat_id, history)

    history_str = "\n".join([f"[{m['role']}]: {m['content']}" for m in history])
    formatted_prompt = f"System: {prompt}\n\nRecent Chat Context:\n{history_str}\n\nUser: {input_text}\nAssistant:"

    messages_payload = [{"role": "system", "content": prompt}] + history

    payload = {
        "messages": messages_payload,
        "prompt": formatted_prompt,
    }

    # Decide if we send a voice note this time. 
    # If explicitly enabled, always True. 
    # If the user sent a voice message, we definitely reply with a voice message to match their energy.
    # Otherwise, give a 15% random chance in normal mode to keep it natural.
    if message.voice:
        should_send_voice = True
    else:
        should_send_voice = True if voice_enabled else (random.random() < 0.15)

    try:
        action = ChatAction.RECORD_AUDIO if should_send_voice else ChatAction.TYPING
        await app.send_chat_action(chat_id, action)
    except:
        pass

    try:
        data = await fetch_chat_response(payload)
        if data:
            reply = data.get("reply") or data.get("message") or data.get("response")
            if isinstance(reply, dict):
                reply = reply.get("content", "")
            if reply:
                # Add assistant response to history
                current_history = chat_histories.get(chat_id)
                current_history.append({"role": "assistant", "content": reply})
                chat_histories.put(chat_id, current_history)

                # Extract and handle long code blocks
                code_blocks = re.findall(r'```([a-zA-Z]*)\n(.*?)```', reply, re.DOTALL)
                files_to_send = []
                
                for lang, code in code_blocks:
                    lines = code.strip().split('\n')
                    if len(lines) > 5:
                        ext = f".{lang}" if lang else ".txt"
                        if lang == "python": ext = ".py"
                        elif lang in ("javascript", "js"): ext = ".js"
                        elif lang == "html": ext = ".html"
                        elif lang == "css": ext = ".css"
                        elif lang == "json": ext = ".json"
                        elif lang in ("cpp", "c++"): ext = ".cpp"
                        elif lang == "sh" or lang == "bash": ext = ".sh"

                        filename = f"code_snippet{ext}"
                        file_obj = BytesIO(code.strip().encode('utf-8'))
                        file_obj.name = filename
                        files_to_send.append(file_obj)

                        original_block = f"```{lang}\n{code}```"
                        reply = reply.replace(original_block, f"**[Long code block sent as file: {filename}]**")

                if reply.strip():
                    if should_send_voice and not code_blocks and (edge_tts or gTTS): # Only send voice if there's no code block and TTS available
                        try:
                            voice_fp = await text_to_speech(reply)
                            await message.reply_voice(voice=voice_fp)
                        except Exception as e:
                            LOGGER.error(f"TTS error: {e}")
                            await message.reply_text(reply) # Fallback to text
                    else:
                        await message.reply_text(reply)

                for f in files_to_send:
                    await message.reply_document(document=f)
    except Exception as e:
        LOGGER.error(f"Chatbot error: {e}")

__mod_name__ = "Cʜᴀᴛʙᴏᴛ"
__help__ = """
AI Chatbot for your group.

 ❍ /chatbot <on/off>*:* Toggle AI chatbot in group.
 ❍ /voice <on/off>*:* Toggle Voice Mode (Bot replies with audio notes).
 ❍ Bot responds only when tagged (@BotUsername) or replied to.
"""