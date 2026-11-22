#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.

import asyncio
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

from MeowRobot import application
from MeowRobot.modules.helper_funcs.chat_status import is_user_admin
import MeowRobot.modules.sql.abuse_sql as user_sql
import MeowRobot.modules.sql.admin_abuse_sql as admin_sql
import unicodedata

def normalize_text(text):
    return unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("utf-8").lower()

ABUSE_WORDS = [
    "sex", "porn", "nude", "fuck", "bitch", "dick", "pussy", "slut", "boobs", "cock", "asshole", "chudai", "rand", "chhinar", "sexy", "hot girl", "land", "lund",
    "रंडी", "चोद", "मादरचोद", "गांड", "लंड", "भोसड़ी", "हिजड़ा", "पागल", "नंगा",
    # ✅ Common Hindi Gaaliyan
    "चूतिया", "मादरचोद", "बहनचोद", "गांडू", "रंडी", "भोसड़ी", "हिजड़ा", "लंड", "चोद", "झाटू", "हरामी", "कमीन", 
    "साला", "गांड", "पागल", "भड़वा", "चुत", "बेवकूफ", "कमीना", "निकम्मा", "हरामखोर", "चालू", "फट्टू", "ढक्कन", 
    "गधे", "कुत्ते", "साले", "बंदर", "सुअर", "बेशरम", "भोसड़ीवाले", "तेरी मां की", "तेरी बहन की", "चूतड़", "हरामज़ादा", 
    "हराम की औलाद", "सुअर का बच्चा", "गधे का लौड़ा", "लौंडा", "भड़वी", "मुफ्तखोर", "चालाक लोमड़ी", "आवारा", "फटीचर", 
    "फेंकू", "धोखेबाज", "मतलबी", "कायर", "नाकारा", "आवारा लड़का", "बेशर्म", "नालायक", "फेकू", "गंदा आदमी", "नाकाम", 
    "निकम्मी", "अकड़ू", "गटर का कीड़ा", "अंधभक्त", "गंजा", "पाखंडी", "चिरकुट", "घटिया", "सड़ियल", "चोर", "गटरछाप", 
    "लुटेरा", "छिछोरा", "बदतमीज़", "बददिमाग", "फ्रॉड", "नालायक", "बेवड़ा", "संडास", "गंदा", "ढोंगी", "भिखारी", 
    "फालतू", "कचरा", "पागल कुत्ता", "बदमाश", "आलसी", "कंजूस", "घमंडी", "फर्जी", "धूर्त", "बकचोद", "गप्पी", "फेंकू", 
    "बेवकूफी", "बेवड़ा", "फ्रॉड", "टटी", "भांड", "नाकारा", "कमीनी", "लंपट", "सैडिस्ट", "लफंगा", "बकवास", "घटिया", 
    "चिचोरा", "छिछोरा", "मक्खनचूस", "लफंगा", "तेरा बाप", "तेरी मां", "तेरी बहन", "तेरी औकात", "तेरी औकात क्या", 
    "तेरी फटी", "तेरी बैंड", "तेरा बैंड", "तेरी वाट", "तेरी बैंड बजा दूं", "तेरी ऐसी की तैसी", "तेरी टांग तोड़ दूं", 
    "तेरी खोपड़ी फोड़ दूं", "तेरा भेजा निकाल दूं", "तेरी हड्डी तोड़ दूं", "तेरी चप्पल से पिटाई करूंगा", "तेरी हड्डियां चूर-चूर",
    

    # ✅ Common Hindi Gaaliyan in English Font
    "chutiya", "madarchod", "Madhrachod", "Madharchod", "betichod", "behenchod", "gandu", "randi", "bhosdi", "hijda", "lund", "chod", "jhaatu", 
    "harami", "kamina", "saala", "gand", "pagal", "bhadwa", "chut", "bevkoof", "nikkamma", "haramkhor", 
    "chaalu", "fattuu", "dhakkan", "gadha", "kutta", "suvar", "besharam", "bhosdike", "teri maa ki", 
    "teri behan ki", "chutad", "haramzaada", "haram ki aulaad", "suvar ka baccha", "gand ka keeda", 
    "chirkut", "ghatiya", "sadela", "choor", "lutera", "chichora", "badtameez", "baddimag", "fraud", 
    "nalayak", "bewda", "sandass", "ganda", "dhongi", "bhikhari", "faltu", "kachra", "pagal kutta", 
    "badmash", "aalsi", "kanjoos", "ghamandi", "farzi", "dhurt", "bakchod", "gappi", "nakli", "chalu", 
    "lafanga", "bakwas", "bikau", "chapri", "nalla", "tatti", "jhantu", "ullu ka pattha", "ulloo", 
    "chindi", "panauti", "lukkha", "kuttiya", "kaminey", "kamzarf", "budbak", "chirkut", "sust", "tharki", 
    "bhagoda", "kutta kamina", "bhains ki aankh", "teri taang tod dunga", "teri band baja dunga", 
    "tera dimaag kharab hai", "teri waat laga dunga", "teri maa ka bhosda", "teri gaand maar dunga",

    
    # ✅ Common Porn & NSFW Terms (Mix of Hindi & English)
    "sex", "porn", "nude", "nangi", "chudai", "bhabhi chudai", "lund", "gaand", "bhosda", "chut", 
    "maal", "jism", "randi", "randi khana", "desi sex", "hot video", "nangi ladki", "bhabhi nudes", 
    "bhabhi sex", "sexy aunty", "nude aunty", "bhabhi ki chut", "aunty ki chut", "boobs", "tits", 
    "nipple", "dildo", "pussy", "vagina", "penis", "cock", "dick", "cum", "anal", "squirt", "deepthroat", 
    "hentai", "bdsm", "lesbian", "gay sex", "futa", "69", "screwing", "sex chat", "incest", "stepmom", 
    "stepsis", "stepbro", "honeymoon sex", "bhabhi nude", "hot indian actress", "desi nudes", 
    "sexy saree", "lingerie", "erotic", "kinky", "naughty", "sensual", "lust", "muth", "muthi", 
    "masturbation", "call girl", "escort", "sex worker", "rape porn", "forced porn", "underage porn", 
    "child porn", "pedo", "loli", "teen sex", "schoolgirl porn", "hijab porn", "casting couch", 
    "sex tape", "strip club", "naked", "uncensored", "bikini photos", "hot saree", "sexy photos", 
    "onlyfans", "patreon nudes", "hot cam", "sex cam", "live sex", "private parts", "exposed", 
    "naked selfie", "sex video", "desi sex video", "bollywood sex", "lingam massage", "tantra sex", 
    "milf", "hotwife", "swinger", "erotic massage", "boobs press", "licking", "lick pussy", 
    "moaning", "dirty talk", "hot girl", "big boobs", "tight pussy", "wet pussy", "hard cock", 
    "big cock", "blowjob", "handjob", "sexy dance", "strip tease", "sex position", "saree sex", 
    "sexy aunty video", "hot desi bhabhi", "bollywood hot", "item girl", "hot indian model", 
    "desi randi", "desi call girl", "sexy night", "hijra sex", "chudai story", "sex story", 
    "suhagraat sex", "honeymoon night", "love making", "hot romance", "desi romance", "hot chat", 
    "sexy time", "naughty chat", "dirty video", "hidden cam", "bathroom sex", "hotel sex", 
    "massage sex", "body to body massage", "saree romance", "choli romance", "cleavage show", 
    "hot navel", "desi thighs", "big ass", "backside show", "fuck","fucker","fucking","motherfucker","mf","bitch","bitches","bastard","asshole","ass","shit","bullshit",
"dumbass","jackass","idiot","moron","loser","jerk","retard","stupid","trash","scumbag","dipshit","douche",
"douchebag","prick","slut","whore","skank","twat","wanker","arsehole","bloody fool","imbecile",

# 🔴 Variations / Bypass
"f*ck","f**k","fucck","fuk","phuck","fook","fuxk","fuker","fuking",
"b!tch","biatch","bich","btch","b*tch",
"sh!t","shyt","shittt","shiit","sh1t",
"a$$","asss","azz","a55","a*s",

# 🔴 Sexual / NSFW
"sex","porn","xxx","nude","naked","boobs","tits","nipple","pussy","dick","cock","penis","vagina",
"cum","anal","blowjob","handjob","deepthroat","squirt","orgasm","masturbation","hentai","bdsm",
"fetish","erotic","kinky","lust","sexual","hardcore","softcore","threesome","gangbang","strip",
"stripper","stripclub","onlyfans","camgirl","webcam","sexcam","pornhub","xvideos","xnxx","redtube",

# 🔴 Sexual Slang
"horny","sexy","hotgirl","hotboy","milf","dilf","nsfw","lewd","naughty","dirtytalk",
"seduce","foreplay","hookup","one night stand","quickie",

# 🔴 Porn Keywords
"sexvideo","pornvideo","nudevideo","xxxvideo","hotvideo","dirtyvideo",
"live sex","sex chat","private show","adult content","uncensored","explicit",

# 🔴 Drugs
"drug","drugs","cocaine","heroin","weed","marijuana","cannabis","hash","lsd","mdma","ecstasy",
"meth","crystal meth","opium","morphine","smack","dope","acid","psychedelic","joint","blunt",
"stoned","high","drugdealer","narcotics","overdose","addict","addiction",

# 🔴 Alcohol / Smoking
"alcohol","beer","whiskey","vodka","rum","wine","tequila","drunk","drunkard","hangover",
"cigarette","cigar","smoking","tobacco","nicotine","vape","hookah","weed smoke",

# 🔴 Toxic / Internet Slang
"noob","n00b","loser","crybaby","clown","bozo","trash player","kiddo","wannabe",
"tryhard","sucker","lame","pathetic","cringe","toxic","salty","triggered",

# 🔴 Misc Dirty / Unsafe
"escort","callgirl","sexworker","adultservice","paid sex","prostitute",
"illegal link","blackmarket","human trafficking","hitman","contract killing"
    
]
# ================= COMMANDS ================= #

