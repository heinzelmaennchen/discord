import discord
from discord.ext import commands
from typing import Literal, Optional

from utils.misc import isDev

class sync(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(hidden=True)
    @commands.guild_only()
    @commands.check(isDev)
    async def sync(self, ctx: commands.Context, guilds: commands.Greedy[discord.Object], spec: Optional[Literal["~", "*", "^"]] = None) -> None:
        ''' syncs CommandTree:
        !sync       This takes all global commands within the CommandTree and sends them to Discord.
        !sync ~     This will sync all guild commands for the current context’s guild.
        !sync *     This command copies all global commands to the current guild (within the CommandTree) and syncs.
        !sync ^     This command will remove all guild commands from the CommandTree and syncs, which effectively removes all commands from the guild.
        !sync 123 456 789   This command will sync the 3 guild ids we passed: 123, 456 and 789. Only their guilds and guild-bound commands.
        '''
        if not guilds:
            if spec == "~":
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "*":
                ctx.bot.tree.copy_global_to(guild=ctx.guild)
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "^":
                ctx.bot.tree.clear_commands(guild=ctx.guild)
                await ctx.bot.tree.sync(guild=ctx.guild)
                synced = []
            else:
                synced = await ctx.bot.tree.sync()

            await ctx.send(
                f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
            )
            return

        ret = 0
        for guild in guilds:
            try:
                await ctx.bot.tree.sync(guild=guild)
            except discord.HTTPException:
                pass
            else:
                ret += 1

        await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")

async def setup(client):
    await client.add_cog(sync(client))