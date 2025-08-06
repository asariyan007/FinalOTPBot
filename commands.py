from telegram import Update
from telegram.ext import ContextTypes
from database import get_status, save_status
import requests

OWNER_ID = 5359578794

def is_owner(user_id):
    return user_id == OWNER_ID

def is_admin(user_id, status):
    return user_id in status.get("admins", [])

def has_limited_access(user_id, status):
    return is_owner(user_id) or is_admin(user_id, status)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = get_status()
    user_id = update.effective_user.id

    if is_owner(user_id):
        await update.message.reply_text(
            "🤖 Bot Commands:\n"
            "/on /off /status\n"
            "/addgroup <id> /rmvgroup <id>\n"
            "/addadmin <id> /rmvadmin <id>\n"
            "/allow <admin_id> <group_id1> <group_id2>...\n"
            "/disallow <admin_id> <group_id1> <group_id2>...\n"
            "/permissions\n"
            "/cnglink <link>\n"
            "/cngcredit <group_id> <name>\n"
            "/cngcnllink <group_id> <link>\n"
            "/cngnumlink <group_id> <link>\n"
            "/addapi <url> /rmvapi <url>\n"
            "/listapis /admins\n"
            "/broadcast <message>"
        )
    elif is_admin(user_id, status):
        await update.message.reply_text(
            "🤖 Admin Commands:\n"
            "/on /off /status\n"
            "/listapis"
        )
    else:
        await update.message.reply_text("❌ You are not authorized to use this bot.")

# /on
async def on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = get_status()
    user_id = update.effective_user.id

    if is_owner(user_id):
        status["on"] = True
        save_status(status)
        await update.message.reply_text("✅ Bot is now ON.")
        return

    if is_admin(user_id, status):
        allowed_groups = status.get("admin_permissions", {}).get(str(user_id), [])
        if not allowed_groups:
            await update.message.reply_text("❌ You are not allowed to control any group.")
            return
        status["on"] = True
        save_status(status)
        await update.message.reply_text("✅ Bot is now ON for your allowed groups.")
        return

    await update.message.reply_text("❌ You are not authorized.")

# /off
async def off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = get_status()
    user_id = update.effective_user.id

    if is_owner(user_id):
        status["on"] = False
        save_status(status)
        await update.message.reply_text("🛑 Bot is now OFF.")
        return

    if is_admin(user_id, status):
        allowed_groups = status.get("admin_permissions", {}).get(str(user_id), [])
        if not allowed_groups:
            await update.message.reply_text("❌ You are not allowed to control any group.")
            return
        status["on"] = False
        save_status(status)
        await update.message.reply_text("🛑 Bot is now OFF for your allowed groups.")
        return

    await update.message.reply_text("❌ You are not authorized.")

# /status
async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = get_status()
    user_id = update.effective_user.id

    if not has_limited_access(user_id, status):
        await update.message.reply_text("❌ You are not authorized to command this bot.")
        return

    bot_status = "ON ☑️" if status.get("on") else "OFF ❌"
    group_list = ", ".join([str(g) for g in status.get("groups", [])]) or "None"
    api_text = ""

    for api in status.get("apis", []):
        try:
            r = requests.get(api, timeout=5)
            r.raise_for_status()
            r.json()
            api_text += f"{api}\n🛠️ API Status: Working ☑️\n"
        except Exception:
            api_text += f"{api}\n🛠️ API Status: Not Working ✖️\n"

    msg = (
        f"📊 Status: {bot_status}\n"
        f"💼 Groups: {group_list}\n"
        f"📡 APIs:\n{api_text or 'None'}"
    )
    await update.message.reply_text(msg)

# /broadcast (owner only)
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = get_status()
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("❌ Only owner can broadcast.")
        return

    if not context.args:
        await update.message.reply_text("❌ Usage: /broadcast <message>")
        return

    msg = "📢 " + " ".join(context.args)

    for gid in status.get("groups", []):
        try:
            await context.bot.send_message(chat_id=gid, text=msg)
        except:
            pass

    for uid in status.get("admins", []):
        try:
            await context.bot.send_message(chat_id=uid, text=msg)
        except:
            pass

    await update.message.reply_text("✅ Broadcast sent.")

