import os
import asyncio
import json
import feedparser
import discord
from discord import option
from discord.ext import commands, tasks
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import pprint
from markdownify import markdownify
import requests
from bs4 import BeautifulSoup
import re

# from lxml import etree
from lxml import html
from lxml.cssselect import CSSSelector
# from cssselect import Selector
# from cssselect import HTMLTranslator, SelectorError

import traceback

load_dotenv()


TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
EXAMPLE_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.example.json")
REMINDER_BANNER_PATH = "uploads/reminder-banner.jpg"
REMINDER_BANNER_PATH_ABS = os.path.join(os.path.dirname(__file__), REMINDER_BANNER_PATH)
NEWS_SOURCES = [
    "blu-ray.com",
]

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(intents=intents)

dvduesday = bot.create_group("dvd", "DVDuesday reminder commands", guild_ids=[GUILD_ID])
# dvd_edit = dvduesday.subgroup("edit", "Edit reminder", guild_ids=[GUILD_ID])


def init_config():
    if not os.path.exists(CONFIG_PATH):
        with open(EXAMPLE_CONFIG_PATH, "r") as file:
            example_data = json.load(file)
        with open(CONFIG_PATH, "w") as file:
            json.dump(example_data, file, indent=4)

def load_reminder():
    try:
        with open("config.json", "r") as file:
            data = json.load(file)
            return data.get("reminder", "Default reminder")
    except (FileNotFoundError, json.JSONDecodeError):
        return "config file not found!"

def update_reminder(message):
    with open("config.json", "r") as file:
        data = json.load(file)

    data["reminder"] = message

    with open("config.json", "w") as file:
        json.dump(data, file, indent=4)

def update_latest_br_news_url(url: str):
    with open("config.json", "r") as file:
        data = json.load(file)

    data["br_news"] = url

    with open("config.json", "w") as file:
        json.dump(data, file, indent=4)

def load_latest_br_news_url():
    try:
        with open("config.json", "r") as file:
            data = json.load(file)
            return data.get("br_news")
    except (FileNotFoundError, json.JSONDecodeError):
        return "config file not found!"

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
            await ctx.respond(embed=embed, file=file, ephemeral=ephemeral)
        elif not followup and inter is not None:
            await inter.respond(embed=embed, file=file, ephemeral=ephemeral)
        elif followup and ctx:
            await ctx.send_followup(embed=embed, file=file, ephemeral=ephemeral)
        elif followup and inter:
            await inter.followup.send(embed=embed, file=file, ephemeral=ephemeral)
    elif automatic and channel is not None:
        await channel.send(embed=embed, file=file)


class ReminderEditModal(discord.ui.DesignerModal):
    def __init__(self, img_only=False, msg_only=False, *args, **kwargs) -> None:
        if img_only:
            print("image only!")
        elif msg_only:
            print("message only!")

        self.text_input = discord.ui.Label(
            "Reminder message body",
            discord.ui.TextInput(
                value=load_reminder(),
                placeholder="Create/edit your reminder message",
                required=False,
                style=discord.InputTextStyle.long,
            ),
        )

        # image_file = discord.ui.Label(
        #     "Upload a banner image (Optional)",
        #     discord.ui.FileUpload(
        #         max_values=1,
        #         required=False,
        #     ),
        #     description="If you already uploaded an image, ignore this.",
        # )
        super().__init__(
            self.text_input,
            # image_file,
            *args,
            **kwargs,
        )

    async def callback(self, inter: discord.Interaction):
        await inter.response.defer()
        await inter.followup.send("Reminder Set. Preview below:", ephemeral=True)
        # embed = discord.Embed(
        #     description=self.children[0].item.value,
        #     color=discord.Color.random(),
        # )
        update_reminder(self.text_input.item.value) # Update the reminder stored on disk
        await send_reminder(inter=inter, followup=True, ephemeral=True)


@bot.event
async def on_ready():
    init_config()
    channel = bot.get_channel(CHANNEL_ID)
    print(f"Logged in as {bot.user}!")
    print(f"Current reminder: {load_reminder()}")

    if not channel:
        print("Error: channel not found!")


@dvduesday.command(
    name="view",
    description="(Only visible to you) See the reminder message",
)
async def reminder_view(ctx: discord.ApplicationContext):
    await send_reminder(ctx, ephemeral=True)


@dvduesday.command(
    name="edit", description="Edit a new reminder message"
)
async def reminder_edit(ctx: discord.ApplicationContext, image: discord.Attachment=None):
    if image:
        await image.save(REMINDER_BANNER_PATH_ABS)
        await ctx.respond("Image uploaded! Here is a private preview:", ephemeral=True)
        await send_reminder(ctx, followup=True, ephemeral=True)
    else:
        modal = ReminderEditModal(title="Edit the reminder")
        await ctx.send_modal(modal)

