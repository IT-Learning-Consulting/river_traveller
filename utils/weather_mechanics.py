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

# Phase 2: Weather Event Constants
COLD_FRONT_TRIGGER_ROLL = 2
HEAT_WAVE_TRIGGER_ROLL = 99
COLD_FRONT_COOLDOWN_DAYS = 7
HEAT_WAVE_COOLDOWN_DAYS = 7
COLD_FRONT_TEMP_MODIFIER = -10
HEAT_WAVE_TEMP_MODIFIER = 10


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


def get_category_from_actual_temp(actual_temp: int, base_temp: int) -> str:
    """
    Determine temperature category based on difference from base temperature.

    Used during cold fronts/heat waves to categorize the final temperature
    after event modifiers and daily variation have been applied.

    Args:
        actual_temp: Final calculated temperature (°C)
        base_temp: Province/season base temperature (°C)

    Returns:
        Category string for display

    Examples:
        >>> get_category_from_actual_temp(6, 21)  # 15° below base
        'extremely_low'

        >>> get_category_from_actual_temp(11, 21)  # 10° below base
        'very_low'

        >>> get_category_from_actual_temp(18, 21)  # 3° below base
        'cool'
    """
    diff = actual_temp - base_temp

    if diff <= -15:
        return "extremely_low"
    elif diff <= -10:
        return "very_low"
    elif diff <= -6:
        return "low"
    elif diff <= -3:
        return "cool"
    elif diff <= 2:
        return "average"
    elif diff <= 5:
        return "warm"
    elif diff <= 9:
        return "high"
    elif diff <= 14:
        return "very_high"
    else:
        return "extremely_high"


def handle_cold_front(
    roll: int,
    current_cold_front_days: int,
    current_total_duration: int = 0,
    days_since_last_cold_front: int = 99,
    heat_wave_active: bool = False,
) -> Tuple[int, int, int]:
    """
    Check for cold front and manage duration with cooldown and mutual exclusivity.

    Cold fronts occur on a roll of 2 and last 1d5 days.
    Cannot trigger during cooldown period (7 days) or when heat wave is active.

    Args:
        roll: Temperature roll (1-100)
        current_cold_front_days: Days remaining in current cold front (0 if none)
        current_total_duration: Total duration of current cold front (0 if none)
        days_since_last_cold_front: Days since last cold front ended
        heat_wave_active: Whether a heat wave is currently active

    Returns:
        Tuple of (temperature_modifier, days_remaining, total_duration)
    """
    # If cold front is active, decrement and continue
    if current_cold_front_days > 0:
        return (
            COLD_FRONT_TEMP_MODIFIER,
            current_cold_front_days - 1,
            current_total_duration,
        )

    # Check if new cold front can trigger
    if roll == COLD_FRONT_TRIGGER_ROLL:
        # Block if heat wave is active (mutual exclusivity)
        if heat_wave_active:
            return 0, 0, 0

        # Block if still in cooldown period
        if days_since_last_cold_front < COLD_FRONT_COOLDOWN_DAYS:
            return 0, 0, 0

        # New cold front triggers!
        duration = random.randint(1, 5)  # 1d5 days
        return COLD_FRONT_TEMP_MODIFIER, duration, duration

    # No cold front
    return 0, 0, 0


def handle_heat_wave(
    roll: int,
    current_heat_wave_days: int,
    current_total_duration: int = 0,
    days_since_last_heat_wave: int = 99,
    cold_front_active: bool = False,
) -> Tuple[int, int, int]:
    """
    Check for heat wave and manage duration with cooldown and mutual exclusivity.

    Heat waves occur on a roll of 99 and last 10+1d10 days (11-20 days).
    Cannot trigger during cooldown period (7 days) or when cold front is active.

    Args:
        roll: Temperature roll (1-100)
        current_heat_wave_days: Days remaining in current heat wave (0 if none)
        current_total_duration: Total duration of current heat wave (0 if none)
        days_since_last_heat_wave: Days since last heat wave ended
        cold_front_active: Whether a cold front is currently active

    Returns:
        Tuple of (temperature_modifier, days_remaining, total_duration)
    """
    # If heat wave is active, decrement and continue
    if current_heat_wave_days > 0:
        return (
            HEAT_WAVE_TEMP_MODIFIER,
            current_heat_wave_days - 1,
            current_total_duration,
        )

    # Check if new heat wave can trigger
    if roll == HEAT_WAVE_TRIGGER_ROLL:
        # Block if cold front is active (mutual exclusivity)
        if cold_front_active:
            return 0, 0, 0

        # Block if still in cooldown period
        if days_since_last_heat_wave < HEAT_WAVE_COOLDOWN_DAYS:
            return 0, 0, 0

        # New heat wave triggers!
        duration = 10 + random.randint(1, 10)  # 10+1d10 days (11-20)
        return HEAT_WAVE_TEMP_MODIFIER, duration, duration

    # No heat wave
    return 0, 0, 0


