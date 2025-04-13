import discord
from discord.ext import commands

from utils.misc import getNick, isDev

import random

START_VALUE = 1337
TEST = True
TEST_PLAYER = ""

class DeathrollButton(discord.ui.Button['DeathRoll']):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.primary, label="DEATHROLL!!!")

    async def callback(self, interaction: discord.Interaction):
        view: DeathRoll = self.view
        if view.current_player == view.player1:
            if not TEST:
                if interaction.user != view.player1:
                    return
            view.roll_value = random.randint(1, view.roll_value)
            view.history.append(view.roll_value)
            if view.roll_value > 1:
                view.current_player = view.player2
                self.style = discord.ButtonStyle.danger
            self.label = view.roll_value
            content = f"## Deathroll\n{getNick(view.player1)} vs. {getNick(view.player2)}\n{getNick(view.player1)} rolled a {view.roll_value}.\nIt's now {view.current_player.mention}'s turn:"

        elif view.current_player == view.player2:
            if not TEST:
                if interaction.user != view.player2:
                    return
            view.roll_value = random.randint(1, view.roll_value)
            view.history.append(view.roll_value)
            if view.roll_value > 1:
                view.current_player = view.player1
                self.style = discord.ButtonStyle.success
            self.label = view.roll_value
            content = f"## Deathroll\n{getNick(view.player1)} vs. {getNick(view.player2)}\n{getNick(view.player2)} rolled a {view.roll_value}.\nIt's now {view.current_player.mention}'s turn:"

        else:
            if not TEST:
                if interaction.user == view.player1:
                    return
                view.player2 = interaction.user
            else:
                view.player2 = TEST_PLAYER

            view.current_player = view.player1
            content = f"## Deathroll\n{view.player1} vs. {view.player2}\n It's {view.current_player.mention}'s turn:"
            self.style = discord.ButtonStyle.success
            self.label = view.roll_value

        
        if view.roll_value == 1:
            loser = view.current_player
            content = f'{loser.mention} lost\n{len(view.history)} Rolls:\n' + view.get_history_string()
            
            for child in view.children:
                child.disabled = True
            
            view.stop()
        
        await interaction.response.edit_message(content=content, view=view)

class DeathRoll(discord.ui.View):

    history = []

    def __init__(self, player):
        super().__init__(timeout=None)
        self.current_player = 'START'
        self.player1 = player
        self.player2 = None
        self.roll_value = START_VALUE
        self.add_item(DeathrollButton())
    
    def get_history_string(self):
        history_str = f'```\nStart: {START_VALUE}\n'
        for i in range(len(self.history)):
            if i % 2 == 0:
                player = self.player1
            else:
                player = self.player2
            history_str = history_str + f'{getNick(player)}: {self.history[i]} '
            if i == 0:
                history_str = history_str + f'({round(self.history[i]/START_VALUE*100,1)}%)\n'
            else:
                history_str = history_str + f'({round(self.history[i]/self.history[i-1]*100,1)}%)\n'
        history_str = history_str + '```'
        return history_str

class deathroll(commands.Cog):
    def __init__(self, client):
        self.client = client
        if TEST:
            global TEST_PLAYER
            guild = self.client.get_guild(405433814114893835)
            TEST_PLAYER = guild.get_member(706072542334550048)
            
    @commands.command()
    @commands.check(isDev)
    @commands.guild_only()
    async def deathroll(self, ctx):
        await ctx.send(f'## Deathroll\n@everyone, who clicks the button and dares to deathroll against {ctx.author.mention}?', view=DeathRoll(ctx.author))

    @commands.command()
    @commands.check(isDev)
    @commands.guild_only()
    async def drembed(self, ctx):
        endembed = discord.Embed(
            title="Deathroll",
            description="Player X lost!",
            colour=discord.Colour.dark_embed(),
        )
        endembed.set_thumbnail(url="https://c.tenor.com/F3qTVd9MfTgAAAAd/tenor.gif")
        endembed.add_field(name="Rolls: ` 6 `", value="", inline=False)
        endembed.add_field(name="Player1", value="` 133333 `\n\n` 111111 `\n\n`  88888 `", inline=True)
        endembed.add_field(name="Player2", value="\u200B\n` 122222 `\n\n`  99999 `\n\n`  77777 `", inline=True)
        endembed.add_field(name="%", value="` 95% `\n` 90% `\n` 80% `\n` 70% `\n` 90% `\n`  8% `", inline=True)
        

        await ctx.send(embeds=[endembed])
        




async def setup(client):
    await client.add_cog(deathroll(client))