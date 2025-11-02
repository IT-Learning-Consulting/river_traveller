"""
Calculate and extract weather modifiers for boat handling tests.

⚠️ DEPRECATED MODULE - Will be removed in Phase 5
This module has been superseded by WeatherModifierService (utils/weather_modifier_service.py).

MIGRATION PATH:
  OLD: from utils.modifier_calculator import get_active_weather_modifiers
  NEW: from utils.weather_modifier_service import WeatherModifierService
       service = WeatherModifierService()
       impact = service.get_active_weather_modifiers(guild_id, time)
       # Returns WeatherImpact dataclass instead of dict

FUNCTIONS TO MIGRATE:
  - get_active_weather_modifiers() → WeatherModifierService.get_active_weather_modifiers()
  - get_weather_summary() → WeatherModifierService.get_weather_summary()
  - format_weather_impact_for_embed() → Move to presentation/command layer

REMAINING USAGE:
  - commands/boat_handling.py still uses this module
  - Will be migrated in Phase 5.1

This module bridges the weather system and boat handling mechanics,
extracting active weather conditions and converting them to test modifiers.

Key Responsibilities:
    - Extract current weather conditions from stored journey state
    - Convert wind strength/direction to movement speed modifiers
    - Identify boat handling penalties from calm/adverse conditions
    - Detect special requirements (tacking, tests)
    - Format weather data for Discord embeds

Design Principles:
    - Defensive programming: Handles missing/malformed data gracefully
    - Separation of concerns: Weather extraction vs modifier calculation vs formatting
    - Pure helper functions for parsing and conversion
    - Type safety with full type hints

Wind Modifier System:
    - Speed: -25% to +25% movement modifier
    - Tacking: Some tailwinds require tacking for bonus
    - Tests: Special boat handling tests for strong winds
    - Penalties: Calm winds impose -10 to Boat Handling tests

Usage Example:
    >>> mods = get_active_weather_modifiers("guild_123", "midday")
    >>> if mods:
    ...     print(f"Wind: {mods['wind_strength']} {mods['wind_direction']}")
    ...     print(f"Speed modifier: {mods['wind_modifier_percent']}%")
    >>> formatted = format_weather_impact_for_embed(mods)
"""

from typing import Optional, Dict
from db.weather_storage import WeatherStorage
from db.weather_data import WIND_STRENGTH, WIND_DIRECTION
from utils.weather_mechanics import get_wind_modifiers, get_weather_effects
from db.models.weather_models import WindTimeline, WindCondition

# Time of day constants
TIME_DAWN: str = "dawn"
TIME_MIDDAY: str = "midday"
TIME_DUSK: str = "dusk"
TIME_MIDNIGHT: str = "midnight"

# Time mapping for lookups
TIME_MAP: Dict[str, str] = {
    TIME_DAWN: "Dawn",
    TIME_MIDDAY: "Midday",
    TIME_DUSK: "Dusk",
    TIME_MIDNIGHT: "Midnight",
}

# Parsing constants
EM_DASH: str = "—"
DEFAULT_MODIFIER: int = 0
BOAT_HANDLING_PHRASE: str = "Boat Handling"
BOAT_HANDLING_PHRASE_LOWER: str = "boat handling"
TACKING_KEYWORD: str = "tacking"
TEST_REQUIRED_PHRASE: str = "must be made"

# Formatting constants
EMOJI_TACKING: str = "⚓"
EMOJI_TEST_REQUIRED: str = "⚠️"
NO_HAZARDS_TEXT: str = "No weather-related hazards"

# Default display values
DEFAULT_WIND_DISPLAY: str = "Unknown"


