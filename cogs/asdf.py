import discord
from discord.ext import commands
import asyncio

from datetime import datetime, timedelta
from pytz import timezone

from utils.misc import getMessageTime, getNick
from utils.db import check_connection, init_db

from cogs.levels import levels

asdfMention = False
asdfCombo = False
asdfReset = False
asdfList = []
DISCORD_EPOCH = 1420070400000


class asdf(commands.Cog):
    def __init__(self, client):
        self.client = client
        # Initiate an instance of levels to use its updateXp function
        self.levels = levels(client)

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

    # List asdf stats
    @commands.command(aliases=['ls'])
    @commands.guild_only()
    async def liststreak(self, ctx):
        await self.printStreak(ctx)

    # On Message Listener
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.client.user or message.author.bot or message.channel.type == "private":
            return

        # asdf check in BOT DEV channels and #wlc
        if message.channel.id == 405433814547169301 or message.channel.id == 705617951440633877 or message.channel.id == 156040097819525120:
            time = getMessageTime(message.id)
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
                    self.updatePoints(message, 'asdf')
                await self.enforceRules(message)
            elif asdfMention == True:
                asdfCombo = True
                if message.author.id not in asdfList:
                    asdfList.append(message.author.id)
                    self.updatePoints(message, 'asdf')
        # '<anything else>'
        else:
            if minute == 37 and asdfCombo == True:
                await self.enforceRules(message)

    # Enforce the rules by adding Eierklatscher and a fail point
    async def enforceRules(self, message):
        await message.add_reaction('🥚')
        await message.add_reaction('👏')
        self.updatePoints(message, 'fail')

    # Add an asdf or fail point to the user's stats and add or remove bonus xp
    def updatePoints(self, message, keyword):
        if keyword == 'asdf':
            asdf = 1
            fail = 0
        else:
            asdf = 0
            fail = 1
        # Check DB connection
        self.cnx = check_connection(self.cnx)
        self.cursor = self.cnx.cursor(buffered=True)
        # Add the record
        query = (f"""INSERT INTO `asdf` (`date`, `author`, `asdf`, `fail`)
                   VALUES (CURRENT_DATE(), '{message.author.id}', '{asdf}', '{fail}')"""
                 )
        self.cursor.execute(query)
        self.cnx.commit()

        # Execute updateXp from levels to give or remove bonus xp
        asyncio.create_task(self.levels.updateXp(message, keyword))

    # List asdf stats
    async def printStreak(self, ctx):
        async with ctx.channel.typing():
            # Check DB connection
            self.cnx = check_connection(self.cnx)
            self.cursor = self.cnx.cursor(buffered=True)

            # Determine the last date for the streak, which is yesterday if today's asdf hasn't happened
            now = datetime.now(timezone('Europe/Vienna'))
            asdfTime = now.replace(hour=13, minute=38, second=0, microsecond=0)
            if now > asdfTime:
                today = datetime.now(
                    timezone('Europe/Vienna')).strftime('%Y-%m-%d')
            else:
                today = datetime.now(
                    timezone('Europe/Vienna')) - timedelta(days=1)
                today = today.strftime('%Y-%m-%d')

            resetDate = '2020-06-04'

            # Grab wlc with the correct date
            query = (f"""SELECT c.dt,
                                IFNULL(a.asdf, '0')
                         FROM `calendar` c
                         LEFT OUTER JOIN
                           (SELECT DATE, COUNT(asdf) AS asdf
                            FROM `asdf`
                            WHERE asdf > 0
                            GROUP BY 1) AS a ON c.dt = a.date
                         WHERE dt BETWEEN '{resetDate}' AND '{today}'
                         ORDER BY c.dt;""")
            self.cursor.execute(query)
            self.cnx.commit()

            wlc_streak = 0
            streak_end = "läuft lohnt"

            if self.cursor.rowcount > 0:
                rows = self.cursor.fetchall()
                maxStreak = 0
                currStreak = 0

                # Grab max streak for wlc
                for row in rows:
                    if int(row[1]) > 0:
                        currStreak += 1
                    elif int(row[1]) == 0:
                        if currStreak > maxStreak:
                            maxStreak = currStreak
                            streak_end = row[0]
                        currStreak = 0

                wlc_streak = max(maxStreak, currStreak)

                # Grab active streak for wlc
                rows_sorted = sorted(rows, key=lambda x: x[0], reverse=True)
                activeStreak = 0

                for row in rows_sorted:
                    if int(row[1]) > 0:
                        activeStreak += 1
                    elif int(row[1]) == 0:
                        break

                wlc_active_streak = activeStreak

            # Set streak end to the day before
            if streak_end != "läuft lohnt":
                streak_end -= timedelta(days=1)

            # Grab users
            query = (f"SELECT DISTINCT(author) FROM `asdf`")
            self.cursor.execute(query)
            self.cnx.commit()

            if self.cursor.rowcount > 0:
                rows = self.cursor.fetchall()
                user_max_streaks = {}
                user_active_streaks = {}
                r = ''
                asdfEmbed = discord.Embed(
                    title=f'Top and (active) ASDF streaks',
                    colour=discord.Colour.from_rgb(102, 153, 255))

                for row in rows:
                    user_max_streak = self.getUserStreak(
                        True, int(row[0]), resetDate, today)
                    user_active_streak = self.getUserStreak(
                        False, int(row[0]), resetDate, today)
                    user = ctx.guild.get_member(int(row[0]))
                    if user == None:  # Skip User if not found in Guild
                        continue
                    else:  # User in guild > check if Nick or use Name instead
                        user = getNick(user)
                    user_max_streaks[user] = user_max_streak
                    user_active_streaks[user] = user_active_streak

                user_max_streaks_sorted = sorted(user_max_streaks.items(),
                                                 key=lambda x: x[1],
                                                 reverse=True)

                for user in user_max_streaks_sorted:
                    r += f'{user[0]}: {user[1]} ({user_active_streaks[user[0]]})\n'

                asdfEmbed.add_field(
                    name=
                    f'**WLC max: {wlc_streak}**\nWLC active: {wlc_active_streak}\nMax ended: {streak_end}',
                    value=r)

        if wlc_streak == 0:
            await ctx.send(f'```Noch keine streak ... bis jetzt.```')
        else:
            await ctx.send(embed=asdfEmbed)

    # Calculate user streak
    def getUserStreak(self, isMax, user, resetDate, today):
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
                        AND author = {user}
                        GROUP BY 1) AS a ON c.dt = a.date
                     WHERE dt BETWEEN '{resetDate}' AND '{today}'
                     ORDER BY c.dt;""")
        self.cursor.execute(query)
        self.cnx.commit()

        # If max streak is requested, grab max
        if isMax:
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

        # Otherwise grab the active streak and return it
        else:
            if self.cursor.rowcount > 0:
                rows = self.cursor.fetchall()
                rows_sorted = sorted(rows, key=lambda x: x[0], reverse=True)
                activeStreak = 0

                for row in rows_sorted:
                    if int(row[1]) > 0:
                        activeStreak += 1
                    elif int(row[1]) == 0:
                        break

                return activeStreak

    # Calculate and print overall stats and ranking
    async def printStats(self, ctx, keyword):
        async with ctx.channel.typing():
            # Check DB connection
            self.cnx = check_connection(self.cnx)
            self.cursor = self.cnx.cursor(buffered=True)
            query = (f"""SELECT author,
                                count({keyword})
                         FROM `asdf`
                         WHERE {keyword} > 0
                         GROUP BY 1
                        ORDER BY 2 DESC;""")
            self.cursor.execute(query)
            self.cnx.commit()

            total = 0

            if self.cursor.rowcount > 0:
                rows = self.cursor.fetchall()
                r = ''

                # ASDF ranking should be green
                if keyword == "asdf":
                    colour = discord.Colour.from_rgb(25, 100, 25)
                else:
                    colour = discord.Colour.from_rgb(153, 0, 0)

                asdfEmbed = discord.Embed(title=f'{keyword.upper()} ranking',
                                          colour=colour)

                for row in rows:
                    total += int(row[1])
                    user = ctx.guild.get_member(int(row[0]))
                    if user == None:  # Skip User if not found in Guild
                        continue
                    else:  # User in guild > check if Nick or use Name instead
                        user = getNick(user)
                    r += f'{user}: {row[1]}\n'

                asdfEmbed.add_field(name=f'**Gesamt: {total}**', value=r)

        if total == 0:
            await ctx.send(f'```Noch keine {keyword}s ... bis jetzt.```')
        else:
            await ctx.send(embed=asdfEmbed)


def setup(client):
    client.add_cog(asdf(client))