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
import matplotlib.ticker as mticker
import matplotlib.path as mpath
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
import ast
import math
from datetime import datetime

START_VALUE = 133337
TEST = False
TEST_PLAYER = ""

# Helper function to format numbers (int if whole, else float/string)


def format_num(num, decimals=0):
    if num is None or (isinstance(num, float) and (math.isnan(num) or math.isinf(num))):
        return "N/A"
    if isinstance(num, (int, float)):
        if abs(num - round(num)) < 1e-9:
            return str(int(round(num)))
        return f"{num:.{decimals}f}"
    return str(num)

# Helper function to safely get nickname


def get_nick_safe(ctx, player_id):  # Pass ctx now
    if player_id is None or pd.isna(player_id):
        return "N/A"
    try:
        int_player_id = int(player_id)  # Ensure int for lookup
        member = ctx.guild.get_member(int_player_id)
        return getNick(member) if member else f"ID: {int_player_id}"
    except (ValueError, TypeError):
        return f"ID: {player_id}"


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

            # BOT GAME - Bot rolls immediately after Player1
            if view.botgame and view.roll_value > 1:
                view.roll_value = random.randint(1, view.roll_value)
                view.history.append(view.roll_value)
                if view.roll_value > 1:
                    view.current_player = view.player1
                    self.style = discord.ButtonStyle.success

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
                if view.player2 != None and interaction.user != view.player2 and not view.botgame:
                    await interaction.response.send_message(content=f"{getNick(view.player2)} wurde herausgefordert. Nicht du, du Heisl!", ephemeral=True, delete_after=10)
                    return
                if not view.botgame:
                    view.player2 = TEST_PLAYER

            # Randomize starting player
            currentplayer = random.choice([view.player1, view.player2])
            if currentplayer == view.player2 and view.botgame:
                # BOT Game & Bot Starting ... rolls already first time
                view.roll_value = random.randint(1, view.roll_value)
                view.history.append(view.roll_value)
                view.current_player = view.player1
                if view.roll_value == 1:
                    # If Bot loses with first roll change current_player back to Bot for correct loser handling
                    view.current_player = view.player2
                self.style = discord.ButtonStyle.success

            elif currentplayer == view.player1:
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

        # Check if Deathroll message is in last X messages of the channel
        channel = interaction.message.channel
        history = [message async for message in channel.history(limit=3)]
        if interaction.message in history:
            await interaction.response.edit_message(content=None, embed=embed, view=view)
        else:
            await interaction.response.defer()
            await interaction.message.delete()
            await interaction.channel.send(content=None, embed=embed, view=view)


