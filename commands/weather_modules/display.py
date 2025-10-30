"""
Display Manager for Weather Commands

Handles all Discord embed creation and user-facing displays for weather data.
Provides a clean separation between business logic and presentation layer,
using WeatherFormatters for consistent formatting across the application.

Key Features:
    - Daily weather embeds with comprehensive information
    - Wind condition timelines (Dawn, Midday, Dusk, Midnight)
    - Temperature display with wind chill effects
    - Weather effects and special event notifications
    - Historical weather viewing
    - Error and informational messages

Design Principles:
    - Separation of concerns: Display logic isolated from business logic
    - Reusability: Methods can be used by both slash and prefix commands
    - Consistency: All embeds follow the same styling conventions
    - Defensive programming: Handles missing data gracefully

Usage Example:
    >>> manager = WeatherDisplayManager()
    >>> await manager.show_daily_weather(ctx, weather_data, is_slash=True)
"""

from typing import Any, Dict, List, Optional, Union
import discord
from datetime import datetime, timezone
from discord.ext import commands

from .formatters import WeatherFormatters
from utils.weather_mechanics import get_weather_effects
from db.weather_data import WEATHER_EFFECTS


# Display color scheme
COLOR_DEFAULT = 0x3498DB  # Blue - Default weather display
COLOR_ERROR = 0xE74C3C  # Red - Error messages
COLOR_INFO = 0x95A5A6  # Gray - Informational messages

# Display emojis
EMOJI_HISTORICAL = "📜"
EMOJI_DAILY = "🌤️"
EMOJI_WIND = "💨"
EMOJI_EFFECTS = "⚠️"
EMOJI_ERROR = "❌"
EMOJI_INFO = "ℹ️"
EMOJI_CALM_WIND = "🌊"

# Temperature difference thresholds
TEMP_DIFF_STRONG_WIND = 10  # Difference considered "strong" wind effect

# Default display values
DEFAULT_PROVINCE = "Unknown"
DEFAULT_SEASON = "spring"
DEFAULT_WEATHER = "fair"
DEFAULT_TEMPERATURE = 15
DEFAULT_DAY = 1

# Footer text
FOOTER_TEXT = "Warhammer Fantasy Roleplay 4e | River Travel"


