"""
Weather Data Module for WFRP River Travel

Comprehensive weather configuration tables and lookup data for WFRP 4th Edition
river travel weather generation system. Contains all static weather reference data.

Key Responsibilities:
    - Wind strength/direction lookup tables with modifiers
    - Weather condition tables by season (dry, fair, rain, snow, blizzard)
    - Temperature ranges and province-specific base temperatures
    - Weather effect descriptions and mechanical consequences
    - Conversion functions for dice rolls to weather parameters

Data Categories:
    1. Wind System:
       - Strength: calm, light, bracing, strong, very_strong (d10 roll)
       - Direction: tailwind, sidewind, headwind (d10 roll)
       - Modifiers: Speed adjustments and tacking requirements
       - Very strong winds have critical effects (capsize, rigging damage)

    2. Weather Conditions:
       - Season-dependent d100 tables (spring, summer, autumn, winter)
       - Types: dry, fair, rain, downpour, snow, blizzard
       - Each has mechanical effects (visibility, test penalties, movement)

    3. Temperature System:
       - Province base temperatures by season (15 provinces, 4 seasons)
       - d100 roll determines temperature category (extremely_low to extremely_high)
       - Special events: cold fronts (10+1d10 days), heat waves (10+1d10 days)

    4. Weather Effects:
       - Visibility penalties (75 ft to near zero)
       - Combat modifiers (ranged weapons -10 to -20)
       - Movement restrictions (snow/blizzard)
       - Environmental hazards (gunpowder ruined, animals spooked)

Usage:
    # Generate wind conditions
    strength_roll = roll_d10()
    direction_roll = roll_d10()
    strength = get_wind_strength_from_roll(strength_roll)
    direction = get_wind_direction_from_roll(direction_roll)
    modifier, notes = WIND_MODIFIERS[(strength, direction)]

    # Generate weather type
    weather_roll = roll_d100()
    weather_type = get_weather_from_roll(season, weather_roll)
    effects = WEATHER_EFFECTS[weather_type]

    # Calculate temperature
    temp_roll = roll_d100()
    temp_category, temp_modifier = get_temperature_category_from_roll(temp_roll)
    base_temp = get_province_base_temperature(province, season)
    actual_temp = base_temp + temp_modifier

Design Principles:
    - All data is const (no runtime modification)
    - Complete d10/d100 coverage (no gaps in ranges)
    - Season-specific weather distributions (summer warmer, winter colder)
    - Province-specific temperature baselines (Kislev coldest, Stirland warmest)
    - Wind modifiers from WFRP 4e core rules
    - Very strong winds require special Boat Handling Tests
"""

from typing import List, Tuple

# =============================================================================
# MODULE-LEVEL CONSTANTS
# =============================================================================

# Dice Roll Validation
D10_MIN = 1
D10_MAX = 10
D100_MIN = 1
D100_MAX = 100

# Wind Strength Roll Ranges (d10)
WIND_STRENGTH_CALM_MAX = 2
WIND_STRENGTH_LIGHT_MAX = 4
WIND_STRENGTH_BRACING_MAX = 6
WIND_STRENGTH_STRONG_MAX = 8
# WIND_STRENGTH_VERY_STRONG = 9-10 (remaining rolls)

# Wind Direction Roll Ranges (d10)
WIND_DIRECTION_TAILWIND_MAX = 3
WIND_DIRECTION_SIDEWIND_MAX = 7
# WIND_DIRECTION_HEADWIND = 8-10 (remaining rolls)

# Wind Strength Names (lookup keys)
WIND_KEY_CALM = "calm"
WIND_KEY_LIGHT = "light"
WIND_KEY_BRACING = "bracing"
WIND_KEY_STRONG = "strong"
WIND_KEY_VERY_STRONG = "very_strong"

# Wind Direction Names (lookup keys)
WIND_KEY_TAILWIND = "tailwind"
WIND_KEY_SIDEWIND = "sidewind"
WIND_KEY_HEADWIND = "headwind"

# Weather Type Names (lookup keys)
WEATHER_KEY_DRY = "dry"
WEATHER_KEY_FAIR = "fair"
WEATHER_KEY_RAIN = "rain"
WEATHER_KEY_DOWNPOUR = "downpour"
WEATHER_KEY_SNOW = "snow"
WEATHER_KEY_BLIZZARD = "blizzard"

# Season Names (lookup keys)
SEASON_SPRING = "spring"
SEASON_SUMMER = "summer"
SEASON_AUTUMN = "autumn"
SEASON_WINTER = "winter"

