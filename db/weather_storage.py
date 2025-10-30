"""
Weather Persistence and Storage for Multi-Day Journeys

Comprehensive SQLite-based storage system for managing weather state across
multi-day river journeys in Discord guilds. Handles journey lifecycle, daily
weather persistence, stage tracking, and special event cooldowns.

Key Responsibilities:
    - Guild journey state management (season, province, current day/stage)
    - Daily weather record persistence (wind, temperature, special events)
    - Stage-based progression with configurable duration (default: 3 days/stage)
    - Special event cooldown tracking (cold fronts, heat waves)
    - Database schema migrations for backward compatibility
    - Multi-guild isolation (each guild has independent journey state)

Database Schema:
    1. guild_weather_state table (one row per guild):
       - Guild identification (guild_id)
       - Journey metadata (season, province, start date)
       - Progress tracking (current_day, current_stage, stage_duration)
       - Display settings (stage_display_mode: 'simple' or 'detailed')
       - Cooldown tracking (days_since_last_cold_front, days_since_last_heat_wave)

    2. daily_weather table (one row per guild per day):
       - Day identification (guild_id, day_number)
       - Generation metadata (generated_at timestamp)
       - Weather data (wind_timeline JSON, weather_type, temperature)
       - Special events (cold_front/heat_wave remaining days and total duration)

Storage Features:
    - Automatic table creation with migrations for existing databases
    - Context manager for safe connection handling with rollback
    - JSON serialization for complex wind timeline data
    - UNIQUE constraints prevent duplicate day records
    - Foreign key relationships ensure data integrity
    - Indexed lookups for fast guild/day queries

Journey Lifecycle:
    1. start_journey(): Initialize new journey with season/province
    2. save_daily_weather(): Store weather for specific day
    3. get_daily_weather(): Retrieve past weather records
    4. advance_day() or advance_stage(): Progress journey
    5. end_journey(): Clear all journey data

Special Event Cooldowns:
    - Tracks days_since_last_cold_front and days_since_last_heat_wave
    - 7-day cooldown enforced by weather_mechanics.py
    - Cooldowns increment daily, reset to 0 when event starts
    - Default value 99 = "never happened" or "cooldown expired"

Usage:
    # Initialize storage
    storage = WeatherStorage("data/weather.db")

    # Start journey
    storage.start_journey("guild_123", "spring", "reikland", stage_duration=3)

    # Save daily weather
    storage.save_daily_weather("guild_123", 1, weather_data_dict)

    # Advance time
    new_day = storage.advance_day("guild_123")
    # or
    new_day, new_stage = storage.advance_stage("guild_123")

    # Manage cooldowns
    cf_cooldown, hw_cooldown = storage.get_cooldown_status("guild_123")
    storage.increment_cooldown("guild_123", "cold_front")
    storage.reset_cooldown("guild_123", "heat_wave")

Design Principles:
    - Multi-guild isolation (no cross-contamination between servers)
    - Automatic schema migrations (backward compatible with old databases)
    - Safe connection handling (context managers with rollback on error)
    - Type hints for all public methods
    - Testing support (set_default_db_path for in-memory testing)
"""

import sqlite3
import json
from typing import Optional, Dict, List
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager

# =============================================================================
# MODULE-LEVEL CONSTANTS
# =============================================================================

# Database Configuration
DEFAULT_DB_PATH = "data/weather.db"
DEFAULT_DB_DIRECTORY = "data"

# Stage Display Modes
STAGE_DISPLAY_MODE_SIMPLE = "simple"
STAGE_DISPLAY_MODE_DETAILED = "detailed"
DEFAULT_STAGE_DISPLAY_MODE = STAGE_DISPLAY_MODE_SIMPLE

# Journey Defaults
DEFAULT_CURRENT_DAY = 1
DEFAULT_CURRENT_STAGE = 1
DEFAULT_STAGE_DURATION = 3

# Cooldown Defaults
DEFAULT_COOLDOWN_VALUE = 99  # "Never happened" or "cooldown expired"
COOLDOWN_NEVER_HAPPENED = 99

# Special Event Types
EVENT_TYPE_COLD_FRONT = "cold_front"
EVENT_TYPE_HEAT_WAVE = "heat_wave"

