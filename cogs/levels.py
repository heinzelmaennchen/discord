import discord
from discord.ext import commands
import os
import mysql.connector
import asyncio
from helpers.levels import createRankcard, createLeaderboard


class levels(commands.Cog):
    def __init__(self, client):
        self.client = client

        self.host = os.environ['DATABASE_HOST']
        self.user = os.environ['DATABASE_USER']
        self.passwd = os.environ['DATABASE_PW']
        self.database = os.environ['DATABASE_DB']

        self.active_authors = []

        self.cnx = mysql.connector.connect(host=self.host,
                                           user=self.user,
                                           passwd=self.passwd,
                                           database=self.database)
        self.cursor = self.cnx.cursor(buffered=True)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.client.user or message.author.bot or message.channel.type == "private" or message.guild.id != 156040097819525120:
            return

        if message.author.id in self.active_authors:
            return
        else:
            self.active_authors.append(message.author.id)
            asyncio.create_task(self.updateXp(message))

    @commands.command()
    @commands.guild_only()
    async def rank(self, ctx):
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

            query = ('SELECT author, xp FROM levels ORDER BY xp DESC')
            self.cursor.execute(query)
            rank = 0
            for row in self.cursor.fetchall():
                rank += 1
                if ctx.author.id == row[0]:
                    break

            createRankcard(ctx.author.name, ctx.author.discriminator,
                           ctx.author.avatar_url, rank, level_current, rest_xp,
                           nlvlxp)
            await ctx.send(
                file=discord.File(f"storage/levels/{ctx.author.name}.png"))

    @commands.command()
    @commands.guild_only()
    async def levels(self, ctx):
        async with ctx.channel.typing():
            # Grab all records
            query = (f'SELECT author, xp, level FROM levels ORDER BY xp DESC')
            self.cursor.execute(query)
            self.cnx.commit()
            if self.cursor.rowcount == 0:
                await ctx.message.channel.send(
                    f"Keiner da, keiner hat levels. :person_shrugging:")
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
                        if user.nick == None:
                            name = user.name
                        else:
                            name = user.nick
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
                createLeaderboard(author, authorurl, level, xp, lvlxp, nlvlxp)
                await ctx.send(
                    file=discord.File('storage/levels/leaderboard.png'))

    # Runs in its own thread and updates the author's XP in the database
    async def updateXp(self, message):
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

            if level_reached > level_current:
                # sendCongratsMessage(message.author.id) TODO: congrats message
                query = (
                    f'UPDATE `levels` SET `xp`={new_xp}, `level`={level_reached} WHERE author = {message.author.id}'
                )
                self.cursor.execute(query)
                self.cnx.commit()
                await message.channel.send(
                    f"Grz {message.author.mention}, du Heisl! **Level {level_reached}!**"
                )
            else:
                query = (
                    f'UPDATE `levels` SET `xp`={new_xp} WHERE author = {message.author.id}'
                )
                self.cursor.execute(query)
                self.cnx.commit()
        # Wait for 30 seconds and then remove the author from the active list to allow for new XP
        await asyncio.sleep(30)
        self.active_authors.remove(message.author.id)


def setup(client):
    client.add_cog(levels(client))