async def abuse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    if not await is_user_admin(chat, user.id):
        await update.message.reply_text("❌ Admins only.")
        return

    if not context.args:
        await update.message.reply_text("Use: /abuse on or off")
        return

    if context.args[0].lower() == "on":
        user_sql.enable_abuse(chat.id)
        await update.message.reply_text("👤 User Abuse ENABLED")
    elif context.args[0].lower() == "off":
        user_sql.disable_abuse(chat.id)
        await update.message.reply_text("👤 User Abuse DISABLED")

# ---------------- ADMIN ---------------- #

async def adminabuse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    if not await is_user_admin(chat, user.id):
        await update.message.reply_text("❌ Admins only.")
        return

    if not context.args:
        await update.message.reply_text("Use: /adminabuse on or off")
        return

    if context.args[0].lower() == "on":
        admin_sql.enable(chat.id)
        await update.message.reply_text("👑 Admin Abuse ENABLED")
    elif context.args[0].lower() == "off":
        admin_sql.disable(chat.id)
        await update.message.reply_text("👑 Admin Abuse DISABLED")

# ---------------- STATS ---------------- #

async def abusestats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat

    user_status = "ON ✅" if user_sql.is_abuse(chat.id) else "OFF ❌"
    admin_status = "ON 🔥" if admin_sql.is_on(chat.id) else "OFF ❌"

    await update.message.reply_text(
        f"🚫 Abuse Status\n\n"
        f"👤 User Abuse : {user_status}\n"
        f"👑 Admin Abuse : {admin_status}"
    )

