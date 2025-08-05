from telegram import Update
from telegram.ext import ContextTypes
from database import get_status, save_status
import requests

def is_admin(user_id, status):
    return user_id in status.get("admins", [])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = get_status()
    if not is_admin(update.effective_user.id, status):
        await update.message.reply_text("❌ You are not authorized to command this bot.")
        return

    await update.message.reply_text(
        "🤖 Bot Commands:\n"
        "/on /off /status\n"
        "/addgroup <id> /rmvgroup <id>\n"
        "/addadmin <id> /rmvadmin <id>\n"
        "/cnglink <link>\n"
        "/cngcredit <group_id> <name>\n"
        "/cngcnllink <group_id> <link>\n"
        "/cngnumlink <group_id> <link>\n"
        "/addapi <url> /rmvapi <url>\n"
        "/listapis /admins"
    )

async def on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = get_status()
    if not is_admin(update.effective_user.id, status):
        await update.message.reply_text("❌ You are not authorized to command this bot.")
        return
    status["on"] = True
    save_status(status)
    await update.message.reply_text("✅ Bot is now ON.")

async def off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = get_status()
    if not is_admin(update.effective_user.id, status):
        await update.message.reply_text("❌ You are not authorized to command this bot.")
        return
    status["on"] = False
    save_status(status)
    await update.message.reply_text("🛑 Bot is now OFF.")

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = get_status()
    if not is_admin(update.effective_user.id, status):
        await update.message.reply_text("❌ You are not authorized to command this bot.")
        return

    bot_status = "ON ☑️" if status.get("on") else "OFF ❌"
    group_list = ", ".join([str(g) for g in status.get("groups", [])]) or "None"
    api_list = status.get("apis", [])
    api_text = ""
    for api in api_list:
        try:
            r = requests.get(api, timeout=5)
            r.raise_for_status()
            r.json()  # Ensure response is valid JSON
            api_text += f"{api}\n🛠️ API Status: Working ☑️\n"
        except Exception:
            api_text += f"{api}\n🛠️ API Status: Not Working ✖️\n"

    if not api_text:
        api_text = "None"

    msg = (
        f"📊 Status: {bot_status}\n"
        f"💼 Groups: {group_list}\n"
        f"📡 APIs:\n{api_text}"
    )

    await update.message.reply_text(msg)

async def addgroup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = get_status()
    if not is_admin(update.effective_user.id, status):
        await update.message.reply_text("❌ You are not authorized to command this bot.")
        return
    if len(context.args) != 1:
        await update.message.reply_text("❌ Usage: /addgroup <chat_id>")
        return
    gid = int(context.args[0])
    if gid not in status["groups"]:
        status["groups"].append(gid)
        save_status(status)
        await update.message.reply_text("✅ Group added.")
    else:
        await update.message.reply_text("⚠️ Group already exists.")

async def rmvgroup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = get_status()
    if not is_admin(update.effective_user.id, status):
        await update.message.reply_text("❌ You are not authorized to command this bot.")
        return
    if len(context.args) != 1:
        await update.message.reply_text("❌ Usage: /rmvgroup <chat_id>")
        return
    gid = int(context.args[0])
    if gid in status["groups"]:
        status["groups"].remove(gid)
        save_status(status)
        await update.message.reply_text("✅ Group removed.")
    else:
        await update.message.reply_text("⚠️ Group not found.")

async def addadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = get_status()
    if not is_admin(update.effective_user.id, status):
        await update.message.reply_text("❌ You are not authorized to command this bot.")
        return
    if len(context.args) != 1:
        await update.message.reply_text("❌ Usage: /addadmin <user_id>")
        return
    aid = int(context.args[0])
    if aid not in status["admins"]:
        status["admins"].append(aid)
        save_status(status)
        await update.message.reply_text("✅ Admin added.")
    else:
        await update.message.reply_text("⚠️ Admin already exists.")

