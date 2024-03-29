from discord.ext import commands
import discord
import time
import asyncio
import datetime
from aioosuapi import exceptions as aioosuapi_exceptions


class MemberInfoSyncing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.background_tasks.append(
            self.bot.loop.create_task(self.member_name_syncing_loop())
        )

    @commands.Cog.listener()
    async def on_user_update(self, before, after):
        if before.name == after.name:
            return

        async with self.bot.db.execute("SELECT guild_id, channel_id FROM channels WHERE setting = ?",
                                       ["notices"]) as cursor:
            notices_channel_list = await cursor.fetchall()

        if not notices_channel_list:
            return

        async with self.bot.db.execute("SELECT user_id, osu_id, osu_username, osu_join_date, "
                                       "pp, country, ranked_maps_amount, kudosu, no_sync "
                                       "FROM users WHERE user_id = ?", [int(after.id)]) as cursor:
            query = await cursor.fetchone()

        if not query:
            return

        osu_profile = await self.bot.osu.get_user(u=query[1])
        if not osu_profile:
            return

        for this_guild in notices_channel_list:
            guild = self.bot.get_guild(int(this_guild[0]))

            notices_channel = self.bot.get_channel(int(this_guild[1]))

            if not notices_channel:
                continue

            member = guild.get_member(int(after.id))
            await self.sync_nickname(notices_channel, query, member, osu_profile)

    async def member_name_syncing_loop(self):
        print("Member Name Syncing Loop launched!")
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            await asyncio.sleep(10)
            print(time.strftime("%Y/%m/%d %H:%M:%S %Z") + " | member_name_syncing_loop start")
            async with self.bot.db.execute("SELECT guild_id, channel_id FROM channels WHERE setting = ?",
                                           ["notices"]) as cursor:
                notices_channel_list = await cursor.fetchall()

            if not notices_channel_list:
                await asyncio.sleep(43200)
                continue

            async with self.bot.db.execute("SELECT user_id, osu_id, osu_username, osu_join_date, "
                                           "pp, country, ranked_maps_amount, kudosu, no_sync FROM users") as cursor:
                user_list = await cursor.fetchall()
            async with self.bot.db.execute("SELECT guild_id, osu_id FROM restricted_users") as cursor:
                restricted_user_list = await cursor.fetchall()

            for notices_channel_id in notices_channel_list:

                notices_channel = self.bot.get_channel(int(notices_channel_id[1]))
                guild = self.bot.get_guild(int(notices_channel_id[0]))

                await self.cycle_through_members(guild, notices_channel, restricted_user_list, user_list)

            print(time.strftime("%Y/%m/%d %H:%M:%S %Z") + " | member_name_syncing_loop finished")
            await asyncio.sleep(43200)

    async def cycle_through_members(self, guild, notices_channel, restricted_user_list, user_list):
        for member in guild.members:
            if member.bot:
                continue

            for db_user in user_list:
                if int(member.id) != int(db_user[0]):
                    continue

                try:
                    osu_profile = await self.bot.osu.get_user(u=db_user[1], event_days="1")
                except aioosuapi_exceptions.HTTPException as e:
                    print(e)
                    await asyncio.sleep(120)
                    break

                if osu_profile:
                    await self.sync_nickname(notices_channel, db_user, member, osu_profile)

                    if (int(guild.id), int(db_user[1])) in restricted_user_list:
                        embed = await self.embed_unrestricted(db_user, member)
                        await notices_channel.send(embed=embed)
                        await self.bot.db.execute("DELETE FROM restricted_users "
                                                  "WHERE guild_id = ? AND osu_id = ?",
                                                  [int(guild.id), int(db_user[1])])
                        await self.bot.db.commit()
                else:
                    # at this point we are sure that the user is restricted.
                    if not (int(guild.id), int(db_user[1])) in restricted_user_list:
                        embed = await self.embed_restricted(db_user, member)
                        await notices_channel.send(embed=embed)
                        await self.bot.db.execute("INSERT INTO restricted_users VALUES (?,?)",
                                                  [int(guild.id), int(db_user[1])])
                        await self.bot.db.commit()
                await asyncio.sleep(1)

    async def embed_unrestricted(self, db_user, member):
        embed = discord.Embed(
            color=0xbd3661,
            description=":tada: unrestricted lol",
            title=member.display_name,
            url=f"https://osu.ppy.sh/users/{db_user[1]}"
        )
        embed.add_field(name="user", value=member.mention, inline=False)
        embed.add_field(name="osu_username", value=db_user[2], inline=False)
        embed.add_field(name="osu_id", value=db_user[1], inline=False)
        embed.set_thumbnail(url=member.avatar_url)
        return embed

    async def embed_restricted(self, db_user, member):
        embed = discord.Embed(
            color=0xbd3661,
            description=":hammer: restricted lmao",
            title=member.display_name,
            url=f"https://osu.ppy.sh/users/{db_user[1]}"
        )
        embed.add_field(name="user", value=member.mention, inline=False)
        embed.add_field(name="osu_username", value=db_user[2], inline=False)
        embed.add_field(name="osu_id", value=db_user[1], inline=False)
        embed.set_thumbnail(url=member.avatar_url)
        return embed

    async def sync_nickname(self, notices_channel, db_user, member, osu_profile):
        if str(db_user[2]) != osu_profile.name:
            embed = await self.embed_namechange(db_user, member, osu_profile)
            await notices_channel.send(embed=embed)

        if member.display_name != osu_profile.name:
            await self.apply_nickname(db_user, member, notices_channel, osu_profile)

        await self.bot.db.execute("UPDATE users SET country = ?, pp = ?, "
                                  "osu_join_date = ?, osu_username = ? WHERE user_id = ?;",
                                  [str(osu_profile.country), int(float(osu_profile.pp_raw)),
                                   0, str(osu_profile.name), int(member.id)])
        await self.bot.db.commit()

    async def embed_namechange(self, db_user, member, osu_profile):
        embed = discord.Embed(
            color=0xbd3661,
            description=":pen_ballpoint: namechange",
            title=member.display_name,
            url=f"https://osu.ppy.sh/users/{db_user[1]}"
        )
        embed.add_field(name="user", value=member.mention, inline=False)
        embed.add_field(name="old_osu_username", value=db_user[2], inline=False)
        embed.add_field(name="new_osu_username", value=osu_profile.name, inline=False)
        embed.add_field(name="osu_id", value=db_user[1], inline=False)
        embed.set_thumbnail(url=member.avatar_url)
        return embed

    async def apply_nickname(self, db_user, member, notices_channel, osu_profile):
        now = datetime.datetime.now()
        if "04-01T" in str(now.isoformat()):
            return
        if "03-31T" in str(now.isoformat()):
            return
        if int(db_user[8]) == 1:
            return
        if member.guild_permissions.administrator:
            return

        old_nickname = member.display_name
        try:
            await member.edit(nick=osu_profile.name)
            embed = await self.embed_nickname_updated(db_user, member, old_nickname, osu_profile)
            await notices_channel.send(embed=embed)
        except discord.Forbidden as e:
            print(time.strftime("%Y/%m/%d %H:%M:%S %Z"))
            print(f"in apply_nickname, error changing nickname of {member.display_name} ({member.id})")
            print(e)
            embed = await self.embed_error_name_change(db_user, member, old_nickname, osu_profile)
            await notices_channel.send(embed=embed)

    async def embed_nickname_updated(self, db_user, member, old_nickname, osu_profile):
        embed = discord.Embed(
            color=0xbd3661,
            description=":pencil2: nickname updated",
            title=member.display_name,
            url=f"https://osu.ppy.sh/users/{db_user[1]}"
        )
        embed.add_field(name="user", value=member.mention, inline=False)
        embed.add_field(name="cached_osu_username", value=db_user[2], inline=False)
        embed.add_field(name="current_osu_username", value=osu_profile.name, inline=False)
        embed.add_field(name="osu_id", value=db_user[1], inline=False)
        embed.add_field(name="old_nickname", value=old_nickname, inline=False)
        embed.set_thumbnail(url=member.avatar_url)
        return embed

    async def embed_error_name_change(self, db_user, member, old_nickname, osu_profile):
        embed = discord.Embed(
            color=0xFF0000,
            description=":anger: no perms to update nickname",
            title=member.display_name,
            url=f"https://osu.ppy.sh/users/{db_user[1]}"
        )
        embed.add_field(name="user", value=member.mention, inline=False)
        embed.add_field(name="cached_osu_username", value=db_user[2], inline=False)
        embed.add_field(name="current_osu_username", value=osu_profile.name, inline=False)
        embed.add_field(name="osu_id", value=db_user[1], inline=False)
        embed.add_field(name="old_nickname", value=old_nickname, inline=False)
        embed.set_thumbnail(url=member.avatar_url)
        return embed


async def setup(bot):
    await bot.add_cog(MemberInfoSyncing(bot))
