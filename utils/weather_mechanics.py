"""
Weather mechanics for WFRP river travel.

Handles weather generation and calculations for multi-day river journeys.

Key Responsibilities:
    - Generate randomized weather conditions (wind, weather type, temperature)
    - Manage special weather events (cold fronts, heat waves)
    - Calculate wind chill and temperature perception
    - Track weather continuity across days
    - Apply seasonal and regional variations

Design Principles:
    - Random generation with WFRP-style dice rolls (d10, d100)
    - Day-to-day continuity: midnight wind continues to dawn
    - Special events with cooldowns and mutual exclusivity
    - Separation of data (db/weather_data) and logic (this module)

Weather Systems:
    1. Wind System:
       - 4 time periods per day (dawn, midday, dusk, midnight)
       - 10% chance of change per period
       - 5 strength levels: calm → light → bracing → strong → very strong
       - 10 directions (8 compass + headwind + tailwind)

    2. Temperature System:
       - Base temps by province/season (db/weather_data)
       - Daily variation: -15°C to +15°C from base
       - Special events: cold fronts (-10°C), heat waves (+10°C)
       - Wind chill: -5°C (light/bracing), -10°C (strong/very_strong)

    3. Special Events:
       - Cold Front: Roll 2, lasts 1d5 days, 7-day cooldown
       - Heat Wave: Roll 99, lasts 10+1d10 days, 7-day cooldown
       - Mutual exclusivity: Cannot overlap
       - Progression tracking: "Day X of Y" in descriptions

Usage Example:
    >>> # Generate first day
    >>> wind = generate_daily_wind()
    >>> weather = roll_weather_condition("spring")
    >>> temp, cat, desc, *event_data = roll_temperature_with_special_events(
    ...     "spring", "reikland"
    ... )

    >>> # Generate second day (continuity)
    >>> wind = generate_daily_wind_with_previous(wind[-1])
"""

import random
from typing import Tuple, List, Dict, Optional
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

# Wind change mechanics
WIND_CHANGE_ROLL: int = 1  # Wind changes on a roll of 1 (10% chance)
DIRECTION_CHANGE_ROLL: int = 1  # 50% chance direction changes with strength
WIND_CHANGE_DIRECTIONS: List[str] = ["stronger", "lighter"]
WIND_STRENGTH_ORDER: List[str] = ["calm", "light", "bracing", "strong", "very_strong"]

# Wind strength boundary rules
VERY_STRONG_MAX: str = "strong"  # Very strong can only decrease to strong
CALM_MIN: str = "light"  # Calm can only increase to light

# Special weather events
COLD_FRONT_TRIGGER_ROLL: int = 2
HEAT_WAVE_TRIGGER_ROLL: int = 99
COLD_FRONT_COOLDOWN_DAYS: int = 7
HEAT_WAVE_COOLDOWN_DAYS: int = 7
COLD_FRONT_TEMP_MODIFIER: int = -10
HEAT_WAVE_TEMP_MODIFIER: int = 10
COLD_FRONT_MIN_DURATION: int = 1
COLD_FRONT_MAX_DURATION: int = 5
HEAT_WAVE_BASE_DURATION: int = 10
HEAT_WAVE_BONUS_MIN: int = 1
HEAT_WAVE_BONUS_MAX: int = 10

# Temperature thresholds for categorization
TEMP_EXTREMELY_LOW: int = -15
TEMP_VERY_LOW: int = -10
TEMP_LOW: int = -6
TEMP_COOL: int = -3
TEMP_AVERAGE: int = 2
TEMP_WARM: int = 5
TEMP_HIGH: int = 9
TEMP_VERY_HIGH: int = 14

# Wind chill modifiers
WIND_CHILL_LIGHT_BRACING: int = -5
WIND_CHILL_STRONG_VERY_STRONG: int = -10
WIND_CHILL_WINDS_LIGHT: List[str] = ["light", "bracing"]
WIND_CHILL_WINDS_STRONG: List[str] = ["strong", "very_strong"]

# Temperature description thresholds
DESC_DANGEROUS_COLD: int = -15
DESC_VERY_COLD: int = -10
DESC_COOLER: int = -5
DESC_SLIGHTLY_COOL: int = -2
DESC_SLIGHTLY_WARM: int = 2
DESC_WARMER: int = 5
DESC_VERY_WARM: int = 10
DESC_DANGEROUS_HOT: int = 15

# Time periods
TIMES_OF_DAY: List[str] = ["Dawn", "Midday", "Dusk", "Midnight"]
TIME_DAWN: str = "Dawn"
TIME_MIDDAY: str = "Midday"
TIME_DUSK: str = "Dusk"
TIME_MIDNIGHT: str = "Midnight"

