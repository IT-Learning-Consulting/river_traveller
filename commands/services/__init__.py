"""
Command Services - Business logic extracted from command modules.

This package contains service classes that encapsulate business logic,
making it testable without Discord dependencies.

Services:
    - RollService: Dice rolling and WFRP skill tests
    - CommandLogger: Centralized command logging to Discord channels

Usage:
    from commands.services.roll_service import RollService, RollResult
    from commands.services.command_logger import CommandLogger
"""

from commands.services.roll_service import RollService, RollResult
from commands.services.command_logger import CommandLogger

__all__ = [
    "RollService",
    "RollResult",
    "CommandLogger",
]