# Temperature Category Names (lookup keys)
TEMP_EXTREMELY_LOW = "extremely_low"
TEMP_COLD_FRONT = "cold_front"
TEMP_VERY_LOW = "very_low"
TEMP_LOW = "low"
TEMP_AVERAGE = "average"
TEMP_HIGH = "high"
TEMP_VERY_HIGH = "very_high"
TEMP_HEAT_WAVE = "heat_wave"
TEMP_EXTREMELY_HIGH = "extremely_high"

# Temperature Modifiers (degrees Celsius)
TEMP_MODIFIER_EXTREMELY_LOW = -15
TEMP_MODIFIER_COLD_FRONT = -10
TEMP_MODIFIER_VERY_LOW = -10
TEMP_MODIFIER_LOW = -5
TEMP_MODIFIER_AVERAGE = 0
TEMP_MODIFIER_HIGH = 5
TEMP_MODIFIER_VERY_HIGH = 10
TEMP_MODIFIER_HEAT_WAVE = 10
TEMP_MODIFIER_EXTREMELY_HIGH = 15

# Weather Effects Dictionary Keys
WEATHER_EFFECT_NAME = "name"
WEATHER_EFFECT_DESCRIPTION = "description"
WEATHER_EFFECT_EFFECTS = "effects"

# Default Values
DEFAULT_SEASON = SEASON_SPRING
DEFAULT_WEATHER = WEATHER_KEY_FAIR
DEFAULT_PROVINCE = "reikland"
DEFAULT_TEMP_MODIFIER = TEMP_MODIFIER_AVERAGE


# Wind Strength Names
WIND_STRENGTH = {
    "calm": "Calm",
    "light": "Light",
    "bracing": "Bracing",
    "strong": "Strong",
    "very_strong": "Very Strong",
}

# Wind Direction Names
WIND_DIRECTION = {
    "tailwind": "Tailwind",
    "sidewind": "Sidewind",
    "headwind": "Headwind",
}

# Wind Modifiers: (strength, direction) -> (speed_modifier, special_notes)
WIND_MODIFIERS = {
    ("calm", "tailwind"): (
        "-10 penalty, 25% speed",
        "Boat drifts downstream at 25% of its normal movement rate; Boat Handling Tests are made with a penalty of -10",
    ),
    ("calm", "sidewind"): (
        "-10 penalty, 25% speed",
        "Boat drifts downstream at 25% of its normal movement rate; Boat Handling Tests are made with a penalty of -10",
    ),
    ("calm", "headwind"): (
        "-10 penalty, 25% speed",
        "Boat drifts downstream at 25% of its normal movement rate; Boat Handling Tests are made with a penalty of -10",
    ),
    ("light", "tailwind"): (
        "+5%",
        "The movement increase shown can only be achieved by tacking, which requires a successful Boat Handling Test",
    ),
    ("light", "sidewind"): ("—", "No modifier"),
    ("light", "headwind"): ("-5%", None),
    ("bracing", "tailwind"): (
        "+10%",
        "The movement increase shown can only be achieved by tacking, which requires a successful Boat Handling Test",
    ),
    ("bracing", "sidewind"): (
        "+5%",
        "The movement increase shown can only be achieved by tacking, which requires a successful Boat Handling Test",
    ),
    ("bracing", "headwind"): ("-10%", None),
    ("strong", "tailwind"): (
        "+20%",
        "The movement increase shown can only be achieved by tacking, which requires a successful Boat Handling Test",
    ),
    ("strong", "sidewind"): (
        "+10%",
        "The movement increase shown can only be achieved by tacking, which requires a successful Boat Handling Test",
    ),
    ("strong", "headwind"): ("-20%", None),
    ("very_strong", "tailwind"): (
        "+25%",
        "The movement increase shown can only be achieved by tacking, which requires a successful Boat Handling Test",
    ),
    ("very_strong", "sidewind"): (
        "—",
        "A successful Boat Handling Test must be made in order to take the sail down before the boat keels over. If the Test is failed, the sail and rigging is torn down as above, and the boat begins to take on water. A Boat Handling Test may be attempted every turn in order to right the boat; there is a cumulative 5% penalty for each failed Test. The boat sinks in a number of turns equal to its Toughness × 10 unless righted in that time",
    ),
    ("very_strong", "headwind"): (
        "-25%",
        "A successful Boat Handling Test is required to avoid damage to the sail and rigging. If the Test is failed, treat the result as a Critical Hit to the rigging (see below). The boat drifts out of control at 25% of its normal movement rate, modified according to the strength and direction of the wind; Boat Handling Tests to steer the boat are made with at -25",
    ),
}

