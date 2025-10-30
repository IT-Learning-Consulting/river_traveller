"""
Service layer for command business logic.

This package contains service classes that separate business logic from Discord
interaction code, making the codebase more testable and maintainable.

Services:
- RollService: Dice rolling and WFRP test mechanics
- BoatHandlingService: Boat handling test logic with skill selection
- EncounterService: River encounter generation
- CommandLogger: Centralized command logging to Discord channels
"""

from commands.services.roll_service import RollService, RollResult
from commands.services.boat_handling_service import (
    BoatHandlingService,
    BoatHandlingResult,
)
from commands.services.command_logger import CommandLogger, CommandLogEntry
from commands.services.encounter_service import EncounterService

__all__ = [
    "RollService",
    "RollResult",
    "BoatHandlingService",
    "BoatHandlingResult",
    "CommandLogger",
    "CommandLogEntry",
    "EncounterService",
]
