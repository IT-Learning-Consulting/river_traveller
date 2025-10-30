"""
Encounter Service for River Encounters.

This service wraps the encounter generation logic from utils.encounter_mechanics,
providing validation, error handling, and a clean interface for Discord commands.

Key responsibilities:
- Generate random river encounters with complete data
- Validate encounter type overrides
- Provide type-safe encounter data structures
- Handle invalid inputs gracefully

Design principles:
- No Discord imports (pure business logic)
- All exceptions clearly documented
- Type hints for all public methods
- Wraps existing encounter_mechanics utilities

Example usage:
    >>> service = EncounterService()
    >>> encounter = service.generate_encounter()
    >>> print(encounter["type"], encounter["title"])
    harmful Submerged Debris

    >>> # With specific type
    >>> accident = service.generate_encounter(encounter_type="accident")
    >>> print(accident["type"])
    accident
"""

from typing import Dict, Optional, List
from utils.encounter_mechanics import generate_encounter as _generate_encounter


class EncounterService:
    """
    Service for generating and validating river encounters.

    This service provides a validated interface to the encounter generation
    system, ensuring that all inputs are valid and all outputs contain
    expected data structures.
    """

    # Valid encounter types
    VALID_TYPES: List[str] = [
        "positive",
        "coincidental",
        "uneventful",
        "harmful",
        "accident",
    ]

    def generate_encounter(self, encounter_type: Optional[str] = None) -> Dict:
        """
        Generate a complete river encounter.

        If encounter_type is None, rolls randomly on d100 table.
        If encounter_type is specified, generates that specific type.

        Args:
            encounter_type: Optional encounter type. Must be one of:
                "positive", "coincidental", "uneventful", "harmful", "accident"
                If None, rolls randomly.

        Returns:
            Dict: Complete encounter data with keys:
                - type (str): Encounter type
                - type_roll (int): The d100 roll for type determination
                - detail_roll (Optional[int]): The d100 roll for specific encounter
                - flavor_text (str): Cryptic player-facing message
                - title (str): Encounter name (for GM)
                - description (str): Full encounter description (for GM)
                - effects (list): List of mechanical effects (for GM)
                - mechanics (Dict): Detailed mechanics (tests, damage) (for GM)
                - cargo_loss (Optional[Dict]): Cargo loss data (Cargo Shift only)

        Raises:
            ValueError: If encounter_type is not None and not in VALID_TYPES

        Example:
            >>> service = EncounterService()
            >>> encounter = service.generate_encounter()
            >>> print(encounter["type"])
            harmful

            >>> accident = service.generate_encounter("accident")
            >>> print(accident["type"])
            accident

            >>> # Invalid type raises ValueError
            >>> service.generate_encounter("invalid")
            ValueError: Invalid encounter type: 'invalid'. Must be one of: ...
        """
        # Validate encounter type if specified
        if encounter_type is not None:
            if encounter_type not in self.VALID_TYPES:
                valid_types_str = ", ".join(f"'{t}'" for t in self.VALID_TYPES)
                raise ValueError(
                    f"Invalid encounter type: '{encounter_type}'. "
                    f"Must be one of: {valid_types_str}"
                )

        # Generate encounter using utils function
        encounter_data = _generate_encounter(encounter_type=encounter_type)

        # Validate that required keys are present
        self._validate_encounter_data(encounter_data)

        return encounter_data

    def _validate_encounter_data(self, encounter_data: Dict) -> None:
        """
        Validate that encounter data contains required keys.

        Args:
            encounter_data: The encounter data dictionary to validate

        Raises:
            KeyError: If required keys are missing
        """
        required_keys = ["type", "type_roll", "flavor_text", "title", "description"]

        missing_keys = [key for key in required_keys if key not in encounter_data]

        if missing_keys:
            raise KeyError(
                f"Encounter data missing required keys: {', '.join(missing_keys)}"
            )

    def is_valid_encounter_type(self, encounter_type: str) -> bool:
        """
        Check if an encounter type string is valid.

        Args:
            encounter_type: The encounter type to check

        Returns:
            bool: True if valid, False otherwise

        Example:
            >>> service = EncounterService()
            >>> service.is_valid_encounter_type("harmful")
            True
            >>> service.is_valid_encounter_type("invalid")
            False
        """
        return encounter_type in self.VALID_TYPES

    def get_valid_types(self) -> List[str]:
        """
        Get list of valid encounter types.

        Returns:
            List[str]: List of valid encounter type strings

        Example:
            >>> service = EncounterService()
            >>> types = service.get_valid_types()
            >>> print(types)
            ['positive', 'coincidental', 'uneventful', 'harmful', 'accident']
        """
        return self.VALID_TYPES.copy()