# Weather Conditions by Season
WEATHER_RANGES = {
    "spring": [
        (1, 10, "dry"),
        (11, 30, "fair"),
        (31, 90, "rain"),
        (91, 95, "downpour"),
        (96, 100, "snow"),
    ],
    "summer": [
        (1, 40, "dry"),
        (41, 70, "fair"),
        (71, 95, "rain"),
        (96, 100, "downpour"),
    ],
    "autumn": [
        (1, 30, "dry"),
        (31, 60, "fair"),
        (61, 90, "rain"),
        (91, 98, "downpour"),
        (99, 100, "snow"),
    ],
    "winter": [
        (1, 10, "fair"),
        (11, 60, "rain"),
        (61, 65, "downpour"),
        (66, 90, "snow"),
        (91, 100, "blizzard"),
    ],
}

# Weather Effects
WEATHER_EFFECTS = {
    "dry": {
        "name": "Dry",
        "description": "Prolonged dry weather causes curtains of dust to blow across the road at the slightest breeze, obscuring vision and parching throats. Travel is easy, if uncomfortable.",
        "effects": ["-10 penalty to Forage Endeavours"],
    },
    "fair": {
        "name": "Fair",
        "description": "For once, the weather is being kind. Clear skies and comfortable conditions.",
        "effects": ["No weather-related hazards"],
    },
    "rain": {
        "name": "Rain",
        "description": "Rain can last anywhere from a few hours to a few days. Rain reduces visibility and makes ranged combat more difficult.",
        "effects": [
            "Visibility reduced to 75 ft or less",
            "-10 penalty to ranged weapons due to driving wind and rain",
        ],
    },
    "downpour": {
        "name": "Downpour",
        "description": "Terrible storms reduce visibility to near zero, making any sound below a shout impossible to hear. Everything and everyone not under cover is soaked through within minutes. Water streams off the road, carving deep gullies.",
        "effects": [
            "Visibility reduced to near zero",
            "-10 penalty on all physical Tests",
            "-20 penalty to ranged weapons",
            "Exposed gunpowder is immediately ruined",
            "Animals with the Skittish Trait may become spooked by lightning",
        ],
    },
    "snow": {
        "name": "Snow",
        "description": "A gentle snow covers the world in a blanket of white, making everything seem new and clean. It is undoubtedly beautiful, until one has to move through it.",
        "effects": [
            "Visibility reduced to 150 ft",
            "Movement faster than Walking impossible",
            "Average (+20) Endurance Test or gain a Fatigued Condition",
        ],
    },
    "blizzard": {
        "name": "Blizzard",
        "description": "Howling winds drive snow into every crevice. Visibility is nearly zero and exposed skin freezes quickly.",
        "effects": [
            "Visibility reduced to near zero",
            "Movement faster than Walking impossible",
            "Challenging (+0) Endurance Test or gain a Fatigued Condition",
            "-10 penalty on all physical Tests",
            "Animals with the Skittish Trait may panic",
        ],
    },
}

# Province Temperature Averages (°C) by Season
PROVINCE_TEMPERATURES = {
    "reikland": {"spring": 9, "summer": 21, "autumn": 11, "winter": 0},
    "nordland": {"spring": 7, "summer": 19, "autumn": 10, "winter": -1},
    "ostland": {"spring": 8, "summer": 21, "autumn": 10, "winter": -2},
    "middenland": {"spring": 7, "summer": 21, "autumn": 14, "winter": -2},
    "hochland": {"spring": 9, "summer": 23, "autumn": 12, "winter": -2},
    "talabecland": {"spring": 10, "summer": 22, "autumn": 13, "winter": -2},
    "ostermark": {"spring": 6, "summer": 19, "autumn": 13, "winter": -4},
    "stirland": {"spring": 7, "summer": 23, "autumn": 15, "winter": 4},
    "sylvania": {"spring": 6, "summer": 20, "autumn": 12, "winter": -2},
    "wissenland": {"spring": 7, "summer": 20, "autumn": 11, "winter": -2},
    "averland": {"spring": 11, "summer": 22, "autumn": 13, "winter": -1},
    "solland": {"spring": 9, "summer": 21, "autumn": 12, "winter": -1},
    "kislev": {"spring": -1, "summer": 15, "autumn": 7, "winter": -7},
    "wasteland": {"spring": 9, "summer": 19, "autumn": 12, "winter": 6},
    "border_princes": {"spring": 8, "summer": 21, "autumn": 11, "winter": 3},
}

