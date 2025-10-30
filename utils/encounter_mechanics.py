"""
River Encounter Mechanics Module

Handles encounter generation, dice rolling, calculations, and formatting
for the /river-encounter command.

Key Responsibilities:
    - Roll and generate random river encounters using d100 tables
    - Calculate cargo loss for Cargo Shift accidents
    - Format encounter data for player (flavor text) and GM (full details)
    - Provide display utilities (emoji, colors, formatting)

Design Principles:
    - Functional design: Pure functions for formatting and calculations
    - Separation of concerns: Generation vs formatting vs display
    - Data-driven: All encounter tables in db/encounter_data.py
    - Type safety: Full type hints for all functions

Encounter Types:
    - Positive (1-10): Beneficial encounters
    - Coincidental (11-25): Neutral encounters
    - Uneventful (26-75): Nothing happens
    - Harmful (76-95): Dangerous encounters
    - Accident (96-100): Boat accidents

Usage Example:
    >>> encounter = generate_encounter()
    >>> print(encounter['flavor_text'])  # For players
    'A strange mist rolls across the water...'
    >>> print(encounter['title'])  # For GM
    'Friendly Merchant'
"""

from typing import Dict, Optional, Tuple
import discord
from utils.wfrp_mechanics import roll_dice
from db.encounter_data import (
    get_encounter_type_from_roll,
    get_random_flavor_text,
    get_positive_encounter_from_roll,
    get_coincidental_encounter_from_roll,
    get_uneventful_encounter,
    get_harmful_encounter_from_roll,
    get_accident_from_roll,
)

# Encounter type roll ranges (for default roll values when type specified)
TYPE_ROLL_POSITIVE: int = 5
TYPE_ROLL_COINCIDENTAL: int = 18
TYPE_ROLL_UNEVENTFUL: int = 50
TYPE_ROLL_HARMFUL: int = 90
TYPE_ROLL_ACCIDENT: int = 98

# Cargo Shift accident range
CARGO_SHIFT_MIN: int = 41
CARGO_SHIFT_MAX: int = 50

# Cargo loss calculation constants
CARGO_LOSS_BASE: int = 10
CARGO_LOSS_DIVISOR: int = 10
CARGO_LOSS_ROLL_MODIFIER: int = 5
CARGO_LOSS_MULTIPLIER: int = 10

# Encounter type emoji
EMOJI_POSITIVE: str = "✨"
EMOJI_COINCIDENTAL: str = "🎲"
EMOJI_UNEVENTFUL: str = "😐"
EMOJI_HARMFUL: str = "⚔️"
EMOJI_ACCIDENT: str = "⚠️"
EMOJI_UNKNOWN: str = "❓"

# Default values
DEFAULT_TEST_NAME: str = "Unknown"
DEFAULT_HIT_COUNT: int = 1
DEFAULT_FALLBACK_MESSAGE: str = "See full description"
NO_EFFECTS_MESSAGE: str = "No special effects"
NO_MECHANICS_MESSAGE: str = "No special mechanics"


def roll_encounter_type() -> Tuple[str, int]:
    """
    Roll for encounter type using 1d100.

    Uses standard d100 encounter table ranges:
    - 1-10: Positive
    - 11-25: Coincidental
    - 26-75: Uneventful
    - 76-95: Harmful
    - 96-100: Accident

    Returns:
        Tuple[str, int]: (encounter_type, roll_value). Type is one of:
            "positive", "coincidental", "uneventful", "harmful", "accident"

    Example:
        >>> enc_type, roll = roll_encounter_type()
        >>> print(f"Rolled {roll}: {enc_type}")
        Rolled 87: harmful
    """
    roll = roll_dice(1, 100)[0]
    encounter_type = get_encounter_type_from_roll(roll)
    return encounter_type, roll