async def rmvadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = get_status()
    if not is_admin(update.effective_user.id, status):
        await update.message.reply_text("❌ You are not authorized to command this bot.")
        return
    if len(context.args) != 1:
        await update.message.reply_text("❌ Usage: /rmvadmin <user_id>")
        return
    aid = int(context.args[0])
    if aid in status["admins"]:
        status["admins"].remove(aid)
        save_status(status)
        await update.message.reply_text("✅ Admin removed.")
    else:
        await update.message.reply_text("⚠️ Admin not found.")

async def admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = get_status()
    if not is_admin(update.effective_user.id, status):
        await update.message.reply_text("❌ You are not authorized to command this bot.")
        return
    admin_list = "\n".join([f"<code>{aid}</code>" for aid in status["admins"]])
    await update.message.reply_text(f"👮‍♂️ Current Admins:\n{admin_list or 'None'}", parse_mode="HTML")

async def cnglink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = get_status()
    if not is_admin(update.effective_user.id, status):
        await update.message.reply_text("❌ You are not authorized to command this bot.")
        return
    if len(context.args) != 1:
        await update.message.reply_text("❌ Usage: /cnglink <new_file_link>")
        return
    status["link"] = context.args[0]
    save_status(status)
    await update.message.reply_text("✅ Default numbers file link updated.")

async def cngcredit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = get_status()
    if not is_admin(update.effective_user.id, status):
        await update.message.reply_text("❌ You are not authorized to command this bot.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("❌ Usage: /cngcredit <group_id> <new_credit>")
        return
    gid = context.args[0]
    new_credit = " ".join(context.args[1:])
    status["credits"][gid] = new_credit
    save_status(status)
    await update.message.reply_text(f"✅ Credit updated for {gid}.")

async def cngcnllink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = get_status()
    if not is_admin(update.effective_user.id, status):
        await update.message.reply_text("❌ You are not authorized to command this bot.")
        return
    if len(context.args) != 2:
        await update.message.reply_text("❌ Usage: /cngcnllink <group_id> <channel_link>")
        return
    gid, link = context.args
    status["group_links"][gid] = link
    save_status(status)
    await update.message.reply_text(f"✅ Main channel link updated for {gid}.")

async def cngnumlink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = get_status()
    if not is_admin(update.effective_user.id, status):
        await update.message.reply_text("❌ You are not authorized to command this bot.")
        return
    if len(context.args) != 2:
        await update.message.reply_text("❌ Usage: /cngnumlink <group_id> <numbers_link>")
        return
    gid, link = context.args
    status["group_files"][gid] = link
    save_status(status)
    await update.message.reply_text(f"✅ Numbers file link updated for {gid}.")

async def addapi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = get_status()
    if not is_admin(update.effective_user.id, status):
        await update.message.reply_text("❌ You are not authorized to command this bot.")
        return
    if len(context.args) != 1:
        await update.message.reply_text("❌ Usage: /addapi <api_url>")
        return
    url = context.args[0]
    if url not in status["apis"]:
        status["apis"].append(url)
        save_status(status)
        await update.message.reply_text("✅ API added.")
    else:
        await update.message.reply_text("⚠️ API already exists.")

async def rmvapi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = get_status()
    if not is_admin(update.effective_user.id, status):
        await update.message.reply_text("❌ You are not authorized to command this bot.")
        return
    if len(context.args) != 1:
        await update.message.reply_text("❌ Usage: /rmvapi <api_url>")
        return
    url = context.args[0]
    if url in status["apis"]:
        status["apis"].remove(url)
        save_status(status)
        await update.message.reply_text("✅ API removed.")
    else:
        await update.message.reply_text("⚠️ API not found.")

async def listapis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = get_status()
    if not is_admin(update.effective_user.id, status):
        await update.message.reply_text("❌ You are not authorized to command this bot.")
        return
    msg = "📡 APIs:\n" + "\n".join(status["apis"])
    await update.message.reply_text(msg)