# Temperature Ranges (d100)
TEMPERATURE_RANGES = [
    (1, 1, "extremely_low", -15),
    (2, 2, "cold_front", -10),
    (3, 10, "very_low", -10),
    (11, 25, "low", -5),
    (26, 75, "average", 0),
    (76, 90, "high", 5),
    (91, 98, "very_high", 10),
    (99, 99, "heat_wave", 10),
    (100, 100, "extremely_high", 15),
]

# Temperature Descriptions
TEMPERATURE_DESCRIPTIONS = {
    "extremely_low": "Extremely low: More than 15 degrees colder than average",
    "cold_front": "Cold Front: Temperatures remain 'very low' during 10+1d10 days. Sky is filled by flocks of emigrating birds",
    "very_low": "Very low: About 10 degrees colder than average",
    "low": "Low: About 5 degrees colder than average",
    "average": "Average for month and region",
    "high": "High: About 5 degrees warmer than average",
    "very_high": "Very high: About 10 degrees warmer than average",
    "heat_wave": "Heat Wave: Temperature remains 'very high' during 10+1d10 days. Both in summer and winter this can be disastrous",
    "extremely_high": "Extremely high: More than 15 degrees warmer than average",
}


def get_wind_strength_from_roll(roll: int) -> str:
    """
    Convert a d10 roll to wind strength category.

    Wind Strength Distribution (d10):
        - 1-2: Calm (20%) - Nearly no wind, boat drifts
        - 3-4: Light (20%) - Gentle breeze
        - 5-6: Bracing (20%) - Moderate wind, good sailing
        - 7-8: Strong (20%) - Heavy wind, requires skill
        - 9-10: Very Strong (20%) - Dangerous wind, capsize risk

    Args:
        roll: d10 result (1-10)

    Returns:
        Wind strength key: "calm", "light", "bracing", "strong", or "very_strong"

    Examples:
        >>> get_wind_strength_from_roll(1)
        'calm'
        >>> get_wind_strength_from_roll(5)
        'bracing'
        >>> get_wind_strength_from_roll(10)
        'very_strong'
    """
    if roll <= WIND_STRENGTH_CALM_MAX:
        return WIND_KEY_CALM
    elif roll <= WIND_STRENGTH_LIGHT_MAX:
        return WIND_KEY_LIGHT
    elif roll <= WIND_STRENGTH_BRACING_MAX:
        return WIND_KEY_BRACING
    elif roll <= WIND_STRENGTH_STRONG_MAX:
        return WIND_KEY_STRONG
    else:
        return WIND_KEY_VERY_STRONG


def get_wind_direction_from_roll(roll: int) -> str:
    """
    Convert a d10 roll to wind direction relative to travel.

    Wind Direction Distribution (d10):
        - 1-3: Tailwind (30%) - Wind from behind, speeds travel (requires tacking)
        - 4-7: Sidewind (40%) - Wind from side, moderate benefit (requires tacking)
        - 8-10: Headwind (30%) - Wind from front, slows travel

    Args:
        roll: d10 result (1-10)

    Returns:
        Wind direction key: "tailwind", "sidewind", or "headwind"

    Examples:
        >>> get_wind_direction_from_roll(2)
        'tailwind'
        >>> get_wind_direction_from_roll(5)
        'sidewind'
        >>> get_wind_direction_from_roll(9)
        'headwind'
    """
    if roll <= WIND_DIRECTION_TAILWIND_MAX:
        return WIND_KEY_TAILWIND
    elif roll <= WIND_DIRECTION_SIDEWIND_MAX:
        return WIND_KEY_SIDEWIND
    else:
        return WIND_KEY_HEADWIND


def get_weather_from_roll(season: str, roll: int) -> str:
    """
    Get weather type from d100 roll and season using seasonal probability tables.

    Weather probability varies by season:
        - Spring: Mostly rain (60%), some fair (20%), occasional snow (5%)
        - Summer: More dry/fair weather (70%), less rain (25%), rare downpour (5%)
        - Autumn: Balanced rain (30%), fair (30%), dry (30%), some downpour/snow (10%)
        - Winter: Mostly snow/rain (90%), little fair weather (10%), blizzards (10%)

    Args:
        season: Season name (spring, summer, autumn, winter) - case insensitive
        roll: d100 result (1-100)

    Returns:
        Weather type key: "dry", "fair", "rain", "downpour", "snow", or "blizzard"
        Returns "fair" as fallback if roll is out of range

    Examples:
        >>> get_weather_from_roll("spring", 50)
        'rain'
        >>> get_weather_from_roll("winter", 80)
        'snow'
        >>> get_weather_from_roll("summer", 10)
        'dry'
    """
    season_ranges = WEATHER_RANGES.get(season.lower(), WEATHER_RANGES[DEFAULT_SEASON])

    for min_roll, max_roll, weather_type in season_ranges:
        if min_roll <= roll <= max_roll:
            return weather_type

    return DEFAULT_WEATHER


