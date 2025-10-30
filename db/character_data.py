"""
Character data and lookup utilities for the WFRP traveling bot.

Contains player character profiles with complete statistics, skills, and
characteristics for the traveling party.

Key Responsibilities:
    - Store complete character data (characteristics, skills, status)
    - Provide lookup functions for character retrieval
    - Calculate derived values (boat handling skills, lore bonuses)
    - Validate character existence and skill availability

Data Structure:
    Each character entry contains:
    - name: Full character name
    - species: Character race (Human, High Elf, etc.)
    - status: WFRP social standing (Brass/Silver/Gold tier + number)
    - characteristics: 10 core WFRP characteristics (WS, BS, S, T, I, AG, DEX, INT, WP, FEL)
    - trading_skills: Skills used for commerce and social interaction
    - river_travelling_skills: Skills used for river travel and navigation

Skills of Note:
    - Row: Basic boat handling (all characters have this)
    - Sail: Advanced boat handling (preferred if available)
    - Lore (Riverways): Provides bonus to boat handling tests
    - Navigation, Perception, Outdoor Survival: Key travel skills

Usage Example:
    >>> char = get_character("anara")
    >>> print(char['name'])
    Anara of Sānxiá

    >>> skill, value = get_boat_handling_skill(char)
    >>> print(f"{skill}: {value}")
    Row: 45

    >>> bonus = get_lore_riverways_bonus(char)
    >>> print(f"Lore bonus: +{bonus}")
    Lore bonus: +0
"""

from typing import Dict, Any, Tuple, List

# Skill name constants
SKILL_SAIL: str = "Sail"
SKILL_ROW: str = "Row"
SKILL_LORE_RIVERWAYS: str = "Lore (Riverways)"

# Character data keys
KEY_NAME: str = "name"
KEY_RIVER_SKILLS: str = "river_travelling_skills"

# Lore bonus calculation
LORE_TENS_DIVISOR: int = 10
MIN_LORE_VALUE: int = 0
DEFAULT_BONUS: int = 0


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
    Get character data by key (case-insensitive).

    Retrieves complete character profile including characteristics,
    skills, and metadata.

    Args:
        character_key: Character identifier (case-insensitive).
            Valid keys: 'anara', 'emmerich', 'hildric', 'oktavian', 'lupus'

    Returns:
        Dict[str, Any]: Complete character data dictionary with keys:
            - name (str): Full character name
            - species (str): Character race
            - status (str): Social standing
            - characteristics (Dict): 10 core stats
            - trading_skills (Dict): Commerce skills
            - river_travelling_skills (Dict): Travel skills

    Raises:
        ValueError: If character_key not found in database. Error message
            includes list of available character keys

    Example:
        >>> char = get_character("ANARA")
        >>> print(char['name'])
        Anara of Sānxiá
        >>> print(char['characteristics']['I'])
        61
    """
    char_key = character_key.lower().strip()
    if char_key not in characters_data:
        available = ", ".join(characters_data.keys())
        raise ValueError(
            f"Character '{character_key}' not found. Available: {available}"
        )
    return characters_data[char_key]


def get_available_characters() -> list:
    """
    Get list of available character keys.

    Returns:
        list: Character identifier keys that can be used with get_character().
            Example: ['anara', 'emmerich', 'hildric', 'oktavian', 'lupus']

    Example:
        >>> chars = get_available_characters()
        >>> print(f"Available characters: {', '.join(chars)}")
        Available characters: anara, emmerich, hildric, oktavian, lupus
    """
    return list(characters_data.keys())


def get_boat_handling_skill(character: Dict[str, Any]) -> tuple[str, int]:
    """
    Determine which boat handling skill to use for a character.

    WFRP boat handling uses either Row (basic) or Sail (advanced). This
    function selects the appropriate skill, preferring Sail if available.

    Priority:
    1. Sail (advanced boat handling skill)
    2. Row (basic boat handling skill)

    Args:
        character: Complete character data dictionary from get_character()

    Returns:
        tuple[str, int]: (skill_name, skill_value)
            - skill_name: Either "Sail" or "Row"
            - skill_value: Character's skill percentage (e.g., 45)

    Raises:
        ValueError: If character has neither Row nor Sail skill

    Example:
        >>> char = get_character("emmerich")
        >>> skill, value = get_boat_handling_skill(char)
        >>> print(f"{skill}: {value}")
        Sail: 30

        >>> char = get_character("anara")
        >>> skill, value = get_boat_handling_skill(char)
        >>> print(f"{skill}: {value}")
        Row: 45
    """
    river_skills = character.get(KEY_RIVER_SKILLS, {})
    sail_skill = river_skills.get(SKILL_SAIL)
    row_skill = river_skills.get(SKILL_ROW)

    if sail_skill:
        return (SKILL_SAIL, sail_skill)
    elif row_skill:
        return (SKILL_ROW, row_skill)
    else:
        char_name = character.get(KEY_NAME, "Character")
        raise ValueError(f"{char_name} has no Row or Sail skill!")


def get_lore_riverways_bonus(character: Dict[str, Any]) -> int:
    """
    Calculate Lore (Riverways) bonus for boat handling tests.

    WFRP specialty skill bonus: The tens digit of Lore (Riverways) provides
    a bonus to related boat handling tests.

    Calculation: bonus = skill_value // 10
    - Lore (Riverways) 47 → bonus +4
    - Lore (Riverways) 52 → bonus +5
    - Lore (Riverways) None → bonus 0

    Args:
        character: Complete character data dictionary from get_character()

    Returns:
        int: Bonus value (0 if skill not present or None or 0)

    Example:
        >>> char = get_character("emmerich")
        >>> # Emmerich has Lore (Riverways): None
        >>> bonus = get_lore_riverways_bonus(char)
        >>> print(bonus)
        0

        >>> # If a character had Lore (Riverways) 47:
        >>> # bonus would be 47 // 10 = 4
    """
    river_skills = character.get(KEY_RIVER_SKILLS, {})
    lore_riverways = river_skills.get(SKILL_LORE_RIVERWAYS, MIN_LORE_VALUE)
    return (
        lore_riverways // LORE_TENS_DIVISOR
        if (lore_riverways and lore_riverways > MIN_LORE_VALUE)
        else DEFAULT_BONUS
    )
