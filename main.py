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

Architecture:
    This module serves as the composition root - it wires dependencies together
    and starts the bot. Business logic lives in command modules and services.

    Dependency Injection Pattern:
        1. Load configuration (config.py)
        2. Create bot with dependencies (create_bot factory)
        3. Register command modules
        4. Start Flask keep-alive server (for deployment)
        5. Run bot

Design Principles:
    - Separation of concerns (commands in modules, not in main)
    - Dependency injection (services passed to commands)
    - Configuration externalization (environment variables)
    - Clean composition root (minimal business logic)
"""

import logging
import discord
from discord.ext import commands

# Configuration management
from config import load_config

# Flask server for Render deployment
from server import keep_alive

# Command module setup functions
from commands.roll import setup as setup_roll
from commands.boat_handling import setup as setup_boat_handling
from commands.weather import setup as setup_weather
from commands.river_encounter import setup_river_encounter
from commands.help import setup as setup_help


# =============================================================================
# Bot Creation Factory
# =============================================================================


def create_bot(config) -> commands.Bot:
    """
    Create and configure Discord bot instance with all dependencies.

    This factory function is the composition root - it instantiates all
    dependencies and wires them together. Commands receive their dependencies
    through this factory rather than creating them internally.

    Args:
        config: AppConfig instance with bot configuration

    Returns:
        Configured discord.ext.commands.Bot instance

    Dependency Injection Pattern:
        Currently, services are instantiated within command modules.
        Future enhancement: Create services here and pass to command setup.

        Example (future):
            services = {
                'roll_service': RollService(),
                'boat_service': BoatHandlingService(),
                ...
            }
            setup_roll(bot, services['roll_service'])

    Testing:
        Mock services can be injected by passing custom config:

        >>> test_config = AppConfig(discord_token="test", ...)
        >>> bot = create_bot(test_config)
        >>> # Bot uses test configuration
    """
    # Configure Discord intents (message_content required for prefix commands)
    intents = discord.Intents.default()
    intents.message_content = True

    # Create bot with configuration
    bot = commands.Bot(
        command_prefix=config.command_prefix,
        intents=intents,
        help_command=None,  # Use custom /help command
    )

    # Register event handlers
    @bot.event
    async def on_ready():
        """Handle bot ready event - sync commands and log readiness."""
        try:
            synced = await bot.tree.sync()
            print(f"Synced {len(synced)} command(s)")
        except discord.DiscordException as e:
            print(f"Failed to sync commands: {e}")

        print(f"We are ready to go in {bot.user.name}")

    @bot.event
    async def on_message(message):
        """Handle incoming messages - process commands, ignore bots."""
        if message.author.bot:
            return

        print(f"Message received: {message.content}")
        await bot.process_commands(message)

    # Register hello command (kept in main.py as simple example)
    @bot.tree.command(name="hello", description="Greet the traveling bot")
    async def hello_slash(interaction: discord.Interaction):
        """Slash command greeting."""
        await interaction.response.send_message(
            f"Hello {interaction.user.mention}! 🚢 I am your WFRP traveling companion."
        )

    @bot.command(name="hello")
    async def hello_prefix(ctx):
        """Prefix command greeting."""
        await ctx.send(
            f"Hello {ctx.author.mention}! 🚢 I am your WFRP traveling companion."
        )

    # Register command modules
    # Each module exports a setup(bot) function that registers its commands
    setup_roll(bot)
    setup_boat_handling(bot)
    setup_weather(bot)
    setup_river_encounter(bot)
    setup_help(bot)

    return bot


# =============================================================================
# Application Entry Point
# =============================================================================


def main():
    """
    Main application entry point.

    Execution flow:
        1. Load configuration from environment
        2. Start Flask keep-alive server (for Render deployment)
        3. Create bot with configuration
        4. Run bot with logging

    The keep_alive() server responds to HTTP health checks to prevent
    the bot from sleeping on free hosting tiers.
    """
    # Load configuration with validation
    config = load_config()
    print(f"Loaded configuration: {config}")

    # Start Flask keep-alive server for deployment
    keep_alive()

    # Create bot with dependencies
    bot = create_bot(config)

    # Configure logging
    handler = logging.FileHandler(
        filename=config.log_filename,
        encoding="utf-8",
        mode="w",  # Overwrite log file on restart
    )

    # Run bot
    bot.run(config.discord_token, log_handler=handler, log_level=logging.DEBUG)


# =============================================================================
# Script Entry Point
# =============================================================================

if __name__ == "__main__":
    main()