def generate_encounter(encounter_type: Optional[str] = None) -> Dict:
    """
    Generate a complete encounter with all details.

    Rolls for encounter type (if not specified), then generates specific
    encounter details including player flavor text and full GM information.
    Handles special cargo loss calculation for Cargo Shift accidents.

    Args:
        encounter_type: Optional specific type to generate. One of:
            "positive", "coincidental", "uneventful", "harmful", "accident".
            If None, rolls randomly on d100 table

    Returns:
        Dict: Complete encounter details with keys:
            - type (str): Encounter type
            - type_roll (int): The d100 roll for type determination
            - detail_roll (Optional[int]): The d100 roll for specific encounter
            - flavor_text (str): Cryptic player-facing message
            - title (str): Encounter name (for GM)
            - description (str): Full encounter description (for GM)
            - effects (list): List of mechanical effects (for GM)
            - mechanics (Dict): Detailed mechanics (tests, damage) (for GM)
            - cargo_loss (Optional[Dict]): Cargo loss data for Cargo Shift accidents

    Example:
        >>> # Random encounter
        >>> encounter = generate_encounter()
        >>> print(encounter['type'], encounter['title'])
        harmful Submerged Debris

        >>> # Specific encounter type
        >>> accident = generate_encounter("accident")
        >>> print(accident['type'])
        accident
    """
    # Roll for type if not specified
    if encounter_type is None:
        encounter_type, type_roll = roll_encounter_type()
    else:
        # If type specified, we still need a roll value for display
        type_roll = None  # Will be determined from type
        if encounter_type == "positive":
            type_roll = TYPE_ROLL_POSITIVE
        elif encounter_type == "coincidental":
            type_roll = TYPE_ROLL_COINCIDENTAL
        elif encounter_type == "uneventful":
            type_roll = TYPE_ROLL_UNEVENTFUL
        elif encounter_type == "harmful":
            type_roll = TYPE_ROLL_HARMFUL
        elif encounter_type == "accident":
            type_roll = TYPE_ROLL_ACCIDENT

    # Get flavor text for player
    flavor_text = get_random_flavor_text(encounter_type)

    # Build encounter data
    encounter_data = {
        "type": encounter_type,
        "type_roll": type_roll,
        "flavor_text": flavor_text,
    }

    # Get specific encounter details based on type
    if encounter_type == "uneventful":
        uneventful_data = get_uneventful_encounter()
        encounter_data.update(uneventful_data)
        encounter_data["detail_roll"] = None

    elif encounter_type == "positive":
        detail_roll = roll_dice(1, 100)[0]
        positive_data = get_positive_encounter_from_roll(detail_roll)
        encounter_data.update(positive_data)
        encounter_data["detail_roll"] = detail_roll

    elif encounter_type == "coincidental":
        detail_roll = roll_dice(1, 100)[0]
        coincidental_data = get_coincidental_encounter_from_roll(detail_roll)
        encounter_data.update(coincidental_data)
        encounter_data["detail_roll"] = detail_roll

    elif encounter_type == "harmful":
        detail_roll = roll_dice(1, 100)[0]
        harmful_data = get_harmful_encounter_from_roll(detail_roll)
        encounter_data.update(harmful_data)
        encounter_data["detail_roll"] = detail_roll

    elif encounter_type == "accident":
        detail_roll = roll_dice(1, 100)[0]
        accident_data = get_accident_from_roll(detail_roll)
        encounter_data.update(accident_data)
        encounter_data["detail_roll"] = detail_roll

        # Special handling for Cargo Shift (41-50)
        if CARGO_SHIFT_MIN <= detail_roll <= CARGO_SHIFT_MAX:
            cargo_loss_data = calculate_cargo_loss()
            encounter_data["cargo_loss"] = cargo_loss_data

    return encounter_data


def calculate_cargo_loss() -> Dict[str, int]:
    """
    Calculate cargo loss for Cargo Shift accident.

    Uses WFRP formula: 10 + floor((1d100 + 5) / 10) * 10
    Results in 20-120 encumbrance lost.

    Returns:
        Dict[str, int]: Cargo loss data with keys:
            - roll (int): The d100 roll (1-100)
            - intermediate (int): Calculated intermediate value ((roll+5)//10)
            - encumbrance_lost (int): Final encumbrance lost (20-120)

    Example:
        >>> # Simulated roll of 55
        >>> loss = calculate_cargo_loss()
        >>> # intermediate = (55+5)//10 = 6
        >>> # encumbrance = 10 + (6*10) = 70
        >>> print(f"Lost {loss['encumbrance_lost']} encumbrance")
        Lost 70 encumbrance
    """
    cargo_roll = roll_dice(1, 100)[0]
    intermediate = (cargo_roll + CARGO_LOSS_ROLL_MODIFIER) // CARGO_LOSS_DIVISOR
    encumbrance_lost = CARGO_LOSS_BASE + (intermediate * CARGO_LOSS_MULTIPLIER)

    return {
        "roll": cargo_roll,
        "intermediate": intermediate,
        "encumbrance_lost": encumbrance_lost,
    }


