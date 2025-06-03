# imports
import discord
from discord.ext import commands
from discord import app_commands

import requests

from dotenv import load_dotenv
import os

import gspread
from google.oauth2.service_account import Credentials

# credentials for google sheets api
scopes = [
    "https://www.googleapis.com/auth/spreadsheets"
]
creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
sheetsClient = gspread.authorize(creds)

# opening the google sheets document
sheet_id = "1vr2ltnMgevSpoeI3HAT5emdaU07G7AgjjItbz7hDFdg"
workbook = sheetsClient.open_by_key(sheet_id)

# google sheets worksheets
TestSheet = workbook.worksheet("Sheet1")
Seedings = workbook.worksheet("Seedings")
MatchupsU = workbook.worksheet("MatchupsU")
StandingsU = workbook.worksheet("Standings for 2025U")
MatchupsL = workbook.worksheet("MatchupsL")
StandingsL = workbook.worksheet("Standings for 2025L")
MatchInfo = workbook.worksheet("MatchInfo")

# getting info from each worksheet

# matchinfo sheet
team1name = 1  # name of team 1
team2name = 12  # name of team 2
team1lineupentry = 2  # first entry of team 1 lineup
team2lineupentry = 7  # first entry of team 2 lineup
roundinfo = 13  # round 1 scoring entry
matchsubmissionstatus = 18  # whether the match is finalized or not
team1role = 19  # role id of team 1
team2role = 20  # role id of team 2

# round information data storage
team1player = 0
team1submission_team1score = 1
team1submission_team2score = 2
team2submission_team1score = 3
team2submission_team2score = 4
team2player = 5
scorevalidation = 6

# loading discord bot token from .env
load_dotenv()
token = os.getenv('DISCORD_TOKEN')

# turning on the bot
class Client(commands.Bot):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        guild_ids = [761274425475072010,1163677315553824768,1375638530126119062]
        try:
            for guild_id in guild_ids:
                guild = discord.Object(id=guild_id)
                synced = await self.tree.sync(guild=guild)
                print(f'Synced {len(synced)} commands to guild {guild.id}')
        except Exception as e:
            print(f'Error syncing commands: {e}')

# discord intents (permissions)
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
client = Client(command_prefix="!", intents=intents, activity = discord.Game(name="TETR.IO"), status=discord.Status.idle)

# helper function for team autocomplete
def team_autocomplete(current: str):
    teams = Seedings.col_values(1)[1:]
    filtered = [team for team in teams if current.lower() in team.lower()]
    limited = filtered[:25]
    return [
        app_commands.Choice(name=team, value=team)
        for team in limited
    ]

# helper function for player autocomplete
def player_autocomplete(current:str):
    player_list = Seedings.batch_get(["D2:H","N2:R"])
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

# helper function for generating results from a round
def generateresultsembed(matchid):
    round1, round2, round3, round4, round5 = [MatchInfo.cell(matchid,i).value for i in range(roundinfo,roundinfo+5)]
    results = ""
    team1score = 0
    team2score = 0
    team1rounds = 0
    team2rounds = 0
    team1lineup = [MatchInfo.cell(matchid,i).value for i in range(team1lineupentry,team1lineupentry+5)]
    team2lineup = [MatchInfo.cell(matchid,i).value for i in range(team2lineupentry,team2lineupentry+5)]
    winner = 0
    for round in [round1, round2, round3, round4, round5]:  # for each round
        player1 = int(round[team1player])-1
        player2 = int(round[team2player])-1
        # add player 1
        if player1 == -1:
            results += "**N/A** "
        else:
            results += f'**[{team1lineup[player1]}](https://ch.tetr.io/u/{team1lineup[player1]})** '
        # add score
        results += f'{round[team1submission_team1score]} - {round[team2submission_team2score]} '
        # add player 2
        if player2 == -1:
            results += "**N/A**\n"
        else:
            results += f'**[{team2lineup[player2]}](https://ch.tetr.io/u/{team2lineup[player2]})**\n'
        # adjust total scores
        team1score += int(round[team1submission_team1score])
        team2score += int(round[team1submission_team2score])
        # count rounds for tiebreaker
        if int(round[team1submission_team1score]) > int(round[team1submission_team2score]):
            team1score += 1
            team1rounds += 1
        elif int(round[team1submission_team1score]) < int(round[team1submission_team2score]):
            team2score += 1
            team2rounds += 1
        # determine winner
        if team1score > team2score:
            winner = 1
        elif team1score < team2score:
            winner = 2
        else:
            if team1rounds > team2rounds:
                winner = 1
            elif team1rounds < team2rounds:
                winner = 1
    embed = discord.Embed(title=f'Match {matchid} Results', color=discord.Color.purple())
    embed.add_field(
        name=f'{MatchInfo.cell(matchid,1).value} {"(W)" if winner == 1 else "(L)"} {team1score} - {team2score} {"(W)" if winner == 2 else "(L)"} {MatchInfo.cell(matchid,12).value}',
        value=results,
        inline=True
    )
    return embed