# Admin Group Permissions Commands
async def allow_group_access(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = get_status()
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("❌ Only owner can assign permissions.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("❌ Usage: /allow <admin_id> <group_id1> <group_id2> ...")
        return

    aid = context.args[0]
    gids = context.args[1:]

    if "admin_permissions" not in status:
        status["admin_permissions"] = {}

    if aid not in status["admin_permissions"]:
        status["admin_permissions"][aid] = []

    for gid in gids:
        if gid not in status["admin_permissions"][aid]:
            status["admin_permissions"][aid].append(gid)

    save_status(status)
    await update.message.reply_text(f"✅ Admin {aid} now has access to: {', '.join(gids)}")

async def disallow_group_access(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = get_status()
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("❌ Only owner can remove permissions.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("❌ Usage: /disallow <admin_id> <group_id1> <group_id2> ...")
        return

    aid = context.args[0]
    gids = context.args[1:]

    if "admin_permissions" in status and aid in status["admin_permissions"]:
        status["admin_permissions"][aid] = [
            gid for gid in status["admin_permissions"][aid] if gid not in gids
        ]
        save_status(status)
        await update.message.reply_text(f"✅ Removed access for admin {aid} to: {', '.join(gids)}")
    else:
        await update.message.reply_text("⚠️ Admin or permissions not found.")

async def view_permissions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = get_status()
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("❌ Only owner can view permissions.")
        return

    msg = "🧾 Admin Group Permissions:\n\n"
    perms = status.get("admin_permissions", {})

    if not perms:
        msg += "No permissions set."
    else:
        for aid, gids in perms.items():
            msg += f"👤 <code>{aid}</code> ➤ {', '.join(gids)}\n"

    await update.message.reply_text(msg, parse_mode="HTML")

# Missing Basic Admin Commands
async def addgroup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = get_status()
    if not is_owner(update.effective_user.id):
        return await update.message.reply_text("❌ Only owner can use this.")
    if context.args:
        gid = context.args[0]
        if gid not in status["groups"]:
            status["groups"].append(gid)
            save_status(status)
            await update.message.reply_text(f"✅ Group {gid} added.")
        else:
            await update.message.reply_text("⚠️ Group already added.")
    else:
        await update.message.reply_text("❌ Usage: /addgroup <group_id>")

async def rmvgroup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = get_status()
    if not is_owner(update.effective_user.id):
        return await update.message.reply_text("❌ Only owner can use this.")
    if context.args:
        gid = context.args[0]
        if gid in status["groups"]:
            status["groups"].remove(gid)
            save_status(status)
            await update.message.reply_text(f"✅ Group {gid} removed.")
        else:
            await update.message.reply_text("⚠️ Group not found.")
    else:
        await update.message.reply_text("❌ Usage: /rmvgroup <group_id>")

async def addadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = get_status()
    if not is_owner(update.effective_user.id):
        return await update.message.reply_text("❌ Only owner can use this.")
    if context.args:
        aid = int(context.args[0])
        if aid not in status["admins"]:
            status["admins"].append(aid)
            save_status(status)
            await update.message.reply_text(f"✅ Admin {aid} added.")
        else:
            await update.message.reply_text("⚠️ Already an admin.")
    else:
        await update.message.reply_text("❌ Usage: /addadmin <user_id>")

async def rmvadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = get_status()
    if not is_owner(update.effective_user.id):
        return await update.message.reply_text("❌ Only owner can use this.")
    if context.args:
        aid = int(context.args[0])
        if aid in status["admins"]:
            status["admins"].remove(aid)
            save_status(status)
            await update.message.reply_text(f"✅ Admin {aid} removed.")
        else:
            await update.message.reply_text("⚠️ Admin not found.")
    else:
        await update.message.reply_text("❌ Usage: /rmvadmin <user_id>")

async def cnglink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = get_status()
    if not is_owner(update.effective_user.id):
        return await update.message.reply_text("❌ Only owner can use this.")
    if context.args:
        status["link"] = context.args[0]
        save_status(status)
        await update.message.reply_text(f"✅ Link changed.")
    else:
        await update.message.reply_text("❌ Usage: /cnglink <link>")

async def cngcredit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = get_status()
    if not is_owner(update.effective_user.id):
        return await update.message.reply_text("❌ Only owner can use this.")
    if len(context.args) >= 2:
        gid = context.args[0]
        name = " ".join(context.args[1:])
        status["credits"][gid] = name
        save_status(status)
        await update.message.reply_text(f"✅ Credit updated for group {gid}.")
    else:
        await update.message.reply_text("❌ Usage: /cngcredit <group_id> <name>")

async def cngcnllink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = get_status()
    if not is_owner(update.effective_user.id):
        return await update.message.reply_text("❌ Only owner can use this.")
    if len(context.args) >= 2:
        gid = context.args[0]
        link = context.args[1]
        status["group_links"][gid] = link
        save_status(status)
        await update.message.reply_text(f"✅ Main Channel link updated for group {gid}.")
    else:
        await update.message.reply_text("❌ Usage: /cngcnllink <group_id> <link>")

async def cngnumlink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = get_status()
    if not is_owner(update.effective_user.id):
        return await update.message.reply_text("❌ Only owner can use this.")
    if len(context.args) >= 2:
        gid = context.args[0]
        link = context.args[1]
        status["group_files"][gid] = link
        save_status(status)
        await update.message.reply_text(f"✅ Numbers File link updated for group {gid}.")
    else:
        await update.message.reply_text("❌ Usage: /cngnumlink <group_id> <link>")

async def addapi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = get_status()
    if not is_owner(update.effective_user.id):
        return await update.message.reply_text("❌ Only owner can use this.")
    if context.args:
        url = context.args[0]
        if url not in status["apis"]:
            status["apis"].append(url)
            save_status(status)
            await update.message.reply_text("✅ API added.")
        else:
            await update.message.reply_text("⚠️ API already exists.")
    else:
        await update.message.reply_text("❌ Usage: /addapi <url>")

async def rmvapi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = get_status()
    if not is_owner(update.effective_user.id):
        return await update.message.reply_text("❌ Only owner can use this.")
    if context.args:
        url = context.args[0]
        if url in status["apis"]:
            status["apis"].remove(url)
            save_status(status)
            await update.message.reply_text("✅ API removed.")
        else:
            await update.message.reply_text("⚠️ API not found.")
    else:
        await update.message.reply_text("❌ Usage: /rmvapi <url>")

async def listapis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = get_status()
    if not has_limited_access(update.effective_user.id, status):
        return await update.message.reply_text("❌ You are not authorized.")
    apis = status.get("apis", [])
    if apis:
        await update.message.reply_text("📡 APIs:\n" + "\n".join(apis))
    else:
        await update.message.reply_text("⚠️ No APIs set.")

async def admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = get_status()
    if not is_owner(update.effective_user.id):
        return await update.message.reply_text("❌ Only owner can use this.")
    admins_list = status.get("admins", [])
    if admins_list:
        await update.message.reply_text("👮 Admins:\n" + "\n".join([str(a) for a in admins_list]))
    else:
        await update.message.reply_text("⚠️ No admins added.")