def format_test_requirement(test_data: Dict[str, str]) -> str:
    """
    Format a test requirement for display.

    Combines test name, difficulty, and target into readable format.
    Handles missing fields gracefully.

    Args:
        test_data: Dict with optional keys:
            - name (str): Test name (e.g., "Dodge", "Cool")
            - difficulty (str): Difficulty level (e.g., "Challenging (+0)")
            - target (str): Who takes test (e.g., "all crew", "helmsman")

    Returns:
        str: Formatted test requirement. Examples:
            - "Challenging (+0) Dodge Test (all crew)"
            - "Cool Test" (no difficulty or target)
            - "Unknown Test" (empty dict)

    Example:
        >>> test = {"name": "Dodge", "difficulty": "Challenging (+0)", "target": "all crew"}
        >>> print(format_test_requirement(test))
        Challenging (+0) Dodge Test (all crew)
    """
    test_name = test_data.get("name", DEFAULT_TEST_NAME)
    difficulty = test_data.get("difficulty", "")
    target = test_data.get("target", "")

    result = f"{difficulty} {test_name} Test" if difficulty else f"{test_name} Test"

    if target:
        result += f" ({target})"

    return result


def format_damage_result(damage: str, hits: int = DEFAULT_HIT_COUNT) -> str:
    """
    Format damage for display with correct pluralization.

    Args:
        damage: Damage value (e.g., "+5", "1d10", "2d10+6")
        hits: Number of hits (default: 1)

    Returns:
        str: Formatted damage string with correct singular/plural.
            Examples: "1 hit for +5 Damage", "3 hits for 1d10 Damage"

    Example:
        >>> print(format_damage_result("+5", 1))
        1 hit for +5 Damage
        >>> print(format_damage_result("1d10", 3))
        3 hits for 1d10 Damage
    """
    hit_text = "hit" if hits == 1 else "hits"
    return f"{hits} {hit_text} for {damage} Damage"


def get_encounter_emoji(encounter_type: str) -> str:
    """
    Get emoji for encounter type.

    Provides visual indicator for encounter severity and type in Discord embeds.

    Args:
        encounter_type: Type of encounter. One of:
            "positive", "coincidental", "uneventful", "harmful", "accident"

    Returns:
        str: Single emoji character:
            - ✨ for positive
            - 🎲 for coincidental
            - 😐 for uneventful
            - ⚔️ for harmful
            - ⚠️ for accident
            - ❓ for unknown types

    Example:
        >>> print(get_encounter_emoji("harmful"))
        ⚔️
        >>> print(get_encounter_emoji("unknown_type"))
        ❓
    """
    emoji_map = {
        "positive": EMOJI_POSITIVE,
        "coincidental": EMOJI_COINCIDENTAL,
        "uneventful": EMOJI_UNEVENTFUL,
        "harmful": EMOJI_HARMFUL,
        "accident": EMOJI_ACCIDENT,
    }
    return emoji_map.get(encounter_type, EMOJI_UNKNOWN)


def get_severity_color(encounter_type: str) -> discord.Color:
    """
    Get embed color for encounter type based on severity.

    Colors follow danger scale: green (safe) → red (dangerous).

    Args:
        encounter_type: Type of encounter. One of:
            "positive", "coincidental", "uneventful", "harmful", "accident"

    Returns:
        discord.Color: Color object for Discord embeds:
            - Green for positive
            - Blue for coincidental
            - Light grey for uneventful
            - Orange for harmful
            - Red for accident
            - Default (black) for unknown types

    Example:
        >>> color = get_severity_color("harmful")
        >>> embed = discord.Embed(title="Encounter", color=color)
    """
    color_map = {
        "positive": discord.Color.green(),
        "coincidental": discord.Color.blue(),
        "uneventful": discord.Color.light_grey(),
        "harmful": discord.Color.orange(),
        "accident": discord.Color.red(),
    }
    return color_map.get(encounter_type, discord.Color.default())