def get_active_weather_modifiers(
    guild_id: str,
    time_of_day: str = TIME_MIDDAY,
    storage: Optional[WeatherStorage] = None,
) -> Optional[Dict]:
    """
    Get currently active weather modifiers for a guild at a specific time.

    Extracts current weather conditions, converts to modifiers, and packages
    all relevant data for boat handling tests.

    Args:
        guild_id: Discord guild ID
        time_of_day: Time period (dawn, midday, dusk, midnight). Default: midday
        storage: Optional WeatherStorage instance (uses default if not provided).
            Primarily for testing

    Returns:
        Optional[Dict]: Weather modifiers dict with keys:
            - wind_modifier_percent (int): Movement speed modifier (-25 to +25)
            - wind_strength (str): Raw wind strength key
            - wind_direction (str): Raw wind direction key
            - wind_strength_display (str): Formatted wind strength
            - wind_direction_display (str): Formatted wind direction
            - requires_tacking (bool): Whether tacking is required
            - requires_test (bool): Whether special test required
            - boat_handling_penalty (int): Test penalty (usually -10 for calm)
            - weather_effects (List[str]): Active weather effects
            - wind_notes (str): Additional wind notes
            - weather_name (str): Weather type display name
            - day_number (int): Current journey day
        Returns None if no active journey or no weather data

    Example:
        >>> mods = get_active_weather_modifiers("123456", "midday")
        >>> if mods:
        ...     print(f"Speed: {mods['wind_modifier_percent']}%")
        ...     print(f"Penalty: {mods['boat_handling_penalty']}")
    """
    # Use provided storage or create new one
    if storage is None:
        storage = WeatherStorage()

    # Get current journey state
    journey = storage.get_journey_state(guild_id)
    if not journey:
        return None

    # Get current day weather
    # current_day represents the current day being played
    current_day = journey.current_day
    weather = storage.get_daily_weather(guild_id, current_day)

    if not weather:
        return None

    # Get wind_timeline from dataclass
    wind_timeline = weather.wind_timeline
    if not wind_timeline:
        return None

    # Extract wind for specific time (returns WindCondition dataclass)
    wind_data = _get_wind_for_time_dataclass(wind_timeline, time_of_day.lower())

    if not wind_data:
        return None

    # Get wind modifiers from WindCondition dataclass
    wind_mods = get_wind_modifiers(wind_data.strength, wind_data.direction)

    # Parse wind modifier percentage (e.g., "+10%" → 10)
    speed_mod = _parse_speed_modifier(wind_mods["modifier"])

    # Check for special conditions
    requires_tacking = False
    requires_test = False
    if wind_mods["notes"]:
        notes_lower = wind_mods["notes"].lower()
        requires_tacking = TACKING_KEYWORD in notes_lower
        requires_test = TEST_REQUIRED_PHRASE in notes_lower

    # Get boat handling penalty (from Calm winds or special notes)
    bh_penalty = _extract_boat_handling_penalty(
        wind_mods["modifier"], wind_mods["notes"]
    )

    # Get weather effects
    weather_effects_data = get_weather_effects(weather.weather_type)

    return {
        "wind_modifier_percent": speed_mod,
        "wind_strength": wind_data.strength,
        "wind_direction": wind_data.direction,
        "wind_strength_display": WIND_STRENGTH.get(
            wind_data.strength, DEFAULT_WIND_DISPLAY
        ),
        "wind_direction_display": WIND_DIRECTION.get(
            wind_data.direction, DEFAULT_WIND_DISPLAY
        ),
        "requires_tacking": requires_tacking,
        "requires_test": requires_test,
        "boat_handling_penalty": bh_penalty,
        "weather_effects": weather_effects_data["effects"],
        "wind_notes": wind_mods["notes"],
        "weather_name": weather_effects_data["name"],
        "day_number": current_day,
    }


def _get_wind_for_time_dataclass(
    wind_timeline: WindTimeline, time_of_day: str
) -> Optional[WindCondition]:
    """
    Extract wind data for specific time of day from WindTimeline dataclass.

    Args:
        wind_timeline: WindTimeline dataclass with dawn/midday/dusk/midnight attributes
        time_of_day: Time period (dawn, midday, dusk, midnight). Case-insensitive

    Returns:
        Optional[WindCondition]: WindCondition dataclass for the time period,
            or None if invalid time_of_day

    Example:
        >>> wind = _get_wind_for_time_dataclass(timeline, "midday")
        >>> print(wind.strength)
        moderate
    """
    time_lower = time_of_day.lower()

    if time_lower == TIME_DAWN:
        return wind_timeline.dawn
    elif time_lower == TIME_MIDDAY:
        return wind_timeline.midday
    elif time_lower == TIME_DUSK:
        return wind_timeline.dusk
    elif time_lower == TIME_MIDNIGHT:
        return wind_timeline.midnight
    else:
        return None


def _parse_speed_modifier(modifier_text: str) -> int:
    """
    Parse speed modifier from text like "+10%" or "-25%".

    Handles various formats and edge cases (em dash, None, invalid).

    Args:
        modifier_text: Modifier string from wind data (e.g., "+10%", "-25%", "—")

    Returns:
        int: Integer percentage (-25 to +25), or 0 if invalid/empty

    Example:
        >>> print(_parse_speed_modifier("+10%"))
        10
        >>> print(_parse_speed_modifier("-25%"))
        -25
        >>> print(_parse_speed_modifier("—"))
        0
    """
    if not modifier_text or modifier_text == EM_DASH:
        return DEFAULT_MODIFIER

    # Remove % and convert to int
    try:
        # Handle formats like "+10%", "-20%", or "0%"
        clean = modifier_text.replace("%", "").replace("+", "").strip()
        return int(clean)
    except (ValueError, AttributeError):
        return DEFAULT_MODIFIER


