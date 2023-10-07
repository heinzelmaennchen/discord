from discord.ext import commands
from datetime import timedelta
from utils.db import check_connection
from utils.db import init_db


class gamenight(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.cnx = init_db()
        self.cursor = self.cnx.cursor(buffered=True)

    @commands.command()
    @commands.guild_only()
    async def shift(self, ctx):
        '''returns this weeks and next weeks shift from db'''

        query = (f"""SELECT date, WEEKDAY(date) as day, shift
                 FROM schicht
                 WHERE WEEK(CURDATE(),1)=WEEK(date,1)
                 OR (WEEK(CURDATE(),1)+1)=WEEK(date,1)""")

        # Check DB connection
        self.cnx = check_connection(self.cnx)
        self.cursor = self.cnx.cursor(buffered=True)
        # Execute query
        self.cursor.execute(query)
        self.cnx.commit()

        if self.cursor.rowcount > 0:
            rows = self.cursor.fetchall()
            dateStart1 = rows[0][0]
            sixdays = timedelta(days=6)
            dateEnd1 = dateStart1 + sixdays
            dateEnd2 = rows[-1][0]
            r = f"```Diese Woche ({dateStart1.day}.{dateStart1.month}. - {dateEnd1.day}.{dateEnd1.month}.):\n"
            for row in rows:
                if row[1] == 0 and not row == rows[0]:
                    dateStart2 = row[0]
                    r = r[:-2] + f"\n\nNächste Woche ({dateStart2.day}.{dateStart2.month}. - {dateEnd2.day}.{dateEnd2.month}.):\n"
                day = self.getDayString(row[1])
                r += f'{day}: {row[2]} | '
            r = r[:-2] + "```"            
            await ctx.send(r)
        else:
            await ctx.send("Kaputt.")

    def getDayString(self, day):
        days = ['Mo','Di','Mi','Do','Fr','Sa','So']
        return days[day]



def setup(client):
    client.add_cog(gamenight(client))
