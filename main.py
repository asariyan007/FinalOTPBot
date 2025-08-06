# main.py (with API health notification to group)

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

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
WEBHOOK_URL = os.getenv("WEBHOOK_DOMAIN", "").strip()
ADMIN_ID = 5359578794
NOTIFY_CHAT_ID = -1002820327439

if not BOT_TOKEN or not WEBHOOK_URL.startswith("https://"):
    print("❌ BOT_TOKEN or WEBHOOK_DOMAIN missing or invalid. Please set Railway variables.")
    exit(1)

DEFAULT_CHANNEL = "https://t.me/TEAM_ELITE_X"
DEFAULT_FILE = "https://t.me/TE_X_NUMBERS"
DEFAULT_CREDIT = "𝙏𝙀𝘼𝙈 𝙀𝙇𝙄𝙏𝙀 𝙓"
DEFAULT_APIS = ["https://techflare.2cloud.top/mainapi.php"]

api_status_memory = {}

def extract_code(text):
    patterns = [
        r'(?i)\b(?:FB-)?(\d{4,8})\b',
        r'#\s?(\d{4,8})\b',
        r'\b\d{3}-\d{3}\b',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).replace('-', '')
    return ""

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
        f"<b>🔑 OTP:</b> <code>{otp or 'N/A'}</code>\n"
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
    print("[DEBUG] Loaded APIs:", apis)

    for url in apis:
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            print(f"[DEBUG] API response from {url}: {data}")

            if api_status_memory.get(url) == "failed":
                await app.bot.send_message(
                    chat_id=NOTIFY_CHAT_ID,
                    text=f"✅ API is working again:\n<code>{url}</code>",
                    parse_mode="HTML"
                )
            api_status_memory[url] = "working"

            if not isinstance(data, list) or not data:
                continue

            new_entries = []
            for entry in data:
                # ✅ Skip invalid entries like {'Number': 0, 'Platform': 0, 'OTP': 0}
                if not all(isinstance(entry.get(k), str) and entry.get(k).strip() for k in ("Number", "Platform", "OTP")):
                    print("[SKIPPED] Invalid entry:", entry)
                    continue

                uid = hashlib.md5((entry["Number"] + entry["Platform"] + entry["OTP"]).encode()).hexdigest()
                print("[DEBUG] UID:", uid)

                if is_duplicate(uid):
                    print(f"[SKIPPED] Duplicate UID: {uid}")
                    continue

                add_to_cache(uid)
                new_entries.append(entry)
                print("[NEW] Added entry:", entry)

            for entry in new_entries:
                for gid in status["groups"]:
                    text, buttons = format_message(entry, gid, status)
                    await app.bot.send_message(chat_id=gid, text=text, parse_mode="HTML", reply_markup=buttons)
                    print(f"[SENT] OTP sent to group {gid}: {entry['OTP']}")

        except Exception as e:
            print(f"[ERROR] Exception from {url}: {e}")
            if api_status_memory.get(url) != "failed":
                try:
                    await app.bot.send_message(
                        chat_id=NOTIFY_CHAT_ID,
                        text=f"⚠️ API Error:\n<code>{url}</code>\n<pre>{str(e)}</pre>",
                        parse_mode="HTML"
                    )
                except:
                    print(f"⚠️ Failed to report error for {url}")
            api_status_memory[url] = "failed"

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

        # ✅ Newly added commands:
        ("broadcast", broadcast),
        ("allow", allow_group_access),
        ("disallow", disallow_group_access),
        ("permissions", view_permissions),
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
