"""
Weather formatters - utility functions for formatting weather data.

This module provides pure utility functions for formatting weather-related data
for display in Discord. All functions are static methods organized in a utility
class for namespace organization and easy testing.

Key Features:
    - Weather emoji selection based on condition types
    - Temperature emoji selection based on temperature ranges
    - Wind modifier formatting for clear display
    - Province and season name formatting for consistent display

Design Principles:
    - Pure functions with no side effects
    - Static methods for easy testing in isolation
    - Clear input/output contracts with type hints
    - Consistent formatting patterns across all methods

Usage Example:
    >>> emoji = WeatherFormatters.get_weather_emoji("rain")
    >>> print(emoji)
    '🌧️'
    >>> province = WeatherFormatters.format_province_name("border_princes")
    >>> print(province)
    'Border Princes'
"""

# Weather emoji mappings
WEATHER_EMOJI_DRY = "☀️"
WEATHER_EMOJI_FAIR = "🌤️"
WEATHER_EMOJI_RAIN = "🌧️"
WEATHER_EMOJI_DOWNPOUR = "⛈️"
WEATHER_EMOJI_SNOW = "❄️"
WEATHER_EMOJI_BLIZZARD = "🌨️"
WEATHER_EMOJI_DEFAULT = WEATHER_EMOJI_FAIR

# Temperature emoji mappings and thresholds
TEMP_FREEZING = -5  # Below this is freezing cold
TEMP_COLD = 5  # Below this is cold
TEMP_COOL = 15  # Below this is cool
TEMP_WARM = 25  # Below this is warm, above is hot

TEMP_EMOJI_FREEZING = "🥶"
TEMP_EMOJI_COLD = "❄️"
TEMP_EMOJI_COOL = "🌡️"
TEMP_EMOJI_WARM = "☀️"
TEMP_EMOJI_HOT = "🔥"

# Modifier display text
MODIFIER_NO_EFFECT = "—"
MODIFIER_NO_EFFECT_TEXT = "No modifier to movement or tests"
MODIFIER_SPEED_LABEL = "**Movement Speed:**"
MODIFIER_TEST_LABEL = "**Boat Handling Tests:**"


