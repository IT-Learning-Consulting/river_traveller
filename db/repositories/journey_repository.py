"""
Journey Repository - Database operations for journey state.

Handles all SQL operations for guild_weather_state table.
Provides CRUD operations for journey data using JourneyState dataclass.
"""

import sqlite3
from typing import Optional
from contextlib import contextmanager
from db.models.weather_models import JourneyState


class JourneyRepository:
    """
    Repository for journey state persistence.

    Handles all database operations for guild journey state including
    creation, retrieval, updates, and deletion.
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

    def create_journey(self, journey: JourneyState) -> None:
        """
        Create a new journey in the database.

        Args:
            journey: JourneyState dataclass with journey details
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO guild_weather_state (
                    guild_id, season, province, current_day, current_stage,
                    stage_duration, stage_display_mode, days_since_last_cold_front,
                    days_since_last_heat_wave, last_weather_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    journey.guild_id,
                    journey.season,
                    journey.province,
                    journey.current_day,
                    journey.current_stage,
                    journey.stage_duration,
                    journey.stage_display_mode,
                    journey.days_since_last_cold_front,
                    journey.days_since_last_heat_wave,
                    journey.last_weather_date,
                ),
            )

    def get_journey(self, guild_id: str) -> Optional[JourneyState]:
        """
        Retrieve journey state for a guild.

        Args:
            guild_id: Discord guild ID

        Returns:
            JourneyState dataclass or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM guild_weather_state WHERE guild_id = ?
                """,
                (guild_id,),
            )
            row = cursor.fetchone()

            if not row:
                return None

            return JourneyState(
                guild_id=row["guild_id"],
                season=row["season"],
                province=row["province"],
                current_day=row["current_day"],
                current_stage=row["current_stage"],
                stage_duration=row["stage_duration"],
                stage_display_mode=row["stage_display_mode"],
                days_since_last_cold_front=row["days_since_last_cold_front"],
                days_since_last_heat_wave=row["days_since_last_heat_wave"],
                last_weather_date=row["last_weather_date"],
            )

    def update_current_day(self, guild_id: str, day: int, stage: int) -> None:
        """
        Update current day and stage for a journey.

        Args:
            guild_id: Discord guild ID
            day: New current day number
            stage: New current stage number
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE guild_weather_state
                SET current_day = ?, current_stage = ?
                WHERE guild_id = ?
                """,
                (day, stage, guild_id),
            )

    def update_cooldowns(
        self, guild_id: str, cold_front_days: int, heat_wave_days: int
    ) -> None:
        """
        Update cooldown counters for special events.

        Args:
            guild_id: Discord guild ID
            cold_front_days: Days since last cold front
            heat_wave_days: Days since last heat wave
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE guild_weather_state
                SET days_since_last_cold_front = ?, days_since_last_heat_wave = ?
                WHERE guild_id = ?
                """,
                (cold_front_days, heat_wave_days, guild_id),
            )

    def delete_journey(self, guild_id: str) -> int:
        """
        Delete a journey from the database.

        Args:
            guild_id: Discord guild ID

        Returns:
            Number of rows deleted (0 or 1)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                DELETE FROM guild_weather_state WHERE guild_id = ?
                """,
                (guild_id,),
            )
            return cursor.rowcount
