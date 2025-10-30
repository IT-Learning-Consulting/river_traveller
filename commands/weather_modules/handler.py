"""
Weather command handler - orchestrates weather generation and display.

This module provides the main business logic for weather commands, coordinating
between weather generation, storage, display, and notifications.
"""

from typing import Optional

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


class WeatherCommandHandler:
    """
    Main handler for weather commands.

    Responsibilities:
    - Route actions to appropriate methods
    - Generate weather data
    - Coordinate display and notifications
    - Manage journey state
    """

    def __init__(self):
        """Initialize the handler with required dependencies."""
        self.storage = WeatherStorage()
        # Note: display, stage_display, and notifications are classes with static methods
        # We reference them directly rather than instantiating
        self.display = WeatherDisplayManager
        self.stage_display = StageDisplayManager
        self.notifications = NotificationManager

    async def handle_command(
        self,
        context,
        action: str,
        season: Optional[str],
        province: Optional[str],
        day: Optional[int],
        is_slash: bool,
    ):
        """
        Route command to appropriate handler method.

        Args:
            context: Discord context (interaction or ctx)
            action: The action to perform (next, view, journey, etc.)
            season: Season name (optional, used for journey/override)
            province: Province name (optional, used for journey/override)
            day: Day number (optional, used for view)
            is_slash: Whether this is a slash command
        """
        guild_id = str(context.guild.id) if context.guild else None

        if not guild_id:
            await self.display.send_error(
                context, "This command must be used in a server.", is_slash
            )
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
            await handler_func(context, guild_id, season, province, day, is_slash)
            # Log command after successful execution
            await self._send_command_log(
                context, action, season, province, day, is_slash
            )
        else:
            await self.display.send_error(
                context, f"Unknown action: {action}", is_slash
            )

    async def _handle_next(
        self,
        context,
        guild_id: str,
        _season: Optional[str],  # Unused - kept for consistent signature
        _province: Optional[str],  # Unused - kept for consistent signature
        _day: Optional[int],  # Unused - kept for consistent signature
        is_slash: bool,
    ):
        """Generate weather for the next day."""
        try:
            journey = self.storage.get_journey_state(guild_id)

            # Auto-start journey if needed
            if not journey:
                await self.display.send_info(
                    context,
                    "⚠️ No journey in progress. Starting new journey with default settings (Summer in Reikland).",
                    is_slash,
                )
                self.storage.start_journey(guild_id, "summer", "reikland")
                journey = self.storage.get_journey_state(guild_id)

                # Send initial journey start notification
                guild = context.guild if hasattr(context, "guild") else context.guild
                if guild:
                    await self.notifications.send_journey_notification(
                        guild,
                        "boat-travelling-notifications",
                        "start",
                        season="summer",
                        province="reikland",
                    )

            # Generate weather data
            weather_data = self._generate_daily_weather(guild_id, journey)

            # Display to player
            await self.display.show_daily_weather(context, weather_data, is_slash)

            # Send mechanics notification to GM channel
            guild = context.guild if hasattr(context, "guild") else context.guild
            if guild:
                await self.notifications.send_weather_notification(
                    guild, "boat-travelling-notifications", weather_data
                )

        except Exception as e:
            await self.display.send_error(
                context, f"Error generating weather: {str(e)}", is_slash
            )

    async def _handle_next_stage(
        self,
        context,
        guild_id: str,
        _season: Optional[str],  # Unused - kept for consistent signature
        _province: Optional[str],  # Unused - kept for consistent signature
        _day: Optional[int],  # Unused - kept for consistent signature
        is_slash: bool,
    ):
        """Generate weather for the next stage (multi-day)."""
        try:
            journey = self.storage.get_journey_state(guild_id)

            if not journey:
                await self.display.send_error(
                    context,
                    "❌ No journey in progress. Use `/weather journey` to start a new journey first.",
                    is_slash,
                )
                return

            # Get stage configuration
            stage_duration = journey.get("stage_duration", 3)

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
                    "boat-travelling-notifications",
                    stage_num,
                    stage_num,  # Using stage_num for total_stages (not tracked)
                    stage_duration,
                )

        except Exception as e:
            await self.display.send_error(
                context, f"Error generating stage: {str(e)}", is_slash
            )

    async def _handle_journey(
        self,
        context,
        guild_id: str,
        season: Optional[str],
        province: Optional[str],
        _day: Optional[int],  # Unused - day is always 1 for new journeys
        is_slash: bool,
    ):
        """Start a new journey."""
        try:
            if not season or not province:
                await self.display.send_error(
                    context,
                    "❌ Both season and province are required to start a journey.\n"
                    "Example: `/weather journey season:summer province:reikland`",
                    is_slash,
                )
                return

            # Check if journey already exists
            existing_journey = self.storage.get_journey_state(guild_id)
            if existing_journey:
                await self.display.send_info(
                    context,
                    "⚠️ A journey is already in progress. Ending previous journey and starting new one.",
                    is_slash,
                )

            # Start new journey
            self.storage.start_journey(guild_id, season.lower(), province.lower())

            await self.display.send_info(
                context,
                f"🗺️ **New Journey Started!**\n\n"
                f"**Season:** {season.title()}\n"
                f"**Province:** {province.replace('_', ' ').title()}\n\n"
                f"Use `/weather next` to generate the first day's weather.",
                is_slash,
            )

            # Send journey start notification to GM channel
            guild = context.guild if hasattr(context, "guild") else context.guild
            if guild:
                await self.notifications.send_journey_notification(
                    guild,
                    "boat-travelling-notifications",
                    "start",
                    season=season.lower(),
                    province=province.lower(),
                )

        except Exception as e:
            await self.display.send_error(
                context, f"Error starting journey: {str(e)}", is_slash
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
            previous_midnight = current_weather["wind_timeline"][3]
            wind_timeline = generate_daily_wind_with_previous(previous_midnight)
            continuity_note = (
                f"🔄 Wind carried over from Day {current_day} midnight: "
                f"{previous_midnight['strength']} {previous_midnight['direction']}"
            )
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
