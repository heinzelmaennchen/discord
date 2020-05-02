import discord
from discord.ext import commands
import random

class utility(commands.Cog):

  def __init__(self, client):
    self.client = client

  @commands.command()
  async def asdf(self, ctx):
    await ctx.send('@everyone Verachtung!!! Guade lupe uiuiui')
  
  @commands.command()
  async def calc(self, ctx, *, calcString):
    result = self.doCalculate(calcString)
    if result:
      await ctx.send(result)

  @commands.command(aliases=['rand', 'dice', 'roll'])
  async def random(self, ctx, *arg):
    '''Gibt eine zufällige Zahl oder Member aus
    Benutzung:
    -----------
    !random
        Gibt eine zufällige Zahl zwischen 1 und 100 aus
    !random coin
        Wirft eine Münze (Kopf oder Zahl)
    !random 6
        Gibt eine zufällige Zahl zwischen 1 und 6 aus
    !random 10 20
        Gibt eine zufällige Zahl zwischen 10 und 20 aus
    '''
    if ctx.invoked_subcommand is None:
      if not arg:
        start = 1
        end = 100
      elif arg[0] == 'flip' or arg[0] == 'coin':
        coin = ['Kopf', 'Zahl']
        await ctx.send(':arrows_counterclockwise: {0}'.format(random.choice(coin)))
        return
      elif len(arg) == 1:
        start = 1
        end = int(arg[0])
      elif len(arg) > 1:
        start = int(arg[0])
        end = int(arg[1])
      await ctx.send('**:arrows_counterclockwise:** Zufällige Zahl ({0} - {1}): {2}'.format(start, end, random.randint(start, end)))

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

def setup(client):
  client.add_cog(utility(client))