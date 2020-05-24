import discord
from discord.ext import commands
import os
import mysql.connector
import asyncio


class levels(commands.Cog):

  def __init__(self, client):
    self.client = client

    self.host = os.environ['DATABASE_HOST']
    self.user = os.environ['DATABASE_USER']
    self.passwd = os.environ['DATABASE_PW']
    self.database = os.environ['DATABASE_DB']

    self.active_authors = []

    self.cnx = mysql.connector.connect(
      host=self.host,
      user=self.user,
      passwd=self.passwd,
      database=self.database
      )
    self.cursor = self.cnx.cursor(buffered=True)

  @commands.Cog.listener()
  async def on_message(self, message):
    if message.author == self.client.user or message.author.bot or message.channel.type == "private":
      return

    if message.author.id in self.active_authors:
      return
    else:
      self.active_authors.append(message.author.id)
      asyncio.create_task(self.updateXp(message))

  @commands.command()
  @commands.guild_only()
  async def rank(self, ctx):
    # Grab the author's record
    query = (f'SELECT author, xp, level FROM levels WHERE author = {ctx.message.author.id}')
    self.cursor.execute(query)
    self.cnx.commit()
    if self.cursor.rowcount == 0:
      await ctx.message.channel.send(f"Du hast noch keinen Rank, du Nudel!")
    # Build an embed with the current level and xp and send it
    else:
      row = self.cursor.fetchone()
      xp = row[1]
      level_current = row[2]

      if ctx.author.nick == None:
        name = ctx.author.name
      else:
        name = ctx.author.nick

      embed = discord.Embed(
        colour = discord.Colour.orange(),
        description = f'{name}, du Heisl, du bist Level {level_current} mit {xp} XP!'
        )
      
      await ctx.send(embed = embed)

  
  @commands.command()
  @commands.guild_only()
  async def levels(self, ctx):
    # Grab all records
    query = (f'SELECT author, xp, level FROM levels ORDER BY xp DESC')
    self.cursor.execute(query)
    self.cnx.commit()
    if self.cursor.rowcount == 0:
      await ctx.message.channel.send(f"Keiner da, keiner hat levels. :person_shrugging:")
    # Build an embed with all authors, current level and xp and send it
    else:
      r = ''
      rank = 0
      for row in self.cursor.fetchall():
        rank += 1
        author = row[0]
        user = ctx.guild.get_member(author)
        if user.nick == None:
          name = user.name
        else:
          name = user.nick
        xp = row[1]
        level_current = row[2]
        r += f'#{rank} {name} - Level {level_current} mit {xp} XP!\n'

      embed = discord.Embed(
        colour = discord.Colour.orange(),
        description = r
        )
      
      await ctx.send(embed = embed)

  # Runs in its own thread and updates the author's XP in the database
  async def updateXp(self, message):
    # Grab the author's record
    query = (f'SELECT author, xp, level FROM levels WHERE author = {message.author.id}')
    self.cursor.execute(query)
    self.cnx.commit()
    
    # If the author is new, create a row, give them 20xp and level 1
    if self.cursor.rowcount == 0:
      query = (f'INSERT INTO `levels` (`author`, `xp`, `level`) VALUES ("{message.author.id}", "20", "0")') 
      self.cursor.execute(query)
      self.cnx.commit()
    else:
      row = self.cursor.fetchone()
      new_xp = row[1] + 20
      level_current = row[2]
      loop_xp = 0
      # Calculate the level limits and check if there was a level-up
      for i in range(0,500):
        xp_needed = 5 * (i ** 2) + 50 * i + 100
        loop_xp += xp_needed
        if loop_xp > new_xp:
          level_reached = i
          break
      
      if level_reached > level_current:
        # sendCongratsMessage(message.author.id) TODO: congrats message
        query = (f'UPDATE `levels` SET `xp`={new_xp}, `level`={level_reached} WHERE author = {message.author.id}') 
        self.cursor.execute(query)
        self.cnx.commit()
        await message.channel.send(f"Grz {message.author.mention}, du Heisl! **Level {level_reached}!**")
      else:
        query = (f'UPDATE `levels` SET `xp`={new_xp} WHERE author = {message.author.id}') 
        self.cursor.execute(query)
        self.cnx.commit()
    # Wait for a minute and then remove the author from the active list to allow for new XP
    await asyncio.sleep(30)
    self.active_authors.remove(message.author.id)

def setup(client):
  client.add_cog(levels(client))
