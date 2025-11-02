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

    def __init__(self, db_path: str, persistent_conn=None):
        """
        Initialize repository with database path.

        Args:
            db_path: Path to SQLite database file
            persistent_conn: Optional persistent connection for :memory: databases
        """
        self.db_path = db_path
        self._persistent_conn = persistent_conn

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        # Use persistent connection if available (for :memory: databases)
        if self._persistent_conn:
            # Don't close persistent connections
            try:
                yield self._persistent_conn
                self._persistent_conn.commit()
            except Exception:
                self._persistent_conn.rollback()
                raise
        else:
            # Create new connection for file-based databases
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
                    guild_id, day_number, season, province,
                    weather_type, weather_roll, wind_timeline,
                    temperature_actual, perceived_temp, temperature_category, temp_modifier, temperature_roll,
                    cold_front_days_remaining, cold_front_total_duration,
                    heat_wave_days_remaining, heat_wave_total_duration,
                    weather_effects, generated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    guild_id,
                    weather.day_number,
                    weather.season,
                    weather.province,
                    weather.weather_type,
                    0,  # weather_roll - not tracked currently
                    wind_timeline_json,
                    weather.temperature.actual,
                    weather.temperature.perceived,
                    weather.temperature.category,
                    weather.temperature.modifier,
                    weather.temperature.roll,
                    weather.special_event.days_remaining if weather.special_event.event_type == "cold_front" else 0,
                    weather.special_event.total_duration if weather.special_event.event_type == "cold_front" else 0,
                    weather.special_event.days_remaining if weather.special_event.event_type == "heat_wave" else 0,
                    weather.special_event.total_duration if weather.special_event.event_type == "heat_wave" else 0,
                    json.dumps(weather.weather_effects),
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

    def cleanup_old_weather(self, days_to_keep: int = 30) -> int:
        """
        Delete weather data older than specified days for all guilds.

        Args:
            days_to_keep: Number of recent days to keep per guild

        Returns:
            Number of records deleted
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # For each guild, delete days older than days_to_keep
            cursor.execute(
                """
                DELETE FROM daily_weather
                WHERE (guild_id, day_number) IN (
                    SELECT d.guild_id, d.day_number
                    FROM daily_weather d
                    JOIN guild_weather_state g ON d.guild_id = g.guild_id
                    WHERE d.day_number < g.current_day - ?
                )
            """,
                (days_to_keep,),
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
                rolls=wind_data[0].get("rolls", []),
                modifier=wind_data[0].get("modifier", 0),
                notes=wind_data[0].get("notes", ""),
            ),
            midday=WindCondition(
                strength=wind_data[1]["strength"],
                direction=wind_data[1]["direction"],
                rolls=wind_data[1].get("rolls", []),
                modifier=wind_data[1].get("modifier", 0),
                notes=wind_data[1].get("notes", ""),
            ),
            dusk=WindCondition(
                strength=wind_data[2]["strength"],
                direction=wind_data[2]["direction"],
                rolls=wind_data[2].get("rolls", []),
                modifier=wind_data[2].get("modifier", 0),
                notes=wind_data[2].get("notes", ""),
            ),
            midnight=WindCondition(
                strength=wind_data[3]["strength"],
                direction=wind_data[3]["direction"],
                rolls=wind_data[3].get("rolls", []),
                modifier=wind_data[3].get("modifier", 0),
                notes=wind_data[3].get("notes", ""),
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
            actual=row["temperature_actual"],
            perceived=row["perceived_temp"],
            category=row["temperature_category"],
            modifier=row["temp_modifier"],
            roll=row["temperature_roll"],
        )

        # Parse weather effects (handle missing column)
        try:
            weather_effects = json.loads(row["weather_effects"]) if row["weather_effects"] else []
        except (KeyError, IndexError):
            weather_effects = []

        return DailyWeather(
            day_number=row["day_number"],
            guild_id=row["guild_id"],
            province=row["province"] if "province" in row.keys() else "",
            season=row["season"] if "season" in row.keys() else "",
            weather_type=row["weather_type"],
            wind_timeline=wind_timeline,
            temperature=temperature,
            special_event=special_event,
            weather_effects=weather_effects,  # Now stored in database
            generated_at=row["generated_at"] if "generated_at" in row.keys() else "",
        )