# helper function for checking and authorizing team roles for a match
def checkRoles(user: object, matchid: int):
    for role in user.roles:
        if role.id == int(MatchInfo.cell(matchid,team1role).value):
            print("Authorized.")
            return 1
        elif role.id == int(MatchInfo.cell(matchid,team2role).value):
            print("Authorized.")
            return 2
    return 0

# guild ids
GUILD_IDS = [discord.Object(id=761274425475072010), discord.Object(id=1163677315553824768),discord.Object(id=1375638530126119062)]
    
for GUILD_ID in GUILD_IDS:
    
    # help command: display list of commands
    @client.tree.command(name="help", description="Display a list of all commands.", guild=GUILD_ID)
    async def help(interaction: discord.Interaction):
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

    # getstats command: get tetrio stats of a user using tetrio api
    @client.tree.command(name="getstats", description="Get the stats of any TETR.IO user!", guild=GUILD_ID)
    @app_commands.describe(
        username="Username of the TETR.IO user to search."
    )
    async def getStats(interaction: discord.Interaction, username: str):
        league_url = f"https://ch.tetr.io/api/users/{username.lower()}/summaries/league"
        user_url = f"https://ch.tetr.io/api/users/{username.lower()}"
        headers = {"User-Agent": "aaronthmetic"}
        league = requests.get(league_url, headers=headers)
        if league.status_code == 200:
            user = requests.get(user_url, headers=headers)
            data = league.json().get("data", {})
            userdata = user.json().get("data", {})
            embed = discord.Embed(title=f'{username.upper()}\'s Stats', color=discord.Color.purple())
            embed.set_thumbnail(url=f'https://tetr.io/user-content/avatars/{ userdata.get("_id") }.jpg?rv={ userdata.get("avatar_revision") }')
            embed.add_field(
                    name="Rank",
                    value=data.get("rank", -1).upper(),
                    inline=True
                )
            embed.add_field(
                    name="TR",
                    value=round(data.get("tr", -1)),
                    inline=True
                )
            embed.add_field(
                    name="Glicko",
                    value=round(data.get("glicko", -1), 2),
                    inline=True
                )
            embed.add_field(
                    name="APM",
                    value=round(data.get("apm", -1) or -1, 2),
                    inline=True
                )
            embed.add_field(
                    name="PPS",
                    value=round(data.get("pps", -1) or -1, 2),
                    inline=True
                )
            embed.add_field(
                    name="VS",
                    value=round(data.get("vs", -1) or -1, 2),
                    inline=True
                )
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(f"Error {league.status_code}: Access denied.")

    # pagination for standings, still wip
    class View(discord.ui.View):
        @discord.ui.button(style=discord.ButtonStyle.gray, emoji="⬅️")
        async def backward(self, interaction=discord.Interaction, button=discord.ui.Button):
            await interaction.response.send_message("this should go back a page", ephemeral=True)
        @discord.ui.button(style=discord.ButtonStyle.gray, emoji="➡️")
        async def forward(self, interaction=discord.Interaction, button=discord.ui.Button):
            await interaction.response.send_message("this should go forward a page", ephemeral=True)
        
    # standings command: show the standings for a certain league / team
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
        teams = Seedings.col_values(1)[1:]
        upperStandings = StandingsU.get("C2:G17")
        lowerStandings = StandingsL.get("C2:G29")
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
        return team_autocomplete(current)

    # roster command: show a team's roster
    @client.tree.command(name="roster", description="Display the full roster of a team.", guild=GUILD_ID)
    @app_commands.describe(team="Select a team.")
    async def roster(interaction: discord.Interaction, team: str):
        rosters = Seedings.get("A2:R45")
        teams = Seedings.col_values(1)[1:]
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
        return team_autocomplete(current)
    
    # add validation of team status
    @client.tree.command(name="setlineup", description="Set your team's lineup for a match", guild=GUILD_ID) # modify this later for team from roles
    @app_commands.describe(
        matchid="Match ID",
        p1="Player 1 (Optional: N/A if left unfilled)",
        p2="Player 2 (Optional: N/A if left unfilled)",
        p3="Player 3 (Optional: N/A if left unfilled)",
        p4="Player 4 (Optional: N/A if left unfilled)",
        p5="Player 5 (Optional: N/A if left unfilled)"
    )
    async def setlineup(interaction: discord.Interaction, matchid: int, p1: str = "N/A", p2: str = "N/A", p3: str = "N/A", p4: str = "N/A", p5: str = "N/A"):
        rosters = Seedings.get("A2:R45")
        position = team2lineupentry
        team = ""
        message = ""
        if matchid > len(MatchInfo.get("A:A")):
            await interaction.response.send_message("Invalid match ID.", ephemeral=True)
        elif MatchInfo.cell(matchid,13).value is not None and MatchInfo.cell(matchid,13).value[0] != '0' and MatchInfo.cell(matchid,13).value[5] != '0':
            await interaction.response.send_message("Match has already started. Lineups cannot be modified.", ephemeral=True)
        else:
            user = interaction.user
            teamAssign = checkRoles(user, matchid)
            if teamAssign != 0:
                if teamAssign == 2:
                    position = team2lineupentry
                    team = MatchInfo.cell(matchid, team2name).value
                    if MatchInfo.cell(matchid,roundinfo).value is not None and MatchInfo.cell(matchid,roundinfo).value[team2player] != '0':
                        message = "⚠️ **WARNING:** You have already made a blindpick. This lineup change may change your blindpick."
                else:
                    team = MatchInfo.cell(matchid, team1name).value
                    if MatchInfo.cell(matchid,roundinfo).value is not None and MatchInfo.cell(matchid,roundinfo).value[team1player] != '0':
                        message = "⚠️ **WARNING:** You have already made a blindpick. This lineup change may change your blindpick."
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
                    await interaction.response.send_message(message, embed=embed, ephemeral=True)
                    for i, player in enumerate([p1, p2, p3, p4, p5]):
                        MatchInfo.update_cell(matchid, position + i, player)
            else:
                await interaction.response.send_message("You are not authorized to set a lineup for this match.", ephemeral=True)

    for player in ['p1', 'p2', 'p3', 'p4', 'p5']:
        @setlineup.autocomplete(player)
        async def roster_autocomplete(interaction: discord.Interaction, current: str):
            return player_autocomplete(current)
    
    # lineups command: show lineups for a match
    @client.tree.command(name="lineups", description="See lineups for a match.", guild=GUILD_ID)
    @app_commands.describe(matchid="Match ID")
    async def lineups(interaction:discord.Interaction, matchid: int):
        if matchid > len(MatchInfo.get("A:A")):
            await interaction.response.send_message("Invalid match ID.", ephemeral=True)
        else:
            embed = discord.Embed(title=f'Match {matchid}', color=discord.Color.purple())
            embed.add_field(
                name=MatchInfo.cell(matchid,1).value,
                value="\n".join(f'**[{player}](https://ch.tetr.io/u/{player})**' if player != "N/A" and player is not None else "**N/A**"
                    for player in [MatchInfo.cell(matchid,i).value for i in range(2,7)]),
                inline=True
            )
            embed.add_field(
                name=MatchInfo.cell(matchid,12).value,
                value="\n".join(f'**[{player}](https://ch.tetr.io/u/{player})**' if player != "N/A" and player is not None else "**N/A**"
                    for player in [MatchInfo.cell(matchid,i).value for i in range(7,12)]),
                inline=True
            )
            await interaction.response.send_message(embed=embed)
            
    # blindpick command: blindpicking
    @client.tree.command(name="blindpick", description="Blindpick for a scheduled match.", guild=GUILD_ID) # modify this later for team from roles
    @app_commands.describe(matchid="Match ID", team="Your team")
    async def blindpick(interaction:discord.Interaction, matchid: int, team: str):
        if matchid > len(MatchInfo.get("A:A")):
            await interaction.response.send_message("Invalid match ID.", ephemeral=True)
        elif team not in [MatchInfo.cell(matchid,1).value,MatchInfo.cell(matchid,12).value]:
            await interaction.response.send_message("Invalid team.", ephemeral=True)
        elif MatchInfo.cell(matchid,13).value is not None and MatchInfo.cell(matchid,13).value[0] != '0' and MatchInfo.cell(matchid,13).value[5] != '0':
            await interaction.response.send_message("Match has already been started.", ephemeral=True)
        else:
            if (team == MatchInfo.cell(matchid,1).value and MatchInfo.cell(matchid,1).value is None) or (team == MatchInfo.cell(matchid,12).value and MatchInfo.cell(matchid,7).value is None):
                await interaction.response.send_message("Roster must be set.", ephemeral=True)
            else:
                class Select(discord.ui.Select):
                    def __init__(self, author:discord.User):
                        self.author = author
                        if team == MatchInfo.cell(matchid,1).value:
                            options=[discord.SelectOption(label=player, value=f'{index}:{player}') for index, player in enumerate([MatchInfo.cell(matchid,i).value for i in range(2,7)])]
                        else:
                            options=[discord.SelectOption(label=player, value=f'{index}:{player}') for index, player in enumerate([MatchInfo.cell(matchid,i).value for i in range(7,12)])]
                        super().__init__(placeholder="Select a player to blindpick.",max_values=1,min_values=1,options=options)
                    async def callback(self, interaction: discord.Interaction):
                        if interaction.user.id != self.author.id:
                            await interaction.response.send_message(
                                "You are not allowed to use this select menu.", ephemeral=True
                            )
                            return
                        if team == MatchInfo.cell(matchid,1).value:
                            selected_value = self.values[0]
                            index_str, player = selected_value.split(":", 1)
                            index = int(index_str)
                            await interaction.response.send_message(f'You have selected to blindpick {player}.',ephemeral=True)
                            MatchInfo.update_cell(
                                matchid,
                                13,
                                (f'{index+1}000000' if MatchInfo.cell(matchid,13).value is None
                                 else str(index+1)+MatchInfo.cell(matchid,13).value[1:])
                            )
                        else:
                            selected_value = self.values[0]
                            index_str, player = selected_value.split(":", 1)
                            index = int(index_str)
                            await interaction.response.send_message(f'You have selected to blindpick {player}.',ephemeral=True)
                            MatchInfo.update_cell(
                                matchid,
                                13,
                                (f'00000{index+1}0' if MatchInfo.cell(matchid,13).value is None
                                 else MatchInfo.cell(matchid,13).value[:5]+str(index+1)+'0')
                            )
                        for child in self.view.children:
                            child.disabled = True
                        await interaction.message.edit(view=self.view)
                        if MatchInfo.cell(matchid,13).value[0] != '0' and MatchInfo.cell(matchid,13).value[5] != '0':
                            embed = discord.Embed(title=f'Match {matchid} Blindpick Results', color=discord.Color.purple())
                            blindpicked1 = MatchInfo.cell(matchid, 1 + int(MatchInfo.cell(matchid,13).value[0])).value
                            blindpicked2 = MatchInfo.cell(matchid, 6 + int(MatchInfo.cell(matchid,13).value[5])).value
                            embed.add_field(
                                name=MatchInfo.cell(matchid,1).value,
                                value=(f'**[{blindpicked1}](https://ch.tetr.io/u/{blindpicked1})**' if blindpicked1 != "N/A" else "**N/A**"),
                                inline=True
                            )
                            embed.add_field(
                                name=MatchInfo.cell(matchid,12).value,
                                value=(f'**[{blindpicked2}](https://ch.tetr.io/u/{blindpicked2})**' if blindpicked2 != "N/A" else "**N/A**"),
                                inline=True
                            )
                            await interaction.followup.send(embed=embed)
                class SelectView(discord.ui.View):
                    def __init__(self, author: discord.User, *, timeout=180):
                        super().__init__(timeout=timeout)
                        self.add_item(Select(author))
                await interaction.response.send_message(view=SelectView(interaction.user))
    
    @blindpick.autocomplete('team')
    async def roster_autocomplete(interaction: discord.Interaction, current: str):
        return team_autocomplete(current)
    
    # matchresults command: shows match results
    @client.tree.command(name="matchresults", description="Shows match results for a given match.", guild=GUILD_ID)
    async def matchresults(interaction:discord.Interaction, matchid: int):
        if matchid > len(MatchInfo.get("A:A")):
            await interaction.response.send_message("Invalid match ID.", ephemeral=True)
        elif (MatchInfo.cell(matchid,18).value == "FALSE"):
            await interaction.response.send_message("Match not completed.", ephemeral=True)
        else:
            await interaction.response.defer()
            embed = generateresultsembed(matchid)
            await interaction.followup.send(embed=embed)

    # forfeitmatch command: organizers can forfeit a match on behalf of a team
    @client.tree.command(name="forfeitmatch", description="(Organizer Use) Forfeit a match for a team.", guild=GUILD_ID)
    @app_commands.describe(matchid="Match ID", team1="Team to lose by forfeit", team2="(Optional) Use in case of double forfeit.")
    async def forfeitmatch(interaction:discord.Interaction, matchid: int, team1: str, team2: str = None):
        if matchid > len(MatchInfo.get("A:A")):
            await interaction.response.send_message("Invalid match ID.", ephemeral=True)
        elif (MatchInfo.cell(matchid,18).value == "TRUE"):
            await interaction.response.send_message("Match already completed.", ephemeral=True)
        else:
            if (team1 == MatchInfo.cell(matchid,1).value and team2 == MatchInfo.cell(matchid,12).value) or (team1 == MatchInfo.cell(matchid,12).value and team2 == MatchInfo.cell(matchid,1).value):
                for i in range(13,18):
                    MatchInfo.update_cell(matchid, i, "0000001")
                await interaction.response.send_message(f'Double forfeited Match {matchid}.', ephemeral=True)
            elif team1 == MatchInfo.cell(matchid,1).value:
                if MatchInfo.cell(matchid,7).value is None:
                    await interaction.response.send_message("Roster must be set.", ephemeral=True)
                    return
                else:
                    for i in range(13,18):
                        MatchInfo.update_cell(matchid, i, f'00707{i-12}1')
                    await interaction.response.send_message(f'{team1} forfeited Match {matchid}.', ephemeral=True)
            elif team1 == MatchInfo.cell(matchid,12).value:
                if MatchInfo.cell(matchid,2).value is None:
                    await interaction.response.send_message("Roster must be set.", ephemeral=True)
                    return
                else:
                    for i in range(13,18):
                        MatchInfo.update_cell(matchid, i, f'{i-12}707001')
                    await interaction.response.send_message(f'{team1} forfeited Match {matchid}.', ephemeral=True)
            else:
                await interaction.response.send_message("Invalid team.", ephemeral=True)
                return
            MatchInfo.update_cell(matchid,18,"TRUE")
    
    @forfeitmatch.autocomplete('team1')
    async def roster_autocomplete(interaction: discord.Interaction, current: str):
        return team_autocomplete(current)
    
    @forfeitmatch.autocomplete('team2')
    async def roster_autocomplete(interaction: discord.Interaction, current: str):
        return team_autocomplete(current)
    
    # Submits a match score based on matchID and round. Need valid parameters and roles to set match information
    @client.tree.command(name="submitround", description="Submit round results.)", guild = GUILD_ID)
    @app_commands.describe(matchid="Match ID", round="Round Number", score1="Team 1 Score", score2="Team 2 Score")
    async def submitmatch(interaction:discord.Interaction, matchid: int, round: int, score1: int, score2: int):
        if matchid > len(MatchInfo.get("A:A")):
            await interaction.response.send_message("Invalid Match ID.", ephemeral=True)
        elif round not in range(1, 6):
            await interaction.response.send_message("Invalid round number.", ephemeral=True)
        elif score1 < 0 or score1 > 7 or score2 < 0 or score2 > 7:
            await interaction.response.send_message("Invalid score.", ephemeral=True)
        elif MatchInfo.cell(matchid, 12+round).value is None:
            await interaction.response.send_message("Round does not exist.", ephemeral=True)
        else:
            user = interaction.user
            teamAssign = checkRoles(user, matchid)
            if teamAssign != 0:
                gameValue = MatchInfo.cell(matchid, 12+round).value
                if teamAssign == 1:
                    gameValue = gameValue[0] + str(score1) + str(score2) + gameValue[3:]
                else:
                    gameValue = gameValue[:3] + str(score1) + str(score2) + gameValue[5:]
                validRound = False
                tempScore1 = gameValue[1:3]
                tempScore2 = gameValue[3:5]
                if(tempScore1 != tempScore2):
                    print("Score invalid.")
                    validRound = False
                else:
                    print("Score valid.")
                    validRound = True
                scoreString = "Score of " + str(score1) + " - " + str(score2) + " successfully submitted. "
                if validRound:
                    gameValue = gameValue[:6] + "1"
                    await interaction.response.send_message(scoreString + "Scores between both teams are matching! Round validated!", ephemeral=True)
                else:
                    if gameValue[6] == "1":
                        await interaction.response.send_message(scoreString + "You are changing a round that was considered valid. Please ensure you follow up with the opposing team and revalidate scores.", ephemeral=False)
                        gameValue = gameValue[:6] + "0"
                    else:
                        await interaction.response.send_message(scoreString + "Currently, scores for this round are not matching between teams. Please follow up with opposing team to confirm scores.", ephemeral=False)
                MatchInfo.update_cell(matchid, 12+round, gameValue)
            else:
                await interaction.response.send_message("You are not authorized to submit a score to this game.", ephemeral=True)

    # submitmatch command: submit the results of a match
    @client.tree.command(name="submitmatch", description="Submit the results of a given match.", guild=GUILD_ID)
    @app_commands.describe(matchid="Match ID")
    async def submitround(interaction:discord.Interaction, matchid: int):
        if matchid > len(MatchInfo.get("A:A")):
            await interaction.response.send_message("Invalid Match ID", ephemeral=True)
        else:
            user = interaction.user
            teamAssign = checkRoles(user, matchid)
            if teamAssign != 0:
                await interaction.response.defer()
                gameValues = [MatchInfo.cell(matchid, 13+round).value for round in range(5)]
                if all(value is not None and str(value)[-1] == '1' for value in gameValues):
                    await interaction.followup.send("Scores between both teams are matching. Match validated.", ephemeral=True, embed=generateresultsembed(matchid))
                    MatchInfo.update_cell(matchid, 18, "TRUE")
                else:
                    await interaction.followup.send("It appears this match cannot be finalized. Please follow up with opposing team to confirm scores.", ephemeral=False)
            else:
                await interaction.response.send_message("You are not authorized to submit this match.", ephemeral=True)

client.run(token)