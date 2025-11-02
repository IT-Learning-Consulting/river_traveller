"""
Weather Impact - Structured weather modifier data.

This module defines the WeatherImpact dataclass that encapsulates
all weather-related modifiers for boat handling tests. It replaces
the untyped dictionaries previously returned by modifier_calculator.

Design Principles:
    - Type safety: All fields are properly typed
    - Immutability: Frozen dataclass prevents accidental modification
    - Documentation: Clear field descriptions for all attributes
    - Completeness: Contains all weather modifier information

Usage:
    >>> from utils.weather_impact import WeatherImpact
    >>> impact = WeatherImpact(
    ...     speed_percent=10,
    ...     boat_penalty=0,
    ...     wind_strength="moderate",
    ...     wind_direction="tailwind",
    ...     requires_tacking=True,
    ...     requires_test=False,
    ...     weather_effects=["No hazards"],
    ...     wind_notes="Tacking required for speed bonus",
    ...     weather_name="Clear",
    ...     day_number=1
    ... )
    >>> print(f"Speed modifier: {impact.speed_percent}%")
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class WeatherImpact:
    """
    Structured weather impact data for boat handling tests.

    Contains all weather-related modifiers, conditions, and descriptive
    information needed for boat handling tests and journey display.

    Attributes:
        speed_percent: Movement speed modifier percentage (-25 to +25)
        boat_penalty: Boat Handling test penalty (typically -10 or 0)
        wind_strength: Raw wind strength key (e.g., "light", "moderate", "strong")
        wind_direction: Raw wind direction key (e.g., "tailwind", "headwind")
        wind_strength_display: Formatted wind strength for display (e.g., "Light")
        wind_direction_display: Formatted wind direction for display (e.g., "Tailwind")
        requires_tacking: Whether tacking is required for speed bonus
        requires_test: Whether special Boat Handling test is required
        weather_effects: List of active weather effect descriptions
        wind_notes: Additional wind condition notes (e.g., "Calm: -10 penalty")
        weather_name: Weather type display name (e.g., "Clear", "Heavy Rain")
        day_number: Current journey day number

    Example:
        >>> impact = WeatherImpact(
        ...     speed_percent=10,
        ...     boat_penalty=0,
        ...     wind_strength="moderate",
        ...     wind_direction="tailwind",
        ...     wind_strength_display="Moderate",
        ...     wind_direction_display="Tailwind",
        ...     requires_tacking=True,
        ...     requires_test=False,
        ...     weather_effects=["No weather-related hazards"],
        ...     wind_notes="Tacking required for speed bonus",
        ...     weather_name="Clear",
        ...     day_number=3
        ... )
        >>> print(impact.speed_percent)
        10
    """

    speed_percent: int
    boat_penalty: int
    wind_strength: str
    wind_direction: str
    wind_strength_display: str
    wind_direction_display: str
    requires_tacking: bool
    requires_test: bool
    weather_effects: List[str]
    wind_notes: str
    weather_name: str
    day_number: int


@dataclass(frozen=True)
class WeatherSummary:
    """
    Summary of weather conditions for all time periods in a day.

    Contains weather data for dawn, midday, dusk, and midnight along
    with journey metadata (day number, season, province).

    Attributes:
        day_number: Current journey day number
        season: Current season (e.g., "Spring", "Summer")
        province: Current province (e.g., "Reikland", "Averland")
        dawn: Weather impact for dawn time period (optional)
        midday: Weather impact for midday time period (optional)
        dusk: Weather impact for dusk time period (optional)
        midnight: Weather impact for midnight time period (optional)

    Example:
        >>> summary = WeatherSummary(
        ...     day_number=1,
        ...     season="Spring",
        ...     province="Reikland",
        ...     midday=impact,
        ...     dawn=None,
        ...     dusk=None,
        ...     midnight=None
        ... )
    """

    day_number: int
    season: str
    province: str
    dawn: Optional[WeatherImpact] = None
    midday: Optional[WeatherImpact] = None
    dusk: Optional[WeatherImpact] = None
    midnight: Optional[WeatherImpact] = None
