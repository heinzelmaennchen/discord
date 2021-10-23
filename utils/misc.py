import discord
import os
from datetime import datetime
from pytz import timezone

DISCORD_EPOCH = 1420070400000
MAX_MESSAGE_LENGTH = 1980


def getMessageTime(snowflake):
    ms = (snowflake >> 22) + DISCORD_EPOCH
    time = datetime.fromtimestamp(ms / 1000, timezone('Europe/Vienna'))
    return time


def getNick(user):
    if user.nick == False:
        name = user.name
    else:
        name = user.nick
    return name


def isDevServer(ctx):
    if ctx.guild.id == 405433814114893835:
        return True
    else:
        return False


async def sendLongMsg(channel, response):
    # Embeds haben max size von 6000 > wird bei uns nie vorkommen
    # Won't check - infeasible
    if type(response) == discord.embeds.Embed:
        await channel.send(embed=response)
        return

    responses = msgSplitter(response)
    for response in responses:
        await channel.send(response)


def msgSplitter(response):
    responses = []
    addCb = False
    while len(response) > MAX_MESSAGE_LENGTH:
        splitindex = response.rfind('\n', 0, MAX_MESSAGE_LENGTH)
        if splitindex == -1:
            splitindex = response.rfind(' ', 0, MAX_MESSAGE_LENGTH)

        responses.append(response[:splitindex])
        if addCb == True:
            responses[-1] = f'```{responses[-1]}'
            addCb = False
        if responses[-1].count('```') % 2 != 0:
            responses[-1] += '```'
            addCb = True
        response = response[splitindex + 1:]
    responses.append(response)
    if addCb == True:
        responses[-1] = f'```{responses[-1]}'
        addCb = False
    return responses