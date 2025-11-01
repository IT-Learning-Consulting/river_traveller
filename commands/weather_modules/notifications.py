"""
Notifications Manager for Weather Commands

This module handles GM channel notifications for weather-related events.
Sends concise, mechanics-focused notifications to the GM channel without
the narrative embellishments shown to players.

Key Responsibilities:
    - Send weather mechanics notifications to GM channels
    - Format boat handling modifiers and penalties
    - Notify about stage progression and journey events
    - Provide quick reference information for GMs
    - Handle special weather events (cold fronts, heat waves)

Design Principles:
    - GM-focused: Clear, mechanics-only information
    - Non-intrusive: Embeds for weather, simple text for other events
    - Informative: All relevant mechanical details at a glance
    - Error-resilient: Gracefully handles missing channels and permissions

Notification Types:
    - Weather notifications: Detailed embeds with modifiers and effects
    - Stage notifications: Simple text messages for stage completion
    - Journey notifications: Start/end/advance announcements

Usage Example:
    >>> await NotificationManager.send_weather_notification(guild, "gm-channel", weather_data)
    >>> await NotificationManager.send_journey_notification(guild, "gm-channel", "start", season="winter", province="reikland")
"""

from typing import Any, Dict, Optional

import discord

from .formatters import WeatherFormatters

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
MSG_CALM_ALL_DAY = "Calm all day (+0)"
MSG_NO_HAZARDS = "No weather-related hazards"

# Journey notification messages
MSG_JOURNEY_START = "**🗺️ Journey Started**\nLocation: {province}\nSeason: {season}"
MSG_JOURNEY_END = "**🏁 Journey Ended**\nTotal Duration: {duration} day{plural}"
MSG_JOURNEY_ADVANCE = "**📅 Advanced to Day {day}**"
MSG_STAGE_COMPLETE = (
    "**🚢 Stage {current}/{total} Complete**\nDuration: {duration} day{plural}"
)

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

# Emoji
EMOJI_CALENDAR = "📅"
EMOJI_MAP = "🗺️"
EMOJI_FINISH = "🏁"
EMOJI_SHIP = "🚢"


