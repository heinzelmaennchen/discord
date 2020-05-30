import discord
from discord.ext import commands
import asyncio
import json
from utils.misc import getMessageTime
from utils.db import check_connection
from utils.db import init_db

asdfMention = False
asdfCombo = False
asdfReset = False
asdfList = []
DISCORD_EPOCH = 1420070400000


class asdf(commands.Cog):
    def __init__(self, client):
        self.client = client

        self.cnx = init_db()
        self.cursor = self.cnx.cursor(buffered=True)

    @commands.command()
    @commands.guild_only()
    async def asdf(self, ctx):
        '''1337!!!'''
        await ctx.send('@everyone Verachtung!!! Guade lupe uiuiui')

    # List asdf fails
    @commands.command(aliases=['lf'])
    @commands.guild_only()
    async def listfails(self, ctx):
        await self.printStats(ctx, "fail")

    # List asdf stats
    @commands.command(aliases=['la'])
    @commands.guild_only()
    async def listasdf(self, ctx):
        await self.printStats(ctx, "asdf")

    # On Message Listener
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.client.user or message.author.bot or message.channel.type == "private":
            return

    # asdf check
        if message.channel.id == 405433814547169301 or message.channel.id == 705617951440633877 or message.channel.id == 156040097819525120:
            # BOT DEV Channels and #wlc
            time = getMessageTime(message)
            global asdfReset
            if time.hour == 13 and time.minute >= 35 and time.minute <= 38:
                # Check if active
                if asdfReset == False:
                    asdfReset = True
                    asyncio.create_task(self.startReset(time.minute))
                await self.checkHolyRules(message, time.minute)

    async def startReset(self, minute):
        dt = (39 - minute) * 60
        await asyncio.sleep(dt)
        global asdfMention
        global asdfCombo
        global asdfReset
        global asdfList
        asdfMention = False
        asdfCombo = False
        asdfReset = False
        asdfList.clear()

    async def checkHolyRules(self, message, minute):
        global asdfMention
        global asdfCombo
        global asdfList
        # '!asdf'
        if message.content.lower() == '!asdf':
            if minute == 36 or minute == 37:
                if asdfCombo == True:
                    await self.enforceRules(message)
                else:
                    asdfMention = True
            else:
                await self.enforceRules(message)
        # 'asdf'
        elif message.content.lower() == 'asdf':
            if minute != 37:
                await self.enforceRules(message)
            elif asdfMention == False:
                asdfMention = True
                asdfCombo = True
                if message.author.id not in asdfList:
                    asdfList.append(message.author.id)
                    self.updatePoints(message.author.id, "asdf")
                await self.enforceRules(message)
            elif asdfMention == True:
                asdfCombo = True
                if message.author.id not in asdfList:
                    asdfList.append(message.author.id)
                    self.updatePoints(message.author.id, "asdf")
        # '<anything else>'
        else:
            if minute == 37 and asdfCombo == True:
                await self.enforceRules(message)

    # Enforce the rules by adding Eierklatscher and a fail point
    async def enforceRules(self, message):
        await message.add_reaction('🥚')
        await message.add_reaction('👏')
        self.updatePoints(message.author.id, "fail")

    # Add an asdf point to the user's stats and add bonus xp
    def updatePoints(self, user, keyword):
        if keyword == "asdf":
            asdf = 1
            fail = 0
        else:
            asdf = 0
            fail = 1
        # Check DB connection
        self.cnx = check_connection(self.cnx)
        self.cursor = self.cnx.cursor(buffered=True)
        # Add a record
        query = (f"""INSERT INTO `asdf` (`date`, `author`, `asdf`, `fail`)
                   VALUES (CURRENT_DATE(), '{user}', '{asdf}', '{fail}')""")
        self.cursor.execute(query)
        self.cnx.commit()

        # self.setBonusXp(user, keyword) TODO: remove comment when bonus goes live

    # Update xp in the database - remove for fail, add for bonus
    def setBonusXp(self, user, keyword):
        # Check DB connection
        self.cnx = check_connection(self.cnx)
        self.cursor = self.cnx.cursor(buffered=True)
        # Grab the author's record
        query = (f'SELECT author, xp FROM levels WHERE author = {user.id}')
        self.cursor.execute(query)
        self.cnx.commit()

        row = self.cursor.fetchone()
        if keyword == "asdf":
            new_xp = row[1] + 1337
        else:
            if row[1] < 1337:
                new_xp = 0
            else:
                new_xp = row[1] - 1337

        query = (f'UPDATE `levels` SET `xp`={new_xp} WHERE author = {user.id}')
        self.cursor.execute(query)
        self.cnx.commit()

    # List asdf stats
    async def asdfStreak(self):
        # Check DB connection
        self.cnx = check_connection(self.cnx)
        self.cursor = self.cnx.cursor(buffered=True)
        query = (f"""SELECT c.dt,
                            IFNULL(a.asdf, '0')
                     FROM `calendar` c
                     LEFT OUTER JOIN
                       (SELECT DATE, COUNT(asdf) AS asdf
                        FROM `asdf`
                        WHERE asdf > 0
                        GROUP BY 1) AS a ON c.dt = a.date
                     WHERE dt BETWEEN '2020-05-05' AND '2020-05-30'
                     ORDER BY c.dt;""")
        self.cursor.execute(query)
        self.cnx.commit()

        if self.cursor.rowcount > 0:
            rows = self.cursor.fetchall()
            maxStreak = 0
            currStreak = 0

            for row in rows:
                if int(row[1]) > 0:
                    currStreak += 1
                elif int(row[1]) == 0:
                    if currStreak > maxStreak:
                        maxStreak = currStreak
                    currStreak = 0

            return max(maxStreak, currStreak)

    # Calculate and print overall stats and ranking
    async def printStats(self, ctx, keyword):
        # Check DB connection
        self.cnx = check_connection(self.cnx)
        self.cursor = self.cnx.cursor(buffered=True)
        query = (f"""SELECT author,
                            count({keyword})
                     FROM `asdf`
                     WHERE {keyword} > 0
                     GROUP BY 1;""")
        self.cursor.execute(query)
        self.cnx.commit()

        if self.cursor.rowcount > 0:
            rows = self.cursor.fetchall()
            r = ''
            total = 0
            asdfEmbed = discord.Embed(title=f'{keyword.upper()} ranking',
                                      colour=discord.Colour.from_rgb(
                                          25, 100, 25))

            for row in rows:
                total += int(row[1])
                user = ctx.guild.get_member(int(row[0]))
                if user.nick == None:
                    user = user.name
                else:
                    user = user.nick
                r += f'{user}: {row[1]}\n'

            if keyword == "asdf":
                # Grab asdfStreak
                streak = await self.asdfStreak()
                asdfEmbed.add_field(
                    name=f'**Gesamt: {total}\nMax Streak: {streak}**', value=r)
            else:
                asdfEmbed.add_field(name=f'**Gesamt: {total}**', value=r)

            if total == 0:
                await ctx.send(f'```Noch keine {keyword}s ... bis jetzt.```')
            else:
                await ctx.send(embed=asdfEmbed)


def setup(client):
    client.add_cog(asdf(client))