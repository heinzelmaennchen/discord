import discord
from discord.ext import commands
import os
import requests


class crypto(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.moon_string = ':full_moon: :full_moon: :full_moon:'
        self.gurkerl_string = ':cucumber: :cucumber: :cucumber:'
        self.ripperl_string = ':meat_on_bone: :meat_on_bone: :meat_on_bone:'
        self.ourCoins = os.environ['OUR_COINS']
        self.api_key = os.environ['API_KEY']

    # Use on_message if command isn't possible
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.client.user or message.author.bot or message.channel.type == "private":
            return

        if message.content.startswith('$'):
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
        await self.checkChannelAndSend(
            ctx.message, self.getCurrentValues(self.ourCoins, globalStats))

    @commands.command(aliases=['topbtc', 'topBtc'])
    @commands.guild_only()
    async def topBTC(self, ctx):
        await self.checkChannelAndSend(
            ctx.message, self.getCurrentValues(self.ourCoins, currency='BTC'))

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
        coins = self.getTopTenCoins()
        await self.checkChannelAndSend(
            ctx.message, self.getCurrentValues(coins, currency='BTC'))

    # Crypto helper functions
    def getCurrentValues(self, coin, globalStats=False, currency='EUR'):
        """Grab current values for a coin from Coinlib."""
        apiRequestCoins = requests.get('https://coinlib.io/api/v1/coin?key=' +
                                       self.api_key + '&pref=' + currency +
                                       '&symbol=' + coin)
        apiRequestCoins = apiRequestCoins.json()
        """Grab global stats if requested."""
        if globalStats:
            apiRequestGlobal = requests.get(
                'https://coinlib.io/api/v1/global?key=' + self.api_key +
                '&pref=EUR').json()

            totalMarketCap = str(
                round(float(apiRequestGlobal['total_market_cap']) / 10**9, 1))
            totalVolume = str(
                round(float(apiRequestGlobal['total_volume_24h']) / 10**9, 1))
            """Calculate the rating for emoji madness."""
            rating_24h = self.calculateRating(
                round(float(apiRequestCoins['coins'][0]['delta_24h']), 2))
            rating_7d = self.calculateRating(
                round(float(apiRequestCoins['coins'][0]['delta_7d']), 2))
            rating_30d = self.calculateRating(
                round(float(apiRequestCoins['coins'][0]['delta_30d']), 2))
            """This only works as long as BTC is the first coin in the response."""
            btcDominance = '{0:.2f}%'.format(
                float(apiRequestCoins['coins'][0]['market_cap']) /
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
                values.append('%.2f' % round(float(coinStats['price']), 2))
                change_24h.append('%.2f' %
                                  round(float(coinStats['delta_24h']), 2))
                change_7d.append('%.2f' %
                                 round(float(coinStats['delta_7d']), 2))
                change_30d.append('%.2f' %
                                  round(float(coinStats['delta_30d']), 2))
            except KeyError:
                r = (
                    'Heast du elelelendige Scheißkreatur, schau amoi wos du für an'
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
            r += ((coins[coins.index(x)]).rjust(coinwidth) + ': ' +
                  (values[coins.index(x)]).rjust(valuewidth) + ' ' + currency +
                  ' | ' + (change_24h[coins.index(x)]).rjust(changewidth_24h) +
                  '% | ' + (change_7d[coins.index(x)]).rjust(changewidth_7d) +
                  '% | ' +
                  (change_30d[coins.index(x)]).rjust(changewidth_30d) + '%\n')
        if globalStats:
            r += ('\nMarket Cap: ' + totalMarketCap + ' Mrd. EUR')
            r += ('\nVolume 24h: ' + totalVolume + ' Mrd. EUR')
            r += ('\nBTC dominance: ' + btcDominance)
            r += '```'
            r += rating_24h + ' ' + rating_7d + ' ' + rating_30d
        else:
            r += '```'
        return r

    def getTopTenCoins(self):
        topTenList = requests.get('https://coinlib.io/api/v1/coinlist?key=' +
                                  self.api_key +
                                  '&pref=EUR&page=1&order=rank_asc').json()
        topTenCoins = []
        for i in range(10):
            topTenCoins.append(topTenList['coins'][i]['symbol'])
        return ', '.join(topTenCoins)

    def calculateRating(self, change):
        if change < -5:
            rating = self.ripperl_string
        elif change > 5:
            rating = self.moon_string
        else:
            rating = self.gurkerl_string
        return rating

    def getEzkValue(self):
        """Grab secret values from environment variables."""
        amountBTC = float(os.environ['AMOUNT_BTC'])
        amountETH = float(os.environ['AMOUNT_ETH'])
        apiRequest = \
          requests.get('https://coinlib.io/api/v1/coin?key=' + self.api_key + '&pref=EUR&symbol='
                      + 'BTC,ETH').json()
        valueBTC = float(apiRequest['coins'][0]['price'])
        valueETH = float(apiRequest['coins'][1]['price'])
        value = round(amountBTC * valueBTC + amountETH * valueETH, 2)
        r = '```'
        r += '€zk: ' + str(value) + ' EUR | ' + '{:+}%'.format(
            round((value / 220 - 1) * 100, 2))
        r += '```'
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