# Special Event Duration Defaults
DEFAULT_EVENT_DAYS_REMAINING = 0
DEFAULT_EVENT_TOTAL_DURATION = 0

# Table Names
TABLE_GUILD_WEATHER_STATE = "guild_weather_state"
TABLE_DAILY_WEATHER = "daily_weather"

# Column Names - Guild Weather State Table
COL_GUILD_ID = "guild_id"
COL_CURRENT_DAY = "current_day"
COL_CURRENT_STAGE = "current_stage"
COL_STAGE_DURATION = "stage_duration"
COL_STAGE_DISPLAY_MODE = "stage_display_mode"
COL_JOURNEY_START_DATE = "journey_start_date"
COL_LAST_WEATHER_DATE = "last_weather_date"
COL_SEASON = "season"
COL_PROVINCE = "province"
COL_DAYS_SINCE_LAST_COLD_FRONT = "days_since_last_cold_front"
COL_DAYS_SINCE_LAST_HEAT_WAVE = "days_since_last_heat_wave"

# Column Names - Daily Weather Table
COL_ID = "id"
COL_DAY_NUMBER = "day_number"
COL_GENERATED_AT = "generated_at"
COL_WIND_TIMELINE = "wind_timeline"
COL_WEATHER_TYPE = "weather_type"
COL_WEATHER_ROLL = "weather_roll"
COL_TEMPERATURE_ACTUAL = "temperature_actual"
COL_TEMPERATURE_CATEGORY = "temperature_category"
COL_TEMPERATURE_ROLL = "temperature_roll"
COL_COLD_FRONT_DAYS_REMAINING = "cold_front_days_remaining"
COL_COLD_FRONT_TOTAL_DURATION = "cold_front_total_duration"
COL_HEAT_WAVE_DAYS_REMAINING = "heat_wave_days_remaining"
COL_HEAT_WAVE_TOTAL_DURATION = "heat_wave_total_duration"

# Index Names
INDEX_GUILD_DAY = "idx_guild_day"