# Dice roll ranges
D10_MIN: int = 1
D10_MAX: int = 10
D100_MIN: int = 1
D100_MAX: int = 100
COIN_FLIP_MIN: int = 1
COIN_FLIP_MAX: int = 2

# Special event emoji
EMOJI_COLD_FRONT: str = "❄️"
EMOJI_HEAT_WAVE: str = "🔥"

# Event suppression values (to prevent nested events)
COLD_FRONT_SUPPRESSION_ROLL: int = 3  # Treat as very_low instead
HEAT_WAVE_SUPPRESSION_ROLL: int = 98  # Treat as very_high instead

# Default values
DEFAULT_MODIFIER: int = 0
DEFAULT_WIND_MODIFIER: str = "—"
DEFAULT_COOLDOWN: int = 99  # Large number to allow event triggers
DEFAULT_EVENT_DAYS: int = 0
DEFAULT_EVENT_TOTAL: int = 0

# Fallback keys for missing data
FALLBACK_WEATHER: str = "fair"
FALLBACK_TEMP_CATEGORY: str = "average"


def generate_wind_conditions() -> Tuple[str, str]:
    """
    Generate initial wind conditions using d10 tables.

    Rolls on standard WFRP wind tables for strength and direction.

    Returns:
        Tuple[str, str]: (strength_key, direction_key). Examples:
            - ("light", "north")
            - ("bracing", "tailwind")
            - ("calm", "calm")

    Example:
        >>> strength, direction = generate_wind_conditions()
        >>> print(f"{WIND_STRENGTH[strength]} {WIND_DIRECTION.get(direction, '')}")
        Light Headwind
    """
    strength_roll = random.randint(D10_MIN, D10_MAX)
    direction_roll = random.randint(D10_MIN, D10_MAX)

    strength = get_wind_strength_from_roll(strength_roll)
    direction = get_wind_direction_from_roll(direction_roll)

    return strength, direction


def check_wind_change(current_strength: str) -> Tuple[bool, str]:
    """
    Check if wind strength changes (10% chance per time period).

    Wind changes on a roll of 1 on d10. When it changes, 50/50 stronger or lighter.
    Boundaries: Very Strong can only decrease, Calm can only increase.

    Args:
        current_strength: Current wind strength key (from WIND_STRENGTH_ORDER)

    Returns:
        Tuple[bool, str]: (changed, new_strength). Examples:
            - (False, "light") - No change
            - (True, "bracing") - Changed from light to bracing

    Example:
        >>> changed, new_strength = check_wind_change("light")
        >>> if changed:
        ...     print(f"Wind changed to {new_strength}")
    """
    roll = random.randint(D10_MIN, D10_MAX)

    if roll != WIND_CHANGE_ROLL:
        return False, current_strength

    # Wind changes - 50% stronger, 50% lighter
    direction = random.choice(WIND_CHANGE_DIRECTIONS)

    current_index = WIND_STRENGTH_ORDER.index(current_strength)

    if direction == "stronger":
        if current_strength == "very_strong":
            # Very Strong can only go to Strong
            return True, VERY_STRONG_MAX
        new_index = min(current_index + 1, len(WIND_STRENGTH_ORDER) - 1)
    else:  # lighter
        if current_strength == "calm":
            # Calm can only go to Light
            return True, CALM_MIN
        new_index = max(current_index - 1, 0)

    return True, WIND_STRENGTH_ORDER[new_index]


