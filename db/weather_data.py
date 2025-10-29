"""
Weather data module for WFRP river travel.
Contains all weather-related tables and constants.
"""

from typing import List, Tuple


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
    Convert a d10 roll to wind strength.

    Args:
        roll: d10 result (1-10)

    Returns:
        Wind strength key (calm, light, bracing, strong, very_strong)
    """
    if roll <= 2:
        return "calm"
    elif roll <= 4:
        return "light"
    elif roll <= 6:
        return "bracing"
    elif roll <= 8:
        return "strong"
    else:
        return "very_strong"


def get_wind_direction_from_roll(roll: int) -> str:
    """
    Convert a d10 roll to wind direction.

    Args:
        roll: d10 result (1-10)

    Returns:
        Wind direction key (tailwind, sidewind, headwind)
    """
    if roll <= 3:
        return "tailwind"
    elif roll <= 7:
        return "sidewind"
    else:
        return "headwind"


def get_weather_from_roll(season: str, roll: int) -> str:
    """
    Get weather type from d100 roll and season.

    Args:
        season: Season name (spring, summer, autumn, winter)
        roll: d100 result (1-100)

    Returns:
        Weather type key
    """
    season_ranges = WEATHER_RANGES.get(season.lower(), WEATHER_RANGES["spring"])

    for min_roll, max_roll, weather_type in season_ranges:
        if min_roll <= roll <= max_roll:
            return weather_type

    return "fair"


def get_temperature_category_from_roll(roll: int) -> Tuple[str, int]:
    """
    Get temperature category and modifier from d100 roll.

    Args:
        roll: d100 result (1-100)

    Returns:
        Tuple of (category_key, temperature_modifier)
    """
    for min_roll, max_roll, category, modifier in TEMPERATURE_RANGES:
        if min_roll <= roll <= max_roll:
            return category, modifier

    return "average", 0


def get_province_base_temperature(province: str, season: str) -> int:
    """
    Get base temperature for a province and season.

    Args:
        province: Province name
        season: Season name

    Returns:
        Base temperature in Celsius
    """
    province_key = province.lower().replace(" ", "_")
    province_data = PROVINCE_TEMPERATURES.get(
        province_key, PROVINCE_TEMPERATURES["reikland"]
    )
    return province_data.get(season.lower(), 15)


def get_available_provinces() -> List[str]:
    """Get list of all available province names."""
    return [name.replace("_", " ").title() for name in PROVINCE_TEMPERATURES.keys()]
