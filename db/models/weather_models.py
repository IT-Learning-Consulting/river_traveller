"""
Weather domain models.

This module provides frozen dataclasses for weather data, replacing the previous
dict-based representations with type-safe immutable objects.

Domain Models:
- WindCondition: Wind data for a single time period
- WindTimeline: Wind conditions across 4 time periods (dawn/midday/dusk/midnight)
- TemperatureData: Temperature information with perceived temp and modifiers
- SpecialEvent: Special weather events (cold fronts, heat waves)
- DailyWeather: Complete daily weather state
- JourneyState: Guild's current journey state
- StageWeather: Multi-day stage weather aggregation

Phase: 3.1 - Database Domain Models
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List


@dataclass(frozen=True)
class WindCondition:
    """
    Wind condition for a single time period.

    Attributes:
        strength: Wind strength category (Calm, Light, Moderate, Strong, Gale)
        direction: Wind direction (N, NE, E, SE, S, SW, W, NW)
        rolls: List of dice rolls that generated this condition
        modifier: Game modifier value for this wind condition
        notes: Additional notes about this wind condition
    """

    strength: str
    direction: str
    rolls: List[int]
    modifier: int
    notes: str


@dataclass(frozen=True)
class WindTimeline:
    """
    Wind conditions across all four time periods of a day.

    Attributes:
        dawn: Wind condition at dawn
        midday: Wind condition at midday
        dusk: Wind condition at dusk
        midnight: Wind condition at midnight
    """

    dawn: WindCondition
    midday: WindCondition
    dusk: WindCondition
    midnight: WindCondition


@dataclass(frozen=True)
class TemperatureData:
    """
    Temperature information for a day.

    Attributes:
        actual: Actual temperature value
        perceived: Perceived temperature (with wind chill, etc.)
        category: Temperature category (Freezing, Cold, Cool, Mild, Warm, Hot)
        modifier: Game modifier value for temperature
        roll: Dice roll that generated this temperature
    """

    actual: int
    perceived: int
    category: str
    modifier: int
    roll: int


@dataclass(frozen=True)
class SpecialEvent:
    """
    Special weather event data.

    Attributes:
        event_type: Type of event ("cold_front", "heat_wave", or None)
        days_remaining: Days remaining in event (None if no event active)
        total_duration: Total duration of event in days (None if no event)
    """

    event_type: Optional[str]
    days_remaining: Optional[int]
    total_duration: Optional[int]


@dataclass(frozen=True)
class DailyWeather:
    """
    Complete daily weather state.

    Represents all weather data for a single day including wind conditions
    across all time periods, temperature, and special events.

    Attributes:
        day_number: Day number in the journey
        guild_id: Discord guild ID
        province: Province name
        season: Current season
        weather_type: Weather type (Clear, Overcast, Rain, etc.)
        wind_timeline: Wind conditions for all time periods
        temperature: Temperature data
        special_event: Special event data (cold fronts, heat waves)
        weather_effects: List of active weather effects
        generated_at: ISO timestamp when weather was generated
    """

    day_number: int
    guild_id: str
    province: str
    season: str
    weather_type: str
    wind_timeline: WindTimeline
    temperature: TemperatureData
    special_event: SpecialEvent
    weather_effects: List[str]
    generated_at: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DailyWeather":
        """
        Create DailyWeather from raw database dictionary.

        Converts database row (with wind_timeline as list) to dataclass representation.

        Args:
            data: Raw weather dict from database

        Returns:
            DailyWeather dataclass instance
        """
        # Parse wind_timeline - expecting a list of 4 time periods
        wind_timeline_data = data["wind_timeline"]

        # Extract wind conditions by time period
        wind_by_time = {period["time"]: period for period in wind_timeline_data}

        # Create wind conditions for each time period
        wind_timeline = WindTimeline(
            dawn=WindCondition(
                strength=wind_by_time["dawn"]["strength"],
                direction=wind_by_time["dawn"]["direction"],
                rolls=wind_by_time["dawn"]["rolls"],
                modifier=wind_by_time["dawn"]["modifier"],
                notes=wind_by_time["dawn"]["notes"],
            ),
            midday=WindCondition(
                strength=wind_by_time["midday"]["strength"],
                direction=wind_by_time["midday"]["direction"],
                rolls=wind_by_time["midday"]["rolls"],
                modifier=wind_by_time["midday"]["modifier"],
                notes=wind_by_time["midday"]["notes"],
            ),
            dusk=WindCondition(
                strength=wind_by_time["dusk"]["strength"],
                direction=wind_by_time["dusk"]["direction"],
                rolls=wind_by_time["dusk"]["rolls"],
                modifier=wind_by_time["dusk"]["modifier"],
                notes=wind_by_time["dusk"]["notes"],
            ),
            midnight=WindCondition(
                strength=wind_by_time["midnight"]["strength"],
                direction=wind_by_time["midnight"]["direction"],
                rolls=wind_by_time["midnight"]["rolls"],
                modifier=wind_by_time["midnight"]["modifier"],
                notes=wind_by_time["midnight"]["notes"],
            ),
        )

        # Create temperature data
        temperature = TemperatureData(
            actual=data["actual_temp"],
            perceived=data["perceived_temp"],
            category=data["temp_category"],
            modifier=data["temp_modifier"],
            roll=data["temp_roll"],
        )

        # Determine special event type
        event_type = None
        days_remaining = None
        total_duration = None

        if data.get("cold_front_days_remaining") is not None:
            event_type = "cold_front"
            days_remaining = data["cold_front_days_remaining"]
            total_duration = data.get("cold_front_total_duration")
        elif data.get("heat_wave_days_remaining") is not None:
            event_type = "heat_wave"
            days_remaining = data["heat_wave_days_remaining"]
            total_duration = data.get("heat_wave_total_duration")

        special_event = SpecialEvent(
            event_type=event_type,
            days_remaining=days_remaining,
            total_duration=total_duration,
        )

        return cls(
            day_number=data["day_number"],
            guild_id=str(data["guild_id"]),
            province=data["province"],
            season=data["season"],
            weather_type=data["weather_type"],
            wind_timeline=wind_timeline,
            temperature=temperature,
            special_event=special_event,
            weather_effects=data["weather_effects"],
            generated_at=data["generated_at"],
        )


@dataclass(frozen=True)
class JourneyState:
    """
    Guild's current journey state.

    Tracks the guild's progress through a river journey including stage information
    and cooldown tracking.

    Attributes:
        guild_id: Discord guild ID
        season: Current season
        province: Province name
        current_day: Current day number in journey
        current_stage: Current stage number
        stage_duration: Duration of current stage in days
        stage_display_mode: Display mode for stage ("simple" or "detailed")
        days_since_last_cold_front: Days since last cold front
        days_since_last_heat_wave: Days since last heat wave
        last_weather_date: ISO timestamp of last weather generation (optional)
    """

    guild_id: str
    season: str
    province: str
    current_day: int
    current_stage: int
    stage_duration: int
    stage_display_mode: str
    days_since_last_cold_front: int
    days_since_last_heat_wave: int
    last_weather_date: Optional[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JourneyState":
        """
        Create JourneyState from raw database dictionary.

        Args:
            data: Raw journey state dict from database

        Returns:
            JourneyState dataclass instance
        """
        return cls(
            guild_id=str(data["guild_id"]),
            season=data["season"],
            province=data["province"],
            current_day=data["current_day"],
            current_stage=data["current_stage"],
            stage_duration=data["stage_duration"],
            stage_display_mode=data["stage_display_mode"],
            days_since_last_cold_front=data["days_since_last_cold_front"],
            days_since_last_heat_wave=data["days_since_last_heat_wave"],
            last_weather_date=data.get("last_weather_date"),
        )


@dataclass(frozen=True)
class StageWeather:
    """
    Multi-day stage weather aggregation.

    Represents weather data across multiple days of a journey stage.

    Attributes:
        stage_number: Stage number
        daily_weather: List of DailyWeather for each day in the stage
    """

    stage_number: int
    daily_weather: List[DailyWeather]
