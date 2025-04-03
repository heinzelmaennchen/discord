import discord
import datetime
import os

from discord import app_commands
from discord.ext import commands, tasks

from utils.misc import isGameChannel

oneweek_h = 24*7

class threads(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.ch_id = os.environ['GAMENIGHT_CH_ID']
        self.guild_id = os.environ['GUILD_ID']
        self.usrs_ch_id = os.environ['GAMENIGHT_USRS_CH_ID'] 

    @app_commands.command()
    @app_commands.guild_only()
    @app_commands.check(isGameChannel)
    async def zockermittwoch(self, interaction: discord.Interaction) -> None:
        thread = await interaction.channel.create_thread(name = "Zockizock")
        poll = discord.Poll(question="Zockermittwoch wen wen wen?", duration=datetime.timedelta(days = 3), multiple=True)
        poll.add_answer(text="Montag")
        poll.add_answer(text="Dienstag")
        poll.add_answer(text="Mittwoch")
        poll.add_answer(text="Donnerstag")
        poll.add_answer(text="Freitag")
        await thread.send(poll=poll)

        if interaction.guild.id == 405433814114893835:
            mention_members = self.getMembers(interaction.channel)
        else:
            mention_members = self.getMembers(await interaction.guild.get_channel(self.usrs_ch_id))
            
        r = f''
        for member in mention_members:
            r += f'{member.name} '
        await thread.send(r)
        await interaction.response.send_message("Thread & Poll erstellt.", ephemeral=True)

    def getMembers(self, channel):
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
    await client.add_cog(threads(client))