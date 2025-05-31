import discord
from discord.ext import commands
from discord import app_commands

GUILD_ID = 742833700034576515

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @app_commands.command(name='help', description='Display the help message')
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Help", color=discord.Color.purple())
        embed.add_field(name="/help", value="Display this message!", inline=False)
        embed.add_field(name="/getstats", value="Display the Tetra League stats for a given TETR.IO player.", inline=False)
        embed.add_field(name="/roster `[team]`", value="Display the roster of a given team.", inline=False)
        embed.add_field(name="/standings `[league]` `[team]` `[shown]`", value="Display the standings of a given league or the record of a given team. Entry for `team` overrides all other values. `league` defaults to upper league, `shown` defaults to 10.", inline=False)
        embed.add_field(name="/setlineup `[matchid]` `[team]` `[p1]` `[p2]` `[p3]` `[p4]` `[p5]`", value="Set a team's lineup for a given match. All players default to `N/A`.", inline=False)
        embed.add_field(name="/lineups `[matchid]`", value="Display the lineups of both teams for a given match.", inline=False)
        embed.add_field(name="/blindpick `[matchid]` `[team]`", value="Initiate blindpick for a given match.", inline=False)
        embed.add_field(name="/matchresults `[matchid]`", value="Display the match results for a given completed match.", inline=False)
        embed.add_field(name="/forfeitmatch `[matchid]` `[team1]` `[team2]`", value="**(Organizer Use)** Forfeit a match on behalf of a given team. Filling `[team2]` yields a double forfeit.", inline=False)
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Help(bot))