def get_wind_modifiers(strength: str, direction: str) -> Dict[str, Optional[str]]:
    """
    Get wind modifiers for boat handling from lookup table.

    Retrieves speed modifier and special notes from WIND_MODIFIERS table.

    Args:
        strength: Wind strength key (e.g., "light", "bracing")
        direction: Wind direction key (e.g., "north", "tailwind")

    Returns:
        Dict[str, Optional[str]]: Dictionary with keys:
            - modifier (str): Speed modifier (e.g., "+10%", "-25%", "—")
            - notes (Optional[str]): Special conditions or None

    Example:
        >>> mods = get_wind_modifiers("moderate", "tailwind")
        >>> print(mods['modifier'])
        +10%
        >>> print(mods['notes'])
        Tacking required for speed bonus
    """
    modifier_data = WIND_MODIFIERS.get(
        (strength, direction), (DEFAULT_WIND_MODIFIER, None)
    )

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
    Roll for weather condition based on season using d100 table.

    Uses seasonal weather tables from db/weather_data. Different seasons
    have different probabilities for weather types.

    Args:
        season: Season name (spring, summer, autumn, winter)

    Returns:
        str: Weather type key (e.g., "fair", "rain", "snow", "blizzard")

    Example:
        >>> weather = roll_weather_condition("winter")
        >>> print(weather)
        snow  # More likely in winter
    """
    roll = random.randint(D100_MIN, D100_MAX)
    return get_weather_from_roll(season, roll)


def get_weather_effects(weather_type: str) -> Dict[str, any]:
    """
    Get weather effects and description from lookup table.

    Retrieves complete weather data including name, description, and mechanical effects.

    Args:
        weather_type: Weather type key (e.g., "rain", "snow", "blizzard")

    Returns:
        Dict[str, any]: Weather data with keys:
            - name (str): Display name
            - description (str): Flavor text
            - effects (List[str]): Mechanical effects list

    Example:
        >>> data = get_weather_effects("rain")
        >>> print(data['name'])
        Rain
        >>> print(data['effects'])
        ['Visibility reduced', 'Slippery surfaces']
    """
    return WEATHER_EFFECTS.get(weather_type, WEATHER_EFFECTS[FALLBACK_WEATHER])


def roll_temperature(season: str, province: str) -> Tuple[int, str, str]:
    """
    Roll for temperature using d100 table with provincial/seasonal base.

    Combines base temperature (province + season) with daily variation roll.
    Does NOT include special events (use roll_temperature_with_special_events for that).

    Args:
        season: Season name (spring, summer, autumn, winter)
        province: Province name (e.g., "reikland", "middenland")

    Returns:
        Tuple[int, str, str]: (actual_temp, category, description)
            - actual_temp: Final temperature in °C
            - category: Temperature category key
            - description: Descriptive text

    Example:
        >>> temp, cat, desc = roll_temperature("winter", "reikland")
        >>> print(f"{temp}°C - {desc}")
        -5°C - Cooler than average
    """
    roll = random.randint(D100_MIN, D100_MAX)
    category, modifier = get_temperature_category_from_roll(roll)

    base_temp = get_province_base_temperature(province, season)
    actual_temp = base_temp + modifier

    description = TEMPERATURE_DESCRIPTIONS.get(
        category, TEMPERATURE_DESCRIPTIONS[FALLBACK_TEMP_CATEGORY]
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

    if diff <= TEMP_EXTREMELY_LOW:
        return "extremely_low"
    elif diff <= TEMP_VERY_LOW:
        return "very_low"
    elif diff <= TEMP_LOW:
        return "low"
    elif diff <= TEMP_COOL:
        return "cool"
    elif diff <= TEMP_AVERAGE:
        return "average"
    elif diff <= TEMP_WARM:
        return "warm"
    elif diff <= TEMP_HIGH:
        return "high"
    elif diff <= TEMP_VERY_HIGH:
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
        duration = random.randint(
            COLD_FRONT_MIN_DURATION, COLD_FRONT_MAX_DURATION
        )  # 1d5 days
        return COLD_FRONT_TEMP_MODIFIER, duration, duration

    # No cold front
    return DEFAULT_MODIFIER, DEFAULT_EVENT_DAYS, DEFAULT_EVENT_TOTAL


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
            return DEFAULT_MODIFIER, DEFAULT_EVENT_DAYS, DEFAULT_EVENT_TOTAL

        # Block if still in cooldown period
        if days_since_last_heat_wave < HEAT_WAVE_COOLDOWN_DAYS:
            return DEFAULT_MODIFIER, DEFAULT_EVENT_DAYS, DEFAULT_EVENT_TOTAL

        # New heat wave triggers!
        duration = HEAT_WAVE_BASE_DURATION + random.randint(
            HEAT_WAVE_BONUS_MIN, HEAT_WAVE_BONUS_MAX
        )  # 10+1d10 days (11-20)
        return HEAT_WAVE_TEMP_MODIFIER, duration, duration

    # No heat wave
    return DEFAULT_MODIFIER, DEFAULT_EVENT_DAYS, DEFAULT_EVENT_TOTAL


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
    roll = random.randint(D100_MIN, D100_MAX)
    original_roll = roll

    # 2. Suppress event triggers during active events (prevents nesting)
    if cold_front_days > 0 and roll == COLD_FRONT_TRIGGER_ROLL:
        roll = COLD_FRONT_SUPPRESSION_ROLL  # Treat as very_low instead of triggering new cold front
    if heat_wave_days > 0 and roll == HEAT_WAVE_TRIGGER_ROLL:
        roll = HEAT_WAVE_SUPPRESSION_ROLL  # Treat as very_high instead of triggering new heat wave

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
            description += f"\n*{EMOJI_COLD_FRONT} Cold Front: Day {days_elapsed} of {cold_front_total_new} - Sky filled with flocks of emigrating birds*"
        elif cold_front_remaining == 1:
            # Final day
            description += f"\n*{EMOJI_COLD_FRONT} Cold Front: Day {days_elapsed} of {cold_front_total_new} (Final Day)*"
        else:
            # Middle days
            description += f"\n*{EMOJI_COLD_FRONT} Cold Front: Day {days_elapsed} of {cold_front_total_new}*"

    if heat_wave_remaining > 0:
        days_elapsed = heat_wave_total_new - heat_wave_remaining + 1

        if days_elapsed == 1:
            # First day
            description += f"\n*{EMOJI_HEAT_WAVE} Heat Wave: Day {days_elapsed} of {heat_wave_total_new}*"
        elif heat_wave_remaining == 1:
            # Final day
            description += f"\n*{EMOJI_HEAT_WAVE} Heat Wave: Day {days_elapsed} of {heat_wave_total_new} (Final Day)*"
        else:
            # Middle days
            description += f"\n*{EMOJI_HEAT_WAVE} Heat Wave: Day {days_elapsed} of {heat_wave_total_new}*"

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
    Apply wind chill modifier to temperature based on wind strength.

    Wind chill makes it feel colder:
    - Light/Bracing winds: -5°C
    - Strong/Very Strong winds: -10°C
    - Calm winds: No effect

    Args:
        temperature: Actual temperature in Celsius
        wind_strength: Wind strength key from WIND_STRENGTH_ORDER

    Returns:
        int: Perceived temperature with wind chill applied

    Example:
        >>> apply_wind_chill(10, "light")
        5  # Feels 5°C colder
        >>> apply_wind_chill(10, "strong")
        0  # Feels 10°C colder
        >>> apply_wind_chill(10, "calm")
        10  # No wind chill
    """
    if wind_strength in WIND_CHILL_WINDS_LIGHT:
        return temperature + WIND_CHILL_LIGHT_BRACING
    elif wind_strength in WIND_CHILL_WINDS_STRONG:
        return temperature + WIND_CHILL_STRONG_VERY_STRONG
    else:
        return temperature


