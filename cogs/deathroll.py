import os
import discord
from discord.ext import commands

from utils.misc import getNick, getTimezone
from utils.db import check_connection, init_db
from utils.deathrollgifs import gifdict

import random
import pandas as pd
import ast
from datetime import datetime

START_VALUE = 133337
TEST = False
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
                    await interaction.response.send_message(content=f"Du bist nicht {getNick(view.player1)}", ephemeral=True, delete_after=10)
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
                    await interaction.response.send_message(content=f"Du bist nicht {getNick(view.player2)}", ephemeral=True, delete_after=10)
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
                if view.player2 != None and interaction.user != view.player2:
                    await interaction.response.send_message(content=f"{getNick(view.player2)} wurde herausgefordert. Nicht du, du Heisl!", ephemeral=True, delete_after=10)
                    return
                if interaction.user == view.player1:
                    await interaction.response.send_message(content="Du kannst nicht gegen dich selbst spielen!\nWarte auf einen Gegner.", ephemeral=True, delete_after=10)
                    return
                if view.player2 == None:
                    view.player2 = interaction.user
            else:
                if view.player2 != None and interaction.user != view.player2:
                    await interaction.response.send_message(content=f"{getNick(view.player2)} wurde herausgefordert. Nicht du, du Heisl!", ephemeral=True, delete_after=10)
                    return
                view.player2 = TEST_PLAYER

            # Randomize starting player
            currentplayer = random.choice([view.player1, view.player2])
            if currentplayer == view.player1:
                view.current_player = view.player1
                self.style = discord.ButtonStyle.success
            else:
                view.current_player = view.player2
                self.style = discord.ButtonStyle.danger
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
                    embed = view.get_deathroll_end_embed(
                        db_lastrow=None, db_exception=e)
                else:
                    embed = view.get_deathroll_end_embed(
                        db_lastrow=lastrow, db_exception=None)
            else:
                embed = view.get_deathroll_end_embed()
            view.stop()

        await interaction.response.edit_message(content=None, embed=embed, view=view)


