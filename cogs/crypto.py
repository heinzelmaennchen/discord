import discord
from discord.ext import commands
import aiohttp
import os
import requests
from utils.db import check_connection
from utils.db import init_db
from datetime import date

class crypto(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.moon_string = ':full_moon: :full_moon: :full_moon:'
        self.gurkerl_string = ':cucumber: :cucumber: :cucumber:'
        self.ripperl_string = ':meat_on_bone: :meat_on_bone: :meat_on_bone:'
        self.ourCoins = os.environ['OUR_COINS']
        self.api_key = os.environ['API_KEY']
        self.cnx = init_db()
        
    # Use on_message if command isn't possible
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.client.user or message.author.bot or message.channel.type == "private":
            return

        if message.content.startswith('$'):
            if message.content.startswith('$ratio'):
                coin = message.content[7:].upper().strip(' ,')
                await self.checkChannelAndSend(
                    message, self.getCurrentValues(coin, currency='BTC'))
            else:
                coin = message.content[1:].upper().strip(' ,')
                await self.checkChannelAndSend(message,
                                               self.getCurrentValues(coin))
        elif message.content == '€zk':
            await self.checkChannelAndSend(message, self.getEzkValue())

    # Fun crypto commands
    @commands.command()
    @commands.guild_only()
    async def moon(self, ctx):
        await ctx.send(self.moon_string)

    @commands.command()
    @commands.guild_only()
    async def gurkerl(self, ctx):
        await ctx.send(self.gurkerl_string)

    @commands.command()
    @commands.guild_only()
    async def ripperl(self, ctx):
        await ctx.send(self.ripperl_string)

    @commands.command()
    @commands.guild_only()
    async def earth(self, ctx):
        await ctx.send(':airplane_arriving: :earth_africa:')

    @commands.command()
    @commands.guild_only()
    async def pray(self, ctx):
        await ctx.send(':pray: :pray: :pray: :pray: :pray:')

    @commands.command(aliases=['buffett'])
    @commands.guild_only()
    async def buffet(self, ctx):
        await self.checkChannelAndSend(ctx.message,
                                       'https://imgur.com/02Bxkye')

    # Real crypto commands
    @commands.command()
    @commands.guild_only()
    async def top(self, ctx):
        globalStats = True
        print('in top')
        await self.checkChannelAndSend(
            ctx.message, await self.getCurrentValues(self.ourCoins, globalStats))

    @commands.command(aliases=['topbtc', 'topBtc'])
    @commands.guild_only()
    async def topBTC(self, ctx):
        # Slice away 'BTC,' since cryptocompare can't do a BTC/BTC comparison.
        coins = self.ourCoins[4:]
        await self.checkChannelAndSend(
            ctx.message, self.getCurrentValues(coins, currency='BTC'))

    @commands.command(aliases=['top10'])
    @commands.guild_only()
    async def topten(self, ctx):
        coins = self.getTopTenCoins()
        await self.checkChannelAndSend(ctx.message,
                                       self.getCurrentValues(coins))

    @commands.command(
        aliases=['toptenbtc', 'toptenBtc', 'top10BTC', 'top10Btc', 'top10btc'])
    @commands.guild_only()
    async def toptenBTC(self, ctx):
        coins = self.getTopTenCoins(True)
        await self.checkChannelAndSend(
            ctx.message, self.getCurrentValues(coins, currency='BTC'))

    @commands.command()
    @commands.guild_only()
    async def history(self, ctx):
        await self.checkChannelAndSend(
            ctx.message, self.getHistoricalPrices())
                             
    # Crypto helper functions
    async def getCurrentValues(self, coinList, globalStats=False, currency='EUR'):
        # Grab current values for a coin from Cryptocompare.
        async with aiohttp.ClientSession() as session:
            async with session.get('https://min-api.cryptocompare.com/data/pricemultifull?fsyms=' +
                                   coinList + '&tsyms=' + currency + '&api_key=' +
                                   self.api_key) as r:
                if r.status == 200:
                    apiRequestCoins = await r.json()
                else: print(r.status)

        # Grab global stats if requested.
        if globalStats:

            async with aiohttp.ClientSession() as session:
                print('in session globalstats')
                async with session.get('https://api.coingecko.com/api/v3/global') as r:
                    print(r)
                    if r.status == 200:
                        apiRequestGlobal = await r.json()['data']
                    else: print(r.status)

            totalMarketCap = str(
                round(
                    float(apiRequestGlobal['total_market_cap']['eur']) / 10**9,
                    1))
            totalVolume = str(
                round(
                    float(apiRequestGlobal['total_volume']['eur']) / 10**9, 1))
            btcDominance = str(
                round(float(apiRequestGlobal['market_cap_percentage']['btc']),
                      1))

        # Create and initiate lists for coins, values, %change and rating.
        coins = coinList.split(',')
        values = []
        change_24h = []
        change_7d = []
        change_30d = []

        # Define floating point precision for price.
        if currency == 'BTC':
            precision = 5
        else:
            precision = 2

        # Build response.
        for coin in coins:
            try:
                # Add price and 24h to the dictionary.
                values.append('%.{}f'.format(precision) % round(
                    float(apiRequestCoins['RAW'][coin][currency]['PRICE']),
                    precision))
                change_24h.append('%.1f' % round(
                    float(apiRequestCoins['RAW'][coin][currency]
                          ['CHANGEPCT24HOUR']), 2))

                # Get historical values for this coin and calculate change.
                async with aiohttp.ClientSession() as session:
                    async with session.get('https://min-api.cryptocompare.com/data/v2/histoday?fsym='
                                   + coin + '&tsym=' + currency + '&limit=30&api_key=' +
                                   self.api_key) as r:
                        if r.status == 200:
                            apiRequestHistory = await r.json()

                current_price = float(
                    apiRequestCoins['RAW'][coin][currency]['PRICE'])
                price_7d = float(
                    apiRequestHistory['Data']['Data'][23]['close'])
                price_30d = float(
                    apiRequestHistory['Data']['Data'][0]['close'])

                # Check for 0 prices before dividing to calculate the change.
                if price_7d == 0:
                    change_7d.append('n/a')
                else:
                    change_7d.append(
                        '%.1f' %
                        round(100 * float(current_price / price_7d - 1), 2))
                if price_30d == 0:
                    change_30d.append('n/a')
                else:
                    change_30d.append(
                        '%.1f' %
                        round(100 * float(current_price / price_30d - 1), 2))

            except KeyError:
                r = (
                    'Heast du elelelendige Scheißkreatur, schau amoi wos du für an'
                    + ' Bledsinn gschrieben host. Oida!')
                return r

        # Dynamic indent width.
        coinwidth = len(max(coins, key=len))
        valuewidth = len(max(values, key=len))
        changewidth_24h = len(max(change_24h, key=len))
        changewidth_7d = len(max(change_7d, key=len))
        changewidth_30d = len(max(change_30d, key=len))

        # Calculate rating for the first coin in the list.
        rating_24h = self.calculateRating(change_24h[0])
        rating_7d = self.calculateRating(change_7d[0])
        rating_30d = self.calculateRating(change_30d[0])

        # Use currency symbols to save space.
        if currency == 'EUR':
            currency_symbol = '€'
        elif currency == 'BTC':
            currency_symbol = '₿'
        else:
            currency_symbol = 'N/A'

        r = '```\n'
        for x in coins:
            r += ((coins[coins.index(x)]).rjust(coinwidth) + ': ' +
                  (values[coins.index(x)]).rjust(valuewidth) + ' ' + currency_symbol +
                  ' | ' + (change_24h[coins.index(x)]).rjust(changewidth_24h) +
                  '% | ' + (change_7d[coins.index(x)]).rjust(changewidth_7d) +
                  '% | ' +
                  (change_30d[coins.index(x)]).rjust(changewidth_30d) + '%\n')
        if globalStats:
            r += ('\nMarket Cap: ' + totalMarketCap + ' Mrd. EUR')
            r += ('\nVolume 24h: ' + totalVolume + ' Mrd. EUR')
            r += ('\nBTC dominance: ' + btcDominance + '%')
            r += '```'
            r += rating_24h + ' ' + rating_7d + ' ' + rating_30d
        else:
            r += '```'
            r += rating_24h + ' ' + rating_7d + ' ' + rating_30d
        return r

    def getTopTenCoins(self, btc=False):
        topTenList = requests.get(
            'https://api.coingecko.com/api/v3/coins/markets?vs_currency=EUR&order=market_cap_desc&per_page=10&page=1&sparkline=false'
        ).json()
        topTenCoins = []
        for i in range(10):
            topTenCoins.append(topTenList[i]['symbol'].upper())
        if btc:
            topTenCoins.remove('BTC')
        return ','.join(topTenCoins)

    def calculateRating(self, change):
        try:
            if float(change) < -5:
                rating = self.ripperl_string
            elif float(change) > 5:
                rating = self.moon_string
            else:
                rating = self.gurkerl_string
        except ValueError:
            rating = ''
        return rating

    def getEzkValue(self):
        """Grab secret values from environment variables."""
        amountBTC = float(os.environ['AMOUNT_BTC'])
        amountETH = float(os.environ['AMOUNT_ETH'])
        apiRequest = requests.get(
            'https://min-api.cryptocompare.com/data/pricemultifull?fsyms=BTC,ETH&tsyms=EUR&api_key='
            + self.api_key).json()
        valueBTC = float(apiRequest['RAW']['BTC']['EUR']['PRICE'])
        valueETH = float(apiRequest['RAW']['ETH']['EUR']['PRICE'])
        value = round(amountBTC * valueBTC + amountETH * valueETH, 2)
        r = '```'
        r += '€zk: ' + str(value) + ' EUR | ' + '{:+}%'.format(
            round((value / 220 - 1) * 100, 2))
        r += '```'
        return r

    def getHistoricalPrices(self):
        # Initiate arrays
        rows = []
        returns= []
        
        # Grab current values for a coin from Cryptocompare and get the current price
        apiRequestCoins = requests.get(
            'https://min-api.cryptocompare.com/data/pricemultifull?fsyms=' +
            'BTC' + '&tsyms=' + 'EUR' + '&api_key=' +
            self.api_key).json()
      
        current_price = float(
                    apiRequestCoins['RAW']['BTC']['EUR']['PRICE'])
        
        rows.append(tuple([str(date.today().strftime("%Y-%m-%d")), current_price]))  
        
        # Query to retrieve historical BTC prices
        query = ("""SELECT DATE, CLOSE
                FROM
                    wlcbot.`bitcoin_historical`
                WHERE
                    DAYOFYEAR(CURRENT_DATE) = DAYOFYEAR(DATE)
                ORDER BY DATE DESC""")
                
        # Check DB connection
        self.cnx = check_connection(self.cnx)
        self.cursor = self.cnx.cursor(buffered=True)
        
        # Execute query
        self.cursor.execute(query)
        self.cnx.commit()
        
        # If resultset is non empty, add rows to array        
        if self.cursor.rowcount > 0:
            rows += self.cursor.fetchall()
            
            # Calculate year on year returns
            for index, row in enumerate(rows):
                if index == len(rows)-1:
                    returns.append('\n')
                else:
                    returns.append(str('%.1f' % ((float(row[1]) / float(rows[index+1][1])-1)*100)) + '%\n')
            
            # Define widths for prices and returns
            valuewidth = len(max((str(row[1]) for row in rows), key=len))
            returnswidth = len(max(returns, key=len))        

            # Prepare and send output
            r = '```\n' 
            for index, row in enumerate(rows):
                r += row[0] + ': ' + str(row[1]).rjust(valuewidth) + ' € | ' + returns[index].rjust(returnswidth)       
            r += '```'
        else:
            r = 'Keine Daten in der Datenbank 😟'    
        return r

    # Check if the channel is crypto or test, otherwise Eierklatscher
    async def checkChannelAndSend(self, message, function):
        if message.channel.id == 351724430306574357 or message.channel.id == 705617951440633877:
            await message.channel.send(function)
        else:
            await message.add_reaction('🥚')
            await message.add_reaction('👏')
            await message.channel.send('fc, heast!')



def setup(client):
    client.add_cog(crypto(client))
