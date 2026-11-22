#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import io
from gtts import gTTS
from pyrogram import filters

from MeowRobot import pbot as app

@app.on_message(filters.command("tts"))
async def text_to_speech(client, message):
    if len(message.command) < 2:
        return await message.reply_text("Please provide some text to convert to speech.")

    text = message.text.split(None, 1)[1]
    tts = gTTS(text, lang="hi")
    audio_data = io.BytesIO()
    tts.write_to_fp(audio_data)
    audio_data.seek(0)

    audio_file = io.BytesIO(audio_data.read())
    audio_file.name = "audio.mp3"
    await message.reply_audio(audio_file)

__mod_name__ = "Tᴛs"
__help__ = """
Convert text to speech.

 ❍ /tts <text>*:* Generate an audio file from the provided text.
"""
