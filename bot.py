from __future__ import annotations

import os
import json
import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

import traceback

load_dotenv()

TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
GUILD_OBJ = discord.Object(id=GUILD_ID)
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

# UPLOADS_PATH = os.path.join(os.path.dirpath())
REMINDER_PATH = os.path.join(os.path.dirname(__file__), 'reminder.json')
EXAMPLE_REMINDER_PATH = os.path.join(os.path.dirname(__file__), 'reminder.example.json')

def init_reminder():
    if not os.path.exists(REMINDER_PATH):
        with open(EXAMPLE_REMINDER_PATH, 'r') as f:
            example_data = json.load(f)
        with open(REMINDER_PATH, 'w') as f:
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
    
class BaseModal(discord.ui.Modal):
    _interaction: discord.Interaction | None = None

    async def on_submit(self, interaction: discord.Interaction) -> None:
        # if not responded to, defer interaction
        if not interaction.response.is_done():
            await interaction.response.defer()
        self._interaction = interaction
        self.stop()

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        tb = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        message = f"An error occurred while processing the interaction:\n```py\n{tb}\n```"
        try:
            await interaction.response.send_message(message, ephemeral=True)
        except:
            await interaction.edit_original_response(content=message, view=None)
        self.stop()
        
    @property
    def interaction(self) -> discord.Interaction | None:
        return self._interaction


class ReminderSetModal(BaseModal, title="Set the reminder"):
    # reminder_title = discord.ui.TextInput(label="Reminder title", placeholder="Enter a message title (optional)", required=False, min_length=1, max_length=2000, style=discord.TextStyle.long)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.reminder_msg = discord.ui.TextInput(
            label="Reminder message body",
            placeholder="Enter a new reminder message",
            required=True, min_length=1,
            max_length=2000,
            style=discord.TextStyle.long
        )
        self.add_item(self.reminder_msg)
    
    async def on_submit(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(
            title="Reminder updated. The new reminder will appear as:",
            description=self.reminder_msg.value,
            color=discord.Color.random()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        update_reminder(self.reminder_msg.value)
        await super().on_submit(interaction)


async def do_reminder(inter: discord.Interaction, ephemeral=False):
    reminder = load_reminder()
    file = discord.File("uploads/reminder-banner.jpg", filename="reminder-banner.jpg")
    embed = discord.Embed(description=reminder, color=discord.Color.random())
    await inter.response.send_message(file=file, embed=embed, ephemeral=ephemeral)
    

class ReminderCommandGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="reminder", description="Reminder commands", guild_ids=[GUILD_ID])
        
    @app_commands.command(name="view", description="Privately see the reminder message (only visible to you)")
    async def reminder_view(self, interaction: discord.Interaction):
        await do_reminder(interaction, ephemeral=True)

    @app_commands.command(name="edit", description="Edit a new reminder message")
    async def reminder_edit(self, interaction: discord.Interaction):
        modal = ReminderSetModal()
        modal.reminder_msg.default = load_reminder()
        await interaction.response.send_modal(modal)

    @app_commands.command(name="post", description="Make the bot send the reminder as a message (⚠️ CAUTION! Visible to all! ⚠️)")
    async def reminder_post(self, interaction: discord.Interaction):
        await do_reminder(interaction)


intents = discord.Intents.default()
intents.message_content = True
bot = Client(command_prefix="!", intents=intents)

@tasks.loop(minutes=1) # Check every minute
async def send_reminder():
    now = datetime.now(timezone.utc)  # Current UTC time

    if now.weekday() == 1:  # (0=Monday, 1=Tuesday, ...)
        time_to_send = now.replace(hour=17, minute=0, second=0, microsecond=0) # set to 17:00 UTC (noon EST)
        if now >= time_to_send and now < time_to_send + timedelta(minutes=1): # sends the reminder *within the minute*
            channel = bot.get_channel(CHANNEL_ID)
            if channel:
                reminder = load_reminder()
                file = discord.File("uploads/reminder-banner.jpg", filename="reminder-banner.jpg")
                embed = discord.Embed(description=reminder, color=discord.Color.random())
                await channel.send(file=file, embed=embed)

@send_reminder.after_loop
async def after_reminder():
    print(f"Reminder sent automatically at {datetime.now(timezone.utc)} UTC time.\n\nReminder:\n{load_reminder()}")

reminder_cmd = ReminderCommandGroup()
bot.tree.add_command(reminder_cmd)
bot.run(TOKEN)
