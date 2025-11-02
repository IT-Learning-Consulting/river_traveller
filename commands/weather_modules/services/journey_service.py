"""
JourneyService - Journey Lifecycle Management

This service handles all journey-related operations including starting, ending,
state management, stage configuration, and cooldown tracking.

Responsibilities:
    - Start new journeys with season and province
    - End journeys and provide summaries
    - Retrieve current journey state
    - Advance day counter
    - Configure stage settings (duration, display mode)
    - Track and enforce cooldowns for special events

Design Principles:
    - Focused: Only journey lifecycle, no weather generation
    - Stateless: All state stored via WeatherStorage
    - Simple: Pure business logic, no Discord interaction
    - Testable: All methods return values or modify storage

Usage:
    >>> service = JourneyService(storage)
    >>> journey_state = service.start_journey("guild123", "winter", "reikland")
    >>> current = service.get_journey_state("guild123")
    >>> new_day = service.advance_day("guild123")
"""

from typing import Optional, Dict, Tuple
from db.weather_storage import WeatherStorage
from db.models.weather_models import JourneyState


class JourneyService:
    """
    Service for managing journey lifecycle and state.

    This service provides a clean interface for journey operations,
    encapsulating all journey-related business logic separate from
    Discord command handling and weather generation.

    Attributes:
        storage: WeatherStorage instance for persisting journey state
    """

    def __init__(self, storage: WeatherStorage):
        """
        Initialize JourneyService with storage dependency.

        Args:
            storage: WeatherStorage instance for data persistence
        """
        self.storage = storage

    def start_journey(
        self, guild_id: str, season: str, province: str
    ) -> Optional[JourneyState]:
        """
        Start a new journey with specified season and province.

        Automatically ends any existing journey before starting a new one.
        Journey starts at day 1 with default stage settings.

        Args:
            guild_id: Guild identifier
            season: Season name (winter, spring, summer, autumn)
            province: Province name (reikland, talabecland, etc.)

        Returns:
            dict: New journey state with keys:
                - season: str
                - province: str
                - current_day: int (always 1)
                - stage_duration: int (default 3)
                - display_mode: str (default "simple")

        Example:
            >>> journey = service.start_journey("123", "winter", "reikland")
            >>> journey["current_day"]
            1
        """
        # Normalize inputs
        season = season.lower()
        province = province.lower()

        # End existing journey if present (storage handles this automatically)
        self.storage.start_journey(guild_id, season, province)

        # Get the newly created journey state
        journey = self.storage.get_journey_state(guild_id)

        # Note: journey is now a JourneyState dataclass (frozen/immutable)
        # The guild_id and current_stage are already part of the dataclass
        # No need to "enhance" - all fields are already present from storage

        return journey

    def end_journey(self, guild_id: str) -> Optional[JourneyState]:
        """
        End the current journey and return final state summary.

        Retrieves journey state before deletion for summary purposes,
        then removes journey and all associated weather data from storage.

        Args:
            guild_id: Guild identifier

        Returns:
            JourneyState or None: Final journey state before deletion, or None if no
                journey exists. JourneyState contains all journey information.

        Example:
            >>> final_state = service.end_journey("123")
            >>> if final_state:
            ...     print(f"Journey lasted {final_state.current_day} days")
        """
        # Get journey state before ending (for summary)
        journey = self.storage.get_journey_state(guild_id)

        if not journey:
            return None

        # End journey (storage removes journey and weather data)
        self.storage.end_journey(guild_id)

        # Return the final state (immutable JourneyState dataclass)
        return journey

    def get_journey_state(self, guild_id: str) -> Optional[JourneyState]:
        """
        Retrieve current journey state.

        Args:
            guild_id: Guild identifier

        Returns:
            JourneyState or None: Journey state dataclass if exists, None otherwise.

        Example:
            >>> journey = service.get_journey_state("123")
            >>> if journey:
            ...     print(f"Day {journey.current_day}")
        """
        return self.storage.get_journey_state(guild_id)

    def get_journey(self, guild_id: str) -> Optional[JourneyState]:
        """
        Alias for get_journey_state for backward compatibility.

        Deprecated: Use get_journey_state() instead.

        Args:
            guild_id: Guild identifier

        Returns:
            JourneyState or None: Journey state if exists, None otherwise
        """
        return self.get_journey_state(guild_id)

    def has_active_journey(self, guild_id: str) -> bool:
        """
        Check if guild has an active journey.

        Args:
            guild_id: Guild identifier

        Returns:
            bool: True if journey exists, False otherwise

        Example:
            >>> if service.has_active_journey("123"):
            ...     print("Journey in progress")
        """
        return self.storage.get_journey_state(guild_id) is not None

    def advance_day(self, guild_id: str) -> int:
        """
        Advance journey to next day.

        Increments current_day counter in journey state. Should be called
        after generating weather for the current day.

        Args:
            guild_id: Guild identifier

        Returns:
            int: New day number after advancement

        Raises:
            ValueError: If no journey exists for guild

        Example:
            >>> new_day = service.advance_day("123")
            >>> print(f"Advanced to day {new_day}")
        """
        journey = self.storage.get_journey_state(guild_id)
        if not journey:
            raise ValueError(f"No journey found for guild {guild_id}")

        return self.storage.advance_day(guild_id)

    def configure_stage(
        self,
        guild_id: str,
        stage_duration: Optional[int] = None,
        display_mode: Optional[str] = None,
    ) -> Dict[str, any]:
        """
        Configure stage settings for current journey.

        Updates stage duration and/or display mode. Only provided parameters
        are updated; others remain unchanged.

        Args:
            guild_id: Guild identifier
            stage_duration: Number of days per stage (1-10), or None to keep current
            display_mode: Display mode ("simple" or "detailed"), or None to keep current

        Returns:
            dict: Updated journey state with new settings

        Raises:
            ValueError: If no journey exists, or if parameters are invalid

        Example:
            >>> journey = service.configure_stage("123", stage_duration=5)
            >>> journey["stage_duration"]
            5
        """
        journey = self.storage.get_journey_state(guild_id)
        if not journey:
            raise ValueError(f"No journey found for guild {guild_id}")

        # Validate and update stage duration
        if stage_duration is not None:
            if stage_duration < 1 or stage_duration > 10:
                raise ValueError("Stage duration must be between 1 and 10 days")
            self.storage.update_stage_duration(guild_id, stage_duration)

        # Validate and update display mode
        if display_mode is not None:
            if display_mode not in ["simple", "detailed"]:
                raise ValueError("Display mode must be 'simple' or 'detailed'")
            self.storage.update_stage_display_mode(guild_id, display_mode)

        # Return updated state
        return self.storage.get_journey_state(guild_id)

    def get_stage_config(self, guild_id: str) -> Tuple[int, str]:
        """
        Get current stage configuration.

        Args:
            guild_id: Guild identifier

        Returns:
            tuple: (stage_duration, display_mode)
                - stage_duration: int (days per stage)
                - display_mode: str ("simple" or "detailed")

        Raises:
            ValueError: If no journey exists

        Example:
            >>> duration, mode = service.get_stage_config("123")
            >>> print(f"{duration} days per stage, {mode} display")
        """
        journey = self.storage.get_journey_state(guild_id)
        if not journey:
            raise ValueError(f"No journey found for guild {guild_id}")

        stage_duration = journey.get("stage_duration", 3)
        display_mode = journey.get("display_mode", "simple")

        return stage_duration, display_mode

    def get_cooldown_status(self, guild_id: str) -> Tuple[int, int]:
        """
        Get current cooldown status for special weather events.

        Cooldown values indicate days since last event:
        - 0: Event is currently active
        - 1-14: Days since event ended (cooldown period)
        - 99: Never happened or cooldown expired

        Args:
            guild_id: Guild identifier

        Returns:
            tuple: (cold_front_cooldown, heat_wave_cooldown)
                Both values are integers representing days since last event

        Example:
            >>> cold, heat = service.get_cooldown_status("123")
            >>> if cold >= 14:
            ...     print("Cold front available")
        """
        return self.storage.get_cooldown_status(guild_id)

    def check_cooldown_ready(
        self, guild_id: str, event_type: str, minimum_cooldown: int = 14
    ) -> bool:
        """
        Check if cooldown period has elapsed for an event type.

        Args:
            guild_id: Guild identifier
            event_type: "cold_front" or "heat_wave"
            minimum_cooldown: Minimum days required (default 14)

        Returns:
            bool: True if event can occur (cooldown >= minimum), False otherwise

        Example:
            >>> if service.check_cooldown_ready("123", "cold_front"):
            ...     print("Can trigger cold front")
        """
        cold_front_cooldown, heat_wave_cooldown = self.storage.get_cooldown_status(
            guild_id
        )

        if event_type == "cold_front":
            return cold_front_cooldown >= minimum_cooldown
        elif event_type == "heat_wave":
            return heat_wave_cooldown >= minimum_cooldown
        else:
            raise ValueError(f"Unknown event type: {event_type}")

    def configure_stage_duration(self, guild_id: str, duration: int) -> None:
        """
        Configure stage duration for current journey.

        Args:
            guild_id: Guild identifier
            duration: Number of days per stage (1-10)

        Raises:
            ValueError: If no journey exists or duration invalid

        Example:
            >>> service.configure_stage_duration("123", 5)
        """
        journey = self.storage.get_journey_state(guild_id)
        if not journey:
            raise ValueError("No active journey")

        if duration < 1 or duration > 10:
            raise ValueError("Stage duration must be between 1 and 10")

        self.storage.update_stage_duration(guild_id, duration)

    def get_current_stage(self, guild_id: str) -> int:
        """
        Calculate current stage number from day and stage duration.

        Args:
            guild_id: Guild identifier

        Returns:
            int: Current stage number (1-based)

        Raises:
            ValueError: If no journey exists

        Example:
            >>> stage = service.get_current_stage("123")
            >>> print(f"Currently in stage {stage}")
        """
        journey = self.storage.get_journey_state(guild_id)
        if not journey:
            raise ValueError(f"No journey found for guild {guild_id}")

        current_day = journey.get("current_day", 1)
        stage_duration = journey.get("stage_duration", 3)

        # Calculate stage: (day - 1) // stage_duration + 1
        # Day 1-3 (duration 3) = stage 1, Day 4-6 = stage 2, etc.
        return ((current_day - 1) // stage_duration) + 1