class NotificationManager:
    """
    Manages GM channel notifications for weather and journey events.

    This class provides static methods for sending various types of notifications
    to GM channels. All notifications are mechanics-focused to provide GMs with
    quick reference information during gameplay sessions.

    Responsibilities:
        - Send detailed weather mechanics embeds to GM channels
        - Format boat handling modifiers and movement penalties
        - Notify about stage progression and completion
        - Announce journey start, end, and day advancement
        - Display special weather events (cold fronts, heat waves)
        - Handle Discord API errors gracefully

    Design Pattern:
        All methods are static as this class maintains no state. It serves
        purely as a utility namespace for notification operations.

    Error Handling:
        - Returns False if channel not found
        - Returns False on Discord permission errors
        - Returns False on Discord API errors
        - Never raises exceptions to calling code

    Example:
        >>> # Send weather notification
        >>> success = await NotificationManager.send_weather_notification(
        ...     guild, "gm-channel", weather_data
        ... )
        >>> # Send journey start notification
        >>> await NotificationManager.send_journey_notification(
        ...     guild, "gm-channel", "start", season="winter", province="reikland"
        ... )
    """

    @staticmethod
    async def send_weather_notification(
        guild: discord.Guild, channel_name: str, weather_data: Dict[str, Any]
    ) -> bool:
        """
        Send a weather notification embed to the specified GM channel.

        Creates a detailed mechanics-focused embed with boat handling modifiers,
        active penalties, temperature effects, and special events. The embed
        provides GMs with all mechanical information needed for the current day.

        Args:
            guild: Discord guild object to search for channels
            channel_name: Name of the GM channel (e.g., "boat-travelling-notifications")
            weather_data: Dictionary containing comprehensive weather information with keys:
                - day: Current day number
                - province: Province name (e.g., "reikland")
                - season: Season name (e.g., "winter")
                - weather_type: Type of weather (e.g., "rain", "snow")
                - actual_temp: Actual temperature value
                - perceived_temp: Temperature after wind chill
                - temp_category: Temperature category for the season
                - wind_timeline: List of wind conditions by time period
                - weather_effects: List of active effect strings
                - cold_front_days_remaining: Days left in cold front (optional)
                - heat_wave_days_remaining: Days left in heat wave (optional)

        Returns:
            bool: True if notification sent successfully, False otherwise
                  (channel not found, permission denied, or API error)

        Example:
            >>> weather_data = {
            ...     "day": 5,
            ...     "province": "reikland",
            ...     "season": "winter",
            ...     "weather_type": "snow",
            ...     "actual_temp": -2,
            ...     "wind_timeline": [...]
            ... }
            >>> success = await NotificationManager.send_weather_notification(
            ...     guild, "gm-channel", weather_data
            ... )
        """
        # Find the channel
        channel = discord.utils.get(guild.text_channels, name=channel_name)
        if not channel:
            return False

        # Create the embed
        embed = NotificationManager._create_notification_embed(weather_data)

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
    def _create_notification_embed(weather_data: Dict[str, Any]) -> discord.Embed:
        """
        Create a detailed GM notification embed with full mechanics.

        Builds a comprehensive embed showing all mechanical information GMs
        need for the current day including boat handling modifiers, active
        penalties, temperature effects, and special events.

        Args:
            weather_data: Dictionary containing complete weather information
                (see send_weather_notification for full structure)

        Returns:
            discord.Embed: Formatted embed ready to send to GM channel

        Note:
            This method imports WIND_MODIFIERS locally to avoid circular imports.
        """
        from db.weather_data import WIND_MODIFIERS

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

        # Create embed
        embed = discord.Embed(
            title=TITLE_WEATHER_MECHANICS,
            description=f"Weather conditions for {season_name} in {province_name}",
            color=COLOR_NOTIFICATION,
        )

        # Boat Handling Modifiers section
        if wind_timeline:
            boat_handling_text = NotificationManager._format_boat_handling_modifiers(
                wind_timeline
            )
            embed.add_field(
                name=TITLE_BOAT_HANDLING,
                value=boat_handling_text,
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
                temp_text += (
                    f"\nActual: {actual_temp}°C, Feels like: {perceived_temp}°C"
                )
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
            event_text = (
                MSG_COLD_FRONT.format(elapsed=days_elapsed, total=cold_front_total)
                + "\n"
            )
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
            event_text = (
                MSG_HEAT_WAVE.format(elapsed=days_elapsed, total=heat_wave_total) + "\n"
            )
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
    def _format_boat_handling_modifiers(wind_timeline: list) -> str:
        """
        Format detailed boat handling modifiers for GM notification.

        Creates a detailed breakdown of boat handling modifiers for each time
        period of the day. Includes movement speed penalties/bonuses and
        any special notes from the WIND_MODIFIERS table.

        Args:
            wind_timeline: List of wind condition dictionaries for each time period.
                Each dict contains 'time', 'strength', and 'direction' keys.

        Returns:
            str: Multi-line formatted string showing modifiers for each time period

        Example:
            >>> timeline = [
            ...     {'time': 'dawn', 'strength': 'light', 'direction': 'north'},
            ...     {'time': 'midday', 'strength': 'bracing', 'direction': 'northeast'}
            ... ]
            >>> NotificationManager._format_boat_handling_modifiers(timeline)
            '**Dawn:** Light North\\n  └─ **Movement Speed:** +10%...'

        Note:
            Imports WIND_MODIFIERS locally to avoid circular imports.
        """
        from db.weather_data import WIND_MODIFIERS

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

            # Get the actual modifiers from the data
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
                lines.append(
                    f"**{time_display}:** {strength_display} {direction_display}"
                )
                lines.append(f"  └─ **Movement Speed:** {modifier}")
                if notes:
                    lines.append(f"  └─ *{notes}*")

        return "\n".join(lines)

    @staticmethod
    def _format_notification(weather_data: Dict[str, Any]) -> str:
        """
        Format weather data into a GM notification message.

        Args:
            weather_data: Dictionary containing weather information

        Returns:
            str: Formatted notification message
        """
        day = weather_data.get("day", 1)
        province = weather_data.get("province", "Unknown")
        season = weather_data.get("season", "spring")
        weather_type = weather_data.get("weather_type", "fair")
        temperature = weather_data.get("temperature", 15)
        wind_timeline = weather_data.get("wind_timeline", {})
        weather_effects = weather_data.get("weather_effects", [])

        # Format display names
        province_name = WeatherFormatters.format_province_name(province)
        season_name = WeatherFormatters.format_season_name(season)
        weather_name = weather_type.replace("_", " ").title()

        # Get emojis
        weather_emoji = WeatherFormatters.get_weather_emoji(weather_type)
        temp_emoji = WeatherFormatters.get_temperature_emoji(temperature)

        # Build notification parts
        parts = [
            f"**📅 Day {day} Weather Update**",
            f"**Location:** {province_name} | {season_name}",
            f"**Condition:** {weather_emoji} {weather_name}",
            f"**Temperature:** {temp_emoji} {temperature}°C",
        ]

        # Add wind summary
        wind_summary = NotificationManager._format_wind_summary(wind_timeline)
        if wind_summary:
            parts.append(f"**Wind:** {wind_summary}")

        # Add effects if any
        if weather_effects:
            effects_text = "\n".join(f"  • {effect}" for effect in weather_effects)
            parts.append(f"**Effects:**\n{effects_text}")

        return "\n".join(parts)

    @staticmethod
    def _format_wind_summary(wind_timeline: Dict[str, Dict[str, Any]]) -> str:
        """
        Format wind conditions into a concise summary for notifications.

        Args:
            wind_timeline: Dictionary with wind data for each time of day

        Returns:
            str: Concise wind summary (e.g., "Light N (+10) → Bracing NE (+0)")
        """
        if not wind_timeline:
            return "Calm all day (+0)"

        # Get unique wind conditions (strength + direction)
        conditions = []
        seen = set()

        time_order = ["dawn", "morning", "afternoon", "evening", "night"]
        for time_of_day in time_order:
            if time_of_day not in wind_timeline:
                continue

            wind_data = wind_timeline[time_of_day]
            strength = wind_data.get("strength", "calm")
            direction = wind_data.get("direction", "")
            modifier = wind_data.get("modifier", "+0")

            # Create a unique key for this condition
            if strength.lower() == "calm":
                condition_key = "calm"
                condition_str = "Calm (+0)"
            else:
                condition_key = f"{strength}_{direction}"
                strength_display = strength.replace("_", " ").title()

                # Format modifier concisely
                modifier_display = WeatherFormatters.format_modifier_for_display(
                    modifier
                )
                condition_str = f"{strength_display} {direction} ({modifier_display})"

            # Only add if we haven't seen this condition yet
            if condition_key not in seen:
                conditions.append(condition_str)
                seen.add(condition_key)

        if not conditions:
            return MSG_CALM_ALL_DAY

        # Join with arrow if multiple conditions
        if len(conditions) == 1:
            return conditions[0]
        else:
            return " → ".join(conditions)

    @staticmethod
    async def send_stage_notification(
        guild: discord.Guild,
        channel_name: str,
        stage_number: int,
        total_stages: int,
        stage_duration: int,
    ) -> bool:
        """
        Send a stage advancement notification to the GM channel.

        Sends a simple text message announcing the completion of a stage
        and the duration covered. Used for multi-day stage progression.

        Args:
            guild: Discord guild object to search for channels
            channel_name: Name of the GM channel (e.g., "boat-travelling-notifications")
            stage_number: Current completed stage number (1-based)
            total_stages: Total number of stages in the journey
            stage_duration: Duration of this stage in days

        Returns:
            bool: True if notification sent successfully, False otherwise
                  (channel not found, permission denied, or API error)

        Example:
            >>> await NotificationManager.send_stage_notification(
            ...     guild, "gm-channel", 2, 5, 3
            ... )
            # Sends: "🚢 Stage 2/5 Complete\nDuration: 3 days"
        """
        # Find the channel
        channel = discord.utils.get(guild.text_channels, name=channel_name)
        if not channel:
            return False

        plural = "s" if stage_duration != 1 else ""
        message = MSG_STAGE_COMPLETE.format(
            current=stage_number,
            total=total_stages,
            duration=stage_duration,
            plural=plural,
        )

        try:
            await channel.send(message)
            return True
        except (discord.Forbidden, discord.HTTPException):
            return False

    @staticmethod
    async def send_journey_notification(
        guild: discord.Guild, channel_name: str, notification_type: str, **kwargs
    ) -> bool:
        """
        Send a journey-related notification to the GM channel.

        Sends simple text messages announcing journey lifecycle events like
        start, end, or day advancement. The message format depends on the
        notification type.

        Args:
            guild: Discord guild object to search for channels
            channel_name: Name of the GM channel (e.g., "boat-travelling-notifications")
            notification_type: Type of notification. Valid values:
                - "start": Journey started (requires season, province kwargs)
                - "end": Journey ended (requires final_day kwarg)
                - "advance": Advanced to new day (requires new_day kwarg)
            **kwargs: Additional data depending on notification type:
                For "start": season (str), province (str)
                For "end": final_day (int)
                For "advance": new_day (int)

        Returns:
            bool: True if notification sent successfully, False if:
                - Channel not found
                - Unknown notification_type
                - Permission denied
                - Discord API error

        Example:
            >>> # Journey start
            >>> await NotificationManager.send_journey_notification(
            ...     guild, "gm-channel", "start",
            ...     season="winter", province="reikland"
            ... )
            >>> # Journey end
            >>> await NotificationManager.send_journey_notification(
            ...     guild, "gm-channel", "end", final_day=15
            ... )
        """
        # Find the channel
        channel = discord.utils.get(guild.text_channels, name=channel_name)
        if not channel:
            return False

        # Format message based on type
        if notification_type == "start":
            province = kwargs.get("province", DEFAULT_PROVINCE)
            season = kwargs.get("season", DEFAULT_SEASON)
            province_name = WeatherFormatters.format_province_name(province)
            season_name = WeatherFormatters.format_season_name(season)
            message = MSG_JOURNEY_START.format(
                province=province_name, season=season_name
            )
        elif notification_type == "end":
            final_day = kwargs.get("final_day", 0)
            plural = "s" if final_day != 1 else ""
            message = MSG_JOURNEY_END.format(duration=final_day, plural=plural)
        elif notification_type == "advance":
            new_day = kwargs.get("new_day", 1)
            message = MSG_JOURNEY_ADVANCE.format(day=new_day)
        else:
            return False

        try:
            await channel.send(message)
            return True
        except (discord.Forbidden, discord.HTTPException):
            return False
