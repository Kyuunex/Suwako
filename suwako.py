#!/usr/bin/env python3

import os
from discord.ext import commands

from modules import db

from modules.connections import database_file as database_file
from modules.connections import bot_token as bot_token

command_prefix = "-"
app_version = "d20191122"
client = commands.Bot(command_prefix=command_prefix,
                      description="Suwako %s" % app_version)

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

initial_extensions = [
    "cogs.BotManagement",
    "cogs.MemberManagement",
    "cogs.MemberNameSyncing",
    "cogs.MemberVerification",
]

if __name__ == "__main__":
    for extension in initial_extensions:
        try:
            client.load_extension(extension)
        except Exception as e:
            print(e)


@client.event
async def on_ready():
    print("Logged in as")
    print(client.user.name)
    print(client.user.id)
    print("------")
    if not db.query("SELECT * FROM admins"):
        app_info = await client.application_info()
        db.query(["INSERT INTO admins VALUES (?, ?)", [str(app_info.owner.id), "1"]])
        print("Added %s to admin list" % app_info.owner.name)


client.run(bot_token)
