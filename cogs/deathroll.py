import discord
from discord.ext import commands

from utils.misc import getNick

import random

START_VALUE = 133337

class DeathrollButton(discord.ui.Button['DeathRoll']):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.primary, label="DEATHROLL!!!")

    async def callback(self, interaction: discord.Interaction):
        view: DeathRoll = self.view
        if view.current_player == view.player1:
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
            if interaction.user == view.player1:
                return
            view.player2 = interaction.user
            view.current_player = view.player1
            content = f"## Deathroll\n{view.player1} vs. {view.player2}\n It's {view.current_player.mention}'s turn:"
            self.style = discord.ButtonStyle.success
            self.label = view.roll_value

        
        if view.roll_value == 1:
            loser = view.current_player
            content = f'{loser.mention} lost\nRolls:\n' + view.get_history_string()
            
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
        history_str = f'```\nStart: {START_VALUE}'
        for i in range(len(self.history)):
            history_str = history_str + f'{getNick(self.player1)}: {self.history[i]} '
            if i == 0:
                history_str = history_str + f'({round(self.history[i]/START_VALUE,3)*100}%)'
            else:
                history_str = history_str + f'({round(self.history[i]/self.history[i-1],3)*100}%)'
            history_str = history_str + '```'
        return history_str

class deathroll(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    @commands.guild_only()
    async def deathroll(self, ctx):
        await ctx.send(f'## Deathroll\n@everyone, who clicks the button and dares to deathroll against {ctx.author.mention}?', view=DeathRoll(ctx.author))

async def setup(client):
    await client.add_cog(deathroll(client))