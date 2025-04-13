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
        embed = None
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
            embed = view.get_deathroll_game_embed()

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
            embed = view.get_deathroll_game_embed()

        else:
            if not TEST:
                if interaction.user == view.player1:
                    return
                view.player2 = interaction.user
            else:
                view.player2 = TEST_PLAYER

            view.current_player = view.player1
            self.style = discord.ButtonStyle.success
            self.label = view.roll_value
            embed = view.get_deathroll_start_embed()
        
        if view.roll_value == 1:
            loser = view.current_player
            for child in view.children:
                child.disabled = True
            embed = view.get_deathroll_end_embed()
            view.stop()
        
        await interaction.response.edit_message(content=None, embed=embed, view=view)


class DeathRoll(discord.ui.View):
    def __init__(self, player):
        super().__init__(timeout=None)
        self.current_player = 'START'
        self.player1 = player
        self.player2 = None
        self.roll_value = START_VALUE
        self.history = [START_VALUE]
        self.add_item(DeathrollButton())
    
    def get_deathroll_start_embed(self):
        embed = discord.Embed(
            title = "Deathroll",
            description = f'**{getNick(self.player1)} vs. {getNick(self.player2)}**',
            colour=discord.Colour.dark_embed()
        )
        embed.set_thumbnail(url="https://c.tenor.com/I7QkHH-wak4AAAAd/tenor.gif")
        embed.add_field(name="\u200B", value=f"{self.player1.mention} start rolling!")

        return embed
    
    def get_deathroll_game_embed(self):
        if self.current_player == self.player1:
            player_roll = self.player2
            player_next = self.player1
        else:
            player_roll = self.player1
            player_next = self.player2
        
        embed = discord.Embed(
            title = "Deathroll",
            description = f'**{getNick(self.player1)} vs. {getNick(self.player2)}**',
            colour=discord.Colour.dark_embed()
        )
        embed.set_thumbnail(url="https://c.tenor.com/Li11L5d4GakAAAAd/tenor.gif")
        embed.add_field(name="\u200B", value=f"{getNick(player_roll)} rolled a **{self.roll_value}**. ({round(self.roll_value/self.history[-2]*100,1)}% of {self.history[-2]})\nIt's now {player_next.mention}'s turn:")
        
        return embed
    
    def get_deathroll_end_embed(self):
        p1_value = ""
        p2_value = "\u200B"
        pct_value = ""

        value_width = len(str(self.history[1]))

        for i in range(1, len(self.history)):
            if i % 2 == 1:
                p1_value = p1_value + f'` {str(self.history[i]).rjust(value_width)} `\n'
                p2_value = p2_value + "\n"
            else:
                p1_value = p1_value + "\n"
                p2_value = p2_value + f'` {str(self.history[i]).rjust(value_width)} `\n' 
            pct_value = pct_value + f'` {str(round(self.history[i]/self.history[i-1]*100,1)).rjust(5)}% `\n'

        embed = discord.Embed(
            title="Deathroll concluded",
            description=f"{self.current_player.mention} lost!",
            colour=discord.Colour.dark_embed()
        )
        embed.set_thumbnail(url="https://c.tenor.com/F3qTVd9MfTgAAAAd/tenor.gif")
        embed.add_field(name=f'Rolls: ` {len(self.history)-1} `', value="", inline=False)
        embed.add_field(name=getNick(self.player1), value=p1_value, inline=True)
        embed.add_field(name=getNick(self.player2), value=p2_value, inline=True)
        embed.add_field(name="%", value=pct_value, inline=True)

        return embed


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



    # TEST EMBEDS BEGIN ===============================================================================================

    @commands.command()
    @commands.check(isDev)
    @commands.guild_only()
    async def drembed(self, ctx):
        history = [133337, 105784, 75545, 74123, 68914, 24133, 7085, 1337, 223, 147, 53, 22, 13, 5, 3, 2, 1]
        player1 = "Stefan"
        player2 = "Benny"

        value_width = len(str(history[1]))

        p1_value = ""
        p2_value = "\u200B"
        pct_value = ""
        for i in range(1, len(history)):
            if i % 2 == 1:
                p1_value = p1_value + f'` {str(history[i]).rjust(value_width)} `\n'
                p2_value = p2_value + "\n"
            else:
                p1_value = p1_value + "\n"
                p2_value = p2_value + f'` {str(history[i]).rjust(value_width)} `\n' 
            pct_value = pct_value + f'` {str(round(history[i]/history[i-1]*100,1)).rjust(4)}% `\n'

        endembed = discord.Embed(
            title="Deathroll",
            description=f"{player1} lost!",
            colour=discord.Colour.dark_embed(),
        )
        endembed.set_thumbnail(url="https://c.tenor.com/F3qTVd9MfTgAAAAd/tenor.gif")
        endembed.add_field(name=f'Rolls: ` {len(history)-1} `', value="", inline=False)
        endembed.add_field(name=player1, value=p1_value, inline=True)
        endembed.add_field(name=player2, value=p2_value, inline=True)
        endembed.add_field(name="%", value=pct_value, inline=True)

        playembed = discord.Embed(
            title="Deathroll",
            #description="Player1 vs. Player2\nPlayer1 rolled a ###.\nIt's now {Player2's.mention} turn:"
            description="**Player1 vs. Player2**"
        )
        playembed.set_thumbnail(url="https://c.tenor.com/Li11L5d4GakAAAAd/tenor.gif")
        playembed.add_field(name="\u200B", value="Player1 rolled a ###. (xx.x% of OLDVALUE)\nIt's now {Player2's.mention} turn:")

        await ctx.send(embeds=[playembed, endembed])
        
    # TEST EMBEDS END =================================================================================================



async def setup(client):
    await client.add_cog(deathroll(client))