"""
DailyWeatherService - Weather Generation and Management

This service handles daily weather generation including wind patterns,
temperature calculation with special events, and historical weather retrieval.

Responsibilities:
    - Generate daily weather with wind continuity
    - Calculate temperatures with modifiers
    - Track special events (cold fronts, heat waves)
    - Apply weather effects and wind chill
    - Retrieve historical weather data
    - Generate multi-day stage weather

Design Principles:
    - Focused: Only weather generation, no display or notifications
    - Stateless: All state stored via WeatherStorage
    - Deterministic: Same inputs produce same outputs
    - Testable: Pure functions with dependency injection

Usage:
    >>> service = DailyWeatherService(storage)
    >>> weather = service.generate_daily_weather("guild123", journey_state)
    >>> historical = service.get_historical_weather("guild123", day_number)
"""

from typing import Dict, List, Optional, Any
from db.weather_storage import WeatherStorage
from db.weather_data import get_province_base_temperature
from utils.weather_mechanics import (
    roll_weather_condition,
    roll_temperature_with_special_events,
    apply_wind_chill,
    generate_daily_wind,
    generate_daily_wind_with_previous,
    get_weather_effects,
)


class DailyWeatherService:
    """
    Service for generating and managing daily weather data.

    This service encapsulates all weather generation logic including
    wind patterns, temperature calculation, special events, and
    historical weather retrieval.

    Attributes:
        storage: WeatherStorage instance for persisting weather data
    """

    def __init__(self, storage: WeatherStorage):
        """
        Initialize DailyWeatherService with storage dependency.

        Args:
            storage: WeatherStorage instance for data persistence
        """
        self.storage = storage

    def generate_daily_weather(
        self, guild_id: str, journey: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate complete weather data for a single day.

        Handles wind continuity from previous day, temperature calculation
        with special events, weather type rolling, and cooldown tracking.

        Args:
            guild_id: Guild identifier
            journey: Journey state dict with keys:
                - current_day: int
                - season: str
                - province: str

        Returns:
            dict: Complete weather data with keys:
                - day: int (day number)
                - season: str
                - province: str
                - wind_timeline: list (4 periods: dawn, midday, dusk, midnight)
                - weather_type: str
                - weather_effects: list
                - actual_temp: int
                - perceived_temp: int
                - base_temp: int
                - temp_category: str
                - temp_description: str
                - most_common_wind: str
                - cold_front_days: int
                - heat_wave_days: int
                - continuity_note: str or None

        Example:
            >>> weather = service.generate_daily_weather("123", {
            ...     "current_day": 1,
            ...     "season": "winter",
            ...     "province": "reikland"
            ... })
            >>> weather["day"]
            1
        """
        current_day = journey["current_day"]
        season = journey["season"]
        province = journey["province"]

        # Check if weather already exists for current day
        current_weather = self.storage.get_daily_weather(guild_id, current_day)

        # Determine day number and wind continuity
        if current_weather:
            # Weather exists, advance to next day
            new_day = self.storage.advance_day(guild_id)

            # Check for wind continuity from previous midnight
            wind_timeline_data = current_weather.get("wind_timeline", [])
            if wind_timeline_data and len(wind_timeline_data) >= 4:
                previous_midnight = wind_timeline_data[3]
                wind_timeline = generate_daily_wind_with_previous(previous_midnight)
                continuity_note = (
                    f"🔄 Wind carried over from Day {current_day} midnight: "
                    f"{previous_midnight['strength']} {previous_midnight['direction']}"
                )
            else:
                # No valid wind timeline - generate fresh
                wind_timeline = generate_daily_wind()
                continuity_note = None
        else:
            # First day, no advancement needed
            new_day = current_day
            wind_timeline = generate_daily_wind()
            continuity_note = None

        # Get previous weather for special event continuity
        previous_weather = (
            self.storage.get_daily_weather(guild_id, new_day - 1)
            if new_day > 1
            else None
        )

        # Extract special event state from previous weather
        cold_front_days = (
            previous_weather.get("cold_front_days_remaining", 0)
            if previous_weather
            else 0
        )
        cold_front_total = (
            previous_weather.get("cold_front_total_duration", 0)
            if previous_weather
            else 0
        )
        heat_wave_days = (
            previous_weather.get("heat_wave_days_remaining", 0)
            if previous_weather
            else 0
        )
        heat_wave_total = (
            previous_weather.get("heat_wave_total_duration", 0)
            if previous_weather
            else 0
        )

        # Get cooldown trackers
        days_since_cf, days_since_hw = self.storage.get_cooldown_status(guild_id)

        # Roll weather type
        weather_type = roll_weather_condition(season)
        weather_effects_data = get_weather_effects(weather_type)

        # Roll temperature with special events (8 parameters → 8 returns)
        (
            actual_temp,
            temp_category,
            temp_description,
            temp_roll,
            cold_front_remaining,
            cold_front_total_new,
            heat_wave_remaining,
            heat_wave_total_new,
        ) = roll_temperature_with_special_events(
            season,
            province,
            cold_front_days,
            cold_front_total,
            heat_wave_days,
            heat_wave_total,
            days_since_cf,
            days_since_hw,
        )

        # Calculate wind chill
        base_temp = get_province_base_temperature(province, season)
        wind_strengths = [w["strength"] for w in wind_timeline]

        # Defensive: handle empty wind_timeline
        if not wind_strengths:
            most_common_wind = "Calm"
        else:
            most_common_wind = max(set(wind_strengths), key=wind_strengths.count)

        perceived_temp = apply_wind_chill(actual_temp, most_common_wind)

        # Update cooldown trackers
        self._update_cooldown_trackers(
            guild_id,
            cold_front_days,
            cold_front_remaining,
            heat_wave_days,
            heat_wave_remaining,
        )

        # Save to database
        weather_db_data = {
            "season": season,
            "province": province,
            "wind_timeline": wind_timeline,
            "weather_type": weather_type,
            "weather_roll": 0,
            "temperature_actual": actual_temp,
            "temperature_category": temp_category,
            "temperature_roll": temp_roll,
            "cold_front_days_remaining": cold_front_remaining,
            "cold_front_total_duration": cold_front_total_new,
            "heat_wave_days_remaining": heat_wave_remaining,
            "heat_wave_total_duration": heat_wave_total_new,
        }
        self.storage.save_daily_weather(guild_id, new_day, weather_db_data)

        # Return enriched data for display
        return {
            "day": new_day,
            "season": season,
            "province": province,
            "wind_timeline": wind_timeline,
            "weather_type": weather_type,
            "weather_effects": weather_effects_data["effects"],
            "actual_temp": actual_temp,
            "perceived_temp": perceived_temp,
            "base_temp": base_temp,
            "temp_category": temp_category,
            "temp_description": temp_description,
            "most_common_wind": most_common_wind,
            "cold_front_days": cold_front_remaining,
            "heat_wave_days": heat_wave_remaining,
            "continuity_note": continuity_note,
        }

    def get_historical_weather(
        self, guild_id: str, day: int
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve historical weather data for a specific day.

        Fetches weather from storage and reconstructs display-ready format
        with calculated fields like perceived temperature.

        Args:
            guild_id: Guild identifier
            day: Day number to retrieve

        Returns:
            dict or None: Weather data if exists, None otherwise.
                Contains same fields as generate_daily_weather output.

        Example:
            >>> weather = service.get_historical_weather("123", 5)
            >>> if weather:
            ...     print(f"Day {weather['day']}: {weather['weather_type']}")
        """
        weather_db = self.storage.get_daily_weather(guild_id, day)

        if not weather_db:
            return None

        # Reconstruct display-ready data
        actual_temp = weather_db["temperature_actual"]
        wind_strengths = [w["strength"] for w in weather_db["wind_timeline"]]

        # Defensive: handle empty wind_timeline
        if not wind_strengths:
            most_common_wind = "Calm"
        else:
            most_common_wind = max(set(wind_strengths), key=wind_strengths.count)

        perceived_temp = apply_wind_chill(actual_temp, most_common_wind)
        base_temp = get_province_base_temperature(
            weather_db["province"], weather_db["season"]
        )
        weather_effects_data = get_weather_effects(weather_db["weather_type"])

        # Reconstruct temperature description
        temp_category = weather_db["temperature_category"]
        temp_descriptions = {
            "very_cold": "Bitterly cold",
            "cold": "Cold",
            "cool": "Cool",
            "mild": "Mild",
            "warm": "Warm",
            "hot": "Hot",
            "very_hot": "Sweltering heat",
        }
        temp_description = temp_descriptions.get(temp_category, "Mild")

        return {
            "day": day,
            "season": weather_db["season"],
            "province": weather_db["province"],
            "wind_timeline": weather_db["wind_timeline"],
            "weather_type": weather_db["weather_type"],
            "weather_effects": weather_effects_data["effects"],
            "actual_temp": actual_temp,
            "perceived_temp": perceived_temp,
            "base_temp": base_temp,
            "temp_category": temp_category,
            "temp_description": temp_description,
            "most_common_wind": most_common_wind,
            "cold_front_days": weather_db["cold_front_days_remaining"],
            "heat_wave_days": weather_db["heat_wave_days_remaining"],
            "continuity_note": None,  # Historical views don't show continuity
        }

    def generate_stage_weather(
        self, guild_id: str, journey: Dict[str, Any], stage_duration: int
    ) -> List[Dict[str, Any]]:
        """
        Generate weather for multiple days in a stage.

        Generates consecutive days of weather with proper wind continuity
        and special event tracking across all days.

        Args:
            guild_id: Guild identifier
            journey: Journey state dict
            stage_duration: Number of days to generate

        Returns:
            list: List of weather data dicts, one per day

        Example:
            >>> stage_weather = service.generate_stage_weather("123", journey, 3)
            >>> len(stage_weather)
            3
        """
        stage_weather = []

        for _ in range(stage_duration):
            weather = self.generate_daily_weather(guild_id, journey)
            stage_weather.append(weather)

            # Update journey day for next iteration
            journey["current_day"] = weather["day"]

        return stage_weather

    def _update_cooldown_trackers(
        self,
        guild_id: str,
        previous_cold_front_days: int,
        current_cold_front_days: int,
        previous_heat_wave_days: int,
        current_heat_wave_days: int,
    ) -> None:
        """
        Update cooldown trackers based on event state transitions.

        Tracks when events start, are active, and end to enforce minimum
        cooldown periods between special weather events.

        Args:
            guild_id: Guild ID
            previous_cold_front_days: Days remaining before this generation
            current_cold_front_days: Days remaining after this generation
            previous_heat_wave_days: Days remaining before this generation
            current_heat_wave_days: Days remaining after this generation
        """
        # Cold front cooldown logic
        if current_cold_front_days > 0:
            # Event is active
            if previous_cold_front_days == 0:
                # New event just started - reset cooldown
                self.storage.reset_cooldown(guild_id, "cold_front")
            # else: Event was already active - cooldown stays at 0
        elif previous_cold_front_days > 0 and current_cold_front_days == 0:
            # Event just ended - start incrementing cooldown
            self.storage.increment_cooldown(guild_id, "cold_front")
        elif previous_cold_front_days == 0 and current_cold_front_days == 0:
            # No event - continue incrementing cooldown
            self.storage.increment_cooldown(guild_id, "cold_front")

        # Heat wave cooldown logic (same pattern)
        if current_heat_wave_days > 0:
            # Event is active
            if previous_heat_wave_days == 0:
                # New event just started - reset cooldown
                self.storage.reset_cooldown(guild_id, "heat_wave")
            # else: Event was already active - cooldown stays at 0
        elif previous_heat_wave_days > 0 and current_heat_wave_days == 0:
            # Event just ended - start incrementing cooldown
            self.storage.increment_cooldown(guild_id, "heat_wave")
        elif previous_heat_wave_days == 0 and current_heat_wave_days == 0:
            # No event - continue incrementing cooldown
            self.storage.increment_cooldown(guild_id, "heat_wave")

    def reconstruct_weather_data(self, weather_db: dict, day: int) -> dict:
        """
        Reconstruct display-ready weather data from database storage.

        Takes raw weather data from the database and enriches it with
        calculated fields needed for display (perceived temperature,
        base temperature, weather effects, temperature description).

        Args:
            weather_db: Raw weather data from database
            day: Day number for the weather data

        Returns:
            dict: Complete weather data ready for display with all
                  calculated fields included

        Example:
            >>> service = DailyWeatherService(storage)
            >>> raw_data = storage.get_daily_weather("guild123", 5)
            >>> display_data = service.reconstruct_weather_data(raw_data, 5)
            >>> print(display_data["perceived_temp"])
        """
        actual_temp = weather_db["temperature_actual"]
        wind_strengths = [w["strength"] for w in weather_db["wind_timeline"]]

        # Defensive: handle empty wind_timeline
        if not wind_strengths:
            most_common_wind = "Calm"
        else:
            most_common_wind = max(set(wind_strengths), key=wind_strengths.count)

        perceived_temp = apply_wind_chill(actual_temp, most_common_wind)

        base_temp = get_province_base_temperature(
            weather_db["province"], weather_db["season"]
        )

        weather_effects_data = get_weather_effects(weather_db["weather_type"])

        # Reconstruct temperature description
        temp_category = weather_db["temperature_category"]
        temp_descriptions = {
            "very_cold": "Bitterly cold",
            "cold": "Cold",
            "cool": "Cool",
            "mild": "Mild",
            "warm": "Warm",
            "hot": "Hot",
            "very_hot": "Sweltering heat",
        }
        temp_description = temp_descriptions.get(temp_category, "Mild")

        return {
            "day": day,
            "season": weather_db["season"],
            "province": weather_db["province"],
            "wind_timeline": weather_db["wind_timeline"],
            "weather_type": weather_db["weather_type"],
            "weather_effects": weather_effects_data["effects"],
            "actual_temp": actual_temp,
            "perceived_temp": perceived_temp,
            "base_temp": base_temp,
            "temp_category": temp_category,
            "temp_description": temp_description,
            "most_common_wind": most_common_wind,
            "cold_front_days": weather_db["cold_front_days_remaining"],
            "heat_wave_days": weather_db["heat_wave_days_remaining"],
            "continuity_note": None,  # Historical views don't show continuity
        }
