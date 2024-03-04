import discord
from discord.ext import commands
from utils.db import check_connection, init_db
from openai import OpenAI
import os
import io
import aiohttp

# Start OpenAI client
ai = OpenAI(api_key=os.environ['OPENAI_KEY'])
# You can change this to a different model if desired
model = "gpt-3.5-turbo"  # You can change this to a different model if desired

class chatgpt(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.cnx = init_db()
        self.cursor = self.cnx.cursor(buffered=True)

    @commands.command(name="gpt")
    async def generate_text(self, ctx, *, prompt):
        try:
            # Generate text using the OpenAI API
            completion = ai.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
            )
            message = completion.choices[0].message.content
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
            response = ai.images.generate(
                model="dall-e-3",
                prompt=prompt,
                n=1,
                quality="hd",
                size="1024x1024"
            )
            image_url = response.data[0].url
            image_name = f"img-{ctx.message.id}.png"
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as resp:
                    if resp.status != 200:
                        raise Exception('Could not download file...')
                    data = io.BytesIO(await resp.read())
                    img = discord.File(data, image_name)
            # Send the generated image as an embed in the Discord channel
            embed = discord.Embed(colour=discord.Colour.from_rgb(47, 49, 54))
            embed.set_author(
                name="WLC GPT",
                icon_url="https://townsquare.media/site/295/files/2019/10/Terminator-Orion.jpg")
            embed.set_image(url=f"attachment://{image_name}")
            await ctx.send(file=img, embed=embed)
        except Exception as e:
            # Send an error message to the Discord channel if there was an issue with the API request
            await ctx.send(f"Sorry, there was an error generating the image. Error message: {str(e)}")
        # Update command invoke counter
        else:
            try:
                self.update_img_invokes(ctx.author.id)
            except Exception as e:
                await ctx.send(f'```Error: 666```')

    def update_img_invokes(self, id):
        # Check DB connection
        self.cnx = check_connection(self.cnx)
        self.cursor = self.cnx.cursor(buffered=True)
        # DB query: Insert new entry if user doesn't exist, or update existing row value+1
        query = (
            f'INSERT INTO img_invokes (userid, invokes) VALUES ({id}, 1) ON DUPLICATE KEY UPDATE invokes=invokes+1;'
        )
        self.cursor.execute(query)
        self.cnx.commit()
        return

# Initialize the Discord bot and add the GPT cog
def setup(client):
    client.add_cog(chatgpt(client))
