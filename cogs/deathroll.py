import os
import io
import discord
from discord.ext import commands

from utils.misc import getNick, getTimezone
from utils.db import check_connection, init_db
from utils.deathrollgifs import gifdict

import random
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.colors import LinearSegmentedColormap
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
                                                              interaction.message.id,
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
            colour=discord.Colour.dark_embed()
        )
        embed.set_image(url=self.get_deathroll_gif(start=True))
        embed.add_field(
            name=f'**{getNick(self.player1)} vs. {getNick(self.player2)}**', value=f"{self.current_player.mention} start rolling!")

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
            colour=discord.Colour.dark_embed()
        )
        embed.set_image(url=self.get_deathroll_gif())
        embed.add_field(
            name=f'**{getNick(self.player1)} vs. {getNick(self.player2)}**', value=f"Roll #{len(self.history)-1} - {getNick(player_roll)} rolled **{self.roll_value}**. ({int(self.roll_value/self.history[-2]*1000)/10}% of {self.history[-2]})\n\nNext roll: {player_next.mention}")

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

    @commands.command(aliases=['dr'])
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

    def store_deathroll_to_db(self, channelid, messageid, player1id, player2id, sequence, winner, loser):
        now = datetime.now(tz=getTimezone())
        rolls = len(sequence)-1
        sequence_str = '|'.join(str(x) for x in sequence)
        query = ('INSERT INTO `deathroll_history` (datetime, channel, message, player1, player2, sequence, rolls, winner, loser) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)')
        data = (now, channelid, messageid, player1id, player2id,
                sequence_str, rolls, winner, loser)

        # Check DB connection
        self.cnx = check_connection(self.cnx)
        self.cursor = self.cnx.cursor(buffered=True)
        # Execute query
        self.cursor.execute(query, data)
        self.cnx.commit()

        # return .lastrowid to show the id in the Embed footer
        return self.cursor.lastrowid

    # Global Deathroll stats
    @commands.group(aliases=['drstats'], invoke_without_command=True)
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
            title=f'Global Deathroll Stats',
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

    # Individual Deathroll stats
    @deathrollstats.command(name='player')
    @commands.guild_only()
    async def deathrollstats_player(self, ctx):
        # Check DB connection
        self.cnx = check_connection(self.cnx)
        self.cursor = self.cnx.cursor(buffered=True)
        # Grab all records
        query = (
            f'SELECT datetime, channel, message, player1, player2, sequence, rolls, winner, loser FROM deathroll_history')
        df = pd.read_sql(query, con=self.cnx)
        self.cnx.commit()
        self.cnx.close()

        # Calculations
        player_id = ctx.author.id

        # Filter dataframe to only games with that player
        player_games = df[
            (df['player1'] == player_id) | (
                df['player2'] == player_id)
        ].copy()
        # 1. Total games, wins, losses
        total_games = len(player_games)
        total_wins = (df['winner'] == player_id).sum()
        total_losses = total_games - total_wins

        # 2. Calculate Win Percentage
        if total_games == 0:
            win_percentage = 0.0
        else:
            win_percentage = (total_wins / total_games) * 100
        win_percentage = '{:.0f}%'.format(win_percentage)

        # 3. Calculate roll stats
        total_rolls = player_games['rolls'].sum()
        average_rolls = player_games['rolls'].mean()
        average_rolls = '{:.1f}'.format(average_rolls)
        max_rolls = player_games['rolls'].max()
        min_rolls = player_games['rolls'].min()

        # 4. Calculate top opponents
        # Most games played against
        player_games['opponent'] = player_games.apply(
            lambda row: row['player2'] if row['player1'] == player_id else row['player1'],
            axis=1
        )
        opponent_counts = player_games['opponent'].value_counts()
        top_opponent_id = opponent_counts.idxmax()
        top_opponent = ctx.guild.get_member(top_opponent_id)
        # output fields
        top_opponent_name = getNick(top_opponent)
        top_opponent_count = opponent_counts.max()

        # Most wins against
        wins_df = player_games[player_games['winner'] == player_id]
        wins_vs_counts = wins_df['opponent'].value_counts()
        wins_vs_opponent_id = wins_vs_counts.idxmax()
        wins_vs_opponent = ctx.guild.get_member(wins_vs_opponent_id)
        # output fields
        wins_vs_opponent_name = getNick(wins_vs_opponent)
        wins_vs_opponent_count = wins_vs_counts.max()

        # Most losses against
        losses_df = player_games[player_games['loser'] == player_id]
        losses_vs_counts = losses_df['opponent'].value_counts()
        losses_vs_opponent_id = losses_vs_counts.idxmax()
        losses_vs_opponent = ctx.guild.get_member(losses_vs_opponent_id)
        # output fields
        losses_vs_opponent_name = getNick(losses_vs_opponent)
        losses_vs_opponent_count = losses_vs_counts.max()

        # 5. Calculate lowest % roll
        # Calculate Minimum Sequence Ratio
        all_player_ratios = []
        biggest_loss_numbers = []
        for index, game_row in player_games.iterrows():
            sequence_str = game_row.get('sequence')
            p1_id = game_row['player1']
            p2_id = game_row['player2']
            loser_id = game_row['loser']
            is_player_loser = (loser_id == player_id)

            if not isinstance(sequence_str, str) or not sequence_str:
                continue  # Skip if sequence is not a valid string

            seq_numbers = [float(n) for n in sequence_str.split('|')]

            num_elements = len(seq_numbers)

            # Determine player assignment rule based on loser and length
            is_odd_length = (num_elements % 2 != 0)
            p1_gets_odd_indices = (loser_id == p2_id and is_odd_length) or \
                (loser_id == p1_id and not is_odd_length)

            # Calculate ratios where the target player owns the current number
            for i in range(1, num_elements):
                prev_num = seq_numbers[i-1]
                curr_num = seq_numbers[i]

                # Determine owner of the current number (at index i)
                # 0-based index i means 1st element is even, 2nd is odd, etc.
                index_is_odd = (i % 2 != 0)
                # If p1 gets odd indices (1, 3, 5..) and current index i is odd -> p1 owns it
                # If p1 gets even indices (0, 2, 4..) and current index i is even -> p1 owns it
                current_owner_is_p1 = (p1_gets_odd_indices == index_is_odd)
                current_owner_id = p1_id if current_owner_is_p1 else p2_id

                # If the target player owns the current number, calculate and store ratio
                if current_owner_id == player_id:
                    ratio = curr_num / prev_num
                    all_player_ratios.append(ratio)

            if is_player_loser:
                second_last_str = sequence_str.split('|')[-2]
                second_last_num = int(second_last_str)
                biggest_loss_numbers.append(second_last_num)

        # Find the biggest loss
        biggest_loss = max(biggest_loss_numbers)

        # Find the minimum ratio
        min_ratio = min(all_player_ratios) * 100
        min_ratio = '{:.2f}%'.format(min_ratio)

        # Adjust player name depending on ending (Klaus')
        player_name = getNick(ctx.author)
        if player_name.endswith('s'):
            player_name += "'"
        else:
            player_name += "'s"

        drPlayerStatsEmbed = discord.Embed(
            title=f'{player_name} Deathroll Stats',
            colour=discord.Colour.from_rgb(220, 20, 60))
        drPlayerStatsEmbed.set_thumbnail(
            url='https://cdn.discordapp.com/attachments/723670062023704578/1363260251339620352/unnamed.png?ex=6805628c&is=6804110c&hm=b0156321aa65223c6cf1ae1664756bcb1b6efb85a6260c79570ca67f16faf5e5&')

        # Construct embed with links
        drPlayerStatsEmbed.add_field(name=f'Total games: {total_games}',
                                     value=f'Record: ({total_wins}-{total_losses}), {win_percentage} won\n\n'
                                     + f'**Total rolls: {total_rolls}**\n'
                                     + f'Average: {average_rolls}\n'
                                     + f'Most rolls: {max_rolls} , fewest: {min_rolls}\n\n'
                                     + f'**Opponents**\n'
                                     + f'Top rival: **{top_opponent_name}**, {top_opponent_count} played\n'
                                     + f'Top victim: **{wins_vs_opponent_name}**, {wins_vs_opponent_count} won\n'
                                     + f'Top nemesis: **{losses_vs_opponent_name}**, {losses_vs_opponent_count} lost\n\n'
                                     + f'**Special stats**\n'
                                     + f'Biggest loss: from **{biggest_loss}** down to **1**, propz! \n'
                                     + f'Lowest % roll: **{min_ratio}**')

        await ctx.send(embed=drPlayerStatsEmbed)
    
    # Deathroll Charts
    @deathrollstats.command(name='charts')
    @commands.guild_only()
    async def deathrollstats_charts(self, ctx):
        # Check DB connection
        self.cnx = check_connection(self.cnx)
        self.cursor = self.cnx.cursor(buffered=True)
        # Grab all records
        query = (
            f'SELECT datetime, channel, message, player1, player2, sequence, rolls, winner, loser FROM deathroll_history')
        df = pd.read_sql(query, con=self.cnx)
        self.cnx.commit()
        self.cnx.close()

        # COLOR configs for plots:
        figbg_c = '#121214'
        bar_c = '#0969a1'
        label_c = '#82838b'
        pie_c = ['#3c9f3c', '#9f3c3c']
        vs_colors = [(0, '#9f3c3c'), (0.25, '#9f3c3c'), (0.5, '#9f9f3c'), (0.75, '#3c9f3c'), (1, '#3c9f3c')]
        # Create Figure with subplots
        fig, [(ax1, ax2), (ax3, ax4)] = plt.subplots(2, 2, figsize=(12, 12), facecolor=figbg_c)
        #fig, (ax1, ax3) = plt.subplots(1, 2, figsize=(12, 6), facecolor=figbg_c)
        
        # Data for Barplot
        df_grouped = df\
            .groupby(["rolls"])\
            .agg(count = ("rolls", "count"))\
            .reset_index()
        
        max_rolls = df_grouped['rolls'].max()
        df_barplot = df_grouped
        for i in range(1,max_rolls+2):
            if not (df_grouped['rolls'] == i).any():
                df_append = pd.DataFrame([[i, 0]], columns=['rolls','count'])
                df_barplot = pd.concat([df_barplot, df_append])
        df_barplot = df_barplot.sort_values('rolls').reset_index(drop=True)

        # Barplot
        ax1.bar(df_barplot['rolls'], df_barplot['count'], color=bar_c, edgecolor='none')
        ax1.set_xlabel('rolls', color=label_c)
        ax1.set_ylabel('count', color=label_c)
        ax1.set_title('How many rolls?', color=label_c)
        ax1.tick_params(axis='x', colors=label_c)
        ax1.tick_params(axis='y', colors=label_c)
        ax1.set_xticks(range(1, max_rolls + 1))
        ax1.yaxis.set_major_locator(ticker.MultipleLocator(1))
        ax1.set_facecolor(figbg_c)
        ax1.grid(color=label_c, linestyle='-', linewidth=0.5, alpha=0.5)
        ax1.spines[:].set_color(label_c)
        ax1.set_xlim(xmin=0, xmax=max_rolls+1)

        # Data for Pie Chart
        df_start = df
        df_start['starting_player'] = df_start.apply(self.determine_starting_player, axis=1)
        game_count = len(df_start)
        start_wins = len(df_start[df_start['winner']==df_start['starting_player']])
        second_wins = game_count - start_wins

        pie_labels = ['starting\nplayer','second\nplayer']
        pie_data = [start_wins, second_wins]

        # Pie Chart
        ax2.pie(pie_data, labels=pie_labels, autopct='%1.1f%%', startangle=90, colors=pie_c, explode=(0.01, 0.01))
        ax2.set_title('Winning pct. starting vs. second player', color=label_c)
        ax2.set_facecolor(figbg_c)
        ax2.axis('equal')
        for text in ax2.texts:
            text.set_color(label_c)
            if '%' in text.get_text():
                text.set_color('black')
                text.set_fontsize(16)

        # Data for Duels HeatMap
        df_duels = df
        players = sorted(list(set(df['player1']) | set(df['player2'])))
        results = []
        for player1 in players:
            for player2 in players:
                if player1 != player2:
                    # Filtere den DataFrame, um nur die Spiele zwischen den aktuellen Spielern zu berücksichtigen
                    df_filtered = df_duels[((df_duels['player1'] == player1) & (df_duels['player2'] == player2)) |
                                    ((df_duels['player1'] == player2) & (df_duels['player2'] == player1))]

                    # Berechne die Anzahl der Siege für Spieler1
                    wins = len(df_filtered[df_filtered['winner'] == player1])
                    # Berechne die Anzahl der Niederlagen für Spieler1
                    losses = len(df_filtered[df_filtered['loser'] == player1])

                    # Berechne die Siegquote
                    if (wins + losses) > 0:
                        win_percentage = wins / (wins + losses)
                        results.append({'Spieler1': player1, 'Spieler2': player2, 'Siege': wins, 'Niederlagen': losses, 'Siegquote': win_percentage})
                    else:
                        results.append({'Spieler1': player1, 'Spieler2': player2, 'Siege': 0, 'Niederlagen': 0, 'Siegquote': np.nan})
        # Erstelle ein DataFrame aus der Ergebnisliste
        win_loss_df = pd.DataFrame(results)
        # Erstelle eine Pivot-Tabelle, um die Siegquoten für jedes Spielerpaar zu erhalten
        win_loss_pivot = win_loss_df.pivot(index='Spieler1', columns='Spieler2', values='Siegquote')

        # Heatmap
        # Definiere die benutzerdefinierte Colormap
        cmap_name = 'vs_colormap'
        cm = LinearSegmentedColormap.from_list(cmap_name, vs_colors, N=100)

        ax3.imshow(win_loss_pivot, cmap=cm, interpolation='nearest', vmin=0, vmax=1)
        # Füge die Spielernamen als Beschriftungen hinzu
        player_labels = []
        for player in players:
            player_usr = ctx.guild.get_member(player)
            player_labels.append(getNick(player_usr))

        ax3.set_xticks(np.arange(len(players)), player_labels, color=label_c)
        ax3.set_yticks(np.arange(len(players)), player_labels, color=label_c)

        for i, player1 in enumerate(players):
            for j, player2 in enumerate(players):
                if i == j:  #Diagonalelemente schwarz färben
                    ax3.text(j, i, 'X', ha='center', va='center', color=label_c)
                    ax3.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1, facecolor=figbg_c, edgecolor='none'))
                elif np.isnan(win_loss_pivot.iloc[i, j]):
                    ax3.text(j, i, '-', ha='center', va='center', color=label_c)
                    ax3.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1, facecolor='#1a1a1e', edgecolor='none'))
                else:
                    # Finde die Siege und Niederlagen für das Spielerpaar
                    wins = win_loss_df.loc[(win_loss_df['Spieler1'] == player1) & (win_loss_df['Spieler2'] == player2), 'Siege'].values[0]
                    losses = win_loss_df.loc[(win_loss_df['Spieler1'] == player1) & (win_loss_df['Spieler2'] == player2), 'Niederlagen'].values[0]
                    ax3.text(j, i, f"{win_loss_pivot.iloc[i, j]:.0%}\n({wins} - {losses})", ha='center', va='center', color='black')

        # Turn spines off and create white grid.
        ax3.spines[:].set_visible(False)
        ax3.set_facecolor(figbg_c)
        ax3.set_xticks(np.arange(win_loss_pivot.shape[1]+1)-.5, minor=True)
        ax3.set_yticks(np.arange(win_loss_pivot.shape[0]+1)-.5, minor=True)
        ax3.xaxis.set_tick_params(which='major', color=label_c)
        ax3.yaxis.set_tick_params(which='major', color=label_c)
        ax3.grid(which="minor", color=figbg_c, linestyle='-', linewidth=3)
        ax3.tick_params(which="minor", top=False, left=False)
        ax3.set_title('Duels', color=label_c)
        ax3.xaxis.tick_top()

        # Data for Lineplot
        df_line = df
        def calculate_reduction_ratios_from_string(sequence_string):
            rolls = [int(roll) for roll in sequence_string.split('|')]
            ratios = []
            previous_roll = rolls[0]
            for i in range(1, len(rolls)):
                current_roll = rolls[i]
                if previous_roll > 0:
                    ratio = current_roll / previous_roll
                    ratios.append(ratio)
                    previous_roll = current_roll
                else:
                    ratios.append(np.nan)
            return ratios

        df_line['reduction_ratios'] = df_line['sequence'].apply(calculate_reduction_ratios_from_string)
        # Erstellen einer Liste, um die durchschnittlichen Reduktionsfaktoren für jeden Wurf zu speichern
        average_reductions_per_roll_number = {}

        # Iteriere durch jede Spielsequenz
        for ratios in df_line['reduction_ratios']:
            for i, ratio in enumerate(ratios):
                roll_number = i + 1
                if roll_number not in average_reductions_per_roll_number:
                    average_reductions_per_roll_number[roll_number] = []
                if not np.isnan(ratio):
                    average_reductions_per_roll_number[roll_number].append(ratio)

        # Berechne den Durchschnitt für jeden Wurf
        average_reductions = {roll: np.mean(ratios) for roll, ratios in average_reductions_per_roll_number.items()}

        # Sortiere das Dictionary nach der Anzahl der Würfe
        sorted_averages = dict(sorted(average_reductions.items()))
        
        # Lineplot
        ax4.plot(sorted_averages.keys(), sorted_averages.values(), marker='o', linestyle='-')
        ax4.set_facecolor(figbg_c)
        ax4.set_xlabel('roll #', color=label_c)
        ax4.set_ylabel('Avg. Reduction Factor', color=label_c)
        ax4.set_title('Avg. Reduction of Number Range per Roll', color=label_c)
        ax4.xaxis.set_tick_params(which='major', color=label_c)
        ax4.yaxis.set_tick_params(which='major', color=label_c)
        ax4.grid(True, alpha=0.5, color=label_c)
        ax4.spines[:].set_color(label_c)
        ax4.tick_params(axis='x', colors=label_c)
        ax4.tick_params(axis='y', colors=label_c)
        ax4.set_xticks(np.arange(1, max(sorted_averages.keys()) + 1))
        ax4.set_yticks(np.linspace(0, 1, 11, endpoint=True))
        ax4.set_xlim(xmin=0.5, xmax=max(sorted_averages.keys())+0.5)
        ax4.set_ylim(ymin=0, ymax=1)

        plt.tight_layout(pad=1.08, h_pad=5, w_pad=5)
        # Save the plot to a BytesIO object
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=400)
        buffer.seek(0)

        discord_charts = discord.File(buffer, filename='dr_charts.png')
        plt.close(fig)

        drChartsEmbed = discord.Embed(
            title='Deathroll Charts',
            colour=discord.Colour.from_rgb(220, 20, 60)
        )
        drChartsEmbed.set_image(url="attachment://dr_charts.png")
        await ctx.send(file=discord_charts, embed=drChartsEmbed)


    # Takes a row of deathroll_history DataFrame and returns the ID of the starting player
    def determine_starting_player(self, row):
        if row['rolls'] % 2 != 0:
            return row['loser']
        else:
            return row['winner']
        
async def setup(client):
    await client.add_cog(deathroll(client))
