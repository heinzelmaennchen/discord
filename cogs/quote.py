import discord
from discord.ext import commands
import os
import psycopg2
from datetime import datetime, timezone

DATABASE_URL = os.environ['DATABASE_URL'] 
conn = psycopg2.connect(DATABASE_URL, sslmode='require')

class quote(commands.Cog):

  def __init__(self, client):
    self.client = client

  @commands.command()
  async def quote(self, ctx):
    '''returns a random quote from our history'''
    await ctx.send(embed = randomQuote())

def randomQuote():
  cur = conn.cursor()
  sql = 'SELECT * FROM wlc_quotes ORDER BY RANDOM() LIMIT 1'
  cur.execute(sql)
  row = cur.fetchone()
  r = ''
  
  while row is not None:
    r += ('[' + str(datetime.fromtimestamp(row[2])) + '] ' + row[1] + ': ' + row[3] + '\n')
    embedQuote = discord.Embed(
      colour = discord.Colour.from_rgb(22, 136, 173),
      description = f'{row[3]}\n - {row[1]}'
    )
    embedQuote.set_footer(text = str(datetime.fromtimestamp(row[2])))

    row = cur.fetchone()
  
  cur.close()
  return embedQuote

def setup(client):
  client.add_cog(quote(client))