import discord
import os
import ast
import random

from discord.ext import commands, tasks
from datetime import time, date, datetime, timedelta

from utils.misc import getDatetimeNow, getTimezone

my_timezone = getTimezone()
gn_pollthread_time = time(19, 30, 0, tzinfo=my_timezone)

class gamenight(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.guild_id = int(ast.literal_eval(os.environ['GUILD_IDS'])['default'])
        self.channel_id = int(ast.literal_eval(os.environ['CHANNEL_IDS'])['gaming'])
        self.users_channel_id = int(ast.literal_eval(os.environ['CHANNEL_IDS'])['gaming_users'])
        if not self.gn_pollthread.is_running():
            self.gn_pollthread.start()

    def cog_unload(self):
        self.gn_pollthread.cancel()

    @tasks.loop(time=gn_pollthread_time)
    async def gn_pollthread(self) -> None:
        now = getDatetimeNow()
        weekday = now.isoweekday()

        if weekday % 4 != 0:
            # If weekday is not %1: Monday, %2: Tuesday, %3: Wednesday, %4: Thursday, %5: Friday, %6: Saturday, %7: Sunday then return/skip
            return
        
        guild = self.client.get_guild(self.guild_id)
        channel = guild.get_channel(self.channel_id)
        emojis = guild.emojis
        days_to_monday = timedelta(days=(7-weekday%7+1))
        thread = await channel.create_thread(name=f'Zocktag {(now + days_to_monday).strftime("%d.%m.")}-{(now + days_to_monday + timedelta(days=4)).strftime("%d.%m.")}', auto_archive_duration=10080)
        poll = discord.Poll(question="Zockermittwoch wen wen wen?", duration=timedelta(days=3), multiple=True)
        poll.add_answer(text=f'Montag {(now + days_to_monday).strftime("%d.%m.")}', emoji=random.choice(emojis))
        poll.add_answer(text=f'Dienstag {(now + days_to_monday + timedelta(days=1)).strftime("%d.%m.")}', emoji=random.choice(emojis))
        poll.add_answer(text=f'Mittwoch {(now + days_to_monday + timedelta(days=2)).strftime("%d.%m.")}', emoji=random.choice(emojis))
        poll.add_answer(text=f'Donnerstag {(now + days_to_monday + timedelta(days=3)).strftime("%d.%m.")}', emoji=random.choice(emojis))
        poll.add_answer(text=f'Freitag {(now + days_to_monday + timedelta(days=4)).strftime("%d.%m.")}', emoji=random.choice(emojis))
        await thread.send(poll=poll)
        mention_members = self.getMembers(guild.get_channel(self.users_channel_id))
        r = f''
        for member in mention_members:
            r += f'{member.mention} '
        await thread.send(r)
    
    def getMembers(self, channel) -> list:
        # getChannelMembers from "main channel" to mention and add them into the thread
        # ignore Bots
        ch_members = channel.members
        mention_members = []
        for member in ch_members:
            if member.bot == True:
                continue
            mention_members.append(member)
        return mention_members

async def setup(client):
    await client.add_cog(gamenight(client))
