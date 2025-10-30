"""
Display Manager for Weather Commands

This module handles all Discord embed creation and user-facing displays
for weather data. It uses the WeatherFormatters for consistent formatting.

Design Principles:
- Separation of concerns: Display logic isolated from business logic
- Reusability: Methods can be used by both slash and prefix commands
- Consistency: All embeds follow the same styling conventions
"""

from typing import Optional, Dict, Any, List
import discord
from datetime import datetime, timezone

from .formatters import WeatherFormatters
from utils.weather_mechanics import get_weather_effects
from db.weather_data import WEATHER_EFFECTS


class WeatherDisplayManager:
    """
    Manages the creation and sending of weather-related Discord embeds.

    This class is responsible for:
    - Creating daily weather embeds with all relevant information
    - Formatting wind conditions for display
    - Formatting weather effects and conditions
    - Handling both slash and prefix command responses
    - Displaying error and info messages
    """

    COLOR_DEFAULT = 0x3498DB  # Blue
    COLOR_ERROR = 0xE74C3C  # Red
    COLOR_INFO = 0x95A5A6  # Gray

    @staticmethod
    async def show_daily_weather(
        context,
        weather_data: Dict[str, Any],
        is_slash: bool = False,
        is_historical: bool = False,
    ) -> None:
        """
        Display daily weather information to the user.

        Args:
            context: Discord context (can be ctx for prefix or interaction for slash)
            weather_data: Dictionary containing weather information with keys:
                - day: Current day number
                - province: Province name
                - season: Season name
                - weather_type: Type of weather (e.g., 'fair', 'rain')
                - weather_effects: List of weather effect strings
                - temperature: Temperature value (integer)
                - wind_chill: Wind chill adjusted temperature (integer)
                - wind_chill_note: Description of wind chill effect (string)
                - wind_timeline: Dict with wind conditions for different times of day
            is_slash: Whether this is a slash command response
            is_historical: Whether this is historical weather (past day)
        """
        embed = WeatherDisplayManager._create_daily_weather_embed(
            weather_data, is_historical
        )
        await WeatherDisplayManager._send_embed(context, embed, is_slash)

    @staticmethod
    def _create_daily_weather_embed(
        weather_data: Dict[str, Any], is_historical: bool = False
    ) -> discord.Embed:
        """
        Create a Discord embed for daily weather display.

        Args:
            weather_data: Dictionary containing weather information
            is_historical: Whether this is historical weather

        Returns:
            discord.Embed: Configured embed ready to send
        """
        day = weather_data.get("day", 1)
        province = weather_data.get("province", "Unknown")
        season = weather_data.get("season", "spring")
        weather_type = weather_data.get("weather_type", "fair")
        weather_effects = weather_data.get("weather_effects", [])
        temperature = weather_data.get(
            "actual_temp", weather_data.get("temperature", 15)
        )
        wind_timeline = weather_data.get("wind_timeline", {})

        # Format display names
        province_name = WeatherFormatters.format_province_name(province)
        season_name = WeatherFormatters.format_season_name(season)

        # Get emojis
        weather_emoji = WeatherFormatters.get_weather_emoji(weather_type)
        temp_emoji = WeatherFormatters.get_temperature_emoji(temperature)

        # Create title
        title_prefix = "📜 Historical Weather" if is_historical else "🌤️ Daily Weather"
        title = f"{title_prefix} - Day {day}"

        # Create embed
        embed = discord.Embed(
            title=title,
            description=f"**{province_name}** | **{season_name}**",
            color=WeatherDisplayManager.COLOR_DEFAULT,
            timestamp=datetime.now(timezone.utc),
        )

        # Add weather condition
        weather_condition_text = WeatherDisplayManager._format_weather_condition(
            weather_type, weather_effects
        )
        embed.add_field(
            name=f"{weather_emoji} Weather Condition",
            value=weather_condition_text,
            inline=False,
        )

        # Add temperature
        temp_text = WeatherDisplayManager._format_temperature(weather_data)
        embed.add_field(name=f"{temp_emoji} Temperature", value=temp_text, inline=True)

        # Add wind conditions
        wind_text = WeatherDisplayManager._format_wind_conditions(wind_timeline)
        embed.add_field(name="💨 Wind Conditions", value=wind_text, inline=True)

        # Add weather effects if any
        if weather_effects:
            effects_text = WeatherDisplayManager._format_weather_effects(
                weather_effects
            )
            embed.add_field(name="⚠️ Weather Effects", value=effects_text, inline=False)

        # Add footer
        embed.set_footer(text="Warhammer Fantasy Roleplay 4e | River Travel")

        return embed

    @staticmethod
    def _format_wind_conditions(wind_timeline) -> str:
        """
        Format wind conditions for display in an embed field.

        Args:
            wind_timeline: List of dicts with wind data for each time period
                Format: [
                    {'time': 'Dawn', 'strength': str, 'direction': str, 'changed': bool},
                    {'time': 'Midday', ...}, etc.
                ]

        Returns:
            str: Formatted wind conditions text
        """
        if not wind_timeline:
            return "🌊 Calm throughout the day"

        # Check if all periods have same wind
        all_same = all(
            w["strength"] == wind_timeline[0]["strength"]
            and w["direction"] == wind_timeline[0]["direction"]
            for w in wind_timeline
        )

        if all_same and wind_timeline[0]["strength"] == "calm":
            return "🌊 Calm throughout the day"

        lines = []
        for wind_data in wind_timeline:
            time_display = wind_data.get("time", "").title()
            strength = wind_data.get("strength", "calm")
            direction = wind_data.get("direction", "")

            # Format strength and direction for display
            strength_display = strength.replace("_", " ").title()
            direction_display = direction.replace("_", " ").title()

            # Create line
            if strength.lower() == "calm":
                lines.append(f"**{time_display}:** Calm")
            else:
                lines.append(
                    f"**{time_display}:** {strength_display} {direction_display}"
                )

        return "\n".join(lines)

    @staticmethod
    def _format_weather_condition(weather_type: str, weather_effects: List[str]) -> str:
        """
        Format the weather condition description.

        Args:
            weather_type: Type of weather (e.g., 'fair', 'rain')
            weather_effects: List of weather effect strings

        Returns:
            str: Formatted weather condition text
        """
        # Capitalize weather type for display
        weather_display = weather_type.replace("_", " ").title()

        # Get base description from WEATHER_EFFECTS if available
        base_description = ""
        if weather_type in WEATHER_EFFECTS:
            effect_data = WEATHER_EFFECTS[weather_type]
            if isinstance(effect_data, dict) and "description" in effect_data:
                base_description = effect_data["description"]
            elif isinstance(effect_data, str):
                base_description = effect_data

        if base_description:
            return f"**{weather_display}**\n{base_description}"
        else:
            return f"**{weather_display}**"

    @staticmethod
    def _format_weather_effects(effects: List[str]) -> str:
        """
        Format weather effects for display.

        Args:
            effects: List of weather effect strings

        Returns:
            str: Formatted effects text with bullet points
        """
        if not effects:
            return "*No special effects*"

        # Add bullet points to each effect
        formatted_effects = [f"• {effect}" for effect in effects]
        return "\n".join(formatted_effects)

    @staticmethod
    def _format_temperature(weather_data: Dict[str, Any]) -> str:
        """
        Format temperature information including wind chill.

        Args:
            weather_data: Dictionary containing temperature data

        Returns:
            str: Formatted temperature text
        """
        # Get actual and perceived temperatures
        actual_temp = weather_data.get(
            "actual_temp", weather_data.get("temperature", 15)
        )
        perceived_temp = weather_data.get("perceived_temp", actual_temp)
        temp_description = weather_data.get("temp_description", "")
        temp_category = weather_data.get("temp_category", "")

        # Base temperature with category
        if temp_category:
            category_display = temp_category.replace("_", " ").title()
            temp_text = f"**{actual_temp}°C** ({category_display} for the season)"
        else:
            temp_text = f"**{actual_temp}°C**"

        # Add description if available
        if temp_description:
            temp_text += f"\n*{temp_description}*"

        # Add wind chill if different from base temperature
        if perceived_temp != actual_temp:
            temp_text += f"\n**Feels like: {perceived_temp}°C** (feels {abs(perceived_temp - actual_temp)}°C {'colder' if perceived_temp < actual_temp else 'warmer'} due to {'Strong' if abs(perceived_temp - actual_temp) >= 10 else ''} wind)"

        return temp_text

    @staticmethod
    async def _send_embed(
        context, embed: discord.Embed, is_slash: bool = False
    ) -> None:
        """
        Send an embed to Discord, handling both slash and prefix commands.

        Args:
            context: Discord context (ctx or interaction)
            embed: The embed to send
            is_slash: Whether this is a slash command
        """
        # Auto-detect if is_slash parameter is incorrect by checking context type
        if hasattr(context, "response"):
            # This is an Interaction (slash command)
            if context.response.is_done():
                await context.followup.send(embed=embed)
            else:
                await context.response.send_message(embed=embed)
        else:
            # This is a Context (prefix command)
            await context.send(embed=embed)

    @staticmethod
    async def send_error(context, message: str, is_slash: bool = False) -> None:
        """
        Send an error message to the user.

        Args:
            context: Discord context (ctx or interaction)
            message: Error message to display
            is_slash: Whether this is a slash command
        """
        embed = discord.Embed(
            title="❌ Error",
            description=message,
            color=WeatherDisplayManager.COLOR_ERROR,
        )
        await WeatherDisplayManager._send_embed(context, embed, is_slash)

    @staticmethod
    async def send_info(
        context, message: str, title: str = "ℹ️ Information", is_slash: bool = False
    ) -> None:
        """
        Send an informational message to the user.

        Args:
            context: Discord context (ctx or interaction)
            message: Information message to display
            title: Title for the embed
            is_slash: Whether this is a slash command
        """
        embed = discord.Embed(
            title=title, description=message, color=WeatherDisplayManager.COLOR_INFO
        )
        await WeatherDisplayManager._send_embed(context, embed, is_slash)
