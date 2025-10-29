"""
Notifications Manager for Weather Commands

This module handles GM channel notifications for weather-related events.
Sends concise, mechanics-focused notifications to the GM channel without
the narrative embellishments shown to players.

Design Principles:
- GM-focused: Clear, mechanics-only information
- Non-intrusive: Simple text messages, not embeds
- Informative: All relevant mechanical details at a glance
"""

from typing import Optional, Dict, Any
import discord

from .formatters import WeatherFormatters


class NotificationManager:
    """
    Manages GM channel notifications for weather events.

    This class is responsible for:
    - Sending weather notifications to GM channel
    - Formatting notifications with key mechanical data
    - Providing quick reference for GMs during sessions
    """

    @staticmethod
    async def send_weather_notification(
        guild: discord.Guild, channel_name: str, weather_data: Dict[str, Any]
    ) -> bool:
        """
        Send a weather notification to the specified GM channel.

        Args:
            guild: Discord guild object
            channel_name: Name of the channel to send notification to
            weather_data: Dictionary containing weather information with keys:
                - day: Current day number
                - province: Province name
                - season: Season name
                - weather_type: Type of weather
                - temperature: Temperature value
                - wind_timeline: Dict with wind conditions
                - weather_effects: List of weather effect strings

        Returns:
            bool: True if notification was sent successfully, False otherwise
        """
        # Find the channel
        channel = discord.utils.get(guild.text_channels, name=channel_name)
        if not channel:
            return False

        # Format the notification message
        message = NotificationManager._format_notification(weather_data)

        try:
            await channel.send(message)
            return True
        except discord.Forbidden:
            # Bot doesn't have permission to send messages
            return False
        except discord.HTTPException:
            # Other Discord API error
            return False

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
            return "Calm all day (+0)"

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

        Args:
            guild: Discord guild object
            channel_name: Name of the channel to send notification to
            stage_number: Current stage number
            total_stages: Total number of stages in journey
            stage_duration: Duration of this stage in days

        Returns:
            bool: True if notification was sent successfully, False otherwise
        """
        # Find the channel
        channel = discord.utils.get(guild.text_channels, name=channel_name)
        if not channel:
            return False

        message = (
            f"**🚢 Stage {stage_number}/{total_stages} Complete**\n"
            f"Duration: {stage_duration} day{'s' if stage_duration != 1 else ''}"
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

        Args:
            guild: Discord guild object
            channel_name: Name of the channel to send notification to
            notification_type: Type of notification ('start', 'end', 'advance')
            **kwargs: Additional data depending on notification type

        Returns:
            bool: True if notification was sent successfully, False otherwise
        """
        # Find the channel
        channel = discord.utils.get(guild.text_channels, name=channel_name)
        if not channel:
            return False

        # Format message based on type
        if notification_type == "start":
            province = kwargs.get("province", "Unknown")
            season = kwargs.get("season", "spring")
            province_name = WeatherFormatters.format_province_name(province)
            season_name = WeatherFormatters.format_season_name(season)
            message = (
                f"**🗺️ Journey Started**\n"
                f"Location: {province_name}\n"
                f"Season: {season_name}"
            )
        elif notification_type == "end":
            final_day = kwargs.get("final_day", 0)
            message = (
                f"**🏁 Journey Ended**\n"
                f"Total Duration: {final_day} day{'s' if final_day != 1 else ''}"
            )
        elif notification_type == "advance":
            new_day = kwargs.get("new_day", 1)
            message = f"**📅 Advanced to Day {new_day}**"
        else:
            return False

        try:
            await channel.send(message)
            return True
        except (discord.Forbidden, discord.HTTPException):
            return False
