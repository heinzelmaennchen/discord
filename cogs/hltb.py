import discord
from discord.ext import commands
from bs4 import BeautifulSoup
import requests

HLTB_URL = 'https://howlongtobeat.com/search_results.php?page=1'
HLTB_PRE = 'https://howlongtobeat.com/'


class hltb(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    @commands.guild_only()
    async def hltb(self, ctx, *, game):
        hltbResult = HLTB(game)
        for x in hltbResult:
            title = x

        embedHltb = discord.Embed(title=title,
                                  url=hltbResult[title]['url'],
                                  colour=discord.Colour.from_rgb(255, 128, 0))
        embedHltb.add_field(name='Main Story',
                            value=f"{hltbResult[title]['Main Story']}",
                            inline=True)
        embedHltb.add_field(name='Main + Extra',
                            value=f"{hltbResult[title]['Main + Extra']}",
                            inline=True)
        embedHltb.add_field(name='Completionist',
                            value=f"{hltbResult[title]['Completionist']}",
                            inline=True)

        await ctx.send(embed=embedHltb)


# Copied and modified from: https://github.com/fuzzylimes/howlongtobeat-scraper
### Main Function ###
def HLTB(title):
    try:
        times, title, url = FindGame(title)
        return {
            title: {
                'url': url,
                'Main Story': times[0][1],
                'Main + Extra': times[1][1],
                'Completionist': times[2][1]
            }
        }
    except:
        raise


#######################################
# Helpers
#######################################
def FindGame(title):
    soup = BeautifulSoup(GetPage(title), 'html.parser')
    try:
        page = soup.findAll("div", class_="search_list_details")[0]
    except IndexError:
        raise Exception('{} Not Found'.format(title))
    tmp = page.find("a", title=True, href=True)
    #title,url = tmp['title'], HLTB_PRE + tmp['href'] ORIGINAL
    title, url = tmp.text, HLTB_PRE + tmp['href']
    scrape = page.findAll("div", class_="search_list_tidbit")
    result = [(scrape[0].text.split(' ')[1],
               "{} Hrs".format(scrape[1].text.split(' ')[0])),
              (''.join(scrape[2].text.split(' ')[1:]),
               "{} Hrs".format(scrape[3].text.split(' ')[0])),
              (scrape[4].text, "{} Hrs".format(scrape[5].text.split(' ')[0]))]
    return result, title, url


def GetPage(title):
    data = {
        'queryString': title,
        't': 'games',
        'sorthead': 'popular',
        'length_type': 'main'
    }
    return requests.post(HLTB_URL, data=data).text


def setup(client):
    client.add_cog(hltb(client))