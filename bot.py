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

  response = False
  globalStats = False

  if message.content.startswith('€zk'):
    response = getEzkValue()
  elif message.content.startswith('$'):
    coin = message.content[1:].upper().strip(' ,')
    response = getCurrentValues(coin, globalStats)
  elif message.content == '!top':
    globalStats = True
    """ Hier die coins für !top eintragen """
    coin = 'BTC,ETH,ICN,XLM,XMR,LSK,SAN'
    response = getCurrentValues(coin, globalStats)
  elif message.content == '!topvol':
    response = getTopVolume()
  elif message.content.startswith('!buffet'):
    response = 'https://imgur.com/02Bxkye'
  elif message.content.startswith('!rip'):
    response = ':meat_on_bone: :meat_on_bone: :meat_on_bone:'
  elif message.content.startswith('!moon'):
    response = ':rocket: :full_moon:'

  if response:
    await client.send_message(message.channel, response)

def getCurrentValues(coin, globalStats):
  """Grab current values for a coin from Cryptocompare."""
  apiRequestCoins = requests.get(
    'https://min-api.cryptocompare.com/data/pricemultifull?fsyms='
    + coin +
    '&tsyms=EUR').json()

  apiRequestGlobal = requests.get(
      'https://api.coinmarketcap.com/v1/global/?convert=EUR'
  ).json()
  
  totalMarketCapEUR = str(round(apiRequestGlobal['total_market_cap_eur'] / 10**9,1))
  totalVolumeEUR = str(round(apiRequestGlobal['total_24h_volume_eur'] / 10**9,1))
  btcDominance = str(apiRequestGlobal['bitcoin_percentage_of_market_cap'])

  """Create and initiate lists for coins, values and %change"""
  coins = coin.split(',')
  values = []
  change = []
  """Build response"""
  for x in coins:
    try:
      coinStats = apiRequestCoins['RAW'][x]['EUR']
    except KeyError:
      r = ('Heast du elelelendige Scheißkreatur, schau amoi wos du für an'
           + ' Bledsinn gschrieben host. Oida!')
      return r

    """Build arrays"""
    values.append('%.2f' % round(coinStats['PRICE'],2))
    change.append('%.2f' % round(coinStats['CHANGEPCT24HOUR'],2))

  """Dynamic indent width"""
  coinwidth = len(max(coins, key=len))
  valuewidth = len(max(values, key=len))
  changewidth = len(max(change, key=len))

  r = '```\n'
  for x in coins:
    r += ((coins[coins.index(x)]).rjust(coinwidth) + ': '
          + (values[coins.index(x)]).rjust(valuewidth) + ' EUR | '
          + (change[coins.index(x)]).rjust(changewidth) + '%\n')
  if globalStats:  
    r += ('\nMarket Cap: ' + totalMarketCapEUR + ' Mrd. EUR')
    r += ('\nVolume 24h: ' + totalVolumeEUR + ' Mrd. EUR')
    r += ('\nBTC dominance: ' + btcDominance + ' %')
  r += '```'
  return r

def getEzkValue():

  amountBTC = 0.0280071
  amountETH = 0.38042397
  apiRequest = \
    requests.get('https://min-api.cryptocompare.com/data/pricemulti?fsyms='
                 + 'BTC,ETH&tsyms=EUR').json()
  valueBTC = float(apiRequest['BTC']['EUR'])
  valueETH = float(apiRequest['ETH']['EUR'])
  value = round(amountBTC * valueBTC + amountETH * valueETH,2)
  r = '```'
  r += '€zk: ' + str(value) + ' EUR | ' + '{:+}%'.format(round((value/220-1)*100,2))
  r += '```'
  return r

client.run(os.environ['BOT_TOKEN'])
