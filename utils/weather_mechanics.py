"""
Weather mechanics for WFRP river travel.
Handles weather generation and calculations.
"""

import random
from typing import Tuple, List, Dict
from db.weather_data import (
    get_wind_strength_from_roll,
    get_wind_direction_from_roll,
    get_weather_from_roll,
    get_temperature_category_from_roll,
    get_province_base_temperature,
    WIND_STRENGTH,
    WIND_MODIFIERS,
    WEATHER_EFFECTS,
    TEMPERATURE_DESCRIPTIONS,
)


def generate_wind_conditions() -> Tuple[str, str]:
    """
    Generate initial wind conditions.

    Returns:
        Tuple of (strength, direction) as keys
    """
    strength_roll = random.randint(1, 10)
    direction_roll = random.randint(1, 10)

    strength = get_wind_strength_from_roll(strength_roll)
    direction = get_wind_direction_from_roll(direction_roll)

    return strength, direction


def check_wind_change(current_strength: str) -> Tuple[bool, str]:
    """
    Check if wind strength changes.

    Args:
        current_strength: Current wind strength key

    Returns:
        Tuple of (changed, new_strength)
    """
    roll = random.randint(1, 10)

    if roll != 1:
        return False, current_strength

    # Wind changes - 50% stronger, 50% lighter
    direction = random.choice(["stronger", "lighter"])

    strength_order = ["calm", "light", "bracing", "strong", "very_strong"]
    current_index = strength_order.index(current_strength)

    if direction == "stronger":
        if current_strength == "very_strong":
            # Very Strong can only go to Strong
            return True, "strong"
        new_index = min(current_index + 1, len(strength_order) - 1)
    else:  # lighter
        if current_strength == "calm":
            # Calm can only go to Light
            return True, "light"
        new_index = max(current_index - 1, 0)

    return True, strength_order[new_index]


def get_wind_modifiers(strength: str, direction: str) -> Dict[str, str]:
    """
    Get wind modifiers for boat handling.

    Args:
        strength: Wind strength key
        direction: Wind direction key

    Returns:
        Dict with 'modifier' and 'notes' keys
    """
    modifier_data = WIND_MODIFIERS.get((strength, direction), ("—", None))

    return {
        "modifier": modifier_data[0],
        "notes": modifier_data[1],
    }


def generate_daily_wind() -> List[Dict[str, str]]:
    """
    Generate wind conditions for a full day (dawn, midday, dusk, midnight).

    Returns:
        List of dicts with 'time', 'strength', 'direction', 'changed' keys
    """
    # Initial wind at dawn
    strength, direction = generate_wind_conditions()

    wind_timeline = [
        {
            "time": "Dawn",
            "strength": strength,
            "direction": direction,
            "changed": False,
        }
    ]

    # Check for changes at midday, dusk, midnight
    for time in ["Midday", "Dusk", "Midnight"]:
        changed, strength = check_wind_change(strength)

        # If wind changed, may also change direction
        if changed:
            # 50% chance direction also changes
            if random.randint(1, 2) == 1:
                direction_roll = random.randint(1, 10)
                direction = get_wind_direction_from_roll(direction_roll)

        wind_timeline.append(
            {
                "time": time,
                "strength": strength,
                "direction": direction,
                "changed": changed,
            }
        )

    return wind_timeline


def generate_daily_wind_with_previous(
    previous_midnight_wind: Dict[str, str],
) -> List[Dict[str, str]]:
    """
    Generate wind conditions for a new day, starting from previous day's midnight wind.
    This ensures weather continuity across days.

    Args:
        previous_midnight_wind: Dict with 'strength' and 'direction' from yesterday's midnight

    Returns:
        List of dicts with 'time', 'strength', 'direction', 'changed' keys
    """
    # Start with previous midnight conditions at dawn
    strength = previous_midnight_wind["strength"]
    direction = previous_midnight_wind["direction"]

    wind_timeline = [
        {
            "time": "Dawn",
            "strength": strength,
            "direction": direction,
            "changed": False,  # Not a change, it's continuity
        }
    ]

    # Check for changes at midday, dusk, midnight
    for time in ["Midday", "Dusk", "Midnight"]:
        changed, strength = check_wind_change(strength)

        # If wind changed, may also change direction
        if changed:
            # 50% chance direction also changes
            if random.randint(1, 2) == 1:
                direction_roll = random.randint(1, 10)
                direction = get_wind_direction_from_roll(direction_roll)

        wind_timeline.append(
            {
                "time": time,
                "strength": strength,
                "direction": direction,
                "changed": changed,
            }
        )

    return wind_timeline


def roll_weather_condition(season: str) -> str:
    """
    Roll for weather condition based on season.

    Args:
        season: Season name (spring, summer, autumn, winter)

    Returns:
        Weather type key
    """
    roll = random.randint(1, 100)
    return get_weather_from_roll(season, roll)


def get_weather_effects(weather_type: str) -> Dict[str, any]:
    """
    Get weather effects and description.

    Args:
        weather_type: Weather type key

    Returns:
        Dict with 'name', 'description', 'effects' keys
    """
    return WEATHER_EFFECTS.get(weather_type, WEATHER_EFFECTS["fair"])


