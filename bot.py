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
  """ Hier die coins für !top und !topBTC eintragen. """
  ourCoins = os.environ['OUR_COINS']
  global gurkerl_string
  gurkerl_string = ':cucumber: :cucumber: :cucumber:'
  global moon_string
  moon_string = ':full_moon: :full_moon: :full_moon:'
  global ripperl_string
  ripperl_string = ':meat_on_bone: :meat_on_bone: :meat_on_bone:'
  
  if message.content.startswith('€zk'):
    response = getEzkValue()
  elif message.content.startswith('$'):
    coin = message.content[1:].upper().strip(' ,')
    response = getCurrentValues(coin)
  elif message.content == '!top':
    globalStats = True
    response = getCurrentValues(ourCoins, globalStats)
  elif message.content == '!topBTC':
    response = getCurrentValues(ourCoins, currency = 'BTC')
  elif message.content == '!topten':
    coins = getTopTenCoins()
    response = getCurrentValues(coins)
  elif message.content == '!toptenBTC':
    coins = getTopTenCoins()
    response = getCurrentValues(coins, currency = 'BTC')
  elif message.content.startswith('!buffet'):
    response = 'https://imgur.com/02Bxkye'
  elif message.content.startswith('!calc '):
    calcStr = message.content.split(' ', 1)
    response = doCalculate(calcStr[1])
  elif message.content.startswith('!earth'):
    response = ':airplane_arriving: :earth_africa:'
  elif message.content.startswith('!gurkerl'):
    response = gurkerl_string
  elif message.content.startswith('!moon'):
    response = moon_string
  elif message.content.startswith('!pray'):
    response = ':pray: :pray: :pray: :pray: :pray:'
  elif message.content.startswith('!rip'):
    response = ripperl_string

  if response:
    channel = message.channel
    await channel.send(response)

def getCurrentValues(coin, globalStats = False, currency = 'EUR'):
    
  """Grab current values for a coin from Coinlib."""
  apiRequestCoins = requests.get(
    'https://coinlib.io/api/v1/coin?key=' + api_key + '&pref=' + currency + '&symbol='
    + coin)
  if apiRequestCoins.history:
    print('Request was redirected')
    for resp in apiRequestCoins.history:
        print(resp.url)
        print(resp.status_code)
        print(resp.headers['Set-Cookie'])
        headerCookie = str(resp.headers['Set-Cookie'])
        sessionIDstart = headerCookie.find('SESSIONID=')
        sessionIDend = headerCookie.find(';', 151)
        sessionID = headerCookie[sessionIDstart:sessionIDend]
        print(sessionID)
  apiRequestCoins = apiRequestCoins.json()
  
  """Inititalize rating variable."""
  rating = ''
  
  """Grab global stats if requested."""
  if globalStats:
    apiRequestGlobal = requests.get(
    'https://coinlib.io/api/v1/global?key=' + api_key + '&pref=EUR'
    ).json()
    
    totalMarketCap = str(round(float(apiRequestGlobal['total_market_cap']) / 10**9,1))
    totalVolume = str(round(float(apiRequestGlobal['total_volume_24h']) / 10**9,1))
    """Calculate the rating for emoji madness."""
    rating_24h = calculateRating(round(float(apiRequestCoins['coins'][0]['delta_24h']),2))
    rating_7d = calculateRating(round(float(apiRequestCoins['coins'][0]['delta_7d']),2))
    rating_30d = calculateRating(round(float(apiRequestCoins['coins'][0]['delta_30d']),2))
    """This only works as long as BTC is the first coin in the response."""
    btcDominance = '{0:.2f}%'.format(
      float(apiRequestCoins['coins'][0]['market_cap'])/
      float(apiRequestGlobal['total_market_cap']) * 100)

  """Create and initiate lists for coins, values, %change and rating."""
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
          + (values[coins.index(x)]).rjust(valuewidth) + ' ' + currency + ' | '
          + (change_24h[coins.index(x)]).rjust(changewidth_24h) + '% | '
          + (change_7d[coins.index(x)]).rjust(changewidth_7d) + '% | '
          + (change_30d[coins.index(x)]).rjust(changewidth_30d) + '%\n')
  if globalStats:  
    r += ('\nMarket Cap: ' + totalMarketCap + ' Mrd. EUR')
    r += ('\nVolume 24h: ' + totalVolume + ' Mrd. EUR')
    r += ('\nBTC dominance: ' + btcDominance)
    r += '```'
    r += rating_24h + ' ' + rating_7d + ' ' + rating_30d 
  else:
    r += '```'
  return r

def getEzkValue():
  amountBTC = float(os.environ['AMOUNT_BTC'])
  amountETH = float(os.environ['AMOUNT_ETH'])
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

def getTopTenCoins():
  topTenList = requests.get(
    'https://coinlib.io/api/v1/coinlist?key=' + api_key + '&pref=EUR&page=1&order=rank_asc'
    ).json()
  
  topTenCoins = []
  for i in range(10):
    topTenCoins.append(topTenList['coins'][i]['symbol'])
    
  return ', '.join(topTenCoins)

def doCalculate(calcStr):
  try:
    result = eval(calcStr, {'__builtins__': None})
    if result % 1 == 0:
      r = int(result)
    else:
      r = float(result)
  except:
    r = False
  return r

def calculateRating(change):
  if change < -5:
    rating = ripperl_string
  elif change > 5:
    rating = moon_string
  else:
    rating = gurkerl_string
  return rating

client.run(os.environ['BOT_TOKEN'])