# ================= WATCHER ================= #

async def abuse_watch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if not msg or not msg.text:
        return

    text = normalize_text(msg.text)

    user_mode = user_sql.is_abuse(chat.id)
    admin_mode = admin_sql.is_on(chat.id)

    for bad in ABUSE_WORDS:
        if bad in text:
            # USER MODE
            if user_mode and not await is_user_admin(chat, user.id):
                await msg.delete()

            # ADMIN MODE
            elif admin_mode and await is_user_admin(chat, user.id):
                await msg.delete()
            else:
                return

            warn = await context.bot.send_message(
                chat.id,
                f"🚫 {user.first_name}, abusive words not allowed!"
            )
            await asyncio.sleep(5)
            try:
                await warn.delete()
            except:
                pass
            break

# ================= HANDLERS ================= #
__help__ = """
*Abuse Control System*

➤ /abuse on/off  
» Enable or disable abuse filter for *users only*

➤ /adminabuse on/off  
» Enable or disable abuse filter for *admins only*

➤ /abusestats  
» Show current abuse filter status

❖ Notes:
• User mode → only users messages deleted  
• Admin mode → only admins messages deleted  
• Both ON → both filtered
"""

__mod_name__ = "Abuse"


application.add_handler(CommandHandler("abuse", abuse))
application.add_handler(CommandHandler("adminabuse", adminabuse))
application.add_handler(CommandHandler("abusestats", abusestats))

application.add_handler(
    MessageHandler(
        filters.TEXT & filters.ChatType.GROUPS & ~filters.COMMAND,
        abuse_watch
    )
)
