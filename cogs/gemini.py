import discord
from discord.ext import commands
from utils.db import check_connection, init_db
from google import genai
from google.genai import types
from io import BytesIO
import base64
import os

# Set up Gemini client
client = genai.Client(api_key=os.environ['GEMINI_KEY'])
# You can change this to a different model if desired
model = "gemini-2.5-pro-preview-03-25"


class gemini(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.cnx = init_db()
        self.cursor = self.cnx.cursor(buffered=True)

    @commands.command(name="gem")
    async def generate_text(self, ctx, *, prompt):
        try:

            # Generate text using the OpenAI API
            response = client.models.generate_content(
                model=model, contents=prompt)
            message = response.text
            # Send the generated text as a message in the Discord channel
            embed = discord.Embed(colour=discord.Colour.from_rgb(47, 49, 54))
            embed.set_author(
                name="WLC Gem",
                icon_url="https://townsquare.media/site/295/files/2019/10/Terminator-Orion.jpg")
            embed.description = message
            await ctx.send(embed=embed)
        except Exception as e:
            # Send an error message to the Discord channel if there was an issue with the API request
            await ctx.send(f"Sorry, there was an error generating the text. Error message: {str(e)}")

    @commands.command(name="img")
    async def generate_image(self, ctx, *, prompt):
        await ctx.defer()
        try:
            # Generate image using 2.0 Flash
            response = client.models.generate_images(
                model="imagen-3.0-generate-002",
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                )
            )

            images_to_send = []

            for i, generated_image in enumerate(response.generated_images):
                # Check if image data exists
                if generated_image.image and generated_image.image.image_bytes:

                    raw_or_encoded_data = generated_image.image.image_bytes

                    # Wrap the bytes in a BytesIO object (acts as an in-memory file)
                    image_file_like_object = BytesIO(
                        raw_or_encoded_data)

                    # Create a discord.File object
                    discord_file = discord.File(
                        fp=image_file_like_object, filename=f"generated_image_{i+1}.png")

                    images_to_send.append(discord_file)

            # Send the generated images as a reply to the prompt message
            await ctx.reply(files=images_to_send)
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


async def setup(client):
    await client.add_cog(gemini(client))
