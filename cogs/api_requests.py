import discord
from discord.ext import commands
import os
import requests
import json

class api_requests(commands.Cog):

  def __init__(self, client):
    self.youtube_key = os.environ['YOUTUBE_KEY']

  # Youtube video search
  @commands.command()
  async def yt(self, ctx, *, arg):
    await ctx.send(self.searchVideo(arg))

  def searchVideo(self, query_string):
      url = "https://www.googleapis.com/youtube/v3/search"
      payload = {
          'key' : self.youtube_key,
          'q' : query_string,
          'part' : 'snippet',
          'maxResults' : 1,
          'safeSearch' : 'none',
          'type' : 'video'
      }

      r = requests.get(url, params=payload).json()
      video_id = r['items'][0]['id']['videoId']
      video_url = ('https://youtube.com/watch?v=' + video_id)
      return video_url

def setup(client):
  client.add_cog(api_requests(client))