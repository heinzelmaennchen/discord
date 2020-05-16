import discord
from discord.ext import commands

class fun(commands.Cog):

  def __init__(self, client):
    self.client = client

  @commands.command()
  @commands.guild_only()
  async def richtig(self, ctx):
    await ctx.send('richtig richtig richtfest!')
  
  @commands.command()
  @commands.guild_only()
  async def falsch(self, ctx):
    await ctx.send('falsch falsch Falschgeld!')

  @commands.command()
  @commands.guild_only()
  async def twss(self, ctx):
    await ctx.send('That\'s what she said.')
  
  @commands.command()
  @commands.guild_only()
  async def läuft(self, ctx):
    await ctx.send('läuft')
    await ctx.send('läuft')
    await ctx.send('lohnt')

  @commands.command()
  @commands.guild_only()
  async def gehackt(self, ctx):
    await ctx.send(':boom: GESPRENGT :boom:')
  
  @commands.command()
  @commands.guild_only()
  async def billig(self, ctx):
    await ctx.send('Billig? Ja.\nMisstrauisch? Ja.\nBerechtigt? Ja')

  @commands.command()
  @commands.guild_only()
  async def rip(self, ctx, *, arg):
    embedRip = discord.Embed()
    embedRip.colour = discord.Colour.from_rgb(0, 0, 0)
    embedRip.title = f':pray: :coffin: :pray:   RIP {arg}   :pray: :coffin: :pray:'
    embedRip.set_image(url = 'https://media.tenor.com/images/29ed9c8ea3a979f3628c23a13ea9366a/tenor.gif')
    await ctx.send(embed = embedRip)

  # Marblelympics commands
  @commands.command()
  @commands.guild_only()
  async def ducks(self, ctx):
    await ctx.send('<:gd_marble:571396561045684224> <:ducks:571352498590318592> <:gd_marble:571396561045684224> **#QUACKATTACK** <:gd_marble:571396561045684224> <:ducks:571352498590318592> <:gd_marble:571396561045684224>')

  @commands.command()
  @commands.guild_only()
  async def my(self, ctx):
    await ctx.send('<:my:573452977726029835> #KEEPITMELLOW <:my:573452977726029835>')

  @commands.command()
  @commands.guild_only()
  async def ss(self, ctx):
    await ctx.send('<:ss_marble:571398818378285071> <:ss:571396511204900881> :100: :fire: :massage: #SPEEDISKEY :massage: :fire: :100: <:ss:571396511204900881> <:ss_marble:571398818378285071>')
  
  @commands.command()
  @commands.guild_only()
  async def tg(self, ctx):
    await ctx.send('<:galacticballs:572766585593266206><:galactic2:572764693203124224>#ReachForTheStars<:galactic2:572764693203124224><:galacticballs:572766585593266206>')
    
  # Good bot, bad bot, thx bot
  @commands.Cog.listener()
  async def on_message(self, message):
    if message.author == self.client.user or message.author.bot or message.channel.type == "private":
        return
    
    if 'good bot' in message.content.lower():
      await message.channel.send(':smiling_face_with_3_hearts:')
    elif 'bad bot' in message.content.lower():
      await message.channel.send(':F')
    elif 'thx bot' in message.content.lower():
      await message.channel.send('<a:meh:563687194351501340>')
    elif 'conan' in message.content.lower():
      await message.channel.send('https://youtube.com/watch?v=Oo9buo9Mtos')
    elif 'antrag' in message.content.lower() and not 'antrag abgelehnt' in message.content.lower():
      await message.channel.send('Antrag ... abgelehnt! ❌')


def setup(client):
    client.add_cog(fun(client))