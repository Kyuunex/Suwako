from modules import db
from modules.connections import database_file as database_file
import os


async def add_admins(self):
    if not db.query("SELECT * FROM admins"):
        app_info = await self.application_info()
        if app_info.team:
            for team_member in app_info.team.members:
                db.query(["INSERT INTO admins VALUES (?, ?)", [str(team_member.id), "1"]])
                print(f"Added {team_member.name} to admin list")
        else:
            db.query(["INSERT INTO admins VALUES (?, ?)", [str(app_info.owner.id), "1"]])
            print(f"Added {app_info.owner.name} to admin list")


def create_tables():
    if not os.path.exists(database_file):
        db.query("CREATE TABLE users "
                 "(user_id, osu_id, osu_username, osu_join_date, pp, country, ranked_maps_amount, no_sync)")
        db.query("CREATE TABLE config (setting, parent, value, flag)")

        db.query("CREATE TABLE channels (setting, guild_id, channel_id)")
        db.query("CREATE TABLE roles (setting, guild_id, role_id)")
        db.query("CREATE TABLE country_roles (country, guild_id, role_id)")
        db.query("CREATE TABLE pp_roles (pp, guild_id, role_id)")

        db.query("CREATE TABLE admins (user_id, permissions)")
        db.query("CREATE TABLE restricted_users (guild_id, osu_id)")
        db.query("CREATE TABLE member_goodbye_messages (message)")
        db.query(["INSERT INTO member_goodbye_messages VALUES (?)", ["%s double tapped on hidamari no uta"]])
        db.query(["INSERT INTO member_goodbye_messages VALUES (?)", ["%s missed the last note"]])
