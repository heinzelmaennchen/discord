import discord
from discord.ext import commands
import os
import psycopg2

DATABASE_URL = os.environ['DATABASE_URL'] 
conn = psycopg2.connect(DATABASE_URL, sslmode='require')

class quote(commands.Cog):

  def __init__(self, client):
    self.client = client

  @commands.command()
  async def quote(self, ctx):
    await ctx.send(randomQuote())

def randomQuote():
  cur = conn.cursor()
  sql = 'SELECT * FROM wlc_quotes ORDER BY RANDOM() LIMIT 1'
  cur.execute(sql)
  row = cur.fetchone()
  r = ''

  while row is not None:
    r += (row[1] + ' ' + str(row[2]) + ' ' + row[3] + '\n')
    row = cur.fetchone()
  
  cur.close()
  return r

def setup(client):
  client.add_cog(quote(client))