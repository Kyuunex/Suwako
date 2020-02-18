from discord.ext import commands
from modules import permissions
import osuembed

from modules.connections import osu as osu


class MemberManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="get_members_not_in_db", brief="Get a list of users who are not in db", description="")
    @commands.check(permissions.is_owner)
    @commands.guild_only()
    async def get_members_not_in_db(self, ctx):
        for member in ctx.guild.members:
            if not member.bot:
                async with self.bot.db.execute("SELECT osu_id FROM users WHERE user_id = ?",
                                               [str(member.id)]) as cursor:
                    in_db_check = await cursor.fetchall()
                if not in_db_check:
                    await ctx.send(member.mention)

    @commands.command(name="get_roleless_members", brief="Get a list of members without a role", description="")
    @commands.check(permissions.is_owner)
    @commands.guild_only()
    async def get_roleless_members(self, ctx, lookup_in_db: str = None):
        for member in ctx.guild.members:
            if len(member.roles) < 2:
                await ctx.send(member.mention)
                if lookup_in_db:
                    async with self.bot.db.execute("SELECT osu_id FROM users WHERE user_id = ?",
                                                   [str(member.id)]) as cursor:
                        query = await cursor.fetchall()
                    if query:
                        await ctx.send("person above is in my database "
                                       f"and linked to <https://osu.ppy.sh/users/{query[0][0]}>")

    @commands.command(name="get_member_osu_profile",
                      brief="Check which osu account is a discord account linked to", description="")
    @commands.check(permissions.is_admin)
    @commands.guild_only()
    async def get_member_osu_profile(self, ctx, *, user_id):
        async with self.bot.db.execute("SELECT osu_id FROM users WHERE user_id = ?", [str(user_id)]) as cursor:
            osu_id = await cursor.fetchall()
        if osu_id:
            result = await osu.get_user(u=osu_id[0][0])
            if result:
                embed = await osuembed.user(result)
                await ctx.send(result.url, embed=embed)
            else:
                await ctx.send(f"<https://osu.ppy.sh/users/{osu_id[0][0]}>")


def setup(bot):
    bot.add_cog(MemberManagement(bot))
