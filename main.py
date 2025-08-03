# main.py

import os
import asyncio
import hashlib
import re
from datetime import datetime
import requests
import nest_asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler
from country_codes import country_codes
from database import get_status, save_status, is_duplicate, add_to_cache
from commands import *

nest_asyncio.apply()

BOT_TOKEN = "7943158999:AAG5t9je40J4Sb1p6CaCLLEfRKtckp3JWtc"
ADMIN_ID = 5359578794
WEBHOOK_URL = "https://final-otp-bot-production.up.railway.app"  # Your Railway domain

DEFAULT_CHANNEL = "https://t.me/TEAM_ELITE_X"
DEFAULT_FILE = "https://t.me/TE_X_NUMBERS"
DEFAULT_CREDIT = "𝙏𝙀𝘼𝙈 𝙀𝙇𝙄𝙏𝙀 𝙓"
DEFAULT_APIS = ["https://techflare.2cloud.top/mainapi.php"]

def extract_code(text):
    match = re.search(r'\b(\d{4,8}|\d{3}-\d{3})\b', text)
    return match.group(1).replace('-', '') if match else ""

def detect_country(number):
    number = number.replace(' ', '').replace('-', '')
    for code in sorted(country_codes.keys(), key=lambda x: -len(x)):
        if number.startswith(code) or number.startswith("+" + code):
            return country_codes[code]
    return ("Unknown", "🌍")

def format_message(entry, gid, status):
    time_now = datetime.now().strftime('%H:%M:%S')
    date_now = datetime.now().strftime('%d %B %Y')
    country, emoji = detect_country(entry["Number"])
    otp = extract_code(entry["OTP"])
    full = entry["OTP"]

    credit = status["credits"].get(str(gid), DEFAULT_CREDIT)
    main_link = status["group_links"].get(str(gid), DEFAULT_CHANNEL)
    num_file = status["group_files"].get(str(gid), status.get("link", DEFAULT_FILE))

    return (
        f"✨ <b>𝙉𝙀𝙒 𝘾𝙊𝘿𝙀 𝙍𝙀𝘾𝙀𝙄𝙑𝙀𝘿</b> ✨\n"
        f"<b>⏰ Time:</b> {time_now}\n"
        f"<b>🗓️ Date:</b> {date_now}\n"
        f"<b>🌍 Country:</b> {country} {emoji}\n"
        f"<b>⚙️ Service:</b> {entry['Platform']}\n"
        f"<b>☎️ Number:</b> <code>{entry['Number']}</code>\n"
        f"<b>🔑 OTP:</b> <code>{otp}</code>\n"
        f"✉️ <b>Full Message:</b>\n<pre>{full}</pre>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📝 Note: ~ Wait at least 30 seconds to get your requested OTP code ~\n"
        f"Pᴏᴡᴇʀᴇᴅ ʙʏ {credit}\n"
        f"Dᴇᴠᴇʟᴏᴘᴇᴅ Bʏ <a href='https://t.me/CEO_OF_TE_X'>Ariyan</a>"
    ), InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀Main Channel", url=main_link)],
        [InlineKeyboardButton("📁Numbers File", url=num_file)]
    ])

async def fetch_otps(app, status):
    if not status.get("on", True):
        return

    apis = status.get("apis", DEFAULT_APIS)
    for url in apis:
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            if not isinstance(data, list) or not data:
                continue

            new_entries = []
            for entry in data:
                uid = hashlib.md5((entry["Number"] + entry["Platform"] + entry["OTP"]).encode()).hexdigest()
                if is_duplicate(uid):
                    continue
                add_to_cache(uid)
                new_entries.append(entry)

            for entry in new_entries:
                for gid in status["groups"]:
                    text, buttons = format_message(entry, gid, status)
                    await app.bot.send_message(chat_id=gid, text=text, parse_mode="HTML", reply_markup=buttons)

            break
        except Exception as e:
            try:
                await app.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=f"⚠️ API Error:\n<pre>{str(e)}</pre>",
                    parse_mode="HTML"
                )
            except:
                print("⚠️ Failed to report error to Telegram")

def get_all_commands():
    return [
        ("start", start),
        ("on", on),
        ("off", off),
        ("status", status_cmd),
        ("addgroup", addgroup),
        ("rmvgroup", rmvgroup),
        ("addadmin", addadmin),
        ("rmvadmin", rmvadmin),
        ("cnglink", cnglink),
        ("cngcredit", cngcredit),
        ("cngcnllink", cngcnllink),
        ("cngnumlink", cngnumlink),
        ("addapi", addapi),
        ("rmvapi", rmvapi),
        ("listapis", listapis),
        ("admins", admins),
    ]

async def main():
    status = get_status()
    app = Application.builder().token(BOT_TOKEN).build()

    app.bot_data["status"] = status
    app.bot_data["save_status"] = save_status

    for cmd, func in get_all_commands():
        app.add_handler(CommandHandler(cmd, func))

    async def otp_runner():
        while True:
            await fetch_otps(app, get_status())
            await asyncio.sleep(10)

    asyncio.create_task(otp_runner())

    print("✅ Bot Running...")
    await app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        webhook_url=WEBHOOK_URL
    )

import sys

if __name__ == "__main__":
    if sys.platform.startswith("win"):
        asyncio.run(main())
    else:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())