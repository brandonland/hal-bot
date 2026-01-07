import os
import json
import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
GUILD_OBJ = discord.Object(id=GUILD_ID)
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

def init_reminder():
    if not os.path.exists('reminder.json'):
        with open('reminder.example.json', 'r') as f:
            example_data = json.load(f)
        with open('reminder.json', 'w') as f:
            json.dump(example_data, f, indent=4)

def load_reminder():
    try:
        with open('reminder.json', 'r') as f:
            data = json.load(f)
            return data.get('reminder', 'Default reminder')
    except (FileNotFoundError, json.JSONDecodeError):
        return "# DVDuesday Reminder (file not found error!)"

def update_reminder(message):
    data = { 'reminder': message }
    with open('reminder.json', 'w') as f:
        json.dump(data, f, indent=4)

class Client(commands.Bot):
    async def on_ready(self):
        init_reminder()
        channel = self.get_channel(CHANNEL_ID)
        print(f'Logged in as {self.user}!')
        print(f'Current reminder: {load_reminder()}')

        if not channel:
            print('Error: channel not found!')

        try:
            synced = await self.tree.sync(guild=GUILD_OBJ)
            print(f'Synced {len(synced)} commands to guild {GUILD_OBJ.id}')
        except Exception as e:
            print(f'Error occurred while syncing commands: {e}')
            
        send_reminder.start()
    

intents = discord.Intents.default()
intents.message_content = True
client = Client(command_prefix="!", intents=intents)

@tasks.loop(minutes=1) # Check every minute
async def send_reminder():
    now = datetime.now(timezone.utc)  # Current UTC time

    if now.weekday() == 1:  # (0=Monday, 1=Tuesday, ...)
        time_to_send = now.replace(hour=17, minute=0, second=0, microsecond=0) # set to 17:00 UTC (noon EST)
        if now >= time_to_send and now < time_to_send + timedelta(minutes=1): # sends the reminder *within the minute*
            channel = client.get_channel(CHANNEL_ID)
            if channel:
                await channel.send(load_reminder())

@client.tree.command(name="seereminder", description="See the reminder message (only visible to you)", guild=GUILD_OBJ)
async def get_reminder(interaction: discord.Interaction):
    reminder = load_reminder()
    await interaction.response.send_message(reminder, ephemeral=True)

@client.tree.command(name="postreminder", description="Make the bot say the reminder message (visible to all!)", guild=GUILD_OBJ)
async def say_reminder(interaction: discord.Interaction):
    reminder = load_reminder()
    await interaction.response.send_message(reminder)

@client.tree.command(name="setreminder", description="Set the reminder message", guild=GUILD_OBJ)
async def set_reminder(interaction: discord.Interaction, new_reminder: str):
    update_reminder(new_reminder)
    await interaction.response.send_message(f"The reminder has been updated! The new reminder will appear as:\n{new_reminder} ", ephemeral=True)


client.run(TOKEN)
