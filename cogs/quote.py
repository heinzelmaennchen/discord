import discord
from discord.ext import commands
import os
from datetime import datetime, timezone
import mysql.connector
import random

class quote(commands.Cog):

    def __init__(self, client):
        self.client = client

        self.host = os.environ['DATABASE_HOST']
        self.user = os.environ['DATABASE_USER']
        self.passwd = os.environ['DATABASE_PW']
        self.database = os.environ['DATABASE_DB']

        self.cnx = mysql.connector.connect(
            host=self.host,
            user=self.user,
            passwd=self.passwd,
            database=self.database
        )
        self.cursor = self.cnx.cursor(buffered=True)

    @commands.command()
    @commands.guild_only()
    async def quote(self, ctx, offset=3):
      '''returns a random quote from our history'''
      randomNumber = random.randint(1, 368542)
      query = (f"""SELECT number, `time`, author, message
                FROM wlc_quotes WHERE number IN
                (SELECT nr FROM
                 (SELECT {randomNumber} AS nr""")
      for i in range(1,offset):
        query += f' UNION SELECT {randomNumber+i} AS nr'
      query += ') AS result)'

      self.cursor.execute(query)
      self.cnx.commit()
      
      if self.cursor.rowcount > 0:
        rows = self.cursor.fetchall()
        r = f'**#{rows[0][0]}**\n\n'
        timestamp = rows[0][1]

        for row in rows:
          r += f'**{row[2]}**\n *- {row[3]}*\n'

        embedQuote = discord.Embed(
          colour=discord.Colour.from_rgb(22, 136, 173),
          description=r
          )
        embedQuote.set_footer(text=timestamp)
        await ctx.send(embed=embedQuote)
      else:
        await ctx.send("Kaputt.")

def setup(client):
    client.add_cog(quote(client))