class DeathRoll(discord.ui.View):
    def __init__(self, cog, player, challenged_user):
        super().__init__(timeout=None)
        self.cog = cog
        self.current_player = 'START'
        self.player1 = player
        self.player2 = challenged_user
        self.botgame = challenged_user == cog.client.user
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
        if self.botgame and len(self.history) == 2:
            # BOT Game and Bot started already
            embed.set_image(url=self.get_deathroll_gif())
            embed.add_field(
                name=f'**{getNick(self.player1)} vs. {getNick(self.player2)}**', value=f"{getNick(self.player2)} started.\nRoll #{len(self.history)-1} - {getNick(self.player2)} rolled **{self.roll_value}**. ({int(self.roll_value/self.history[-2]*1000)/10}% of {self.history[-2]})\n\nNext roll: {self.player1.mention}")
        else:
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
        if not self.botgame:
            embed.add_field(
                name=f'**{getNick(self.player1)} vs. {getNick(self.player2)}**', value=f"Roll #{len(self.history)-1} - {getNick(player_roll)} rolled **{self.roll_value}**. ({int(self.roll_value/self.history[-2]*1000)/10}% of {self.history[-2]})\n\nNext roll: {player_next.mention}")
        else:
            embed.add_field(
                name=f'**{getNick(self.player1)} vs. {getNick(self.player2)}**', value=f"Roll #{len(self.history)-2} - {getNick(self.player1)} rolled **{self.history[-2]}**. ({int(self.history[-2]/self.history[-3]*1000)/10}% of {self.history[-3]})\nRoll #{len(self.history)-1} - {getNick(player_roll)} rolled **{self.roll_value}**. ({int(self.roll_value/self.history[-2]*1000)/10}% of {self.history[-2]})\n\nNext roll: {player_next.mention}")
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

        # Check for 300
        if new_roll == 300:
            return random.choice(gifdict['300'])

        # Check for 69
        if new_roll == 69:
            return random.choice(gifdict['69'])

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
            elif not ctx.message.mentions[0].bot or ctx.message.mentions[0] == self.client.user:
                text = f'## Deathroll\n{ctx.author.mention} challenged {ctx.message.mentions[0].mention}!'
                if ctx.message.mentions[0] == self.client.user:
                    text += f'\n{getNick(ctx.author)} click the Button to start the game vs. {getNick(ctx.message.mentions[0])}'
                await ctx.send(text, view=DeathRoll(self, ctx.author, ctx.message.mentions[0]))
            else:
                await ctx.reply(f'-# Du kannst diesen Bot nicht herausfordern.', ephemeral=True)

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
        self.cnx.close()

        # Number of games
        global_games = len(df)

        # --- Basic Global Roll Stats ---
        # Ensure 'rolls' is numeric first
        df['rolls'] = pd.to_numeric(df['rolls'], errors='coerce')
        # Work with rows that have valid rolls
        valid_rolls_df = df.dropna(subset=['rolls'])

        max_rolls, min_rolls = None, None
        max_roll_jump_url, min_roll_jump_url = "#", "#"  # Default URLs
        if not valid_rolls_df.empty:
            idx_max_rolls = valid_rolls_df['rolls'].idxmax()
            idx_min_rolls = valid_rolls_df['rolls'].idxmin()
            row_with_max_rolls = valid_rolls_df.loc[idx_max_rolls]
            row_with_min_rolls = valid_rolls_df.loc[idx_min_rolls]
            max_rolls = row_with_max_rolls['rolls']
            min_rolls = row_with_min_rolls['rolls']
            average_rolls = valid_rolls_df['rolls'].mean()

            guild_id = int(ast.literal_eval(os.environ['GUILD_IDS'])[
                           'default'])  # Ensure GUILD_IDS env var is set
            max_roll_channel = row_with_max_rolls['channel']
            max_roll_message = row_with_max_rolls['message']
            max_roll_jump_url = f'https://discord.com/channels/{guild_id}/{max_roll_channel}/{max_roll_message}'
            min_roll_channel = row_with_min_rolls['channel']
            min_roll_message = row_with_min_rolls['message']
            min_roll_jump_url = f'https://discord.com/channels/{guild_id}/{min_roll_channel}/{min_roll_message}'

        # --- Calculate Global Sequence Bests ---
        global_max_prev_to_loss_num = None
        global_max_prev_to_loss_player_id = None
        global_min_ratio = float('inf')
        global_min_ratio_player_id = None
        global_min_ratio_prev_num = None
        global_min_ratio_curr_num = None
        global_max_matching_roll = None
        global_max_matching_roll_player_id = None
        global_two_after_two_counts = {}
        global_one_after_two_counts = {}

        for index, game_row in df.iterrows():  # Iterate through ALL games
            sequence_str = game_row.get('sequence')
            p1_id = game_row['player1']
            p2_id = game_row['player2']
            loser_id = game_row['loser']

            # Basic checks and parsing
            if not isinstance(sequence_str, str) or not sequence_str:
                continue
            try:
                seq_numbers = [float(n) for n in sequence_str.split('|')]
            except (ValueError, TypeError):
                continue
            num_elements = len(seq_numbers)
            if num_elements < 2:
                continue

            # --- 1. Biggest Loss (Highest pre-'1' roll for any loser) ---
            try:
                second_last_num = seq_numbers[-2]
                # Ensure the last number was indeed 1, as per rule
                if seq_numbers[-1] == 1.0 and not math.isnan(second_last_num) and not math.isinf(second_last_num):
                    if global_max_prev_to_loss_num is None or second_last_num > global_max_prev_to_loss_num:
                        global_max_prev_to_loss_num = second_last_num
                        global_max_prev_to_loss_player_id = loser_id
            except IndexError:
                pass  # Sequence was too short

            # --- Determine assignment rule for pairs ---
            is_odd_length = (num_elements % 2 != 0)
            p1_gets_odd_indices = (loser_id == p2_id and is_odd_length) or \
                                  (loser_id == p1_id and not is_odd_length)

            # --- 2 & 3: Loop through pairs for Min Ratio and Max Matching ---
            for i in range(1, num_elements):
                prev_num = seq_numbers[i-1]
                curr_num = seq_numbers[i]

                if math.isnan(prev_num) or math.isinf(prev_num) or \
                   math.isnan(curr_num) or math.isinf(curr_num):
                    continue

                # 1. Determine owner
                index_is_odd = (i % 2 != 0)
                current_owner_is_p1 = (p1_gets_odd_indices == index_is_odd)
                current_owner_id = p1_id if current_owner_is_p1 else p2_id

                # 2. Lowest % Roll
                if prev_num != 0:
                    ratio = curr_num / prev_num
                    if not math.isnan(ratio) and not math.isinf(ratio):
                        if ratio < global_min_ratio:
                            global_min_ratio = ratio
                            global_min_ratio_player_id = current_owner_id
                            global_min_ratio_prev_num = prev_num
                            global_min_ratio_curr_num = curr_num

                # 3. Highest 100% Roll (Matching Roll)
                if prev_num == curr_num:
                    # Check if current max is None OR if curr_num is greater
                    if global_max_matching_roll is None or curr_num > global_max_matching_roll:
                        global_max_matching_roll = curr_num
                        global_max_matching_roll_player_id = current_owner_id

                # 4. 2 after 2 & 1 after 2 logic
                if prev_num == 2:
                    if curr_num == 2:
                        global_two_after_two_counts[current_owner_id] = global_two_after_two_counts.get(
                            current_owner_id, 0) + 1
                    elif curr_num == 1:
                        global_one_after_two_counts[current_owner_id] = global_one_after_two_counts.get(
                            current_owner_id, 0) + 1

        # --- Calculate Per-Player Streaks (and global longest for special stats) ---
        # For global longest streaks, to ensure the *first* occurrence
        global_longest_win_streak = 0
        global_longest_win_streak_player_id = None
        # Initialize with a very late date
        global_longest_win_streak_datetime = pd.Timestamp.max

        global_longest_loss_streak = 0
        global_longest_loss_streak_player_id = None
        # Initialize with a very late date
        global_longest_loss_streak_datetime = pd.Timestamp.max

        # Dictionaries to store per-player streak info
        current_win_streaks = {}    # {player_id: current_streak}
        max_player_win_streaks = {}  # {player_id: max_streak_achieved}
        current_loss_streaks = {}
        max_player_loss_streaks = {}

        if not df.empty and 'winner' in df.columns and 'loser' in df.columns:
            df['winner'] = pd.to_numeric(
                df['winner'], errors='coerce').astype('Int64')
            df['loser'] = pd.to_numeric(
                df['loser'], errors='coerce').astype('Int64')
            df_sorted = df.sort_values(by='datetime').reset_index(drop=True)

            all_involved_players = pd.unique(pd.concat(
                [df_sorted['player1'], df_sorted['player2'], df_sorted['winner'], df_sorted['loser']]).dropna())
            for player_id_init in all_involved_players:
                current_win_streaks[player_id_init] = 0
                max_player_win_streaks[player_id_init] = 0
                current_loss_streaks[player_id_init] = 0
                max_player_loss_streaks[player_id_init] = 0

            for index, game_row in df_sorted.iterrows():
                winner_id = game_row['winner']
                loser_id = game_row['loser']
                # Datetime of the current game
                game_datetime = game_row['datetime']

                if pd.isna(winner_id) or pd.isna(loser_id):
                    continue

                # --- Winner's Streak Updates ---
                current_loss_streaks[winner_id] = 0
                current_win_streaks[winner_id] = current_win_streaks.get(
                    winner_id, 0) + 1
                max_player_win_streaks[winner_id] = max(
                    max_player_win_streaks.get(winner_id, 0), current_win_streaks[winner_id])

                # Check/Update Global Longest Win Streak
                if current_win_streaks[winner_id] > global_longest_win_streak:
                    global_longest_win_streak = current_win_streaks[winner_id]
                    global_longest_win_streak_player_id = winner_id
                    global_longest_win_streak_datetime = game_datetime
                elif current_win_streaks[winner_id] == global_longest_win_streak:
                    if game_datetime < global_longest_win_streak_datetime:  # Achieved same length earlier
                        global_longest_win_streak_player_id = winner_id
                        global_longest_win_streak_datetime = game_datetime

                # --- Loser's Streak Updates ---
                current_win_streaks[loser_id] = 0
                current_loss_streaks[loser_id] = current_loss_streaks.get(
                    loser_id, 0) + 1
                max_player_loss_streaks[loser_id] = max(
                    max_player_loss_streaks.get(loser_id, 0), current_loss_streaks[loser_id])

                # Check/Update Global Longest Loss Streak
                if current_loss_streaks[loser_id] > global_longest_loss_streak:
                    global_longest_loss_streak = current_loss_streaks[loser_id]
                    global_longest_loss_streak_player_id = loser_id
                    global_longest_loss_streak_datetime = game_datetime
                elif current_loss_streaks[loser_id] == global_longest_loss_streak:
                    if game_datetime < global_longest_loss_streak_datetime:  # Achieved same length earlier
                        global_longest_loss_streak_player_id = loser_id
                        global_longest_loss_streak_datetime = game_datetime

        # --- Calculate Game with Most '2's ---
        max_twos_count = 0
        max_twos_jump_url = "#"  # Default

        if 'sequence' in df.columns and not df.empty:
            # Count occurrences of the string '2' in each sequence
            # Fill NaN sequences with empty string, convert to string just in case
            df['twos_count'] = df['sequence'].fillna('').astype(
                str).str.split('|').apply(lambda x: x.count('2'))

            if df['twos_count'].max() > 0:  # Check if any '2's were found
                # Get index of first max occurrence
                idx_max_twos = df['twos_count'].idxmax()
                max_twos_count = df.loc[idx_max_twos, 'twos_count']
                row_with_max_twos = df.loc[idx_max_twos]

                # Construct jump URL
                try:  # Use same guild_id as obtained above
                    max_twos_channel = row_with_max_twos['channel']
                    max_twos_message = row_with_max_twos['message']
                    # Ensure channel/message IDs are valid before creating URL
                    if pd.notna(max_twos_channel) and pd.notna(max_twos_message):
                        # Cast to int
                        max_twos_jump_url = f'https://discord.com/channels/{guild_id}/{int(max_twos_channel)}/{int(max_twos_message)}'
                except Exception as e:
                    print(
                        f"Warning: Error creating jump URL for max twos: {e}")
                    max_twos_jump_url = "#"  # Reset on error

        # --- Player Ranking Calculation ---
        all_player_ids_for_ranking = pd.concat(
            [df['player1'], df['player2']]).dropna().astype(int).unique()
        player_stats_list = []
        for pid in all_player_ids_for_ranking:
            games_as_p1 = (df['player1'] == pid).sum()
            games_as_p2 = (df['player2'] == pid).sum()
            total_p_games = games_as_p1 + games_as_p2
            if total_p_games == 0:
                continue  # Should not happen if pid came from player1/2 list

            total_p_wins = (df['winner'] == pid).sum()
            total_p_losses = (df['loser'] == pid).sum()  # Use loser column

            win_pct = (total_p_wins / total_p_games) * \
                100 if total_p_games > 0 else 0.0

            # Get streak info for this player
            p_max_w_streak = max_player_win_streaks.get(pid, 0)
            p_max_l_streak = max_player_loss_streaks.get(pid, 0)
            p_curr_w_streak = current_win_streaks.get(pid, 0)
            p_curr_l_streak = current_loss_streaks.get(pid, 0)

            current_streak_display = ""
            if p_curr_w_streak > 0:
                current_streak_display = f"w{p_curr_w_streak}"
            elif p_curr_l_streak > 0:
                current_streak_display = f"l{p_curr_l_streak}"

            streaks_combined_str = f"{current_streak_display} (W{p_max_w_streak}-L{p_max_l_streak})"

            player_stats_list.append({
                'player_id': pid,
                'total_games': total_p_games,
                'total_wins': total_p_wins,
                'total_losses': total_p_losses,
                'win_percentage': win_pct,
                'streaks_display': streaks_combined_str
            })

        player_stats_df = pd.DataFrame(player_stats_list)
        if player_stats_df.empty:  # Handle no players found
            final_ranking_df = pd.DataFrame(
                columns=['player_name', 'win_percentage', 'player_record', 'streaks_display'])
        else:
            ranked_players = player_stats_df.sort_values(
                by=['win_percentage', 'total_games'], ascending=[False, False])

            output_df_formatted = ranked_players.copy()
            output_df_formatted['player_name'] = output_df_formatted['player_id'].apply(
                lambda an_id: get_nick_safe(ctx, an_id))
            output_df_formatted['win_percentage'] = output_df_formatted['win_percentage'].map(
                '{:.0f}%'.format)
            output_df_formatted['player_record'] = output_df_formatted.apply(
                lambda row: f"({row['total_wins']}-{row['total_losses']})", axis=1
            )
            final_ranking_df = output_df_formatted[[
                'player_name', 'win_percentage', 'player_record', 'streaks_display']]

        # --- Format Global Record Results ---
        # Biggest Loss
        biggest_loss_player_name = get_nick_safe(ctx,
                                                 global_max_prev_to_loss_player_id)
        biggest_loss_num_str = format_num(global_max_prev_to_loss_num)
        biggest_loss_str = f"**{biggest_loss_num_str}** down to **1** by {biggest_loss_player_name}" if global_max_prev_to_loss_num is not None else "N/A"

        # Lowest % Roll
        min_ratio_player_name = get_nick_safe(ctx, global_min_ratio_player_id)
        if global_min_ratio != float('inf'):
            min_prev_n = format_num(global_min_ratio_prev_num)
            min_curr_n = format_num(global_min_ratio_curr_num)
            min_ratio_pct_str = f"{global_min_ratio * 100:.2f}%"
            min_ratio_str = f"**{min_ratio_pct_str}** ({min_prev_n} to {min_curr_n}) by {min_ratio_player_name}"
        else:
            min_ratio_str = "N/A"

        # Highest 100% Roll
        max_match_player_name = get_nick_safe(ctx,
                                              global_max_matching_roll_player_id)
        max_match_num_str = format_num(global_max_matching_roll)
        max_match_str = f"**{max_match_num_str}** by {max_match_player_name}" if global_max_matching_roll is not None else "N/A"

        # 2 after 2
        if global_two_after_two_counts:
            top_survivor_id = max(
                global_two_after_two_counts, key=global_two_after_two_counts.get)
            top_survivor_count = global_two_after_two_counts[top_survivor_id]
            survivor_str = f"**{top_survivor_count}** times by {get_nick_safe(ctx, top_survivor_id)}"
        else:
            survivor_str = "N/A"

        # 1 after 2
        if global_one_after_two_counts:
            top_victim_id = max(global_one_after_two_counts,
                                key=global_one_after_two_counts.get)
            top_victim_count = global_one_after_two_counts[top_victim_id]
            victim_str = f"**{top_victim_count}** times by {get_nick_safe(ctx, top_victim_id)}"
        else:
            victim_str = "N/A"

        # Format new streak results
        win_streak_player_name_overall = get_nick_safe(
            ctx, global_longest_win_streak_player_id)
        loss_streak_player_name_overall = get_nick_safe(
            ctx, global_longest_loss_streak_player_id)
        longest_win_streak_str = f"**{global_longest_win_streak}** by {win_streak_player_name_overall}" if global_longest_win_streak > 0 else "N/A"
        longest_loss_streak_str = f"**{global_longest_loss_streak}** by {loss_streak_player_name_overall}" if global_longest_loss_streak > 0 else "N/A"

        # --- Construct Embed ---
        # Top part: General Stats
        embed_value_part1 = (
            f'**Most rolls:** [{format_num(max_rolls)}]({max_roll_jump_url})\n'
            f'**Fewest rolls:** [{format_num(min_rolls)}]({min_roll_jump_url})\n'
            f'**Average rolls:** {format_num(average_rolls, 2)}\n'
            f'**Most "2"s rolled:** [{format_num(max_twos_count)}]({max_twos_jump_url})\n\n'
        )

        # Middle part: Global Records
        embed_value_part2 = (
            f'Biggest Loss: {biggest_loss_str}\n'
            f'Highest 100% Roll: {max_match_str}\n'
            f'Lowest % Roll: {min_ratio_str}\n'
            f'Longest Win Streak: {longest_win_streak_str}\n'
            f'Longest Loss Streak: {longest_loss_streak_str}\n'
            f'Most "2 after 2": {survivor_str}\n'
            f'Most "1 after 2": {victim_str}\n\n'
        )

        # Bottom part: Ranking
        ranking_string = final_ranking_df.to_string(index=False, header=False)
        embed_value_part3 = (
            # Updated header
            f'```\n{ranking_string}\n```'
        )

        drStatsEmbed = discord.Embed(
            title=f'Global Deathroll Stats',
            colour=discord.Colour.from_rgb(220, 20, 60))
        drStatsEmbed.add_field(name=f'**Total # of games: {global_games}**',
                               value=embed_value_part1,
                               inline=False)  # Use one field, check length
        drStatsEmbed.add_field(name=f'**Special Stats**',
                               value=embed_value_part2,
                               inline=False)  # Use one field, check length
        drStatsEmbed.add_field(name=f'**Ranking** (name, win%, record, streak (max streaks)',
                               value=embed_value_part3,
                               inline=False)  # Use one field, check length

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
        average_rolls = '{:.2f}'.format(average_rolls)
        max_rolls = player_games['rolls'].max()
        min_rolls = player_games['rolls'].min()

        # 4. Calculate top opponents
        player_games['opponent'] = player_games.apply(
            lambda row: row['player2'] if row['player1'] == player_id else row['player1'], axis=1
        )

        top_opponent_name, top_opponent_count_str = "n/a", "0"
        top_victim_display = "n/a"
        top_nemesis_display = "n/a"

        if not player_games.empty and 'opponent' in player_games.columns:
            opponent_counts = player_games['opponent'].value_counts()
            if not opponent_counts.empty:
                top_opponent_id = opponent_counts.idxmax()
                top_opponent_name = get_nick_safe(ctx, top_opponent_id)
                top_opponent_count_str = str(opponent_counts.max())

            # Calculate wins and losses against each opponent for difference-based stats
            wins_vs_opponent = player_games[player_games['winner']
                                            == player_id]['opponent'].value_counts()
            losses_vs_opponent = player_games[player_games['loser']
                                              == player_id]['opponent'].value_counts()

            matchup_stats_df = pd.DataFrame({
                'wins_vs': wins_vs_opponent,
                'losses_vs': losses_vs_opponent
            }).fillna(0).astype(int)  # Ensure int after fillna

            if not matchup_stats_df.empty:
                matchup_stats_df['difference'] = matchup_stats_df['wins_vs'] - \
                    matchup_stats_df['losses_vs']

                # Top Victim (largest positive difference)
                # Filter for only positive differences before finding idxmax
                positive_diffs = matchup_stats_df[matchup_stats_df['difference'] > 0]
                if not positive_diffs.empty:
                    top_victim_id = positive_diffs['difference'].idxmax()
                    # Get original wins/losses
                    victim_row = matchup_stats_df.loc[top_victim_id]
                    victim_name = get_nick_safe(ctx, top_victim_id)
                    top_victim_display = f"**{victim_name}** (+{victim_row['difference']})"

                # Top Nemesis (largest negative difference / smallest overall difference)
                # Filter for only negative differences before finding idxmin
                negative_diffs = matchup_stats_df[matchup_stats_df['difference'] < 0]
                if not negative_diffs.empty:
                    top_nemesis_id = negative_diffs['difference'].idxmin()
                    # Get original wins/losses
                    nemesis_row = matchup_stats_df.loc[top_nemesis_id]
                    nemesis_name = get_nick_safe(ctx, top_nemesis_id)
                    top_nemesis_display = f"**{nemesis_name}** ({nemesis_row['difference']})"

        # 5. Calculate lowest % roll
        # Calculate Minimum Sequence Ratio
        biggest_loss_numbers = []
        matching_rolls_list = []
        player_roll_ratios_all_games = []
        min_ratio_so_far = float('inf')
        player_two_after_two_count = 0
        player_one_after_two_count = 0

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
                if current_owner_id == player_id and prev_num != 0:
                    ratio = curr_num / prev_num
                    player_roll_ratios_all_games.append(ratio)
                    if ratio < min_ratio_so_far:
                        min_ratio_so_far = ratio
                        min_prev_num_for_ratio = prev_num  # Store the numbers
                        min_curr_num_for_ratio = curr_num  # Store the numbers
                    # 2 after 2 and 1 after 2 logic
                    if prev_num == 2:
                        if curr_num == 2:
                            player_two_after_two_count += 1
                        elif curr_num == 1:
                            player_one_after_two_count += 1

                if prev_num == curr_num and current_owner_id == player_id:
                    matching_rolls_list.append(curr_num)

            if is_player_loser:
                second_last_str = sequence_str.split('|')[-2]
                second_last_num = int(second_last_str)
                biggest_loss_numbers.append(second_last_num)

        # Find the biggest loss
        biggest_loss = max(biggest_loss_numbers)

        # Format the minimum ratio and the pair of rolls it's associated with
        min_ratio = min_ratio_so_far * 100
        min_ratio = '{:.2f}%'.format(min_ratio)
        min_prev_num_for_ratio = '{:.0f}'.format(min_prev_num_for_ratio)
        min_curr_num_for_ratio = '{:.0f}'.format(min_curr_num_for_ratio)

        # 6. Calculate highest 100% roll
        if matching_rolls_list:
            max_match = max(matching_rolls_list)
            max_match = '{:.0f}'.format(max_match)

        # 7. Calculate average % roll
        avg_player_roll_pct_str = "N/A"
        if player_roll_ratios_all_games:
            avg_ratio_val = sum(player_roll_ratios_all_games) / \
                len(player_roll_ratios_all_games)
            avg_player_roll_pct_str = '{:.2f}%'.format(avg_ratio_val * 100)

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
                                     + f'Average per game: {average_rolls}\n'
                                     + f'Most rolls: {max_rolls} , fewest: {min_rolls}\n\n'
                                     + f'**Opponents**\n'
                                     f'Top rival: **{top_opponent_name}**, {top_opponent_count_str} played\n'
                                     f'Top victim: {top_victim_display}\n'
                                     f'Top nemesis: {top_nemesis_display}\n\n'
                                     + f'**Special stats**\n'
                                     + f'Average roll %: **{avg_player_roll_pct_str}**\n'
                                     + f'Biggest loss: from **{biggest_loss}** down to **1**, propz!\n'
                                     + f'Highest 100% roll: **{max_match}**\n'
                                     + f'Lowest % roll: **{min_ratio}** ({min_prev_num_for_ratio} to {min_curr_num_for_ratio})\n'
                                     + f'Survived "2 after 2": **{player_two_after_two_count}**/**{player_two_after_two_count + player_one_after_two_count}** times ({round(float(player_two_after_two_count/(player_two_after_two_count + player_one_after_two_count)*100),1)}%)\n')

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
        vs_colors = [(0, '#9f3c3c'), (0.25, '#9f3c3c'),
                     (0.5, '#9f9f3c'), (0.75, '#3c9f3c'), (1, '#3c9f3c')]

        # Create figure 1
        fig1 = plt.figure(1, figsize=(8, 6), facecolor=figbg_c)
        ax1 = fig1.gca()
        fig1.subplots_adjust(left=0.1, right=0.88)

        # Data for Barplot
        df_grouped = df\
            .groupby(["rolls"])\
            .agg(count=("rolls", "count"))\
            .reset_index()

        max_rolls = df_grouped['rolls'].max()
        df_barplot = df_grouped
        for i in range(1, max_rolls+2):
            if not (df_grouped['rolls'] == i).any():
                df_append = pd.DataFrame([[i, 0]], columns=['rolls', 'count'])
                df_barplot = pd.concat([df_barplot, df_append])
        df_barplot = df_barplot.sort_values('rolls').reset_index(drop=True)

        # Data of 100k simulated games for occurance distribution
        sim_data = {2: 2, 3: 3, 4: 31, 5: 120, 6: 288, 7: 734, 8: 1371, 9: 2618, 10: 3912,
                    11: 5585, 12: 7318, 13: 8868, 14: 9689, 15: 9918, 16: 9646, 17: 8968,
                    18: 7836, 19: 6311, 20: 4967, 21: 3787, 22: 2751, 23: 1826, 24: 1286,
                    25: 861, 26: 548, 27: 334, 28: 194, 29: 96, 30: 59, 31: 33, 32: 19,
                    33: 12, 34: 6, 35: 2, 37: 1}
        simulation = pd.Series(data=sim_data)

        # 2. Berechne den prozentualen Anteil jeder Häufigkeit
        sim_total_rolls = simulation.sum()
        sim_roll_percentages = (simulation / sim_total_rolls) * 100

        # Barplot
        ax1.bar(df_barplot['rolls'], df_barplot['count'],
                color=bar_c, edgecolor='none')
        ax1.set_xlabel('rolls', color=label_c)
        ax1.set_ylabel('count', color=label_c)
        ax1.set_title('How many rolls?', color=label_c)
        ax1.tick_params(axis='x', colors=label_c)
        ax1.tick_params(axis='y', colors=label_c)
        ax1.set_xticks(range(1, max_rolls + 1))
        ax1.yaxis.set_major_locator(mticker.MultipleLocator(1))
        ax1.set_facecolor(figbg_c)
        ax1.grid(color=label_c, linestyle='-', linewidth=0.5, alpha=0.5)
        ax1.spines[:].set_color(label_c)
        ax1.set_xlim(xmin=0, xmax=max_rolls+1)
        ax1.set_ylim(ymin=0, ymax=df_barplot['count'].max()+1)

        axbell = ax1.twinx()
        axbell.set_ylabel('probability of 100k simulated games', color=label_c)
        axbell.plot(sim_roll_percentages.index, sim_roll_percentages.values,
                    marker='', linestyle='-', color='#9f3c3c')
        axbell.tick_params(axis='y', colors=label_c)
        axbell.set_yticks(range(0, int(sim_roll_percentages.max()+2)))
        axbell.set_ylim(ymin=0, ymax=int(sim_roll_percentages.max()+1))
        axbell.spines[:].set_color(label_c)
        axbell.yaxis.set_major_formatter(mticker.PercentFormatter(decimals=0))

        # Data for Pie Chart
        df_start = df
        df_start['starting_player'] = df_start.apply(
            self.determine_starting_player, axis=1)
        game_count = len(df_start)
        start_wins = len(df_start[df_start['winner']
                         == df_start['starting_player']])
        second_wins = game_count - start_wins

        pie_labels = ['starting\nplayer', 'second\nplayer']
        pie_data = [start_wins, second_wins]

        # Create figure 2
        fig2 = plt.figure(2, figsize=(8, 6), facecolor=figbg_c)
        ax2 = fig2.gca()

        # Pie Chart
        ax2.pie(pie_data, labels=pie_labels, autopct='%1.1f%%',
                startangle=90, colors=pie_c, explode=(0.01, 0.01))
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
                        results.append({'Spieler1': player1, 'Spieler2': player2,
                                       'Siege': wins, 'Niederlagen': losses, 'Siegquote': win_percentage})
                    else:
                        results.append({'Spieler1': player1, 'Spieler2': player2,
                                       'Siege': 0, 'Niederlagen': 0, 'Siegquote': np.nan})
        # Erstelle ein DataFrame aus der Ergebnisliste
        win_loss_df = pd.DataFrame(results)
        # Erstelle eine Pivot-Tabelle, um die Siegquoten für jedes Spielerpaar zu erhalten
        win_loss_pivot = win_loss_df.pivot(
            index='Spieler1', columns='Spieler2', values='Siegquote')

        # Create figure 3
        fig3 = plt.figure(3, figsize=(8, 6), facecolor=figbg_c)
        ax3 = fig3.gca()

        # Heatmap
        # Definiere die benutzerdefinierte Colormap
        cmap_name = 'vs_colormap'
        cm = LinearSegmentedColormap.from_list(cmap_name, vs_colors, N=100)

        ax3.imshow(win_loss_pivot, cmap=cm,
                   interpolation='nearest', vmin=0, vmax=1)
        # Füge die Spielernamen als Beschriftungen hinzu
        player_labels = []
        for player in players:
            player_usr = ctx.guild.get_member(player)
            player_labels.append(getNick(player_usr))

        ax3.set_xticks(np.arange(len(players)), player_labels, color=label_c)
        ax3.set_yticks(np.arange(len(players)), player_labels, color=label_c)

        for i, player1 in enumerate(players):
            for j, player2 in enumerate(players):
                if i == j:  # Diagonalelemente schwarz färben
                    ax3.text(j, i, 'X', ha='center',
                             va='center', color=label_c)
                    ax3.add_patch(plt.Rectangle((j - 0.5, i - 0.5),
                                  1, 1, facecolor=figbg_c, edgecolor='none'))
                elif np.isnan(win_loss_pivot.iloc[i, j]):
                    ax3.text(j, i, '-', ha='center',
                             va='center', color=label_c)
                    ax3.add_patch(plt.Rectangle((j - 0.5, i - 0.5),
                                  1, 1, facecolor='#1a1a1e', edgecolor='none'))
                else:
                    # Finde die Siege und Niederlagen für das Spielerpaar
                    wins = win_loss_df.loc[(win_loss_df['Spieler1'] == player1) & (
                        win_loss_df['Spieler2'] == player2), 'Siege'].values[0]
                    losses = win_loss_df.loc[(win_loss_df['Spieler1'] == player1) & (
                        win_loss_df['Spieler2'] == player2), 'Niederlagen'].values[0]
                    ax3.text(
                        j, i, f"{win_loss_pivot.iloc[i, j]:.0%}\n({wins} - {losses})", ha='center', va='center', color='black')

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
        def get_rolls_list(sequence_string):
            return [int(roll) for roll in sequence_string.split('|')]
        df_line = df
        df_line['rolls_list'] = df_line['sequence'].apply(get_rolls_list)

        short_rolls = {}
        for rolls in df_line[df_line['rolls'] == df_line['rolls'].min()]['rolls_list']:
            for i, roll_value in enumerate(rolls):
                roll_number = i
                if roll_number not in short_rolls:
                    short_rolls[roll_number] = []
                short_rolls[roll_number].append(roll_value)

        short_max_rolls = {roll: np.max(values)
                           for roll, values in short_rolls.items()}
        short_min_rolls = {roll: np.min(values)
                           for roll, values in short_rolls.items()}
        short_max_rolls = list(short_max_rolls.values())
        short_min_rolls = list(short_min_rolls.values())[0:-1]
        short_min_rolls.reverse()

        short_path_rolls = short_max_rolls
        short_path_rolls.extend(short_min_rolls)

        long_rolls = {}
        for rolls in df_line[df_line['rolls'] == df_line['rolls'].max()]['rolls_list']:
            for i, roll_value in enumerate(rolls):
                roll_number = i
                if roll_number not in long_rolls:
                    long_rolls[roll_number] = []
                long_rolls[roll_number].append(roll_value)

        long_max_rolls = {roll: np.max(values)
                          for roll, values in long_rolls.items()}
        long_min_rolls = {roll: np.min(values)
                          for roll, values in long_rolls.items()}
        long_max_rolls = list(long_max_rolls.values())
        long_min_rolls = list(long_min_rolls.values())[0:-1]
        long_min_rolls.reverse()

        long_path_rolls = long_max_rolls
        long_path_rolls.extend(long_min_rolls)

        # Finde die Indizes des kürzesten Spiels und bei mehreren kürzesten Spiele die Min/Max Begrenzungen
        if len(df_line[df_line['rolls'] == df_line['rolls'].min()]) == 1:
            min1 = True
            shortest_game_index = df_line['rolls'].idxmin()
            shortest_game_rolls = df_line['rolls_list'][shortest_game_index]
        elif len(df_line[df_line['rolls'] == df_line['rolls'].min()]) > 1:
            min1 = False
            minPathData = []
            for x, y in enumerate(short_path_rolls):
                if x == 0:
                    minPathPoint = (mpath.Path.MOVETO, [x, y])
                elif x == len(short_path_rolls)-1:
                    minPathPoint = (mpath.Path.CLOSEPOLY, [0, 0])
                else:
                    if x > (len(short_path_rolls)-1)/2:
                        x = (len(short_path_rolls)-1) - x
                    minPathPoint = (mpath.Path.LINETO, [x, y])
                minPathData.append(minPathPoint)
            min_codes, min_verts = zip(*minPathData)
            minPath = mpath.Path(min_verts, min_codes)
            min_patch = mpatches.PathPatch(minPath, facecolor='#9f3c3c', edgecolor=None, alpha=0.3,
                                           label=f"corridor of shortest games (Length: {df_line['rolls'].min()})")

        if len(df_line[df_line['rolls'] == df_line['rolls'].max()]) == 1:
            max1 = True
            longest_game_index = df_line['rolls'].idxmax()
            longest_game_rolls = df_line['rolls_list'][longest_game_index]
        elif len(df_line[df_line['rolls'] == df_line['rolls'].max()]) > 1:
            max1 = False
            maxPathData = []

            for x, y in enumerate(long_path_rolls):
                if x == 0:
                    maxPathPoint = (mpath.Path.MOVETO, [x, y])
                elif x == len(long_path_rolls)-1:
                    maxPathPoint = (mpath.Path.CLOSEPOLY, [0, 0])
                else:
                    if x > (len(long_path_rolls)-1)/2:
                        x = (len(long_path_rolls)-1) - x
                    maxPathPoint = (mpath.Path.LINETO, [x, y])
                maxPathData.append(maxPathPoint)
            max_codes, max_verts = zip(*maxPathData)
            maxPath = mpath.Path(max_verts, max_codes)
            max_patch = mpatches.PathPatch(maxPath, facecolor='#3c9f3c', edgecolor=None,
                                           alpha=0.3, label=f"corridor of longest games (Length: {df_line['rolls'].max()})")

        all_rolls_per_roll_number = {}

        # Sammle alle Würfe für jede Wurfnummer
        for rolls in df_line['rolls_list']:
            for i, roll_value in enumerate(rolls):
                roll_number = i
                if roll_number not in all_rolls_per_roll_number:
                    all_rolls_per_roll_number[roll_number] = []
                all_rolls_per_roll_number[roll_number].append(roll_value)

        # Berechne Durchschnitt, Maximum und Minimum für jede Wurfnummer
        average_rolls = {roll: np.mean(
            values) for roll, values in all_rolls_per_roll_number.items()}
        # print(average_rolls)
        max_rolls = {roll: np.max(values) for roll,
                     values in all_rolls_per_roll_number.items()}
        min_rolls = {roll: np.min(values) for roll,
                     values in all_rolls_per_roll_number.items()}

        # Sortiere nach Wurfnummer
        sorted_averages_rolls = dict(sorted(average_rolls.items()))
        sorted_max_rolls = dict(sorted(max_rolls.items()))
        sorted_min_rolls = dict(sorted(min_rolls.items()))

        # Create figure 4
        fig4 = plt.figure(4, figsize=(8, 6), facecolor=figbg_c)
        ax4 = fig4.gca()

        # Lineplot
        ax4.plot(sorted_min_rolls.keys(), sorted_min_rolls.values(
        ), linestyle='--', label='Minimum Roll Value', alpha=0.8, color='#9f3c3c')
        if min1:
            ax4.plot(range(0, len(shortest_game_rolls)), shortest_game_rolls, marker=11, linestyle='-',
                     label=f'Shortest Game (Length: {len(shortest_game_rolls)-1})', linewidth=1, color='#9f3c3c')
        else:
            ax4.add_patch(min_patch)
        ax4.plot(sorted_max_rolls.keys(), sorted_max_rolls.values(
        ), linestyle='--', label='Maximum Roll Value', alpha=0.8, color='#3c9f3c')
        if max1:
            ax4.plot(range(0, len(longest_game_rolls)), longest_game_rolls, marker=10, linestyle='-',
                     label=f'Longest Game (Length: {len(longest_game_rolls)-1})', linewidth=1, color='#3c9f3c')
        else:
            ax4.add_patch(max_patch)
        ax4.plot(sorted_averages_rolls.keys(), sorted_averages_rolls.values(), marker='o',
                 linestyle='-', label='Average Roll Value', alpha=1, color=bar_c, markersize=3)

        ax4.set_title(
            'Average, Max, Min, Shortest & Longest Game Roll Values', color=label_c)
        ax4.set_xlabel('roll number', color=label_c)
        ax4.set_ylabel('roll value', color=label_c)
        ax4.set_facecolor(figbg_c)
        ax4.tick_params(axis='x', colors=label_c)
        ax4.tick_params(axis='y', colors=label_c)
        ax4.set_yscale('log')
        ax4.grid(True, which="both", ls="-",
                 color=label_c, linewidth=0.5, alpha=0.5)
        ax4.spines[:].set_color(label_c)
        ax4.set_xticks(np.arange(0, max(sorted_averages_rolls.keys()) + 1, 1))
        ax4.set_ylim(1, 200000)
        ax4.legend(labelcolor=label_c, facecolor=figbg_c,
                   edgecolor=label_c, reverse=True)

        # Speichere die Plots als temporäre Dateien im Speicher (BytesIO)
        image_files = []
        for i, fig in enumerate([fig3, fig1, fig4, fig2]):
            buffer = io.BytesIO()
            fig.savefig(buffer, format='png', dpi=400)
            buffer.seek(0)
            image_files.append(discord.File(
                buffer, filename=f'dr_chart_{i+1}.png'))
            plt.close(fig)

        # Erstelle die Embeds für jede Grafik
        embeds = []
        for i, file in enumerate(image_files):
            embed = discord.Embed(description='### Deathroll Charts',
                                  colour=discord.Colour.from_rgb(220, 20, 60),
                                  url='https://discord.com')
            embed.set_image(url=f'attachment://{file.filename}')
            embeds.append(embed)

        await ctx.send(embeds=embeds, files=image_files)

    # Takes a row of deathroll_history DataFrame and returns the ID of the starting player
    def determine_starting_player(self, row):
        if row['rolls'] % 2 != 0:
            return row['loser']
        else:
            return row['winner']


async def setup(client):
    await client.add_cog(deathroll(client))