def roll_temperature(season: str, province: str) -> Tuple[int, str, str]:
    """
    Roll for temperature.

    Args:
        season: Season name
        province: Province name

    Returns:
        Tuple of (actual_temp, category, description)
    """
    roll = random.randint(1, 100)
    category, modifier = get_temperature_category_from_roll(roll)

    base_temp = get_province_base_temperature(province, season)
    actual_temp = base_temp + modifier

    description = TEMPERATURE_DESCRIPTIONS.get(
        category, TEMPERATURE_DESCRIPTIONS["average"]
    )

    return actual_temp, category, description


def handle_cold_front(roll: int, current_cold_front_days: int) -> Tuple[int, int]:
    """
    Check for cold front and manage duration.

    Cold fronts occur on a roll of 2 and last 10+1d10 days.

    Args:
        roll: Temperature roll (1-100)
        current_cold_front_days: Days remaining in current cold front (0 if none)

    Returns:
        Tuple of (temperature_modifier, days_remaining)
    """
    if roll == 2 and current_cold_front_days == 0:
        # New cold front starting
        duration = 10 + random.randint(1, 10)
        return -10, duration
    elif current_cold_front_days > 0:
        # Cold front continuing
        return -10, current_cold_front_days - 1
    else:
        # No cold front
        return 0, 0


def handle_heat_wave(roll: int, current_heat_wave_days: int) -> Tuple[int, int]:
    """
    Check for heat wave and manage duration.

    Heat waves occur on a roll of 99 and last 10+1d10 days.

    Args:
        roll: Temperature roll (1-100)
        current_heat_wave_days: Days remaining in current heat wave (0 if none)

    Returns:
        Tuple of (temperature_modifier, days_remaining)
    """
    if roll == 99 and current_heat_wave_days == 0:
        # New heat wave starting
        duration = 10 + random.randint(1, 10)
        return 10, duration
    elif current_heat_wave_days > 0:
        # Heat wave continuing
        return 10, current_heat_wave_days - 1
    else:
        # No heat wave
        return 0, 0


def roll_temperature_with_special_events(
    season: str, province: str, cold_front_days: int = 0, heat_wave_days: int = 0
) -> Tuple[int, str, str, int, int, int]:
    """
    Roll for temperature including cold fronts and heat waves.

    Args:
        season: Season name
        province: Province name
        cold_front_days: Days remaining in current cold front
        heat_wave_days: Days remaining in current heat wave

    Returns:
        Tuple of (actual_temp, category, description, roll, cold_front_remaining, heat_wave_remaining)
    """
    roll = random.randint(1, 100)
    category, modifier = get_temperature_category_from_roll(roll)

    base_temp = get_province_base_temperature(province, season)
    actual_temp = base_temp + modifier

    # Handle cold fronts and heat waves
    cold_mod, cold_front_remaining = handle_cold_front(roll, cold_front_days)
    heat_mod, heat_wave_remaining = handle_heat_wave(roll, heat_wave_days)

    # Apply special modifiers
    actual_temp += cold_mod + heat_mod

    description = TEMPERATURE_DESCRIPTIONS.get(
        category, TEMPERATURE_DESCRIPTIONS["average"]
    )

    return (
        actual_temp,
        category,
        description,
        roll,
        cold_front_remaining,
        heat_wave_remaining,
    )


def apply_wind_chill(temperature: int, wind_strength: str) -> int:
    """
    Apply wind chill to temperature.

    Args:
        temperature: Actual temperature in Celsius
        wind_strength: Wind strength key

    Returns:
        Perceived temperature with wind chill applied
    """
    if wind_strength in ["light", "bracing"]:
        return temperature - 5
    elif wind_strength in ["strong", "very_strong"]:
        return temperature - 10
    else:
        return temperature


def get_temperature_description_text(temp: int, base_temp: int) -> str:
    """
    Get descriptive text for temperature relative to average.

    Args:
        temp: Actual temperature
        base_temp: Average temperature for season

    Returns:
        Descriptive text
    """
    diff = temp - base_temp

    if diff <= -15:
        return "Dangerously cold"
    elif diff <= -10:
        return "Very cold for the season"
    elif diff <= -5:
        return "Cooler than average"
    elif diff <= -2:
        return "Slightly cool"
    elif diff >= 15:
        return "Dangerously hot"
    elif diff >= 10:
        return "Very warm for the season"
    elif diff >= 5:
        return "Warmer than average"
    elif diff >= 2:
        return "Slightly warm"
    else:
        return "Comfortable for the season"


def get_wind_chill_note(wind_strength: str) -> str:
    """
    Get note about wind chill effect.

    Args:
        wind_strength: Wind strength key

    Returns:
        Wind chill note or empty string
    """
    if wind_strength in ["light", "bracing"]:
        return f" (feels 5°C colder due to {WIND_STRENGTH[wind_strength]} wind)"
    elif wind_strength in ["strong", "very_strong"]:
        return f" (feels 10°C colder due to {WIND_STRENGTH[wind_strength]} wind)"
    return ""
