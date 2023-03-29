import discord
from discord.ext import commands
import openai
import os

# Connect to the OpenAI API
openai.api_key = os.environ['OPENAI_KEY']
# You can change this to a different model if desired
model = "text-davinci-003"  # You can change this to a different model if desired


class chatgpt(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(name="gpt")
    @commands.guild_only()
    async def generate_text(self, ctx, *, prompt):
        try:
            # Generate text using the OpenAI API
            response = openai.Completion.create(
                model=model,
                prompt=prompt,
                max_tokens=500,
            )
            message = response.choices[0].text
            # Send the generated text as a message in the Discord channel
            await ctx.send(message)
        except Exception as e:
            # Send an error message to the Discord channel if there was an issue with the API request
            await ctx.send(f"Sorry, there was an error generating the text. Error message: {str(e)}")


# Initialize the Discord bot and add the GPT cog
def setup(client):
    client.add_cog(chatgpt(client))
