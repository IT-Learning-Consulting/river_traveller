"""
Weather Domain Transfer Objects - Typed data structures for weather services.

These DTOs build on database domain models to provide a clean service layer API.
They encapsulate weather data with rich type information, replacing raw dicts.

DTOs are frozen (immutable) and provide factory methods to convert from database
domain models (DailyWeather, JourneyState) to presentation-layer objects.
"""

from dataclasses import dataclass
from typing import List, Optional
from db.models.weather_models import DailyWeather, JourneyState, WindCondition


@dataclass(frozen=True)
class WeatherSummary:
    """
    Complete weather summary for display.

    Enriches DailyWeather with calculated display fields.
    Used by services and handlers to pass typed weather data.

    Attributes:
        day: Day number of journey
        season: Season name (spring, summer, autumn, winter)
        province: Province name
        weather_type: Weather condition type
        wind_timeline: List of wind conditions for each time period
        most_common_wind: Most frequent wind condition (for summary)
        actual_temp: Actual temperature in Celsius
        perceived_temp: Perceived temperature with wind chill
        base_temp: Base temperature before modifiers
        temp_category: Temperature category name
        temp_description: Human-readable temperature description
        weather_effects: List of active weather effects
        cold_front_days: Days remaining in cold front (0 if none)
        heat_wave_days: Days remaining in heat wave (0 if none)
        continuity_note: Optional note about weather continuity
    """

    # Core weather data
    day: int
    season: str
    province: str
    weather_type: str

    # Wind information
    wind_timeline: List[WindCondition]
    most_common_wind: str

    # Temperature information
    actual_temp: int
    perceived_temp: int
    base_temp: int
    temp_category: str
    temp_description: str

    # Weather effects
    weather_effects: List[str]

    # Special events
    cold_front_days: int
    heat_wave_days: int
    continuity_note: Optional[str] = None

    @classmethod
    def from_daily_weather(cls, daily_weather: DailyWeather) -> "WeatherSummary":
        """
        Create WeatherSummary from DailyWeather domain model.

        Args:
            daily_weather: DailyWeather dataclass from database

        Returns:
            WeatherSummary DTO for presentation layer
        """
        # Extract wind conditions into a list
        wind_timeline = [
            daily_weather.wind_timeline.dawn,
            daily_weather.wind_timeline.midday,
            daily_weather.wind_timeline.dusk,
            daily_weather.wind_timeline.midnight,
        ]

        # Determine most common wind (simplified - could be improved)
        # For now, just use the strongest wind
        wind_strengths = [w.strength for w in wind_timeline]
        most_common = max(
            set(wind_strengths), key=wind_strengths.count
        ) if wind_strengths else "calm"

        # Extract special event days
        special_event = daily_weather.special_event
        cold_front_days = (
            special_event.days_remaining
            if special_event.event_type == "cold_front"
            else 0
        )
        heat_wave_days = (
            special_event.days_remaining
            if special_event.event_type == "heat_wave"
            else 0
        )

        # Calculate base temperature (before modifiers)
        # Actual temp = base + modifier, so base = actual - modifier
        base_temp = daily_weather.temperature.actual - daily_weather.temperature.modifier

        # Create temperature description
        temp_description = f"{daily_weather.temperature.category} ({daily_weather.temperature.actual}°C)"

        return cls(
            day=daily_weather.day_number,
            season=daily_weather.season,
            province=daily_weather.province,
            weather_type=daily_weather.weather_type,
            wind_timeline=wind_timeline,
            most_common_wind=most_common,
            actual_temp=daily_weather.temperature.actual,
            perceived_temp=daily_weather.temperature.perceived,
            base_temp=base_temp,
            temp_category=daily_weather.temperature.category,
            temp_description=temp_description,
            weather_effects=daily_weather.weather_effects,
            cold_front_days=cold_front_days,
            heat_wave_days=heat_wave_days,
            continuity_note=None,  # Can be set by service layer
        )


@dataclass(frozen=True)
class JourneySummary:
    """
    Journey state summary for display.

    Wraps JourneyState with display-friendly formatting.
    Used to pass journey information between service and display layers.

    Attributes:
        guild_id: Discord guild ID
        season: Current season
        province: Current province
        current_day: Current day number
        stage_duration: Days per stage
        cold_front_cooldown: Days since last cold front
        heat_wave_cooldown: Days since last heat wave
    """

    guild_id: str
    season: str
    province: str
    current_day: int
    stage_duration: int

    # Cooldown information
    cold_front_cooldown: int
    heat_wave_cooldown: int

    @classmethod
    def from_journey_state(cls, journey_state: JourneyState) -> "JourneySummary":
        """
        Create JourneySummary from JourneyState domain model.

        Args:
            journey_state: JourneyState dataclass from database

        Returns:
            JourneySummary DTO for presentation layer
        """
        return cls(
            guild_id=journey_state.guild_id,
            season=journey_state.season,
            province=journey_state.province,
            current_day=journey_state.current_day,
            stage_duration=journey_state.stage_duration,
            cold_front_cooldown=journey_state.days_since_last_cold_front,
            heat_wave_cooldown=journey_state.days_since_last_heat_wave,
        )


@dataclass(frozen=True)
class StageSummary:
    """
    Multi-day stage summary for display.

    Aggregates multiple WeatherSummary objects into a stage view.
    Used for displaying stage-based weather forecasts.

    Attributes:
        stage_number: Stage number (1-indexed)
        start_day: First day of stage
        end_day: Last day of stage
        daily_weather: List of weather summaries for each day
    """

    stage_number: int
    start_day: int
    end_day: int
    daily_weather: List[WeatherSummary]

    @property
    def duration(self) -> int:
        """
        Calculate stage duration in days.

        Returns:
            Number of days in this stage (length of daily_weather list)
        """
        return len(self.daily_weather)
