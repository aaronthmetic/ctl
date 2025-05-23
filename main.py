import discord
from discord.ext import commands
from discord import app_commands

import requests

from dotenv import load_dotenv
import os

import gspread
from google.oauth2.service_account import Credentials

scopes = [
    "https://www.googleapis.com/auth/spreadsheets"
]
creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
sheetsClient = gspread.authorize(creds)

sheet_id = "1vr2ltnMgevSpoeI3HAT5emdaU07G7AgjjItbz7hDFdg"
workbook = sheetsClient.open_by_key(sheet_id)

TestSheet = workbook.worksheet("Sheet1")
Seedings = workbook.worksheet("Seedings")
MatchupsU = workbook.worksheet("MatchupsU")
StandingsU = workbook.worksheet("Standings for 2025U")
MatchupsL = workbook.worksheet("MatchupsL")
StandingsL = workbook.worksheet("Standings for 2025L")

teams = Seedings.col_values(1)[1:]

upperStandings = StandingsU.get("C2:G17")
lowerStandings = StandingsL.get("C2:G29")

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

class Client(commands.Bot):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        try:
            guild = discord.Object(id=761274425475072010)
            synced = await self.tree.sync(guild=guild)
            print(f'Synced {len(synced)} commands to guild {guild.id}')
        except Exception as e:
            print(f'Error syncing commands: {e}')

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
    league="(Optional) Choose a league to display standings for. Defaults to upper if no team is indicated.",
    team="(Optional) Choose a team to display standings.",
    shown="(Optional) Choose the number of teams shown. Defaults to 10 teams. 0 means show all."
)
@app_commands.choices(
    league=[
        app_commands.Choice(name="upper", value="upper"),
        app_commands.Choice(name="lower", value="lower")
    ]
)
async def standings(interaction: discord.Interaction, league: app_commands.Choice[str] = None, team: str = None, shown: str = "10"):
    maxTeams = 0 # placeholder for max teams there are
    if team is None:
        if (league is None or league.name == "upper"):
            embed = discord.Embed(title="2026 Upper League Standings", color=discord.Color.purple())
            embed.set_thumbnail(url="https://cdn.discordapp.com/icons/829182450185142312/f78172b9c494c081f4c4ca6da29b76e2.png?size=1024")
            embed.add_field(
                name="Team",
                value="\n".join([f"**{index+1}: {university}** ({score} Points, {bucholz} Bucholz, {point_differential} Point Differential)" 
                             for index, (university, score, bucholz, point_differential,games_played) in enumerate(upperStandings[:min(int(shown),10)])]),
                inline=True
            ) # fix with buttons later
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(title="2026 Lower League Standings", color=discord.Color.purple())
            embed.set_thumbnail(url="https://cdn.discordapp.com/icons/829182450185142312/f78172b9c494c081f4c4ca6da29b76e2.png?size=1024")
            embed.add_field(
                name="Team",
                value="\n".join([f"**{index+1}: {university}** ({score} Points, {bucholz} Bucholz, {point_differential} Point Differential)" 
                             for index, (university, score, bucholz, point_differential,games_played) in enumerate(lowerStandings[:min(int(shown),10)])]),
                inline=True
            ) # fix with buttons later
            await interaction.response.send_message(embed=embed)
    else:
         def find_university_info(university_name):
            for index, (university, score, bucholz, point_differential, games_played) in enumerate(lowerStandings + upperStandings):
                if university_name == university:
                    if (index+1-len(lowerStandings))>0:
                        return index+1-len(lowerStandings), score, bucholz, point_differential, games_played
                    else:
                        return index+1, score, bucholz, point_differential, games_played
         rank, score, bucholz, point_differential, games_played = find_university_info(team)
         embed = discord.Embed(title=f'2026 {team} Standings', color=discord.Color.purple())
         embed.set_thumbnail(url="https://cdn.discordapp.com/icons/829182450185142312/f78172b9c494c081f4c4ca6da29b76e2.png?size=1024")
         embed.add_field(name="Record", value=f'{score}-{int(games_played)-int(score)}', inline=True)
         embed.add_field(name="Rank", value=rank, inline=True)
         embed.add_field(name="", value="", inline=False)
         embed.add_field(name="Bucholz", value=bucholz, inline=True)
         embed.add_field(name="Point Differential", value=point_differential, inline=True)
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