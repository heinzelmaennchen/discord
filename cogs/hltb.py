import discord
from discord.ext import commands
from bs4 import BeautifulSoup
import aiohttp

HLTB_URL = 'https://howlongtobeat.com/'
HLTB_SEARCH = HLTB_URL + 'search_results?page=1'
HLTB_REFERER = HLTB_URL


class hltb(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    @commands.guild_only()
    async def hltb(self, ctx, *, game):
        hltbResult = await HLTB(game)
        for x in hltbResult:
            title = x

        embedHltb = discord.Embed(title=title,
                                  url=hltbResult[title]['url'],
                                  colour=discord.Colour.from_rgb(255, 128, 0))
        try:
            embedHltb.add_field(name='Main Story',
                                value=f"{hltbResult[title]['Main Story']}",
                                inline=True)
            embedHltb.add_field(name='Main + Extra',
                                value=f"{hltbResult[title]['Main + Extra']}",
                                inline=True)
            embedHltb.add_field(name='Completionist',
                                value=f"{hltbResult[title]['Completionist']}",
                                inline=True)
        except:
            pass
        try:
            embedHltb.add_field(name='Solo',
                                value=f"{hltbResult[title]['Solo']}",
                                inline=True)
        except:
            pass
        try:
            embedHltb.add_field(name='Co-Op',
                                value=f"{hltbResult[title]['Co-Op']}",
                                inline=True)
        except:
            pass
        try:
            embedHltb.add_field(name='Vs.',
                                value=f"{hltbResult[title]['Vs.']}",
                                inline=True)
        except:
            pass

        await ctx.send(embed=embedHltb)


# Copied and modified from: https://github.com/fuzzylimes/howlongtobeat-scraper
### Main Function ###
async def HLTB(title):
    try:
        times, title, url = await FindGame(title)
        hltbResult = {
            title: {
                'url': url,
            }
        }
        for i in range(0, len(times)):
            hltbResult[title].update({times[i][0]: times[i][1]})
        return hltbResult
    except:
        raise


#######################################
# Helpers
#######################################
async def FindGame(title):
    soup = BeautifulSoup(await GetPage(title), 'html.parser')
    try:
        page = soup.findAll("div", class_="search_list_details")[0]
    except IndexError:
        raise Exception('{} Not Found'.format(title))
    tmp = page.find("a", title=True, href=True)
    #title,url = tmp['title'], HLTB_PRE + tmp['href'] ORIGINAL
    title, url = tmp.text, HLTB_URL + tmp['href']
    scrape = page.findAll("div", class_="search_list_tidbit")
    result = []
    try:
        result = [
            (scrape[0].text, "{} Hrs".format(scrape[1].text.split(' ')[0])),
            (scrape[2].text, "{} Hrs".format(scrape[3].text.split(' ')[0])),
            (scrape[4].text, "{} Hrs".format(scrape[5].text.split(' ')[0]))
        ]
    except IndexError:
        pass
    scrape = [
        page.findAll("div", class_="search_list_tidbit_short"),
        page.findAll("div", class_="search_list_tidbit_long")
    ]
    try:
        for i in range(0, len(scrape[0])):
            result.append((scrape[0][i].text,
                           "{} Hrs".format(scrape[1][i].text.split(' ')[0])))
    except IndexError:
        pass
    return result, title, url


async def GetPage(title):
    headers = {
        'Content-type':
        'application/x-www-form-urlencoded',
        'User-Agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36',
        'referer': HLTB_REFERER
    }
    data = {
        'queryString': title,
        't': 'games',
        'sorthead': 'popular',
        'length_type': 'main'
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(HLTB_SEARCH, data=data, headers=headers) as r:
            if r is not None and r.status == 200:
                data = await r.text()
                r = data
            else:
                r = None
        await session.close()
        return r

def setup(client):
    client.add_cog(hltb(client))