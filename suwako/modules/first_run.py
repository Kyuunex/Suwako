import sqlite3
from suwako.modules.storage_management import database_file


async def add_admins(self):
    async with await self.db.execute("SELECT user_id, permissions FROM admins") as cursor:
        admin_list = await cursor.fetchall()

    if not admin_list:
        app_info = await self.application_info()
        if app_info.team:
            for team_member in app_info.team.members:
                await self.db.execute("INSERT INTO admins VALUES (?, ?)", [int(team_member.id), 1])
                print(f"Added {team_member.name} to admin list")
        else:
            await self.db.execute("INSERT INTO admins VALUES (?, ?)", [int(app_info.owner.id), 1])
            print(f"Added {app_info.owner.name} to admin list")
        await self.db.commit()


def ensure_tables():
    conn = sqlite3.connect(database_file)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS "config" (
        "setting"    TEXT, 
        "parent"    TEXT,
        "value"    TEXT,
        "flag"    TEXT
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS "admins" (
        "user_id"    INTEGER NOT NULL UNIQUE,
        "permissions"    INTEGER NOT NULL
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS "ignored_users" (
        "user_id"    INTEGER NOT NULL UNIQUE,
        "reason"    TEXT
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS "channels" (
        "setting"    TEXT NOT NULL,
        "guild_id"    INTEGER NOT NULL,
        "channel_id"    INTEGER NOT NULL
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS "country_roles" (
        "country"    TEXT NOT NULL,
        "guild_id"    INTEGER NOT NULL,
        "role_id"    INTEGER NOT NULL
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS "member_goodbye_messages" (
        "message"    TEXT NOT NULL UNIQUE
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS "pp_roles" (
        "pp"    INTEGER NOT NULL,
        "guild_id"    INTEGER NOT NULL,
        "role_id"    INTEGER NOT NULL
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS "restricted_users" (
        "guild_id"    INTEGER NOT NULL,
        "osu_id"    INTEGER NOT NULL
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS "roles" (
        "setting"    TEXT NOT NULL,
        "guild_id"    INTEGER NOT NULL,
        "role_id"    INTEGER NOT NULL
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS "users" (
        "user_id"    INTEGER NOT NULL UNIQUE,
        "osu_id"    INTEGER NOT NULL,
        "osu_username"    TEXT NOT NULL,
        "osu_join_date"    INTEGER,
        "pp"    INTEGER,
        "country"    TEXT,
        "ranked_maps_amount"    INTEGER,
        "kudosu"    INTEGER,
        "no_sync"    INTEGER
    )
    """)
    c.execute("INSERT OR IGNORE INTO member_goodbye_messages VALUES (?)", ["%s double tapped on hidamari no uta"])
    c.execute("INSERT OR IGNORE INTO member_goodbye_messages VALUES (?)", ["%s missed the last note"])
    conn.commit()
    conn.close()
