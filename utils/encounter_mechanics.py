"""
River Encounter Mechanics Module

Handles encounter generation, dice rolling, calculations, and formatting
for the /river-encounter command.
"""

from typing import Dict, Tuple
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


def roll_encounter_type() -> Tuple[str, int]:
    """
    Roll for encounter type using 1d100.

    Returns:
        Tuple of (encounter_type, roll_value)
    """
    roll = roll_dice(1, 100)[0]
    encounter_type = get_encounter_type_from_roll(roll)
    return encounter_type, roll


def generate_encounter(encounter_type: str = None) -> Dict:
    """
    Generate a complete encounter with all details.

    Args:
        encounter_type: Optional specific type, otherwise rolls randomly

    Returns:
        Dictionary with complete encounter details:
        - type: encounter type
        - type_roll: the d100 roll for type
        - detail_roll: the d100 roll for specific encounter (if applicable)
        - flavor_text: cryptic player message
        - title: encounter name (for GM)
        - description: full description (for GM)
        - effects: list of effects (for GM)
        - mechanics: mechanical details (for GM)
        - cargo_loss: calculated cargo loss (for Cargo Shift accidents)
    """
    # Roll for type if not specified
    if encounter_type is None:
        encounter_type, type_roll = roll_encounter_type()
    else:
        # If type specified, we still need a roll value for display
        type_roll = None  # Will be determined from type
        if encounter_type == "positive":
            type_roll = 5  # Middle of range
        elif encounter_type == "coincidental":
            type_roll = 18
        elif encounter_type == "uneventful":
            type_roll = 50
        elif encounter_type == "harmful":
            type_roll = 90
        elif encounter_type == "accident":
            type_roll = 98

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
        if 41 <= detail_roll <= 50:
            cargo_loss_data = calculate_cargo_loss()
            encounter_data["cargo_loss"] = cargo_loss_data

    return encounter_data


def calculate_cargo_loss() -> Dict:
    """
    Calculate cargo loss for Cargo Shift accident.
    Formula: 10 + floor((1d100 + 5) / 10) * 10

    Returns:
        Dictionary with:
        - roll: the d100 roll
        - intermediate: the calculated intermediate value
        - encumbrance_lost: final encumbrance lost
    """
    cargo_roll = roll_dice(1, 100)[0]
    intermediate = (cargo_roll + 5) // 10
    encumbrance_lost = 10 + (intermediate * 10)

    return {
        "roll": cargo_roll,
        "intermediate": intermediate,
        "encumbrance_lost": encumbrance_lost,
    }


def format_test_requirement(test_data: Dict) -> str:
    """
    Format a test requirement for display.

    Args:
        test_data: Dict with 'name', 'difficulty', and optionally 'target'

    Returns:
        Formatted string like "Challenging (+0) Dodge Test (all crew)"
    """
    test_name = test_data.get("name", "Unknown")
    difficulty = test_data.get("difficulty", "")
    target = test_data.get("target", "")

    result = f"{difficulty} {test_name} Test" if difficulty else f"{test_name} Test"

    if target:
        result += f" ({target})"

    return result


def format_damage_result(damage: str, hits: int = 1) -> str:
    """
    Format damage for display.

    Args:
        damage: Damage value like "+5" or "1d10"
        hits: Number of hits (default 1)

    Returns:
        Formatted string like "1 hit for +5 Damage"
    """
    hit_text = "hit" if hits == 1 else "hits"
    return f"{hits} {hit_text} for {damage} Damage"


def get_encounter_emoji(encounter_type: str) -> str:
    """
    Get emoji for encounter type.

    Args:
        encounter_type: Type of encounter

    Returns:
        Emoji string
    """
    emoji_map = {
        "positive": "✨",
        "coincidental": "🎲",
        "uneventful": "😐",
        "harmful": "⚔️",
        "accident": "⚠️",
    }
    return emoji_map.get(encounter_type, "❓")


def get_severity_color(encounter_type: str) -> discord.Color:
    """
    Get embed color for encounter type.

    Args:
        encounter_type: Type of encounter

    Returns:
        Discord Color object
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
    Format encounter type name for display.

    Args:
        encounter_type: Type of encounter

    Returns:
        Formatted name
    """
    name_map = {
        "positive": "Positive",
        "coincidental": "Coincidental",
        "uneventful": "Uneventful",
        "harmful": "Harmful",
        "accident": "Accident",
    }
    return name_map.get(encounter_type, encounter_type.title())


def format_effects_list(effects: list) -> str:
    """
    Format effects list for display.

    Args:
        effects: List of effect strings

    Returns:
        Formatted bullet list
    """
    if not effects:
        return "No special effects"

    return "\n".join(f"• {effect}" for effect in effects)


def format_mechanics_summary(mechanics: Dict) -> str:
    """
    Format mechanics summary for quick reference.

    Args:
        mechanics: Mechanics dictionary

    Returns:
        Formatted summary string
    """
    if not mechanics:
        return "No special mechanics"

    summary_parts = []

    # Check for various mechanic types
    if "primary_test" in mechanics:
        test = mechanics["primary_test"]
        summary_parts.append(f"• Test: {test.get('name', 'Unknown')}")

    if "primary_failure" in mechanics:
        failure = mechanics["primary_failure"]
        if "damage" in failure:
            summary_parts.append(f"• Damage: {failure['damage']}")
        if "effect" in failure:
            summary_parts.append(f"• Effect: {failure['effect']}")

    if "secondary_test" in mechanics:
        test = mechanics["secondary_test"]
        summary_parts.append(f"• Secondary test: {test.get('name', 'Unknown')}")

    if "secondary_failure" in mechanics:
        failure = mechanics["secondary_failure"]
        if "effect" in failure:
            summary_parts.append(f"• Secondary effect: {failure['effect']}")

    if "damage_type" in mechanics:
        summary_parts.append(f"• Damage type: {mechanics['damage_type']}")

    if "immediate_effect" in mechanics:
        summary_parts.append(f"• Immediate: {mechanics['immediate_effect']}")

    return "\n".join(summary_parts) if summary_parts else "See full description"