def format_encounter_type_name(encounter_type: str) -> str:
    """
    Format encounter type name for display with proper capitalization.

    Args:
        encounter_type: Type of encounter (lowercase internal format)

    Returns:
        str: Title-cased display name. Examples:
            - "positive" → "Positive"
            - "coincidental" → "Coincidental"
            - "unknown_type" → "Unknown_Type"

    Example:
        >>> print(format_encounter_type_name("harmful"))
        Harmful
        >>> print(format_encounter_type_name("custom_type"))
        Custom_Type
    """
    name_map = {
        "positive": "Positive",
        "coincidental": "Coincidental",
        "uneventful": "Uneventful",
        "harmful": "Harmful",
        "accident": "Accident",
    }
    return name_map.get(encounter_type, encounter_type.title())


def format_effects_list(effects: Optional[list]) -> str:
    """
    Format effects list for display as bullet points.

    Args:
        effects: List of effect strings, or None/empty

    Returns:
        str: Bullet-pointed list, or fallback message if empty/None.
            Examples:
            - "• Effect 1\n• Effect 2\n• Effect 3"
            - "No special effects" (if empty)

    Example:
        >>> effects = ["Crew must test Cool", "Boat takes 1d10 damage"]
        >>> print(format_effects_list(effects))
        • Crew must test Cool
        • Boat takes 1d10 damage

        >>> print(format_effects_list([]))
        No special effects
    """
    if not effects:
        return NO_EFFECTS_MESSAGE

    return "\n".join(f"• {effect}" for effect in effects)


def format_mechanics_summary(mechanics: Optional[Dict]) -> str:
    """
    Format mechanics summary for quick reference.

    Extracts key mechanical elements (tests, damage, effects) from complex
    mechanics dict and formats as bullet list. Provides GM with quick overview.

    Args:
        mechanics: Optional mechanics dictionary with possible keys:
            - primary_test: Dict with test details
            - primary_failure: Dict with damage/effect on test failure
            - secondary_test: Dict with secondary test details
            - secondary_failure: Dict with secondary failure effects
            - damage_type: String describing damage type
            - immediate_effect: String describing immediate effects

    Returns:
        str: Bullet-pointed summary or fallback message. Examples:
            - "• Test: Dodge\n• Damage: +5\n• Effect: Stunned"
            - "No special mechanics" (if empty)
            - "See full description" (if no recognized fields)

    Example:
        >>> mechanics = {
        ...     "primary_test": {"name": "Dodge"},
        ...     "primary_failure": {"damage": "+5"}
        ... }
        >>> print(format_mechanics_summary(mechanics))
        • Test: Dodge
        • Damage: +5
    """
    if not mechanics:
        return NO_MECHANICS_MESSAGE

    summary_parts = []

    # Check for various mechanic types
    if "primary_test" in mechanics:
        test = mechanics["primary_test"]
        summary_parts.append(f"• Test: {test.get('name', DEFAULT_TEST_NAME)}")

    if "primary_failure" in mechanics:
        failure = mechanics["primary_failure"]
        if "damage" in failure:
            summary_parts.append(f"• Damage: {failure['damage']}")
        if "effect" in failure:
            summary_parts.append(f"• Effect: {failure['effect']}")

    if "secondary_test" in mechanics:
        test = mechanics["secondary_test"]
        summary_parts.append(f"• Secondary test: {test.get('name', DEFAULT_TEST_NAME)}")

    if "secondary_failure" in mechanics:
        failure = mechanics["secondary_failure"]
        if "effect" in failure:
            summary_parts.append(f"• Secondary effect: {failure['effect']}")

    if "damage_type" in mechanics:
        summary_parts.append(f"• Damage type: {mechanics['damage_type']}")

    if "immediate_effect" in mechanics:
        summary_parts.append(f"• Immediate: {mechanics['immediate_effect']}")

    return "\n".join(summary_parts) if summary_parts else DEFAULT_FALLBACK_MESSAGE
