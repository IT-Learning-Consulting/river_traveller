"""
Character data and lookup utilities for the WFRP traveling bot.
"""

from typing import Dict, Any


# Character database
characters_data = {
    "anara": {
        "name": "Anara of Sānxiá",
        "species": "High Elf",
        "status": "Silver 1",
        "characteristics": {
            "WS": 55,
            "BS": 33,
            "S": 45,
            "T": 31,
            "I": 61,
            "AG": 47,
            "DEX": 39,
            "INT": 47,
            "WP": 48,
            "FEL": 32,
        },
        "trading_skills": {
            "Haggle": 35,
            "Charm": 33,
            "Gossip": 32,
            "Bribery": 32,
            "Intuition": 61,
        },
        "river_travelling_skills": {
            "Row": 45,
            "Swim": 48,
            "Navigation": 61,
            "Outdoor Survival": 47,
            "Perception": 76,
            "Dodge": 57,
        },
    },
    "emmerich": {
        "name": "Emmerich Falkenrath",
        "species": "Human",
        "status": "Brass 3",
        "characteristics": {
            "WS": 47,
            "BS": 25,
            "S": 37,
            "T": 34,
            "I": 40,
            "AG": 36,
            "DEX": 29,
            "INT": 45,
            "WP": 37,
            "FEL": 34,
        },
        "trading_skills": {
            "Haggle": 37,
            "Charm": 39,
            "Gossip": 42,
            "Bribery": 34,
            "Intuition": 45,
            "Evaluate": 50,
        },
        "river_travelling_skills": {
            "Row": 42,
            "Swim": 47,
            "Navigation": 45,
            "Outdoor Survival": 55,
            "Perception": 50,
            "Dodge": 41,
            "Lore (Geography)": 50,
            "Lore (Riverways)": None,
            "Sail": 30,
        },
    },
    "hildric": {
        "name": "Hildric Sokhlundt",
        "species": "Human",
        "status": "Brass 2",
        "characteristics": {
            "WS": 28,
            "BS": 30,
            "S": 32,
            "T": 36,
            "I": 42,
            "AG": 30,
            "DEX": 42,
            "INT": 42,
            "WP": 37,
            "FEL": 40,
        },
        "trading_skills": {
            "Haggle": 40,
            "Charm": 45,
            "Gossip": 45,
            "Bribery": 40,
            "Intuition": 48,
            "Evaluate": 45,
        },
        "river_travelling_skills": {
            "Row": 32,
            "Navigation": 42,
            "Outdoor Survival": 52,
            "Perception": 47,
            "Dodge": 30,
        },
    },
    "oktavian": {
        "name": "Oktavian Babel",
        "species": "Human",
        "status": "Silver 1",
        "characteristics": {
            "WS": 27,
            "BS": 34,
            "S": 30,
            "T": 40,
            "I": 40,
            "AG": 55,
            "DEX": 42,
            "INT": 31,
            "WP": 49,
            "FEL": 33,
        },
        "trading_skills": {
            "Haggle": 33,
            "Charm": 36,
            "Gossip": 38,
            "Bribery": 33,
            "Intuition": 50,
            "Evaluate": 32,
        },
        "river_travelling_skills": {
            "Row": 31,
            "Navigation": 40,
            "Outdoor Survival": 31,
            "Perception": 50,
            "Dodge": 65,
        },
    },
    "lupus": {
        "name": "Lupus Leonard Joachim Rohrig",
        "species": "Human",
        "status": "Gold 3",
        "characteristics": {
            "WS": 40,
            "BS": 34,
            "S": 33,
            "T": 30,
            "I": 40,
            "AG": 25,
            "DEX": 33,
            "INT": 30,
            "WP": 33,
            "FEL": 50,
        },
        "trading_skills": {
            "Haggle": 53,
            "Charm": 55,
            "Gossip": 53,
            "Bribery": 60,
            "Intuition": 40,
        },
        "river_travelling_skills": {
            "Row": 33,
            "Navigation": 40,
            "Outdoor Survival": 30,
            "Perception": 40,
            "Dodge": 25,
        },
    },
}


def get_character(character_key: str) -> Dict[str, Any]:
    """
    Get character data by key.

    Args:
        character_key: Character identifier (e.g., 'anara', 'emmerich')

    Returns:
        Character data dictionary

    Raises:
        ValueError: If character not found
    """
    char_key = character_key.lower().strip()
    if char_key not in characters_data:
        available = ", ".join(characters_data.keys())
        raise ValueError(
            f"Character '{character_key}' not found. Available: {available}"
        )
    return characters_data[char_key]


def get_available_characters() -> list:
    """Get list of available character keys."""
    return list(characters_data.keys())


def get_boat_handling_skill(character: Dict[str, Any]) -> tuple[str, int]:
    """
    Determine which boat handling skill to use for a character.

    Prefers Sail (advanced skill) if available, otherwise uses Row (basic skill).

    Args:
        character: Character data dictionary

    Returns:
        Tuple of (skill_name, skill_value)

    Raises:
        ValueError: If character has neither Row nor Sail skill
    """
    river_skills = character.get("river_travelling_skills", {})
    sail_skill = river_skills.get("Sail")
    row_skill = river_skills.get("Row")

    if sail_skill:
        return ("Sail", sail_skill)
    elif row_skill:
        return ("Row", row_skill)
    else:
        char_name = character.get("name", "Character")
        raise ValueError(f"{char_name} has no Row or Sail skill!")


def get_lore_riverways_bonus(character: Dict[str, Any]) -> int:
    """
    Calculate Lore (Riverways) bonus for boat handling.

    The bonus is the first digit of the skill value.

    Args:
        character: Character data dictionary

    Returns:
        Bonus value (0 if skill not present or None)

    Example:
        Lore (Riverways) 47 -> bonus of +4
        Lore (Riverways) None -> bonus of 0
    """
    river_skills = character.get("river_travelling_skills", {})
    lore_riverways = river_skills.get("Lore (Riverways)", 0)
    return lore_riverways // 10 if (lore_riverways and lore_riverways > 0) else 0
