from math import floor
import discord
from discord.ext import commands
from bs4 import BeautifulSoup
import aiohttp
import json
import re

HLTB_URL = 'https://howlongtobeat.com/'
HLTB_SEARCH = HLTB_URL + 'api/search/'
HLTB_REFERER = HLTB_URL


class hltb(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    @commands.guild_only()
    async def hltb(self, ctx, *, game):
        hltbResult = await HLTB(game)
        if hltbResult == -1:
            await ctx.send(f"Spiel {game} nicht gefunden.")
            return

        url = HLTB_URL + 'game/' + str(hltbResult['game_id'])

        embedHltb = discord.Embed(title=hltbResult['game_name'],
                                  url=url,
                                  colour=discord.Colour.from_rgb(255, 128, 0))
        embedHltb.set_thumbnail(url = HLTB_URL + 'games/' + hltbResult['image_url'])
        if hltbResult['flag_combine'] == 0 and hltbResult['flag_sp'] == 1:
            embedHltb.add_field(name='Main Story',
                                value=f"{hltbResult['comp_main']}",
                                inline=True)
            embedHltb.add_field(name='Main + Extra',
                                value=f"{hltbResult['comp_plus']}",
                                inline=True)
            embedHltb.add_field(name='Completionist',
                                value=f"{hltbResult['comp_100']}",
                                inline=True)

        else:
            if hltbResult['flag_combine'] & hltbResult['flag_sp']:
                embedHltb.add_field(name='Solo',
                                    value=f"{hltbResult['comp_all']}",
                                    inline=True)

            if hltbResult['flag_co']:
                embedHltb.add_field(name='Co-Op',
                                    value=f"{hltbResult['invested_co']}",
                                    inline=True)

            if hltbResult['flag_mp']:
                embedHltb.add_field(name='Vs.',
                                    value=f"{hltbResult['invested_mp']}",
                                    inline=True)

        await ctx.send(embed=embedHltb)

### Main Function ###
async def HLTB(title):
    data = await getHltbApiResponse(title)
    if data == -1:
        return -1

    hltbresult = {
        'game_name': data['game_name'],
        'game_id': data['game_id'],
        'comp_main': getTimeString(data['comp_main']),
        'comp_plus': getTimeString(data['comp_plus']),
        'comp_100': getTimeString(data['comp_100']),
        'comp_all': getTimeString(data['comp_all']),
        'invested_co': getTimeString(data['invested_co']),
        'invested_mp': getTimeString(data['invested_mp']),
        'flag_combine': data['comp_lvl_combine'],
        'flag_sp': data['comp_lvl_sp'],
        'flag_co': data['comp_lvl_co'],
        'flag_mp': data['comp_lvl_mp'],
        'image_url': data['game_image']
    }
    return hltbresult

def getRequestHeaders():
    headers = {
        'Content-type':
        'application/json',
        'accept': '*/*',
        'User-Agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36',
        'referer': HLTB_REFERER
    }
    return headers

def getRequestPayload(title):
    payload = {
        "searchType": "games",
        "searchTerms": title.split(),
        "searchPage": 1,
        "size": 5,
        "searchOptions": {
            "games": {
                "userId": 0,
                "platform": "",
                "sortCategory": "popular",
                "rangeCategory": "main",
                "rangeTime": {
                    "min": 0,
                    "max": 0
                },
                "gameplay": {
                    "perspective": "",
                    "flow": "",
                    "genre": "",
                    "subGenre": " "
                },
                'rangeYear':
                    {
                        'max': "",
                        'min': ""
                    },
                "modifier": ""
            },
            "users": {
                "sortCategory": "postcount"
            },
            "filter": "",
            "sort": 0,
            "randomizer": 0
        },
        "useCache": True
    }
    return json.dumps(payload)

    
async def getHltbApiResponse(title):
    headers = getRequestHeaders()
    payload = getRequestPayload(title)
    HLTB_KEY = await getHltbKey(False)
    if HLTB_KEY is None:
        HLTB_KEY = await getHltbKey(True)

    async with aiohttp.ClientSession() as session:
        async with session.post(HLTB_SEARCH + HLTB_KEY, data=payload, headers=headers) as r:
            if r is not None and r.status == 200:
                jsonresponse = await r.json()
                if not jsonresponse['data']:
                    return -1
                
                for index in range(len(jsonresponse['data'])):
                    if jsonresponse['data'][index]['game_name'] == title:
                        break
                
                if jsonresponse['data'][index]['game_name'] != title:
                    index = 0
                try:
                    r = jsonresponse['data'][index]
                except IndexError:
                    return -1
            else:
                r = None
        await session.close()
        return r

def getTimeString(timeInSeconds):
    if timeInSeconds == 0:
        return "-- Hrs"
    timeString = ""
    timeInHours = round(timeInSeconds / 3600 * 2) / 2
    timeString += str(floor(timeInHours))
    if timeInHours % 1 != 0:
        timeString += "½"
    timeString += " Hrs"
    return timeString

async def getHltbKey(parse_all: bool):
    headers = getRequestHeaders()
    async with aiohttp.ClientSession() as session:
        async with session.get(HLTB_URL, headers=headers) as r:
            if r is not None and r.status == 200:
                response = await r.text()
                soup = BeautifulSoup(response, 'html.parser')
                scripts = soup.find_all('script', src=True)
                if parse_all:
                    matching_scripts = [script['src'] for script in scripts]
                else:
                    matching_scripts = [script['src'] for script in scripts if '_app-' in script['src']]
                for script_url in matching_scripts:
                    script_url = HLTB_URL + script_url
                    async with aiohttp.ClientSession() as session:
                        async with session.get(script_url, headers = headers) as r_script:
                            if r_script is not None and r_script.status == 200:
                                response_script = await r_script.text()
                                pattern = r'"/api/search/".concat\("([a-zA-Z0-9]+)"\).concat\("([a-zA-Z0-9]+)"\)'
                                matches = re.findall(pattern, response_script)
                                key = matches[0][0]+matches[0][1]
                                return key
                            else:
                                return None
            else:
                return None

def setup(client):
    client.add_cog(hltb(client))