def _extract_boat_handling_penalty(
    modifier_text: str, notes: Optional[str] = None
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
        >>> print(_extract_boat_handling_penalty("-10 penalty, 25% speed"))
        -10
        >>> print(_extract_boat_handling_penalty("Calm conditions: -10 Boat Handling"))
        -10
        >>> print(_extract_boat_handling_penalty("+25%", "Tailwind"))
        0
    """
    # Check both modifier_text and notes for "Boat Handling" or "boat handling"
    text_to_check = modifier_text
    if notes:
        text_to_check += " " + notes

    if (
        BOAT_HANDLING_PHRASE in text_to_check
        or BOAT_HANDLING_PHRASE_LOWER in text_to_check.lower()
    ):
        try:
            # Extract the number (e.g., "-10 penalty" → -10 or "penalty of -10" → -10)
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

    return DEFAULT_MODIFIER


def get_weather_summary(guild_id: str) -> Optional[Dict]:
    """
    Get a summary of current weather for all time periods.

    Aggregates weather data for all four time periods (dawn, midday, dusk, midnight)
    into a single summary dict. Useful for full-day weather displays.

    Args:
        guild_id: Discord guild ID

    Returns:
        Optional[Dict]: Weather summary with keys:
            - day_number (int): Current journey day
            - season (str): Current season
            - province (str): Current province
            - times (Dict[str, Dict]): Weather for each time period with:
                - wind (str): Formatted wind description
                - speed_mod (int): Speed modifier percentage
                - bh_penalty (int): Boat handling penalty
                - requires_tacking (bool): Tacking requirement
                - requires_test (bool): Special test requirement
        Returns None if no active journey

    Example:
        >>> summary = get_weather_summary("123456")
        >>> if summary:
        ...     print(f"Day {summary['day_number']}")
        ...     for time, data in summary['times'].items():
        ...         print(f"{time}: {data['wind']}")
    """
    storage = WeatherStorage()

    journey = storage.get_journey_state(guild_id)
    if not journey:
        return None

    # current_day represents the current day being played
    current_day = journey.current_day
    weather = storage.get_daily_weather(guild_id, current_day)

    if not weather:
        return None

    summary = {
        "day_number": current_day,
        "season": journey.season,
        "province": journey.province,
        "times": {},
    }

    for time in [TIME_DAWN, TIME_MIDDAY, TIME_DUSK, TIME_MIDNIGHT]:
        mods = get_active_weather_modifiers(guild_id, time)
        if mods:
            summary["times"][time] = {
                "wind": f"{mods['wind_strength_display']} {mods['wind_direction_display']}",
                "speed_mod": mods["wind_modifier_percent"],
                "bh_penalty": mods["boat_handling_penalty"],
                "requires_tacking": mods["requires_tacking"],
                "requires_test": mods["requires_test"],
            }

    return summary


def format_weather_impact_for_embed(weather_mods: Dict) -> str:
    """
    Format weather modifiers into a string suitable for Discord embed.

    Creates multi-line formatted text with wind info, modifiers, and special
    conditions. Designed for Discord embed field values.

    Args:
        weather_mods: Dictionary from get_active_weather_modifiers() with all keys

    Returns:
        str: Multi-line formatted string with:
            - Wind description (strength + direction)
            - Movement speed modifier
            - Boat handling penalty (if applicable)
            - Special conditions (tacking, tests)
            - Weather effects (if hazardous)

    Example:
        >>> mods = get_active_weather_modifiers("123", "midday")
        >>> formatted = format_weather_impact_for_embed(mods)
        >>> print(formatted)
        **Wind:** Moderate Tailwind
        **Movement Speed:** +10%
        ⚓ *Tacking required for speed bonus*
    """
    lines = []

    # Wind information
    lines.append(
        f"**Wind:** {weather_mods['wind_strength_display']} {weather_mods['wind_direction_display']}"
    )

    # Movement modifier
    speed_mod = weather_mods["wind_modifier_percent"]
    speed_text = f"{speed_mod:+d}%" if speed_mod != 0 else "0%"
    lines.append(f"**Movement Speed:** {speed_text}")

    # Boat handling penalty
    if weather_mods["boat_handling_penalty"] != DEFAULT_MODIFIER:
        lines.append(f"**Test Modifier:** {weather_mods['boat_handling_penalty']:+d}")

    # Special conditions
    if weather_mods["requires_tacking"]:
        lines.append(f"{EMOJI_TACKING} *Tacking required for speed bonus*")

    if weather_mods["requires_test"]:
        lines.append(f"{EMOJI_TEST_REQUIRED} *Special Boat Handling test required*")

    # Weather conditions
    if (
        weather_mods["weather_effects"]
        and weather_mods["weather_effects"][0] != NO_HAZARDS_TEXT
    ):
        lines.append(f"\n**{weather_mods['weather_name']}:**")
        for effect in weather_mods["weather_effects"]:
            lines.append(f"• {effect}")

    return "\n".join(lines)
