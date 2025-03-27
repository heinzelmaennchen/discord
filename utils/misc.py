import discord
from discord.ext import commands
import os
from datetime import datetime
from pytz import timezone

DISCORD_EPOCH = 1420070400000
MAX_MESSAGE_LENGTH = 1980

devs = list(map(int, os.environ['DEVS'].split(",")))


def getMessageTime(snowflake):
    ms = (snowflake >> 22) + DISCORD_EPOCH
    time = datetime.fromtimestamp(ms / 1000, timezone('Europe/Vienna'))
    return time

def isleap(year):
    """Return True for leap years, False for non-leap years."""
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

def getNick(user):
    if user.nick is not None:
        name = user.nick
    else:
        name = user.name
    return name

def msgSplitter(response):
    responses = []
    addCb = False
    while len(response) > MAX_MESSAGE_LENGTH:
        splitindex = response.rfind('\n', 0, MAX_MESSAGE_LENGTH)
        if splitindex == -1:
            splitindex = response.rfind(' ', 0, MAX_MESSAGE_LENGTH)

        responses.append(response[:splitindex])
        if addCb == True:
            responses[-1] = f'```\n{responses[-1]}'
            addCb = False
        if responses[-1].count('```') % 2 != 0:
            responses[-1] += '```'
            addCb = True
        response = response[splitindex + 1:]
    responses.append(response)
    if addCb == True:
        responses[-1] = f'```\n{responses[-1]}'
        addCb = False
    return responses

async def sendLongMsg(channel, response):
    # Embeds haben max size von 6000 > wird bei uns nie vorkommen
    # Won't check - infeasible
    if type(response) == discord.embeds.Embed:
        await channel.send(embed=response)
        return

    responses = msgSplitter(response)
    for response in responses:
        await channel.send(response)

# Custom Checks
# CheckFailure argument codes. Codes are handled in main.py in the on_command_error section:
# '1': no dev permissions
# '2': wrong channel

def isDevServer(ctx):
    if ctx.guild.id == 405433814114893835:
        return True
    else:
        return False

def isDev(ctx):
    if ctx.author.id in devs:
        return True
    else:
        raise commands.CheckFailure('1')
        
def isCryptoChannel(ctx):
    if ctx.channel.id == 351724430306574357 or isDevServer(ctx):
        return True
    else:
        raise commands.CheckFailure('2')