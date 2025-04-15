import discord
import os
import ast
import random

from discord.ext import commands, tasks
from datetime import time, date, datetime, timedelta

from utils.db import check_connection, init_db
from utils.misc import getDatetimeNow, getTimezone

my_timezone = getTimezone()
gn_pollthread_time = time(21, 33, 37, tzinfo=my_timezone)

class gamenight(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.cnx = init_db()
        self.cursor = self.cnx.cursor(buffered=True)
        self.guild_id = int(ast.literal_eval(os.environ['GUILD_IDS'])['default'])
        self.channel_id = int(ast.literal_eval(os.environ['CHANNEL_IDS'])['gaming'])
        self.users_channel_id = int(ast.literal_eval(os.environ['CHANNEL_IDS'])['gaming_users'])
        if not self.gn_pollthread.is_running():
            self.gn_pollthread.start()

    def cog_unload(self):
        self.gn_pollthread.cancel()

    @tasks.loop(time=gn_pollthread_time)
    async def gn_pollthread(self) -> None:
        now = getDatetimeNow()
        weekday = now.isoweekday()
        if weekday % 4 == 0:    # True if weekday is %1: Monday, %2: Tuesday, %3: Wednesday, %4: Thursday, %5: Friday, %6: Saturday, %7: Sunday
            guild = self.client.get_guild(self.guild_id)
            channel = guild.get_channel(self.channel_id)
            emojis = guild.emojis

            thread = await channel.create_thread(name = f'Zocktag {(now + timedelta(days=3)).strftime("%d.%m.")}-{(now + timedelta(days=7)).strftime("%d.%m.")}')
            poll = discord.Poll(question="Zockermittwoch wen wen wen?", duration=timedelta(days=3), multiple=True)
            poll.add_answer(text=f'Montag {(now + timedelta(days=3)).strftime("%d.%m.")}', emoji=random.choice(emojis))
            poll.add_answer(text=f'Dienstag {(now + timedelta(days=4)).strftime("%d.%m.")}', emoji=random.choice(emojis))
            poll.add_answer(text=f'Mittwoch {(now + timedelta(days=5)).strftime("%d.%m.")}', emoji=random.choice(emojis))
            poll.add_answer(text=f'Donnerstag {(now + timedelta(days=6)).strftime("%d.%m.")}', emoji=random.choice(emojis))
            poll.add_answer(text=f'Freitag {(now + timedelta(days=7)).strftime("%d.%m.")}', emoji=random.choice(emojis))
            await thread.send(poll=poll)
            mention_members = self.getMembers(guild.get_channel(self.users_channel_id))
            r = f''
            for member in mention_members:
                r += f'{member.mention} '
            await thread.send(r)
    
    def getMembers(self, channel) -> list:
        # getChannelMembers from "main channel" to mention and add them into the thread
        # ignore Bots
        ch_members = channel.members
        mention_members = []
        for member in ch_members:
            if member.bot == True:
                continue
            mention_members.append(member)
        return mention_members


    @commands.command()
    @commands.guild_only()
    async def shift(self, ctx):
        '''returns this weeks and next weeks shift from db'''

        today = datetime.today()
        firstweekday = today - timedelta(days=today.weekday() % 7)
        firstday = date(firstweekday.year, firstweekday.month, firstweekday.day)
        lastday = firstday + timedelta(days=13)

        query = (f"""SELECT date, WEEKDAY(date) as day, shift
                 FROM schicht
                 WHERE date BETWEEN DATE("{firstday}") AND DATE("{lastday}")""")

        # Check DB connection
        self.cnx = check_connection(self.cnx)
        self.cursor = self.cnx.cursor(buffered=True)
        # Execute query
        self.cursor.execute(query)
        self.cnx.commit()

        if self.cursor.rowcount > 0:
            rows = self.cursor.fetchall()
            dateEnd1 = firstday + timedelta(days=6)
            dateStart2 = firstday + timedelta(days=7)

            r = f"```Diese Woche ({firstday.day}.{firstday.month}. - {dateEnd1.day}.{dateEnd1.month}.):\n"
            for row in rows:
                if row[1] == 0 and not row == rows[0]:
                    r = r[:-2] + f"\n\nNächste Woche ({dateStart2.day}.{dateStart2.month}. - {lastday.day}.{lastday.month}.):\n"
                day = self.getDayString(row[1])
                r += f'{day}: {row[2]} | '
            r = r[:-2] + "```"            
            await ctx.send(r)
        else:
            await ctx.send("Kaputt.")

    def getDayString(self, day):
        days = ['Mo','Di','Mi','Do','Fr','Sa','So']
        return days[day]



async def setup(client):
    await client.add_cog(gamenight(client))