class WeatherDisplayManager:
    """
    Manages the creation and sending of weather-related Discord embeds.

    This class provides static methods for creating and sending weather displays
    to Discord. All methods are static as this class maintains no state and
    serves purely as a utility for display formatting.

    Responsibilities:
        - Creating daily weather embeds with all relevant information
        - Formatting wind conditions for display across day periods
        - Formatting weather effects and conditions
        - Handling both slash (/) and prefix (!) command responses
        - Displaying error and informational messages
        - Managing color schemes and emoji consistency

    Class Attributes:
        COLOR_DEFAULT: Blue color for normal weather displays
        COLOR_ERROR: Red color for error messages
        COLOR_INFO: Gray color for informational messages

    Example:
        >>> # Display daily weather
        >>> await WeatherDisplayManager.show_daily_weather(ctx, data, is_slash=True)
        >>> # Show error message
        >>> await WeatherDisplayManager.send_error(ctx, "Journey not found")
    """

    # Color scheme constants (kept for backward compatibility and clarity)
    COLOR_DEFAULT = COLOR_DEFAULT
    COLOR_ERROR = COLOR_ERROR
    COLOR_INFO = COLOR_INFO

    @staticmethod
    async def show_daily_weather(
        context: Union[discord.Interaction, commands.Context],
        weather_data: Dict[str, Any],
        is_slash: bool = False,
        is_historical: bool = False,
    ) -> None:
        """
        Display daily weather information in a formatted embed.

        Creates a comprehensive weather display showing current conditions,
        temperature, wind patterns, and any special effects for the day.
        Automatically handles both slash and prefix command contexts.

        Args:
            context: The Discord context or interaction to respond to
            weather_data: Dictionary containing weather information with keys:
                - province: Location name
                - season: Current season
                - day: Journey day number
                - weather_type: Current weather condition
                - temperature: Current temperature in degrees
                - wind_direction: Current wind direction
                - daily_wind_changes: List of wind changes throughout day
                - daily_weather_effects: List of special weather effects
            is_slash: Whether this is a slash command response (affects response method)
            is_historical: Whether this is historical weather display (changes embed title)

        Returns:
            None: Sends embed directly to Discord channel

        Example:
            >>> data = {
            ...     "province": "Reikland",
            ...     "season": "winter",
            ...     "day": 5,
            ...     "weather_type": "snow",
            ...     "temperature": -2
            ... }
            >>> await WeatherDisplayManager.show_daily_weather(ctx, data)
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

        Builds a rich embed containing weather information formatted for Discord.
        Includes title, color, fields for weather conditions, wind, effects,
        and temperature. Uses default values for missing data.

        Args:
            weather_data: Dictionary containing weather information with keys:
                - day: Journey day number (default: 1)
                - province: Location name (default: "Unknown")
                - season: Current season (default: "spring")
                - weather_type: Weather condition (default: "fair")
                - temperature: Current temperature (default: 15)
                - wind_timeline: Dict of wind conditions by time period
                - daily_weather_effects: List of effect strings
            is_historical: If True, shows "Historical Weather" title (default: False)

        Returns:
            discord.Embed: Configured embed ready to send to Discord

        Example:
            >>> data = {"day": 3, "province": "Reikland", "weather_type": "rain"}
            >>> embed = WeatherDisplayManager._create_daily_weather_embed(data)
            >>> # embed is now ready to send
        """
        day = weather_data.get("day", DEFAULT_DAY)
        province = weather_data.get("province", DEFAULT_PROVINCE)
        season = weather_data.get("season", DEFAULT_SEASON)
        weather_type = weather_data.get("weather_type", DEFAULT_WEATHER)
        weather_effects = weather_data.get("weather_effects", [])
        temperature = weather_data.get(
            "actual_temp", weather_data.get("temperature", DEFAULT_TEMPERATURE)
        )
        wind_timeline = weather_data.get("wind_timeline", {})

        # Format display names
        province_name = WeatherFormatters.format_province_name(province)
        season_name = WeatherFormatters.format_season_name(season)

        # Get emojis
        weather_emoji = WeatherFormatters.get_weather_emoji(weather_type)
        temp_emoji = WeatherFormatters.get_temperature_emoji(temperature)

        # Create title with appropriate emoji
        title_prefix = (
            f"{EMOJI_HISTORICAL} Historical Weather"
            if is_historical
            else f"{EMOJI_DAILY} Daily Weather"
        )
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
        embed.add_field(
            name=f"{EMOJI_WIND} Wind Conditions", value=wind_text, inline=True
        )

        # Add weather effects if any
        if weather_effects:
            effects_text = WeatherDisplayManager._format_weather_effects(
                weather_effects
            )
            embed.add_field(
                name=f"{EMOJI_EFFECTS} Weather Effects",
                value=effects_text,
                inline=False,
            )

        # Add footer
        embed.set_footer(text=FOOTER_TEXT)

        return embed

    @staticmethod
    def _format_wind_conditions(wind_timeline: Dict[str, Any]) -> str:
        """
        Format wind conditions for display in an embed field.

        Creates a timeline of wind conditions showing strength and direction
        across different time periods. Shows changes when wind shifts occur.

        Args:
            wind_timeline: Dictionary of wind data for each time period
                Format: {
                    'Dawn': {'strength': str, 'direction': str, 'changed': bool},
                    'Midday': {...}, etc.
                }

        Returns:
            str: Formatted string showing wind timeline, or calm wind message if empty

        Example:
            >>> timeline = {
            ...     'Dawn': {'strength': 'Light', 'direction': 'NE', 'changed': False},
            ...     'Midday': {'strength': 'Strong', 'direction': 'E', 'changed': True}
            ... }
            >>> WeatherDisplayManager._format_wind_conditions(timeline)
            '**Dawn:** Light NE\\n**Midday:** Strong E (changed)'
        """
        if not wind_timeline:
            return f"{EMOJI_CALM_WIND} Calm throughout the day"

        # Check if all periods have same wind
        all_same = all(
            w["strength"] == wind_timeline[0]["strength"]
            and w["direction"] == wind_timeline[0]["direction"]
            for w in wind_timeline
        )

        if all_same and wind_timeline[0]["strength"] == "calm":
            return f"{EMOJI_CALM_WIND} Calm throughout the day"

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

        Retrieves the display name and description for the weather type
        from the WEATHER_EFFECTS data structure. Returns a formatted string
        with the weather type as title and description if available.

        Args:
            weather_type: Type of weather (e.g., 'fair', 'rain', 'snow')
            weather_effects: List of weather effect strings (currently unused,
                            kept for interface compatibility)

        Returns:
            str: Formatted weather condition text with type and description

        Example:
            >>> WeatherDisplayManager._format_weather_condition("rain", [])
            '**Rain**\\nLight to moderate rainfall'
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
        Format weather effects for display as a bulleted list.

        Converts a list of effect strings into a formatted display with
        bullet points for each effect. Returns placeholder text if no effects.

        Args:
            effects: List of weather effect strings (e.g., visibility, bonuses)

        Returns:
            str: Formatted effects text with bullet points, or placeholder message

        Example:
            >>> effects = ["Visibility reduced", "Difficult terrain"]
            >>> WeatherDisplayManager._format_weather_effects(effects)
            '• Visibility reduced\\n• Difficult terrain'
        """
        if not effects:
            return "*No special effects*"

        # Add bullet points to each effect
        formatted_effects = [f"• {effect}" for effect in effects]
        return "\n".join(formatted_effects)

    @staticmethod
    def _format_temperature(weather_data: Dict[str, Any]) -> str:
        """
        Format temperature information including wind chill effects.

        Displays actual temperature and includes wind chill perception if
        the temperature difference is significant (≥10°C). Wind chill is
        calculated by weather mechanics based on wind strength.

        Args:
            weather_data: Dictionary containing temperature information with keys:
                - actual_temp or temperature: Base temperature value
                - perceived_temp: Temperature after wind chill adjustment
                - wind_chill_note: Description of wind chill effect

        Returns:
            str: Formatted temperature text, with wind chill info if significant

        Example:
            >>> data = {
            ...     "actual_temp": 5,
            ...     "perceived_temp": -3,
            ...     "wind_chill_note": "strong winds"
            ... }
            >>> WeatherDisplayManager._format_temperature(data)
            '**5°C** (Feels like -3°C due to strong winds)'
        """
        # Get actual and perceived temperatures
        actual_temp = weather_data.get(
            "actual_temp", weather_data.get("temperature", DEFAULT_TEMPERATURE)
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
            temp_diff = abs(perceived_temp - actual_temp)
            wind_strength = "Strong" if temp_diff >= TEMP_DIFF_STRONG_WIND else ""
            temp_text += f"\n**Feels like: {perceived_temp}°C** (feels {temp_diff}°C {'colder' if perceived_temp < actual_temp else 'warmer'} due to {wind_strength} wind)"

        return temp_text

    @staticmethod
    async def _send_embed(
        context: Union[discord.Interaction, commands.Context],
        embed: discord.Embed,
        is_slash: bool = False,
    ) -> None:
        """
        Send an embed to Discord, handling both slash and prefix commands.

        Automatically detects the context type and uses the appropriate
        response method. For slash commands, uses interaction.response.send_message
        or followup. For prefix commands, uses ctx.send.

        Args:
            context: The Discord context or interaction to respond to
            embed: The Discord embed to send
            is_slash: Whether this is a slash command response

        Returns:
            None: Sends message directly to Discord

        Note:
            For slash commands, automatically handles whether to use
            response.send_message or followup based on interaction state.
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
    async def send_error(
        context: Union[discord.Interaction, commands.Context],
        message: str,
        is_slash: bool = False,
    ) -> None:
        """
        Send an error message to the user in a red embed.

        Creates a standardized error message format with red color and
        error emoji. Handles both slash and prefix command contexts.

        Args:
            context: The Discord context or interaction to respond to
            message: The error message text to display
            is_slash: Whether this is a slash command response

        Returns:
            None: Sends error embed directly to Discord

        Example:
            >>> await WeatherDisplayManager.send_error(ctx, "Journey not found", True)
        """
        embed = discord.Embed(
            title=f"{EMOJI_ERROR} Error",
            description=message,
            color=WeatherDisplayManager.COLOR_ERROR,
        )
        await WeatherDisplayManager._send_embed(context, embed, is_slash)

    @staticmethod
    async def send_info(
        context: Union[discord.Interaction, commands.Context],
        message: str,
        title: str = f"{EMOJI_INFO} Information",
        is_slash: bool = False,
    ) -> None:
        """
        Send an informational message to the user in a gray embed.

        Creates a standardized informational message format with gray color
        and info emoji. Handles both slash and prefix command contexts.

        Args:
            context: The Discord context or interaction to respond to
            message: The informational message text to display
            title: Title for the embed (default: "ℹ️ Information")
            is_slash: Whether this is a slash command response

        Returns:
            None: Sends info embed directly to Discord

        Example:
            >>> await WeatherDisplayManager.send_info(ctx, "Weather updated", is_slash=True)
        """
        embed = discord.Embed(
            title=title, description=message, color=WeatherDisplayManager.COLOR_INFO
        )
        await WeatherDisplayManager._send_embed(context, embed, is_slash)
