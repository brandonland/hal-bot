import os
import asyncio
import json
import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import pprint

import traceback

load_dotenv()


TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
GUILD_OBJ = discord.Object(id=GUILD_ID)
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
REMINDER_PATH = os.path.join(os.path.dirname(__file__), "reminder.json")
EXAMPLE_REMINDER_PATH = os.path.join(os.path.dirname(__file__), "reminder.example.json")
REMINDER_BANNER_PATH = "uploads/reminder-banner.jpg"
REMINDER_BANNER_PATH_ABS = os.path.join(os.path.dirname(__file__), REMINDER_BANNER_PATH)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(intents=intents)

reminder = bot.create_group("reminder", "Reminder commands", guild_ids=[GUILD_ID])
reminder_edit = reminder.subgroup("edit", "Edit reminder", guild_ids=[GUILD_ID])

def init_reminder():
    if not os.path.exists(REMINDER_PATH):
        with open(EXAMPLE_REMINDER_PATH, "r") as f:
            example_data = json.load(f)
        with open(REMINDER_PATH, "w") as f:
            json.dump(example_data, f, indent=4)


def load_reminder():
    try:
        with open("reminder.json", "r") as f:
            data = json.load(f)
            return data.get("reminder", "Default reminder")
    except (FileNotFoundError, json.JSONDecodeError):
        return "# DVDuesday Reminder (file not found error!)"


def update_reminder(message):
    data = {"reminder": message}
    with open("reminder.json", "w") as f:
        json.dump(data, f, indent=4)


async def send_reminder(
    ctx: discord.ApplicationContext = None,
    *,
    inter: discord.Interaction = None,
    reminder=None,
    ephemeral=False,
    automatic=False,
    channel=None,
    followup=False,
):
    if not reminder:
        reminder = load_reminder()

    file = discord.File("uploads/reminder-banner.jpg", filename="reminder-banner.jpg")
    embed = discord.Embed(description=reminder, color=discord.Color.random())
    embed.set_image(url="attachment://reminder-banner.jpg")

    if not automatic:
        if not followup and ctx is not None:
            print("not followup and ctx")
            await ctx.respond(embed=embed, file=file, ephemeral=ephemeral)
        elif not followup and inter is not None:
            print("not followup and inter")
            await inter.respond(embed=embed, file=file, ephemeral=ephemeral)
        elif followup and ctx:
            print("followup and ctx")
            await ctx.send_followup(embed=embed, file=file, ephemeral=ephemeral)
        elif followup and inter:
            print("followup and inter")
            await inter.followup.send(embed=embed, file=file, ephemeral=ephemeral)
    elif automatic and channel is not None:
        await channel.send(embed=embed, file=file)


class ReminderEditModal(discord.ui.DesignerModal):
    def __init__(self, img_only=False, msg_only=False, *args, **kwargs) -> None:
        if img_only:
            print("image only!")
        elif msg_only:
            print("message only!")

        text_input = discord.ui.Label(
            "Reminder message body",
            discord.ui.TextInput(
                value=load_reminder(),
                placeholder="Create/edit your reminder message",
                required=False,
                style=discord.InputTextStyle.long,
            ),
        )

        image_file = discord.ui.Label(
            "Upload a banner image (Optional)",
            discord.ui.FileUpload(
                max_values=1,
                required=False,
            ),
            description="If you already uploaded an image, ignore this.",
        )
        super().__init__(
            text_input,
            image_file,
            *args,
            **kwargs,
        )

    async def callback(self, inter: discord.Interaction):
        await inter.response.defer()
        await inter.followup.send("Reminder Set. Preview below:")
        embed = discord.Embed(
            description=self.children[0].item.value,
            color=discord.Color.random(),
        )
        attachment = (
            self.children[1].item.values[0] if self.children[1].item.values else None
        )
        if attachment:  # Only save to disk if a file was uploaded
            await attachment.save(REMINDER_BANNER_PATH_ABS)

        # Preview embed
        # await inter.followup.send(
        #     embeds=[embed],
        #     files=[await attachment.to_file()] if attachment else [],
        #     ephemeral=True,
        # )
        await send_reminder(inter=inter, followup=True, ephemeral=True)


@bot.event
async def on_ready():
    init_reminder()
    channel = bot.get_channel(CHANNEL_ID)
    print(f"Logged in as {bot.user}!")
    print(f"Current reminder: {load_reminder()}")

    if not channel:
        print("Error: channel not found!")


@reminder.command(
    name="view",
    description="(Only visible to you) See the reminder message",
)
async def reminder_view(ctx: discord.ApplicationContext):
    await send_reminder(ctx, ephemeral=True)


@reminder.command(
    name="edit", description="Edit a new reminder message"
)
async def reminder_edit(ctx: discord.ApplicationContext, image: discord.Attachment=None):
    if image:
        # file = await image.to_file()
        await image.save(REMINDER_BANNER_PATH_ABS)
        await ctx.respond("Image uploaded! Here is a private preview:", ephemeral=True)
        await send_reminder(ctx, followup=True, ephemeral=True)
    else:
        modal = ReminderEditModal(title="Edit the reminder")
        await ctx.send_modal(modal)



# TODO: have a confirm/prompt modal: "Are you sure you want to...?"
@reminder.command(
    name="post",
    description="Manually announce the reminder in this channel (⚠️ CAUTION! Visible to all! ⚠️)",
)
async def reminder_post(ctx: discord.ApplicationContext):
    await send_reminder(ctx)


# TODO: automatic reminders (migrate to pycord!)

# @tasks.loop(minutes=1) # Check every minute
# async def send_auto_reminder():
#     now = datetime.now(timezone.utc)  # Current UTC time

#     if now.weekday() == 1:  # (0=Monday, 1=Tuesday, ...)
#         time_to_send = now.replace(hour=17, minute=0, second=0, microsecond=0) # set to 17:00 UTC (noon EST)
#         if now >= time_to_send and now < time_to_send + timedelta(minutes=1): # sends the reminder *within the minute*
#             channel = bot.get_channel(CHANNEL_ID)
#             if channel:
#                 send_reminder(automatic=True, channel=channel)

# @send_reminder.after_loop
# async def after_reminder():
#     print(f"Reminder sent automatically at {datetime.now(timezone.utc)} UTC time.\n\nReminder:\n{load_reminder()}")

# reminder_cmd = ReminderCommandGroup()
# bot.tree.add_command(reminder_cmd)
bot.run(TOKEN)
