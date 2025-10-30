"""
WFRP River Travel Discord Bot - Main Entry Point

A Discord bot providing comprehensive river travel assistance for Warhammer Fantasy
Roleplay 4th Edition campaigns. Handles dice rolling, boat navigation, weather
simulation, encounter generation, and multi-day journey management.

Key Features:
    - WFRP 4e dice rolling (d10, d100, skill tests with success levels)
    - Boat handling tests with weather-based modifiers
    - Multi-day weather generation with special events (cold fronts, heat waves)
    - River encounter system with d100 tables (positive, harmful, accident)
    - Character-specific skill bonuses (Sail, Row, Lore Riverways)
    - Stage-based journey progression with configurable duration
    - Discord slash commands and prefix commands support

Commands:
    Dice Rolling:
        - /roll, /r: Generic dice rolling (XdY format)
        - /wfrp-roll: WFRP 4e skill tests with difficulty modifiers

    Boat Navigation:
        - /boat-handling: Boat handling skill test with active weather modifiers
        - /cargo-shift: Roll for cargo shift during rough conditions

    Weather System:
        - /weather: Start multi-day journey with season/province selection
        - /stage: Advance to next stage of journey
        - /next-day: Advance one day with new weather
        - /forecast: View upcoming weather for planning

    Encounters:
        - /river-encounter: Generate random river encounter with d100 tables

    Utility:
        - /help: Display all available commands
        - /hello: Simple greeting command

Architecture:
    - Modular command structure (commands/ folder with separate modules)
    - Weather system split into handler, stages, notifications, display
    - Utility modules for mechanics (WFRP, encounters, modifiers, weather)
    - Database layer (character data, weather storage, encounter tables)
    - Flask keep-alive server for Render deployment

Bot Configuration:
    - Discord Intents: message_content enabled for prefix commands
    - Command Prefix: ! (for legacy prefix commands)
    - Help Command: Custom help disabled (uses /help command)
    - Logging: FileHandler to discord.log with DEBUG level

Environment Variables:
    - DISCORD_TOKEN: Required Discord bot token (from .env file)

Usage:
    Run directly: python main.py
    Automatically starts Flask server and Discord bot

Design Principles:
    - Separation of concerns (commands in modules, not in main)
    - Event-driven architecture (Discord event handlers)
    - Async/await for non-blocking operations
    - Modular command registration (setup functions)
    - Bot ignores messages from other bots (prevents loops)
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

# =============================================================================
# MODULE-LEVEL CONSTANTS
# =============================================================================

# Environment Configuration
ENV_DISCORD_TOKEN = "DISCORD_TOKEN"

# Bot Configuration
BOT_COMMAND_PREFIX = "!"
LOG_FILENAME = "discord.log"
LOG_ENCODING = "utf-8"
LOG_MODE = "w"  # Overwrite log file on restart

# Emoji used in responses
EMOJI_BOAT = "🚢"

# Command Response Messages
HELLO_MESSAGE_TEMPLATE = "Hello {mention}! {emoji} I am your WFRP traveling companion."
READY_MESSAGE_TEMPLATE = "We are ready to go in {bot_name}"
SYNC_SUCCESS_MESSAGE_TEMPLATE = "Synced {count} command(s)"
SYNC_FAILURE_MESSAGE_TEMPLATE = "Failed to sync commands: {error}"
MESSAGE_RECEIVED_TEMPLATE = "Message received: {content}"

# Command Names
CMD_HELLO = "hello"

# Command Descriptions
CMD_HELLO_DESC = "Greet the traveling bot"


# Load environment variables from .env file
load_dotenv()
token = os.getenv(ENV_DISCORD_TOKEN)

# Configure logging to file with overwrite mode
handler = logging.FileHandler(
    filename=LOG_FILENAME, encoding=LOG_ENCODING, mode=LOG_MODE
)

# Configure Discord intents (message_content required for prefix commands)
intents = discord.Intents.default()
intents.message_content = True

# Initialize bot (use ! for prefix commands, disable default help command)
bot = commands.Bot(
    command_prefix=BOT_COMMAND_PREFIX, intents=intents, help_command=None
)


@bot.event
async def on_ready():
    """
    Handle the bot's ready event after successful Discord connection.

    Called when the bot has successfully connected to Discord and is fully initialized.
    Syncs all application commands (slash commands) with Discord and logs readiness.

    Behavior:
        1. Syncs slash commands to Discord API (makes /commands available)
        2. Prints sync status (success with count or failure with error)
        3. Logs bot readiness with bot name

    Exceptions:
        - Catches discord.DiscordException during sync and logs failure
        - Bot continues running even if sync fails

    Examples:
        >>> # On successful connection:
        >>> # Output: "Synced 12 command(s)"
        >>> # Output: "We are ready to go in TravelingBot"
    """
    try:
        synced = await bot.tree.sync()
        print(SYNC_SUCCESS_MESSAGE_TEMPLATE.format(count=len(synced)))
    except discord.DiscordException as e:
        print(SYNC_FAILURE_MESSAGE_TEMPLATE.format(error=e))

    print(READY_MESSAGE_TEMPLATE.format(bot_name=bot.user.name))


@bot.event
async def on_message(message):
    """
    Handle incoming messages from Discord channels.

    Processes all messages except those from bots (including self) to prevent
    infinite loops and bot-to-bot interactions. Passes user messages to command
    processor for prefix command handling.

    Behavior:
        1. Ignore all messages from bots (message.author.bot check)
        2. Log message content for debugging
        3. Process prefix commands (bot.process_commands)

    Args:
        message: discord.Message object containing message data

    Examples:
        >>> # User sends: "!roll 2d10"
        >>> # Output: "Message received: !roll 2d10"
        >>> # Command is processed by roll module
    """
    # Ignore messages from bots (including self) to prevent loops
    if message.author.bot:
        return

    print(MESSAGE_RECEIVED_TEMPLATE.format(content=message.content))
    await bot.process_commands(message)


# ==================== HELLO COMMAND ====================
# Simple greeting command demonstrating both slash and prefix command patterns
# This is the only command that stays in main.py (all others are in modules)


@bot.tree.command(name=CMD_HELLO, description=CMD_HELLO_DESC)
async def hello_slash(interaction: discord.Interaction):
    """
    Slash command greeting the user with bot introduction.

    A simple demonstration command showing bot personality and availability.
    Responds with personalized greeting mentioning the user.

    Args:
        interaction: Discord interaction object from slash command invocation

    Examples:
        >>> # User runs: /hello
        >>> # Bot responds: "Hello @User! 🚢 I am your WFRP traveling companion."
    """
    await interaction.response.send_message(
        HELLO_MESSAGE_TEMPLATE.format(
            mention=interaction.user.mention, emoji=EMOJI_BOAT
        )
    )


@bot.command(name=CMD_HELLO)
async def hello_prefix(ctx):
    """
    Prefix command greeting the user with bot introduction.

    Legacy prefix command version of hello (uses ! prefix). Functionality
    identical to slash command version but triggered differently.

    Args:
        ctx: Discord context object from prefix command invocation

    Examples:
        >>> # User sends: !hello
        >>> # Bot responds: "Hello @User! 🚢 I am your WFRP traveling companion."
    """
    await ctx.send(
        HELLO_MESSAGE_TEMPLATE.format(mention=ctx.author.mention, emoji=EMOJI_BOAT)
    )


# ==================== REGISTER COMMANDS ====================
# Register commands from separate modules using their setup functions.
# Each module exports a setup(bot) function that registers its commands.
#
# Command Modules:
#   - roll: Generic dice rolling and WFRP skill tests
#   - boat_handling: Boat navigation with weather modifiers
#   - weather: Multi-day journey weather system
#   - river_encounter: Random encounter generation
#   - help: Custom help command with categorized listing

setup_roll(bot)
setup_boat_handling(bot)
setup_weather(bot)
setup_river_encounter(bot)
setup_help(bot)


# ==================== RUN BOT ====================
if __name__ == "__main__":
    """
    Main entry point for the bot application.

    Execution flow:
        1. Starts Flask keep-alive server (for Render free tier)
        2. Runs Discord bot with configured token and logging

    The keep_alive() server responds to HTTP health checks from Render
    to prevent the bot from sleeping due to inactivity.

    Logging:
        - Handler: FileHandler (discord.log)
        - Level: DEBUG (most verbose logging)
        - Captures all Discord API interactions
    """
    # Start Flask server to keep bot alive on Render's free tier
    keep_alive()

    # Run the Discord bot with token from environment
    bot.run(token, log_handler=handler, log_level=logging.DEBUG)
