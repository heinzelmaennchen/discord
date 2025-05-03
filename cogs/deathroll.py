import os
import discord
from discord.ext import commands

from utils.misc import getNick, getTimezone
from utils.db import check_connection, init_db
from utils.deathrollgifs import gifdict

import random
import pandas as pd
import ast
import math
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

        # --- Player Ranking Calculation ---
        all_players = pd.concat([df['player1'], df['player2']]).dropna().astype(
            int)  # Ensure IDs are consistent type and drop NaNs
        games_played = all_players.value_counts()
        games_won = df['winner'].dropna().astype(int).value_counts()
        games_lost = df['loser'].dropna().astype(int).value_counts()
        # Start with games played index
        player_stats = pd.DataFrame({'total_games': games_played})
        player_stats = player_stats.join(
            games_won.rename('total_wins'), how='left')  # Join wins
        player_stats = player_stats.join(games_lost.rename(
            'total_losses'), how='left')  # Join losses

        player_stats['total_wins'] = player_stats['total_wins'].fillna(
            0).astype(int)
        player_stats['total_losses'] = player_stats['total_losses'].fillna(
            0).astype(int)
        # Ensure total_games is not zero before calculating percentage
        player_stats['win_percentage'] = 0.0  # Initialize
        player_stats.loc[player_stats['total_games'] > 0, 'win_percentage'] = \
            (player_stats['total_wins'] / player_stats['total_games']) * 100

        ranked_players = player_stats.sort_values(by=['win_percentage', 'total_games'], ascending=[
                                                  False, False])  # Sort by % then games
        ranked_players_reset = ranked_players.reset_index().rename(
            columns={'index': 'player_id'})  # fix potential multi-index name issue
        output_df = ranked_players_reset[[
            'player_id', 'win_percentage', 'total_games', 'total_wins', 'total_losses']]

        # Formatting for Player Ranking display
        output_df_formatted = output_df.copy()
        output_df_formatted['player_name'] = output_df_formatted['player_id'].apply(
            # Handle user leaving server
            lambda pid: getNick(ctx.guild.get_member(
                pid)) if ctx.guild else f"ID: {pid}"
        )
        output_df_formatted['win_percentage'] = output_df_formatted['win_percentage'].map(
            '{:.0f}%'.format)
        output_df_formatted['player_record'] = output_df_formatted.apply(
            lambda row: f"({row['total_wins']}-{row['total_losses']})", axis=1
        )
        final_ranking_df = output_df_formatted[[
            'player_name', 'win_percentage', 'player_record']]

        # --- Calculate Global Sequence Bests ---
        global_max_prev_to_loss_num = None
        global_max_prev_to_loss_player_id = None
        global_min_ratio = float('inf')
        global_min_ratio_player_id = None
        global_min_ratio_prev_num = None
        global_min_ratio_curr_num = None
        global_max_matching_roll = None
        global_max_matching_roll_player_id = None

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

                # Determine owner
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

        # --- Calculate Longest Streaks ---
        longest_win_streak = 0
        longest_win_streak_player_id = None
        longest_loss_streak = 0
        longest_loss_streak_player_id = None

        if not df.empty and 'winner' in df.columns and 'loser' in df.columns:
            # Use Int64 to handle potential NaN from conversion/original data
            df['winner'] = pd.to_numeric(
                df['winner'], errors='coerce').astype('Int64')
            df['loser'] = pd.to_numeric(
                df['loser'], errors='coerce').astype('Int64')
            # Sort by datetime to process streaks chronologically
            df_sorted = df.sort_values(by='datetime').reset_index(drop=True)

            current_win_streaks = {}  # Tracks current streak for each player
            max_win_streaks = {}     # Tracks max streak found *so far* for each player
            current_loss_streaks = {}
            max_loss_streaks = {}

            for index, game_row in df_sorted.iterrows():
                winner_id = game_row['winner']
                loser_id = game_row['loser']

                # Skip if winner or loser ID is missing for this row
                if pd.isna(winner_id) or pd.isna(loser_id):
                    continue

                # --- Update Winner's Streaks ---
                # End loser's win streak, potentially start/continue loser's loss streak
                current_win_streaks[loser_id] = 0  # End win streak
                current_loss_streaks[loser_id] = current_loss_streaks.get(
                    loser_id, 0) + 1  # Increment loss streak
                # Update loser's max loss streak if current is higher
                max_loss_streaks[loser_id] = max(max_loss_streaks.get(
                    loser_id, 0), current_loss_streaks[loser_id])

                # --- Update Loser's Streaks ---
                # End winner's loss streak, potentially start/continue winner's win streak
                current_loss_streaks[winner_id] = 0  # End loss streak
                current_win_streaks[winner_id] = current_win_streaks.get(
                    winner_id, 0) + 1  # Increment win streak
                # Update winner's max win streak if current is higher
                max_win_streaks[winner_id] = max(max_win_streaks.get(
                    winner_id, 0), current_win_streaks[winner_id])

            # Find the overall maximum streaks after iterating through all games
            if max_win_streaks:  # Check if any wins occurred
                # Find player ID with the highest value in max_win_streaks
                longest_win_streak_player_id = max(
                    max_win_streaks, key=max_win_streaks.get)
                # Get the corresponding streak value
                longest_win_streak = max_win_streaks[longest_win_streak_player_id]

            if max_loss_streaks:  # Check if any losses occurred
                longest_loss_streak_player_id = max(
                    max_loss_streaks, key=max_loss_streaks.get)
                longest_loss_streak = max_loss_streaks[longest_loss_streak_player_id]

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

        # --- Format Global Record Results ---
        # Helper to format numbers and get nicks safely
        def format_num(num, decimals=0):
            if num is None or math.isnan(num) or math.isinf(num):
                return "N/A"
            if abs(num - round(num)) < 1e-9:
                return str(int(round(num)))
            return f"{num:.{decimals}f}"

        def get_nick_safe(player_id):
            if player_id is None:
                return "N/A"
            # Ensure ID is int for lookup
            member = ctx.guild.get_member(int(player_id))
            return getNick(member) if member else f"ID: {player_id}"

        # Biggest Loss
        biggest_loss_player_name = get_nick_safe(
            global_max_prev_to_loss_player_id)
        biggest_loss_num_str = format_num(global_max_prev_to_loss_num)
        biggest_loss_str = f"**{biggest_loss_num_str}** down to **1** by {biggest_loss_player_name}" if global_max_prev_to_loss_num is not None else "N/A"

        # Lowest % Roll
        min_ratio_player_name = get_nick_safe(global_min_ratio_player_id)
        if global_min_ratio != float('inf'):
            min_prev_n = format_num(global_min_ratio_prev_num)
            min_curr_n = format_num(global_min_ratio_curr_num)
            min_ratio_pct_str = f"{global_min_ratio * 100:.2f}%"
            min_ratio_str = f"**{min_ratio_pct_str}** ({min_prev_n} to {min_curr_n}) by {min_ratio_player_name}"
        else:
            min_ratio_str = "N/A"

        # Highest 100% Roll
        max_match_player_name = get_nick_safe(
            global_max_matching_roll_player_id)
        max_match_num_str = format_num(global_max_matching_roll)
        max_match_str = f"**{max_match_num_str}** by {max_match_player_name}" if global_max_matching_roll is not None else "N/A"

        # Format new streak results
        win_streak_player_name = get_nick_safe(longest_win_streak_player_id)
        loss_streak_player_name = get_nick_safe(longest_loss_streak_player_id)
        longest_win_streak_str = f"**{longest_win_streak}** by {win_streak_player_name}" if longest_win_streak > 0 else "N/A"
        longest_loss_streak_str = f"**{longest_loss_streak}** by {loss_streak_player_name}" if longest_loss_streak > 0 else "N/A"

        # --- Construct Embed ---
        # Top part: General Stats
        embed_value_part1 = (
            f'**Most rolls:** [{format_num(max_rolls)}]({max_roll_jump_url})\n'
            f'**Fewest rolls:** [{format_num(min_rolls)}]({min_roll_jump_url})\n'
            f'**Average rolls:** {format_num(average_rolls, 1)}\n'
            f'**Most "2"s rolled:** [{format_num(max_twos_count)}]({max_twos_jump_url})\n\n'
        )

        # Middle part: Global Records
        embed_value_part2 = (
            f'**Special Stats**\n'
            f'Biggest Loss: {biggest_loss_str}\n'
            f'Highest 100% Roll: {max_match_str}\n'
            f'Lowest % Roll: {min_ratio_str}\n'
            f'Longest Win Streak: {longest_win_streak_str}\n'
            f'Longest Loss Streak: {longest_loss_streak_str}\n\n'
        )

        # Bottom part: Ranking
        ranking_string = final_ranking_df.to_string(index=False, header=False)
        embed_value_part3 = (
            f'**Ranking**\n'
            f'{ranking_string}'
        )

        drStatsEmbed = discord.Embed(
            title=f'Global Deathroll Stats',
            colour=discord.Colour.from_rgb(220, 20, 60))
        drStatsEmbed.set_thumbnail(
            url='https://cdn.discordapp.com/attachments/723670062023704578/1362911780313108611/unnamed.png?ex=68041e02&is=6802cc82&hm=cb5879590b96bbbd69476fc88ff355e07dc9cdcdbfc27adafde77abe1bf31df3&')

        drStatsEmbed.add_field(name=f'**Total # of games: {global_games}**',
                               value=embed_value_part1 + embed_value_part2 + embed_value_part3,
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
        biggest_loss_numbers = []
        matching_rolls_list = []
        min_ratio_so_far = float('inf')

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
                    if ratio < min_ratio_so_far:
                        min_ratio_so_far = ratio
                        min_prev_num_for_ratio = prev_num  # Store the numbers
                        min_curr_num_for_ratio = curr_num  # Store the numbers

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
                                     + f'Biggest loss: from **{biggest_loss}** down to **1**, propz!\n'
                                     + f'Highest 100% roll: **{max_match}**\n'
                                     + f'Lowest % roll: **{min_ratio}** ({min_prev_num_for_ratio} to {min_curr_num_for_ratio})')

        await ctx.send(embed=drPlayerStatsEmbed)


async def setup(client):
    await client.add_cog(deathroll(client))
