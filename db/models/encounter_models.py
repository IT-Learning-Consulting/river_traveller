"""
Encounter Domain Models

Dataclasses for river encounter data from encounter_data.py.
Provides type-safe alternatives to anonymous dicts.
"""

from dataclasses import dataclass
from typing import Optional, Dict, List, Any


@dataclass(frozen=True)
class Encounter:
    """
    Represents a river encounter with flavor text and mechanical details.

    Attributes:
        title: Encounter name (e.g., "Experienced Guide", "River Pirate Ambush")
        description: Full GM description of the encounter
        effects: List of mechanical effects or narrative outcomes
        mechanics: Optional dictionary with mechanical details (bonuses, damage, tests, etc.)
        roll: The d100 roll that generated this encounter
        encounter_type: Type of encounter (positive, harmful, accident, etc.)
    """
    title: str
    description: str
    effects: List[str]
    mechanics: Optional[Dict[str, Any]]
    roll: int
    encounter_type: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any], encounter_type: str) -> "Encounter":
        """
        Create Encounter from dictionary (for backward compatibility).

        Args:
            data: Dictionary with encounter data
            encounter_type: Type of encounter (positive, harmful, etc.)

        Returns:
            Encounter dataclass instance
        """
        return cls(
            title=data["title"],
            description=data["description"],
            effects=data["effects"],
            mechanics=data.get("mechanics"),
            roll=data.get("roll", 0),
            encounter_type=encounter_type,
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Encounter to dictionary (for backward compatibility).

        Returns:
            Dictionary with encounter data
        """
        return {
            "title": self.title,
            "description": self.description,
            "effects": self.effects,
            "mechanics": self.mechanics,
            "roll": self.roll,
        }
