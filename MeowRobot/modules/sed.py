#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import sre_constants
import regex
from telegram import Update
MAX_MESSAGE_LENGTH = 4096
from telegram.ext import ContextTypes, filters

from MeowRobot import LOGGER, application
from MeowRobot.modules.disable import DisableAbleMessageHandler
from MeowRobot.modules.helper_funcs.regex_helper import infinite_loop_check

DELIMITERS = ("/", ":", "|", "_")


def separate_sed(sed_string):
    if (
        len(sed_string) >= 3
        and sed_string[1] in DELIMITERS
        and sed_string.count(sed_string[1]) >= 2
    ):
        delim = sed_string[1]
        start = counter = 2
        while counter < len(sed_string):
            if sed_string[counter] == "\\":
                counter += 1

            elif sed_string[counter] == delim:
                replace = sed_string[start:counter]
                counter += 1
                start = counter
                break

            counter += 1

        else:
            return None

        while counter < len(sed_string):
            if (
                sed_string[counter] == "\\"
                and counter + 1 < len(sed_string)
                and sed_string[counter + 1] == delim
            ):
                sed_string = sed_string[:counter] + sed_string[counter + 1 :]

            elif sed_string[counter] == delim:
                replace_with = sed_string[start:counter]
                counter += 1
                break

            counter += 1
        else:
            return replace, sed_string[start:], ""

        flags = ""
        if counter < len(sed_string):
            flags = sed_string[counter:]
        return replace, replace_with, flags.lower()


async def sed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_message or not update.effective_message.text:
         return

    sed_result = separate_sed(update.effective_message.text)
    if sed_result and update.effective_message.reply_to_message:
        if update.effective_message.reply_to_message.text:
            to_fix = update.effective_message.reply_to_message.text
        elif update.effective_message.reply_to_message.caption:
            to_fix = update.effective_message.reply_to_message.caption
        else:
            return

        repl, repl_with, flags = sed_result
        if not repl:
            await update.effective_message.reply_to_message.reply_text(
                "You're trying to replace... " "nothing with something?"
            )
            return

        try:
            try:
                check = regex.match(repl, to_fix, flags=regex.IGNORECASE, timeout=5)
            except TimeoutError:
                return
            if check and check.group(0).lower() == to_fix.lower():
                await update.effective_message.reply_to_message.reply_text(
                    "Hey everyone, {} is trying to make "
                    "me say stuff I don't wanna "
                    "say!".format(update.effective_user.first_name)
                )
                return
            if infinite_loop_check(repl):
                await update.effective_message.reply_text(
                    "I'm afraid I can't run that regex."
                )
                return
            if "i" in flags and "g" in flags:
                text = regex.sub(
                    repl, repl_with, to_fix, flags=regex.I, timeout=3
                ).strip()
            elif "i" in flags:
                text = regex.sub(
                    repl, repl_with, to_fix, count=1, flags=regex.I, timeout=3
                ).strip()
            elif "g" in flags:
                text = regex.sub(repl, repl_with, to_fix, timeout=3).strip()
            else:
                text = regex.sub(repl, repl_with, to_fix, count=1, timeout=3).strip()
        except TimeoutError:
            await update.effective_message.reply_text("Timeout")
            return
        except sre_constants.error:
            LOGGER.warning(update.effective_message.text)
            LOGGER.exception("SRE constant error")
            await update.effective_message.reply_text("Do you even sed? Apparently not.")
            return

        # empty string errors -_-
        if len(text) >= MAX_MESSAGE_LENGTH:
            await update.effective_message.reply_text(
                "The result of the sed command was too long for telegram!"
            )
        elif text:
            await update.effective_message.reply_to_message.reply_text(text)


__mod_name__ = "Sed/Regex"

SED_HANDLER = DisableAbleMessageHandler(
    filters.Regex(r"s([{}]).*?\1.*".format("".join(DELIMITERS))),
    sed,
    friendly="sed",
)

application.add_handler(SED_HANDLER)

__handlers__ = [SED_HANDLER]
