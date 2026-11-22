<!--
#
# Copyright (C) 2026 by Kanha-Team@Github, < https://github.com/Kanha-Team>.
# This file is part of < https://github.com/Kanha-Team/MeowRobot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE >
#
# All rights reserved.
-->

<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,19,26&height=220&section=header&text=MeowRobot&fontSize=65&fontColor=ffffff&animation=fadeIn&fontAlignY=38&desc=Next-Generation%20Telegram%20Group%20Management%20%26%20AI%20Bot&descAlignY=62&descAlign=50" width="100%" alt="MeowRobot Banner"/>
</p>

<p align="center">
  <img src="https://files.catbox.moe/4ntzos.jpg" width="300px" alt="MeowRobot" style="border-radius: 20px;" />
</p>

<p align="center">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=20&pause=1000&color=00E5FF&center=true&vCenter=true&width=650&lines=Advanced+Telegram+Group+Management+Bot;Intelligent+AI+Chatbot+Integration;Military-Grade+Lock+%26+Security+System;Automated+Night+Mode+%26+Anti-Flood+Protection;Developed+%26+Maintained+by+Kanha-Team" alt="Typing SVG" />
</p>

<p align="center">
  <a href="https://github.com/Kanha-Team/MeowRobot/stargazers">
    <img src="https://img.shields.io/github/stars/Kanha-Team/MeowRobot?color=FFD700&style=for-the-badge&logo=github&logoColor=white" alt="GitHub Stars"/>
  </a>
  <a href="https://github.com/Kanha-Team/MeowRobot/network/members">
    <img src="https://img.shields.io/github/forks/Kanha-Team/MeowRobot?color=00C853&style=for-the-badge&logo=github&logoColor=white" alt="GitHub Forks"/>
  </a>
  <a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python Version"/>
  </a>
  <a href="https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE">
    <img src="https://img.shields.io/badge/License-GNU%20v3.0-blueviolet?style=for-the-badge&logo=opensourceinitiative&logoColor=white" alt="License"/>
  </a>
</p>

<p align="center">
  <a href="https://t.me/MeowClone">
    <img src="https://img.shields.io/badge/Support%20Group-MeowClone-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white" alt="Support Group"/>
  </a>
  <a href="https://t.me/MeowCloner">
    <img src="https://img.shields.io/badge/Updates%20Channel-MeowCloner-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white" alt="Updates Channel"/>
  </a>
  <a href="https://t.me/About_Kanhaa">
    <img src="https://img.shields.io/badge/Developer-Kanha-FF6F00?style=for-the-badge&logo=telegram&logoColor=white" alt="Developer"/>
  </a>
</p>

---

<p align="center">
  <a href="#-overview"><b>Overview</b></a> •
  <a href="#-key-features"><b>Features</b></a> •
  <a href="#-quick-deployment"><b>Deployment</b></a> •
  <a href="#%EF%B8%8F-configuration-variables"><b>Configuration</b></a> •
  <a href="#%EF%B8%8F-modules--commands-overview"><b>Modules</b></a> •
  <a href="#-community--support"><b>Community</b></a> •
  <a href="#-credits--license"><b>License</b></a>
</p>

---

## 🌟 Overview

**MeowRobot** is an advanced, ultra-fast, and modular **Telegram Group Management & AI Bot** engineered to manage, protect, and energize Telegram Supergroups and Communities with absolute ease.

Built on an asynchronous dual-engine framework (**python-telegram-bot v20+** & **Pyrogram**) with a hybrid persistence model (**SQLAlchemy PostgreSQL/SQLite** + **MongoDB**), MeowRobot provides enterprise-grade moderation tools, intelligent AI chatbot conversations, an interactive scientific calculator, Telegram Stars donation invoicing, granular content locks, scheduled night mode, and automated cleanup utilities.

---

## ✨ Key Features

