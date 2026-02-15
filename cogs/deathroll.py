
import os
import io
import discord
from discord.ext import commands

from utils.misc import getNick, getTimezone
from utils.db import get_db_connection
from utils.deathrollgifs import gifdict
import utils.deathroll_processing as dr_utils

import functools
import random
import pandas as pd
import numpy as np
import ast
import math
from datetime import datetime

START_VALUE = 133337
TEST = False
TEST_PLAYER = ""

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
        # connection pool is managed by get_db_connection, no need to init here

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

        # Get pooled connection
        cnx = get_db_connection()
        cursor = None
        try:
            cursor = cnx.cursor(buffered=True)
            # Execute query
            cursor.execute(query, data)
            cnx.commit()
            return cursor.lastrowid
        finally:
            if cursor:
                cursor.close()
            if cnx:
                cnx.close()

    # Global Deathroll stats
    @commands.group(aliases=['drstats'], invoke_without_command=True)
    @commands.guild_only()
    async def deathrollstats(self, ctx):
        # Get pooled connection
        cnx = get_db_connection()
        try:
            # Grab all records
            query = ('SELECT datetime, channel, message, player1, player2, sequence, rolls, winner, loser FROM deathroll_history')
            df = pd.read_sql(query, con=cnx)
        finally:
            if cnx:
                cnx.close()
        
        # Calculate in thread
        guild_id = int(ast.literal_eval(os.environ['GUILD_IDS'])['default'])
        stats = await self.client.loop.run_in_executor(None, dr_utils.calculate_global_stats, df, guild_id)

        # -- Format results --
        # Rankings
        player_stats_list = stats['player_stats_list']
        player_stats_df = pd.DataFrame(player_stats_list)

        ranking_string = ""
        if not player_stats_df.empty:
            ranked_players = player_stats_df.sort_values(
                by=['win_percentage', 'total_games'], ascending=[False, False])
            
            output_df = ranked_players.copy()
            output_df['player_name'] = output_df['player_id'].apply(lambda pid: get_nick_safe(ctx, pid))
            output_df['win_percentage'] = output_df['win_percentage'].map('{:.0f}%'.format)
            output_df['player_record'] = output_df.apply(
                lambda row: f"({row['total_wins']}-{row['total_losses']})", axis=1
            )
            ranking_string = output_df[['player_name', 'win_percentage', 'player_record', 'streaks_display']].to_string(index=False, header=False)

        # Special Stats Formatting
        biggest_loss_player = get_nick_safe(ctx, stats['global_max_prev_to_loss_player_id'])
        biggest_loss_str = f"**{dr_utils.format_num(stats['global_max_prev_to_loss_num'])}** down to **1** by {biggest_loss_player}" if stats['global_max_prev_to_loss_num'] is not None else "N/A"

        min_ratio_player = get_nick_safe(ctx, stats['global_min_ratio_player_id'])
        if stats['global_min_ratio'] != float('inf'):
            min_ratio_str = f"**{stats['global_min_ratio'] * 100:.2f}%** ({dr_utils.format_num(stats['global_min_ratio_prev_num'])} to {dr_utils.format_num(stats['global_min_ratio_curr_num'])}) by {min_ratio_player}"
        else:
            min_ratio_str = "N/A"

        max_match_player = get_nick_safe(ctx, stats['global_max_matching_roll_player_id'])
        max_match_str = f"**{dr_utils.format_num(stats['global_max_matching_roll'])}** by {max_match_player}" if stats['global_max_matching_roll'] is not None else "N/A"

        # Survivors/Victims
        two_after_two = stats['global_two_after_two_counts']
        if two_after_two:
            top_survivor_id = max(two_after_two, key=two_after_two.get)
            survivor_str = f"**{two_after_two[top_survivor_id]}** times by {get_nick_safe(ctx, top_survivor_id)}"
        else:
            survivor_str = "N/A"

        one_after_two = stats['global_one_after_two_counts']
        if one_after_two:
            top_victim_id = max(one_after_two, key=one_after_two.get)
            victim_str = f"**{one_after_two[top_victim_id]}** times by {get_nick_safe(ctx, top_victim_id)}"
        else:
            victim_str = "N/A"

        # Streaks
        win_streak_player = get_nick_safe(ctx, stats['global_longest_win_streak_player_id'])
        loss_streak_player = get_nick_safe(ctx, stats['global_longest_loss_streak_player_id'])
        longest_win_str = f"**{stats['global_longest_win_streak']}** by {win_streak_player}" if stats['global_longest_win_streak'] > 0 else "N/A"
        longest_loss_str = f"**{stats['global_longest_loss_streak']}** by {loss_streak_player}" if stats['global_longest_loss_streak'] > 0 else "N/A"

        # Construct Embed
        embed_value_part1 = (
            f'**Most rolls:** [{dr_utils.format_num(stats["max_rolls"])}]({stats["max_roll_jump_url"]})\n'
            f'**Fewest rolls:** [{dr_utils.format_num(stats["min_rolls"])}]({stats["min_roll_jump_url"]})\n'
            f'**Average rolls:** {dr_utils.format_num(stats["average_rolls"], 2)}\n'
            f'**Most "2"s rolled:** [{dr_utils.format_num(stats["max_twos_count"])}]({stats["max_twos_jump_url"]})\n\n'
        )

        embed_value_part2 = (
            f'Biggest Loss: {biggest_loss_str}\n'
            f'Highest 100% Roll: {max_match_str}\n'
            f'Lowest % Roll: {min_ratio_str}\n'
            f'Longest Win Streak: {longest_win_str}\n'
            f'Longest Loss Streak: {longest_loss_str}\n'
            f'Most "2 after 2": {survivor_str}\n'
            f'Most "1 after 2": {victim_str}\n\n'
        )

        embed_value_part3 = (
            f'```\n{ranking_string}\n```'
        )

        drStatsEmbed = discord.Embed(
            title=f'Global Deathroll Stats',
            colour=discord.Colour.from_rgb(220, 20, 60))
        drStatsEmbed.add_field(name=f'**Total # of games: {stats["global_games"]}**',
                               value=embed_value_part1,
                               inline=False)
        drStatsEmbed.add_field(name=f'**Special Stats**',
                               value=embed_value_part2,
                               inline=False)
        drStatsEmbed.add_field(name=f'**Ranking** (name, win%, record, streak (max streaks)',
                               value=embed_value_part3,
                               inline=False)

        await ctx.send(embed=drStatsEmbed)

    # Individual Deathroll stats
    @deathrollstats.command(name='player')
    @commands.guild_only()
    async def deathrollstats_player(self, ctx):
        # Get pooled connection
        cnx = get_db_connection()
        try:
            # Grab all records
            query = (
                f'SELECT datetime, channel, message, player1, player2, sequence, rolls, winner, loser FROM deathroll_history')
            df = pd.read_sql(query, con=cnx)
        finally:
            if cnx:
                cnx.close()
        
        # Calculate in thread
        stats = await self.client.loop.run_in_executor(None, dr_utils.calculate_player_stats, df, ctx.author.id)

        # Format Names
        top_opponent_name = get_nick_safe(ctx, stats['top_opponent_id']) if stats['top_opponent_id'] else "n/a"
        top_victim_display = "n/a"
        if stats['top_victim_id']:
            victim_name = get_nick_safe(ctx, stats['top_victim_id'])
            top_victim_display = f"**{victim_name}** (+{stats['top_victim_difference']})"
            
        top_nemesis_display = "n/a"
        if stats['top_nemesis_id']:
             nemesis_name = get_nick_safe(ctx, stats['top_nemesis_id'])
             top_nemesis_display = f"**{nemesis_name}** ({stats['top_nemesis_difference']})"

        player_name = getNick(ctx.author)
        if player_name.endswith('s'):
            player_name += "'"
        else:
            player_name += "'s"

        drPlayerStatsEmbed = discord.Embed(
            title=f'{player_name} Deathroll Stats',
            colour=discord.Colour.from_rgb(220, 20, 60))
        # Hardcoded thumbnail from original code
        drPlayerStatsEmbed.set_thumbnail(
            url='https://cdn.discordapp.com/attachments/723670062023704578/1363260251339620352/unnamed.png?ex=6805628c&is=6804110c&hm=b0156321aa65223c6cf1ae1664756bcb1b6efb85a6260c79570ca67f16faf5e5&')

        drPlayerStatsEmbed.add_field(name=f'Total games: {stats["total_games"]}',
                                     value=f'Record: ({stats["total_wins"]}-{stats["total_losses"]}), {stats["win_percentage"]} won\n\n'
                                     + f'**Total rolls: {stats["total_rolls"]}**\n'
                                     + f'Average per game: {stats["average_rolls"]}\n'
                                     + f'Most rolls: {stats["max_rolls"]} , fewest: {stats["min_rolls"]}\n\n'
                                     + f'**Opponents**\n'
                                     f'Top rival: **{top_opponent_name}**, {stats["top_opponent_count_str"]} played\n'
                                     f'Top victim: {top_victim_display}\n'
                                     f'Top nemesis: {top_nemesis_display}\n\n'
                                     + f'**Special stats**\n'
                                     + f'Average roll %: **{stats["avg_player_roll_pct_str"]}**\n'
                                     + f'Biggest loss: from **{stats["biggest_loss"]}** down to **1**, propz!\n'
                                     + f'Highest 100% roll: **{stats["max_match"]}**\n'
                                     + f'Lowest % roll: **{stats["min_ratio"]}** ({stats["min_prev_num_for_ratio"]} to {stats["min_curr_num_for_ratio"]})\n'
                                     + f'Survived "2 after 2": **{stats["player_two_after_two_count"]}**/**{stats["player_two_after_two_count"] + stats["player_one_after_two_count"]}** times ({round(float(stats["player_two_after_two_count"]/(stats["player_two_after_two_count"] + stats["player_one_after_two_count"])*100),1)}%)\n')

        await ctx.send(embed=drPlayerStatsEmbed)

    # Deathroll Charts
    @deathrollstats.command(name='charts')
    @commands.guild_only()
    async def deathrollstats_charts(self, ctx):
        # Get pooled connection
        cnx = get_db_connection()
        try:
            # Grab all records
            query = ('SELECT datetime, channel, message, player1, player2, sequence, rolls, winner, loser FROM deathroll_history')
            df = pd.read_sql(query, con=cnx)
        finally:
            if cnx:
                cnx.close()

        # Map Player Names
        all_players = pd.unique(pd.concat([df['player1'], df['player2']]).dropna())
        name_map = {}
        for pid in all_players:
             try:
                 name_map[int(pid)] = get_nick_safe(ctx, int(pid))
             except:
                 pass
        
        # Generate Charts in Thread
        image_buffers, players_list = await self.client.loop.run_in_executor(
            None, dr_utils.generate_charts, df, name_map)

        # Create Files and Embeds
        image_files = []
        for i, buf in enumerate(image_buffers):
            image_files.append(discord.File(buf, filename=f'dr_chart_{i+1}.png'))

        embeds = []
        for i, file in enumerate(image_files):
            embed = discord.Embed(description='### Deathroll Charts',
                                  colour=discord.Colour.from_rgb(220, 20, 60),
                                  url='https://discord.com')
            embed.set_image(url=f'attachment://{file.filename}')
            embeds.append(embed)

        await ctx.send(embeds=embeds, files=image_files)


async def setup(client):
    await client.add_cog(deathroll(client))
