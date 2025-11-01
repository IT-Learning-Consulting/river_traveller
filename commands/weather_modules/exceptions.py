"""
Weather Domain Exceptions - Typed exceptions for weather command errors.

This module defines domain-specific exceptions that provide clear error
semantics and enable centralized error handling in WeatherCommandHandler.

Exception Hierarchy:
    WeatherCommandError (base)
    ├── JourneyNotFoundError - No active journey
    ├── InvalidStageConfigError - Invalid stage duration
    ├── WeatherDataNotFoundError - Missing weather data for day
    └── JourneyAlreadyExistsError - Journey already in progress

Usage Example:
    >>> if not journey:
    ...     raise JourneyNotFoundError("No journey in progress")
"""


class WeatherCommandError(Exception):
    """
    Base exception for all weather command domain errors.

    All weather-specific exceptions inherit from this, enabling
    centralized error handling in the command handler.

    Attributes:
        message: User-friendly error message
        details: Optional technical details for logging
    """

    def __init__(self, message: str, details: str = None):
        """
        Initialize weather command error.

        Args:
            message: User-friendly error message to display
            details: Optional technical details for logging
        """
        self.message = message
        self.details = details
        super().__init__(message)


class JourneyNotFoundError(WeatherCommandError):
    """
    Raised when an operation requires an active journey but none exists.

    Examples:
        - User tries /weather next without starting a journey
        - User tries /weather view without a journey
        - User tries /weather end when no journey is active
    """

    def __init__(self, message: str = None, details: str = None):
        """
        Initialize journey not found error.

        Args:
            message: Custom message, or uses default if None
            details: Optional technical details
        """
        default_message = "❌ No journey in progress. Use `/weather journey` to start a new journey first."
        super().__init__(message or default_message, details)


class InvalidStageConfigError(WeatherCommandError):
    """
    Raised when stage configuration parameters are invalid.

    Examples:
        - Stage duration < 1 or > 10 days
        - Invalid starting day number
        - Conflicting stage parameters
    """

    def __init__(self, message: str = None, details: str = None):
        """
        Initialize invalid stage config error.

        Args:
            message: Custom message, or uses default if None
            details: Optional technical details
        """
        default_message = "❌ Stage duration must be between 1 and 10 days."
        super().__init__(message or default_message, details)


class WeatherDataNotFoundError(WeatherCommandError):
    """
    Raised when requested weather data doesn't exist.

    Examples:
        - User requests day 10 but journey only has 3 days
        - Historical data not found in database
        - Corrupted or missing weather record
    """

    def __init__(self, day: int = None, message: str = None, details: str = None):
        """
        Initialize weather data not found error.

        Args:
            day: Day number that was not found
            message: Custom message, or uses default with day number
            details: Optional technical details
        """
        if message is None and day is not None:
            message = f"❌ No weather data found for Day {day}."
        elif message is None:
            message = "❌ Weather data not found."
        super().__init__(message, details)
        self.day = day


class JourneyAlreadyExistsError(WeatherCommandError):
    """
    Raised when trying to start a journey while one is already active.

    This is typically a warning condition - the handler may choose
    to end the existing journey and start a new one, or reject the request.

    Examples:
        - User runs /weather journey twice without ending first
        - Concurrent journey start attempts
    """

    def __init__(self, message: str = None, details: str = None):
        """
        Initialize journey already exists error.

        Args:
            message: Custom message, or uses default if None
            details: Optional technical details
        """
        default_message = (
            "⚠️ A journey is already in progress. "
            "Ending previous journey and starting new one."
        )
        super().__init__(message or default_message, details)


class InvalidParametersError(WeatherCommandError):
    """
    Raised when command parameters are missing or invalid.

    Examples:
        - Missing required season parameter
        - Invalid province name
        - Missing day parameter for /weather view
    """

    def __init__(self, message: str, details: str = None):
        """
        Initialize invalid parameters error.

        Args:
            message: Description of what parameters are invalid
            details: Optional technical details
        """
        super().__init__(message, details)