# TODO: have a confirm/prompt modal: "Are you sure you want to...?"
@dvduesday.command(
    name="post",
    description="Manually announce the reminder in this channel (⚠️ CAUTION! Visible to all! ⚠️)",
)
async def reminder_post(ctx: discord.ApplicationContext):
    await send_reminder(ctx)
    
    
# TODO: Autocomplete news sources

async def get_news_source(ctx: discord.AutocompleteContext):
    return NEWS_SOURCES

def scrape_bluray_for_image(url: str, t: str="image") -> str | None:
    """
    Given the url of the post, returns featured image.

    (blu-ray.com posts usually have two images per news post. Sometimes
    the image is omitted while the thumbnail remains, so the return value must
    optionally allow a `None` type, in case no image was found.)
    
    Pass type="thumb" as an argument to scrape the thumbnail instead. 
    """
    
    response = requests.get(url)
    tree = html.fromstring(response.content)

    if t == "image":
        selector = CSSSelector("div > a img:not(.cover)")
    elif t == "thumb":
        selector = CSSSelector("img:not(.cover)")
    else:
        raise("Error: incorrect type passed to scrape_bluray_for_image")

    images = selector(tree)
    
    if t == "image":
        image_sources = [img.get('src') for img in images if img.get('src') and img.get('src').endswith('.jpg')]
        if image_sources:
            return image_sources[0]
        else:
            return None
    
    if t == "thumb":
        for img in images:
            src = img.get('src')
            if "/news/icons" in src:
                return src

def get_latest_bluray_url() -> str:
    p = feedparser.parse("https://www.blu-ray.com/rss/newsfeed.xml")
    entry = p.entries[0]
    return entry.link
        
def get_latest_bluray_news() -> discord.Embed:
    p = feedparser.parse("https://www.blu-ray.com/rss/newsfeed.xml")
    entry = p.entries[0]
    title = entry.title
    desc = markdownify(entry.description)
    published = entry.published
    # image = entry.image | None
    link = entry.link
    summary = entry.summary
    img_link = scrape_bluray_for_image(link)
    thumb_link = scrape_bluray_for_image(link, "thumb")

    embed = discord.Embed(
        title=title,
        color=discord.Color.random(),
    )
    embed.add_field(name="", value=f"Published: {published}", inline=False)
    embed.add_field(name="", value=desc, inline=False)
    if img_link:
        embed.set_image(url=img_link)
    if thumb_link:
        embed.set_thumbnail(url=thumb_link)

    return embed

        
async def get_news(source: str) -> discord.Embed | None:
    if source not in NEWS_SOURCES:
        ctx.send_response(f"Sorry, that news source {source} is unknown to me.")
        
    if source == "blu-ray.com":
        return get_latest_bluray_news()
    
async def send_br_news(channel: None):
    url = get_latest_bluray_url()
    embed = get_latest_bluray_news()
    if channel:
        await channel.send(embed=embed)
        update_latest_br_news_url(url)
    

# @bot.group(name="news", invoke_without_command=True, guild_ids=[GUILD_ID])
@bot.slash_command(description="Manually fetch the news. Posts publicly!", guild_ids=[GUILD_ID])
async def brnews(
    ctx: discord.ApplicationContext,
):
    source = "blu-ray.com"
    news_embed = await get_news(source)
    await ctx.send_response(f"Here is the latest news article from {source}:")
    await ctx.send_followup(embed=news_embed)


@tasks.loop(minutes=1) # Check every minute
async def auto_reminder():
    now = datetime.now(timezone.utc)
    if now.weekday() == 1:  # (0=Monday, 1=Tuesday, ...)
        time_to_send = now.replace(hour=17, minute=0, second=0, microsecond=0) # set to 17:00 UTC (noon EST)
        if now >= time_to_send and now < time_to_send + timedelta(minutes=1): # sends the reminder *within the minute*
            channel = bot.get_channel(CHANNEL_ID)
            if channel:
                print("Sending automatic reminder.")
                await send_reminder(automatic=True, channel=channel)
            else:
                print("Error: channel not found")


# TODO: Check every hour if a new post to blu-ray.com was posted.
#       If there is a new post, post it in specified channel.
@tasks.loop(minutes=1)
async def auto_br_news():
    now = datetime.now(timezone.utc)
    if now.minute == 0 or now.minute == 30: # check 2x per hour
        latest_url = get_latest_bluray_url()
        if latest_url != load_latest_br_news_url():
            channel = bot.get_channel(CHANNEL_ID)
            print("Sending blu-ray news...")
            await send_br_news(channel=channel)

auto_reminder.start()
auto_br_news.start()

bot.run(TOKEN)
