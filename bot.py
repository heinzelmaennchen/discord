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
		coin = message.content[1:].upper().strip(' ,')
		response = getCurrentValues(coin)
		await client.send_message(message.channel, response)
    
def getCurrentValues(coin):
	"""Grabs current values for a coin from Cryptocompare."""
	apiRequest = requests.get(
		'https://min-api.cryptocompare.com/data/pricemultifull?fsyms=' 
		+ coin + 
		'&tsyms=EUR').json()
    
	"""Creating and initiating lists for coins, values and %change"""
	coins = coin.split(',')
	values = []
	change = []
	"""Building response"""
	r = '```\n'
	for x in coins:
		try:
			coinStats = apiRequest['RAW'][x]['EUR']
		except KeyError:
			r = 'Heast du elelelendige Scheißkreatur, schau amoi wos du für an Bledsinn gschrieben host.'
			return r            
		values.append(coinStats['PRICE'])
		change.append(round(coinStats['CHANGEPCT24HOUR'],2))
		
		i = len(values)-1
		r += coins[i] + ': ' + str(values[i]) + ' EUR (' + str(change[i]) + '%)\n'
		
	r += '```'
	return r

client.run(os.environ['BOT_TOKEN'])
