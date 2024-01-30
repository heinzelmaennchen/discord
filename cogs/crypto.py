import discord
from discord.ext import commands
import aiohttp
import os
from utils.db import check_connection
from utils.db import init_db
from utils.crypto import getTrackedBannedCoins
from utils.misc import isDev, isCChannel
from datetime import date, datetime, timedelta
from pytz import timezone
import re


class crypto(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.moon_string = ':full_moon: :full_moon: :full_moon:'
        self.gurkerl_string = ':cucumber: :cucumber: :cucumber:'
        self.ripperl_string = ':meat_on_bone: :meat_on_bone: :meat_on_bone:'
        self.api_key = os.environ['COINGECKO_KEY']
        self.ratings = []
        self.cnx = init_db()
        self.ourCoins, self.bannedCoins = getTrackedBannedCoins(self)

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
    async def halving(self, ctx):
        await self.checkChannelAndSend(ctx.message, await
                                       self.getHalvingTime())

    @commands.command(
        aliases=['priceon', 'wasletztepreisam', 'warderpreisheißam', 'wasletztepreis', 'ytd'])
    @commands.guild_only()
    async def price(self, ctx, inputDate=None):
        await self.checkChannelAndSend(ctx.message, await
                                       self.getHistoricalPriceByDate(inputDate))

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
        
    @commands.command()
    @commands.guild_only()
    @commands.check(isDev)
    @commands.check(isCChannel)
    async def addcoin(self, ctx, arg):
        query = (f'INSERT INTO `tracked_banned_coins` (coin, is_banned) VALUES (%s, %s)')
        data = (arg, 0)
        # Check DB connection
        self.cnx = check_connection(self.cnx)
        self.cursor = self.cnx.cursor(buffered=True)
        # Execute query
        try:
            self.cursor.execute(query, data)
            self.cnx.commit()
        except:
            return
        return
    
    @commands.command()
    @commands.guild_only()
    @commands.check(isDev)
    @commands.check(isCChannel)
    async def removecoin(self, ctx, arg):
        query = (f'DELETE FROM `tracked_banned_coins` WHERE id = %s AND is_banned = %s')
        data = (arg, 0)
        # Check DB connection
        self.cnx = check_connection(self.cnx)
        self.cursor = self.cnx.cursor(buffered=True)
        # Execute query
        try:
            self.cursor.execute(query, data)
            self.cnx.commit()
        except:
            return
        return
    
    @commands.command()
    @commands.guild_only()
    @commands.check(isDev)
    @commands.check(isCChannel)
    async def bancoin(self, ctx, arg):
        query = (f'INSERT INTO `tracked_banned_coins` (coin, is_banned) VALUES (%s, %s)')
        data = (arg, 1)
        # Check DB connection
        self.cnx = check_connection(self.cnx)
        self.cursor = self.cnx.cursor(buffered=True)
        # Execute query
        try:
            self.cursor.execute(query, data)
            self.cnx.commit()
        except:
            return
        return
    
    @commands.command()
    @commands.guild_only()
    @commands.check(isDev)
    @commands.check(isCChannel)
    async def unbancoin(self, ctx, arg):
        query = (f'DELETE FROM `tracked_banned_coins` WHERE id = %s AND is_banned = %s')
        data = (arg, 1)
        # Check DB connection
        self.cnx = check_connection(self.cnx)
        self.cursor = self.cnx.cursor(buffered=True)
        # Execute query
        try:
            self.cursor.execute(query, data)
            self.cnx.commit()
        except:
            return
        return
    
    @commands.command()
    @commands.guild_only()
    @commands.check(isDev)
    @commands.check(isCChannel)
    async def listtracked(self, ctx):
        query = (f'SELECT id, coin FROM `tracked_banned_coins` WHERE is_banned = 0')
        # Check DB connection
        self.cnx = check_connection(self.cnx)
        self.cursor = self.cnx.cursor(buffered=True)
        # Execute query
        try:
            self.cursor.execute(query)
            self.cnx.commit()
            rows = self.cursor.fetchall()
        except:
            return
        r = "```\n"
        for row in rows:
            r += f'{row[0]}: {row[1]}\n'
        r += "```"
        await self.checkChannelAndSend(ctx.message, r)
    
    @commands.command()
    @commands.guild_only()
    @commands.check(isDev)
    @commands.check(isCChannel)
    async def listbanned(self, ctx):
        query = (f'SELECT id, coin FROM `tracked_banned_coins` WHERE is_banned = 1')
        # Check DB connection
        self.cnx = check_connection(self.cnx)
        self.cursor = self.cnx.cursor(buffered=True)
        # Execute query
        try:
            self.cursor.execute(query)
            self.cnx.commit()
            rows = self.cursor.fetchall()
        except:
            return
        r = "```\n"
        for row in rows:
            r += f'{row[0]}: {row[1]}\n'
        r += "```"
        await self.checkChannelAndSend(ctx.message, r)

    async def getCurrentValues(self,
                               coinList,
                               globalStats=False,
                               ath=False,
                               currency='EUR'):
        # Based on an ID get the corresponding symbol, or, if supplying a symbol, get the corresponding ID from Coingecko.
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.coingecko.com/api/v3/coins/list?x_cg_demo_api_key=' + self.api_key) as r:
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
                        filter(lambda x: x["symbol"] == coin.lower() and x["id"] == matches[0], apiResponseCoinList))[0]["id"]] = coin.lower()
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
                        + '&developer_data=false'
                        + '&x_cg_demo_api_key=' + self.api_key) as r:
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
                        'https://api.coingecko.com/api/v3/global?x_cg_demo_api_key=' + self.api_key) as r:
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
        rating_24h = self.calculateRating(change_24h[0], reactposition=1)
        rating_7d = self.calculateRating(change_7d[0], reactposition=2)
        rating_30d = self.calculateRating(change_30d[0], reactposition=3)

        self.ratings = [rating_24h, rating_7d, rating_30d]

        # Use currency symbols to save space.
        if currency == 'EUR':
            currency_symbol = '€'
        elif currency == 'BTC':
            currency_symbol = '₿'
        else:
            currency_symbol = 'N/A'

        r = '```\n\u200b'
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
        else:
            r += '```'
        return r

    async def getTopTenCoins(self, btc=False):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    'https://api.coingecko.com/api/v3/coins/markets?vs_currency=EUR&order=market_cap_desc&per_page=20&page=1&sparkline=false&x_cg_demo_api_key='
                    + self.api_key
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
            if symbol in ('usdt, usdc, busd, dai') or symbol == 'steth':
                continue
            else:
                topTenCoins.append(coin)
        if btc:
            topTenCoins.remove('bitcoin')
        return ','.join(topTenCoins)

    def calculateRating(self, change, reactposition):
        try:
            if float(change) <= -5:
                if reactposition == 1:
                    rating = '<:meatonbone_mgr_1:1184563797810216980>'
                elif reactposition == 2:
                    rating = '<:meatonbone_mgr_2:1184563834590072902>'
                elif reactposition == 3:
                    rating = '<:meatonbone_mgr_3:1184563872024248461>'
                else:
                    rating = '❌'
            elif float(change) >= 5:
                if reactposition == 1:
                    rating = '<:fullmoon_mgr_1:1184563679287591052>'
                elif reactposition == 2:
                    rating = '<:fullmoon_mgr_2:1184563713907367946>'
                elif reactposition == 3:
                    rating = '<:fullmoon_mgr_3:1184563746371272754>'
                else:
                    rating = '❌'
            else:
                if reactposition == 1:
                    rating = '<:cucumber_mgr_1:1184563462953775134>'
                elif reactposition == 2:
                    rating = '<:cucumber_mgr_2:1184563534667972628>'
                elif reactposition == 3:
                    rating = '<:cucumber_mgr_3:1184563581228961943>'
                else:
                    rating = '❌'
        except ValueError:
            rating = '❌'
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
        # Amounts for €zk
        amountBTC = float(os.environ['AMOUNT_BTC'])
        amountETH = float(os.environ['AMOUNT_ETH'])
        # Amount for ¥zk
        amountBTC2 = float(os.environ['AMOUNT_BTC2'])
        # Amount for ₴zk
        amountBTC3 = float(os.environ['AMOUNT_BTC3'])

        async with aiohttp.ClientSession() as session:
            async with session.get(
                    'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin%2Cethereum&vs_currencies=eur&x_cg_demo_api_key=' + self.api_key) as r:
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

        # Get current BTC and ETH price.
        valueBTC = float(apiRequest['bitcoin']['eur'])
        valueETH = float(apiRequest['ethereum']['eur'])
        # Calculate total value for €zk.
        value = round(amountBTC * valueBTC + amountETH * valueETH, 0)
        # Calculate total value for ¥zk.
        value2 = round(amountBTC2 * valueBTC, 0)
        # Calculate total value for ₴zk.
        value3 = round(amountBTC3 * valueBTC, 0)
        # Calculate change values to baseline.
        change = round((value / 220 - 1) * 100, 0)
        change2 = round((value2 / 255 - 1) * 100, 0)
        change3 = round((value3 / 250 - 1) * 100, 0)
        # Calculate width for dynamic indent.
        valuewidth = len(max(str(value), str(value2), str(value3)))-1
        changewidth = len(max(str(change), str(change2), str(change3)))
        # Construct response and return.
        r = '```'
        r += '€zk: ' + '{0:.0f}'.format(value).rjust(valuewidth) + ' € | ' + '{:+.0f}%'.format(
            change).rjust(changewidth)
        r += '\n'
        r += '¥zk: ' + '{0:.0f}'.format(value2).rjust(valuewidth) + ' € | ' + '{:+.0f}%'.format(
            change2).rjust(changewidth)
        r += '\n'
        r += '₴zk: ' + '{0:.0f}'.format(value3).rjust(valuewidth) + ' € | ' + '{:+.0f}%'.format(
            change3).rjust(changewidth)
        r += '```'
        return r

    async def getHistoricalPrices(self):
        # Initiate arrays
        rows = []
        returns = []

        # Grab current values for a coin from Coingecko and get the current price
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    'https://api.coingecko.com/api/v3/coins/'
                    + 'bitcoin'
                    + '?localization=false'
                    + '&tickers=false'
                    + '&market_data=true'
                    + '&community_data=false'
                    + '&developer_data=false'
                    + '&x_cg_demo_api_key=' + self.api_key) as r:
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

    async def getHistoricalPriceByDate(self, inputDate):
        rows = []
        changes = []
        format = "%Y-%m-%d"

        if inputDate:
            try:
                inputDate = datetime.strptime(str(inputDate), format)
                inputDate = inputDate.strftime(format)
            except ValueError:
                r = "Falsches Format oder kaputtes Datum, need YYYY-MM-DD, pls."
                return r
        else:
            inputDate = date.today().replace(day=1, month=1).strftime(format)

        # Query to retrieve historical BTC prices on a date
        query = (
            f'SELECT DATE, CLOSE FROM `bitcoin_historical` WHERE date = "{inputDate}"'
        )

        # Check DB connection
        self.cnx = check_connection(self.cnx)
        self.cursor = self.cnx.cursor(buffered=True)

        # Execute query
        self.cursor.execute(query)
        self.cnx.commit()

        # If resultset is non empty, add rows to array
        if self.cursor.rowcount > 0:
            rows += self.cursor.fetchall()

            # Grab current values for a coin from Cryptocompare and get the current price
            async with aiohttp.ClientSession() as session:
                async with session.get(
                        'https://api.coingecko.com/api/v3/coins/'
                        + 'bitcoin'
                        + '?localization=false'
                        + '&tickers=false'
                        + '&market_data=true'
                        + '&community_data=false'
                        + '&developer_data=false'
                        + '&x_cg_demo_api_key=' + self.api_key) as r:
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

            # Calculate change
            for index, row in enumerate(rows):
                if index == len(rows) - 1:
                    changes.append(
                        str('%.1f' %
                            ((float(current_price) / float(rows[index-1][1]) - 1) *
                             100)) + '%\n')
                else:
                    changes.append('\n')

            # Define widths for prices and changes
            valuewidth = len(max((str(row[1]) for row in rows), key=len))
            changeswidth = len(max(changes, key=len))

            # Prepare and send output
            r = '```\n'
            for index, row in enumerate(rows):
                r += row[0] + ': ' + str(row[1]).rjust(
                    valuewidth) + ' € | ' + changes[index].rjust(changeswidth)
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

    # Get most recent block height and calculate time until next halving
    async def getHalvingTime(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    'https://mempool.space/api/blocks/tip/height') as r:
                if r.status == 200:
                    currentBlockHeight = int(await r.text())
                    await session.close()
                elif r.status == 429:
                    r = 'Spammen einstellen, sonst fahrst morgen mit dem Zahnbürscht\'l in\'s Leere!'
                    await session.close()
                    return r
                else:
                    r = r.status
                    await session.close()
                    return r
        halvingInterval = 210000
        remainingBlocks = halvingInterval - \
            (currentBlockHeight % halvingInterval)
        predictedHalvingDate = datetime.now(
            timezone('Europe/Vienna')) + timedelta(minutes=remainingBlocks * 10)
        r = '```\n'
        r += 'Next halving approximately on: ' + \
            predictedHalvingDate.strftime('%Y-%m-%d %H:%M') + '\n'
        r += 'Current block height: ' + str(currentBlockHeight) + '\n'
        r += 'Blocks remaining: ' + str(remainingBlocks)
        r += '```'
        return r

    # Check if the channel is crypto or test, otherwise Eierklatscher
    async def checkChannelAndSend(self, message, function):
        if message.channel.id == 351724430306574357 or message.channel.id == 705617951440633877:
            sent_message = await message.channel.send(function)
            if self.ratings:
                await sent_message.add_reaction(self.ratings[0])
                await sent_message.add_reaction(self.ratings[1])
                await sent_message.add_reaction(self.ratings[2])
                self.ratings = []
        else:
            await message.add_reaction('🥚')
            await message.add_reaction('👏')
            await message.channel.send('fc, heast!')

def setup(client):
    client.add_cog(crypto(client))