### 🛡️ Group Administration & Moderation
- **Advanced Moderation:** Seamlessly `/ban`, `/unban`, `/mute`, `/unmute`, `/kick` with detailed audit logs.
- **Temporary Actions:** Support for `/tban` (Temp Ban) and `/tmute` (Temp Mute) with automatic timer expirations.
- **Granular Warning Engine:** Custom warn limits, configurable punishment modes (ban/mute/kick), and warn resets.
- **Anti-Channel / Clean Linked:** Protect groups against malicious channel impersonators and forwarded spam.
- **Purge Engine:** Lightning-fast message purging (`/purge`, `/del`, `/spurge`) with asynchronous processing.

### 🔒 Military-Grade Security & Lock System
- **20+ Content Lock Types:** Lock stickers, voice notes, audio, photos, videos, GIFs, documents, forward messages, contacts, bot adds, invite links, spoilers, commands, RTL, and more.
- **Automated Anti-Flood:** High-speed flood protection that silences spam bots instantly.
- **Auto-Demote Protection:** Safeguard group administrative hierarchies against unauthorized admin demotions.
- **Anti-Edit Tracker:** Monitor and track edited messages across group conversations.

### 🤖 Intelligent AI Chatbot
- **Conversational Intelligence:** Natural context-aware replies in both Hinglish and English powered by fast AI endpoints.
- **Code Attachment Handler:** Automatically formats lengthy code blocks and scripts into clean, downloadable text files.

### 🧮 Interactive Scientific Calculator
- **Dual Mode Support:** Full inline keyboard interface supporting both standard arithmetic and scientific calculation functions (`sin`, `cos`, `tan`, `log`, `ln`, `√`, `^`, `π`, `e`).
- **Direct Calculations:** Quick inline calculations via `/calc <expression>`.

### ⭐ Telegram Stars Payments & Invoicing
- **Native Telegram Stars:** Official Star invoicing (`currency="XTR"`) for community donations via `/pay <amount>`.
- **Pre-Checkout & Receipt Verification:** Automatic checkout approvals and instant donor receipts.
- **Owner Dashboard & Refunds:** Live stars balance checker (`/stars`) with refresh animation and one-click donor refunds.

### 🗑️ Automated Message & Media Cleaner
- **Media-Del:** Automatic deletion of photos, videos, stickers, and GIFs on configurable delays (`/mediadelete`).
- **Msg-Del:** Universal message auto-deletion for clean, ephemeral chat environments (`/msgdelete`).

### 📝 Notes, Filters & Automation
- **Rich Media Filters:** Save custom keyword triggers linked to text, inline buttons, photos, stickers, or audio.
- **Modular Notes:** Group-level persistent notes system supporting button markup and private delivery.
- **Scheduled Night Mode:** Automatically restricts chat permissions during night hours based on timezone.
- **Welcome & Rules:** Instant join-request approvals and customizable welcome messages.

### 🌐 Instant Media Uploader
- **Catbox / Telegraph Uploader:** Reply to any photo, sticker, animation, or document with `/tgm` or `/tm` to get an instant, permanent CDN link.

---

## 🚀 Quick Deployment

### 1. Deploy on Heroku

Click the button below to deploy your own instance of **MeowRobot** on Heroku in one click:

<p align="center">
  <a href="https://dashboard.heroku.com/new?template=https://github.com/Kanha-Team/MeowRobot">
    <img src="https://img.shields.io/badge/Deploy%20To%20Heroku-79589F?style=for-the-badge&logo=heroku&logoColor=white" alt="Deploy on Heroku"/>
  </a>
</p>

---

### 2. Deploy on VPS / Ubuntu (Recommended)

```bash
# 1. Update system packages
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install python3 python3-pip git screen -y

# 2. Clone repository
git clone https://github.com/Kanha-Team/MeowRobot.git
cd MeowRobot

# 3. Create and activate virtual environment (Recommended)
python3 -m venv venv
source venv/bin/activate

# 4. Install dependencies
pip install -U pip setuptools wheel
pip install -U -r requirements.txt

# 5. Configure environment variables
nano .env   # Configure your credentials

# 6. Start the bot
python3 -m MeowRobot
```

---

### 3. Deploy as a Systemd Service (24/7 Uptime)

