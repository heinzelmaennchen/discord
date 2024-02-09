import os
import pickle
import discord
from discord.ext import commands
from utils.misc import getMessageTime
import utils.googlephotos


class imagealbum(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.client.user or message.author.bot or message.channel.type == "private":
            return

        if message.attachments:
            atts = message.attachments
            pic_ext = ['.jpg', '.png', '.jpeg', '.gif']
            try:
                for att in atts:
                    for ext in pic_ext:
                        if att.filename.lower().endswith(ext):
                            #AUTH TOKEN
                            service = utils.googlephotos.init_service()
                            token = pickle.load(
                                open(
                                    'storage/auth/token_photoslibrary_v1.pickle',
                                    'rb'))
                            #print(f'Token: {token}\n')
                            #ALBUM TITLE
                            album_title = f'{message.guild.name} #{message.channel.name}'
                            #print(f'Album Title: {album_title}\n')
                            #ALBUMID
                            albumId = utils.googlephotos.get_albumId(
                                album_title, service)
                            if albumId == None:
                                albumId = utils.googlephotos.create_album(
                                    album_title, service)
                            #print(f'AlbumId: {albumId}\n')
                            #FILENAME
                            time = getMessageTime(message.id)
                            filenametime = f'{time.year}{time.month}{time.day}{time.hour}{time.minute}{time.second}'
                            filename = os.path.splitext(att.filename)[0]
                            filename = filenametime + '_' + filename + os.path.splitext(
                                att.filename)[1]
                            #print(f'File Name: {filename}\n')

                            #IMAGE BYTE STREAM
                            image_bytes = await att.read()

                            mediaItem = await utils.googlephotos.upload_image_to_album(
                                albumId, image_bytes, filename, token, service)
                            #print(f'Media Item: {mediaItem}')

                            await message.add_reaction('⬆️')
            except:
                await message.add_reaction('❌')


async def setup(client):
    await client.add_cog(imagealbum(client))