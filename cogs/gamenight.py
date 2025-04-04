import os
import zoneinfo
import ast

from discord.ext import commands, tasks
from datetime import time, date, datetime, timedelta

from utils.db import check_connection
from utils.db import init_db

my_timezone = zoneinfo.ZoneInfo("Europe/Vienna")
task_exec_time = time(8, 0, 0, tzinfo=my_timezone)

class gamenight(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.cnx = init_db()
        self.cursor = self.cnx.cursor(buffered=True)
        self.guild_id = int(ast.literal_eval(os.environ['GUILD_IDS'])['default'])
        self.channel_id = int(ast.literal_eval(os.environ['CHANNEL_IDS'])['bottest'])
        self.test_task.start()

    @tasks.loop(time=task_exec_time)
    async def test_task(self) -> None:
        guild = self.client.get_guild(self.guild_id)
        channel = guild.get_channel(self.channel_id)
        await channel.send("Es ist 08:00 Uhr!")

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