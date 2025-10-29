"""
Calculate and extract weather modifiers for boat handling tests.

This module bridges the weather system and boat handling mechanics,
extracting active weather conditions and converting them to test modifiers.
"""

from typing import Optional, Dict, List
from db.weather_storage import WeatherStorage
from db.weather_data import WIND_STRENGTH, WIND_DIRECTION
from utils.weather_mechanics import get_wind_modifiers, get_weather_effects


def get_active_weather_modifiers(
    guild_id: str, time_of_day: str = "midday"
) -> Optional[Dict]:
    """
    Get currently active weather modifiers for a guild at a specific time.

    Args:
        guild_id: Discord guild ID
        time_of_day: Time period (dawn, midday, dusk, midnight)

    Returns:
        Dict with weather modifiers or None if no active weather:
        {
            "wind_modifier_percent": int (-25 to +25),
            "wind_strength": str,
            "wind_direction": str,
            "wind_strength_display": str,
            "wind_direction_display": str,
            "requires_tacking": bool,
            "requires_test": bool,
            "boat_handling_penalty": int,
            "weather_effects": List[str],
            "wind_notes": str,
            "weather_name": str,
            "day_number": int,
        }
    """
    storage = WeatherStorage()

    # Get current journey state
    journey = storage.get_journey_state(guild_id)
    if not journey:
        return None

    # Get current day weather
    current_day = journey["current_day"]
    weather = storage.get_daily_weather(guild_id, current_day)

    if not weather:
        return None

    # Extract wind for specific time
    wind_data = _get_wind_for_time(weather["wind_timeline"], time_of_day.lower())

    if not wind_data:
        return None

    # Get wind modifiers from data
    wind_mods = get_wind_modifiers(wind_data["strength"], wind_data["direction"])

    # Parse wind modifier percentage (e.g., "+10%" → 10)
    speed_mod = _parse_speed_modifier(wind_mods["modifier"])

    # Check for special conditions
    requires_tacking = False
    requires_test = False
    if wind_mods["notes"]:
        notes_lower = wind_mods["notes"].lower()
        requires_tacking = "tacking" in notes_lower
        requires_test = "must be made" in notes_lower

    # Get boat handling penalty (from Calm winds or special notes)
    bh_penalty = _extract_boat_handling_penalty(
        wind_mods["modifier"], wind_mods["notes"]
    )

    # Get weather effects
    weather_effects_data = get_weather_effects(weather["weather_type"])

    return {
        "wind_modifier_percent": speed_mod,
        "wind_strength": wind_data["strength"],
        "wind_direction": wind_data["direction"],
        "wind_strength_display": WIND_STRENGTH.get(wind_data["strength"], "Unknown"),
        "wind_direction_display": WIND_DIRECTION.get(wind_data["direction"], "Unknown"),
        "requires_tacking": requires_tacking,
        "requires_test": requires_test,
        "boat_handling_penalty": bh_penalty,
        "weather_effects": weather_effects_data["effects"],
        "wind_notes": wind_mods["notes"],
        "weather_name": weather_effects_data["name"],
        "day_number": current_day,
    }


def _get_wind_for_time(wind_timeline: List[Dict], time_of_day: str) -> Optional[Dict]:
    """
    Extract wind data for specific time of day from timeline.

    Args:
        wind_timeline: List of wind entries for the day
        time_of_day: dawn, midday, dusk, or midnight

    Returns:
        Wind entry dict or None if not found
    """
    time_map = {
        "dawn": "Dawn",
        "midday": "Midday",
        "dusk": "Dusk",
        "midnight": "Midnight",
    }

    target_time = time_map.get(time_of_day.lower())
    if not target_time:
        return None

    for wind_entry in wind_timeline:
        if wind_entry["time"] == target_time:
            return wind_entry

    return None


def _parse_speed_modifier(modifier_text: str) -> int:
    """
    Parse speed modifier from text like "+10%" or "-25%".

    Args:
        modifier_text: Modifier string from wind data

    Returns:
        Integer percentage (-25 to +25)
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
    modifier_text: str, notes: Optional[str] = None
) -> int:
    """
    Extract boat handling test penalty from wind conditions.

    Calm winds impose a -10 penalty on Boat Handling tests.

    Args:
        modifier_text: Modifier string (e.g., "-10 penalty, 25% speed")
        notes: Additional notes about wind effects

    Returns:
        Penalty value (negative integer) or 0 if no penalty
    """
    # Check both modifier_text and notes for "Boat Handling" or "boat handling"
    text_to_check = modifier_text
    if notes:
        text_to_check += " " + notes

    if "Boat Handling" in text_to_check or "boat handling" in text_to_check.lower():
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

    return 0


def get_weather_summary(guild_id: str) -> Optional[Dict]:
    """
    Get a summary of current weather for all time periods.

    Args:
        guild_id: Discord guild ID

    Returns:
        Dict with weather summary for each time period or None if no journey
    """
    storage = WeatherStorage()

    journey = storage.get_journey_state(guild_id)
    if not journey:
        return None

    current_day = journey["current_day"]
    weather = storage.get_daily_weather(guild_id, current_day)

    if not weather:
        return None

    summary = {
        "day_number": current_day,
        "season": journey["season"],
        "province": journey["province"],
        "times": {},
    }

    for time in ["dawn", "midday", "dusk", "midnight"]:
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

    Args:
        weather_mods: Dictionary from get_active_weather_modifiers()

    Returns:
        Formatted string with weather impact details
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
    if weather_mods["boat_handling_penalty"] != 0:
        lines.append(f"**Test Modifier:** {weather_mods['boat_handling_penalty']:+d}")

    # Special conditions
    if weather_mods["requires_tacking"]:
        lines.append("⚓ *Tacking required for speed bonus*")

    if weather_mods["requires_test"]:
        lines.append("⚠️ *Special Boat Handling test required*")

    # Weather conditions
    if (
        weather_mods["weather_effects"]
        and weather_mods["weather_effects"][0] != "No weather-related hazards"
    ):
        lines.append(f"\n**{weather_mods['weather_name']}:**")
        for effect in weather_mods["weather_effects"]:
            lines.append(f"• {effect}")

    return "\n".join(lines)
