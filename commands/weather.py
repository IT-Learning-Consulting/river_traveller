"""
Weather Command Interface

Provides Discord command interface for the WFRP weather system with multi-day
journey tracking. Delegates all business logic to WeatherCommandHandler for
separation of concerns.

Features:
    - Multi-day journey tracking with persistent state
    - Day-by-day or stage-based weather generation
    - Historical weather viewing
    - GM-only configuration and override commands
    - Season and province-specific weather patterns

Usage Examples:
    Slash Commands:
        /weather action:next                              # Generate next day
        /weather action:next-stage                        # Generate multi-day stage
        /weather action:journey season:summer province:reikland  # Start journey
        /weather action:view day:3                        # View historical weather
        /weather action:end                               # End current journey
        /weather-stage-config stage_duration:5            # GM: Set stage length
        /weather-stage-config display_mode:detailed       # GM: Set display mode

    Prefix Commands:
        !weather next
        !weather journey summer reikland
        !weather view 3
        !weather end

Permissions:
    - All users can generate weather and view journey state
    - GM role or server owner can:
        - Override weather
        - Configure stage settings (duration, display mode)

Channel Requirements:
    - boat-travelling-notifications: GM weather details (optional)
    - boat-travelling-log: Command logging (optional)

State Management:
    Weather state persists per-guild and includes:
    - Current day number
    - Season and province
    - Historical weather data
    - Stage configuration (duration, display mode)
    - Event cooldown tracking (cold fronts, heat waves)
"""

from typing import Optional
import discord
from discord import app_commands
from discord.ext import commands

from commands.weather_modules.handler import WeatherCommandHandler
from commands.permissions import is_gm
from commands.error_handlers import handle_discord_error, handle_value_error


def setup(bot: commands.Bot) -> None:
    """
    Register weather commands with the bot.

    Registers both slash (/) and prefix (!) versions of weather commands,
    including the main weather command and stage configuration command.
    Initializes a shared WeatherCommandHandler instance for all commands.

    Args:
        bot: The Discord bot instance to register commands with

    Note:
        Called automatically from main.py during bot initialization.
    """

    # Initialize handler with bot instance for logging
    handler = WeatherCommandHandler(bot)

    # === MAIN WEATHER COMMAND ===

    # Slash command
    @bot.tree.command(name="weather", description="Manage daily weather for river travel journeys")
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
        season: Optional[str] = None,
        province: Optional[str] = None,
        day: Optional[int] = None,
    ) -> None:
        """
        Slash command for weather management.

        Handles weather generation, journey management, and historical viewing.
        GM-only actions (override) are gated by permission checks.

        Args:
            interaction: Discord interaction from slash command
            action: Action to perform (next, next-stage, journey, view, end, override)
            season: Season for journey/override (spring, summer, autumn, winter)
            province: Province for journey/override
            day: Day number for view action
        """
        # Check GM permissions for override action
        if action == "override":
            if not is_gm(interaction.user):
                await interaction.response.send_message("❌ Only GMs can override weather.", ephemeral=True)
                return

        await handler.handle_command(interaction, action, season, province, day, is_slash=True)

    # Prefix command
    @bot.command(name="weather")
    async def weather_prefix(
        ctx: commands.Context,
        action: str = "next",
        season: Optional[str] = None,
        province: Optional[str] = None,
        day: Optional[int] = None,
    ) -> None:
        """
        Prefix command for weather management.

        Usage:
            !weather next
            !weather journey summer reikland
            !weather view 3
            !weather end

        Args:
            ctx: Command context
            action: Action to perform
            season: Season for journey/override
            province: Province for journey/override
            day: Day number for view action
        """
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
        stage_duration: Optional[int] = None,
        display_mode: Optional[str] = None,
    ) -> None:
        """
        Configure stage duration and display mode (GM only).

        Allows GMs to customize how multi-day stages are generated and displayed.
        Stage duration controls how many days are generated per "next-stage" command.
        Display mode controls whether full details or summary are shown.

        Args:
            interaction: Discord interaction from slash command
            stage_duration: Number of days per stage (1-10)
            display_mode: Display format ("simple" or "detailed")
        """
        # Check GM permissions
        if not is_gm(interaction.user):
            await interaction.response.send_message("❌ Only GMs can configure stage settings.", ephemeral=True)
            return

        try:
            await handler.configure_stage(interaction, stage_duration, display_mode, is_slash=True)
        except ValueError as e:
            # Validation error - inform user
            await handle_value_error(interaction, e, is_slash=True, command_name="Weather Stage Config")
        except Exception as e:  # noqa: BLE001
            # Generic error (broad exception intentional for user safety)
            await handle_discord_error(interaction, e, is_slash=True)

    # Prefix command for stage configuration
    @bot.command(name="weather-stage-config")
    async def weather_stage_config_prefix(
        ctx: commands.Context,
        stage_duration: Optional[int] = None,
        display_mode: Optional[str] = None,
    ) -> None:
        """
        Configure stage duration and display mode (GM only).

        Usage:
            !weather-stage-config 5
            !weather-stage-config detailed
            !weather-stage-config 5 detailed

        Args:
            ctx: Command context
            stage_duration: Number of days per stage (1-10)
            display_mode: Display format ("simple" or "detailed")
        """
        # Check GM permissions
        if not is_gm(ctx.author):
            await ctx.send("❌ Only GMs can configure stage settings.")
            return

        await handler.configure_stage(ctx, stage_duration, display_mode, is_slash=False)
