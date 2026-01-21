from math import floor
import discord
from discord.ext import commands
from howlongtobeatpy import HowLongToBeat

class hltb(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    @commands.guild_only()
    async def hltb(self, ctx, *, game):
        results_list = await HowLongToBeat().async_search(game)
        if results_list is None or len(results_list) == 0:
            await ctx.send(f"Spiel {game} nicht gefunden.")
            return
        best_element = max(results_list, key=lambda element: element.similarity)
        
        url = best_element.game_web_link
        embedHltb = discord.Embed(title=best_element.game_name,
                                  url=url,
                                  colour=discord.Colour.from_rgb(255, 128, 0))
        embedHltb.set_thumbnail(url = best_element.game_image_url)
        
        if best_element.complexity_lvl_combine == 0 and best_element.complexity_lvl_sp == 1:
            embedHltb.add_field(name='Main Story',
                                value=f"{getTimeString(best_element.main_story)}",
                                inline=True)
            embedHltb.add_field(name='Main + Extra',
                                value=f"{getTimeString(best_element.main_extra)}",
                                inline=True)
            embedHltb.add_field(name='Completionist',
                                value=f"{getTimeString(best_element.completionist)}",
                                inline=True)

        else:
            if best_element.complexity_lvl_combine & best_element.complexity_lvl_sp:
                embedHltb.add_field(name='Solo',
                                    value=f"{getTimeString(best_element.all_styles)}",
                                    inline=True)

            if best_element.complexity_lvl_co:
                embedHltb.add_field(name='Co-Op',
                                    value=f"{getTimeString(best_element.coop_time)}",
                                    inline=True)

            if best_element.complexity_lvl_mp:
                embedHltb.add_field(name='Vs.',
                                    value=f"{getTimeString(best_element.mp_time)}",
                                    inline=True)

        await ctx.send(embed=embedHltb)

def getTimeString(timeInHours):
    if timeInHours == 0:
        return "-- Hrs"
    timeString = ""
    timeInHours = round(timeInHours * 2) / 2
    timeString += str(floor(timeInHours))
    if timeInHours % 1 != 0:
        timeString += "½"
    timeString += " Hrs"
    return timeString

async def setup(client):
    await client.add_cog(hltb(client))
