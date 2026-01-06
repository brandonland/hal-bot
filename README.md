# Discord Reminder Bot

Work in progress.

## Initial Setup
1. Enter your discord bot credentials into the `.env.example` file, including token, channel ID, etc.
2. Rename it to `.env`
3. Set your reminder message in `reminder.example.json`
4. Rename it to `reminder.json`
5. Run the bot: `python bot.py`

For the moment, the reminder interval and time are hardcoded. The reminder time is at 5pm EST (17:00 UTC) every Tuesday. If you want to change this, you'll have to change the code itself. This may change to be user-controlled in the future.

## Usage
There are 3 slash commands:
- `/getreminder`: This command privately echoes back what the reminder is set to. This is only visible to you.
- `/setreminder <new_reminder>`: Replace <new_reminder> with any text to set the reminder to anything. For example: `/setreminder hello` will set the reminder to "hello".
- `/sayreminder`: This command manually forces the bot to speak its reminder in the channel. This is visible to everyone.
