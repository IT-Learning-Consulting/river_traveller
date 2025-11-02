"""
Weather Modifier Service - Business logic for weather impact calculation.

This service encapsulates all weather modifier calculation logic, converting
weather data into structured WeatherImpact dataclasses. It replaces the
procedural functions in modifier_calculator.py with a testable service class.

Design Principles:
    - No Discord dependencies (pure business logic)
    - Returns structured WeatherImpact dataclasses
    - Delegates to utils.weather_mechanics for core rules
    - Fully testable with dependency injection
    - Single responsibility: Calculate weather impacts

Usage:
    >>> from utils.weather_modifier_service import WeatherModifierService
    >>> from db.weather_storage import WeatherStorage
    >>>
    >>> storage = WeatherStorage()
    >>> service = WeatherModifierService(storage=storage)
    >>>
    >>> impact = service.get_active_weather_modifiers("guild_123", "midday")
    >>> if impact:
    ...     print(f"Speed modifier: {impact.speed_percent}%")
    ...     print(f"Boat penalty: {impact.boat_penalty}")
"""

from typing import Optional
from db.weather_storage import WeatherStorage
from db.weather_data import WIND_STRENGTH, WIND_DIRECTION
from utils.weather_mechanics import get_wind_modifiers, get_weather_effects
from utils.weather_impact import WeatherImpact, WeatherSummary
from db.models.weather_models import WindTimeline, WindCondition