def get_temperature_category_from_roll(roll: int) -> Tuple[str, int]:
    """
    Get temperature category and modifier from d100 roll.

    Temperature Distribution (d100):
        - 1: Extremely Low (-15°C) - Deadly cold (1%)
        - 2: Cold Front (-10°C, 10+1d10 days) - Extended cold period (1%)
        - 3-10: Very Low (-10°C) - Very cold (8%)
        - 11-25: Low (-5°C) - Cold (15%)
        - 26-75: Average (±0°C) - Normal temperature (50%)
        - 76-90: High (+5°C) - Warm (15%)
        - 91-98: Very High (+10°C) - Very warm (8%)
        - 99: Heat Wave (+10°C, 10+1d10 days) - Extended hot period (1%)
        - 100: Extremely High (+15°C) - Deadly heat (1%)

    Special Events (rolls 2 and 99):
        - Cold fronts and heat waves last 10+1d10 days (11-20 days)
        - These trigger special event mechanics in weather_mechanics.py
        - 7-day cooldown after event ends before new event can occur

    Args:
        roll: d100 result (1-100)

    Returns:
        Tuple of (category_key, temperature_modifier_celsius):
            - category_key: "extremely_low", "cold_front", "very_low", "low",
                          "average", "high", "very_high", "heat_wave", "extremely_high"
            - temperature_modifier: Integer modifier to add to base temperature (-15 to +15)
        Returns ("average", 0) as fallback if roll is out of range

    Examples:
        >>> get_temperature_category_from_roll(50)
        ('average', 0)
        >>> get_temperature_category_from_roll(2)
        ('cold_front', -10)
        >>> get_temperature_category_from_roll(99)
        ('heat_wave', 10)
    """
    for min_roll, max_roll, category, modifier in TEMPERATURE_RANGES:
        if min_roll <= roll <= max_roll:
            return category, modifier

    return TEMP_AVERAGE, DEFAULT_TEMP_MODIFIER


def get_province_base_temperature(province: str, season: str) -> int:
    """
    Get base temperature for a province and season in Celsius.

    Province Climate Zones:
        - Coldest: Kislev (winter average -7°C)
        - Cold: Nordland, Ostland, Middenland, Ostermark (winter -4°C to -1°C)
        - Temperate: Reikland, Talabecland, Wissenland (winter -2°C to 0°C)
        - Warm: Stirland, Wasteland, Border Princes (winter 3°C to 6°C)

    Temperature ranges from -7°C (Kislev winter) to 23°C (Hochland/Stirland summer).

    Args:
        province: Province name (case insensitive, spaces converted to underscores)
        season: Season name (spring, summer, autumn, winter) - case insensitive

    Returns:
        Base temperature in Celsius for the province/season combination
        Returns Reikland temperature if province not found (fallback to default)

    Examples:
        >>> get_province_base_temperature("reikland", "summer")
        21
        >>> get_province_base_temperature("kislev", "winter")
        -7
        >>> get_province_base_temperature("unknown_province", "spring")
        9  # Reikland spring default
    """
    province_key = province.lower().replace(" ", "_")
    province_data = PROVINCE_TEMPERATURES.get(
        province_key, PROVINCE_TEMPERATURES[DEFAULT_PROVINCE]
    )
    return province_data.get(season.lower(), 15)


def get_available_provinces() -> List[str]:
    """
    Get list of all available province names (lowercase with underscores).

    Returns all 15 provinces in the Empire and surrounding regions that have
    temperature data configured.

    Available Provinces:
        - Empire Core: reikland, nordland, ostland, middenland, hochland,
                      talabecland, ostermark, stirland, wissenland, averland
        - Empire Regions: sylvania, solland
        - Neighboring: kislev, wasteland, border_princes

    Returns:
        List of province keys (lowercase strings with underscores)

    Examples:
        >>> provinces = get_available_provinces()
        >>> len(provinces)
        15
        >>> 'reikland' in provinces
        True
        >>> 'kislev' in provinces
        True
    """
    return list(PROVINCE_TEMPERATURES.keys())
