# Discord Reminder Bot

Work in progress.

## Initial Setup
1. Copy `.env.example` file to `.env`, and add your credentials, including token, channel ID, etc.
3. Copy `reminder.example.json` to `reminder.json`. Add your custom reminder message to it, or change it later with a slash command.
4. Create and activate a virtual environment:
    1. `python -m venv .venv`
    2. `source .venv/bin/activate`
6. Install dependencies: `pip install -r requirements.txt`
7. Run the bot: `python bot.py`

For the moment, the reminder interval and time are hardcoded. The reminder time is at 12pm EST (17:00 UTC) every Tuesday. If you want to change this, you'll have to change the code itself. This may change to be user-controlled in the future.

## Usage
There are 3 slash commands:
- `/reminder view`: This command privately echoes back what the reminder is set to. This is only visible to you.
- `/reminder set <new_reminder>`: Replace <new_reminder> with any text to set the reminder to anything.
  - For example: `/reminder set hello` will set the reminder to "hello".
- `/reminder post`: This command manually forces the bot to write the reminder as a message in the channel. This is visible to everyone.