def roll_temperature_with_special_events(
    season: str,
    province: str,
    cold_front_days: int = 0,
    cold_front_total: int = 0,
    heat_wave_days: int = 0,
    heat_wave_total: int = 0,
    days_since_last_cold_front: int = 99,
    days_since_last_heat_wave: int = 99,
) -> Tuple[int, str, str, int, int, int, int, int]:
    """
    Roll for temperature including cold fronts, heat waves, and daily variation.

    During active events, temperature still varies day-to-day but within
    the event's influence (e.g., cold front keeps it cold but not static).

    Args:
        season: Season name
        province: Province name
        cold_front_days: Days remaining in current cold front
        cold_front_total: Total duration of current cold front
        heat_wave_days: Days remaining in current heat wave
        heat_wave_total: Total duration of current heat wave
        days_since_last_cold_front: Days since last cold front ended
        days_since_last_heat_wave: Days since last heat wave ended

    Returns:
        Tuple of (actual_temp, category, description, roll,
                 cold_front_remaining, cold_front_total_new,
                 heat_wave_remaining, heat_wave_total_new)
    """
    # 1. Roll for daily temperature variation
    roll = random.randint(1, 100)
    original_roll = roll

    # 2. Suppress event triggers during active events (prevents nesting)
    if cold_front_days > 0 and roll == COLD_FRONT_TRIGGER_ROLL:
        roll = 3  # Treat as very_low instead of triggering new cold front
    if heat_wave_days > 0 and roll == HEAT_WAVE_TRIGGER_ROLL:
        roll = 98  # Treat as very_high instead of triggering new heat wave

    # 3. Get daily variation from temperature table
    category, daily_modifier = get_temperature_category_from_roll(roll)

    # 4. Get base temperature
    base_temp = get_province_base_temperature(province, season)

    # 5. Handle special events (cold fronts/heat waves)
    cold_mod, cold_front_remaining, cold_front_total_new = handle_cold_front(
        original_roll,  # Use original roll for trigger check
        cold_front_days,
        cold_front_total,
        days_since_last_cold_front,
        heat_wave_days > 0,  # heat_wave_active flag
    )

    heat_mod, heat_wave_remaining, heat_wave_total_new = handle_heat_wave(
        original_roll,  # Use original roll for trigger check
        heat_wave_days,
        heat_wave_total,
        days_since_last_heat_wave,
        cold_front_days > 0,  # cold_front_active flag
    )

    # 6. Calculate final temperature: base + event + daily_variation
    actual_temp = base_temp + cold_mod + heat_mod + daily_modifier

    # 7. Determine category based on final temperature (not base)
    final_category = get_category_from_actual_temp(actual_temp, base_temp)

    # 8. Build description
    description = TEMPERATURE_DESCRIPTIONS.get(
        final_category, TEMPERATURE_DESCRIPTIONS["average"]
    )

    # 9. Add special event information with day counters
    if cold_front_remaining > 0:
        days_elapsed = cold_front_total_new - cold_front_remaining + 1

        if days_elapsed == 1:
            # First day - add flavor text
            description += f"\n*❄️ Cold Front: Day {days_elapsed} of {cold_front_total_new} - Sky filled with flocks of emigrating birds*"
        elif cold_front_remaining == 1:
            # Final day
            description += f"\n*❄️ Cold Front: Day {days_elapsed} of {cold_front_total_new} (Final Day)*"
        else:
            # Middle days
            description += (
                f"\n*❄️ Cold Front: Day {days_elapsed} of {cold_front_total_new}*"
            )

    if heat_wave_remaining > 0:
        days_elapsed = heat_wave_total_new - heat_wave_remaining + 1

        if days_elapsed == 1:
            # First day
            description += (
                f"\n*🔥 Heat Wave: Day {days_elapsed} of {heat_wave_total_new}*"
            )
        elif heat_wave_remaining == 1:
            # Final day
            description += f"\n*🔥 Heat Wave: Day {days_elapsed} of {heat_wave_total_new} (Final Day)*"
        else:
            # Middle days
            description += (
                f"\n*🔥 Heat Wave: Day {days_elapsed} of {heat_wave_total_new}*"
            )

    return (
        actual_temp,
        final_category,
        description,
        original_roll,  # Return original roll for debugging/logging
        cold_front_remaining,
        cold_front_total_new,
        heat_wave_remaining,
        heat_wave_total_new,
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
