import discord
from discord.ext import commands
import random
import os
import requests
import json
import asyncio
from datetime import datetime
from pytz import timezone

repeat_dict = {}
asdfMention = False
asdfCombo = False
asdfReset = False
asdfList = []
DISCORD_EPOCH = 1420070400000


class skills(commands.Cog):

  def __init__(self, client):
    self.client = client
    self.youtube_key = os.environ['YOUTUBE_KEY']
    self.tenor_key = os.environ['TENOR_KEY']

  @commands.command()
  @commands.guild_only()
  async def asdf(self, ctx):
    '''1337!!!'''
    await ctx.send('@everyone Verachtung!!! Guade lupe uiuiui')
  
  # Calculator
  @commands.command()
  @commands.guild_only()
  async def calc(self, ctx, *, calcString):
    '''calculates the result of your expression'''
    result = self.doCalculate(calcString)
    if result:
      await ctx.send(result)
  
  def doCalculate(self, calcStr):
    try:
      result = eval(calcStr.replace(",","."), {'__builtins__': None})
      if result % 1 == 0:
        r = int(result)
      else:
        r = float(result)
    except:
      r = False
    return r

  # Dice Roll
  @commands.command(aliases=['rand', 'dice', 'roll'])
  @commands.guild_only()
  async def random(self, ctx, *arg):
    '''returns a random number
    instructions:
    -----------
    !random
        return a random number between 1 and 100
    !random coin
        throw a coin (heads or tails)
    !random 6
        return a random number between 1 and 6
    !random 10 20
        return a random number between 10 and 20
    '''
    if ctx.invoked_subcommand is None:
      if not arg:
        start = 1
        end = 100
      elif arg[0] == 'flip' or arg[0] == 'coin':
        coin = ['heads', 'tails']
        await ctx.send(':arrows_counterclockwise: {0}'.format(random.choice(coin)))
        return
      elif len(arg) == 1:
        start = 1
        end = int(arg[0])
      elif len(arg) > 1:
        start = int(arg[0])
        end = int(arg[1])
      await ctx.send('**:arrows_counterclockwise:** ({0} - {1}): {2}'.format(start, end, random.randint(start, end)))
    
  # On Message Listener
  @commands.Cog.listener()
  async def on_message(self, message):
    '''repeats the message if the same message was sent three times in a row by unique authors'''
    if message.author == self.client.user or message.author.bot or message.channel.type == "private":
      return

    # ASDF check
    if message.channel.id == 405433814547169301 or message.channel.id == 705617951440633877 or message.channel.id == 156040097819525120:
      # BOT DEV Channels und #wlc
      time = self.getMessageTime(message)
      global asdfMention
      global asdfCombo
      global asdfReset
      if time.hour == 13 and time.minute >= 35 and time.minute <= 38:
        #CHECK AKTIV
        if asdfReset == False:
          asdfReset = True
          resetTask = asyncio.create_task(self.startReset(time.minute))
          await resetTask
        await self.checkHolyRules(message, time.minute)

    # Triple repeat
    author_list = []
    global repeat_dict

    if message.channel.id in repeat_dict:
      comparison_message = str(repeat_dict[message.channel.id][0])
      author_list = repeat_dict[message.channel.id][1]
      if message.content.lower() == comparison_message.lower():
        if message.author.id not in author_list:
          author_list.append(message.author.id)
          if len(author_list) == 3:
            await message.channel.send(message.content)
            repeat_dict.pop(message.channel.id, None)
      else:
        repeat_dict.update({message.channel.id : [message.content,[message.author.id]]})
    else:
      repeat_dict.update({message.channel.id : [message.content,[message.author.id]]})

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
  
  def getMessageTime(self, message):
    ms = (message.id >> 22) + DISCORD_EPOCH
    time = datetime.fromtimestamp(ms/1000, timezone('Europe/Vienna'))
    return time
  
  async def checkHolyRules(self, message, minute):
    global asdfMention
    global asdfCombo
    global asdfList
    # !ASDF
    if message.content.lower() == '!asdf':
      if minute == 36 or minute == 37:
        if asdfCombo == True:
          await self.enforceRules(message)
        else:
          asdfMention = True
      else:
        await self.enforceRules(message)
    # ASDF
    elif message.content.lower() == 'asdf':
      if  minute != 37:
        await self.enforceRules(message)
      elif asdfMention == False:
        asdfMention = True
        asdfCombo = True
        if message.author.id not in asdfList:
          asdfList.append(message.author.id)
          self.addAsdfPoint(str(message.author.id))
        await self.enforceRules(message)
      elif asdfMention == True:
        asdfCombo = True
        if message.author.id not in asdfList:
          asdfList.append(message.author.id)
          self.addAsdfPoint(str(message.author.id))
    # ALLES ANDERE
    else:
      if minute == 37 and asdfCombo == True:
        await self.enforceRules(message)

  async def enforceRules(self, message):
    await message.add_reaction('🥚')
    await message.add_reaction('👏')
    self.addFailPoint(str(message.author.id))

  def addFailPoint(self, user):
    with open('storage/asdf.json') as json_file:
      jsonAsdfData = json.load(json_file)
    if user in jsonAsdfData['fails']['user']:
      jsonAsdfData['fails']['user'][user] = int(jsonAsdfData['fails']['user'][user]) + 1
    else:
      jsonAsdfData['fails']['user'][user] = 1
    with open('storage/asdf.json', 'w') as json_file:
      json.dump(jsonAsdfData, json_file, indent = 4, ensure_ascii=True)

  def addAsdfPoint(self, user):
    global asdfList
    with open('storage/asdf.json') as json_file:
      jsonAsdfData = json.load(json_file)
    if user in jsonAsdfData['asdf']['user']:
      jsonAsdfData['asdf']['user'][user] = int(jsonAsdfData['asdf']['user'][user]) + 1
    else:
      jsonAsdfData['asdf']['user'][user] = 1
    with open('storage/asdf.json', 'w') as json_file:
      json.dump(jsonAsdfData, json_file, indent = 4, ensure_ascii=True)
  
  @commands.command(aliases = ['lf'])
  @commands.guild_only()
  async def listfails(self, ctx):
    with open('storage/asdf.json') as json_file:
      jsonAsdfData = json.load(json_file)
    fails = 0
    r = ''
    for u, f in jsonAsdfData['fails']['user'].items():
      fails += f
      user = ctx.guild.get_member(int(u))
      if user.nick == None:
        user = user.name
      else:
        user = user.nick
      r += f'\n{user}: {f}'
    r = f'```FAILs gesamt: {fails}' + r + '```'
    await ctx.send(r)

  @commands.command(aliases = ['la'])
  @commands.guild_only()
  async def listasdf(self, ctx):
    with open('storage/asdf.json') as json_file:
      jsonAsdfData = json.load(json_file)
    asdf = 0
    r = ''
    for u, a in jsonAsdfData['asdf']['user'].items():
      asdf += a
      user = ctx.guild.get_member(int(u))
      if user.nick == None:
        user = user.name
      else:
        user = user.nick
      r += f'\n{user}: {a}'
    r = f'```ASDFs gesamt: {asdf}' + r + '```'
    await ctx.send(r)
  
  # Youtube video search
  @commands.command()
  @commands.guild_only()
  async def yt(self, ctx, *, searchterm=None):
    '''returns a youtube video related to the search string'''
    if searchterm is None:
      await ctx.send("Und wonach soll ich jetzt suchen, du Heisl?")
    else:
      await ctx.send(self.searchVideo(searchterm))

  def searchVideo(self, searchterm):
      url = "https://www.googleapis.com/youtube/v3/search"
      payload = {
          'key' : self.youtube_key,
          'q' : searchterm,
          'part' : 'snippet',
          'maxResults' : 1,
          'safeSearch' : 'none',
          'type' : 'video'
      }

      r = requests.get(url, params=payload).json()
      video_id = r['items'][0]['id']['videoId']
      video_url = ('https://youtube.com/watch?v=' + video_id)
      return video_url

  # Tenor GIF search
  @commands.command()
  @commands.guild_only()
  async def gif(self, ctx, *, searchterm=None):
    '''returns a gif related to the search string'''
    if searchterm is None:
      await ctx.send("Und wonach soll ich jetzt suchen, du Heisl?")
    else: 
      await ctx.send(f'{self.searchGif(searchterm)} [via Tenor]')

  def searchGif(self, searchterm):
      url = "https://api.tenor.com/v1/search"
      payload = {
          'key' : self.tenor_key,
          'q' : searchterm,
          'limit' : 1,
      }

      r = requests.get(url, params=payload).json()
      try:
        gif_url = r['results'][0]['media'][0]['gif']['url']
      except:
        gif_url = 'I find\' nix!'
      return gif_url

  # Message recap with miliseconds timestamp
  '''returns x last messages filtered by specified content and miliseconds timestamp
    or a message by id with its timestamp
  '''
  @commands.command()
  @commands.guild_only()
  async def recap(self, ctx, *args):
    
    if not args:
      depth = 5
      filter = None
    else: 
      try:
        depth = int(args[0])
        if (len(args) > 1):
          filter = ' '.join(args[1:len(args)])
        else:
          filter = None
      except:
        filter = ' '.join(args)
        depth = 5

    async with ctx.channel.typing():
      if depth > 100000:
        message = await ctx.channel.fetch_message(depth)
        ms = (message.id >> 22) + DISCORD_EPOCH
        time = datetime.fromtimestamp(
            ms / 1000, timezone('Europe/Vienna')).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        author = message.author.name
        content = message.content
        r = (f'```\n[{time}] {author}: {content}```')
        await ctx.send(r)
        return

    if depth > 30 and filter is None:
        await ctx.send("Na. Zu viel, zu zach. :meh:")
        return

    r = '```\n'
    
    messages = await ctx.channel.history(limit=depth+1).flatten()
    result_found = False

    for message in reversed(messages[1:]):
      if filter is not None:
        if filter.lower() not in message.content.lower():
          continue
      ms = (message.id >> 22) + DISCORD_EPOCH
      time = datetime.fromtimestamp(
        ms / 1000, timezone('Europe/Vienna')).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
      author = message.author.name
      content = message.content
      if '```' in content:
        content = content.replace('```', '')
        content = content.replace('[', '--- [')
        r += (f'[{time}] {author}: {content}\n')
        continue

      r += (f'[{time}] {author}: {content}\n')
      result_found = True

    r += '```'
    if result_found:
      try:
        await ctx.send(r)
      except:
        await ctx.send("pls no - das sind mehr als 2000 Zeichen. :weary:")
    else:
      await ctx.send("Das Nichts nichtet. <:affenkaktus:709677325846839346>")

  # Wrap a code block around the input text
  @commands.command()
  @commands.guild_only()
  async def cb(self, ctx, *, arg):
    embed = discord.Embed(
      colour = discord.Colour.orange(),
      description = f'```{arg}```'
    )
    if ctx.author.nick == None:
      name = ctx.author.name
    else:
      name = ctx.author.nick
    embed.set_author(name=name, icon_url=ctx.author.avatar_url)
    await ctx.send(embed = embed)
    await ctx.message.delete()

def setup(client):
    client.add_cog(skills(client))