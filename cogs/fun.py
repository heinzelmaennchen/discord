import discord
from discord.ext import commands
import asyncio
import random
import os
from utils.misc import isDevServer, sendLongMsg
from utils.bobbybquotes import bbquotes


class fun(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    @commands.guild_only()
    async def richtig(self, ctx):
        await ctx.send('richtig richtig richtfest!')

    @commands.command()
    @commands.guild_only()
    async def falsch(self, ctx):
        await ctx.send('falsch falsch Falschgeld!')

    @commands.command()
    @commands.guild_only()
    async def twss(self, ctx):
        await ctx.send('That\'s what she said.')

    @commands.command()
    @commands.guild_only()
    async def läuft(self, ctx):
        await ctx.send('läuft')
        await ctx.send('läuft')
        await ctx.send('lohnt')

    @commands.command()
    @commands.guild_only()
    async def gehackt(self, ctx):
        await ctx.send(':boom: GESPRENGT :boom:')

    @commands.command(hidden=True)
    @commands.guild_only()
    async def easteregg(self, ctx):
        await ctx.send('Das easteregg ist ...')
        await asyncio.sleep(5)
        await ctx.message.add_reaction('🥚')
        await ctx.message.add_reaction('👏')
        await ctx.send('... jebaitet!')

    @commands.command()
    @commands.guild_only()
    async def billig(self, ctx):
        await ctx.send('Billig? Ja.\nMisstrauisch? Ja.\nBerechtigt? Ja')

    @commands.command()
    @commands.guild_only()
    async def rip(self, ctx, *, arg):
        embedRip = discord.Embed()
        embedRip.colour = discord.Colour.from_rgb(0, 0, 0)
        embedRip.title = f':pray: :coffin: :pray:   RIP {arg}   :pray: :coffin: :pray:'
        embedRip.set_image(
            url=
            'https://media.tenor.com/images/29ed9c8ea3a979f3628c23a13ea9366a/tenor.gif'
        )
        await ctx.send(embed=embedRip)

    # Marblelympics commands
    @commands.command()
    @commands.guild_only()
    async def ducks(self, ctx):
        await ctx.send(
            '<:gd_marble:571396561045684224> <:ducks:571352498590318592> <:gd_marble:571396561045684224> **#QUACKATTACK** <:gd_marble:571396561045684224> <:ducks:571352498590318592> <:gd_marble:571396561045684224>'
        )

    @commands.command()
    @commands.guild_only()
    async def my(self, ctx):
        await ctx.send(
            '<:my:573452977726029835> #KEEPITMELLOW <:my:573452977726029835>')

    @commands.command()
    @commands.guild_only()
    async def ss(self, ctx):
        await ctx.send(
            '<:ss_marble:571398818378285071> <:ss:571396511204900881> :100: :fire: :massage: #SPEEDISKEY :massage: :fire: :100: <:ss:571396511204900881> <:ss_marble:571398818378285071>'
        )

    @commands.command()
    @commands.guild_only()
    async def tg(self, ctx):
        await ctx.send(
            '<:galacticballs:572766585593266206><:galactic2:572764693203124224>#ReachForTheStars<:galactic2:572764693203124224><:galacticballs:572766585593266206>'
        )

    @commands.command()
    @commands.guild_only()
    async def emojilist(self, ctx):
        serverId = 156040097819525120
        server = self.client.get_guild(serverId)
        server = ctx.guild
        emojis = await server.fetch_emojis()

        output = '```\n'
        for emoji in emojis:
            if emoji.animated:
                output += f'<a:{emoji.name}:{emoji.id}+>\n'
            else:
                output += f'<:{emoji.name}:{emoji.id}+>\n'
        output += '```'
        await sendLongMsg(ctx, output)

    # Good bot, bad bot, thx bot
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.client.user or message.author.bot or message.channel.type == "private":
            return

        msg = message.content.lower()
        cleanMsg = cleanupString(msg)

        if ('good bot' in msg or 'bot best' in msg):
            await message.channel.send(':smiling_face_with_3_hearts:')
        elif ('bad bot' in msg or 'scheiss bot' in msg or 'scheiß bot' in msg
              or 'shit bot' in msg or 'huren bot' in msg):
            await message.channel.send(':F')
        elif ('thx bot' in msg or 'danke bot' in msg):
            await message.channel.send('<a:meh:563687194351501340>')
        elif 'conan' in msg:
            await message.channel.send(
                'https://youtube.com/watch?v=Oo9buo9Mtos')
        elif 'antrag' in cleanMsg.split(
        ) and not 'abgelehnt' in cleanMsg.split():
            await message.channel.send('Antrag ... abgelehnt! ❌')
        elif 'rino' in cleanMsg.split() and (message.channel.id
                                             == 156040097819525120
                                             or isDevServer(message)):
            user = await self.client.fetch_user(int(os.environ['RINO_ID']))
            embed = discord.Embed(colour=discord.Colour.from_rgb(47, 49, 54))
            embed.set_author(name="Rino", icon_url=user.avatar_url)
            embed.description = "Bin gleich da."
            await message.channel.send(embed=embed)
        elif 'peda' in cleanMsg.split() and (message.channel.id
                                             == 156040097819525120
                                             or isDevServer(message)):
            strList = [
                'cool bist!',
                'leute besorgts zeug ich will mich zu pufffffffen',
                'willst du meine du mich heirante?',
                'Gratulation {0.mention}! du bist die KUA des Jahres!!!!!'
            ]
            embed = discord.Embed(colour=discord.Colour.from_rgb(47, 49, 54))
            embed.set_author(
                name="Peda",
                icon_url="https://cdn.discordapp.com/embed/avatars/2.png")
            embed.description = random.choice(strList).format(message.author)
            await message.channel.send(embed=embed)
        elif 'bobby b' in msg or 'bobby-b' in msg or 'bobbyb' in msg:
            embed = discord.Embed(colour=discord.Colour.from_rgb(47, 49, 54))
            embed.set_author(name="Bobby B.",
                             icon_url="https://i.imgur.com/GHvm2Xs.png")
            embed.description = random.choice(bbquotes)
            await message.channel.send(embed=embed)
        elif ('obi wan' in msg or 'kenobi' in msg):
            await message.channel.send(
                'https://giphy.com/gifs/mrw-top-escalator-Nx0rz3jtxtEre')
        elif 'bruce lee' in msg:
            await message.channel.send('https://youtu.be/nOodKRhf59s')
        elif 'alf' in cleanMsg.split():
            await message.channel.send('https://youtu.be/sGs6gSrvrhY')
        elif 'succulent' in cleanMsg.split():
            await message.channel.send('https://youtu.be/XebF2cgmFmU')


    # Re-Add bot reaction if it gets deleted
    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        if user != self.client.user:
            return
        else:
            await reaction.message.add_reaction(reaction.emoji)
    
    # Re-Add bot-reactions if they get cleared
    @commands.Cog.listener()
    async def on_reaction_clear(self, message, reactions):
        for reaction in reactions:
            if reaction.me:
                await reaction.message.add_reaction(reaction.emoji)


def cleanupString(text):
    chars = ".,?!"  # chars which get replaced by a space
    for c in chars:
        if c in text:
            text = text.replace(c, ' ')
    return text


def setup(client):
    client.add_cog(fun(client))
