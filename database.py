import sqlite3

DB_FILE = "bot_data.db"

# === INITIAL SETUP ===
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS status (
        id INTEGER PRIMARY KEY,
        is_on BOOLEAN,
        link TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        user_id INTEGER PRIMARY KEY
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS groups (
        group_id INTEGER PRIMARY KEY
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS apis (
        url TEXT PRIMARY KEY
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS credits (
        group_id INTEGER PRIMARY KEY,
        credit TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS group_links (
        group_id INTEGER PRIMARY KEY,
        link TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS group_files (
        group_id INTEGER PRIMARY KEY,
        file TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS otp_cache (
        uid TEXT PRIMARY KEY
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS admin_permissions (
        admin_id INTEGER,
        group_id INTEGER,
        PRIMARY KEY (admin_id, group_id)
    )
    """)

    # Insert default if not exist
    c.execute("SELECT COUNT(*) FROM status")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO status (id, is_on, link) VALUES (1, 1, 'https://t.me/TE_X_NUMBERS')")

    c.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (5359578794)")
    c.execute("INSERT OR IGNORE INTO groups (group_id) VALUES (-1002825600269)")
    c.execute("INSERT OR IGNORE INTO apis (url) VALUES ('https://techflare.2cloud.top/mainapi.php')")
    c.execute("INSERT OR IGNORE INTO credits (group_id, credit) VALUES (-1002825600269, '𝙏𝙀𝘼𝙈 𝙀𝙇𝙄𝙏𝙀 𝙓')")
    c.execute("INSERT OR IGNORE INTO group_links (group_id, link) VALUES (-1002825600269, 'https://t.me/TEAM_ELITE_X')")
    c.execute("INSERT OR IGNORE INTO group_files (group_id, file) VALUES (-1002825600269, 'https://t.me/TE_X_NUMBERS')")

    conn.commit()
    conn.close()

# === LOAD STATUS ===
def get_status():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("SELECT is_on, link FROM status WHERE id = 1")
    status_row = c.fetchone()

    c.execute("SELECT user_id FROM admins")
    admins = [row[0] for row in c.fetchall()]

    c.execute("SELECT group_id FROM groups")
    groups = [row[0] for row in c.fetchall()]

    c.execute("SELECT url FROM apis")
    apis = [row[0] for row in c.fetchall()]

    c.execute("SELECT group_id, credit FROM credits")
    credits = {str(row[0]): row[1] for row in c.fetchall()}

    c.execute("SELECT group_id, link FROM group_links")
    group_links = {str(row[0]): row[1] for row in c.fetchall()}

    c.execute("SELECT group_id, file FROM group_files")
    group_files = {str(row[0]): row[1] for row in c.fetchall()}

    c.execute("SELECT admin_id, group_id FROM admin_permissions")
    raw_permissions = c.fetchall()
    admin_permissions = {}
    for aid, gid in raw_permissions:
        admin_permissions.setdefault(aid, []).append(gid)

    conn.close()

    return {
        "on": bool(status_row[0]) if status_row else True,
        "link": status_row[1] if status_row else "https://t.me/TE_X_NUMBERS",
        "admins": admins,
        "groups": groups,
        "apis": apis,
        "credits": credits,
        "group_links": group_links,
        "group_files": group_files,
        "admin_permissions": admin_permissions
    }

# === SAVE STATUS ===
def save_status(data):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("UPDATE status SET is_on = ?, link = ? WHERE id = 1", (int(data["on"]), data["link"]))

    c.execute("DELETE FROM admins")
    for uid in data["admins"]:
        c.execute("INSERT INTO admins (user_id) VALUES (?)", (uid,))

    c.execute("DELETE FROM groups")
    for gid in data["groups"]:
        c.execute("INSERT INTO groups (group_id) VALUES (?)", (gid,))

    c.execute("DELETE FROM apis")
    for url in data["apis"]:
        c.execute("INSERT INTO apis (url) VALUES (?)", (url,))

    c.execute("DELETE FROM credits")
    for gid, name in data["credits"].items():
        c.execute("INSERT INTO credits (group_id, credit) VALUES (?, ?)", (gid, name))

    c.execute("DELETE FROM group_links")
    for gid, link in data["group_links"].items():
        c.execute("INSERT INTO group_links (group_id, link) VALUES (?, ?)", (gid, link))

    c.execute("DELETE FROM group_files")
    for gid, file in data["group_files"].items():
        c.execute("INSERT INTO group_files (group_id, file) VALUES (?, ?)", (gid, file))

    c.execute("DELETE FROM admin_permissions")
    for aid, groups in data.get("admin_permissions", {}).items():
        for gid in groups:
            c.execute("INSERT INTO admin_permissions (admin_id, group_id) VALUES (?, ?)", (aid, gid))

    conn.commit()
    conn.close()

# === OTP CACHE ===
def is_duplicate(uid):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT uid FROM otp_cache WHERE uid = ?", (uid,))
    exists = c.fetchone() is not None
    conn.close()
    return exists

def add_to_cache(uid):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO otp_cache (uid) VALUES (?)", (uid,))
    conn.commit()
    conn.close()

# Initialize DB
init_db()
