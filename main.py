"""
A Discord bot for Warhammer Fantasy Roleplay river traveling assistance.
Handles dice rolling, boat navigation, trading, and journey management.
"""

import os
import logging
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Import Flask server for keeping bot alive on Render
from server import keep_alive

# Import command setup functions
from commands.roll import setup as setup_roll
from commands.boat_handling import setup as setup_boat_handling
from commands.weather import setup as setup_weather
from commands.river_encounter import setup_river_encounter
from commands.help import setup as setup_help


# Load environment variables
load_dotenv()
token = os.getenv("DISCORD_TOKEN")

# Configure logging
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
intents = discord.Intents.default()
intents.message_content = True

# Initialize bot (use ! for prefix commands, disable default help command)
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)


@bot.event
async def on_ready():
    """
    Handle the bot's ready event.
    Called when the bot has successfully connected to Discord and is fully initialized.
    """
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except discord.DiscordException as e:
        print(f"Failed to sync commands: {e}")

    print(f"We are ready to go in {bot.user.name}")


@bot.event
async def on_message(message):
    """
    Handle incoming messages.
    Processes messages and commands while ignoring bot's own messages.
    """
    if message.author == bot.user:
        return

    print(f"Message received: {message.content}")
    await bot.process_commands(message)


# ==================== HELLO COMMAND ====================
# This is the only command that stays in main.py (as per user request)


@bot.tree.command(name="hello", description="Greet the traveling bot")
async def hello_slash(interaction: discord.Interaction):
    """A simple greeting command."""
    await interaction.response.send_message(
        f"Hello {interaction.user.mention}! 🚢 I am your WFRP traveling companion."
    )


@bot.command(name="hello")
async def hello_prefix(ctx):
    """A simple greeting command."""
    await ctx.send(
        f"Hello {ctx.author.mention}! 🚢 I am your WFRP traveling companion."
    )


# ==================== REGISTER COMMANDS ====================
# Register commands from separate modules
setup_roll(bot)
setup_boat_handling(bot)
setup_weather(bot)
setup_river_encounter(bot)
setup_help(bot)


# ==================== RUN BOT ====================
if __name__ == "__main__":
    # Start Flask server to keep bot alive on Render's free tier
    keep_alive()

    # Run the Discord bot
    bot.run(token, log_handler=handler, log_level=logging.DEBUG)
