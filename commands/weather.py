"""
Command: weather
Description: Generate daily weather conditions for WFRP river travel with multi-day journey tracking

This module provides the command interface for the refactored weather system.
It delegates all business logic to WeatherCommandHandler.
"""

import discord
from discord import app_commands
from discord.ext import commands

from commands.weather_modules.handler import WeatherCommandHandler


def is_gm(user: discord.Member) -> bool:
    """
    Check if user is a GM (server owner or has GM role).

    Args:
        user: Discord member to check

    Returns:
        True if user is GM, False otherwise
    """
    # Server owner is always GM
    if user.guild.owner_id == user.id:
        return True

    # Check for GM role
    gm_role = discord.utils.get(user.guild.roles, name="GM")
    if gm_role and gm_role in user.roles:
        return True

    return False


def setup(bot: commands.Bot):
    """
    Register weather commands with the bot.
    Called from main.py during bot initialization.
    """

    # Initialize handler once
    handler = WeatherCommandHandler()

    # === MAIN WEATHER COMMAND ===

    # Slash command
    @bot.tree.command(
        name="weather", description="Manage daily weather for river travel journeys"
    )
    @app_commands.describe(
        action="What to do",
        season="Season (for 'journey' and 'override' actions)",
        province="Province (for 'journey' and 'override' actions)",
        day="Day number to view (for 'view' action)",
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name="Generate Next Day", value="next"),
            app_commands.Choice(name="Next Stage (Multi-Day)", value="next-stage"),
            app_commands.Choice(name="Start New Journey", value="journey"),
            app_commands.Choice(name="View Day", value="view"),
            app_commands.Choice(name="End Journey", value="end"),
            app_commands.Choice(name="Override Weather", value="override"),
        ],
        season=[
            app_commands.Choice(name="Spring", value="spring"),
            app_commands.Choice(name="Summer", value="summer"),
            app_commands.Choice(name="Autumn", value="autumn"),
            app_commands.Choice(name="Winter", value="winter"),
        ],
        province=[
            app_commands.Choice(name="Reikland", value="reikland"),
            app_commands.Choice(name="Nordland", value="nordland"),
            app_commands.Choice(name="Ostland", value="ostland"),
            app_commands.Choice(name="Middenland", value="middenland"),
            app_commands.Choice(name="Hochland", value="hochland"),
            app_commands.Choice(name="Talabecland", value="talabecland"),
            app_commands.Choice(name="Ostermark", value="ostermark"),
            app_commands.Choice(name="Stirland", value="stirland"),
            app_commands.Choice(name="Sylvania", value="sylvania"),
            app_commands.Choice(name="Wissenland", value="wissenland"),
            app_commands.Choice(name="Averland", value="averland"),
            app_commands.Choice(name="Solland", value="solland"),
            app_commands.Choice(name="Kislev", value="kislev"),
            app_commands.Choice(name="Wasteland", value="wasteland"),
            app_commands.Choice(name="Border Princes", value="border_princes"),
        ],
    )
    async def weather_slash(
        interaction: discord.Interaction,
        action: str = "next",
        season: str = None,
        province: str = None,
        day: int = None,
    ):
        """Manage weather for multi-day journeys."""
        # Check GM permissions for override action
        if action == "override":
            if not is_gm(interaction.user):
                await interaction.response.send_message(
                    "❌ Only GMs can override weather.", ephemeral=True
                )
                return

        await handler.handle_command(
            interaction, action, season, province, day, is_slash=True
        )

    # Prefix command
    @bot.command(name="weather")
    async def weather_prefix(
        ctx,
        action: str = "next",
        season: str = None,
        province: str = None,
        day: int = None,
    ):
        """Manage weather for multi-day journeys."""
        # Check GM permissions for override action
        if action == "override":
            if not is_gm(ctx.author):
                await ctx.send("❌ Only GMs can override weather.")
                return

        await handler.handle_command(ctx, action, season, province, day, is_slash=False)

    # === STAGE CONFIGURATION COMMAND ===

    @bot.tree.command(
        name="weather-stage-config",
        description="[GM] Configure stage duration and display mode for multi-day travel",
    )
    @app_commands.describe(
        stage_duration="Number of days per stage (default: 3, range: 1-10)",
        display_mode="How to show stage weather: 'simple' (summary) or 'detailed' (full weather for each day)",
    )
    @app_commands.choices(
        display_mode=[
            app_commands.Choice(name="Simple Summary", value="simple"),
            app_commands.Choice(name="Detailed (All Days)", value="detailed"),
        ]
    )
    async def weather_stage_config_slash(
        interaction: discord.Interaction,
        stage_duration: int = None,
        display_mode: str = None,
    ):
        """Configure stage duration and display mode (GM only)."""
        # Check GM permissions
        if not is_gm(interaction.user):
            await interaction.response.send_message(
                "❌ Only GMs can configure stage settings.", ephemeral=True
            )
            return

        await handler.configure_stage(
            interaction, stage_duration, display_mode, is_slash=True
        )

    # Prefix command for stage configuration
    @bot.command(name="weather-stage-config")
    async def weather_stage_config_prefix(
        ctx,
        stage_duration: int = None,
        display_mode: str = None,
    ):
        """Configure stage duration and display mode (GM only)."""
        # Check GM permissions
        if not is_gm(ctx.author):
            await ctx.send("❌ Only GMs can configure stage settings.")
            return

        await handler.configure_stage(ctx, stage_duration, display_mode, is_slash=False)