```ini
# /etc/systemd/system/meowrobot.service
[Unit]
Description=MeowRobot Telegram Management Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/MeowRobot
ExecStart=/home/ubuntu/MeowRobot/venv/bin/python3 -m MeowRobot
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start systemd service:
sudo systemctl daemon-reload
sudo systemctl enable meowrobot.service
sudo systemctl start meowrobot.service
sudo systemctl status meowrobot.service
```

---

## ⚙️ Configuration Variables

| Variable | Description | Required | Default / Example |
| :--- | :--- | :---: | :--- |
| `TOKEN` | Telegram Bot token from [@BotFather](https://t.me/BotFather) | **Yes** | `8710329984:AAEiP...` |
| `OWNER_ID` | Telegram User ID of the bot owner | **Yes** | `8617644501` |
| `API_ID` | Telegram API ID from [my.telegram.org](https://my.telegram.org) | **Yes** | `6` |
| `API_HASH` | Telegram API Hash from [my.telegram.org](https://my.telegram.org) | **Yes** | `eb06d4abfb...` |
| `DATABASE_URL` | PostgreSQL Database URL for SQL models | **Yes** | `postgresql://user:pass@localhost:5432/meowdb` |
| `MONGO_DB_URI` | MongoDB connection URI for cloud persistence | **Yes** | `mongodb+srv://...` |
| `SUPPORT_CHAT` | Telegram Support Group username | No | `MeowClone` |
| `SUPPORT_CHANNEL` | Telegram Updates Channel username | No | `MeowCloner` |
| `START_IMG` | Start command banner image URL | No | `https://files.catbox.moe/4ntzos.jpg` |
| `CHATBOT_API_URL` | AI Chatbot endpoint URL | No | `https://chatbot.riteshyt.in/api/chat` |
| `CHATBOT_API_KEY` | Bearer API Key for Chatbot engine | No | `ritesh-8179b3a5da99f...` |
| `WORKERS` | Async worker routines for update handling | No | `8` |

---

## 🗂️ Modules & Commands Overview

<details>
<summary><b>Click to expand module list</b></summary>
<br>

| Module | Primary Commands |
| :--- | :--- |
| **Admin** | `/adminlist`, `/promote`, `/demote`, `/title`, `/admincache` |
| **Bans** | `/ban`, `/sban`, `/tban`, `/unban`, `/kick`, `/punch` |
| **Muting** | `/mute`, `/smute`, `/tmute`, `/unmute` |
| **Locks** | `/lock`, `/unlock`, `/locks`, `/locktypes` |
| **Warns** | `/warn`, `/warns`, `/rmwarn`, `/resetwarn`, `/warnlimit` |
| **Notes** | `/get`, `/save`, `/clear`, `/notes`, `/saved` |
| **Filters** | `/filter`, `/stop`, `/filters`, `/stopall` |
| **Nightmode**| `/nightmode`, `/setnight`, `/rmnight` |
| **Purge** | `/purge`, `/del`, `/spurge` |
| **Couples** | `/couples`, `/cuddle` |
| **Chatbot** | `/chatbot [on/off]` |

</details>

---

## 💬 Community & Support

<p align="center">
  <a href="https://t.me/MeowClone">
    <img src="https://img.shields.io/badge/Support%20Group-MeowClone-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white" alt="Support Group"/>
  </a>
  <a href="https://t.me/MeowCloner">
    <img src="https://img.shields.io/badge/Updates%20Channel-MeowCloner-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white" alt="Updates Channel"/>
  </a>
  <a href="https://t.me/About_Kanhaa">
    <img src="https://img.shields.io/badge/Contact%20Dev-About__Kanhaa-FF6F00?style=for-the-badge&logo=telegram&logoColor=white" alt="Kanha"/>
  </a>
</p>

---

## 📜 Credits & License

- **[Kanha-Team](https://github.com/Kanha-Team)** — Lead Developer & Maintainer 🚩
- **[Paul Larsen](https://github.com/PaulSonOfLars)** — Base framework inspiration
- **[TheHamkerCat](https://github.com/TheHamkerCat)** — Modular concepts
- Special thanks to all contributors and community members!

This project is licensed under the **GNU General Public License v3.0**.  
See the [LICENSE](https://github.com/Kanha-Team/MeowRobot/blob/master/LICENSE) file for more details.
