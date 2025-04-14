import discord
from discord.ext import commands

from utils.misc import getNick, isDev, getTimezone
from utils.db import check_connection, init_db

import random
from datetime import datetime

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
                    await interaction.response.send_message(content=f"Du bist nicht {getNick(view.player1)}", ephemeral=True, delete_after=30)
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
                    await interaction.response.send_message(content=f"Du bist nicht {getNick(view.player2)}", ephemeral=True, delete_after=30)
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
                    await interaction.response.send_message(content="Du kannst nicht gegen dich selbst spielen!\nWarte auf einen Gegner.", ephemeral=True, delete_after=30)
                    return
                view.player2 = interaction.user
            else:
                view.player2 = TEST_PLAYER

            view.current_player = view.player1
            self.style = discord.ButtonStyle.success
            self.label = view.roll_value
            embed = view.get_deathroll_start_embed()
        
        # roll == 1 -> Game Ends. Generate Embed and store game to db
        if view.roll_value == 1:
            # who won, who lost
            view.loser = view.current_player
            if view.player1 == view.loser:
                view.winner = view.player2
            else:
                view.winner = view.player1
            # disable Button
            for child in view.children:
                child.disabled = True
            if not TEST:
                # store to db and generate Embed
                try:
                    lastrow = deathroll.store_deathroll_to_db(view.cog,
                                                    interaction.channel_id,
                                                    view.player1.id,
                                                    view.player2.id,
                                                    view.history,
                                                    view.winner.id,
                                                    view.loser.id)
                except Exception as e:
                    embed = view.get_deathroll_end_embed(db_lastrow=None, db_exception=e)
                else:
                    embed = view.get_deathroll_end_embed(db_lastrow=lastrow, db_exception=None)
            else:
                embed = view.get_deathroll_end_embed()
            view.stop()
        
        await interaction.response.edit_message(content=None, embed=embed, view=view)