class WeatherStorage:
    """
    Handles persistent storage of weather data for multi-day journeys across Discord guilds.

    This class manages all database operations for journey state and daily weather records.
    Each Discord guild can have one active journey with unlimited daily weather records.

    Key Features:
        - SQLite database with automatic schema migrations
        - Multi-guild isolation (each guild independent)
        - Stage-based progression (configurable days per stage)
        - Special event cooldown tracking
        - Safe connection handling with rollback
        - Testing support (in-memory database option)

    Database Tables:
        - guild_weather_state: One row per guild with journey metadata
        - daily_weather: One row per guild per day with weather details

    Attributes:
        db_path (str): Path to SQLite database file
        _default_db_path (Optional[str]): Class-level default for testing

    Thread Safety:
        Not thread-safe. Use separate instances for concurrent access.

    Examples:
        >>> storage = WeatherStorage("data/weather.db")
        >>> storage.start_journey("guild_123", "spring", "reikland")
        >>> weather_data = {...}  # Wind, temperature, special events
        >>> storage.save_daily_weather("guild_123", 1, weather_data)
        >>> current = storage.get_current_day("guild_123")
        1
        >>> storage.advance_day("guild_123")
        2
    """

    # Class variable for default database path (can be overridden for testing)
    _default_db_path: Optional[str] = None

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        """
        Initialize database connection and create schema if needed.

        Creates data directory if it doesn't exist. Automatically runs init_database()
        to create tables and perform migrations on existing databases.

        Args:
            db_path: Path to SQLite database file (default: "data/weather.db")
                    Can be ":memory:" for testing with in-memory database

        Examples:
            >>> storage = WeatherStorage()  # Uses default path
            >>> test_storage = WeatherStorage(":memory:")  # In-memory testing
        """
        # Use class-level default if set, otherwise use parameter
        if self._default_db_path is not None and db_path == DEFAULT_DB_PATH:
            db_path = self._default_db_path

        # Create data directory if it doesn't exist
        Path(db_path).parent.mkdir(exist_ok=True)

        self.db_path = db_path
        self.init_database()

    @classmethod
    def set_default_db_path(cls, path: Optional[str]) -> None:
        """
        Set the default database path for all new instances (primarily for testing).

        This allows tests to use in-memory databases without modifying production code.
        Set to None to reset to default behavior.

        Args:
            path: Database path to use as default (":memory:" for testing),
                 or None to reset to default

        Examples:
            >>> WeatherStorage.set_default_db_path(":memory:")
            >>> storage = WeatherStorage()  # Uses in-memory database
            >>> WeatherStorage.set_default_db_path(None)  # Reset to default
        """
        cls._default_db_path = path

    @contextmanager
    def _get_connection(self):
        """
        Context manager for safe database connections with automatic commit/rollback.

        Enables column access by name (row["column_name"]). Automatically commits
        on success and rolls back on exception. Always closes connection.

        Yields:
            sqlite3.Connection: Database connection with row_factory enabled

        Examples:
            >>> with self._get_connection() as conn:
            ...     cursor = conn.cursor()
            ...     cursor.execute("INSERT INTO ...")
            ...     # Auto-commits if no exception
        """
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

    def _get_table_columns(self, table_name: str) -> Dict[str, str]:
        """
        Get column names and types for a table (for testing).

        Args:
            table_name: Name of the table

        Returns:
            Dictionary mapping column names to their types
        """
        with self._get_connection() as conn:
            cursor = conn.execute(f"PRAGMA table_info({table_name})")
            return {row[1]: row[2] for row in cursor.fetchall()}

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
                    province TEXT NOT NULL,
                    days_since_last_cold_front INTEGER DEFAULT 99,
                    days_since_last_heat_wave INTEGER DEFAULT 99
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

            # Add new cooldown tracking columns (Phase 1 migration)
            try:
                cursor.execute(
                    """
                    ALTER TABLE guild_weather_state 
                    ADD COLUMN days_since_last_cold_front INTEGER DEFAULT 99
                    """
                )
            except sqlite3.OperationalError:
                # Column already exists
                pass

            try:
                cursor.execute(
                    """
                    ALTER TABLE guild_weather_state 
                    ADD COLUMN days_since_last_heat_wave INTEGER DEFAULT 99
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
                    cold_front_total_duration INTEGER DEFAULT 0,
                    heat_wave_days_remaining INTEGER DEFAULT 0,
                    heat_wave_total_duration INTEGER DEFAULT 0,
                    
                    UNIQUE(guild_id, day_number),
                    FOREIGN KEY(guild_id) REFERENCES guild_weather_state(guild_id)
                )
            """
            )

            # Add missing columns to daily_weather
            try:
                cursor.execute(
                    """
                    ALTER TABLE daily_weather 
                    ADD COLUMN cold_front_days_remaining INTEGER DEFAULT 0
                    """
                )
            except sqlite3.OperationalError:
                # Column already exists
                pass

            try:
                cursor.execute(
                    """
                    ALTER TABLE daily_weather 
                    ADD COLUMN cold_front_total_duration INTEGER DEFAULT 0
                    """
                )
            except sqlite3.OperationalError:
                # Column already exists
                pass

            try:
                cursor.execute(
                    """
                    ALTER TABLE daily_weather 
                    ADD COLUMN heat_wave_days_remaining INTEGER DEFAULT 0
                    """
                )
            except sqlite3.OperationalError:
                # Column already exists
                pass

            try:
                cursor.execute(
                    """
                    ALTER TABLE daily_weather 
                    ADD COLUMN heat_wave_total_duration INTEGER DEFAULT 0
                    """
                )
            except sqlite3.OperationalError:
                # Column already exists
                pass

            # Backfill logic: For active events without total_duration, set total = remaining
            # This handles the case where we upgrade mid-cold-front
            # Only run if the columns exist (check by attempting and catching error)
            try:
                cursor.execute(
                    """
                    UPDATE daily_weather 
                    SET cold_front_total_duration = cold_front_days_remaining 
                    WHERE cold_front_days_remaining > 0 AND cold_front_total_duration = 0
                    """
                )
            except sqlite3.OperationalError:
                # Columns don't exist yet or another issue - skip backfill
                pass

            try:
                cursor.execute(
                    """
                    UPDATE daily_weather 
                    SET heat_wave_total_duration = heat_wave_days_remaining 
                    WHERE heat_wave_days_remaining > 0 AND heat_wave_total_duration = 0
                    """
                )
            except sqlite3.OperationalError:
                # Columns don't exist yet or another issue - skip backfill
                pass

            # Index for faster lookups
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_guild_day 
                ON daily_weather(guild_id, day_number)
            """
            )

    def start_journey(
        self,
        guild_id: str,
        season: str,
        province: str,
        stage_duration: int = DEFAULT_STAGE_DURATION,
    ) -> None:
        """
        Start a new journey for a guild, clearing any existing journey data.

        Deletes all previous journey state and daily weather records for the guild,
        then creates new journey with specified parameters. Journey starts at day 1,
        stage 1, with cooldowns set to "never happened" (99 days).

        Args:
            guild_id: Discord guild ID (unique identifier)
            season: Season name (spring, summer, autumn, winter)
            province: Province name (reikland, kislev, etc.)
            stage_duration: Number of days per stage (default: 3)

        Examples:
            >>> storage.start_journey("guild_123", "spring", "reikland")
            >>> storage.start_journey("guild_456", "winter", "kislev", stage_duration=5)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Delete old journey if exists
            cursor.execute(
                f"DELETE FROM {TABLE_GUILD_WEATHER_STATE} WHERE {COL_GUILD_ID} = ?",
                (guild_id,),
            )
            cursor.execute(
                f"DELETE FROM {TABLE_DAILY_WEATHER} WHERE {COL_GUILD_ID} = ?",
                (guild_id,),
            )

            # Create new journey
            cursor.execute(
                f"""
                INSERT INTO {TABLE_GUILD_WEATHER_STATE} 
                ({COL_GUILD_ID}, {COL_CURRENT_DAY}, {COL_CURRENT_STAGE}, {COL_STAGE_DURATION}, {COL_STAGE_DISPLAY_MODE}, {COL_JOURNEY_START_DATE}, {COL_LAST_WEATHER_DATE}, {COL_SEASON}, {COL_PROVINCE})
                VALUES (?, 1, 1, ?, ?, ?, ?, ?, ?)
            """,
                (
                    guild_id,
                    stage_duration,
                    DEFAULT_STAGE_DISPLAY_MODE,
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
        Save or update weather data for a specific day of a guild's journey.

        Uses INSERT OR REPLACE to handle both new and existing day records.
        Wind timeline is automatically serialized to JSON for storage.

        Required weather_data keys:
            - season (str): Season name
            - province (str): Province name
            - wind_timeline (list[dict]): Wind conditions for each time period
            - weather_type (str): Weather condition key
            - weather_roll (int): d100 roll that determined weather
            - temperature_actual (int): Actual temperature in Celsius
            - temperature_category (str): Temperature category key
            - temperature_roll (int): d100 roll that determined temperature

        Optional weather_data keys (default to 0 if not provided):
            - cold_front_days_remaining (int): Days left in cold front
            - cold_front_total_duration (int): Total cold front duration
            - heat_wave_days_remaining (int): Days left in heat wave
            - heat_wave_total_duration (int): Total heat wave duration

        Args:
            guild_id: Discord guild ID
            day_number: Day number of journey (1-indexed)
            weather_data: Dictionary containing all weather information

        Raises:
            KeyError: If required weather_data keys are missing

        Examples:
            >>> weather_data = {
            ...     "season": "spring",
            ...     "province": "reikland",
            ...     "wind_timeline": [...],
            ...     "weather_type": "rain",
            ...     "weather_roll": 50,
            ...     "temperature_actual": 12,
            ...     "temperature_category": "average",
            ...     "temperature_roll": 60
            ... }
            >>> storage.save_daily_weather("guild_123", 1, weather_data)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Convert wind_timeline to JSON string
            wind_json = json.dumps(weather_data[COL_WIND_TIMELINE])

            # Insert or replace daily weather
            cursor.execute(
                f"""
                INSERT OR REPLACE INTO {TABLE_DAILY_WEATHER} 
                ({COL_GUILD_ID}, {COL_DAY_NUMBER}, {COL_GENERATED_AT}, {COL_SEASON}, {COL_PROVINCE},
                 {COL_WIND_TIMELINE}, {COL_WEATHER_TYPE}, {COL_WEATHER_ROLL},
                 {COL_TEMPERATURE_ACTUAL}, {COL_TEMPERATURE_CATEGORY}, {COL_TEMPERATURE_ROLL},
                 {COL_COLD_FRONT_DAYS_REMAINING}, {COL_COLD_FRONT_TOTAL_DURATION},
                 {COL_HEAT_WAVE_DAYS_REMAINING}, {COL_HEAT_WAVE_TOTAL_DURATION})
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    guild_id,
                    day_number,
                    datetime.now().isoformat(),
                    weather_data[COL_SEASON],
                    weather_data[COL_PROVINCE],
                    wind_json,
                    weather_data[COL_WEATHER_TYPE],
                    weather_data[COL_WEATHER_ROLL],
                    weather_data[COL_TEMPERATURE_ACTUAL],
                    weather_data[COL_TEMPERATURE_CATEGORY],
                    weather_data[COL_TEMPERATURE_ROLL],
                    weather_data.get(
                        COL_COLD_FRONT_DAYS_REMAINING, DEFAULT_EVENT_DAYS_REMAINING
                    ),
                    weather_data.get(
                        COL_COLD_FRONT_TOTAL_DURATION, DEFAULT_EVENT_TOTAL_DURATION
                    ),
                    weather_data.get(
                        COL_HEAT_WAVE_DAYS_REMAINING, DEFAULT_EVENT_DAYS_REMAINING
                    ),
                    weather_data.get(
                        COL_HEAT_WAVE_TOTAL_DURATION, DEFAULT_EVENT_TOTAL_DURATION
                    ),
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
            New current day number (returns 1 if no journey exists)
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
            return row["current_day"] if row else 1

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
            Number of daily weather records deleted
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Delete journey state
            cursor.execute(
                "DELETE FROM guild_weather_state WHERE guild_id = ?", (guild_id,)
            )

            # Delete daily weather and get count
            cursor.execute("DELETE FROM daily_weather WHERE guild_id = ?", (guild_id,))
            deleted_count = cursor.rowcount

            return deleted_count

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

    # ============================================================================
    # Phase 1: Cooldown Tracking Methods
    # ============================================================================

    def get_cooldown_status(self, guild_id: str) -> tuple[int, int]:
        """
        Get cooldown status for both event types.

        Args:
            guild_id: Discord guild ID

        Returns:
            Tuple of (days_since_last_cold_front, days_since_last_heat_wave)
            Returns (99, 99) if no journey exists (cooldowns expired/never happened)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT days_since_last_cold_front, days_since_last_heat_wave 
                FROM guild_weather_state 
                WHERE guild_id = ?
            """,
                (guild_id,),
            )

            row = cursor.fetchone()
            if not row:
                return 99, 99

            return (
                row["days_since_last_cold_front"],
                row["days_since_last_heat_wave"],
            )

    def increment_cooldown(self, guild_id: str, event_type: str) -> None:
        """
        Increment cooldown counter for specific event type.

        Args:
            guild_id: Discord guild ID
            event_type: Either "cold_front" or "heat_wave"

        Raises:
            ValueError: If event_type is not recognized
        """
        if event_type not in ["cold_front", "heat_wave"]:
            raise ValueError(
                f"Invalid event_type '{event_type}'. Must be 'cold_front' or 'heat_wave'"
            )

        column_name = f"days_since_last_{event_type}"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                UPDATE guild_weather_state 
                SET {column_name} = {column_name} + 1 
                WHERE guild_id = ?
            """,
                (guild_id,),
            )

    def reset_cooldown(self, guild_id: str, event_type: str) -> None:
        """
        Reset cooldown counter to 0 (event just started or ended).

        Args:
            guild_id: Discord guild ID
            event_type: Either "cold_front" or "heat_wave"

        Raises:
            ValueError: If event_type is not recognized
        """
        if event_type not in ["cold_front", "heat_wave"]:
            raise ValueError(
                f"Invalid event_type '{event_type}'. Must be 'cold_front' or 'heat_wave'"
            )

        column_name = f"days_since_last_{event_type}"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                UPDATE guild_weather_state 
                SET {column_name} = 0 
                WHERE guild_id = ?
            """,
                (guild_id,),
            )
