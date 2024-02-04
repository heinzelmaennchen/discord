import discord
from discord.ext import commands
import asyncio
from utils.db import check_connection, init_db
from utils.levels import createRankcard, createLeaderboard
from utils.misc import getNick


class levels(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.cnx = init_db()
        self.cursor = self.cnx.cursor(buffered=True)
        self.active_authors = []

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.client.user or message.author.bot or message.channel.type == "private" or self.client.user.id != 404467681387872257:
            return

        if message.author.id in self.active_authors:
            return
        else:
            self.active_authors.append(message.author.id)
            asyncio.create_task(self.updateXp(message))

    @commands.command()
    @commands.guild_only()
    async def rank(self, ctx):
        # Check DB connection
        self.cnx = check_connection(self.cnx)
        self.cursor = self.cnx.cursor(buffered=True)
        # Grab the author's record
        query = (
            f'SELECT author, xp, level FROM levels WHERE author = {ctx.message.author.id}'
        )
        self.cursor.execute(query)
        self.cnx.commit()
        if self.cursor.rowcount == 0:
            await ctx.message.channel.send(
                f"Du hast noch keinen Rank, du Nudel!")
        # Build an embed with the current level and xp and send it
        else:
            row = self.cursor.fetchone()
            xp = row[1]
            level_current = row[2]

            nlvlxp = 5 * (level_current**2) + 50 * level_current + 100
            rest_xp = xp
            for i in range(0, 500):
                xp_needed = 5 * (i**2) + 50 * i + 100
                rest_xp -= xp_needed
                if rest_xp < 0:
                    rest_xp += xp_needed
                    break

            if ctx.author.nick == None:
                name = ctx.author.name
            else:
                name = ctx.author.nick

            query = ('SELECT author, xp FROM levels ORDER BY xp DESC')
            self.cursor.execute(query)
            self.cnx.commit()
            rank = 0
            for row in self.cursor.fetchall():
                rank += 1
                if ctx.author.id == row[0]:
                    break

            imgRankcard = await createRankcard(name, ctx.author.avatar_url, rank, xp,
                                 level_current, rest_xp, nlvlxp)
            await ctx.send(file=discord.File(imgRankcard, filename=f"{name}.png"))

    @commands.command()
    @commands.guild_only()
    async def levels(self, ctx):
        async with ctx.channel.typing():
            # Check DB connection
            self.cnx = check_connection(self.cnx)
            self.cursor = self.cnx.cursor(buffered=True)
            # Grab all records
            query = (f'SELECT author, xp, level FROM levels ORDER BY xp DESC')
            self.cursor.execute(query)
            self.cnx.commit()
            if self.cursor.rowcount == 0:
                await ctx.message.channel.send(
                    f'Keiner da, keiner hat levels. :person_shrugging:')
            # Build Lists with authors, author_urls, levels, xp, lvlxp and nlvlxp
            else:
                author = []
                authorurl = []
                level = []
                xp = []
                lvlxp = []
                nlvlxp = []
                for row in self.cursor.fetchall():
                    user = ctx.guild.get_member(row[0])
                    if user == None:  # Skip User if not found in Guild
                        continue
                    else:  # User in guild > check if Nick or use Name instead
                        name = getNick(user)
                    author.append(name)
                    authorurl.append(user.avatar_url)
                    xp.append(row[1])
                    level.append(row[2])

                    nlvlxp.append(5 * (row[2]**2) + 50 * row[2] + 100)
                    rest_xp = row[1]
                    for i in range(0, 500):
                        xp_needed = 5 * (i**2) + 50 * i + 100
                        rest_xp -= xp_needed
                        if rest_xp < 0:
                            rest_xp += xp_needed
                            break
                    lvlxp.append(rest_xp)
                # create Image
                imgLeaderboard = await createLeaderboard(author, authorurl, level, xp, lvlxp,
                                        nlvlxp)
                await ctx.send(file=discord.File(imgLeaderboard, filename="leaderboard.png"))

    # Runs in its own thread and updates the author's XP in the database
    async def updateXp(self, message, keyword=None):
        # Wait before the asdf period is over to distribute bonus xp
        if keyword is not None:
            await asyncio.sleep(180)
        # Check DB connection
        self.cnx = check_connection(self.cnx)
        self.cursor = self.cnx.cursor(buffered=True)
        # Grab the author's record
        query = (
            f'SELECT author, xp, level FROM levels WHERE author = {message.author.id}'
        )
        self.cursor.execute(query)
        self.cnx.commit()

        # If the author is new, create a row, give them 20xp and level 1
        if self.cursor.rowcount == 0:
            query = (
                f'INSERT INTO `levels` (`author`, `xp`, `level`) VALUES ("{message.author.id}", "20", "0")'
            )
            self.cursor.execute(query)
            self.cnx.commit()
        else:
            row = self.cursor.fetchone()
            # Check the keyword to determine xp modifier
            if keyword == 'asdf':
                new_xp = row[1] + 1337
            elif keyword == 'fail':
                if row[1] < 1337:
                    new_xp = 0
                else:
                    new_xp = row[1] - 1337
            else:
                new_xp = row[1] + 20

            level_current = row[2]
            loop_xp = 0

            # Calculate the level limits and check if there was a level-up
            for i in range(0, 500):
                xp_needed = 5 * (i**2) + 50 * i + 100
                loop_xp += xp_needed
                if loop_xp > new_xp:
                    level_reached = i
                    break

            # Check for levelup, leveldown or no change
            if level_reached > level_current:
                query = (
                    f'UPDATE `levels` SET `xp`={new_xp}, `level`={level_reached} WHERE author = {message.author.id}'
                )
                await message.channel.send(
                    f"Grz {message.author.mention}, du Heisl! **Level {level_reached}!**"
                )
            elif level_reached < level_current:
                query = (
                    f'UPDATE `levels` SET `xp`={new_xp}, `level`={level_reached} WHERE author = {message.author.id}'
                )
                await message.channel.send(
                    f"Grz zum verlorenen Level, {message.author.mention}, du Heisl! **Level {level_reached}!**"
                )
            else:
                query = (
                    f'UPDATE `levels` SET `xp`={new_xp} WHERE author = {message.author.id}'
                )

            self.cursor.execute(query)
            self.cnx.commit()
        # If regular message, wait for 30 seconds and then remove the author from the active list to allow for new XP
        if keyword == None:
            await asyncio.sleep(30)
            self.active_authors.remove(message.author.id)
        else:
            return


def setup(client):
    client.add_cog(levels(client))
