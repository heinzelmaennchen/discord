import discord
from discord.ext import commands

class fun(commands.Cog):

  def __init__(self, client):
    self.client = client

  @commands.command()
  async def richtig(self, ctx):
    await ctx.send('richtig richtig richtfest!')
  
  @commands.command()
  async def falsch(self, ctx):
    await ctx.send('falsch falsch Falschgeld!')

  @commands.command()
  async def twss(self, ctx):
    await ctx.send('That\'s what she said.')
  
  @commands.command()
  async def läuft(self, ctx):
    await ctx.send('läuft\nläuft\nlohnt')

  @commands.command()
  async def gehackt(self, ctx):
    await ctx.send(':boom: GESPRENGT :boom:')
  
  @commands.command()
  async def billig(self, ctx):
    await ctx.send('Billig? Ja.\nMisstrauisch? Ja.\nBerechtigt? Ja')

  @commands.command()
  async def rip(self, ctx, *, arg):
    embedRip = discord.Embed()
    embedRip.colour = discord.Colour.from_rgb(0, 0, 0)
    embedRip.title = f':pray: :coffin: :pray:   RIP {arg}   :pray: :coffin: :pray:'
    embedRip.set_image(url = 'https://media.tenor.com/images/29ed9c8ea3a979f3628c23a13ea9366a/tenor.gif')
    await ctx.send(embed = embedRip)

  # Marblelympics commands
  @commands.command()
  async def ducks(self, ctx):
    await ctx.send('<:gd_marble:571396561045684224> <:ducks:571352498590318592> <:gd_marble:571396561045684224> **#QUACKATTACK** <:gd_marble:571396561045684224> <:ducks:571352498590318592> <:gd_marble:571396561045684224>')

  @commands.command()
  async def my(self, ctx):
    await ctx.send('<:my:573452977726029835> #KEEPITMELLOW <:my:573452977726029835>')

  @commands.command()
  async def ss(self, ctx):
    await ctx.send('<:ss_marble:571398818378285071> <:ss:571396511204900881> :100: :fire: :massage: #SPEEDISKEY :massage: :fire: :100: <:ss:571396511204900881> <:ss_marble:571398818378285071>')
  
  @commands.command()
  async def tg(self, ctx):
    await ctx.send('<:galacticballs:572766585593266206><:galactic2:572764693203124224>#ReachForTheStars<:galactic2:572764693203124224><:galacticballs:572766585593266206>')
    
def setup(client):
    client.add_cog(fun(client))