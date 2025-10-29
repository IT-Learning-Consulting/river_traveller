"""
Weather formatters - utility functions for formatting weather data.

This module contains pure utility functions for formatting weather-related data.
All methods are static for easy testing and reusability.
"""


class WeatherFormatters:
    """
    Utility class for weather formatting.

    All methods are static/pure functions for easy testing.
    These functions have no side effects and can be tested in isolation.
    """

    @staticmethod
    def get_weather_emoji(weather_type: str) -> str:
        """
        Get emoji for weather type.

        Args:
            weather_type: Type of weather (dry, fair, rain, downpour, snow, blizzard)

        Returns:
            str: Emoji representing the weather type
        """
        emojis = {
            "dry": "☀️",
            "fair": "🌤️",
            "rain": "🌧️",
            "downpour": "⛈️",
            "snow": "❄️",
            "blizzard": "🌨️",
        }
        return emojis.get(weather_type, "🌤️")

    @staticmethod
    def get_temperature_emoji(temp: int) -> str:
        """
        Get emoji for temperature value.

        Args:
            temp: Temperature in Celsius

        Returns:
            str: Emoji representing the temperature range
        """
        if temp < -5:
            return "🥶"
        elif temp < 5:
            return "❄️"
        elif temp < 15:
            return "🌡️"
        elif temp < 25:
            return "☀️"
        else:
            return "🔥"

    @staticmethod
    def format_modifier_for_display(modifier_str: str) -> str:
        """
        Format wind modifier for clearer display in notifications.

        This converts raw modifier strings like "-10 penalty, 25% speed"
        into formatted text with clear explanations.

        Args:
            modifier_str: Raw modifier string from wind mechanics

        Returns:
            str: Formatted string with clear explanations

        Examples:
            >>> format_modifier_for_display("-10 penalty, 25% speed")
            '**Movement Speed:** 25% speed\\n  └─ **Boat Handling Tests:** -10'

            >>> format_modifier_for_display("+10%")
            '**Movement Speed:** +10%'

            >>> format_modifier_for_display("—")
            'No modifier to movement or tests'
        """
        if "penalty" in modifier_str.lower():
            # Parse complex modifier with penalty
            parts = modifier_str.split(",")
            penalty_part = parts[0].strip()
            speed_part = parts[1].strip() if len(parts) > 1 else None

            # Extract the penalty number (e.g., "-10")
            penalty_num = penalty_part.split()[0]

            result = f"**Movement Speed:** {speed_part}\n"
            result += f"  └─ **Boat Handling Tests:** {penalty_num}"
            return result
        elif modifier_str == "—":
            return "No modifier to movement or tests"
        else:
            # Simple percentage like "+10%" or "-5%"
            return f"**Movement Speed:** {modifier_str}"

    @staticmethod
    def format_province_name(province: str) -> str:
        """
        Format province name for display.

        Converts snake_case province names to Title Case with spaces.

        Args:
            province: Province name in snake_case (e.g., "border_princes")

        Returns:
            str: Formatted province name (e.g., "Border Princes")
        """
        return province.replace("_", " ").title()

    @staticmethod
    def format_season_name(season: str) -> str:
        """
        Format season name for display.

        Args:
            season: Season name in lowercase (e.g., "summer")

        Returns:
            str: Capitalized season name (e.g., "Summer")
        """
        return season.title()