class WeatherFormatters:
    """
    Utility class for weather formatting operations.

    This class provides static utility methods for formatting weather-related
    data for display in Discord. All methods are pure functions with no side
    effects, making them easy to test and reuse.

    Responsibilities:
        - Converting weather types to appropriate emojis
        - Converting temperatures to visual emoji representations
        - Formatting wind modifiers for clear display
        - Formatting province and season names to Title Case

    Class Attributes:
        None - all methods are static utilities

    Example:
        >>> # Get weather emoji
        >>> emoji = WeatherFormatters.get_weather_emoji("rain")
        >>> # Format province name
        >>> name = WeatherFormatters.format_province_name("reikland")
        >>> # Format modifier
        >>> mod = WeatherFormatters.format_modifier_for_display("-10 penalty, 25% speed")
    """

    @staticmethod
    def get_weather_emoji(weather_type: str) -> str:
        """
        Get emoji representation for a weather type.

        Returns the appropriate emoji character for display based on the
        weather condition type. Falls back to fair weather emoji if the
        type is unrecognized.

        Args:
            weather_type: Type of weather condition. Valid values:
                - "dry": Sunny/dry conditions
                - "fair": Fair weather
                - "rain": Rainy conditions
                - "downpour": Heavy rain/storm
                - "snow": Snowy conditions
                - "blizzard": Heavy snow/blizzard

        Returns:
            str: Unicode emoji character representing the weather type

        Example:
            >>> WeatherFormatters.get_weather_emoji("rain")
            '🌧️'
            >>> WeatherFormatters.get_weather_emoji("unknown")
            '🌤️'
        """
        emojis = {
            "dry": WEATHER_EMOJI_DRY,
            "fair": WEATHER_EMOJI_FAIR,
            "rain": WEATHER_EMOJI_RAIN,
            "downpour": WEATHER_EMOJI_DOWNPOUR,
            "snow": WEATHER_EMOJI_SNOW,
            "blizzard": WEATHER_EMOJI_BLIZZARD,
        }
        return emojis.get(weather_type, WEATHER_EMOJI_DEFAULT)

    @staticmethod
    def get_temperature_emoji(temp: int) -> str:
        """
        Get emoji representation for a temperature value.

        Returns an appropriate emoji based on temperature ranges to provide
        visual indication of temperature conditions. Ranges are designed
        for European climate context (Celsius).

        Args:
            temp: Temperature in degrees Celsius

        Returns:
            str: Unicode emoji character representing the temperature range:
                - 🥶 for freezing (< -5°C)
                - ❄️ for cold (-5°C to 5°C)
                - 🌡️ for cool (5°C to 15°C)
                - ☀️ for warm (15°C to 25°C)
                - 🔥 for hot (≥ 25°C)

        Example:
            >>> WeatherFormatters.get_temperature_emoji(-10)
            '🥶'
            >>> WeatherFormatters.get_temperature_emoji(20)
            '☀️'
        """
        if temp < TEMP_FREEZING:
            return TEMP_EMOJI_FREEZING
        elif temp < TEMP_COLD:
            return TEMP_EMOJI_COLD
        elif temp < TEMP_COOL:
            return TEMP_EMOJI_COOL
        elif temp < TEMP_WARM:
            return TEMP_EMOJI_WARM
        else:
            return TEMP_EMOJI_HOT

    @staticmethod
    def format_modifier_for_display(modifier_str: str) -> str:
        """
        Format wind modifier for clearer display in notifications.

        Converts raw modifier strings from wind mechanics into formatted text
        with clear explanations for users. Handles three cases: complex modifiers
        with penalties and speed changes, no modifier, and simple percentage modifiers.

        Args:
            modifier_str: Raw modifier string from wind mechanics. Formats include:
                - "-10 penalty, 25% speed" (complex with penalty and speed)
                - "—" (no modifier)
                - "+10%" or "-5%" (simple percentage)

        Returns:
            str: Formatted string with clear labels and explanations

        Examples:
            >>> WeatherFormatters.format_modifier_for_display("-10 penalty, 25% speed")
            '**Movement Speed:** 25% speed\\n  └─ **Boat Handling Tests:** -10'

            >>> WeatherFormatters.format_modifier_for_display("+10%")
            '**Movement Speed:** +10%'

            >>> WeatherFormatters.format_modifier_for_display("—")
            'No modifier to movement or tests'
        """
        if "penalty" in modifier_str.lower():
            # Parse complex modifier with penalty
            parts = modifier_str.split(",")
            penalty_part = parts[0].strip()
            speed_part = parts[1].strip() if len(parts) > 1 else None

            # Extract the penalty number (e.g., "-10")
            penalty_num = penalty_part.split()[0]

            result = f"{MODIFIER_SPEED_LABEL} {speed_part}\n"
            result += f"  └─ {MODIFIER_TEST_LABEL} {penalty_num}"
            return result
        elif modifier_str == MODIFIER_NO_EFFECT:
            return MODIFIER_NO_EFFECT_TEXT
        else:
            # Simple percentage like "+10%" or "-5%"
            return f"{MODIFIER_SPEED_LABEL} {modifier_str}"

    @staticmethod
    def format_province_name(province: str) -> str:
        """
        Format province name for display in Title Case.

        Converts snake_case province names to human-readable Title Case
        with spaces. Used for consistent display across all weather embeds.

        Args:
            province: Province name in snake_case (e.g., "border_princes", "reikland")

        Returns:
            str: Formatted province name in Title Case (e.g., "Border Princes", "Reikland")

        Example:
            >>> WeatherFormatters.format_province_name("border_princes")
            'Border Princes'
            >>> WeatherFormatters.format_province_name("reikland")
            'Reikland'
        """
        return province.replace("_", " ").title()

    @staticmethod
    def format_season_name(season: str) -> str:
        """
        Format season name for display in Title Case.

        Converts lowercase season names to Title Case for consistent
        display across all weather embeds.

        Args:
            season: Season name in lowercase (e.g., "summer", "winter")

        Returns:
            str: Capitalized season name (e.g., "Summer", "Winter")

        Example:
            >>> WeatherFormatters.format_season_name("summer")
            'Summer'
            >>> WeatherFormatters.format_season_name("winter")
            'Winter'
        """
        return season.title()
