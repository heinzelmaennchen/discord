import discord
from discord.ext import commands
import aiohttp
import os
from utils.db import check_connection
from utils.db import init_db
from datetime import date
import re


class crypto(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.moon_string = ':full_moon: :full_moon: :full_moon:'
        self.gurkerl_string = ':cucumber: :cucumber: :cucumber:'
        self.ripperl_string = ':meat_on_bone: :meat_on_bone: :meat_on_bone:'
        self.ourCoins = os.environ['OUR_COINS']
        self.api_key = os.environ['API_KEY']
        self.bannedCoins = os.environ['COINFILTER']
        self.cnx = init_db()

    # Use on_message if command isn't possible
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.client.user or message.author.bot or message.channel.type == "private":
            return

        if message.content.startswith('$'):
            if message.content.startswith('$ratio'):
                coin = message.content[7:].upper().strip(' ,').replace(' ', '')
                await self.checkChannelAndSend(
                    message, await self.getCurrentValues(coin, currency='BTC'))
            else:
                coin = message.content[1:].upper().strip(' ,').replace(' ', '')
                await self.checkChannelAndSend(
                    message, await self.getCurrentValues(coin))
        elif message.content == '€zk':
            await self.checkChannelAndSend(message, await self.getEzkValue())

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
            ctx.message, await self.getCurrentValues(self.ourCoins,
                                                     globalStats))

    @commands.command(aliases=['topbtc', 'topBtc'])
    @commands.guild_only()
    async def topBTC(self, ctx):
        await self.checkChannelAndSend(
            ctx.message, await self.getCurrentValues(self.ourCoins, currency='BTC'))

    @commands.command(aliases=['top10'])
    @commands.guild_only()
    async def topten(self, ctx):
        coins = await self.getTopTenCoins()
        if coins == 'spam':
            await self.checkChannelAndSend(ctx.message, 'Spammen einstellen, sonst fahrst morgen mit dem Zahnbürscht\'l in\'s Leere!')
        else:
            await self.checkChannelAndSend(ctx.message, await
                                           self.getCurrentValues(coins))

    @commands.command(
        aliases=['toptenbtc', 'toptenBtc', 'top10BTC', 'top10Btc', 'top10btc'])
    @commands.guild_only()
    async def toptenBTC(self, ctx):
        coins = await self.getTopTenCoins(True)
        if coins == 'spam':
            await self.checkChannelAndSend(ctx.message, 'Spammen einstellen, sonst fahrst morgen mit dem Zahnbürscht\'l in\'s Leere!')
        else:
            await self.checkChannelAndSend(ctx.message, await
                                           self.getCurrentValues(coins, currency='BTC'))

    @commands.command()
    @commands.guild_only()
    async def history(self, ctx):
        await self.checkChannelAndSend(ctx.message, await
                                       self.getHistoricalPrices())

    @commands.command()
    @commands.guild_only()
    async def ath(self, ctx, *args):
        if not args:
            await self.checkChannelAndSend(ctx.message, await
                                           self.getCurrentValues(self.ourCoins, ath=True))
        else:
            await self.checkChannelAndSend(ctx.message, await
                                           self.getCurrentValues(','.join(args), ath=True))

    @commands.command()
    @commands.guild_only()
    async def athbtc(self, ctx, *args):
        if not args:
            await self.checkChannelAndSend(ctx.message, await
                                           self.getCurrentValues(self.ourCoins, ath=True, currency='BTC'))
        else:
            await self.checkChannelAndSend(ctx.message, await
                                           self.getCurrentValues(','.join(args), ath=True, currency='BTC'))

    @commands.command()
    @commands.guild_only()
    async def kraken(self, ctx, *args):
        status = 0
        if not args:
            first = 'BTC'
            second = 'EUR'
        elif len(args) == 1:
            first = args[0].upper()
            second = 'EUR'
        elif len(args) == 2:
            first = args[0].upper()
            second = args[1].upper()
        else:
            first = ''
            second = ''
            status = 2

        first = re.sub('[^A-Za-z0-9]+', '', first)
        second = re.sub('[^A-Za-z0-9]+', '', second)

        if len(first) > 6 or len(second) > 6:
            status = 1

        await self.checkChannelAndSend(
            ctx.message, self.getKrakenChartUrl(first, second, status))

    async def getCurrentValues(self,
                               coinList,
                               globalStats=False,
                               ath=False,
                               currency='EUR'):
        # Based on an ID get the corresponding symbol, or, if supplying a symbol, get the corresponding ID from Coingecko.
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.coingecko.com/api/v3/coins/list') as r:
                if r.status == 200:
                    apiResponseCoinList = await r.json()
                    await session.close()
                elif r.status == 429:
                    r = 'Spammen einstellen, sonst fahrst morgen mit dem Zahnbürscht\'l in\'s Leere!'
                    await session.close()
                    return r
                else:
                    r = r.status
                    await session.close()
                    return r

        coins = coinList.split(',')
        coinDict = {}

        for coin in coins:
            try:
                coinDict[coin.lower()] = list(filter(lambda x: x["id"] == coin.lower(), apiResponseCoinList))[
                    0]["symbol"]
                continue
            except IndexError:
                pass
            try:
                results = list(
                    filter(lambda x: x["symbol"] == coin.lower(), apiResponseCoinList))
                # If more than one result is found, first kick out banned coins:
                bannedCoins = self.bannedCoins.split(',')
                matches = []
                for result in results:
                    skip = False
                    for bannedCoin in bannedCoins:
                        if bannedCoin in result["id"]:
                            skip = True
                            break
                    if not skip:
                        matches.append(result["id"])
                if len(matches) > 1:
                    r = (
                        'Leider gibt es das Symbol ' + coin + ' wohl öfter. Bitte eine dieser IDs verwenden, du Oasch: ' + ', '.join(matches))
                    return r
                else:
                    coinDict[list(
                        filter(lambda x: x["symbol"] == coin.lower(), apiResponseCoinList))[0]["id"]] = coin.lower()
            except IndexError:
                r = (
                    'Heast du elelelendige Scheißkreatur, schau amoi wos du für an'
                    + ' Bledsinn gschrieben host. Oida!')
                return r

        # Grab market data for one or multiple coins from Coingecko.
        marketDict = {}

        for coin in coinDict.keys():
            async with aiohttp.ClientSession() as session:
                async with session.get(
                        'https://api.coingecko.com/api/v3/coins/'
                        + coin
                        + '?localization=false'
                        + '&tickers=false'
                        + '&market_data=true'
                        + '&community_data=false'
                        + '&developer_data=false') as r:
                    if r.status == 200:
                        marketDict[coin] = await r.json()
                        await session.close()
                    elif r.status == 429:
                        r = 'Spammen einstellen, sonst fahrst morgen mit dem Zahnbürscht\'l in\'s Leere!'
                        await session.close()
                        return r
                    else:
                        r = r.status
                        await session.close()
                        return r

        # If ATH data is requested, call the function and return the constructed message.
        if ath:
            r = self.getAthData(marketDict, currency)
            return r

        # Grab global stats if requested.
        if globalStats:

            async with aiohttp.ClientSession() as session:
                async with session.get(
                        'https://api.coingecko.com/api/v3/global') as r:
                    if r.status == 200:
                        json = await r.json()
                        apiResponseGlobal = json['data']
                        await session.close()
                    elif r.status == 429:
                        r = 'Spammen einstellen, sonst fahrst morgen mit dem Zahnbürscht\'l in\'s Leere!'
                        await session.close()
                        return r
                    else:
                        r = r.status
                        await session.close()
                        return r

            totalMarketCap = str(
                round(
                    float(
                        apiResponseGlobal['total_market_cap']['eur']) / 10**9,
                    1))
            totalVolume = str(
                round(
                    float(apiResponseGlobal['total_volume']['eur']) / 10**9, 1))
            btcDominance = str(
                round(float(apiResponseGlobal['market_cap_percentage']['btc']),
                      1))

        # Create and initiate lists for coins, values, %change and rating.
        symbols = []
        values = []
        change_24h = []
        change_7d = []
        change_30d = []

        # Define floating point precision for price.
        if len(coinDict) == 1:
            coin = list(coinDict.keys())[0]
            price = str(marketDict[coin]["market_data"]
                        ["current_price"][currency.lower()])

            def scientific_to_float(string):
                if 'e' in string:
                    e_index = string.index('e')
                    base = float(string[:e_index])
                    exponent = float(string[e_index + 1:])
                    float_number = base * (10 ** exponent)
                    return float_number
                else:
                    return float(string)

            price = scientific_to_float(price)

            if price < 1:
                index = re.search("[1-9]", "{:.20f}".format(price)).start()
                precision = index
            else:
                precision = 2
        elif currency == 'BTC':
            precision = 5
        else:
            precision = 2

        # Build response.
        for coin in marketDict:
            symbols.append(marketDict[coin]["symbol"].upper())
            values.append(
                '%.{}f'.format(precision) % round(marketDict[coin]["market_data"]["current_price"][currency.lower()], precision))
            try:
                change_24h.append('%.1f' % round(
                    marketDict[coin]["market_data"]["price_change_percentage_24h_in_currency"][currency.lower()], precision))
            except KeyError:
                change_24h.append('n/a')
                pass
            try:
                change_7d.append('%.1f' % round(
                    marketDict[coin]["market_data"]["price_change_percentage_7d_in_currency"][currency.lower()], precision))
            except KeyError:
                change_7d.append('n/a')
                pass
            try:
                change_30d.append('%.1f' % round(
                    marketDict[coin]["market_data"]["price_change_percentage_30d_in_currency"][currency.lower()], precision))
            except KeyError:
                change_30d.append('n/a')
                pass

        # Dynamic indent width.
        coinwidth = len(max(symbols, key=len))
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
        for x in range(len(symbols)):
            r += ((symbols[x]).rjust(coinwidth) + ': ' +
                  (values[x]).rjust(valuewidth) + ' ' + currency_symbol +
                  ' | ' + (change_24h[x]).rjust(changewidth_24h) + '% | ' +
                  (change_7d[x]).rjust(changewidth_7d) + '% | ' +
                  (change_30d[x]).rjust(changewidth_30d) + '%\n')
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

    async def getTopTenCoins(self, btc=False):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    'https://api.coingecko.com/api/v3/coins/markets?vs_currency=EUR&order=market_cap_desc&per_page=20&page=1&sparkline=false'
            ) as r:
                if r.status == 200:
                    topTenList = await r.json()
                    await session.close()
                else:
                    r = 'spam'
                    await session.close()
                    return r

        topTenCoins = []
        for i in range(20):
            if len(topTenCoins) == 10:
                break
            coin = topTenList[i]['id']
            symbol = topTenList[i]['symbol']
            if symbol in ('usdt, usdc, busd'):
                continue
            else:
                topTenCoins.append(coin)
        if btc:
            topTenCoins.remove('bitcoin')
        return ','.join(topTenCoins)

    def calculateRating(self, change):
        try:
            if float(change) <= -5:
                rating = self.ripperl_string
            elif float(change) >= 5:
                rating = self.moon_string
            else:
                rating = self.gurkerl_string
        except ValueError:
            rating = ''
        return rating

    def getAthData(self, marketDict, currency):
        # Create and initiate lists for coins, values, %change and rating.
        symbols = []
        ath = []
        values = []
        ath_percentage = []
        ath_date = []

        # Define floating point precision for price.
        if currency == 'BTC':
            precision = 6
            if 'bitcoin' in marketDict:
                marketDict.pop('bitcoin')
        else:
            precision = 2

        # Build response.
        for coin in marketDict:
            symbols.append(marketDict[coin]["symbol"].upper())
            try:
                ath.append('%.{}f'.format(precision) % round(
                    marketDict[coin]["market_data"]["ath"][currency.lower()], precision))
            except KeyError:
                ath.append('n/a')
                pass
            values.append(
                '%.{}f'.format(precision) % round(marketDict[coin]["market_data"]["current_price"][currency.lower()], precision))
            try:
                ath_percentage.append('%.1f' % round(
                    marketDict[coin]["market_data"]["ath_change_percentage"][currency.lower()], precision))
            except KeyError:
                ath_percentage.append('n/a')
                pass
            try:
                ath_date.append(
                    marketDict[coin]["market_data"]["ath_date"][currency.lower()][:10])
            except KeyError:
                ath_date.append('n/a')
                pass

                # Dynamic indent width.
        coinwidth = len(max(symbols, key=len))
        athwidth = len(max(ath, key=len))
        valuewidth = len(max(values, key=len))
        changewidth_7d = len(max(ath_percentage, key=len))
        changewidth_30d = len(max(ath_date, key=len))

        # Use currency symbols to save space.
        if currency == 'EUR':
            currency_symbol = '€'
        elif currency == 'BTC':
            currency_symbol = '₿'
        else:
            currency_symbol = 'N/A'

        r = '```\n'
        for x in symbols:
            r += ((symbols[symbols.index(x)]).rjust(coinwidth) + ': ' +
                  (values[symbols.index(x)]).rjust(valuewidth) +
                  currency_symbol + ' | ' +
                  (ath[symbols.index(x)]).rjust(athwidth) + ' ' +
                  currency_symbol + ' | ' +
                  (ath_percentage[symbols.index(x)]).rjust(changewidth_7d) +
                  '% | ' +
                  (ath_date[symbols.index(x)]).rjust(changewidth_30d) + '\n')
        r += '```'
        return r

    async def getEzkValue(self):
        """Grab secret values from environment variables."""
        amountBTC = float(os.environ['AMOUNT_BTC'])
        amountETH = float(os.environ['AMOUNT_ETH'])

        async with aiohttp.ClientSession() as session:
            async with session.get(
                    'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin%2Cethereum&vs_currencies=eur') as r:
                if r.status == 200:
                    apiRequest = await r.json()
                    await session.close()
                elif r.status == 429:
                    r = 'Spammen einstellen, sonst fahrst morgen mit dem Zahnbürscht\'l in\'s Leere!'
                    await session.close()
                    return r
                else:
                    r = r.status
                    await session.close()
                    return r

        valueBTC = float(apiRequest['bitcoin']['eur'])
        valueETH = float(apiRequest['ethereum']['eur'])
        value = round(amountBTC * valueBTC + amountETH * valueETH, 2)
        r = '```'
        r += '€zk: ' + str(value) + ' EUR | ' + '{:+}%'.format(
            round((value / 220 - 1) * 100, 2))
        r += '```'
        return r

    async def getHistoricalPrices(self):
        # Initiate arrays
        rows = []
        returns = []

        # Grab current values for a coin from Cryptocompare and get the current price
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    'https://api.coingecko.com/api/v3/coins/'
                    + 'bitcoin'
                    + '?localization=false'
                    + '&tickers=false'
                    + '&market_data=true'
                    + '&community_data=false'
                    + '&developer_data=false') as r:
                if r.status == 200:
                    apiRequestCoins = await r.json()
                    await session.close()
                elif r.status == 429:
                    r = 'Spammen einstellen, sonst fahrst morgen mit dem Zahnbürscht\'l in\'s Leere!'
                    await session.close()
                    return r
                else:
                    r = r.status
                    await session.close()
                    return r

        current_price = '%.{}f'.format(2) % round(
            apiRequestCoins["market_data"]["current_price"]['eur'], 2)

        rows.append(
            tuple([str(date.today().strftime("%Y-%m-%d")), current_price]))

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
                if index == len(rows) - 1:
                    returns.append('\n')
                else:
                    returns.append(
                        str('%.1f' %
                            ((float(row[1]) / float(rows[index + 1][1]) - 1) *
                             100)) + '%\n')

            # Define widths for prices and returns
            valuewidth = len(max((str(row[1]) for row in rows), key=len))
            returnswidth = len(max(returns, key=len))

            # Prepare and send output
            r = '```\n'
            for index, row in enumerate(rows):
                r += row[0] + ': ' + str(row[1]).rjust(
                    valuewidth) + ' € | ' + returns[index].rjust(returnswidth)
            r += '```'
        else:
            r = 'Keine Daten in der Datenbank 😟'
        return r

    def getKrakenChartUrl(self, first, second, status):
        baseUrl = 'https://trade.kraken.com/charts/KRAKEN:'
        sUrl = baseUrl + first + '-' + second + '/'
        r = sUrl

        if status == 1:
            r = 'Parameter zu lang, das sind doch fix keine echten Tickersymbole'
        elif status == 2:
            r = 'Zu viele Parameter. Maximal 2!'
        else:
            pass
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