class DeathRoll(discord.ui.View):
    def __init__(self, cog, player, challenged_user):
        super().__init__(timeout=None)
        self.cog = cog
        self.current_player = 'START'
        self.player1 = player
        self.player2 = challenged_user
        self.winner = None
        self.loser = None
        self.roll_value = START_VALUE
        self.history = [START_VALUE]
        self.add_item(DeathrollButton())

    # START EMBED
    def get_deathroll_start_embed(self):
        embed = discord.Embed(
            title="Deathroll",
            description=f'**{getNick(self.player1)} vs. {getNick(self.player2)}**',
            colour=discord.Colour.dark_embed()
        )
        embed.set_image(url=self.get_deathroll_gif(start=True))
        embed.add_field(
            name="\u200B", value=f"{self.current_player.mention} start rolling!")

        return embed

    # GAME EMBED
    def get_deathroll_game_embed(self):
        if self.current_player == self.player1:
            player_roll = self.player2
            player_next = self.player1
        else:
            player_roll = self.player1
            player_next = self.player2

        embed = discord.Embed(
            title="Deathroll",
            description=f'**{getNick(self.player1)} vs. {getNick(self.player2)}**',
            colour=discord.Colour.dark_embed()
        )
        embed.set_image(url=self.get_deathroll_gif())
        embed.add_field(
            name="\u200B", value=f"{getNick(player_roll)} rolled **{self.roll_value}**. ({int(self.roll_value/self.history[-2]*1000)/10}% of {self.history[-2]})\n\nNext roll: {player_next.mention}")

        return embed

    # END EMBED
    def get_deathroll_end_embed(self, db_lastrow=None, db_exception=None):
        embed_value = ""
        value_width = len(str(self.history[1]))
        if len(getNick(self.player2)) > len(getNick(self.player1)):
            player_width = len(getNick(self.player2))
        else:
            player_width = len(getNick(self.player1))

        # Calculate starting player and second player from length of roll history
        rolls = len(self.history)-1
        if rolls % 2 == 1:
            starting_player = self.loser
            second_player = self.winner
        else:
            starting_player = self.winner
            second_player = self.loser

        for i in range(1, len(self.history)):
            if i % 2 == 1:
                player = starting_player
            else:
                player = second_player
            embed_value = embed_value + \
                f'` {getNick(player).ljust(player_width)}: ` ` {str(self.history[i]).rjust(value_width)} ` ` {str(int(self.history[i]/self.history[i-1]*1000)/10).rjust(5)}% `\n'

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
        embed.set_image(url=self.get_deathroll_gif(winner=win))
        embed.add_field(
            name=f'Rolls: ` {len(self.history)-1} `', value=embed_value, inline=False)
        if db_exception is not None:
            embed.set_footer(
                text=f'Error occured during storing this game to db:\n{db_exception}')
        if db_lastrow is not None:
            embed.set_footer(text=f'Game stored to db (id: {db_lastrow})')

        return embed

    def get_deathroll_gif(self, start=False, winner=None):

        # Check if the deathroll starts and return a starter gif
        # must before definition of prev_roll because index out of range
        if start:
            return random.choice(gifdict['start'])

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
            guild = self.client.get_guild(
                int(ast.literal_eval(os.environ['GUILD_IDS'])['dev']))
            TEST_PLAYER = guild.get_member(706072542334550048)

    @commands.command()
    @commands.guild_only()
    async def deathroll(self, ctx):
        if len(ctx.message.mentions) == 0:
            await ctx.send(f'## Deathroll\n@here, who clicks the button and dares to deathroll against {ctx.author.mention}?', view=DeathRoll(self, ctx.author, None))
        else:
            if ctx.author == ctx.message.mentions[0]:
                await ctx.reply(f'-# Du kannst dich nicht selbst herausfordern.', ephemeral=True)
            elif not ctx.message.mentions[0].bot:
                await ctx.send(f'## Deathroll\n{ctx.author.mention} challenged {ctx.message.mentions[0].mention}!', view=DeathRoll(self, ctx.author, ctx.message.mentions[0]))
            else:
                await ctx.reply(f'-# Du kannst keinen Bot herausfordern.', ephemeral=True)

    def store_deathroll_to_db(self, channelid, player1id, player2id, sequence, winner, loser):
        now = datetime.now(tz=getTimezone())
        rolls = len(sequence)-1
        sequence_str = '|'.join(str(x) for x in sequence)
        query = ('INSERT INTO `deathroll_history` (datetime, channel, player1, player2, sequence, rolls, winner, loser) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)')
        data = (now, channelid, player1id, player2id,
                sequence_str, rolls, winner, loser)

        # Check DB connection
        self.cnx = check_connection(self.cnx)
        self.cursor = self.cnx.cursor(buffered=True)
        # Execute query
        self.cursor.execute(query, data)
        self.cnx.commit()

        # return .lastrowid to show the id in the Embed footer
        return self.cursor.lastrowid

    @commands.command()
    @commands.guild_only()
    async def deathrollstats(self, ctx):
        # Check DB connection
        self.cnx = check_connection(self.cnx)
        self.cursor = self.cnx.cursor(buffered=True)
        # Grab all records
        query = (
            f'SELECT datetime, channel, message, player1, player2, sequence, rolls, winner, loser FROM deathroll_history')
        df = pd.read_sql(query, con=self.cnx)
        self.cnx.commit()
        self.cnx.close()

        drStatsEmbed = discord.Embed(
            title=f'Deathroll Global Stats',
            colour=discord.Colour.from_rgb(220, 20, 60))
        drStatsEmbed.set_thumbnail(
            url='https://cdn.discordapp.com/attachments/723670062023704578/1362911780313108611/unnamed.png?ex=68041e02&is=6802cc82&hm=cb5879590b96bbbd69476fc88ff355e07dc9cdcdbfc27adafde77abe1bf31df3&')

        global_games = len(df)

        # Find the index (label) of the row with the maximum and the row with the minimum value in the 'rolls' column
        idx_max_rolls = df['rolls'].idxmax()
        idx_min_rolls = df['rolls'].idxmin()

        # Retrieve the entire rows using the indices found
        row_with_max_rolls = df.loc[idx_max_rolls]
        row_with_min_rolls = df.loc[idx_min_rolls]

        # Extract the 'rolls' values from these rows
        max_rolls = row_with_max_rolls['rolls']
        min_rolls = row_with_min_rolls['rolls']

        # Construct jump_urls
        guild_id = int(ast.literal_eval(os.environ['GUILD_IDS'])['default'])

        max_roll_channel = row_with_max_rolls['channel']
        max_roll_message = row_with_max_rolls['message']
        max_roll_jump_url = 'https://discord.com/channels/' + \
            str(guild_id) + '/' + str(max_roll_channel) + \
            '/' + str(max_roll_message)

        min_roll_channel = row_with_min_rolls['channel']
        min_roll_message = row_with_min_rolls['message']
        min_roll_jump_url = 'https://discord.com/channels/' + \
            str(guild_id) + '/' + str(min_roll_channel) + \
            '/' + str(min_roll_message)

        # Calculate win percentage ranking
        all_players = pd.concat([df['player1'], df['player2']])
        games_played = all_players.value_counts()
        games_won = df['winner'].value_counts()
        games_lost = df['loser'].value_counts()
        player_stats = pd.DataFrame(
            {'total_games': games_played, 'total_wins': games_won, 'total_losses': games_lost})
        player_stats['total_wins'] = player_stats['total_wins'].fillna(
            0).astype(int)
        player_stats['total_losses'] = player_stats['total_losses'].fillna(
            0).astype(int)
        player_stats['win_percentage'] = (
            player_stats['total_wins'] / player_stats['total_games']) * 100
        ranked_players = player_stats.sort_values(
            by='win_percentage', ascending=False)
        ranked_players_reset = ranked_players.reset_index(names='player_id')
        output_df = ranked_players_reset[[
            'player_id', 'win_percentage', 'total_games', 'total_wins', 'total_losses']]

        # Create a copy to modify for final display
        output_df_formatted = output_df.copy()

        # Format output fields
        output_df_formatted['player_name'] = output_df_formatted['player_id'].apply(
            ctx.guild.get_member).apply(getNick)
        output_df_formatted['win_percentage'] = output_df_formatted['win_percentage'].map(
            '{:.0f}%'.format)
        output_df_formatted['player_record'] = output_df_formatted.apply(
            lambda row: f"({row['total_wins']}-{row['total_losses']})",
            axis=1
        )

        # Construct final dataframe for output
        final_df = output_df_formatted[[
            'player_name', 'win_percentage', 'player_record']]

        # Construct embed with links
        drStatsEmbed.add_field(name=f'**Total # of games: {global_games}**',
                            value=f'**Most rolls: [{max_rolls}]({max_roll_jump_url})**\n'
                            + f'**Fewest rolls: [{min_rolls}]({min_roll_jump_url})**\n\n'
                            + final_df.to_string(index=False, header=False))

        await ctx.send(embed=drStatsEmbed)

async def setup(client):
    await client.add_cog(deathroll(client))