def get_temperature_description_text(temp: int, base_temp: int) -> str:
    """
    Get descriptive text for temperature relative to seasonal average.

    Describes how the temperature feels compared to normal for the season.

    Args:
        temp: Actual temperature in °C
        base_temp: Average temperature for season/province in °C

    Returns:
        str: Descriptive text. Examples:
            - "Dangerously cold" (15+ degrees below average)
            - "Comfortable for the season" (near average)
            - "Dangerously hot" (15+ degrees above average)

    Example:
        >>> get_temperature_description_text(5, 20)
        'Very cold for the season'
        >>> get_temperature_description_text(21, 20)
        'Slightly warm'
    """
    diff = temp - base_temp

    if diff <= DESC_DANGEROUS_COLD:
        return "Dangerously cold"
    elif diff <= DESC_VERY_COLD:
        return "Very cold for the season"
    elif diff <= DESC_COOLER:
        return "Cooler than average"
    elif diff <= DESC_SLIGHTLY_COOL:
        return "Slightly cool"
    elif diff >= DESC_DANGEROUS_HOT:
        return "Dangerously hot"
    elif diff >= DESC_VERY_WARM:
        return "Very warm for the season"
    elif diff >= DESC_WARMER:
        return "Warmer than average"
    elif diff >= DESC_SLIGHTLY_WARM:
        return "Slightly warm"
    else:
        return "Comfortable for the season"


def get_wind_chill_note(wind_strength: str) -> str:
    """
    Get note about wind chill effect for display.

    Creates descriptive text explaining wind chill perception.

    Args:
        wind_strength: Wind strength key from WIND_STRENGTH_ORDER

    Returns:
        str: Wind chill note with temperature effect, or empty string if no effect

    Example:
        >>> get_wind_chill_note("light")
        ' (feels 5°C colder due to Light wind)'
        >>> get_wind_chill_note("strong")
        ' (feels 10°C colder due to Strong wind)'
        >>> get_wind_chill_note("calm")
        ''
    """
    if wind_strength in WIND_CHILL_WINDS_LIGHT:
        return f" (feels {abs(WIND_CHILL_LIGHT_BRACING)}°C colder due to {WIND_STRENGTH[wind_strength]} wind)"
    elif wind_strength in WIND_CHILL_WINDS_STRONG:
        return f" (feels {abs(WIND_CHILL_STRONG_VERY_STRONG)}°C colder due to {WIND_STRENGTH[wind_strength]} wind)"
    return ""
