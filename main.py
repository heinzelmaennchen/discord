import discord
import os
import random
import re
import json
import ast

from discord.ext import commands, tasks
from discord.ext.commands import Bot
from dotenv import load_dotenv

from config.cogs import __cogs__
from config.botactivity import __activities__, __activityTimer__

load_dotenv()
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

client = commands.Bot(command_prefix='!', intents = intents)
taskDict = {
}  # used in cog 'skills' for saving the Timer Tasks, but saved in main, if cog gets reloaded


@client.event
async def on_ready():
    print(f'Logged in as {client.user.name}')
    print(f'Discord version: {discord.__version__}')
    print('Loading cogs...')
    for cog in __cogs__:
        try:
            await client.load_extension(cog)
            print(f'{cog} loaded')
        except Exception as e:
            print(f'Couldn\'t load cog {cog}: {e}')
            await client.get_channel(int(os.environ['BOTTEST'])).send(f'Couldn\'t load cog {cog}: {e}')   
    print('Loading cogs finished')
    initTimerJSON()
    from cogs.timers import restartTimersOnBoot
    await restartTimersOnBoot(client)
    if not change_status.is_running():
        change_status.start()
    print('Let\'s go!')
    await client.get_channel(int(os.environ['BOTTEST'])).send('`' + os.environ['GUILD_IDS'] + '`')
    await client.get_channel(int(os.environ['BOTTEST'])).send('```' + ast.literal_eval(os.environ['GUILD_IDS']) + '\n' + type(ast.literal_eval(os.environ['GUILD_IDS'])) + '```')


# Loops through different activities as defined in config.botactivity.py
@tasks.loop(seconds=__activityTimer__)
async def change_status():
    rndStatus = random.choice(__activities__)
    await client.change_presence(
        activity=discord.Activity(type=rndStatus[0], name=rndStatus[1]))


# Reload a specific cog
@client.command(hidden=True)
async def reload(ctx, extension):
    try:
        await client.unload_extension(f'cogs.{extension}')
        print(f'{extension} unloaded')
    except Exception as e:
        print(f'Couldn\'t unload cog {extension}: {e}')
    try:
        await client.load_extension(f'cogs.{extension}')
        print(f'{extension} loaded')
    except Exception as e:
        print(f'Couldn\'t load cog {extension}: {e}')


# Load a specific cog that hasn't been loaded
@client.command(hidden=True)
async def load(ctx, extension):
    try:
        await client.load_extension(f'cogs.{extension}')
        print(f'{extension} loaded')
    except Exception as e:
        print(f'Couldn\'t load cog {extension}: {e}')


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
    elif isinstance(error, commands.CheckFailure):
        # CheckFailure error codes (see utils/misc.py)
        # '1': no dev permissions
        # '2': wrong channel
        if error.args[0] == '1':
            await ctx.send('🚫 keine Dev Berechtigung')
            await ctx.message.add_reaction('🚫')
        elif error.args[0] == '2':
            await ctx.send('🚫 not in this channel, oida!')
            await ctx.message.add_reaction('🚫')
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
