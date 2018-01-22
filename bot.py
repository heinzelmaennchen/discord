import discord
import asyncio
import os
import requests
from discord.ext import commands
from discord.ext.commands import Bot

client = discord.Client()

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('Let\'s go!')

@client.event
async def on_message(message):
    if message.content.startswith('!ping'):
        await client.send_message(message.channel, 'Pong!')
    elif message.content.startswith('$'):
        coin = string.upper(message.content[1:5])
        coinStats = getCurrentValues(coin)
        response = buildResponse(coinStats, coin)
        await client.send_message(message.channel, response)
    
def getCurrentValues(coin):
    """Grabs current values for a coin from Cryptocompare."""
    apiRequest = requests.get(
        'https://min-api.cryptocompare.com/data/pricemultifull?fsyms=' 
        + coin + 
        '&tsyms=EUR').json()
    values = apiRequest['RAW'][coin]['EUR']
    return values

def buildResponse(coinStats, coin):
    """Builds response string which will be printed to the channel."""
    r = ('**' + coin + ':** ' + str(coinStats['PRICE']) + ' EUR (' + 
         str(round(coinStats['CHANGEPCT24HOUR'],2)) + '%)\n')
    return r

client.run(os.environ['BOT_TOKEN'])
