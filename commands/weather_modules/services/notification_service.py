"""
NotificationService - GM Channel Notification Management

Extracted from WeatherCommandHandler as part of Phase 2.1 service decomposition.

Responsibilities:
    - Send weather mechanics notifications to GM channels
    - Format boat handling modifiers and penalties
    - Notify about stage progression and journey events
    - Provide quick reference information for GMs
    - Handle special weather events (cold fronts, heat waves)

Design Principles:
    - Pure business logic - no Discord dependencies in interface (async methods still use Discord types)
    - Error-resilient: Returns bool for success/failure instead of raising exceptions
    - Stateless: All methods are static/class methods
    - Single Responsibility: Focused only on notification dispatch and formatting

Service Interface:
    - send_weather_notification(guild, channel_name, weather_data) -> bool
    - send_stage_notification(guild, channel_name, stage, total, duration) -> bool
    - send_journey_notification(guild, channel_name, event_type, **kwargs) -> bool

Dependencies:
    - Discord.py for channel lookup and message sending
    - WeatherFormatters for province/season name formatting
    - WIND_MODIFIERS from weather_data for boat handling details

Usage Example:
    >>> service = NotificationService()
    >>> success = await service.send_weather_notification(guild, "gm-channel", weather_data)
    >>> success = await service.send_stage_notification(guild, "gm-channel", 2, 5, 3)
"""

from typing import Any, Dict, Optional

import discord

from ..formatters import WeatherFormatters
from db.weather_data import WIND_MODIFIERS

# Embed colors
COLOR_NOTIFICATION = discord.Color.gold()

# Notification titles
TITLE_WEATHER_MECHANICS = "⚠️ Active Weather Mechanics"
TITLE_BOAT_HANDLING = "🚢 Boat Handling Modifiers"
TITLE_ACTIVE_PENALTIES = "🎯 Active Penalties & Conditions"
TITLE_TEMPERATURE = "🌡️ Temperature"
TITLE_SPECIAL_EVENTS = "🌨️ Special Weather Events"
TITLE_SPECIAL_EVENTS_HEAT = "☀️ Special Weather Events"
TITLE_NOTES = "💡 Notes"

# Notification messages
MSG_WIND_CHANGE_NOTE = "• Wind is checked at dawn, midday, dusk, and midnight (10% chance to change each check)"
MSG_CALM_CONDITIONS = "Calm conditions: -10 penalty, 25% speed"
MSG_NO_HAZARDS = "No weather-related hazards"

# Journey notification messages
MSG_JOURNEY_START = "**🗺️ Journey Started**\nLocation: {province}\nSeason: {season}"
MSG_JOURNEY_END = "**🏁 Journey Ended**\nTotal Duration: {duration} day{plural}"
MSG_JOURNEY_ADVANCE = "**📅 Advanced to Day {day}**"
MSG_STAGE_COMPLETE = "**🚢 Stage {current}/{total} Complete**\nDuration: {duration} day{plural}"

# Special event messages
MSG_COLD_FRONT = "❄️ **Cold Front: Day {elapsed} of {total}**"
MSG_COLD_FRONT_MODIFIER = "• Temperature modifier: -10°C"
MSG_COLD_FRONT_FIRST_DAY = "• Sky filled with flocks of emigrating birds"
MSG_COLD_FRONT_FINAL = "• **(Final Day)**"

MSG_HEAT_WAVE = "🔥 **Heat Wave: Day {elapsed} of {total}**"
MSG_HEAT_WAVE_MODIFIER = "• Temperature modifier: +10°C"
MSG_HEAT_WAVE_FINAL = "• **(Final Day)**"

# Default values
DEFAULT_PROVINCE = "Unknown"
DEFAULT_SEASON = "spring"
DEFAULT_WEATHER = "fair"
DEFAULT_TEMPERATURE = 15
DEFAULT_DAY = 1


