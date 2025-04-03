import discord
import os
import zoneinfo

from discord.ext import commands, tasks
from datetime import time, date, datetime, timedelta

from utils.db import check_connection
from utils.db import init_db

my_timezone = zoneinfo.ZoneInfo("Europe/Vienna")
time20h = time(20, 42, 0, tzinfo=my_timezone)

class gamenight(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.guild_id = int(os.environ['GUILD_ID'])
        self.ch_id = int(os.environ['GAMENIGHT_CH_ID'])
        self.usrs_ch_id = int(os.environ['GAMENIGHT_USRS_CH_ID'])
        self.cnx = init_db()
        self.cursor = self.cnx.cursor(buffered=True)
        if not self.gamenight_thread.is_running():
            self.gamenight_thread.start()
            print("Task gestartet!")
            print(datetime.now())
        
    @tasks.loop(time=time20h)
    async def gamenight_thread(self) -> None:
        #guild = await self.client.fetch_guild(self.guild_id)
        guild = self.client.guilds[0]
        thread = await guild.get_channel(self.ch_id).create_thread(name = "Zockertag TT.MM. - TT.MM.")
        poll = discord.Poll(question="Zockermittwoch wen wen wen?", duration=timedelta(days = 3), multiple=True)
        poll.add_answer(text="Montag TT.MM.")
        poll.add_answer(text="Dienstag TT.MM.")
        poll.add_answer(text="Mittwoch TT.MM.")
        poll.add_answer(text="Donnerstag TT.MM.")
        poll.add_answer(text="Freitag TT.MM.")
        await thread.send(poll=poll)
        print("Thread gestartet!")
        mention_members = self.getMembers(await guild.fetch_channel(self.usrs_ch_id))
        r = f''
        for member in mention_members:
            r += f'{member.name} '
        await thread.send(r)

    def getMembers(self, channel):
        # getChannelMembers from "main channel" to mention and add them into the thread
        # ignore Bots & specific Users
        # todo: limit Command to #zockerei on WLC and all channels on WLC Testing
        ch_members = channel.members
        mention_members = []
        for member in ch_members:
            if member.bot == True:
                continue
            # if member.name == "spiritoftheocean":
            #     continue
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
