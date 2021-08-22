import discord
import os
import requests
import random
import re
import json

from discord.ext import commands, tasks
from discord.ext.commands import Bot
from dotenv import load_dotenv

from config.cogs import __cogs__
from config.botactivity import __activities__, __activityTimer__

load_dotenv()

client = commands.Bot(command_prefix='!')
taskDict = {
}  # used in cog 'skills' for saving the Timer Tasks, but saved in main, if cog gets reloaded


@client.event
async def on_ready():
    print(f'Logged in as {client.user.name}')
    print(f'Discord version: {discord.__version__}')
    print('Loading cogs...')
    for cog in __cogs__:
        try:
            client.load_extension(cog)
            print(f'{cog} loaded')
        except Exception as e:
            print(f'Couldn\'t load cog {cog}: {e}')
    print('Loading cogs finished')
    initTimerJSON()
    from cogs.timers import restartTimersOnBoot
    await restartTimersOnBoot(client)
    change_status.start()
    print('Let\'s go!')


# Loops through different activities as defined in config.botactivity.py
@tasks.loop(seconds=__activityTimer__)
async def change_status():
    rndStatus = random.choice(__activities__)
    await client.change_presence(
        activity=discord.Activity(type=rndStatus[0], name=rndStatus[1]))


# Reload a specific cog
@client.command(hidden=True)
async def reload(ctx, extension):
    client.unload_extension(f'cogs.{extension}')
    client.load_extension(f'cogs.{extension}')


# Load a specific cog that hasn't been loaded
@client.command(hidden=True)
async def load(ctx, extension):
    client.load_extension(f'cogs.{extension}')


# Invalid command
@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        ignorePattern = r"^!{2,7}$"  # 2-7 Rufzeichen erlaubt
        if re.match(ignorePattern, ctx.message.content):
            return
        else:
            await ctx.message.add_reaction('🥚')
            await ctx.message.add_reaction('👏')
    else:
        print(error)


# Initiate the file that timers are stored in
def initTimerJSON():
    try:
        with open('storage/timer.json') as json_file:
            jsonTimerData = json.load(json_file)

        if "counter" in jsonTimerData and "timers" in jsonTimerData:
            print('Checking timer.json ... OK')
            return
        else:
            raise FileNotFoundError

    except FileNotFoundError:
        print(
            'Checking timer.json ... something wrong > Initializing timer.json'
        )
        newTimerJSON = {"counter": 0, "timers": {}}
        try:
            with open('storage/timer.json', 'w') as json_file:
                json.dump(newTimerJSON,
                          json_file,
                          indent=4,
                          ensure_ascii=False)
        except IOError:
            print('timer.json not accessable')


if __name__ == '__main__':
    try:
        client.run(os.environ['BOT_TOKEN'])
    finally:
        print("Shutting down ...")
