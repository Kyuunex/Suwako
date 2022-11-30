import random

import discord
import datetime
from discord.ext import commands
from suwako.modules import permissions
from suwako.embeds import oldembeds
from aioosuapi import exceptions as aioosuapi_exceptions


class MemberVerification(commands.Cog):
    def __init__(self, bot, verify_channel_list):
        self.bot = bot
        self.verify_channel_list = verify_channel_list
        self.post_verification_emotes = [
            ["FR", "🥖"],
        ]

    @commands.command(name="verify", brief="Manually verify a member", description="")
    @commands.check(permissions.is_admin)
    @commands.guild_only()
    async def verify(self, ctx, user_id, osu_id):
        member = ctx.guild.get_member(int(user_id))
        if member:
            osu_profile = await self.bot.osu.get_user(u=osu_id)
            if osu_profile:
                country_role = await self.get_country_role(member.guild, osu_profile.country)
                pp_role = await self.get_pp_role(member.guild, int(float(osu_profile.pp_raw)))

                try:
                    await member.add_roles(country_role)
                    if pp_role:
                        await member.add_roles(pp_role)
                except discord.Forbidden as e:
                    print(e)
                    await ctx.send("i can't give the role")

                try:
                    await member.edit(nick=osu_profile.name)
                except discord.Forbidden as e:
                    await ctx.send("i can't update the nickname of this user")

                embed = await oldembeds.user(osu_profile)
                if osu_profile.pp_raw:
                    pp_number = osu_profile.pp_raw
                else:
                    pp_number = 0
                await self.bot.db.execute("DELETE FROM users WHERE user_id = ?", [int(member.id)])
                await self.bot.db.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?,?,?,?)",
                                          [int(member.id), int(osu_profile.id), str(osu_profile.name),
                                           0,
                                           int(float(pp_number)), str(osu_profile.country), 0, 0, 0, 0])
                await self.bot.db.commit()
                await ctx.send(content=f"Manually Verified: {member.name}", embed=embed)

    @commands.command(name="verify_restricted", brief="Manually verify a restricted member", description="")
    @commands.check(permissions.is_admin)
    @commands.check(permissions.is_not_ignored)
    async def verify_restricted(self, ctx, user_id, osu_id, username=""):
        await self.bot.db.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?,?,?,?)",
                                  [int(user_id), int(osu_id), username, 0, 0, "", 0, 0, 0, 0])
        await self.bot.db.commit()
        await ctx.send("lol ok")

    @commands.command(name="update_user_discord_account", brief="When user switched accounts, apply this")
    @commands.check(permissions.is_admin)
    @commands.check(permissions.is_not_ignored)
    async def update_user_discord_account(self, ctx, old_id, new_id, osu_id=""):
        if not old_id.isdigit():
            await ctx.send("old_id must be all digits")
            return None

        try:
            old_account = ctx.guild.get_member(int(old_id))
            if old_account:
                await ctx.send("kicking old account")
                await old_account.kick()
        except discord.Forbidden as e:
            print(e)

        if not new_id.isdigit():
            await ctx.send("new_id must be all digits")
            return None

        await self.bot.db.execute("UPDATE users SET user_id = ? WHERE user_id = ?", [int(new_id), int(old_id)])
        await self.bot.db.commit()

        if osu_id:
            await self.verify(ctx, new_id, osu_id)
        await ctx.send("okay, done")

    @commands.command(name="unverify", brief="Unverify a member and delete it from db", description="")
    @commands.check(permissions.is_admin)
    @commands.check(permissions.is_not_ignored)
    @commands.guild_only()
    async def unverify(self, ctx, user_id):
        await self.bot.db.execute("DELETE FROM users WHERE user_id = ?", [int(user_id)])
        await self.bot.db.commit()
        member = ctx.guild.get_member(int(user_id))
        if member:
            try:
                await member.edit(roles=[])
                await member.edit(nick=None)
                await ctx.send("Done")
            except discord.Forbidden as e:
                print(e)
                await ctx.send("no perms to change nickname and/or remove roles")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        for verify_channel_id in self.verify_channel_list:
            if member.guild.id == int(verify_channel_id[1]):
                channel = self.bot.get_channel(int(verify_channel_id[0]))
                if not member.bot:
                    await self.member_verification(channel, member)
                else:
                    await channel.send(f"beep boop boop beep, {member.mention} has joined our army of bots")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id != self.bot.user.id:
            for verify_channel_id in self.verify_channel_list:
                if message.channel.id == int(verify_channel_id[0]):
                    await self.respond_to_verification(message)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        for verify_channel_id in self.verify_channel_list:
            if member.guild.id == int(verify_channel_id[1]):
                channel = self.bot.get_channel(int(verify_channel_id[0]))
                if not member.bot:
                    async with self.bot.db.execute("SELECT osu_id, osu_username FROM users WHERE user_id = ?",
                                                   [int(member.id)]) as cursor:
                        osu_id = await cursor.fetchall()
                    if osu_id:
                        try:
                            osu_profile = await self.bot.osu.get_user(u=osu_id[0][0])
                            embed = await oldembeds.user(osu_profile, 0xffffff, "User left")
                            member_name = osu_profile.name
                        except aioosuapi_exceptions.HTTPException as e:
                            print("Connection issues?")
                            print(e)
                            embed = None
                            member_name = member.name
                    else:
                        embed = None
                        member_name = member.name

                    async with self.bot.db.execute("SELECT message FROM member_goodbye_messages") as cursor:
                        member_goodbye_messages = await cursor.fetchall()
                    goodbye_message = random.choice(member_goodbye_messages)
                    await channel.send(goodbye_message[0] % member_name, embed=embed)
                else:
                    await channel.send(f"beep boop boop beep, {member.mention} has left our army of bots")

    async def get_country_role(self, guild, country):
        async with self.bot.db.execute("SELECT country, guild_id, role_id FROM country_roles") as cursor:
            country_roles = await cursor.fetchall()
        for role_id in country_roles:
            if country == role_id[0] and int(guild.id) == int(role_id[1]):
                return guild.get_role(int(role_id[2]))
        async with self.bot.db.execute("SELECT role_id FROM roles WHERE setting = ? AND guild_id = ?",
                                       ["default_country", int(guild.id)]) as cursor:
            default_role = await cursor.fetchone()
        if not default_role:
            print(f"no default_country role configured for {guild.id}")
            return None
        return guild.get_role(int(default_role[0]))

    async def get_pp_role(self, guild, pp):
        if not pp:
            pp = 0
        async with self.bot.db.execute("SELECT pp, guild_id, role_id FROM pp_roles") as cursor:
            pp_roles = await cursor.fetchall()
        if not pp_roles:
            return None
        for role_id in pp_roles:
            if int(guild.id) == int(role_id[1]):
                if int(float(pp) / 1000) == int(float(role_id[0]) / 1000):
                    return guild.get_role(int(role_id[2]))

    async def respond_to_verification(self, message):
        split_message = []
        if "/" in message.content:
            split_message = message.content.split("/")
        if "https://osu.ppy.sh/u" in message.content:
            profile_id = split_message[4].split("#")[0].split(" ")[0]
            await self.profile_id_verification(message, profile_id)
            return None
        elif message.content.lower() == "yes" and self.is_new_user(message.author) is False:
            # profile_id = message.author.name
            # await self.profile_id_verification(message, profile_id)
            return None
        else:
            return None

    async def profile_id_verification(self, message, osu_id):
        channel = message.channel
        member = message.author
        try:
            osu_profile = await self.bot.osu.get_user(u=osu_id)
        except aioosuapi_exceptions.HTTPException as e:
            print(e)
            await channel.send("i am having connection issues to osu servers, verifying you. "
                               "ping staff to investigate if you are in a hurry")
            return None

        if not osu_profile:
            if osu_id.isdigit():
                await channel.send("verification failure, "
                                   "i can't find any profile from that link or you are restricted. ")
            else:
                await channel.send("verification failure, "
                                   "either your discord username does not match a username of any osu account "
                                   "or you linked an incorrect profile. "
                                   "this error also pops up if you are restricted")
            return None

        country_role = await self.get_country_role(member.guild, osu_profile.country)
        pp_role = await self.get_pp_role(member.guild, int(float(osu_profile.pp_raw)))

        async with self.bot.db.execute("SELECT osu_id FROM users WHERE user_id = ?", [int(member.id)]) as cursor:
            already_linked_to = await cursor.fetchall()
        if already_linked_to:
            if int(osu_profile.id) != int(already_linked_to[0][0]):
                await channel.send(f"{member.mention} it seems like your discord account is already in my database "
                                   f"and is linked to <https://osu.ppy.sh/users/{already_linked_to[0][0]}>")
                return None
            else:
                try:
                    await member.add_roles(country_role)
                    await member.edit(nick=osu_profile.name)
                except discord.Forbidden:
                    await channel.send(content=f"{member.mention} i don't seem to have perms to do this")
                await channel.send(content=f"{member.mention} i already know lol. here, have some roles")
                return None

        async with self.bot.db.execute("SELECT user_id FROM users WHERE osu_id = ?", [int(osu_profile.id)]) as cursor:
            check_if_new_discord_account = await cursor.fetchall()
        if check_if_new_discord_account:
            if int(check_if_new_discord_account[0][0]) != int(member.id):
                old_user_id = check_if_new_discord_account[0][0]
                await channel.send(f"this osu account is already linked to <@{old_user_id}> in my database. "
                                   "if there's a problem, for example, you got a new discord account, ping staff.")
                return None

        try:
            await member.add_roles(country_role)
            if pp_role:
                await member.add_roles(pp_role)
            await member.edit(nick=osu_profile.name)
        except discord.Forbidden:
            await channel.send(content=f"{member.mention} i don't seem to have perms to do this")
        embed = await oldembeds.user(osu_profile)

        if osu_profile.pp_raw:
            pp_number = osu_profile.pp_raw
        else:
            pp_number = 0

        await self.bot.db.execute("DELETE FROM users WHERE user_id = ?", [int(member.id)])
        await self.bot.db.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?,?,?,?)",
                                  [int(member.id), int(osu_profile.id), str(osu_profile.name),
                                   0,
                                   int(float(pp_number)), str(osu_profile.country), 0, 0, 0, 0])
        await self.bot.db.commit()
        await channel.send(content=f"`Verified: {member.name}`", embed=embed)

    async def member_verification(self, channel, member):
        async with self.bot.db.execute("SELECT osu_id, osu_username, pp, country FROM users WHERE user_id = ?",
                                       [int(member.id)]) as cursor:
            user_db_lookup = await cursor.fetchall()
        if user_db_lookup:
            country_role = await self.get_country_role(member.guild, str(user_db_lookup[0][3]))
            pp_role = await self.get_pp_role(member.guild, str(user_db_lookup[0][2]))
            try:
                await member.add_roles(country_role)
                if pp_role:
                    await member.add_roles(pp_role)
            except discord.Forbidden as e:
                print(e)
            osu_profile = await self.get_osu_profile(user_db_lookup[0][0])
            if osu_profile:
                name = osu_profile.name
                embed = await oldembeds.user(osu_profile)
            else:
                name = user_db_lookup[0][1]
                embed = None
            await member.edit(nick=name)
            await channel.send(f"Welcome aboard {member.mention}! Since we know who you are, "
                               "I have automatically gave you appropriate roles. Enjoy your stay!", embed=embed)
        else:
            # osu_profile = await self.get_osu_profile(member.name)
            osu_profile = None
            if (osu_profile and
                    (self.is_new_user(member) is False) and
                    osu_profile.pp_raw and
                    float(osu_profile.pp_raw) > 0):
                await channel.send(content=f"Welcome {member.mention}! We have a verification system in this server "
                                           "so we can give you appropriate roles and keep raids/spam out. \n"
                                           "Is this your osu! profile? "
                                           "If yes, type `yes`, if not, post a link to your profile.",
                                   embed=await oldembeds.user(osu_profile))
            else:
                await channel.send(f"Welcome {member.mention}! We have a verification system in this server "
                                   "so we can give you appropriate roles and keep raids/spam out. \n"
                                   "Please post a link to your osu! profile and I will verify you instantly.")

    async def get_osu_profile(self, name):
        try:
            return await self.bot.osu.get_user(u=name)
        except aioosuapi_exceptions.HTTPException as e:
            print(e)
            return None

    async def add_obligatory_reaction(self, message, osu_profile):
        try:
            if osu_profile.country:
                for stereotype in self.post_verification_emotes:
                    if osu_profile.country == stereotype[0]:
                        await message.add_reaction(stereotype[1])
        except discord.Forbidden as e:
            print(e)

    def is_new_user(self, user):
        user_creation_ago = datetime.datetime.utcnow() - user.created_at
        if abs(user_creation_ago).total_seconds() / 2592000 <= 1 and user.avatar is None:
            return True
        else:
            return False


async def setup(bot):
    async with bot.db.execute("SELECT channel_id, guild_id FROM channels WHERE setting = ?", ["verify"]) as cursor:
        verify_channel_list = await cursor.fetchall()

    await bot.add_cog(MemberVerification(bot, verify_channel_list))
