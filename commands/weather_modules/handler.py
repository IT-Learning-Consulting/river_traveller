"""
Weather command handler - orchestrates weather generation and display.

This module provides the main business logic for weather commands, coordinating
between weather generation, storage, display, and notifications. It serves as
the central orchestrator for all weather-related operations.

Key Responsibilities:
    - Command routing and action handling
    - Weather data generation and progression
    - Journey state management (start, progress, end)
    - Coordination between storage, display, and notification systems
    - Error handling and user feedback
    - Stage-based progression (multi-day weather generation)

Architecture:
    The handler acts as a facade, delegating to specialized services:
    - WeatherStorage: Persistent state and data storage
    - JourneyService: Journey lifecycle management
    - DailyWeatherService: Weather generation and progression
    - DisplayService: User-facing display formatting
    - NotificationService: GM channel notifications
    - StageDisplayManager: Multi-day stage summaries (legacy, still in use)

Usage Example:
    >>> handler = WeatherCommandHandler()
    >>> await handler.handle_command(ctx, "next", None, None, None, False)
    # Generates and displays next day's weather

Command Flow:
    1. Command received → handle_command() routes to action handler
    2. Action handler validates inputs and retrieves journey state
    3. Weather service creates daily data (if applicable)
    4. Display service sends formatted embed to user
    5. Notification service sends GM notification
    6. Command logged to command-log channel
"""

from typing import Any, Dict, Optional, Union
from dataclasses import asdict

import discord
from discord.ext import commands

from db.weather_storage import WeatherStorage

# Import new service layer
from commands.weather_modules.services.journey_service import JourneyService
from commands.weather_modules.services.daily_weather_service import DailyWeatherService
from commands.weather_modules.services.notification_service import NotificationService
from commands.weather_modules.services.display_service import DisplayService
from commands.services.command_logger import CommandLogger

# Keep legacy imports for stage display (not yet refactored)
from commands.weather_modules.stages import StageDisplayManager

# Channel names
CHANNEL_GM_NOTIFICATIONS = "boat-travelling-notifications"
CHANNEL_COMMAND_LOG = "command-log"

# Default journey settings
DEFAULT_SEASON = "summer"
DEFAULT_PROVINCE = "reikland"
DEFAULT_STAGE_DURATION = 3
DEFAULT_JOURNEY_DAY = 1

# Error messages
ERROR_NO_GUILD = "This command must be used in a server."
ERROR_UNKNOWN_ACTION = "Unknown action: {action}"
ERROR_COMMAND_FAILED = "An error occurred: {error}"
ERROR_GENERATING_WEATHER = "Error generating weather: {error}"
ERROR_GENERATING_STAGE = "Error generating stage: {error}"
ERROR_STARTING_JOURNEY = "Error starting journey: {error}"
ERROR_VIEWING_WEATHER = "Error viewing weather: {error}"
ERROR_ENDING_JOURNEY = "Error ending journey: {error}"
ERROR_NO_JOURNEY = "❌ No journey in progress. Use `/weather journey` to start a new journey first."
ERROR_MISSING_PARAMS = "❌ Both season and province are required to start a journey.\nExample: `/weather journey season:summer province:reikland`"
ERROR_NO_DAY_PARAM = "❌ Day parameter is required. Example: `/weather view day:2`"
ERROR_DAY_NOT_FOUND = "❌ No weather data found for day {day}."
ERROR_NOT_IMPLEMENTED = "❌ This feature is not yet implemented."
ERROR_NO_STAGE_CONFIG_GUILD = "This command must be used in a server."
ERROR_NO_STAGE_CONFIG_JOURNEY = "❌ No journey in progress. Start a journey first with `/weather journey`."
ERROR_INVALID_STAGE_DURATION = "❌ Stage duration must be between 1 and 10 days."

