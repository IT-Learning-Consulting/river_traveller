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
                - actual_temp: Actual temperature value
                - perceived_temp: Perceived temperature with wind chill
                - temp_category: Temperature category
                - wind_timeline: List with wind conditions
                - weather_effects: List of weather effect strings

        Returns:
            bool: True if notification was sent successfully, False otherwise
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

        Args:
            weather_data: Dictionary containing weather information

        Returns:
            discord.Embed: Formatted embed for GM channel
        """
        from db.weather_data import WIND_MODIFIERS

        day = weather_data.get("day", 1)
        province = weather_data.get("province", "Unknown")
        season = weather_data.get("season", "spring")
        weather_type = weather_data.get("weather_type", "fair")
        actual_temp = weather_data.get("actual_temp", 15)
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
            title="⚠️ Active Weather Mechanics",
            description=f"Weather conditions for {season_name} in {province_name}",
            color=discord.Color.gold(),
        )

        # Boat Handling Modifiers section
        if wind_timeline:
            boat_handling_text = NotificationManager._format_boat_handling_modifiers(
                wind_timeline
            )
            embed.add_field(
                name="🚢 Boat Handling Modifiers",
                value=boat_handling_text,
                inline=False,
            )

        # Active Penalties & Conditions
        if weather_effects and weather_effects[0] != "No weather-related hazards":
            effects_text = "\n".join(f"• {effect}" for effect in weather_effects)
            embed.add_field(
                name="🎯 Active Penalties & Conditions",
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

        embed.add_field(name="🌡️ Temperature", value=temp_text, inline=False)

        # Special Events section
        cold_front_days = weather_data.get("cold_front_days_remaining", 0)
        cold_front_total = weather_data.get("cold_front_total_duration", 0)
        heat_wave_days = weather_data.get("heat_wave_days_remaining", 0)
        heat_wave_total = weather_data.get("heat_wave_total_duration", 0)

        if cold_front_days > 0 and cold_front_total > 0:
            days_elapsed = cold_front_total - cold_front_days + 1
            event_text = f"❄️ **Cold Front: Day {days_elapsed} of {cold_front_total}**\n"
            event_text += f"• Temperature modifier: -10°C\n"

            if days_elapsed == 1:
                event_text += "• Sky filled with flocks of emigrating birds\n"

            if cold_front_days == 1:
                event_text += "• **(Final Day)**"

            embed.add_field(
                name="🌨️ Special Weather Events",
                value=event_text.strip(),
                inline=False,
            )

        if heat_wave_days > 0 and heat_wave_total > 0:
            days_elapsed = heat_wave_total - heat_wave_days + 1
            event_text = f"🔥 **Heat Wave: Day {days_elapsed} of {heat_wave_total}**\n"
            event_text += f"• Temperature modifier: +10°C\n"

            if heat_wave_days == 1:
                event_text += "• **(Final Day)**"

            embed.add_field(
                name="☀️ Special Weather Events",
                value=event_text.strip(),
                inline=False,
            )

        # Notes section
        embed.add_field(
            name="💡 Notes",
            value="• Wind may change at midday, dusk, or midnight (10% chance each check)",
            inline=False,
        )

        return embed

    @staticmethod
    def _format_boat_handling_modifiers(wind_timeline) -> str:
        """
        Format detailed boat handling modifiers for GM notification.

        Args:
            wind_timeline: List of wind conditions for each time period

        Returns:
            str: Formatted boat handling modifiers with all details
        """
        from db.weather_data import WIND_MODIFIERS

        if not wind_timeline:
            return "Calm conditions: -10 penalty, 25% speed"

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
