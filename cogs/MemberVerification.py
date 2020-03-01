import random

import discord
import sqlite3
from discord.ext import commands
from modules import permissions
import osuembed


class MemberVerification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        conn = sqlite3.connect(self.bot.database_file)
        c = conn.cursor()
        self.verify_channel_list = tuple(c.execute("SELECT channel_id, guild_id FROM channels WHERE setting = ?",
                                                   ["verify"]))
        conn.close()

    @commands.command(name="verify", brief="Manually verify a member", description="")
    @commands.check(permissions.is_admin)
    @commands.guild_only()
    async def verify(self, ctx, user_id, osu_id):
        member = ctx.guild.get_member(int(user_id))
        if member:
            osu_profile = await self.bot.osu.get_user(u=osu_id)
            if osu_profile:
                country_role = await self.get_country_role(member.guild, osu_profile.country)
                pp_role = await self.get_pp_role(member.guild, osu_profile.pp_raw)
                try:
                    await member.add_roles(country_role)
                    await member.add_roles(pp_role)
                    await member.edit(nick=osu_profile.name)
                except:
                    pass
                embed = await osuembed.user(osu_profile)
                await self.bot.db.execute("DELETE FROM users WHERE user_id = ?", [str(member.id)])
                await self.bot.db.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?,?)",
                                          [str(member.id), str(osu_profile.id), str(osu_profile.name),
                                           str(osu_profile.join_date),
                                           str(osu_profile.pp_raw), str(osu_profile.country), "0", "0"])
                await self.bot.db.commit()
                await ctx.send(content=f"Manually Verified: {member.name}", embed=embed)

    @commands.command(name="verify_restricted", brief="Manually verify a restricted member", description="")
    @commands.check(permissions.is_admin)
    async def verify_restricted(self, ctx, user_id, osu_id, username=""):
        await self.bot.db.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?,?)",
                                  [str(user_id), str(osu_id), username, "", "", "", "", ""])
        await self.bot.db.commit()
        await ctx.send("lol ok")

    @commands.command(name="unverify", brief="Unverify a member and delete it from db", description="")
    @commands.check(permissions.is_admin)
    @commands.guild_only()
    async def unverify(self, ctx, user_id):
        await self.bot.db.execute("DELETE FROM users WHERE user_id = ?", [str(user_id)])
        await self.bot.db.commit()
        member = ctx.guild.get_member(int(user_id))
        if member:
            try:
                await member.edit(roles=[])
                await member.edit(nick=None)
                await ctx.send("Done")
            except:
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
                                                   [str(member.id)]) as cursor:
                        osu_id = await cursor.fetchall()
                    if osu_id:
                        try:
                            osu_profile = await self.bot.osu.get_user(u=osu_id[0][0])
                            embed = await osuembed.user(osu_profile, 0xffffff, "User left")
                            member_name = osu_profile.name
                        except:
                            print("Connection issues?")
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
            if country == role_id[0] and str(guild.id) == str(role_id[1]):
                return discord.utils.get(guild.roles, id=int(role_id[2]))
        async with self.bot.db.execute("SELECT role_id FROM roles WHERE setting = ? AND guild_id = ?",
                                       ["default_country", str(guild.id)]) as cursor:
            default_role = await cursor.fetchall()
        return discord.utils.get(guild.roles, id=int(default_role[0][0]))

    async def get_pp_role(self, guild, pp):
        if not pp:
            pp = 0
        async with self.bot.db.execute("SELECT pp, guild_id, role_id FROM pp_roles") as cursor:
            pp_roles = await cursor.fetchall()
        for role_id in pp_roles:
            if str(guild.id) == str(role_id[1]):
                if int(float(pp) / 1000) == int(float(role_id[0]) / 1000):
                    return discord.utils.get(guild.roles, id=int(role_id[2]))

    async def respond_to_verification(self, message):
        split_message = []
        if "/" in message.content:
            split_message = message.content.split("/")
        if "https://osu.ppy.sh/u" in message.content:
            profile_id = split_message[4].split("#")[0].split(" ")[0]
            await self.profile_id_verification(message, profile_id)
            return None
        elif message.content.lower() == "yes":
            profile_id = message.author.name
            await self.profile_id_verification(message, profile_id)
            return None
        else:
            return None

    async def profile_id_verification(self, message, osu_id):
        channel = message.channel
        member = message.author
        try:
            osu_profile = await self.bot.osu.get_user(u=osu_id)
        except:
            await channel.send("i am having connection issues to osu servers, verifying you. "
                               "<@155976140073205761> should look into this")
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
        pp_role = await self.get_pp_role(member.guild, osu_profile.pp_raw)

        async with self.bot.db.execute("SELECT osu_id FROM users WHERE user_id = ?", [str(member.id)]) as cursor:
            already_linked_to = await cursor.fetchall()
        if already_linked_to:
            if str(osu_profile.id) != already_linked_to[0][0]:
                await channel.send(f"{member.mention} it seems like your discord account is already in my database "
                                   f"and is linked to <https://osu.ppy.sh/users/{already_linked_to[0][0]}>")
                return None
            else:
                try:
                    await member.add_roles(country_role)
                    await member.edit(nick=osu_profile.name)
                except:
                    pass
                await channel.send(content=f"{member.mention} i already know lol. here, have some roles")
                return None

        async with self.bot.db.execute("SELECT user_id FROM users WHERE osu_id = ?", [str(osu_profile.id)]) as cursor:
            check_if_new_discord_account = await cursor.fetchall()
        if check_if_new_discord_account:
            if str(check_if_new_discord_account[0][0]) != str(member.id):
                old_user_id = check_if_new_discord_account[0][0]
                await channel.send(f"this osu account is already linked to <@{old_user_id}> in my database. "
                                   "if there's a problem, for example, you got a new discord account, ping kyuunex.")
                return None

        try:
            await member.add_roles(country_role)
            await member.add_roles(pp_role)
            await member.edit(nick=osu_profile.name)
        except:
            pass
        embed = await osuembed.user(osu_profile)
        await self.bot.db.execute("DELETE FROM users WHERE user_id = ?", [str(member.id)])
        await self.bot.db.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?,?)",
                                  [str(member.id), str(osu_profile.id), str(osu_profile.name),
                                   str(osu_profile.join_date),
                                   str(osu_profile.pp_raw), str(osu_profile.country), "0", "0"])
        await self.bot.db.commit()
        await channel.send(content=f"`Verified: {member.name}`", embed=embed)

    async def member_verification(self, channel, member):
        async with self.bot.db.execute("SELECT osu_id, osu_username, pp, country FROM users WHERE user_id = ?",
                                       [str(member.id)]) as cursor:
            user_db_lookup = await cursor.fetchall()
        if user_db_lookup:
            country_role = await self.get_country_role(member.guild, str(user_db_lookup[0][3]))
            pp_role = await self.get_pp_role(member.guild, str(user_db_lookup[0][2]))
            try:
                await member.add_roles(country_role)
                await member.add_roles(pp_role)
            except:
                pass
            osu_profile = await self.get_osu_profile(user_db_lookup[0][0])
            if osu_profile:
                name = osu_profile.name
                embed = await osuembed.user(osu_profile)
            else:
                name = user_db_lookup[0][1]
                embed = None
            await member.edit(nick=name)
            await channel.send(f"Welcome aboard {member.mention}! Since we know who you are, "
                               "I have automatically gave you appropriate roles. Enjoy your stay!", embed=embed)
        else:
            osu_profile = await self.get_osu_profile(member.name)
            if osu_profile:
                await channel.send(content=f"Welcome {member.mention}! We have a verification system in this server "
                                           "so we can give you appropriate roles and keep raids/spam out. \n"
                                           "Is this your osu! profile? "
                                           "If yes, type `yes`, if not, post a link to your profile.",
                                   embed=await osuembed.user(osu_profile))
            else:
                await channel.send(f"Welcome {member.mention}! We have a verification system in this server "
                                   "so we can give you appropriate roles and keep raids/spam out. \n"
                                   "Please post a link to your osu! profile and I will verify you instantly.")

    async def get_osu_profile(self, name):
        try:
            return await self.bot.osu.get_user(u=name)
        except:
            return None


def setup(bot):
    bot.add_cog(MemberVerification(bot))