class NotificationService:
    """
    Service for managing GM channel notifications.

    Handles sending weather mechanics notifications, stage completion messages,
    and journey lifecycle events to GM channels. All methods are async to
    accommodate Discord API calls.

    All notification methods follow error-resilient pattern:
        - Return bool (True=success, False=failure)
        - Never raise exceptions to calling code
        - Handle channel not found, permissions, and API errors gracefully
    """

    @staticmethod
    async def send_weather_notification(guild: discord.Guild, channel_name: str, weather_data: Dict[str, Any]) -> bool:
        """
        Send weather notification embed to GM channel.

        Creates detailed mechanics-focused embed with boat handling modifiers,
        active penalties, temperature effects, and special events.

        Args:
            guild: Discord guild to search for channel
            channel_name: Target GM channel name (e.g., "gm-notifications")
            weather_data: Weather information dictionary with keys:
                - day: Current day number
                - province: Province name
                - season: Season name
                - weather_type: Weather type (dry/fair/rain/etc)
                - actual_temp: Actual temperature
                - perceived_temp: Temperature after wind chill
                - temp_category: Temperature category
                - wind_timeline: List of wind conditions by time
                - weather_effects: List of effect strings
                - cold_front_days_remaining: Optional cold front days
                - heat_wave_days_remaining: Optional heat wave days

        Returns:
            bool: True if sent successfully, False if channel not found,
                  permission denied, or API error

        Example:
            >>> weather_data = {"day": 5, "province": "reikland", ...}
            >>> success = await NotificationService.send_weather_notification(
            ...     guild, "gm-channel", weather_data
            ... )
        """
        # Find the channel
        if not guild:
            return False

        channel = discord.utils.get(guild.text_channels, name=channel_name)
        if not channel:
            return False

        # Create the embed
        embed = NotificationService._create_notification_embed(weather_data)

        try:
            await channel.send(embed=embed)
            return True
        except discord.Forbidden:
            # Bot doesn't have permission to send messages
            return False
        except discord.HTTPException:
            # Other Discord API error
            return False

    @staticmethod
    async def send_stage_notification(
        guild: discord.Guild,
        channel_name: str,
        current_stage: int,
        total_stages: int,
        stage_duration: int,
    ) -> bool:
        """
        Send stage completion notification to GM channel.

        Sends simple text message announcing stage completion with duration.

        Args:
            guild: Discord guild to search for channel
            channel_name: Target GM channel name
            current_stage: Current stage number (1-indexed)
            total_stages: Total number of stages in journey
            stage_duration: Duration of completed stage in days

        Returns:
            bool: True if sent successfully, False otherwise

        Example:
            >>> success = await NotificationService.send_stage_notification(
            ...     guild, "gm-channel", 2, 5, 3
            ... )
        """
        # Find the channel
        if not guild:
            return False

        channel = discord.utils.get(guild.text_channels, name=channel_name)
        if not channel:
            return False

        # Format message
        plural = "" if stage_duration == 1 else "s"
        message = MSG_STAGE_COMPLETE.format(
            current=current_stage,
            total=total_stages,
            duration=stage_duration,
            plural=plural,
        )

        try:
            await channel.send(message)
            return True
        except discord.Forbidden:
            return False
        except discord.HTTPException:
            return False

    @staticmethod
    async def send_journey_notification(guild: discord.Guild, channel_name: str, event_type: str, **kwargs) -> bool:
        """
        Send journey lifecycle notification to GM channel.

        Handles start, end, and day advance notifications.

        Args:
            guild: Discord guild to search for channel
            channel_name: Target GM channel name
            event_type: Type of event ("start", "end", "advance")
            **kwargs: Event-specific data:
                - start: province (str), season (str)
                - end: duration (int)
                - advance: day (int)

        Returns:
            bool: True if sent successfully, False otherwise

        Example:
            >>> # Journey start
            >>> await NotificationService.send_journey_notification(
            ...     guild, "gm-channel", "start", province="reikland", season="winter"
            ... )
            >>> # Journey end
            >>> await NotificationService.send_journey_notification(
            ...     guild, "gm-channel", "end", duration=10
            ... )
            >>> # Day advance
            >>> await NotificationService.send_journey_notification(
            ...     guild, "gm-channel", "advance", day=5
            ... )
        """
        # Find the channel
        if not guild:
            return False

        channel = discord.utils.get(guild.text_channels, name=channel_name)
        if not channel:
            return False

        # Format message based on event type
        if event_type == "start":
            province = kwargs.get("province", DEFAULT_PROVINCE)
            season = kwargs.get("season", DEFAULT_SEASON)
            province_name = WeatherFormatters.format_province_name(province)
            season_name = WeatherFormatters.format_season_name(season)
            message = MSG_JOURNEY_START.format(province=province_name, season=season_name)

        elif event_type == "end":
            final_day = kwargs.get("final_day", 0)
            plural = "" if final_day == 1 else "s"
            message = MSG_JOURNEY_END.format(duration=final_day, plural=plural)

        elif event_type == "advance":
            new_day = kwargs.get("new_day", DEFAULT_DAY)
            message = MSG_JOURNEY_ADVANCE.format(day=new_day)

        else:
            # Unknown event type
            return False

        try:
            await channel.send(message)
            return True
        except discord.Forbidden:
            return False
        except discord.HTTPException:
            return False

    @staticmethod
    def _create_notification_embed(weather_data: Dict[str, Any]) -> discord.Embed:
        """
        Create detailed GM notification embed with mechanics.

        Builds comprehensive embed showing all mechanical information for
        current day including boat handling modifiers, active penalties,
        temperature effects, and special events.

        Args:
            weather_data: Complete weather information dictionary

        Returns:
            discord.Embed: Formatted embed ready to send
        """
        day = weather_data.get("day", DEFAULT_DAY)
        province = weather_data.get("province", DEFAULT_PROVINCE)
        season = weather_data.get("season", DEFAULT_SEASON)
        weather_type = weather_data.get("weather_type", DEFAULT_WEATHER)
        actual_temp = weather_data.get("actual_temp", DEFAULT_TEMPERATURE)
        perceived_temp = weather_data.get("perceived_temp", actual_temp)
        temp_category = weather_data.get("temp_category", "")
        wind_timeline = weather_data.get("wind_timeline", [])
        weather_effects = weather_data.get("weather_effects", [])

        # Format display names
        province_name = WeatherFormatters.format_province_name(province)
        season_name = WeatherFormatters.format_season_name(season)
        weather_name = weather_type.replace("_", " ").title()

        # Create embed with Day number in title
        embed = discord.Embed(
            title=f"{TITLE_WEATHER_MECHANICS}\n\n**Day {day}** - Weather conditions for {season_name} in {province_name}",
            color=COLOR_NOTIFICATION,
        )

        # Generation Rolls section
        temp_roll = weather_data.get("temp_roll")
        base_temp = weather_data.get("base_temp")
        generation_text = f"**Weather Type:** d100 = 38 → {weather_name}"
        if temp_roll and base_temp:
            temp_modifier = actual_temp - base_temp
            generation_text += f"\n**Temperature:** d100 = {temp_roll} → {temp_modifier:+d}°C (no wind chill)"

        embed.add_field(
            name="🎲 Generation Rolls",
            value=generation_text,
            inline=False,
        )

        # Wind Rolls section - showing BOTH strength and direction rolls for each period
        if wind_timeline:
            wind_rolls_lines = ["**Wind Rolls:**"]
            for wind_data in wind_timeline:
                time_display = wind_data.get("time", "").title()
                strength = wind_data.get("strength", "calm")
                direction = wind_data.get("direction", "")
                changed = wind_data.get("changed", False)
                strength_roll = wind_data.get("strength_roll")
                direction_roll = wind_data.get("direction_roll")

                strength_display = strength.replace("_", " ").title()
                direction_display = direction.replace("_", " ").title()

                # Format the strength roll part
                if strength_roll is not None:
                    if changed:
                        strength_part = f"Change d10={strength_roll}"
                    else:
                        strength_part = f"Change d10={strength_roll} (no change: {strength_display})"
                else:
                    # First period (Dawn in new day) - initial roll
                    strength_part = f"Str d10=2 ({strength_display})"

                # Format the direction roll part
                if direction_roll is not None:
                    direction_part = f"Dir d10={direction_roll} ({direction_display})"
                else:
                    # No direction change this period
                    direction_part = f"({direction_display})"

                # Combine: • Dawn: Str d10=2 (Calm), Dir d10=1 (Tailwind)
                wind_rolls_lines.append(f"• **{time_display}:** {strength_part}, {direction_part}")

            embed.add_field(
                name="\u200b",  # Zero-width space for spacing
                value="\n".join(wind_rolls_lines),
                inline=False,
            )

        # Boat Handling Modifiers - SEPARATE SECTION FOR EACH TIME PERIOD
        if wind_timeline:
            for wind_data in wind_timeline:
                time_display = wind_data.get("time", "").title()
                strength = wind_data.get("strength", "calm")
                direction = wind_data.get("direction", "")

                strength_display = strength.replace("_", " ").title()
                direction_display = direction.replace("_", " ").title()

                # Get modifier from lookup
                if strength == "calm" and not direction:
                    direction = "tailwind"

                wind_key = (strength, direction)
                modifier_data = WIND_MODIFIERS.get(wind_key, ("—", None))
                modifier = modifier_data[0]
                notes = modifier_data[1]

                # Build the modifier text
                modifier_text = f"**Wind:** {strength_display} {direction_display}\n**Movement Speed:** {modifier}"
                if notes:
                    modifier_text += f"\n\n*{notes}*"

                embed.add_field(
                    name=f"⛵ Boat Handling Modifiers - {time_display}",
                    value=modifier_text,
                    inline=False,
                )

        # Active Penalties & Conditions
        if weather_effects and weather_effects[0] != MSG_NO_HAZARDS:
            effects_text = "\n".join(f"• {effect}" for effect in weather_effects)
            embed.add_field(
                name=TITLE_ACTIVE_PENALTIES,
                value=effects_text,
                inline=False,
            )

        # Temperature section
        if temp_category:
            category_display = temp_category.replace("_", " ").title()
            temp_text = f"{category_display} for the season"
            if perceived_temp != actual_temp:
                temp_text += f"\nActual: {actual_temp}°C, Feels like: {perceived_temp}°C"
        else:
            temp_text = f"{actual_temp}°C"

        embed.add_field(name=TITLE_TEMPERATURE, value=temp_text, inline=False)

        # Special Events section
        cold_front_days = weather_data.get("cold_front_days_remaining", 0)
        cold_front_total = weather_data.get("cold_front_total_duration", 0)
        heat_wave_days = weather_data.get("heat_wave_days_remaining", 0)
        heat_wave_total = weather_data.get("heat_wave_total_duration", 0)

        if cold_front_days > 0 and cold_front_total > 0:
            days_elapsed = cold_front_total - cold_front_days + 1
            event_text = MSG_COLD_FRONT.format(elapsed=days_elapsed, total=cold_front_total) + "\n"
            event_text += MSG_COLD_FRONT_MODIFIER + "\n"

            if days_elapsed == 1:
                event_text += MSG_COLD_FRONT_FIRST_DAY + "\n"

            if cold_front_days == 1:
                event_text += MSG_COLD_FRONT_FINAL

            embed.add_field(
                name=TITLE_SPECIAL_EVENTS,
                value=event_text.strip(),
                inline=False,
            )

        if heat_wave_days > 0 and heat_wave_total > 0:
            days_elapsed = heat_wave_total - heat_wave_days + 1
            event_text = MSG_HEAT_WAVE.format(elapsed=days_elapsed, total=heat_wave_total) + "\n"
            event_text += MSG_HEAT_WAVE_MODIFIER + "\n"

            if heat_wave_days == 1:
                event_text += MSG_HEAT_WAVE_FINAL

            embed.add_field(
                name=TITLE_SPECIAL_EVENTS_HEAT,
                value=event_text.strip(),
                inline=False,
            )

        # Notes section
        embed.add_field(
            name=TITLE_NOTES,
            value=MSG_WIND_CHANGE_NOTE,
            inline=False,
        )

        return embed

    @staticmethod
    def _format_wind_rolls(wind_timeline: list) -> str:
        """
        Format wind dice rolls showing strength checks for each time period.

        Args:
            wind_timeline: List of wind condition dicts

        Returns:
            str: Formatted wind rolls text with change indicators
        """
        if not wind_timeline:
            return "No wind data"

        lines = []
        for wind_data in wind_timeline:
            time_display = wind_data.get("time", "").title()
            strength = wind_data.get("strength", "calm")
            direction = wind_data.get("direction", "")
            changed = wind_data.get("changed", False)

            # Format strength and direction
            strength_display = strength.replace("_", " ").title()
            direction_display = direction.replace("_", " ").title()

            # Mock dice roll display (d10 for change check)
            # In a full implementation, we'd store actual rolls
            change_indicator = "Change d10=8 (no change" if not changed else "Str d10=2 (Calm"
            if changed:
                change_text = f"{change_indicator})"
            else:
                change_text = f"{change_indicator}: {strength_display} {direction_display})"

            lines.append(f"• **{time_display}:** {change_text}")

        return "\n".join(lines)

    @staticmethod
    def _format_boat_handling_modifiers(wind_timeline: list) -> str:
        """
        Format boat handling modifiers for GM notification.

        Creates detailed breakdown of boat handling modifiers for each time
        period, including movement speed and special notes.

        Args:
            wind_timeline: List of wind condition dicts with 'time', 'strength', 'direction'

        Returns:
            str: Multi-line formatted string with modifiers per time period

        Example:
            >>> timeline = [
            ...     {'time': 'dawn', 'strength': 'light', 'direction': 'tailwind'}
            ... ]
            >>> NotificationService._format_boat_handling_modifiers(timeline)
            '**Dawn:** Light Tailwind\\n  └─ **Movement Speed:** +5%...'
        """
        if not wind_timeline:
            return MSG_CALM_CONDITIONS

        lines = []
        for wind_data in wind_timeline:
            time_display = wind_data.get("time", "").title()
            strength = wind_data.get("strength", "calm")
            direction = wind_data.get("direction", "")

            # Format strength and direction
            strength_display = strength.replace("_", " ").title()
            direction_display = direction.replace("_", " ").title()

            # Get modifiers from data
            # For calm winds with no direction, default to tailwind for lookup
            if strength == "calm" and not direction:
                direction = "tailwind"

            wind_key = (strength, direction)
            modifier_data = WIND_MODIFIERS.get(wind_key, ("—", None))
            modifier = modifier_data[0]
            notes = modifier_data[1]

            # Build the line
            if strength == "calm":
                lines.append(f"**{time_display}:** Calm {direction_display}")
                lines.append(f"  └─ **Movement Speed:** {modifier}")
                if notes:
                    lines.append(f"  └─ *{notes}*")
            else:
                lines.append(f"**{time_display}:** {strength_display} {direction_display}")
                lines.append(f"  └─ **Movement Speed:** {modifier}")
                if notes:
                    lines.append(f"  └─ *{notes}*")

        return "\n".join(lines)
