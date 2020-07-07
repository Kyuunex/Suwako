import sqlite3
from modules.connections import database_file as database_file
import os


async def add_admins(self):
    async with await self.db.execute("SELECT user_id, permissions FROM admins") as cursor:
        admin_list = await cursor.fetchall()

    if not admin_list:
        app_info = await self.application_info()
        if app_info.team:
            for team_member in app_info.team.members:
                await self.db.execute("INSERT INTO admins VALUES (?, ?)", [str(team_member.id), "1"])
                print(f"Added {team_member.name} to admin list")
        else:
            await self.db.execute("INSERT INTO admins VALUES (?, ?)", [str(app_info.owner.id), "1"])
            print(f"Added {app_info.owner.name} to admin list")
        await self.db.commit()


def create_tables():
    if not os.path.exists(database_file):
        conn = sqlite3.connect(database_file)
        c = conn.cursor()
        c.execute("CREATE TABLE config (setting, parent, value, flag)")
        c.execute("CREATE TABLE admins (user_id, permissions)")
        c.execute("CREATE TABLE ignored_users (user_id, reason)")
        c.execute("CREATE TABLE users "
                  "(user_id, osu_id, osu_username, osu_join_date, pp, country, ranked_maps_amount, no_sync)")

        c.execute("CREATE TABLE scoretracking_tracklist (osu_id, osu_username)")
        c.execute("CREATE TABLE scoretracking_channels (osu_id, channel_id, gamemode)")
        c.execute("CREATE TABLE scoretracking_history (osu_id, score_id)")

        c.execute("CREATE TABLE channels (setting, guild_id, channel_id)")
        c.execute("CREATE TABLE roles (setting, guild_id, role_id)")
        c.execute("CREATE TABLE country_roles (country, guild_id, role_id)")
        c.execute("CREATE TABLE pp_roles (pp, guild_id, role_id)")

        c.execute("CREATE TABLE restricted_users (guild_id, osu_id)")
        c.execute("CREATE TABLE member_goodbye_messages (message)")
        c.execute("INSERT INTO member_goodbye_messages VALUES (?)", ["%s double tapped on hidamari no uta"])
        c.execute("INSERT INTO member_goodbye_messages VALUES (?)", ["%s missed the last note"])
        conn.commit()
        conn.close()
