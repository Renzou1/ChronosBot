import os
from dotenv import load_dotenv
import discord
from discord import Intents, Client, Message, app_commands
import database_commands
import format
from datetime import datetime

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

intents: Intents = Intents.default()
intents.message_content = True
client: Client = Client(intents=intents)
tree = app_commands.CommandTree(client)

async def send_message(message: Message, user_message: str, to_send) -> None:
    if not user_message:
        print("empty message")
        return
    return    


@tree.command(
        name="startworking",
        description="begins tracking your working hours",
)

async def start_working(interaction: discord.Interaction):
    guild_id = interaction.guild_id
    worker_id = interaction.user.id
    datetime = interaction.created_at
    response = database_commands.start_working(guild_id, worker_id, datetime)

    await interaction.response.send_message(response)

@tree.command(
        name="stopworking",
        description="finishes tracking your working hours",
)

async def stop_working(interaction: discord.Interaction):
    guild_id = interaction.guild_id
    worker_id = interaction.user.id
    datetime = interaction.created_at
    response = database_commands.stop_working(guild_id, worker_id, datetime)

    await interaction.response.send_message(response)

@tree.command(
        name="status",
        description="tells you your current working status",
)

async def status(interaction: discord.Interaction):
    guild_id = interaction.guild_id
    worker_id = interaction.user.id
    datetime = interaction.created_at
    response =  database_commands.status(guild_id, worker_id, datetime)

    await interaction.response.send_message(response)

@tree.command(
        name="deletesession",
        description="deletes YOUR session with specified id in month/year",
)

async def deletesession(interaction: discord.Interaction, 
                        session_id: int,
                        month: int, 
                        year: int = datetime.now().year):
    if month < 0 or month > 12:
        await interaction.response.send_message("Invalid month.")
        return
    guild_id = interaction.guild_id
    response = database_commands.delete_session(guild_id, interaction.user.id, session_id, month, year)

    await interaction.response.send_message(response)    

@tree.command(
        name="calculatehours",
        description="prints hour registry for a given month for a given user",
)

async def calculate_hours(interaction: discord.Interaction, 
                          member: discord.Member, month: int,
                          year: int = datetime.now().year):
    if month < 0 or month > 12:
        await interaction.response.send_message("Invalid month.")
        return

    guild_id = interaction.guild_id
    hours_worked = database_commands.calculate_work_hours(guild_id, member.id, month, year)
    start, end, diffs = database_commands.get_sessions(guild_id, member.id, month, year)

    line = "-------------------------------------------\n"

    response = "```js\nUser %s - Hour Registry - Month %02d - Year %d:\n\n" % (member.name, month, year)
    response += "sessionXX (dates) | start -> end | hh:mm:ss\n"
    response += line
    for i in range(len(start)):
        if end[i] == None:
            break
        response += "session%02d (%02d/%02d) | %02d:%02d->%02d:%02d | %02d:%02d:%02d\n" % (i, start[i].day, start[i].month, start[i].hour, start[i].minute, end[i].hour, end[i].minute, diffs[i][0], diffs[i][1], diffs[i][2])

    response += line
    response += "total: %s ```" % format.time_worked(hours_worked * 60 * 60)

    await interaction.response.send_message(response)

@tree.command(
        name="timezone",
        description="Sets timezone for the server to specified UTC",
)

async def timezone(interaction: discord.Interaction, utc: int):
    if utc < -12 or utc > 14:
        await interaction.response.send_message("Invalid UTC.")
        return
    
    database_commands.timezone(interaction.guild_id, utc)
    await interaction.response.send_message("UTC set to %d." % utc)

@client.event
async def on_ready():
    await tree.sync()
    print("Running")

@client.event
async def on_message(message: Message):
    if message.author == client.user:
        return

    username = str(message.author)
    user_message = message.content
    channel = str(message.channel)

    await send_message(message, user_message, message.author.id)

def main() -> None:
    client.run(token=DISCORD_TOKEN)

if __name__ == '__main__':
    main()