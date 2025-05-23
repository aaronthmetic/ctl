import discord
from discord.ext import commands
from discord import app_commands

import requests

from dotenv import load_dotenv
import os

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

teams = [
         "Amherst College", "Carnegie Mellon University", "Columbia University", "Cornell University",
         "Georgia Institute of Technology", "New York University A", "New York University B", "Princeton University",
         "Purdue University A", "Purdue University B", "Rochester Institute of Technology", "Simon Fraser University",
         "Stanford University", "Texas A&M University", "University of British Columbia A", "University of British Columbia B",
         "University of California, Irvine", "University of California, Los Angeles A", "University of California, Los Angeles B",
         "University of California, Santa Barbara", "University of California, Santa Cruz", "University of California, San Diego",
         "University of California, Berkeley", "University of California, Davis", "University of Illinois, Urbana-Champaign",
         "University of Florida", "University of Michigan A", "University of Michigan B", "University of Southern California A",
         "University of Southern California B", "University of Toronto A", "University of Toronto B", "University of Texas, Austin",
         "University of Waterloo A", "University of Waterloo B", "University of Waterloo C", "University of Northern British Columbia",
         "University of Washington A", "University of Washington B", "University of Ottawa", "University of Utah", "University of Victoria",
         "Wilfrid Laurier University", "Yale University"
    ]

class Client(commands.Bot):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        try:
            guild = discord.Object(id=761274425475072010)
            synced = await self.tree.sync(guild=guild)
            print(f'Synced {len(synced)} commands to guild {guild.id}')
        except Exception as e:
            print(f'Error syncing commands: {e}')
    async def on_message(self, message):
        if message.author == self.user:
            return
        if message.content.startswith('hello'):
            await message.channel.send(f'Hi there {message.author}')
    async def on_reaction_add(self, reaction, user):
            await reaction.message.channel.send('You reacted')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
client = Client(command_prefix="!", intents=intents)

GUILD_ID = discord.Object(id=761274425475072010)

@client.tree.command(name="help", description="Display a list of all commands.", guild=GUILD_ID)
async def help(interaction: discord.Interaction):
     await interaction.response.send_message("Displaying a list of all commands.")
     # later send list of commands

# getting a 403 for some reason so i'll figure it out later
'''
@client.tree.command(name="getstats", description="Get the stats of any TETR.IO user!", guild=GUILD_ID)
async def getStats(interaction: discord.Interaction, username: str):
     url = f"https://ch.tetr.io/api/users/{username.lower()}/summaries/league"
     response = requests.get(url)
     if response.status_code == 200:
         rank = "rank"
         tr = "tr"
         glicko = "glicko"
         apm = "apm"
         pps = "pps"
         vs = "vs"
         await interaction.response.send_message(f'{username.lower()} stats:\nRank: {rank}\nTR: {tr}\nGlicko: {glicko}\nAPM: {apm}\nPPS:{pps}\nVS:{vs}')
     else:
         await interaction.response.send_message(response.status_code)
'''

@client.tree.command(name="standings", description="Display standings for either the upper league or lower league.", guild=GUILD_ID)
@app_commands.describe(
    league="(Optional) Choose a league to display standings for.",
    team="(Optional) Choose a team to display standings.",
    shown="(Optional) Choose the number of teams shown."
)
@app_commands.choices(
    league=[
        app_commands.Choice(name="upper", value="upper"),
        app_commands.Choice(name="lower", value="lower")
    ]
)
async def standings(interaction: discord.Interaction, league: app_commands.Choice[str] = None, team: str = None, shown: str = None):
    maxTeams = 0 # placeholder for max teams there are as default value for shown
    if team is None:
        if league is None:
            embed = discord.Embed(title="Standings", description="2026 CTL Standings", color=discord.Color.purple())
            embed.set_thumbnail(url="https://cdn.discordapp.com/icons/829182450185142312/f78172b9c494c081f4c4ca6da29b76e2.png?size=1024")
            embed.add_field(name="Team", value="Upper League", inline=False) # fill in later
            embed.add_field(name="Team", value="Lower League", inline=False) # fill in later
            await interaction.response.send_message(embed=embed)
            return
        elif (league.name == "upper"):
            embed = discord.Embed(title="Standings", description="2026 Upper League Standings", color=discord.Color.purple())
            embed.set_thumbnail(url="https://cdn.discordapp.com/icons/829182450185142312/f78172b9c494c081f4c4ca6da29b76e2.png?size=1024")
            embed.add_field(name="Team", value="Upper League", inline=True) # fill in later
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(title="Standings", description="2026 Lower League Standings", color=discord.Color.purple())
            embed.set_thumbnail(url="https://cdn.discordapp.com/icons/829182450185142312/f78172b9c494c081f4c4ca6da29b76e2.png?size=1024")
            embed.add_field(name="Team", value="Lower League", inline=True) # fill in later
            await interaction.response.send_message(embed=embed)
    else:
         embed = discord.Embed(title="Standings", description=f'2026 {team} Standings', color=discord.Color.purple())
         embed.set_thumbnail(url="https://cdn.discordapp.com/icons/829182450185142312/f78172b9c494c081f4c4ca6da29b76e2.png?size=1024")
         embed.add_field(name="Record", value="0-0", inline=False) # fill in later
         embed.add_field(name="Bucholz", value="0", inline=False) # fill in later
         embed.add_field(name="Point Differential", value="0", inline=False) # fill in later
         await interaction.response.send_message(embed=embed)

@standings.autocomplete('team')
async def standings_autocomplete(interaction: discord.Interaction, current: str):
    filtered = [team for team in teams if current.lower() in team.lower()]
    limited = filtered[:25]
    return [
        app_commands.Choice(name=team, value=team)
        for team in limited
    ]

@client.tree.command(name="roster", description="Display the full roster of a team.", guild=GUILD_ID)
@app_commands.describe(team="Select a team.")
async def roster(interaction: discord.Interaction, team: str):
    await interaction.response.send_message(f"You picked: {team}.")
    # later send the roster

@roster.autocomplete('team')
async def roster_autocomplete(interaction: discord.Interaction, current: str):
    filtered = [team for team in teams if current.lower() in team.lower()]
    limited = filtered[:25]
    return [
        app_commands.Choice(name=team, value=team)
        for team in limited
    ]

client.run(token)