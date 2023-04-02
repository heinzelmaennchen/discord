import discord
from discord.ext import commands
import openai
import os

# Connect to the OpenAI API
openai.api_key = os.environ['OPENAI_KEY']
# You can change this to a different model if desired
model = "gpt-3.5-turbo"  # You can change this to a different model if desired


class chatgpt(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(name="gpt")
    async def generate_text(self, ctx, *, prompt):
        try:
            # Generate text using the OpenAI API
            response = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
            )
            message = response.choices[0].message.content
            # Send the generated text as a message in the Discord channel
            embed = discord.Embed(colour=discord.Colour.from_rgb(47, 49, 54))
            embed.set_author(
                name="WLC GPT",
                icon_url="https://townsquare.media/site/295/files/2019/10/Terminator-Orion.jpg")
            embed.description = message
            await ctx.send(embed=embed)
        except Exception as e:
            # Send an error message to the Discord channel if there was an issue with the API request
            await ctx.send(f"Sorry, there was an error generating the text. Error message: {str(e)}")

    @commands.command(name="img")
    async def generate_image(self, ctx, *, prompt):
        try:
            # Generate image using the OpenAI API
            # generate 1 image, 1024x1024px
            response = openai.Image.create(
                prompt=prompt,
                n=1,
                size="1024x1024"
            )
            image_url = response['data'][0]['url']
            # Send the generated image as an embed in the Discord channel
            embed = discord.Embed(colour=discord.Colour.from_rgb(47, 49, 54))
            embed.set_author(
                name="WLC GPT",
                icon_url="https://townsquare.media/site/295/files/2019/10/Terminator-Orion.jpg")
            embed.set_image(url=image_url)
            await ctx.send(embed=embed)
        except Exception as e:
            # Send an error message to the Discord channel if there was an issue with the API request
            await ctx.send(f"Sorry, there was an error generating the image. Error message: {str(e)}")


# Initialize the Discord bot and add the GPT cog
def setup(client):
    client.add_cog(chatgpt(client))
