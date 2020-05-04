import discord
import os
import requests
import random

from discord.ext import commands, tasks
from discord.ext.commands import Bot
from dotenv import load_dotenv

from config.cogs import __cogs__
from config.botactivity import __activities__, __activityTimer__

load_dotenv()

client = commands.Bot(command_prefix = '!')
api_key = os.environ['API_KEY']

@client.event
async def on_ready():
  print('Logged in as')
  print(client.user.name)
  print(discord.__version__)
  print(client.user.id)
  print('Loading cogs...')
  for cog in __cogs__:
        try:
            client.load_extension(cog)
            print(f'{cog} loaded')
        except Exception:
            print(f'Couldn\'t load cog {cog}')
  print('Loading cogs finished')
  print('Let\'s go!')
  change_status.start()

@tasks.loop(seconds = __activityTimer__)
async def change_status():
  rndStatus = random.choice(__activities__)
  await client.change_presence(activity=discord.Activity(type=rndStatus[0], name=rndStatus[1]))

@client.command(hidden = 'True')
async def reload(ctx, extension):
  client.unload_extension(f'cogs.{extension}')
  client.load_extension(f'cogs.{extension}')

if __name__ == '__main__':
  client.run(os.environ['BOT_TOKEN'])