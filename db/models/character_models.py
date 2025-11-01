"""
Character domain models.

This module provides frozen dataclasses for character data, replacing the previous
dict-based representations with type-safe immutable objects.

Domain Models:
- Characteristics: Core character stats (WS, BS, S, T, I, AG, DEX, INT, WP, FEL)
- Skills: Character skill categories (river_travelling_skills, trading_skills)
- Character: Complete character with characteristics, skills, and helper methods

Phase: 3.1 - Database Domain Models
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple


@dataclass(frozen=True)
class Characteristics:
    """
    Character characteristics (core stats).

    Uses uppercase field names to match WFRP convention.

    Attributes:
        WS: Weapon Skill
        BS: Ballistic Skill
        S: Strength
        T: Toughness
        I: Initiative
        AG: Agility
        DEX: Dexterity
        INT: Intelligence
        WP: Willpower
        FEL: Fellowship
    """

    WS: int
    BS: int
    S: int
    T: int
    I: int
    AG: int
    DEX: int
    INT: int
    WP: int
    FEL: int


@dataclass(frozen=True)
class Skills:
    """
    Character skill categories.

    Contains both river travelling skills and trading skills.

    Attributes:
        river_travelling_skills: Skills for river travel (Row, Sail, Navigation, etc.)
        trading_skills: Skills for trading and social interaction
    """

    river_travelling_skills: Dict[str, Optional[int]]
    trading_skills: Dict[str, Optional[int]]


@dataclass(frozen=True)
class Character:
    """
    Complete character data.

    Represents a character with all their stats, skills, and derived behaviors
    for river travel mechanics.

    Attributes:
        name: Character name
        species: Character species (Human, High Elf, etc.)
        status: Character status tier (Brass/Silver/Gold)
        characteristics: Character characteristics (stats)
        skills: Character skills (river_travelling_skills, trading_skills)
    """

    name: str
    species: str
    status: str
    characteristics: Characteristics
    skills: Skills

    def get_boat_handling_skill(self) -> Tuple[str, int]:
        """
        Get the boat handling skill name and level.

        Prefers Sail over Row when both are available.

        Returns:
            Tuple of (skill_name, skill_value) - "Sail" preferred, else "Row"

        Raises:
            ValueError: If character has no boat handling skills
        """
        sail = self.skills.river_travelling_skills.get("Sail")
        row = self.skills.river_travelling_skills.get("Row")

        if sail and sail > 0:
            return ("Sail", sail)
        elif row and row > 0:
            return ("Row", row)
        else:
            raise ValueError("No boat handling skills")

    def get_lore_riverways_bonus(self) -> int:
        """
        Get the Lore (Riverways) bonus.

        Returns:
            Bonus value (skill level // 10), or 0 if skill not present
        """
        lore_riverways = self.skills.river_travelling_skills.get("Lore (Riverways)", 0)
        if lore_riverways is None:
            return 0
        return lore_riverways // 10

    @classmethod
    def from_dict(cls, data: Dict) -> "Character":
        """
        Create Character from raw dictionary data.

        Converts legacy dict format to dataclass representation.

        Args:
            data: Raw character dict from database/config

        Returns:
            Character dataclass instance
        """
        characteristics = Characteristics(
            WS=data["characteristics"]["WS"],
            BS=data["characteristics"]["BS"],
            S=data["characteristics"]["S"],
            T=data["characteristics"]["T"],
            I=data["characteristics"]["I"],
            AG=data["characteristics"]["AG"],
            DEX=data["characteristics"]["DEX"],
            INT=data["characteristics"]["INT"],
            WP=data["characteristics"]["WP"],
            FEL=data["characteristics"]["FEL"],
        )

        skills = Skills(
            river_travelling_skills=data["river_travelling_skills"],
            trading_skills=data.get("trading_skills", {}),
        )

        return cls(
            name=data["name"],
            species=data["species"],
            status=data["status"],
            characteristics=characteristics,
            skills=skills,
        )
