import discord
from discord.ext import commands
import random
import os
import re
import aiohttp
from utils.misc import getMessageTime, sendLongMsg, getNick
import aiohttp
from math import factorial

repeat_dict = {}
asdfMention = False
asdfCombo = False
asdfReset = False
asdfList = []
DISCORD_EPOCH = 1420070400000

redditpattern = re.compile(r'[^\/\w](r\/\w+)|^(r\/\w+)')
calcpattern = re.compile(r'[0-9\+\-\*\/\(\).% ,^!]*')
factorialpattern = r'\d+!'


class skills(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.youtube_key = os.environ['YOUTUBE_KEY']
        self.tenor_key = os.environ['TENOR_KEY']

    # Calculator
    @commands.command()
    @commands.guild_only()
    async def calc(self, ctx, *, calcString):
        '''calculates the result of your expression'''
        result = self.doCalculate(calcString)
        if result != None:
            await ctx.send(result)

    def doCalculate(self, calcStr):
        # erlaube Zeichen: 0-9 + - * / ( ) . %   , ^ !
        matches = calcpattern.fullmatch(calcStr)
        if matches:
            try:
                # Komma zu Dezimalpunkt und ^ zu ** ändern
                calcStr = calcStr.replace(",", ".")
                calcStr = calcStr.replace("^", "**")
                # RegEx Suche für faktoriell
                f_matches = re.findall(factorialpattern, calcStr)
                for f_match in f_matches:
                    calcStr = calcStr.replace(f_match, 'factorial('+ f_match[:-1]+')')
                
                result = eval(calcStr,
                              {'__builtins__': None},{'factorial':factorial})
                if result % 1 == 0:
                    r = f'{int(result):,}'.replace(",", " ")
                else:
                    r = f'{round(float(result), 8):,.8f}'.rstrip('0').rstrip(
                        '.').replace(",", " ")
                if len(str(r)) > 2000:
                    r = "https://i.imgur.com/C38uPeQ.jpg"
            except SyntaxError:
                r = 'I glaub des is a Bledsinn'
            except ValueError:
                r = "https://i.imgur.com/C38uPeQ.jpg"
            except:
                r = '🤷'

        #    return r
        else:
            r = 'Keine gültige Berechnung!'

        return r

    # On Message Listener
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.client.user or message.author.bot or message.channel.type == "private":
            return

        # Triple repeat
        '''repeats the message if the same message was sent three times in a row by unique authors'''
        author_list = []
        global repeat_dict

        if message.channel.id in repeat_dict:
            comparison_message = str(repeat_dict[message.channel.id][0])
            author_list = repeat_dict[message.channel.id][1]
            if message.content.lower() == comparison_message.lower():
                if message.author.id not in author_list:
                    author_list.append(message.author.id)
                    if len(author_list) == 3:
                        repeat_dict.pop(message.channel.id, None)
                        await message.channel.send(message.content)
            else:
                repeat_dict.update({
                    message.channel.id: [message.content, [message.author.id]]
                })
        else:
            repeat_dict.update(
                {message.channel.id: [message.content, [message.author.id]]})

        # Reddit Link
        global redditpattern
        matches = redditpattern.findall(message.content)
        if matches:
            reddit = 'https://www.reddit.com/'
            for match in matches:
                for entry in match:
                    if entry:
                        url = reddit + entry + '/'
                        await message.channel.send(url)

    # Dice Roll
    @commands.command(aliases=['rand', 'dice', 'roll'])
    @commands.guild_only()
    async def random(self, ctx, *arg):
        '''returns a random number
    instructions:
    -----------
    !random
        return a random number between 1 and 100
    !random coin
        throw a coin (heads or tails)
    !random 6
        return a random number between 1 and 6
    !random 10 20
        return a random number between 10 and 20
    '''
        if ctx.invoked_subcommand is None:
            if not arg:
                start = 1
                end = 100
            elif arg[0] == 'flip' or arg[0] == 'coin':
                coin = ['heads', 'tails']
                await ctx.send('{0}'.format(random.choice(coin)))
                return
            elif len(arg) == 1:
                start = 1
                end = int(arg[0])
            elif len(arg) > 1:
                start = int(arg[0])
                end = int(arg[1])
            await ctx.send('({0} - {1}): {2}'.format(
                start, end, random.randint(start, end)))

    # Youtube video search
    @commands.command()
    @commands.guild_only()
    async def yt(self, ctx, *, searchterm=None):
        '''returns a youtube video related to the search string'''
        if searchterm is None:
            await ctx.message.add_reaction('🥚')
            await ctx.message.add_reaction('👏')
            await ctx.send("Und wonach soll ich jetzt suchen, du Heisl?")
        else:
            await ctx.send(await self.searchVideo(searchterm))

    async def searchVideo(self, searchterm):
        url = "https://www.googleapis.com/youtube/v3/search"
        payload = {
            'key': self.youtube_key,
            'q': searchterm,
            'part': 'snippet',
            'maxResults': 1,
            'safeSearch': 'none',
            'type': 'video'
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=payload) as r:
                if r.status == 200:
                    json = await r.json()
                    video_id = json['items'][0]['id']['videoId']
                    video_url = ('https://youtube.com/watch?v=' + video_id)
                    return video_url

    # Tenor GIF search
    @commands.command()
    @commands.guild_only()
    async def gif(self, ctx, *, searchterm=None):
        '''returns a gif related to the search string'''
        if searchterm is None:
            await ctx.message.add_reaction('🥚')
            await ctx.message.add_reaction('👏')
            await ctx.send("Und wonach soll ich jetzt suchen, du Heisl?")
        else:
            await ctx.send(f'{await self.searchGif(searchterm)}')

    async def searchGif(self, searchterm):
        url = "https://api.tenor.com/v1/search"
        payload = {
            'key': self.tenor_key,
            'q': searchterm,
            'limit': 1,
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=payload) as r:
                if r.status == 200:
                    json = await r.json()

        try:
            gif_url = json['results'][0]['media'][0]['gif']['url']
        except:
            gif_url = 'I find\' nix!'
        return gif_url

    # Message recap with miliseconds timestamp
    '''returns x last messages filtered by specified content and miliseconds timestamp
    or a message by id with its timestamp
  '''

    @commands.command()
    @commands.guild_only()
    async def recap(self, ctx, *args):

        # Set up search depth and filter keyword based on input
        if not args:
            depth = 5
            filter = None
        else:
            try:
                depth = int(args[0])
                if (len(args) > 1):
                    filter = ' '.join(args[1:len(args)])
                else:
                    filter = None
            except:
                filter = ' '.join(args)
                depth = 15

        # Recap for a single message by sending the id
        async with ctx.channel.typing():
            if depth > 100000:
                message = await ctx.channel.fetch_message(depth)
                time = getMessageTime(
                    message.id).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                author = getNick(message.author)
                content = message.content
                r = (f'```\n[{time}] {author}: {content}```')
                await sendLongMsg(ctx, r)
                return

            # Exit early if the result most likely be too long
            if depth > 30 and filter is None:
                await ctx.message.add_reaction('🥚')
                await ctx.message.add_reaction('👏')
                await ctx.send("Na. Zu viel, zu zach. :meh:")
                return

            r = '```\n'

            messages = [message async for message in ctx.channel.history(limit=depth + 1)]
            result_found = False

            # Loop through messages and build response string (based on filter)
            for message in reversed(messages[1:]):
                if filter is not None:
                    if filter.lower() not in message.content.lower():
                        continue
                time = getMessageTime(
                    message.id).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                author = getNick(message.author)
                if message.content == '' and len(message.attachments) > 0:
                    content = f'[{len(message.attachments)} attachment(s)]'
                else: 
                    content = message.content
                if '```' in content:
                    content = content.replace('```', '')
                    content = content.replace('[', '--- [')
                    r += (f'[{time}] {author}: {content}\n')
                    continue

                r += (f'[{time}] {author}: {content}\n')
                result_found = True

            r += '```'
        if result_found:
            try:
                await ctx.send(r)
            except:
                await ctx.message.add_reaction('🥚')
                await ctx.message.add_reaction('👏')
                await ctx.send(
                    "pls no - das sind mehr als 2000 Zeichen. :weary:")
        else:
            await ctx.send(
                "Das Nichts nichtet. <:affenkaktus:709677325846839346>")

    # Wrap a code block around the input text
    @commands.command()
    @commands.guild_only()
    async def cb(self, ctx, *, arg):
        embed = discord.Embed(colour=discord.Colour.orange(),
                              description=f'```{arg}```')
        if ctx.author.nick == None:
            name = ctx.author.name
        else:
            name = ctx.author.nick
        embed.set_author(name=name, icon_url=ctx.author.display_avatar)
        await ctx.send(embed=embed)
        await ctx.message.delete()

    # Return timestamp of a Discord Snowflake
    @commands.command()
    @commands.guild_only()
    async def timestamp(self, ctx, *, snowflake):
        isInt = True
        try:
            snowflake = int(snowflake)
        except:
            isInt = False
        if isInt == False:
            r = "Muss eine ganze Zahl sein."
        elif snowflake < 4194304 or snowflake > 100000000000000000000:
            r = "Schaut nicht nach ner gültigen ID aus."
        else:
            time = getMessageTime(snowflake).strftime(
                "%Y-%m-%d %H:%M:%S.%f")[:-3]
            r = (f'```ID: {snowflake}\n{time}```')
        await ctx.send(r)


async def setup(client):
    await client.add_cog(skills(client))