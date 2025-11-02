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
from typing import Optional, Dict
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager

from .models.weather_models import DailyWeather, JourneyState
from .repositories.journey_repository import JourneyRepository
from .repositories.weather_repository import WeatherRepository

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

        # For :memory: databases, keep a persistent connection to share with repositories
        # This prevents creating separate in-memory databases per connection
        self._persistent_conn = None
        if db_path == ":memory:":
            self._persistent_conn = sqlite3.connect(":memory:")
            self._persistent_conn.row_factory = sqlite3.Row

        # Initialize repositories (they'll use persistent connection if available)
        self.journey_repo = JourneyRepository(db_path, self._persistent_conn)
        self.weather_repo = WeatherRepository(db_path, self._persistent_conn)

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
        # Use persistent connection if available (for :memory: databases)
        if self._persistent_conn:
            try:
                yield self._persistent_conn
                self._persistent_conn.commit()
            except Exception:
                self._persistent_conn.rollback()
                raise
        else:
            # Create new connection for file-based databases
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

    # =========================================================================
    # DATACLASS CONVERTERS
    # =========================================================================

    def _dict_to_daily_weather(self, data: Dict) -> DailyWeather:
        """
        Convert dictionary to DailyWeather dataclass (backward compatibility).

        This method provides backward compatibility for services that still
        pass weather data as dictionaries. Once all services are updated to
        use DTOs, this can be removed.

        Args:
            data: Dictionary from service layer with weather data

        Returns:
            DailyWeather dataclass instance
        """
        return DailyWeather.from_dict(data)

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

            # Add missing columns to daily_weather (Phase 3 migrations)
            # Add perceived temperature
            try:
                cursor.execute(
                    """
                    ALTER TABLE daily_weather
                    ADD COLUMN perceived_temp INTEGER DEFAULT 0
                    """
                )
            except sqlite3.OperationalError:
                # Column already exists
                pass

            # Add temperature modifier
            try:
                cursor.execute(
                    """
                    ALTER TABLE daily_weather
                    ADD COLUMN temp_modifier INTEGER DEFAULT 0
                    """
                )
            except sqlite3.OperationalError:
                # Column already exists
                pass

            # Add generated_at timestamp
            try:
                cursor.execute(
                    """
                    ALTER TABLE daily_weather
                    ADD COLUMN generated_at TEXT
                    """
                )
            except sqlite3.OperationalError:
                # Column already exists
                pass

            # Add weather_effects
            try:
                cursor.execute(
                    """
                    ALTER TABLE daily_weather
                    ADD COLUMN weather_effects TEXT DEFAULT '[]'
                    """
                )
            except sqlite3.OperationalError:
                # Column already exists
                pass

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
        # Delete old journey if exists (use repositories)
        self.journey_repo.delete_journey(guild_id)
        self.weather_repo.delete_all_weather(guild_id)

        # Create new journey state
        journey = JourneyState(
            guild_id=guild_id,
            season=season,
            province=province,
            current_day=DEFAULT_CURRENT_DAY,
            current_stage=DEFAULT_CURRENT_STAGE,
            stage_duration=stage_duration,
            stage_display_mode=DEFAULT_STAGE_DISPLAY_MODE,
            days_since_last_cold_front=DEFAULT_COOLDOWN_VALUE,
            days_since_last_heat_wave=DEFAULT_COOLDOWN_VALUE,
            last_weather_date=datetime.now().isoformat(),
        )
        self.journey_repo.create_journey(journey)

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
        # Convert dict to DailyWeather dataclass and delegate to repository
        daily_weather = self._dict_to_daily_weather(weather_data)
        self.weather_repo.save_daily_weather(guild_id, daily_weather)

    def get_daily_weather(
        self, guild_id: str, day_number: int
    ) -> Optional[DailyWeather]:
        """
        Retrieve weather for a specific day.

        Args:
            guild_id: Discord guild ID
            day_number: Day number of journey

        Returns:
            DailyWeather dataclass or None if not found
        """
        return self.weather_repo.get_daily_weather(guild_id, day_number)

    def get_current_day(self, guild_id: str) -> int:
        """
        Get current day number for guild.

        Args:
            guild_id: Discord guild ID

        Returns:
            Current day number or 0 if no journey exists
        """
        journey = self.journey_repo.get_journey(guild_id)
        return journey.current_day if journey else 0

    def advance_day(self, guild_id: str) -> int:
        """
        Increment day counter for guild.

        Args:
            guild_id: Discord guild ID

        Returns:
            New current day number (returns 1 if no journey exists)
        """
        # Get current state
        journey = self.journey_repo.get_journey(guild_id)
        if not journey:
            return 1

        # Update to next day
        new_day = journey.current_day + 1
        self.journey_repo.update_current_day(guild_id, new_day, journey.current_stage)

        return new_day

    def advance_stage(self, guild_id: str) -> tuple[int, int]:
        """
        Advance to the next stage, incrementing day by stage_duration.

        Args:
            guild_id: Discord guild ID

        Returns:
            Tuple of (new_day_number, new_stage_number)
        """
        # Get current state
        journey = self.journey_repo.get_journey(guild_id)
        if not journey:
            return 0, 0

        # Calculate new values
        new_day = journey.current_day + journey.stage_duration
        new_stage = journey.current_stage + 1

        # Update to new stage
        self.journey_repo.update_current_day(guild_id, new_day, new_stage)

        return new_day, new_stage

    def update_stage_duration(self, guild_id: str, stage_duration: int) -> None:
        """
        Update stage duration for an existing journey.

        Args:
            guild_id: Discord guild ID
            stage_duration: New stage duration in days
        """
        self.journey_repo.update_stage_duration(guild_id, stage_duration)

    def update_stage_display_mode(self, guild_id: str, display_mode: str):
        """
        Update stage display mode for a guild's journey.

        Args:
            guild_id: Discord guild ID
            display_mode: Display mode ('simple' or 'detailed')
        """
        self.journey_repo.update_stage_display_mode(guild_id, display_mode)

    def get_journey_state(self, guild_id: str) -> Optional[JourneyState]:
        """
        Get current journey state for guild.

        Args:
            guild_id: Discord guild ID

        Returns:
            JourneyState dataclass or None if no journey exists
        """
        return self.journey_repo.get_journey(guild_id)

    def end_journey(self, guild_id: str) -> int:
        """
        Clear journey data for guild.

        Args:
            guild_id: Discord guild ID

        Returns:
            Number of daily weather records deleted
        """
        # Delete journey state and weather records using repositories
        deleted_count = self.weather_repo.delete_all_weather(guild_id)
        self.journey_repo.delete_journey(guild_id)

        return deleted_count

    def cleanup_old_weather(self, days_to_keep: int = 30) -> int:
        """
        Delete weather data older than specified days for all guilds.

        Args:
            days_to_keep: Number of recent days to keep per guild

        Returns:
            Number of records deleted
        """
        return self.weather_repo.cleanup_old_weather(days_to_keep)

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
        journey = self.journey_repo.get_journey(guild_id)
        if not journey:
            return 99, 99

        return (
            journey.days_since_last_cold_front,
            journey.days_since_last_heat_wave,
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

        # Get current cooldowns
        journey = self.journey_repo.get_journey(guild_id)
        if not journey:
            return

        # Increment the appropriate cooldown
        if event_type == "cold_front":
            new_cold_front = journey.days_since_last_cold_front + 1
            new_heat_wave = journey.days_since_last_heat_wave
        else:
            new_cold_front = journey.days_since_last_cold_front
            new_heat_wave = journey.days_since_last_heat_wave + 1

        self.journey_repo.update_cooldowns(guild_id, new_cold_front, new_heat_wave)

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

        # Get current cooldowns
        journey = self.journey_repo.get_journey(guild_id)
        if not journey:
            return

        # Reset the appropriate cooldown to 0
        if event_type == "cold_front":
            new_cold_front = 0
            new_heat_wave = journey.days_since_last_heat_wave
        else:
            new_cold_front = journey.days_since_last_cold_front
            new_heat_wave = 0

        self.journey_repo.update_cooldowns(guild_id, new_cold_front, new_heat_wave)
