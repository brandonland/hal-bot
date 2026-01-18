# Discord Reminder Bot

Work in progress.

## Initial Setup
1. Copy `.env.example` file to `.env`, and add your credentials, including token, channel ID, etc.
2. Copy `config.example.json` to `config.json`. Add your custom reminder message to it, or change it later with a slash command.

### Using venv
1. Clone the repo: `git clone https://github.com/brandonland/discord-reminder-bot.git`
1. Change to the directory: `cd discord-reminder-bot`
1. Create and activate a virtual environment:
    1. `python -m venv .venv`
    1. `source .venv/bin/activate`
1. Install dependencies: `pip install -r requirements.txt`
1. Run the bot: `python bot.py`

### Using [uv](https://docs.astral.sh/uv/) (recommended)
1. Clone the repo: `git clone https://github.com/brandonland/discord-reminder-bot.git`
1. Change to the directory: `cd discord-reminder-bot`
1. Update environment: `uv sync`
1. Run the bot: `uv run bot.py`



For the moment, the reminder interval and time are hardcoded. The reminder time is at 12pm EST (17:00 UTC) every Tuesday. If you want to change this, you'll have to change the code itself. This may change to be user-controlled in the future.

## Usage
There are 3 slash commands:
- `/reminder view`: This command privately echoes back what the reminder is set to. This is only visible to you.
- `/reminder edit`: This opens up a large text input modal with the current reminder message to be edited.
  - `/reminder edit image`: Upload new banner image or change the existing one.
- `/reminder post`: This command manually forces the bot to write the reminder as a message in the channel. This is visible to everyone.
