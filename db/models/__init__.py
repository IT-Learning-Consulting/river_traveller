"""
Database Domain Models - Typed dataclasses for database entities.

This package provides immutable dataclasses that replace Dict[str, Any]
throughout the database layer, providing type safety and clear data contracts.
"""

from db.models.character_models import Character, Characteristics, Skills
from db.models.weather_models import (
    WindCondition,
    WindTimeline,
    TemperatureData,
    SpecialEvent,
    DailyWeather,
    JourneyState,
    StageWeather,
)

__all__ = [
    "Character",
    "Characteristics",
    "Skills",
    "WindCondition",
    "WindTimeline",
    "TemperatureData",
    "SpecialEvent",
    "DailyWeather",
    "JourneyState",
    "StageWeather",
]