class WeatherModifierService:
    """
    Service for calculating weather impacts on boat handling.

    This service is pure business logic with no Discord dependencies.
    All methods return structured WeatherImpact dataclasses that can be
    used by the command layer or other services.

    Methods:
        get_active_weather_modifiers: Get weather impact for a specific time
        get_weather_summary: Get weather impacts for all time periods
    """

    # Time of day constants
    TIME_DAWN = "dawn"
    TIME_MIDDAY = "midday"
    TIME_DUSK = "dusk"
    TIME_MIDNIGHT = "midnight"

    # Parsing constants
    TACKING_KEYWORD = "tacking"
    TEST_REQUIRED_PHRASE = "must be made"
    BOAT_HANDLING_PHRASE = "Boat Handling"
    BOAT_HANDLING_PHRASE_LOWER = "boat handling"

    def __init__(self, storage: Optional[WeatherStorage] = None):
        """
        Initialize the weather modifier service.

        Args:
            storage: Optional WeatherStorage instance for dependency injection.
                If not provided, creates a new WeatherStorage instance.
                Primarily useful for testing with mock storage.
        """
        self.storage = storage if storage is not None else WeatherStorage()

    def get_active_weather_modifiers(
        self, guild_id: str, time_of_day: str = "midday"
    ) -> Optional[WeatherImpact]:
        """
        Get weather impact for a guild at a specific time of day.

        Extracts current weather conditions, converts to modifiers, and returns
        structured WeatherImpact dataclass with all relevant data.

        Args:
            guild_id: Discord guild ID
            time_of_day: Time period (dawn, midday, dusk, midnight). Default: midday

        Returns:
            Optional[WeatherImpact]: Weather impact data, or None if no active
                journey or no weather data available

        Example:
            >>> service = WeatherModifierService()
            >>> impact = service.get_active_weather_modifiers("123", "midday")
            >>> if impact:
            ...     print(f"Speed: {impact.speed_percent}%")
            ...     print(f"Penalty: {impact.boat_penalty}")
        """
        # Get current journey state
        journey = self.storage.get_journey_state(guild_id)
        if not journey:
            return None

        # Get current day weather
        # current_day represents the current day being played
        current_day = journey.current_day
        weather = self.storage.get_daily_weather(guild_id, current_day)

        if not weather:
            return None

        # Get wind_timeline from dataclass
        wind_timeline = weather.wind_timeline
        if not wind_timeline:
            return None

        # Extract wind for specific time (returns WindCondition dataclass)
        wind_data = self._get_wind_for_time(wind_timeline, time_of_day.lower())

        if not wind_data:
            return None

        # Get wind modifiers from WindCondition dataclass
        wind_mods = get_wind_modifiers(wind_data.strength, wind_data.direction)

        # Parse wind modifier percentage (e.g., "+10%" → 10)
        speed_mod = self._parse_speed_modifier(wind_mods["modifier"])

        # Check for special conditions
        requires_tacking = False
        requires_test = False
        if wind_mods["notes"]:
            notes_lower = wind_mods["notes"].lower()
            requires_tacking = self.TACKING_KEYWORD in notes_lower
            requires_test = self.TEST_REQUIRED_PHRASE in notes_lower

        # Get boat handling penalty (from Calm winds or special notes)
        bh_penalty = self._extract_boat_handling_penalty(
            wind_mods["modifier"], wind_mods["notes"]
        )

        # Get weather effects
        weather_effects_data = get_weather_effects(weather.weather_type)

        # Build and return WeatherImpact dataclass
        return WeatherImpact(
            speed_percent=speed_mod,
            boat_penalty=bh_penalty,
            wind_strength=wind_data.strength,
            wind_direction=wind_data.direction,
            wind_strength_display=WIND_STRENGTH.get(
                wind_data.strength, "Unknown"
            ),
            wind_direction_display=WIND_DIRECTION.get(
                wind_data.direction, "Unknown"
            ),
            requires_tacking=requires_tacking,
            requires_test=requires_test,
            weather_effects=weather_effects_data["effects"],
            wind_notes=wind_mods["notes"],
            weather_name=weather_effects_data["name"],
            day_number=current_day,
        )

    def get_weather_summary(self, guild_id: str) -> Optional[WeatherSummary]:
        """
        Get weather summary for all time periods in the current day.

        Aggregates weather impacts for dawn, midday, dusk, and midnight into
        a single WeatherSummary dataclass.

        Args:
            guild_id: Discord guild ID

        Returns:
            Optional[WeatherSummary]: Summary with weather impacts for all times,
                or None if no active journey

        Example:
            >>> service = WeatherModifierService()
            >>> summary = service.get_weather_summary("123")
            >>> if summary:
            ...     print(f"Day {summary.day_number} - {summary.season}")
            ...     if summary.midday:
            ...         print(f"Midday speed: {summary.midday.speed_percent}%")
        """
        # Get current journey state
        journey = self.storage.get_journey_state(guild_id)
        if not journey:
            return None

        # Get weather impacts for each time period
        dawn_impact = self.get_active_weather_modifiers(guild_id, self.TIME_DAWN)
        midday_impact = self.get_active_weather_modifiers(guild_id, self.TIME_MIDDAY)
        dusk_impact = self.get_active_weather_modifiers(guild_id, self.TIME_DUSK)
        midnight_impact = self.get_active_weather_modifiers(guild_id, self.TIME_MIDNIGHT)

        return WeatherSummary(
            day_number=journey.current_day,
            season=journey.season,
            province=journey.province,
            dawn=dawn_impact,
            midday=midday_impact,
            dusk=dusk_impact,
            midnight=midnight_impact,
        )

    def _get_wind_for_time(
        self, wind_timeline: WindTimeline, time_of_day: str
    ) -> Optional[WindCondition]:
        """
        Extract wind data for specific time of day from WindTimeline dataclass.

        Args:
            wind_timeline: WindTimeline dataclass with dawn/midday/dusk/midnight
            time_of_day: Time period (dawn, midday, dusk, midnight). Case-insensitive

        Returns:
            Optional[WindCondition]: WindCondition for the time period,
                or None if invalid time_of_day
        """
        time_lower = time_of_day.lower()

        if time_lower == self.TIME_DAWN:
            return wind_timeline.dawn
        elif time_lower == self.TIME_MIDDAY:
            return wind_timeline.midday
        elif time_lower == self.TIME_DUSK:
            return wind_timeline.dusk
        elif time_lower == self.TIME_MIDNIGHT:
            return wind_timeline.midnight
        else:
            return None

    def _parse_speed_modifier(self, modifier_text: str) -> int:
        """
        Parse speed modifier from text like "+10%" or "-25%".

        Handles various formats and edge cases (em dash, None, invalid).

        Args:
            modifier_text: Modifier string (e.g., "+10%", "-25%", "—")

        Returns:
            int: Integer percentage (-25 to +25), or 0 if invalid/empty

        Example:
            >>> service._parse_speed_modifier("+10%")
            10
            >>> service._parse_speed_modifier("—")
            0
        """
        if not modifier_text or modifier_text == "—":
            return 0

        # Remove % and convert to int
        try:
            # Handle formats like "+10%", "-20%", or "0%"
            clean = modifier_text.replace("%", "").replace("+", "").strip()
            return int(clean)
        except (ValueError, AttributeError):
            return 0

    def _extract_boat_handling_penalty(
        self, modifier_text: str, notes: Optional[str] = None
    ) -> int:
        """
        Extract boat handling test penalty from wind conditions.

        Calm winds impose a -10 penalty on Boat Handling tests. This function
        searches modifier text and notes for penalty indicators.

        Args:
            modifier_text: Modifier string (e.g., "-10 penalty, 25% speed")
            notes: Optional additional notes about wind effects

        Returns:
            int: Penalty value (negative integer) or 0 if no penalty

        Example:
            >>> service._extract_boat_handling_penalty("-10 penalty")
            -10
            >>> service._extract_boat_handling_penalty("+25%", "Tailwind")
            0
        """
        # Check both modifier_text and notes for "Boat Handling" or "boat handling"
        text_to_check = modifier_text
        if notes:
            text_to_check += " " + notes

        if (
            self.BOAT_HANDLING_PHRASE in text_to_check
            or self.BOAT_HANDLING_PHRASE_LOWER in text_to_check.lower()
        ):
            try:
                # Extract the number (e.g., "-10 penalty" → -10)
                if "-" in text_to_check:
                    # Split and find numeric parts
                    parts = text_to_check.split()
                    for part in parts:
                        # Remove common suffixes/prefixes
                        clean = part.strip(".,;:")
                        if clean.startswith("-"):
                            # Try to extract digits
                            num_str = ""
                            for c in clean[1:]:
                                if c.isdigit():
                                    num_str += c
                                else:
                                    break
                            if num_str:
                                return -int(num_str)
            except (ValueError, AttributeError):
                pass

        return 0
