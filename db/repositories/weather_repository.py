"""
Weather Repository - Database operations for daily weather data.

Handles all SQL operations for daily_weather table.
Provides CRUD operations for weather data using DailyWeather dataclass.
"""

import sqlite3
import json
from typing import Optional, List
from contextlib import contextmanager
from db.models.weather_models import DailyWeather, WindTimeline, WindCondition, TemperatureData, SpecialEvent


class WeatherRepository:
    """
    Repository for daily weather persistence.

    Handles all database operations for daily weather records including
    saving, retrieving, and deleting weather data.
    """

    def __init__(self, db_path: str):
        """
        Initialize repository with database path.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def save_daily_weather(self, guild_id: str, weather: DailyWeather) -> None:
        """
        Save daily weather to the database.

        Args:
            guild_id: Discord guild ID
            weather: DailyWeather dataclass with complete weather data
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Serialize wind_timeline to JSON
            wind_timeline_json = json.dumps([
                {
                    "time": "dawn",
                    "strength": weather.wind_timeline.dawn.strength,
                    "direction": weather.wind_timeline.dawn.direction,
                    "rolls": weather.wind_timeline.dawn.rolls,
                    "modifier": weather.wind_timeline.dawn.modifier,
                    "notes": weather.wind_timeline.dawn.notes,
                },
                {
                    "time": "midday",
                    "strength": weather.wind_timeline.midday.strength,
                    "direction": weather.wind_timeline.midday.direction,
                    "rolls": weather.wind_timeline.midday.rolls,
                    "modifier": weather.wind_timeline.midday.modifier,
                    "notes": weather.wind_timeline.midday.notes,
                },
                {
                    "time": "dusk",
                    "strength": weather.wind_timeline.dusk.strength,
                    "direction": weather.wind_timeline.dusk.direction,
                    "rolls": weather.wind_timeline.dusk.rolls,
                    "modifier": weather.wind_timeline.dusk.modifier,
                    "notes": weather.wind_timeline.dusk.notes,
                },
                {
                    "time": "midnight",
                    "strength": weather.wind_timeline.midnight.strength,
                    "direction": weather.wind_timeline.midnight.direction,
                    "rolls": weather.wind_timeline.midnight.rolls,
                    "modifier": weather.wind_timeline.midnight.modifier,
                    "notes": weather.wind_timeline.midnight.notes,
                },
            ])

            cursor.execute(
                """
                INSERT OR REPLACE INTO daily_weather (
                    guild_id, day_number, weather_type, wind_timeline,
                    actual_temp, perceived_temp, temp_category, temp_modifier, temp_roll,
                    cold_front_days_remaining, cold_front_total_duration,
                    heat_wave_days_remaining, heat_wave_total_duration,
                    generated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    guild_id,
                    weather.day_number,
                    weather.weather_type,
                    wind_timeline_json,
                    weather.temperature.actual,
                    weather.temperature.perceived,
                    weather.temperature.category,
                    weather.temperature.modifier,
                    weather.temperature.roll,
                    weather.special_event.days_remaining if weather.special_event.event_type == "cold_front" else None,
                    weather.special_event.total_duration if weather.special_event.event_type == "cold_front" else None,
                    weather.special_event.days_remaining if weather.special_event.event_type == "heat_wave" else None,
                    weather.special_event.total_duration if weather.special_event.event_type == "heat_wave" else None,
                    weather.generated_at,
                ),
            )

    def get_daily_weather(self, guild_id: str, day_number: int) -> Optional[DailyWeather]:
        """
        Retrieve weather for a specific day.

        Args:
            guild_id: Discord guild ID
            day_number: Day number of journey

        Returns:
            DailyWeather dataclass or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM daily_weather
                WHERE guild_id = ? AND day_number = ?
                """,
                (guild_id, day_number),
            )
            row = cursor.fetchone()

            if not row:
                return None

            return self._row_to_daily_weather(row)

    def get_all_weather(self, guild_id: str) -> List[DailyWeather]:
        """
        Retrieve all weather records for a guild.

        Args:
            guild_id: Discord guild ID

        Returns:
            List of DailyWeather dataclasses, ordered by day_number
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM daily_weather
                WHERE guild_id = ?
                ORDER BY day_number
                """,
                (guild_id,),
            )
            rows = cursor.fetchall()

            return [self._row_to_daily_weather(row) for row in rows]

    def delete_all_weather(self, guild_id: str) -> int:
        """
        Delete all weather records for a guild.

        Args:
            guild_id: Discord guild ID

        Returns:
            Number of rows deleted
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                DELETE FROM daily_weather WHERE guild_id = ?
                """,
                (guild_id,),
            )
            return cursor.rowcount

    def _row_to_daily_weather(self, row: sqlite3.Row) -> DailyWeather:
        """
        Convert database row to DailyWeather dataclass.

        Args:
            row: SQLite row object

        Returns:
            DailyWeather dataclass
        """
        # Parse wind timeline JSON
        wind_data = json.loads(row["wind_timeline"])
        wind_timeline = WindTimeline(
            dawn=WindCondition(
                strength=wind_data[0]["strength"],
                direction=wind_data[0]["direction"],
                rolls=wind_data[0]["rolls"],
                modifier=wind_data[0]["modifier"],
                notes=wind_data[0]["notes"],
            ),
            midday=WindCondition(
                strength=wind_data[1]["strength"],
                direction=wind_data[1]["direction"],
                rolls=wind_data[1]["rolls"],
                modifier=wind_data[1]["modifier"],
                notes=wind_data[1]["notes"],
            ),
            dusk=WindCondition(
                strength=wind_data[2]["strength"],
                direction=wind_data[2]["direction"],
                rolls=wind_data[2]["rolls"],
                modifier=wind_data[2]["modifier"],
                notes=wind_data[2]["notes"],
            ),
            midnight=WindCondition(
                strength=wind_data[3]["strength"],
                direction=wind_data[3]["direction"],
                rolls=wind_data[3]["rolls"],
                modifier=wind_data[3]["modifier"],
                notes=wind_data[3]["notes"],
            ),
        )

        # Determine special event
        cold_front_days = row["cold_front_days_remaining"]
        heat_wave_days = row["heat_wave_days_remaining"]

        if cold_front_days is not None and cold_front_days > 0:
            special_event = SpecialEvent(
                event_type="cold_front",
                days_remaining=cold_front_days,
                total_duration=row["cold_front_total_duration"],
            )
        elif heat_wave_days is not None and heat_wave_days > 0:
            special_event = SpecialEvent(
                event_type="heat_wave",
                days_remaining=heat_wave_days,
                total_duration=row["heat_wave_total_duration"],
            )
        else:
            special_event = SpecialEvent(
                event_type=None,
                days_remaining=None,
                total_duration=None,
            )

        # Build temperature data
        temperature = TemperatureData(
            actual=row["actual_temp"],
            perceived=row["perceived_temp"],
            category=row["temp_category"],
            modifier=row["temp_modifier"],
            roll=row["temp_roll"],
        )

        return DailyWeather(
            day_number=row["day_number"],
            guild_id=row["guild_id"],
            province="",  # Not stored in daily_weather table
            season="",  # Not stored in daily_weather table
            weather_type=row["weather_type"],
            wind_timeline=wind_timeline,
            temperature=temperature,
            special_event=special_event,
            weather_effects=[],  # Not stored in database
            generated_at=row["generated_at"],
        )