class DeathRoll(discord.ui.View):
    def __init__(self, cog, player):
        super().__init__(timeout=None)
        self.cog = cog
        self.current_player = 'START'
        self.player1 = player
        self.player2 = None
        self.winner = None
        self.loser = None
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
        embed.set_thumbnail(url=self.get_deathroll_gif())
        embed.add_field(name="\u200B", value=f"{getNick(player_roll)} rolled a **{self.roll_value}**. ({round(self.roll_value/self.history[-2]*100,1)}% of {self.history[-2]})\nIt's now {player_next.mention}'s turn:")
        
        return embed
    
    def get_deathroll_end_embed(self, db_lastrow = None, db_exception = None):
        embed_value = ""
        value_width = len(str(self.history[1]))
        if len(getNick(self.player2)) > len(getNick(self.player1)):
            player_width = len(getNick(self.player2))
        else:
            player_width = len(getNick(self.player1))

        for i in range(1, len(self.history)):
            if i % 2 == 1:
                embed_value = embed_value + f'`{getNick(self.player1).ljust(player_width)}:` `{str(self.history[i]).rjust(value_width)}` `{str(round(self.history[i]/self.history[i-1]*100,1)).rjust(5)}%`\n'
            else:
                embed_value = embed_value + f'`{getNick(self.player2).ljust(player_width)}:` `{str(self.history[i]).rjust(value_width)}` `{str(round(self.history[i]/self.history[i-1]*100,1)).rjust(5)}%`\n'
        
        # winner or loser get's mentioned in the end_embed, win used in get_deathroll_gif to select a fitting thumbnail
        win = random.choice([True, False])
        if win:
            embed_desc = f"{self.winner.mention} won!"
        else:
            embed_desc = f"{self.loser.mention} lost!"
        
        embed = discord.Embed(
            title="Deathroll concluded",
            description=embed_desc,
            colour=discord.Colour.dark_embed()
        )
        embed.set_thumbnail(url=self.get_deathroll_gif(win))
        embed.add_field(name=f'Rolls: ` {len(self.history)-1} `', value=embed_value, inline=False)
        if db_exception is not None:
            embed.set_footer(text=f'Error occured during storing this game to db:\n{db_exception}')
        if db_lastrow is not None:
            embed.set_footer(text=f'Game stored to db (id: {db_lastrow})')

        return embed
    
    def get_deathroll_gif(self, winner=None):
        
        gifdict = {
            'bigloss': ['https://c.tenor.com/0YKj8P76e98AAAAd/tenor.gif', 
                        'https://c.tenor.com/WvotbqtvuRUAAAAd/tenor.gif', 
                        'https://c.tenor.com/mU8Le3LX3MEAAAAd/tenor.gif'],
            'highroll': ['https://c.tenor.com/y0pu4r01MXkAAAAd/tenor.gif', 
                         'https://c.tenor.com/Ho6Eh52Aw50AAAAd/tenor.gif', 
                         'https://c.tenor.com/RWmF33lS6_UAAAAd/tenor.gif'],
            'leet': ['https://c.tenor.com/yt-NsmpTN54AAAAd/tenor.gif', 
                     'https://c.tenor.com/IE_r1q13XpUAAAAd/tenor.gif', 
                     'https://c.tenor.com/aMO9r7Pq19AAAAAd/tenor.gif'],
            'loser': ['https://c.tenor.com/RearbC1HzewAAAAd/tenor.gif', 
                      'https://c.tenor.com/OUn0kZK9dB0AAAAd/tenor.gif', 
                      'https://c.tenor.com/1fpEjOn5W3QAAAAd/tenor.gif', 
                      'https://c.tenor.com/YMz2WAFV-GcAAAAd/tenor.gif', 
                      'https://c.tenor.com/eTqdoJ96YP4AAAAd/tenor.gif', 
                      'https://c.tenor.com/85iMZeffHQYAAAAC/tenor.gif', 
                      'https://c.tenor.com/Eo_uafpjWDMAAAAC/tenor.gif'],
            'lowroll': ['https://c.tenor.com/JbNlXxXl91QAAAAd/tenor.gif', 
                        'https://c.tenor.com/aWUHvMsuYFkAAAAd/tenor.gif', 
                        'https://c.tenor.com/e_vPwqBG5WUAAAAC/tenor.gif'],
            'roll': ['https://c.tenor.com/_f47EOhUYLQAAAAd/tenor.gif', 
                     'https://c.tenor.com/InKwoemL4EAAAAAd/tenor.gif', 
                     'https://c.tenor.com/5PepR8rD4U0AAAAd/tenor.gif', 
                     'https://c.tenor.com/qeyYUP1MXJMAAAAd/tenor.gif', 
                     'https://c.tenor.com/nVFR4jC3GZwAAAAd/tenor.gif'],
            'whew': ['https://c.tenor.com/OsBUnbQbfsEAAAAC/tenor.gif', 
                     'https://c.tenor.com/8gE5vCt_XIoAAAAC/tenor.gif', 
                     'https://c.tenor.com/Li11L5d4GakAAAAC/tenor.gif', 
                     'https://c.tenor.com/D4TuNIn61aEAAAAd/tenor.gif', 
                     'https://c.tenor.com/NqhZNESuzusAAAAC/tenor.gif'],
            'winner': ['https://c.tenor.com/Zx4EYt-kXmMAAAAd/tenor.gif', 
                       'https://c.tenor.com/nwY77jVH52oAAAAC/tenor.gif', 
                       'https://c.tenor.com/MTGiVk7eL9gAAAAC/tenor.gif', 
                       'https://c.tenor.com/Z2HxUamVZTMAAAAd/tenor.gif', 
                       'https://c.tenor.com/9mUqamN2SOIAAAAC/tenor.gif', 
                       'https://c.tenor.com/xlhV0tC8tMUAAAAd/tenor.gif', 
                       'https://c.tenor.com/1WQApj0YBeUAAAAd/tenor.gif']
        }

        new_roll = self.history[-1]
        prev_roll = self.history[-2]
        percentage_difference = new_roll/prev_roll

        # Check if the deathroll ended and return a winner or loser gif
        if winner == False and prev_roll <= 10:
            return random.choice(gifdict['loser'])
        if winner == True:
            return random.choice(gifdict['winner'])

        # Check for 2
        if new_roll == 2:
            return random.choice(gifdict['whew'])

        # Check for 1337 or 13337
        if new_roll in (1337, 13337):
            return random.choice(gifdict['leet'])

        # Check for big drop down to 1
        if prev_roll > 10 and new_roll == 1:
            return random.choice(gifdict['bigloss'])

        # Check for small difference
        if percentage_difference > 0.99:
            return random.choice(gifdict['lowroll'])

        # Check for big difference
        if percentage_difference < 0.02:
           return random.choice(gifdict['highroll'])

        # If nothing interesting happens, return roll gif
        return random.choice(gifdict['roll'])
  
class deathroll(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.cnx = init_db()

        if TEST:
            global TEST_PLAYER
            guild = self.client.get_guild(405433814114893835)
            TEST_PLAYER = guild.get_member(706072542334550048)
            
    @commands.command()
    @commands.check(isDev)
    @commands.guild_only()
    async def deathroll(self, ctx):
        await ctx.send(f'## Deathroll\n@everyone, who clicks the button and dares to deathroll against {ctx.author.mention}?', view=DeathRoll(self, ctx.author))

    
    def store_deathroll_to_db(self, channelid, player1id, player2id, sequence, winner, loser):
        now = datetime.now(tz=getTimezone())
        rolls = len(sequence)-1
        sequence_str = '|'.join(str(x) for x in sequence)
        query = ('INSERT INTO `deathroll_history` (datetime, channel, player1, player2, sequence, rolls, winner, loser) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)')
        data = (now, channelid, player1id, player2id, sequence_str, rolls, winner, loser)
        
        # Check DB connection
        self.cnx = check_connection(self.cnx)
        self.cursor = self.cnx.cursor(buffered=True)
        # Execute query
        self.cursor.execute(query, data)
        self.cnx.commit()
        
        return self.cursor.lastrowid    # return .lastrowid to show the id in the Embed footer


async def setup(client):
    await client.add_cog(deathroll(client))