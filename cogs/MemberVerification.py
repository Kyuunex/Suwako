import random

import discord
from discord.ext import commands
from modules import db
from modules import permissions
from modules.connections import osu as osu
import osuembed


class MemberVerification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.verify_channel_list = db.query(["SELECT channel_id, guild_id FROM channels "
                                             "WHERE setting = ?",
                                             ["verify"]])
        self.member_goodbye_messages = db.query("SELECT message FROM member_goodbye_messages")
        self.country_roles = db.query("SELECT country, guild_id, role_id FROM country_roles")
        self.pp_roles = db.query("SELECT pp, guild_id, role_id FROM pp_roles")

    @commands.command(name="verify", brief="Manually verify a member", description="")
    @commands.check(permissions.is_admin)
    @commands.guild_only()
    async def verify(self, ctx, user_id, osu_id):
        member = ctx.guild.get_member(int(user_id))
        if member:
            osu_profile = await osu.get_user(u=osu_id)
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
                db.query(["DELETE FROM users WHERE user_id = ?", [str(member.id)]])
                db.query(["INSERT INTO users VALUES (?,?,?,?,?,?,?,?)",
                          [str(member.id), str(osu_profile.id), str(osu_profile.name), str(osu_profile.join_date),
                           str(osu_profile.pp_raw), str(osu_profile.country), "0", "0"]])
                await ctx.send(content="Manually Verified: %s" % member.name, embed=embed)

    @commands.command(name="verify_restricted", brief="Manually verify a restricted member", description="")
    @commands.check(permissions.is_admin)
    async def verify_restricted(self, ctx, user_id, osu_id, username=""):
        db.query(["INSERT INTO users VALUES (?,?,?,?,?,?,?,?)",
                  [str(user_id), str(osu_id), username, "", "", "", "", ""]])
        await ctx.send("lol ok")

    @commands.command(name="unverify", brief="Unverify a member and delete it from db", description="")
    @commands.check(permissions.is_admin)
    @commands.guild_only()
    async def unverify(self, ctx, user_id):
        db.query(["DELETE FROM users WHERE user_id = ?", [str(user_id)]])
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
                    await channel.send("beep boop boop beep, %s has joined our army of bots" % member.mention)

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
                    osu_id = db.query(["SELECT osu_id, osu_username FROM users WHERE user_id = ?", [str(member.id)]])
                    if osu_id:
                        try:
                            osu_profile = await osu.get_user(u=osu_id[0][0])
                            embed = await osuembed.user(osu_profile, 0xffffff, "User left")
                            member_name = osu_profile.name
                        except:
                            print("Connection issues?")
                            embed = None
                            member_name = member.name
                    else:
                        embed = None
                        member_name = member.name
                    goodbye_message = random.choice(self.member_goodbye_messages)
                    await channel.send(goodbye_message[0] % member_name, embed=embed)
                else:
                    await channel.send("beep boop boop beep, %s has left our army of bots" % member.mention)

    async def get_country_role(self, guild, country):
        for role_id in self.country_roles:
            if country == role_id[0] and str(guild.id) == str(role_id[1]):
                return discord.utils.get(guild.roles, id=int(role_id[2]))
        default_role = db.query(["SELECT role_id FROM roles WHERE setting = ? AND guild_id = ?",
                                 ["default_country", str(guild.id)]])
        return discord.utils.get(guild.roles, id=int(default_role[0][0]))

    async def get_pp_role(self, guild, pp):
        for role_id in self.pp_roles:
            if str(guild.id) == str(role_id[1]):
                if int(float(pp)/1000) == int(float(role_id[0]) / 1000):
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
            osu_profile = await osu.get_user(u=osu_id)
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

        check_if_new_discord_account = db.query(["SELECT user_id FROM users WHERE osu_id = ?", [str(osu_profile.id)]])
        if check_if_new_discord_account:
            if str(check_if_new_discord_account[0][0]) != str(member.id):
                await channel.send("this osu account is already linked to <@%s> in my database. "
                                   "if there's a problem, for example, you got a new discord account, ping kyuunex." %
                                   (check_if_new_discord_account[0][0]))
                return None

        already_linked_to = db.query(["SELECT osu_id FROM users WHERE user_id = ?", [str(member.id)]])
        if already_linked_to:
            if str(osu_profile.id) != already_linked_to[0][0]:
                await channel.send("%s it seems like your discord account is already in my database and "
                                   "is linked to <https://osu.ppy.sh/users/%s>" %
                                   (member.mention, already_linked_to[0][0]))
                return None
            else:
                try:
                    await member.add_roles(country_role)
                    await member.edit(nick=osu_profile.name)
                except:
                    pass
                await channel.send(content="%s i already know lol. here, have some roles" % member.mention)
                return None

        try:
            await member.add_roles(country_role)
            await member.add_roles(pp_role)
            await member.edit(nick=osu_profile.name)
        except:
            pass
        embed = await osuembed.user(osu_profile)
        db.query(["DELETE FROM users WHERE user_id = ?", [str(member.id)]])
        db.query(["INSERT INTO users VALUES (?,?,?,?,?,?,?,?)",
                  [str(member.id), str(osu_profile.id), str(osu_profile.name), str(osu_profile.join_date),
                   str(osu_profile.pp_raw), str(osu_profile.country), "0", "0"]])
        await channel.send(content="`Verified: %s`" % member.name, embed=embed)

    async def member_verification(self, channel, member):
        user_db_lookup = db.query(["SELECT osu_id, osu_username, pp, country FROM users "
                                   "WHERE user_id = ?", [str(member.id)]])
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
            await channel.send("Welcome aboard %s! Since we know who you are, I have automatically verified you. "
                               "Enjoy your stay!" % member.mention,
                               embed=embed)
        else:
            await channel.send("Welcome %s! We have a verification system in this server "
                               "so we can give you appropriate roles and keep raids/spam out." % member.mention)
            osu_profile = await self.get_osu_profile(member.name)
            if osu_profile:
                await channel.send(content="Is this your osu! profile? "
                                           "If yes, type `yes`, if not, post a link to your profile.",
                                   embed=await osuembed.user(osu_profile))
            else:
                await channel.send("Please post a link to your osu! profile and I will verify you instantly.")

    async def get_osu_profile(self, name):
        try:
            return await osu.get_user(u=name)
        except:
            return None


def setup(bot):
    bot.add_cog(MemberVerification(bot))
