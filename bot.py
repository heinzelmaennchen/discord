import discord
import asyncio
import os
import requests
from discord.ext import commands
from discord.ext.commands import Bot

client = discord.Client()

api_key = os.environ['API_KEY']

@client.event
async def on_ready():
  print('Logged in as')
  print(client.user.name)
  print(discord.__version__)
  print(client.user.id)
  print('Let\'s go!')

@client.event
async def on_message(message):

  response = False
  globalStats = False
  toplist = False

  if message.content.startswith('€zk'):
    response = getEzkValue()
  elif message.content.startswith('$'):
    coin = message.content[1:].upper().strip(' ,')
    response = getCurrentValues(coin, globalStats)
  elif message.content == '!top':
    globalStats = True
    """ Hier die coins für !top eintragen """
    coin = 'BTC,ETH,XTZ,XLM,XMR,LSK,SAN'
    response = getCurrentValues(coin, globalStats)
  elif message.content == '!topvol':
    response = getTopVolume()
  elif message.content.startswith('!buffet'):
    response = 'https://imgur.com/02Bxkye'
  elif message.content.startswith('!rip'):
    response = ':meat_on_bone: :meat_on_bone: :meat_on_bone:'
  elif message.content.startswith('!moon'):
    response = ':rocket: :full_moon:'
  elif message.content.startswith('!earth'):
    response = ':airplane_arriving: :earth_africa:'

  if response:
    channel = message.channel
    await channel.send(response)

def getCurrentValues(coin, globalStats):
  """Grab current values for a coin from Coinlib."""
  apiRequestCoins = requests.get(
    'https://coinlib.io/api/v1/coin?key=' + api_key + '&pref=EUR&symbol='
    + coin).json()
  
  """Grab global stats if requested."""
  if globalStats:
    apiRequestGlobal = requests.get(
    'https://coinlib.io/api/v1/global?key=' + api_key + '&pref=EUR'
    ).json()
    
    totalMarketCap = str(round(float(apiRequestGlobal['total_market_cap']) / 10**9,1))
    totalVolume = str(round(float(apiRequestGlobal['total_volume_24h']) / 10**9,1))
    """This only works as long as BTC is the first coin in the response."""
    btcDominance = '{0:.2f}%'.format(
      float(apiRequestCoins['coins'][0]['market_cap'])/
      float(apiRequestGlobal['total_market_cap']) * 100)

  """Create and initiate lists for coins, values and %change."""
  coins = coin.split(',')
  values = []
  change_24h = []
  change_7d = []
  change_30d = []
  """Build response."""
  for num, coin in enumerate(coins, start=0):
    try:
      if len(coins) > 1:
        coinStats = apiRequestCoins['coins'][num]
      else:
        coinStats = apiRequestCoins
      """Build arrays."""
      values.append('%.2f' % round(float(coinStats['price']),2))
      change_24h.append('%.2f' % round(float(coinStats['delta_24h']),2))
      change_7d.append('%.2f' % round(float(coinStats['delta_7d']),2))
      change_30d.append('%.2f' % round(float(coinStats['delta_30d']),2))
    except KeyError:
      r = ('Heast du elelelendige Scheißkreatur, schau amoi wos du für an'
           + ' Bledsinn gschrieben host. Oida!')
      return r

  """Dynamic indent width."""
  coinwidth = len(max(coins, key=len))
  valuewidth = len(max(values, key=len))
  changewidth_24h = len(max(change_24h, key=len))
  changewidth_7d = len(max(change_7d, key=len))
  changewidth_30d = len(max(change_30d, key=len))

  r = '```\n'
  for x in coins:
    r += ((coins[coins.index(x)]).rjust(coinwidth) + ': '
          + (values[coins.index(x)]).rjust(valuewidth) + ' EUR | '
          + (change_24h[coins.index(x)]).rjust(changewidth_24h) + '% | '
          + (change_7d[coins.index(x)]).rjust(changewidth_7d) + '% | '
          + (change_30d[coins.index(x)]).rjust(changewidth_30d) + '%\n')
  if globalStats:  
    r += ('\nMarket Cap: ' + totalMarketCap + ' Mrd. EUR')
    r += ('\nVolume 24h: ' + totalVolume + ' Mrd. EUR')
    r += ('\nBTC dominance: ' + btcDominance)
  r += '```'
  return r

def getEzkValue():

  amountBTC = 0.0280071
  amountETH = 0.38042397
  apiRequest = \
    requests.get('https://coinlib.io/api/v1/coin?key=' + api_key + '&pref=EUR&symbol='
                 + 'BTC,ETH').json()
  valueBTC = float(apiRequest['coins'][0]['price'])
  valueETH = float(apiRequest['coins'][1]['price'])
  value = round(amountBTC * valueBTC + amountETH * valueETH,2)
  r = '```'
  r += '€zk: ' + str(value) + ' EUR | ' + '{:+}%'.format(round((value/220-1)*100,2))
  r += '```'
  return r

client.run(os.environ['BOT_TOKEN'])
