import discord
from discord.ext import commands
import random
import os
import requests

repeat_dict = {}

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

  # Triple repeat
  @commands.Cog.listener()
  async def on_message(self, message):
    '''repeats the message if the same message was sent three times in a row by unique authors'''
    if message.author == self.client.user or message.author.bot or message.channel.type == "private":
        return
   
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
        gif_url = r['results'][0]['url']
      except:
        gif_url = 'I find\' nix!'
      return gif_url

def setup(client):
  client.add_cog(skills(client))