# Info messages
INFO_AUTO_START_JOURNEY = "⚠️ No journey in progress. Starting new journey with default settings (Summer in Reikland)."
INFO_JOURNEY_REPLACE = "⚠️ A journey is already in progress. Ending previous journey and starting new one."
INFO_JOURNEY_ENDED = "🏁 **Journey Ended**\n\nYour river journey has been concluded. All weather data has been saved.\nUse `/weather journey` to start a new journey."
INFO_STAGE_CONFIG_UPDATED = "✅ Stage duration updated to {duration} days."

# Message templates
MSG_JOURNEY_START = "🗺️ **New Journey Started!**\n\n**Season:** {season}\n**Province:** {province}\n\nUse `/weather next` to generate weather for the first day."

# Command log colors
COLOR_COMMAND_LOG = 0x95A5A6  # Gray

# Emoji
EMOJI_MAP = "🗺️"
EMOJI_FINISH = "🏁"
EMOJI_WARNING = "⚠️"
EMOJI_ERROR = "❌"
EMOJI_SUCCESS = "✅"


class WeatherCommandHandler:
    """
    Central orchestrator for weather command operations.

    This handler acts as a facade, coordinating between the service layer,
    storage, and Discord API. It routes commands to appropriate handlers,
    manages error responses, and logs command execution.

    Architecture:
        - Thin orchestration layer (no business logic)
        - Delegates to specialized services:
            * JourneyService: Journey lifecycle and state management
            * DailyWeatherService: Weather generation and progression
            * NotificationService: GM channel notifications
            * DisplayService: User-facing Discord embeds
        - Uses CommandLogger for command tracking
        - Maintains WeatherStorage for persistent state

    Attributes:
        storage (WeatherStorage): Database access layer
        journey_service (JourneyService): Journey lifecycle operations
        weather_service (DailyWeatherService): Weather generation logic
        notification_service (NotificationService): GM notifications
        display_service (DisplayService): Discord embed displays
        logger (CommandLogger): Command execution tracking
        stage_display (StageDisplayManager): Multi-day stage displays (legacy)

    Example:
        >>> handler = WeatherCommandHandler()
        >>> await handler.handle_command(ctx, "next", None, None, None, False)
    """

    def __init__(self, bot: commands.Bot) -> None:
        """
        Initialize the handler with required dependencies.

        Sets up storage access and instantiates all service objects.
        Journey and Weather services require storage dependency injection.

        Args:
            bot: Discord bot instance for command logging
        """
        self.storage = WeatherStorage()
        # Service layer - Journey and Weather services require storage
        self.journey_service = JourneyService(self.storage)
        self.weather_service = DailyWeatherService(self.storage)
        self.notification_service = NotificationService()
        self.display_service = DisplayService()
        # Command logger
        self.logger = CommandLogger(bot)
        # Legacy stage display (not yet refactored)
        self.stage_display = StageDisplayManager

    async def handle_command(
        self,
        context: Union[discord.Interaction, commands.Context],
        action: str,
        season: Optional[str],
        province: Optional[str],
        day: Optional[int],
        is_slash: bool,
    ) -> None:
        """
        Route command to appropriate handler method based on action.

        This is the main entry point for all weather commands. It validates
        the guild context, routes to the appropriate action handler, logs
        successful commands, and handles any errors that occur.

        Args:
            context: Discord context (interaction for slash, ctx for prefix commands)
            action: The action to perform. Valid actions:
                - "next": Generate next day's weather
                - "next-stage": Generate weather for full stage (multiple days)
                - "journey": Start a new journey
                - "view": View historical weather for a specific day
                - "end": End the current journey
                - "override": Override weather (not yet implemented)
            season: Season name (required for "journey", ignored for other actions)
            province: Province name (required for "journey", ignored for other actions)
            day: Day number (required for "view", ignored for other actions)
            is_slash: Whether this is a slash command (affects response method)

        Returns:
            None: Sends response directly to Discord

        Raises:
            Displays error message to user if:
            - Command not used in a guild
            - Unknown action specified
            - Action handler raises an exception

        Example:
            >>> await handler.handle_command(ctx, "next", None, None, None, False)
            >>> await handler.handle_command(interaction, "journey", "winter", "reikland", None, True)
        """
        guild_id = str(context.guild.id) if context.guild else None

        if not guild_id:
            await self.display_service.send_error(context, ERROR_NO_GUILD, is_slash)
            return

        # Route to action handlers
        action_map = {
            "next": self._handle_next,
            "next-stage": self._handle_next_stage,
            "journey": self._handle_journey,
            "view": self._handle_view,
            "end": self._handle_end,
            "override": self._handle_override,
        }

        handler_func = action_map.get(action)
        if handler_func:
            try:
                await handler_func(context, guild_id, season, province, day, is_slash)
                # Log command after successful execution
                # Build command string
                if is_slash:
                    command_str = f"/weather action:{action}"
                    if season:
                        command_str += f" season:{season}"
                    if province:
                        command_str += f" province:{province}"
                    if day is not None:
                        command_str += f" day:{day}"
                else:
                    command_str = f"!weather {action}"
                    for param in [season, province, day]:
                        if param is not None:
                            command_str += f" {param}"
                # Build fields for embed
                fields = {"Action": action}
                if season:
                    fields["Season"] = season.title()
                if province:
                    fields["Province"] = province.replace("_", " ").title()
                if day is not None:
                    fields["Day"] = str(day)
                # Log to command-log channel
                await self.logger.log_command_from_context(
                    context=context,
                    command_name="weather",
                    command_string=command_str,
                    fields=fields,
                    color=discord.Color.gold(),
                    is_slash=is_slash,
                )
            except Exception as e:  # noqa: BLE001 - Broad exception handling for user feedback
                # Catch any errors from action handlers and display to user
                await self.display_service.send_error(context, ERROR_COMMAND_FAILED.format(error=str(e)), is_slash)
        else:
            await self.display_service.send_error(context, ERROR_UNKNOWN_ACTION.format(action=action), is_slash)

    async def _handle_next(
        self,
        context: Union[discord.Interaction, commands.Context],
        guild_id: str,
        _season: Optional[str],  # Unused - kept for consistent signature
        _province: Optional[str],  # Unused - kept for consistent signature
        _day: Optional[int],  # Unused - kept for consistent signature
        is_slash: bool,
    ) -> None:
        """
        Generate and display weather for the next day.

        Automatically starts a new journey with default settings if no journey
        is in progress. Generates weather data for the next day, displays it
        to the user, and sends a notification to the GM channel.

        Args:
            context: Discord context (interaction or ctx)
            guild_id: Guild ID string for storage lookup
            _season: Unused parameter (kept for consistent handler signature)
            _province: Unused parameter (kept for consistent handler signature)
            _day: Unused parameter (kept for consistent handler signature)
            is_slash: Whether this is a slash command response

        Returns:
            None: Sends response directly to Discord

        Side Effects:
            - Auto-starts journey with default settings if none exists
            - Increments current_day in journey state
            - Saves generated weather data to storage
            - Sends notification to GM channel
            - Displays weather embed to user

        Example:
            >>> await handler._handle_next(ctx, "12345", None, None, None, False)
        """
        try:
            journey = self.storage.get_journey_state(guild_id)

            # Auto-start journey if needed
            if not journey:
                await self.display_service.send_info(
                    context,
                    INFO_AUTO_START_JOURNEY,
                    is_slash=is_slash,
                )
                self.storage.start_journey(guild_id, DEFAULT_SEASON, DEFAULT_PROVINCE)
                journey = self.storage.get_journey_state(guild_id)

                # Send initial journey start notification
                guild = context.guild if hasattr(context, "guild") else context.guild
                if guild:
                    await self.notification_service.send_journey_notification(
                        guild,
                        CHANNEL_GM_NOTIFICATIONS,
                        "start",
                        season=DEFAULT_SEASON,
                        province=DEFAULT_PROVINCE,
                    )

            # Generate weather data (convert journey to dict for compatibility)
            journey_dict = asdict(journey)
            weather_data = self._generate_daily_weather(guild_id, journey_dict)

            # Display to player
            await self.display_service.show_daily_weather(context, weather_data, is_slash)

            # Send mechanics notification to GM channel
            guild = context.guild if hasattr(context, "guild") else context.guild
            if guild:
                await self.notification_service.send_weather_notification(guild, CHANNEL_GM_NOTIFICATIONS, weather_data)

        except Exception as e:  # noqa: BLE001 - Broad exception handling for user feedback
            await self.display_service.send_error(context, ERROR_GENERATING_WEATHER.format(error=str(e)), is_slash)

    async def _handle_next_stage(
        self,
        context: Union[discord.Interaction, commands.Context],
        guild_id: str,
        _season: Optional[str],  # Unused - kept for consistent signature
        _province: Optional[str],  # Unused - kept for consistent signature
        _day: Optional[int],  # Unused - kept for consistent signature
        is_slash: bool,
    ) -> None:
        """
        Generate weather for the next stage (multi-day).

        Generates weather for multiple consecutive days based on stage_duration
        setting. Displays a summary of all days in the stage and sends a
        notification to the GM channel.

        Args:
            context: Discord context (interaction or ctx)
            guild_id: Guild ID string for storage lookup
            _season: Unused parameter (kept for consistent handler signature)
            _province: Unused parameter (kept for consistent handler signature)
            _day: Unused parameter (kept for consistent handler signature)
            is_slash: Whether this is a slash command response

        Returns:
            None: Sends response directly to Discord

        Side Effects:
            - Generates weather for stage_duration days
            - Increments current_day by stage_duration
            - Increments stage_number by 1
            - Saves all generated weather data
            - Sends GM notification
            - Displays stage summary to user

        Example:
            >>> await handler._handle_next_stage(ctx, "12345", None, None, None, False)
        """
        try:
            journey = self.storage.get_journey_state(guild_id)

            if not journey:
                await self.display_service.send_error(
                    context,
                    ERROR_NO_JOURNEY,
                    is_slash,
                )
                return

            # Get stage configuration
            stage_duration = journey.stage_duration

            # Generate weather for each day in the stage
            stage_weathers = []
            start_day = journey.current_day

            for _ in range(stage_duration):
                journey_dict = asdict(journey)
                weather_data = self._generate_daily_weather(guild_id, journey_dict)
                stage_weathers.append((weather_data["day"], weather_data))
                journey = self.storage.get_journey_state(guild_id)  # Refresh after each day

            # Prepare stage data for display
            stage_num = journey.current_stage
            stage_weathers_list = [weather_data for _, weather_data in stage_weathers]

            # Display stage summary
            await self.stage_display.show_stage_summary(context, stage_num, stage_weathers_list, is_slash)

            # Send stage notification to GM channel
            guild = context.guild if hasattr(context, "guild") else context.guild
            if guild:
                # Note: total_stages is not tracked, using stage_num as placeholder
                await self.notification_service.send_stage_notification(
                    guild,
                    CHANNEL_GM_NOTIFICATIONS,
                    stage_num,
                    stage_num,  # Using stage_num for total_stages (not tracked)
                    stage_duration,
                )

        except Exception as e:  # noqa: BLE001 - Broad exception handling for user feedback
            await self.display_service.send_error(context, ERROR_GENERATING_STAGE.format(error=str(e)), is_slash)

    async def _handle_journey(
        self,
        context: Union[discord.Interaction, commands.Context],
        guild_id: str,
        season: Optional[str],
        province: Optional[str],
        _day: Optional[int],  # Unused - day is always 1 for new journeys
        is_slash: bool,
    ) -> None:
        """
        Start a new journey with specified season and province.

        Validates that both season and province are provided, optionally ends
        any existing journey, and starts a new journey with day 1. Sends
        notifications to both user and GM channel.

        Args:
            context: Discord context (interaction or ctx)
            guild_id: Guild ID string for storage lookup
            season: Season name (required, validated non-null)
            province: Province name (required, validated non-null)
            _day: Unused parameter (kept for consistent handler signature)
            is_slash: Whether this is a slash command response

        Returns:
            None: Sends response directly to Discord

        Side Effects:
            - Ends existing journey if present
            - Starts new journey with day 1
            - Saves journey state to storage
            - Sends GM notification
            - Displays confirmation to user

        Example:
            >>> await handler._handle_journey(ctx, "12345", "winter", "reikland", None, False)
        """
        try:
            if not season or not province:
                await self.display_service.send_error(
                    context,
                    ERROR_MISSING_PARAMS,
                    is_slash,
                )
                return

            # Check if journey already exists
            existing_journey = self.storage.get_journey_state(guild_id)
            if existing_journey:
                await self.display_service.send_info(
                    context,
                    INFO_JOURNEY_REPLACE,
                    is_slash=is_slash,
                )

            # Start new journey
            self.storage.start_journey(guild_id, season.lower(), province.lower())

            await self.display_service.send_info(
                context,
                MSG_JOURNEY_START.format(season=season.title(), province=province.replace("_", " ").title())
                + "\n\nUse `/weather next` to generate the first day's weather.",
                is_slash=is_slash,
            )

            # Send journey start notification to GM channel
            guild = context.guild if hasattr(context, "guild") else context.guild
            if guild:
                await self.notification_service.send_journey_notification(
                    guild,
                    CHANNEL_GM_NOTIFICATIONS,
                    "start",
                    season=season.lower(),
                    province=province.lower(),
                )

        except Exception as e:  # noqa: BLE001 - Broad exception handling for user feedback
            await self.display_service.send_error(context, ERROR_STARTING_JOURNEY.format(error=str(e)), is_slash)

    async def _handle_view(
        self,
        context,
        guild_id: str,
        _season: Optional[str],  # Unused - kept for consistent signature
        _province: Optional[str],  # Unused - kept for consistent signature
        _day: Optional[int],  # day parameter used in body but flagged - using local 'day' instead
        is_slash: bool,
    ):
        """View specific day's weather."""
        # Note: _day parameter is required for signature consistency but we use 'day' from journey state
        day = _day  # Use the day parameter

        try:
            if day is None:
                await self.display_service.send_error(
                    context,
                    "❌ Day number is required to view historical weather.\n" "Example: `/weather view day:1`",
                    is_slash,
                )
                return

            journey = self.storage.get_journey_state(guild_id)
            if not journey:
                await self.display_service.send_error(
                    context,
                    "❌ No journey in progress. Cannot view historical weather.",
                    is_slash,
                )
                return

            # Get weather data for the specified day
            weather_db = self.storage.get_daily_weather(guild_id, day)

            if not weather_db:
                await self.display_service.send_error(
                    context,
                    f"❌ No weather data found for Day {day}. " f"Current journey is on Day {journey.current_day}.",
                    is_slash,
                )
                return

            # Reconstruct display data from database
            weather_data = self.weather_service.reconstruct_weather_data(weather_db, day)

            # Display with historical flag
            await self.display_service.show_daily_weather(context, weather_data, is_slash, is_historical=True)

        except Exception as e:
            await self.display_service.send_error(context, f"Error viewing weather: {str(e)}", is_slash)

    async def _handle_end(
        self,
        context,
        guild_id: str,
        _season: Optional[str],  # Unused - kept for consistent signature
        _province: Optional[str],  # Unused - kept for consistent signature
        _day: Optional[int],  # Unused - kept for consistent signature
        is_slash: bool,
    ):
        """End current journey."""
        try:
            journey = self.storage.get_journey_state(guild_id)

            if not journey:
                await self.display_service.send_error(context, "❌ No journey in progress to end.", is_slash)
                return

            # Get journey summary
            total_days = journey.current_day
            season = journey.season
            province = journey.province

            # End journey
            self.storage.end_journey(guild_id)

            await self.display_service.send_info(
                context,
                f"🏁 **Journey Ended**\n\n"
                f"**Duration:** {total_days} days\n"
                f"**Season:** {season.title()}\n"
                f"**Province:** {province.replace('_', ' ').title()}\n\n"
                f"Use `/weather journey` to start a new journey.",
                is_slash,
            )

            # Send journey end notification to GM channel
            guild = context.guild if hasattr(context, "guild") else context.guild
            if guild:
                await self.notification_service.send_journey_notification(
                    guild,
                    "boat-travelling-notifications",
                    "end",
                    season=season,
                    province=province,
                )

        except Exception as e:
            await self.display_service.send_error(context, f"Error ending journey: {str(e)}", is_slash)

    async def _handle_override(
        self,
        context,
        _guild_id: str,  # Unused - kept for consistent signature
        _season: Optional[str],  # Unused - not yet implemented
        _province: Optional[str],  # Unused - not yet implemented
        _day: Optional[int],  # Unused - not yet implemented
        is_slash: bool,
    ):
        """Override weather (GM only)."""
        # This will be implemented when we integrate with main weather.py
        # which has the is_gm() check
        await self.display_service.send_error(
            context,
            "❌ Override feature not yet implemented in refactored handler.",
            is_slash,
        )

    async def configure_stage(
        self,
        context,
        stage_duration: Optional[int],
        display_mode: Optional[str],
        is_slash: bool,
    ):
        """
        Configure stage settings (GM only).

        Args:
            context: Discord context
            stage_duration: Number of days per stage
            display_mode: Display mode (simple/detailed)
            is_slash: Whether this is a slash command
        """
        guild_id = str(context.guild.id) if context.guild else None

        if not guild_id:
            await self.display_service.send_error(context, "This command must be used in a server.", is_slash)
            return

        try:
            journey = self.storage.get_journey_state(guild_id)

            if not journey:
                await self.display_service.send_error(
                    context,
                    "❌ No journey in progress. Start a journey first with `/weather journey`.",
                    is_slash,
                )
                return

            # Update stage duration if provided
            if stage_duration is not None:
                if stage_duration < 1 or stage_duration > 10:
                    await self.display_service.send_error(
                        context,
                        "❌ Stage duration must be between 1 and 10 days.",
                        is_slash,
                    )
                    return

                self.storage.update_stage_duration(guild_id, stage_duration)

            # Update display mode if provided
            if display_mode is not None:
                if display_mode not in ["simple", "detailed"]:
                    await self.display_service.send_error(
                        context,
                        "❌ Display mode must be either 'simple' or 'detailed'.",
                        is_slash,
                    )
                    return

                self.storage.update_stage_display_mode(guild_id, display_mode)

            # Get current settings
            journey = self.storage.get_journey_state(guild_id)
            current_duration = journey.get("stage_duration", 3)
            current_mode = journey.get("display_mode", "simple")

            await self.display_service.send_info(
                context,
                f"⚙️ **Stage Configuration Updated**\n\n"
                f"**Stage Duration:** {current_duration} days\n"
                f"**Display Mode:** {current_mode.title()}\n\n"
                f"These settings will apply to future stage generations.",
                is_slash,
            )

        except Exception as e:
            await self.display_service.send_error(context, f"Error configuring stage: {str(e)}", is_slash)

    def _generate_daily_weather(self, guild_id: str, journey: dict) -> dict:
        """
        Generate weather data for a single day using DailyWeatherService.

        Args:
            guild_id: Guild ID
            journey: Current journey state dict

        Returns:
            dict: Complete weather data including wind, temperature, conditions
        """
        # Delegate to DailyWeatherService (pass the whole journey dict)
        return self.weather_service.generate_daily_weather(guild_id, journey)
