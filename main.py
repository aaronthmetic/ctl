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
Lineups = workbook.worksheet("Lineups")

teams = Seedings.col_values(1)[1:]
rosters = Seedings.get("A2:R45")
player_list = Seedings.batch_get(["D2:H","N2:R"])
upperStandings = StandingsU.get("C2:G17")
lowerStandings = StandingsL.get("C2:G29")

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

class Client(commands.Bot):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        guild_ids = [761274425475072010,1163677315553824768]
        try:
            for guild_id in guild_ids:
                guild = discord.Object(id=guild_id)
                synced = await self.tree.sync(guild=guild)
                print(f'Synced {len(synced)} commands to guild {guild.id}')
        except Exception as e:
            print(f'Error syncing commands: {e}')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
client = Client(command_prefix="!", intents=intents, activity = discord.Game(name="TETR.IO"), status=discord.Status.idle)

GUILD_IDS = [discord.Object(id=761274425475072010), discord.Object(id=1163677315553824768)]
    
for GUILD_ID in GUILD_IDS:
    
    @client.tree.command(name="help", description="Display a list of all commands.", guild=GUILD_ID)
    async def help(interaction: discord.Interaction):
        embed = discord.Embed(title="Help", color=discord.Color.purple())
        embed.add_field(name="/help", value="Display this message!", inline=False)
        embed.add_field(name="/roster `[team]`", value="Display the roster of any team.", inline=False)
        embed.add_field(name="/standings `[league]` `[team]` `[shown]`", value="Display the standings or the record of a specific team. Entry for `team` overrides all other values. `league` defaults to upper league, `shown` defaults to 10.")
        await interaction.response.send_message(embed=embed)

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

    class View(discord.ui.View):
        @discord.ui.button(style=discord.ButtonStyle.gray, emoji="⬅️")
        async def backward(self, interaction=discord.Interaction, button=discord.ui.Button):
            await interaction.response.send_message("this should go back a page", ephemeral=True)
        @discord.ui.button(style=discord.ButtonStyle.gray, emoji="➡️")
        async def forward(self, interaction=discord.Interaction, button=discord.ui.Button):
            await interaction.response.send_message("this should go forward a page", ephemeral=True)
        
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
    async def standings(interaction: discord.Interaction, league: app_commands.Choice[str] = None, team: str = None, shown: int = 10):
        maxTeams = 0 # placeholder for max teams there are
        if team is None:
            if (league is None or league.value == "upper"):
                embed = discord.Embed(title="2026 Upper League Standings", color=discord.Color.purple())
                embed.set_thumbnail(url="https://cdn.discordapp.com/icons/829182450185142312/f78172b9c494c081f4c4ca6da29b76e2.png?size=1024")
                embed.add_field(
                    name="Team",
                    value="\n".join([f"**{index+1}: {university}** ({score} Points, {bucholz} Bucholz, {point_differential} Point Differential)" 
                                for index, (university, score, bucholz, point_differential,games_played) in enumerate(upperStandings[:min(shown,10)])]),
                    inline=True
                )
                await interaction.response.send_message(embed=embed, view=View())
            else:
                embed = discord.Embed(title="2026 Lower League Standings", color=discord.Color.purple())
                embed.set_thumbnail(url="https://cdn.discordapp.com/icons/829182450185142312/f78172b9c494c081f4c4ca6da29b76e2.png?size=1024")
                embed.add_field(
                    name="Team",
                    value="\n".join([f"**{index+1}: {university}** ({score} Points, {bucholz} Bucholz, {point_differential} Point Differential)" 
                        for index, (university, score, bucholz, point_differential,games_played) in enumerate(lowerStandings[:min(shown,10)])]),
                    inline=True
                )
                await interaction.response.send_message(embed=embed, view=View())
        else:
            if team not in teams:
                await interaction.response.send_message("Invalid team.", ephemeral=True)
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
        if team not in teams:
            await interaction.response.send_message("Invalid team.", ephemeral=True)
        else:
            def find_university_roster(university_name):
                    for info in rosters:
                        if info[0] == university_name:
                            return info
            embed = discord.Embed(title=f'2026 {team} Roster', color=discord.Color.purple())
            embed.set_thumbnail(url="https://cdn.discordapp.com/icons/829182450185142312/f78172b9c494c081f4c4ca6da29b76e2.png?size=1024")
            embed.add_field(
                name="Starters",
                value="\n".join(f'**[{player}](https://ch.tetr.io/u/{player})**'
                    for player in find_university_roster(team)[3:8]),
                inline=True
            )
            embed.add_field(
                name="Substitutes",
                value="\n".join(f'**[{player}](https://ch.tetr.io/u/{player})**'
                    for player in find_university_roster(team)[13:18]),
                inline=True
            )
            await interaction.response.send_message(embed=embed)

    @roster.autocomplete('team')
    async def roster_autocomplete(interaction: discord.Interaction, current: str):
        filtered = [team for team in teams if current.lower() in team.lower()]
        limited = filtered[:25]
        return [
            app_commands.Choice(name=team, value=team)
            for team in limited
        ]
    
    @client.tree.command(name="setlineup", description="Set your team's lineup for a match", guild=GUILD_ID)
    @app_commands.describe(
        matchid="Match ID",
        team="Your team",
        p1="Player 1 (Optional: N/A if left unfilled)",
        p2="Player 2 (Optional: N/A if left unfilled)",
        p3="Player 3 (Optional: N/A if left unfilled)",
        p4="Player 4 (Optional: N/A if left unfilled)",
        p5="Player 5 (Optional: N/A if left unfilled)"
    )
    async def setlineup(interaction: discord.Interaction, matchid: int, team: str, p1: str = "N/A", p2: str = "N/A", p3: str = "N/A", p4: str = "N/A", p5: str = "N/A"):
        position = 2
        if team not in [Lineups.cell(matchid,1).value,Lineups.cell(matchid,12).value]:
            await interaction.response.send_message("Invalid team.", ephemeral=True)
        else:
            if team == Lineups.cell(matchid,12).value:
                position = 7
            def find_university_roster(university_name):
                    for info in rosters:
                        if info[0] == university_name:
                            return info
            if not all (p in find_university_roster(team)[3:8] + find_university_roster(team)[13:18] + ["N/A"] for p in [p1, p2, p3, p4, p5]):
                await interaction.response.send_message("Invalid player.", ephemeral=True)
            else:
                embed = discord.Embed(title=f'Match {matchid}: {team}', color=discord.Color.purple())
                embed.add_field(
                    name="Lineup",
                    value="\n".join(f'**[{player}](https://ch.tetr.io/u/{player})**' if player != "N/A" else f'**{player}**'
                        for player in [p1,p2,p3,p4,p5]),
                    inline=True
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                for i, player in enumerate([p1, p2, p3, p4, p5]):
                    Lineups.update_cell(matchid, position + i, player)
    
    @setlineup.autocomplete('team')
    async def roster_autocomplete(interaction: discord.Interaction, current: str):
        filtered = [team for team in teams if current.lower() in team.lower()]
        limited = filtered[:25]
        return [
            app_commands.Choice(name=team, value=team)
            for team in limited
        ]
    for player in ['p1', 'p2', 'p3', 'p4', 'p5']:
        @setlineup.autocomplete(player)
        async def roster_autocomplete(interaction: discord.Interaction, current: str):
            filtered = list(dict.fromkeys(
                player
                for sublist1 in player_list
                for sublist2 in sublist1
                for player in sublist2
                if current.lower() in player.lower()
            ))
            limited = filtered[:25]
            return [
                app_commands.Choice(name=player, value=player)
                for player in limited
            ]

client.run(token)