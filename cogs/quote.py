import discord
from discord.ext import commands
from datetime import datetime, timezone
import random
from utils.db import check_connection
from utils.db import init_db


class quote(commands.Cog):
    def __init__(self, client):
        self.client = client

        self.cnx = init_db()
        self.cursor = self.cnx.cursor(buffered=True)

    @commands.command()
    @commands.guild_only()
    async def quote(self, ctx, offset=3, id=None):
        '''returns a random quote from our history'''
        if id is not None:
            try:
                number = int(id)
            except:
                await ctx.message.add_reaction('🥚')
                await ctx.message.add_reaction('👏')
                await ctx.send(
                    f'Schaut "{id}" für dich aus wie eine Zahl, du Nudeldrucker?! :F'
                )
                return
        else:
            number = random.randint(1, 368542)

        query = (f"""SELECT number, `time`, author, message
                FROM wlc_quotes WHERE number IN
                (SELECT nr FROM
                 (SELECT {number} AS nr""")
        for i in range(1, offset):
            query += f' UNION SELECT {number+i} AS nr'
        query += ') AS result)'

        # Check DB connection
        self.cnx = check_connection(self.cnx)
        self.cursor = self.cnx.cursor(buffered=True)
        # Execute query
        self.cursor.execute(query)
        self.cnx.commit()

        if self.cursor.rowcount > 0:
            rows = self.cursor.fetchall()
            r = f'**#{rows[0][0]}**\n\n'
            timestamp = rows[0][1]

            for row in rows:
                r += f'**{row[2]}**\n *- {row[3]}*\n'

            embedQuote = discord.Embed(colour=discord.Colour.from_rgb(
                22, 136, 173),
                                       description=r)
            embedQuote.set_footer(text=timestamp)
            await ctx.send(embed=embedQuote)
        else:
            await ctx.send("Kaputt.")


def setup(client):
    client.add_cog(quote(client))
