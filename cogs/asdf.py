import discord
from discord.ext import commands
import asyncio
import json
from utils.misc import getMessageTime
from utils.db import check_connection
from utils.db import init_db

asdfMention = False
asdfCombo = False
asdfReset = False
asdfList = []
DISCORD_EPOCH = 1420070400000


class asdf(commands.Cog):
    def __init__(self, client):
        self.client = client

        self.cnx = init_db()
        self.cursor = self.cnx.cursor(buffered=True)

    @commands.command()
    @commands.guild_only()
    async def asdf(self, ctx):
        '''1337!!!'''
        await ctx.send('@everyone Verachtung!!! Guade lupe uiuiui')

    # On Message Listener
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.client.user or message.author.bot or message.channel.type == "private":
            return

    # asdf check
        if message.channel.id == 405433814547169301 or message.channel.id == 705617951440633877 or message.channel.id == 156040097819525120:
            # BOT DEV Channels and #wlc
            time = getMessageTime(message)
            global asdfReset
            if time.hour == 13 and time.minute >= 35 and time.minute <= 38:
                # Check if active
                if asdfReset == False:
                    asdfReset = True
                    asyncio.create_task(self.startReset(time.minute))
                await self.checkHolyRules(message, time.minute)

    async def startReset(self, minute):
        dt = (39 - minute) * 60
        await asyncio.sleep(dt)
        global asdfMention
        global asdfCombo
        global asdfReset
        global asdfList
        asdfMention = False
        asdfCombo = False
        asdfReset = False
        asdfList.clear()

    async def checkHolyRules(self, message, minute):
        global asdfMention
        global asdfCombo
        global asdfList
        # '!asdf'
        if message.content.lower() == '!asdf':
            if minute == 36 or minute == 37:
                if asdfCombo == True:
                    await self.enforceRules(message)
                else:
                    asdfMention = True
            else:
                await self.enforceRules(message)
        # 'asdf'
        elif message.content.lower() == 'asdf':
            if minute != 37:
                await self.enforceRules(message)
            elif asdfMention == False:
                asdfMention = True
                asdfCombo = True
                if message.author.id not in asdfList:
                    asdfList.append(message.author.id)
                    self.addAsdfPoint(str(message.author.id))
                await self.enforceRules(message)
            elif asdfMention == True:
                asdfCombo = True
                if message.author.id not in asdfList:
                    asdfList.append(message.author.id)
                    self.addAsdfPoint(str(message.author.id))
        # '<anything else>'
        else:
            if minute == 37 and asdfCombo == True:
                await self.enforceRules(message)

    # Enforce the rules by adding Eierklatscher and a fail point
    async def enforceRules(self, message):
        await message.add_reaction('🥚')
        await message.add_reaction('👏')
        self.addFailPoint(str(message.author.id))

    # Add an asdf fail point to the user's stats and deduct xp
    def addFailPoint(self, user):
        with open('storage/asdf.json') as json_file:
            jsonAsdfData = json.load(json_file)
        if user in jsonAsdfData['fails']['user']:
            jsonAsdfData['fails']['user'][user] = int(
                jsonAsdfData['fails']['user'][user]) + 1
        else:
            jsonAsdfData['fails']['user'][user] = 1
        with open('storage/asdf.json', 'w') as json_file:
            json.dump(jsonAsdfData, json_file, indent=4, ensure_ascii=True)

        # self.setBonusXp(user, True) TODO: remove comment when bonus goes live

    # Add an asdf point to the user's stats and add bonus xp
    def addAsdfPoint(self, user):
        global asdfList
        with open('storage/asdf.json') as json_file:
            jsonAsdfData = json.load(json_file)
        if user in jsonAsdfData['asdf']['user']:
            jsonAsdfData['asdf']['user'][user] = int(
                jsonAsdfData['asdf']['user'][user]) + 1
        else:
            jsonAsdfData['asdf']['user'][user] = 1
        with open('storage/asdf.json', 'w') as json_file:
            json.dump(jsonAsdfData, json_file, indent=4, ensure_ascii=True)

        # self.setBonusXp(user, False) TODO: remove comment when bonus goes live

    # List asdf fails
    @commands.command(aliases=['lf'])
    @commands.guild_only()
    async def listfails(self, ctx):
        with open('storage/asdf.json') as json_file:
            jsonAsdfData = json.load(json_file)
        fails = 0
        r = ''
        asdfEmbed = discord.Embed(title='FAIL ranking',
                                  colour=discord.Colour.from_rgb(125, 25, 25))
        for u, f in sorted(jsonAsdfData['fails']['user'].items(),
                           key=lambda item: item[1],
                           reverse=True):
            fails += f
            user = ctx.guild.get_member(int(u))
            if user.nick == None:
                user = user.name
            else:
                user = user.nick
            r += f'{user}: {f}\n'
        asdfEmbed.add_field(name=f'**Gesamt: {fails}**', value=r)
        if fails == 0:
            await ctx.send('```Noch keine fails ... bis jetzt.```')
        else:
            await ctx.send(embed=asdfEmbed)

    # List asdf stats
    @commands.command(aliases=['la'])
    @commands.guild_only()
    async def listasdf(self, ctx):
        with open('storage/asdf.json') as json_file:
            jsonAsdfData = json.load(json_file)
        asdf = 0
        r = ''
        asdfEmbed = discord.Embed(title='ASDF ranking',
                                  colour=discord.Colour.from_rgb(25, 100, 25))
        for u, a in sorted(jsonAsdfData['asdf']['user'].items(),
                           key=lambda item: item[1],
                           reverse=True):
            asdf += a
            user = ctx.guild.get_member(int(u))
            if user.nick == None:
                user = user.name
            else:
                user = user.nick
            r += f'{user}: {a}\n'

        asdfEmbed.add_field(name=f'**Gesamt: {asdf}**', value=r)
        if asdf == 0:
            await ctx.send('```Noch keine asdfs ... bis jetzt.```')
        else:
            await ctx.send(embed=asdfEmbed)

    # Update xp in the database - remove for fail, add for bonus
    def setBonusXp(self, user, bonus):
        # Check DB connection
        self.cnx = check_connection(self.cnx)
        self.cursor = self.cnx.cursor(buffered=True)
        # Grab the author's record
        query = (f'SELECT author, xp FROM levels WHERE author = {user.id}')
        self.cursor.execute(query)
        self.cnx.commit()

        row = self.cursor.fetchone()
        if bonus:
            new_xp = row[1] + 1337
        else:
            if row[1] < 1337:
                new_xp = 0
            else:
                new_xp = row[1] - 1337

        query = (f'UPDATE `levels` SET `xp`={new_xp} WHERE author = {user.id}')
        self.cursor.execute(query)
        self.cnx.commit()


def setup(client):
    client.add_cog(asdf(client))