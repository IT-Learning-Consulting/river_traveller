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
    The handler acts as a facade, delegating to specialized modules:
    - WeatherStorage: Persistent state and data storage
    - WeatherMechanics: Weather generation algorithms
    - WeatherDisplayManager: User-facing display formatting
    - NotificationManager: GM channel notifications
    - StageDisplayManager: Multi-day stage summaries

Usage Example:
    >>> handler = WeatherCommandHandler()
    >>> await handler.handle_command(ctx, "next", None, None, None, False)
    # Generates and displays next day's weather

Command Flow:
    1. Command received → handle_command() routes to action handler
    2. Action handler validates inputs and retrieves journey state
    3. Weather generation creates daily data (if applicable)
    4. Display manager sends formatted embed to user
    5. Notification manager sends GM notification
    6. Command logged to command-log channel
"""

from typing import Any, Dict, Optional, Union

import discord
from discord.ext import commands

from db.weather_storage import WeatherStorage
from utils.weather_mechanics import (
    generate_daily_wind,
    generate_daily_wind_with_previous,
    roll_weather_condition,
    get_weather_effects,
    roll_temperature_with_special_events,
    apply_wind_chill,
    get_province_base_temperature,
)
from commands.weather_modules.display import WeatherDisplayManager
from commands.weather_modules.stages import StageDisplayManager
from commands.weather_modules.notifications import NotificationManager

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
ERROR_NO_JOURNEY = (
    "❌ No journey in progress. Use `/weather journey` to start a new journey first."
)
ERROR_MISSING_PARAMS = "❌ Both season and province are required to start a journey.\nExample: `/weather journey season:summer province:reikland`"
ERROR_NO_DAY_PARAM = "❌ Day parameter is required. Example: `/weather view day:2`"
ERROR_DAY_NOT_FOUND = "❌ No weather data found for day {day}."
ERROR_NOT_IMPLEMENTED = "❌ This feature is not yet implemented."
ERROR_NO_STAGE_CONFIG_GUILD = "This command must be used in a server."
ERROR_NO_STAGE_CONFIG_JOURNEY = (
    "❌ No journey in progress. Start a journey first with `/weather journey`."
)
ERROR_INVALID_STAGE_DURATION = "❌ Stage duration must be between 1 and 10 days."

# Info messages
INFO_AUTO_START_JOURNEY = "⚠️ No journey in progress. Starting new journey with default settings (Summer in Reikland)."
INFO_JOURNEY_REPLACE = (
    "⚠️ A journey is already in progress. Ending previous journey and starting new one."
)
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
    Main handler for weather command routing and orchestration.

    This class coordinates all weather-related operations, acting as the central
    controller for the weather system. It routes commands to appropriate handlers,
    manages journey state, generates weather data, and coordinates display and
    notifications.

    Responsibilities:
        - Route command actions to appropriate handler methods
        - Generate daily weather data using weather mechanics
        - Manage journey lifecycle (start, progress, end)
        - Coordinate between storage, display, and notification modules
        - Handle errors and provide user feedback
        - Support stage-based progression for multi-day travel
        - Log command execution to command-log channel

    Attributes:
        storage (WeatherStorage): Persistent storage for journey and weather data
        display (WeatherDisplayManager): Static class for user-facing displays
        stage_display (StageDisplayManager): Static class for stage summaries
        notifications (NotificationManager): Static class for GM notifications

    Design Pattern:
        This class uses a facade pattern, providing a simple interface for
        complex weather system operations while delegating specific tasks
        to specialized modules.

    Example:
        >>> handler = WeatherCommandHandler()
        >>> # Generate next day's weather
        >>> await handler.handle_command(ctx, "next", None, None, None, False)
        >>> # Start new journey
        >>> await handler.handle_command(ctx, "journey", "winter", "reikland", None, True)
        >>> # View historical weather
        >>> await handler.handle_command(ctx, "view", None, None, 5, False)
    """

    def __init__(self) -> None:
        """
        Initialize the handler with required dependencies.

        Sets up storage access and references to display/notification modules.
        Display and notification modules use static methods, so we reference
        the classes directly rather than instantiating them.
        """
        self.storage = WeatherStorage()
        # Note: display, stage_display, and notifications are classes with static methods
        # We reference them directly rather than instantiating
        self.display = WeatherDisplayManager
        self.stage_display = StageDisplayManager
        self.notifications = NotificationManager

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
            await self.display.send_error(context, ERROR_NO_GUILD, is_slash)
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
                await self._send_command_log(
                    context, action, season, province, day, is_slash
                )
            except (
                Exception
            ) as e:  # noqa: BLE001 - Broad exception handling for user feedback
                # Catch any errors from action handlers and display to user
                await self.display.send_error(
                    context, ERROR_COMMAND_FAILED.format(error=str(e)), is_slash
                )
        else:
            await self.display.send_error(
                context, ERROR_UNKNOWN_ACTION.format(action=action), is_slash
            )

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
                await self.display.send_info(
                    context,
                    INFO_AUTO_START_JOURNEY,
                    is_slash=is_slash,
                )
                self.storage.start_journey(guild_id, DEFAULT_SEASON, DEFAULT_PROVINCE)
                journey = self.storage.get_journey_state(guild_id)

                # Send initial journey start notification
                guild = context.guild if hasattr(context, "guild") else context.guild
                if guild:
                    await self.notifications.send_journey_notification(
                        guild,
                        CHANNEL_GM_NOTIFICATIONS,
                        "start",
                        season=DEFAULT_SEASON,
                        province=DEFAULT_PROVINCE,
                    )

            # Generate weather data
            weather_data = self._generate_daily_weather(guild_id, journey)

            # Display to player
            await self.display.show_daily_weather(context, weather_data, is_slash)

            # Send mechanics notification to GM channel
            guild = context.guild if hasattr(context, "guild") else context.guild
            if guild:
                await self.notifications.send_weather_notification(
                    guild, CHANNEL_GM_NOTIFICATIONS, weather_data
                )

        except (
            Exception
        ) as e:  # noqa: BLE001 - Broad exception handling for user feedback
            await self.display.send_error(
                context, ERROR_GENERATING_WEATHER.format(error=str(e)), is_slash
            )

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
                await self.display.send_error(
                    context,
                    ERROR_NO_JOURNEY,
                    is_slash,
                )
                return

            # Get stage configuration
            stage_duration = journey.get("stage_duration", DEFAULT_STAGE_DURATION)

            # Generate weather for each day in the stage
            stage_weathers = []
            start_day = journey["current_day"]

            for _ in range(stage_duration):
                weather_data = self._generate_daily_weather(guild_id, journey)
                stage_weathers.append((weather_data["day"], weather_data))
                journey = self.storage.get_journey_state(
                    guild_id
                )  # Refresh after each day

            # Prepare stage data for display
            stage_num = journey.get("stage_number", 1)
            stage_weathers_list = [weather_data for _, weather_data in stage_weathers]

            # Display stage summary
            await self.stage_display.show_stage_summary(
                context, stage_num, stage_weathers_list, is_slash
            )

            # Send stage notification to GM channel
            guild = context.guild if hasattr(context, "guild") else context.guild
            if guild:
                # Note: total_stages is not tracked, using stage_num as placeholder
                await self.notifications.send_stage_notification(
                    guild,
                    CHANNEL_GM_NOTIFICATIONS,
                    stage_num,
                    stage_num,  # Using stage_num for total_stages (not tracked)
                    stage_duration,
                )

        except (
            Exception
        ) as e:  # noqa: BLE001 - Broad exception handling for user feedback
            await self.display.send_error(
                context, ERROR_GENERATING_STAGE.format(error=str(e)), is_slash
            )

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
                await self.display.send_error(
                    context,
                    ERROR_MISSING_PARAMS,
                    is_slash,
                )
                return

            # Check if journey already exists
            existing_journey = self.storage.get_journey_state(guild_id)
            if existing_journey:
                await self.display.send_info(
                    context,
                    INFO_JOURNEY_REPLACE,
                    is_slash=is_slash,
                )

            # Start new journey
            self.storage.start_journey(guild_id, season.lower(), province.lower())

            await self.display.send_info(
                context,
                MSG_JOURNEY_START.format(
                    season=season.title(), province=province.replace("_", " ").title()
                )
                + "\n\nUse `/weather next` to generate the first day's weather.",
                is_slash=is_slash,
            )

            # Send journey start notification to GM channel
            guild = context.guild if hasattr(context, "guild") else context.guild
            if guild:
                await self.notifications.send_journey_notification(
                    guild,
                    CHANNEL_GM_NOTIFICATIONS,
                    "start",
                    season=season.lower(),
                    province=province.lower(),
                )

        except (
            Exception
        ) as e:  # noqa: BLE001 - Broad exception handling for user feedback
            await self.display.send_error(
                context, ERROR_STARTING_JOURNEY.format(error=str(e)), is_slash
            )

    async def _handle_view(
        self,
        context,
        guild_id: str,
        _season: Optional[str],  # Unused - kept for consistent signature
        _province: Optional[str],  # Unused - kept for consistent signature
        _day: Optional[
            int
        ],  # day parameter used in body but flagged - using local 'day' instead
        is_slash: bool,
    ):
        """View specific day's weather."""
        # Note: _day parameter is required for signature consistency but we use 'day' from journey state
        day = _day  # Use the day parameter

        try:
            if day is None:
                await self.display.send_error(
                    context,
                    "❌ Day number is required to view historical weather.\n"
                    "Example: `/weather view day:1`",
                    is_slash,
                )
                return

            journey = self.storage.get_journey_state(guild_id)
            if not journey:
                await self.display.send_error(
                    context,
                    "❌ No journey in progress. Cannot view historical weather.",
                    is_slash,
                )
                return

            # Get weather data for the specified day
            weather_db = self.storage.get_daily_weather(guild_id, day)

            if not weather_db:
                await self.display.send_error(
                    context,
                    f"❌ No weather data found for Day {day}. "
                    f"Current journey is on Day {journey['current_day']}.",
                    is_slash,
                )
                return

            # Reconstruct display data from database
            weather_data = self._reconstruct_weather_data(weather_db, day, journey)

            # Display with historical flag
            await self.display.show_daily_weather(
                context, weather_data, is_slash, is_historical=True
            )

        except Exception as e:
            await self.display.send_error(
                context, f"Error viewing weather: {str(e)}", is_slash
            )

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
                await self.display.send_error(
                    context, "❌ No journey in progress to end.", is_slash
                )
                return

            # Get journey summary
            total_days = journey["current_day"]
            season = journey["season"]
            province = journey["province"]

            # End journey
            self.storage.end_journey(guild_id)

            await self.display.send_info(
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
                await self.notifications.send_journey_notification(
                    guild,
                    "boat-travelling-notifications",
                    "end",
                    season=season,
                    province=province,
                )

        except Exception as e:
            await self.display.send_error(
                context, f"Error ending journey: {str(e)}", is_slash
            )

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
        await self.display.send_error(
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
            await self.display.send_error(
                context, "This command must be used in a server.", is_slash
            )
            return

        try:
            journey = self.storage.get_journey_state(guild_id)

            if not journey:
                await self.display.send_error(
                    context,
                    "❌ No journey in progress. Start a journey first with `/weather journey`.",
                    is_slash,
                )
                return

            # Update stage duration if provided
            if stage_duration is not None:
                if stage_duration < 1 or stage_duration > 10:
                    await self.display.send_error(
                        context,
                        "❌ Stage duration must be between 1 and 10 days.",
                        is_slash,
                    )
                    return

                self.storage.update_stage_duration(guild_id, stage_duration)

            # Update display mode if provided
            if display_mode is not None:
                if display_mode not in ["simple", "detailed"]:
                    await self.display.send_error(
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

            await self.display.send_info(
                context,
                f"⚙️ **Stage Configuration Updated**\n\n"
                f"**Stage Duration:** {current_duration} days\n"
                f"**Display Mode:** {current_mode.title()}\n\n"
                f"These settings will apply to future stage generations.",
                is_slash,
            )

        except Exception as e:
            await self.display.send_error(
                context, f"Error configuring stage: {str(e)}", is_slash
            )

    def _generate_daily_weather(self, guild_id: str, journey: dict) -> dict:
        """
        Generate weather data for a single day.

        Args:
            guild_id: Guild ID
            journey: Current journey state

        Returns:
            dict: Complete weather data including wind, temperature, conditions
        """
        current_day = journey["current_day"]
        season = journey["season"]
        province = journey["province"]

        current_weather = self.storage.get_daily_weather(guild_id, current_day)

        # Determine day number and wind continuity
        if current_weather:
            new_day = self.storage.advance_day(guild_id)
            # Check if wind_timeline exists and has at least 4 elements
            wind_timeline_data = current_weather.get("wind_timeline", [])
            if wind_timeline_data and len(wind_timeline_data) >= 4:
                previous_midnight = wind_timeline_data[3]
                wind_timeline = generate_daily_wind_with_previous(previous_midnight)
                continuity_note = (
                    f"🔄 Wind carried over from Day {current_day} midnight: "
                    f"{previous_midnight['strength']} {previous_midnight['direction']}"
                )
            else:
                # No valid wind timeline - generate fresh
                wind_timeline = generate_daily_wind()
                continuity_note = None
        else:
            new_day = current_day
            wind_timeline = generate_daily_wind()
            continuity_note = None

        # Generate temperature with special events
        # Get previous weather and cooldown status
        previous_weather = (
            self.storage.get_daily_weather(guild_id, new_day - 1)
            if new_day > 1
            else None
        )

        # Extract cold front state from previous weather
        cold_front_days = (
            previous_weather.get("cold_front_days_remaining", 0)
            if previous_weather
            else 0
        )
        cold_front_total = (
            previous_weather.get("cold_front_total_duration", 0)
            if previous_weather
            else 0
        )

        # Extract heat wave state from previous weather
        heat_wave_days = (
            previous_weather.get("heat_wave_days_remaining", 0)
            if previous_weather
            else 0
        )
        heat_wave_total = (
            previous_weather.get("heat_wave_total_duration", 0)
            if previous_weather
            else 0
        )

        # Get cooldown trackers from journey state
        journey_state = self.storage.get_journey_state(guild_id)
        days_since_cf, days_since_hw = self.storage.get_cooldown_status(guild_id)

        weather_type = roll_weather_condition(season)
        weather_effects_data = get_weather_effects(weather_type)

        # Roll temperature with all context (8 parameters → 8 returns)
        (
            actual_temp,
            temp_category,
            temp_description,
            temp_roll,
            cold_front_remaining,
            cold_front_total_new,
            heat_wave_remaining,
            heat_wave_total_new,
        ) = roll_temperature_with_special_events(
            season,
            province,
            cold_front_days,
            cold_front_total,
            heat_wave_days,
            heat_wave_total,
            days_since_cf,
            days_since_hw,
        )

        base_temp = get_province_base_temperature(province, season)
        wind_strengths = [w["strength"] for w in wind_timeline]

        # Defensive: handle empty wind_timeline
        if not wind_strengths:
            most_common_wind = "Calm"
        else:
            most_common_wind = max(set(wind_strengths), key=wind_strengths.count)

        perceived_temp = apply_wind_chill(actual_temp, most_common_wind)

        # Update cooldown trackers
        self._update_cooldown_trackers(
            guild_id,
            cold_front_days,
            cold_front_remaining,
            heat_wave_days,
            heat_wave_remaining,
        )

        # Save to database with new fields
        weather_db_data = {
            "season": season,
            "province": province,
            "wind_timeline": wind_timeline,
            "weather_type": weather_type,
            "weather_roll": 0,
            "temperature_actual": actual_temp,
            "temperature_category": temp_category,
            "temperature_roll": temp_roll,
            "cold_front_days_remaining": cold_front_remaining,
            "cold_front_total_duration": cold_front_total_new,
            "heat_wave_days_remaining": heat_wave_remaining,
            "heat_wave_total_duration": heat_wave_total_new,
        }
        self.storage.save_daily_weather(guild_id, new_day, weather_db_data)

        # Return enriched data for display
        return {
            "day": new_day,
            "season": season,
            "province": province,
            "wind_timeline": wind_timeline,
            "weather_type": weather_type,
            "weather_effects": weather_effects_data["effects"],
            "actual_temp": actual_temp,
            "perceived_temp": perceived_temp,
            "base_temp": base_temp,
            "temp_category": temp_category,
            "temp_description": temp_description,
            "most_common_wind": most_common_wind,
            "cold_front_days": cold_front_remaining,
            "heat_wave_days": heat_wave_remaining,
            "continuity_note": continuity_note,
        }

    def _reconstruct_weather_data(
        self,
        weather_db: dict,
        day: int,
        _journey: dict,  # journey unused but kept for future use
    ) -> dict:
        """
        Reconstruct display-ready weather data from database.

        Args:
            weather_db: Weather data from database
            day: Day number
            journey: Journey state

        Returns:
            dict: Complete weather data for display
        """
        actual_temp = weather_db["temperature_actual"]
        wind_strengths = [w["strength"] for w in weather_db["wind_timeline"]]

        # Defensive: handle empty wind_timeline
        if not wind_strengths:
            most_common_wind = "Calm"
        else:
            most_common_wind = max(set(wind_strengths), key=wind_strengths.count)

        perceived_temp = apply_wind_chill(actual_temp, most_common_wind)

        base_temp = get_province_base_temperature(
            weather_db["province"], weather_db["season"]
        )

        weather_effects_data = get_weather_effects(weather_db["weather_type"])

        # Reconstruct temperature description
        temp_category = weather_db["temperature_category"]
        temp_descriptions = {
            "very_cold": "Bitterly cold",
            "cold": "Cold",
            "cool": "Cool",
            "mild": "Mild",
            "warm": "Warm",
            "hot": "Hot",
            "very_hot": "Sweltering heat",
        }
        temp_description = temp_descriptions.get(temp_category, "Mild")

        return {
            "day": day,
            "season": weather_db["season"],
            "province": weather_db["province"],
            "wind_timeline": weather_db["wind_timeline"],
            "weather_type": weather_db["weather_type"],
            "weather_effects": weather_effects_data["effects"],
            "actual_temp": actual_temp,
            "perceived_temp": perceived_temp,
            "base_temp": base_temp,
            "temp_category": temp_category,
            "temp_description": temp_description,
            "most_common_wind": most_common_wind,
            "cold_front_days": weather_db["cold_front_days_remaining"],
            "heat_wave_days": weather_db["heat_wave_days_remaining"],
            "continuity_note": None,  # Historical views don't show continuity
        }

    def _update_cooldown_trackers(
        self,
        guild_id: str,
        previous_cold_front_days: int,
        current_cold_front_days: int,
        previous_heat_wave_days: int,
        current_heat_wave_days: int,
    ):
        """
        Update cooldown trackers based on event state transitions.

        Args:
            guild_id: Guild ID
            previous_cold_front_days: Days remaining before this generation
            current_cold_front_days: Days remaining after this generation
            previous_heat_wave_days: Days remaining before this generation
            current_heat_wave_days: Days remaining after this generation
        """
        # Cold front cooldown logic
        if current_cold_front_days > 0:
            # Event is active
            if previous_cold_front_days == 0:
                # New event just started - reset cooldown
                self.storage.reset_cooldown(guild_id, "cold_front")
            # else: Event was already active - cooldown stays at 0
        elif previous_cold_front_days > 0 and current_cold_front_days == 0:
            # Event just ended - start incrementing cooldown
            self.storage.increment_cooldown(guild_id, "cold_front")
        elif previous_cold_front_days == 0 and current_cold_front_days == 0:
            # No event - continue incrementing cooldown
            self.storage.increment_cooldown(guild_id, "cold_front")

        # Heat wave cooldown logic (same pattern)
        if current_heat_wave_days > 0:
            # Event is active
            if previous_heat_wave_days == 0:
                # New event just started - reset cooldown
                self.storage.reset_cooldown(guild_id, "heat_wave")
            # else: Event was already active - cooldown stays at 0
        elif previous_heat_wave_days > 0 and current_heat_wave_days == 0:
            # Event just ended - start incrementing cooldown
            self.storage.increment_cooldown(guild_id, "heat_wave")
        elif previous_heat_wave_days == 0 and current_heat_wave_days == 0:
            # No event - continue incrementing cooldown
            self.storage.increment_cooldown(guild_id, "heat_wave")

    async def _send_command_log(
        self,
        context,
        action: str,
        season: Optional[str],
        province: Optional[str],
        day: Optional[int],
        is_slash: bool,
    ):
        """Send command details to boat-travelling-log channel."""
        try:
            import discord

            # Find the log channel
            log_channel = discord.utils.get(
                context.guild.text_channels, name="boat-travelling-log"
            )
            if not log_channel:
                return  # Silently fail if log channel doesn't exist

            # Get username
            if is_slash:
                username = context.user.display_name
                user_id = context.user.id
            else:
                username = context.author.display_name
                user_id = context.author.id

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
                if season:
                    command_str += f" {season}"
                if province:
                    command_str += f" {province}"
                if day is not None:
                    command_str += f" {day}"

            # Create log embed
            log_embed = discord.Embed(
                title="🌦️ Command Log: Weather",
                description=f"**User:** {username} (`{user_id}`)\n**Command:** `{command_str}`",
                color=discord.Color.gold(),
                timestamp=discord.utils.utcnow(),
            )

            log_embed.add_field(name="Action", value=action, inline=True)
            if season:
                log_embed.add_field(name="Season", value=season.title(), inline=True)
            if province:
                log_embed.add_field(
                    name="Province",
                    value=province.replace("_", " ").title(),
                    inline=True,
                )
            if day is not None:
                log_embed.add_field(name="Day", value=str(day), inline=True)

            await log_channel.send(embed=log_embed)

        except (discord.Forbidden, discord.HTTPException, AttributeError):
            # Silently fail - logging is not critical
            pass
