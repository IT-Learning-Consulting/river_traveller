"""
Weather persistence and storage for multi-day journeys.

This module handles storing weather data across multiple days for each Discord guild,
including wind conditions, temperature, and special weather events like cold fronts.
"""

import sqlite3
import json
from typing import Optional, Dict, List
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager


class WeatherStorage:
    """Handles persistent storage of weather data for multi-day journeys."""

    def __init__(self, db_path: str = "data/weather.db"):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        # Create data directory if it doesn't exist
        Path(db_path).parent.mkdir(exist_ok=True)

        self.db_path = db_path
        self.init_database()

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_database(self):
        """Create tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Guild weather state table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS guild_weather_state (
                    guild_id TEXT PRIMARY KEY,
                    current_day INTEGER DEFAULT 1,
                    current_stage INTEGER DEFAULT 1,
                    stage_duration INTEGER DEFAULT 3,
                    stage_display_mode TEXT DEFAULT 'simple',
                    journey_start_date TEXT,
                    last_weather_date TEXT,
                    season TEXT NOT NULL,
                    province TEXT NOT NULL
                )
            """
            )

            # Add missing columns if they don't exist (migrations for existing databases)
            try:
                cursor.execute(
                    """
                    ALTER TABLE guild_weather_state 
                    ADD COLUMN current_stage INTEGER DEFAULT 1
                    """
                )
            except sqlite3.OperationalError:
                # Column already exists
                pass

            try:
                cursor.execute(
                    """
                    ALTER TABLE guild_weather_state 
                    ADD COLUMN stage_duration INTEGER DEFAULT 3
                    """
                )
            except sqlite3.OperationalError:
                # Column already exists
                pass

            try:
                cursor.execute(
                    """
                    ALTER TABLE guild_weather_state 
                    ADD COLUMN stage_display_mode TEXT DEFAULT 'simple'
                    """
                )
            except sqlite3.OperationalError:
                # Column already exists
                pass

            # Daily weather records table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS daily_weather (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id TEXT NOT NULL,
                    day_number INTEGER NOT NULL,
                    generated_at TEXT NOT NULL,
                    season TEXT NOT NULL,
                    province TEXT NOT NULL,
                    
                    wind_timeline TEXT NOT NULL,
                    
                    weather_type TEXT NOT NULL,
                    weather_roll INTEGER NOT NULL,
                    
                    temperature_actual INTEGER NOT NULL,
                    temperature_category TEXT NOT NULL,
                    temperature_roll INTEGER NOT NULL,
                    
                    cold_front_days_remaining INTEGER DEFAULT 0,
                    heat_wave_days_remaining INTEGER DEFAULT 0,
                    
                    UNIQUE(guild_id, day_number),
                    FOREIGN KEY(guild_id) REFERENCES guild_weather_state(guild_id)
                )
            """
            )

            # Index for faster lookups
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_guild_day 
                ON daily_weather(guild_id, day_number)
            """
            )

    def start_journey(
        self, guild_id: str, season: str, province: str, stage_duration: int = 3
    ) -> None:
        """
        Start a new journey for a guild.

        Args:
            guild_id: Discord guild ID
            season: Season name (spring, summer, autumn, winter)
            province: Province name
            stage_duration: Number of days per stage (default: 3)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Delete old journey if exists
            cursor.execute(
                "DELETE FROM guild_weather_state WHERE guild_id = ?", (guild_id,)
            )
            cursor.execute("DELETE FROM daily_weather WHERE guild_id = ?", (guild_id,))

            # Create new journey
            cursor.execute(
                """
                INSERT INTO guild_weather_state 
                (guild_id, current_day, current_stage, stage_duration, stage_display_mode, journey_start_date, last_weather_date, season, province)
                VALUES (?, 1, 1, ?, 'simple', ?, ?, ?, ?)
            """,
                (
                    guild_id,
                    stage_duration,
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                    season,
                    province,
                ),
            )

    def save_daily_weather(
        self, guild_id: str, day_number: int, weather_data: Dict
    ) -> None:
        """
        Save weather for a specific day.

        Args:
            guild_id: Discord guild ID
            day_number: Day number of journey
            weather_data: Dictionary containing all weather information
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Convert wind_timeline to JSON string
            wind_json = json.dumps(weather_data["wind_timeline"])

            # Insert or replace daily weather
            cursor.execute(
                """
                INSERT OR REPLACE INTO daily_weather 
                (guild_id, day_number, generated_at, season, province,
                 wind_timeline, weather_type, weather_roll,
                 temperature_actual, temperature_category, temperature_roll,
                 cold_front_days_remaining, heat_wave_days_remaining)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    guild_id,
                    day_number,
                    datetime.now().isoformat(),
                    weather_data["season"],
                    weather_data["province"],
                    wind_json,
                    weather_data["weather_type"],
                    weather_data["weather_roll"],
                    weather_data["temperature_actual"],
                    weather_data["temperature_category"],
                    weather_data["temperature_roll"],
                    weather_data.get("cold_front_days_remaining", 0),
                    weather_data.get("heat_wave_days_remaining", 0),
                ),
            )

    def get_daily_weather(self, guild_id: str, day_number: int) -> Optional[Dict]:
        """
        Retrieve weather for a specific day.

        Args:
            guild_id: Discord guild ID
            day_number: Day number of journey

        Returns:
            Dictionary with weather data or None if not found
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

            # Convert row to dictionary and parse JSON
            weather_data = dict(row)
            weather_data["wind_timeline"] = json.loads(weather_data["wind_timeline"])

            return weather_data

    def get_current_day(self, guild_id: str) -> int:
        """
        Get current day number for guild.

        Args:
            guild_id: Discord guild ID

        Returns:
            Current day number or 0 if no journey exists
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT current_day FROM guild_weather_state 
                WHERE guild_id = ?
            """,
                (guild_id,),
            )

            row = cursor.fetchone()
            return row["current_day"] if row else 0

    def advance_day(self, guild_id: str) -> int:
        """
        Increment day counter for guild.

        Args:
            guild_id: Discord guild ID

        Returns:
            New current day number
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE guild_weather_state 
                SET current_day = current_day + 1,
                    last_weather_date = ?
                WHERE guild_id = ?
            """,
                (datetime.now().isoformat(), guild_id),
            )

            # Get new day number
            cursor.execute(
                """
                SELECT current_day FROM guild_weather_state 
                WHERE guild_id = ?
            """,
                (guild_id,),
            )

            row = cursor.fetchone()
            return row["current_day"] if row else 0

    def advance_stage(self, guild_id: str) -> tuple[int, int]:
        """
        Advance to the next stage, incrementing day by stage_duration.

        Args:
            guild_id: Discord guild ID

        Returns:
            Tuple of (new_day_number, new_stage_number)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get current state
            cursor.execute(
                """
                SELECT current_day, current_stage, stage_duration 
                FROM guild_weather_state 
                WHERE guild_id = ?
            """,
                (guild_id,),
            )

            row = cursor.fetchone()
            if not row:
                return 0, 0

            # Handle legacy data without stage fields
            current_day = row["current_day"]
            current_stage = row["current_stage"] if "current_stage" in row.keys() else 1
            stage_duration = (
                row["stage_duration"] if "stage_duration" in row.keys() else 3
            )

            new_day = current_day + stage_duration
            new_stage = current_stage + 1

            # Update to new stage
            cursor.execute(
                """
                UPDATE guild_weather_state 
                SET current_day = ?,
                    current_stage = ?,
                    last_weather_date = ?
                WHERE guild_id = ?
            """,
                (new_day, new_stage, datetime.now().isoformat(), guild_id),
            )

            return new_day, new_stage

    def update_stage_duration(self, guild_id: str, stage_duration: int) -> None:
        """
        Update stage duration for an existing journey.

        Args:
            guild_id: Discord guild ID
            stage_duration: New stage duration in days
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE guild_weather_state 
                SET stage_duration = ?
                WHERE guild_id = ?
            """,
                (stage_duration, guild_id),
            )

    def update_stage_display_mode(self, guild_id: str, display_mode: str):
        """
        Update stage display mode for a guild's journey.

        Args:
            guild_id: Discord guild ID
            display_mode: Display mode ('simple' or 'detailed')
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE guild_weather_state 
                SET stage_display_mode = ? 
                WHERE guild_id = ?
            """,
                (display_mode, guild_id),
            )

    def get_journey_state(self, guild_id: str) -> Optional[Dict]:
        """
        Get current journey state for guild.

        Args:
            guild_id: Discord guild ID

        Returns:
            Dictionary with journey state or None if no journey exists
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM guild_weather_state 
                WHERE guild_id = ?
            """,
                (guild_id,),
            )

            row = cursor.fetchone()
            return dict(row) if row else None

    def end_journey(self, guild_id: str) -> int:
        """
        Clear journey data for guild.

        Args:
            guild_id: Discord guild ID

        Returns:
            Number of days in completed journey
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get current day before deletion
            cursor.execute(
                """
                SELECT current_day FROM guild_weather_state 
                WHERE guild_id = ?
            """,
                (guild_id,),
            )

            row = cursor.fetchone()
            days = row["current_day"] if row else 0

            # Delete journey
            cursor.execute(
                "DELETE FROM guild_weather_state WHERE guild_id = ?", (guild_id,)
            )
            cursor.execute("DELETE FROM daily_weather WHERE guild_id = ?", (guild_id,))

            return days

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

    def get_all_guild_journeys(self) -> List[Dict]:
        """
        Get journey state for all active guilds.

        Returns:
            List of dictionaries with journey state
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM guild_weather_state")

            return [dict(row) for row in cursor.fetchall()]
