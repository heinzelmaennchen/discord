import discord
import os
import requests

from discord.ext import commands
from discord.ext.commands import Bot
from dotenv import load_dotenv
from config.cogs import __cogs__

load_dotenv()

client = commands.Bot(command_prefix = '!')

api_key = os.environ['API_KEY']

@client.event
async def on_ready():
  print('Logged in as')
  print(client.user.name)
  print(discord.__version__)
  print(client.user.id)
  await client.change_presence(activity=discord.Game('with Cryptos'))
  print('Loading cogs...')
  for cog in __cogs__:
        try:
            client.load_extension(cog)
            print(f'{cog} loaded')
        except Exception:
            print(f'Couldn\'t load cog {cog}')
  print('Loading cogs finished')
  print('Let\'s go!')

@client.command(hidden = 'True')
async def reload(ctx, extension):
  client.unload_extension(f'cogs.{extension}')
  client.load_extension(f'cogs.{extension}')

if __name__ == '__main__':
  client.run(os.environ['BOT_TOKEN'])