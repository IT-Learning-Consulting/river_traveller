"""
Custom Exceptions for WFRP River Travel Bot.

This module defines custom exception classes for different error scenarios
across all bot commands. These exceptions provide structured error information
and make error handling more explicit and maintainable.

Exception Hierarchy:
    BotException (base)
    ├── CommandException (command-level errors)
    │   ├── InvalidParameterException
    │   ├── MissingParameterException
    │   ├── PermissionDeniedException
    │   └── CommandNotAvailableException
    ├── DataException (data access and storage errors)
    │   ├── JourneyNotFoundException
    │   ├── WeatherDataNotFoundException
    │   ├── CharacterNotFoundException
    │   └── DatabaseException
    ├── ValidationException (input validation errors)
    │   ├── DiceNotationException
    │   ├── SkillValueException
    │   ├── DifficultyException
    │   └── RangeException
    ├── ServiceException (business logic errors)
    │   ├── WeatherGenerationException
    │   ├── RollCalculationException
    │   └── BoatHandlingException
    └── DiscordIntegrationException (Discord API errors)
        ├── ChannelNotFoundException
        ├── MessageSendException
        └── EmbedCreationException

Usage Example:
    from commands.exceptions import JourneyNotFoundException, InvalidParameterException

    def get_weather(guild_id: str):
        journey = storage.get_journey_state(guild_id)
        if not journey:
            raise JourneyNotFoundException(
                guild_id=guild_id,
                message="No active journey found. Use /weather journey to start one.",
                user_message="❌ No journey in progress."
            )
"""

from typing import Optional, Dict, Any


class BotException(Exception):
    """
    Base exception for all bot-specific errors.

    Provides common attributes for structured error handling:
    - message: Technical error message for logs
    - user_message: User-friendly message for Discord display
    - context: Additional context data for debugging
    - recoverable: Whether the error can be recovered from

    Attributes:
        message (str): Technical error description for logs
        user_message (str): User-friendly error message for display
        context (dict): Additional debugging context
        recoverable (bool): Whether this error can be recovered from
    """

    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        recoverable: bool = True,
    ):
        """
        Initialize base exception.

        Args:
            message: Technical error description for logging
            user_message: Optional user-friendly message (defaults to message)
            context: Optional dict with additional debugging info
            recoverable: Whether the error is recoverable (default True)
        """
        super().__init__(message)
        self.message = message
        self.user_message = user_message or message
        self.context = context or {}
        self.recoverable = recoverable

    def __str__(self) -> str:
        """String representation includes context if available."""
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{self.message} (Context: {context_str})"
        return self.message


# ============================================================================
# COMMAND EXCEPTIONS - Errors related to command execution and parameters
# ============================================================================


class CommandException(BotException):
    """Base exception for command-level errors."""

    pass


class InvalidParameterException(CommandException):
    """Raised when a command parameter has an invalid value."""

    def __init__(
        self,
        parameter_name: str,
        parameter_value: Any,
        expected: str,
        message: Optional[str] = None,
        user_message: Optional[str] = None,
    ):
        """
        Initialize invalid parameter exception.

        Args:
            parameter_name: Name of the invalid parameter
            parameter_value: The invalid value provided
            expected: Description of what was expected
            message: Optional custom technical message
            user_message: Optional custom user message

        Example:
            >>> raise InvalidParameterException(
            ...     parameter_name="difficulty",
            ...     parameter_value=100,
            ...     expected="Value between -50 and +60",
            ...     user_message="❌ Difficulty must be between -50 and +60"
            ... )
        """
        tech_msg = message or f"Invalid value for parameter '{parameter_name}': {parameter_value}. Expected: {expected}"
        user_msg = user_message or f"❌ Invalid {parameter_name}: {parameter_value}\nExpected: {expected}"

        super().__init__(
            message=tech_msg,
            user_message=user_msg,
            context={"parameter": parameter_name, "value": parameter_value, "expected": expected},
        )
        self.parameter_name = parameter_name
        self.parameter_value = parameter_value
        self.expected = expected


class MissingParameterException(CommandException):
    """Raised when a required command parameter is missing."""

    def __init__(
        self,
        parameter_name: str,
        command_name: str,
        message: Optional[str] = None,
        user_message: Optional[str] = None,
        example: Optional[str] = None,
    ):
        """
        Initialize missing parameter exception.

        Args:
            parameter_name: Name of the missing parameter
            command_name: Name of the command
            message: Optional custom technical message
            user_message: Optional custom user message
            example: Optional usage example

        Example:
            >>> raise MissingParameterException(
            ...     parameter_name="season",
            ...     command_name="weather journey",
            ...     example="/weather journey season:summer province:reikland"
            ... )
        """
        tech_msg = message or f"Missing required parameter '{parameter_name}' for command '{command_name}'"
        user_msg = user_message or f"❌ Missing required parameter: **{parameter_name}**"
        if example:
            user_msg += f"\n\n**Example:** `{example}`"

        super().__init__(
            message=tech_msg,
            user_message=user_msg,
            context={"parameter": parameter_name, "command": command_name, "example": example},
        )
        self.parameter_name = parameter_name
        self.command_name = command_name
        self.example = example


class PermissionDeniedException(CommandException):
    """Raised when a user lacks permission for a command or action."""

    def __init__(
        self,
        command_name: str,
        required_permission: str,
        user_id: Optional[str] = None,
        message: Optional[str] = None,
        user_message: Optional[str] = None,
    ):
        """
        Initialize permission denied exception.

        Args:
            command_name: Name of the command that was denied
            required_permission: The permission that was required
            user_id: Optional user ID that was denied
            message: Optional custom technical message
            user_message: Optional custom user message

        Example:
            >>> raise PermissionDeniedException(
            ...     command_name="weather override",
            ...     required_permission="GM role or server owner",
            ...     user_message="❌ Only GMs can override weather."
            ... )
        """
        tech_msg = message or f"Permission denied for command '{command_name}'. Required: {required_permission}"
        user_msg = (
            user_message or f"❌ You don't have permission to use this command.\nRequired: **{required_permission}**"
        )

        super().__init__(
            message=tech_msg,
            user_message=user_msg,
            context={"command": command_name, "required_permission": required_permission, "user_id": user_id},
            recoverable=False,
        )
        self.command_name = command_name
        self.required_permission = required_permission


class CommandNotAvailableException(CommandException):
    """Raised when a command is temporarily unavailable or not implemented."""

    def __init__(
        self, command_name: str, reason: str, message: Optional[str] = None, user_message: Optional[str] = None
    ):
        """
        Initialize command not available exception.

        Args:
            command_name: Name of the unavailable command
            reason: Reason why it's unavailable
            message: Optional custom technical message
            user_message: Optional custom user message

        Example:
            >>> raise CommandNotAvailableException(
            ...     command_name="weather override",
            ...     reason="Not yet implemented",
            ...     user_message="⚠️ This feature is coming soon!"
            ... )
        """
        tech_msg = message or f"Command '{command_name}' not available: {reason}"
        user_msg = user_message or f"⚠️ **{command_name}** is currently unavailable.\nReason: {reason}"

        super().__init__(message=tech_msg, user_message=user_msg, context={"command": command_name, "reason": reason})
        self.command_name = command_name
        self.reason = reason


# ============================================================================
# DATA EXCEPTIONS - Errors related to data access and storage
# ============================================================================


class DataException(BotException):
    """Base exception for data access and storage errors."""

    pass


class JourneyNotFoundException(DataException):
    """Raised when no journey is found for a guild."""

    def __init__(self, guild_id: str, message: Optional[str] = None, user_message: Optional[str] = None):
        """
        Initialize journey not found exception.

        Args:
            guild_id: The guild ID that has no journey
            message: Optional custom technical message
            user_message: Optional custom user message

        Example:
            >>> raise JourneyNotFoundException(
            ...     guild_id="123456789",
            ...     user_message="❌ No journey in progress. Use `/weather journey` to start one."
            ... )
        """
        tech_msg = message or f"No journey found for guild {guild_id}"
        user_msg = user_message or "❌ No journey in progress.\nUse `/weather journey` to start a new journey."

        super().__init__(message=tech_msg, user_message=user_msg, context={"guild_id": guild_id})
        self.guild_id = guild_id


class WeatherDataNotFoundException(DataException):
    """Raised when weather data for a specific day is not found."""

    def __init__(
        self,
        guild_id: str,
        day: int,
        current_day: Optional[int] = None,
        message: Optional[str] = None,
        user_message: Optional[str] = None,
    ):
        """
        Initialize weather data not found exception.

        Args:
            guild_id: The guild ID
            day: The day that was requested
            current_day: Optional current day in the journey
            message: Optional custom technical message
            user_message: Optional custom user message

        Example:
            >>> raise WeatherDataNotFoundException(
            ...     guild_id="123456789",
            ...     day=5,
            ...     current_day=3,
            ...     user_message="❌ No weather data for Day 5. Journey is on Day 3."
            ... )
        """
        tech_msg = message or f"No weather data found for guild {guild_id}, day {day}"
        user_msg = user_message or f"❌ No weather data found for Day {day}."
        if current_day:
            user_msg += f"\nCurrent journey day: **{current_day}**"

        super().__init__(
            message=tech_msg,
            user_message=user_msg,
            context={"guild_id": guild_id, "day": day, "current_day": current_day},
        )
        self.guild_id = guild_id
        self.day = day
        self.current_day = current_day


class CharacterNotFoundException(DataException):
    """Raised when a character is not found in the database."""

    def __init__(
        self,
        character_name: str,
        available_characters: Optional[list] = None,
        message: Optional[str] = None,
        user_message: Optional[str] = None,
    ):
        """
        Initialize character not found exception.

        Args:
            character_name: The character name that was not found
            available_characters: Optional list of available character names
            message: Optional custom technical message
            user_message: Optional custom user message

        Example:
            >>> raise CharacterNotFoundException(
            ...     character_name="bobby",
            ...     available_characters=["anara", "emmerich", "hildric"]
            ... )
        """
        tech_msg = message or f"Character not found: {character_name}"
        user_msg = user_message or f"❌ Character **{character_name}** not found."
        if available_characters:
            user_msg += f"\n\n**Available characters:** {', '.join(available_characters)}"

        super().__init__(
            message=tech_msg,
            user_message=user_msg,
            context={"character": character_name, "available": available_characters},
        )
        self.character_name = character_name
        self.available_characters = available_characters


class DatabaseException(DataException):
    """Raised when a database operation fails."""

    def __init__(
        self,
        operation: str,
        original_error: Optional[Exception] = None,
        message: Optional[str] = None,
        user_message: Optional[str] = None,
    ):
        """
        Initialize database exception.

        Args:
            operation: The database operation that failed
            original_error: Optional original exception that was caught
            message: Optional custom technical message
            user_message: Optional custom user message

        Example:
            >>> try:
            ...     conn.execute("INSERT ...")
            ... except sqlite3.Error as e:
            ...     raise DatabaseException(
            ...         operation="save_weather_data",
            ...         original_error=e
            ...     )
        """
        tech_msg = message or f"Database operation failed: {operation}"
        if original_error:
            tech_msg += f" (Original error: {str(original_error)})"

        user_msg = user_message or "❌ A database error occurred. Please try again."

        super().__init__(
            message=tech_msg,
            user_message=user_msg,
            context={"operation": operation, "original_error": str(original_error) if original_error else None},
            recoverable=False,
        )
        self.operation = operation
        self.original_error = original_error


# ============================================================================
# VALIDATION EXCEPTIONS - Errors related to input validation
# ============================================================================


class ValidationException(BotException):
    """Base exception for input validation errors."""

    pass


class DiceNotationException(ValidationException):
    """Raised when dice notation is invalid."""

    def __init__(self, notation: str, reason: str, message: Optional[str] = None, user_message: Optional[str] = None):
        """
        Initialize dice notation exception.

        Args:
            notation: The invalid dice notation
            reason: Why the notation is invalid
            message: Optional custom technical message
            user_message: Optional custom user message

        Example:
            >>> raise DiceNotationException(
            ...     notation="5d",
            ...     reason="Missing die size",
            ...     user_message="❌ Invalid dice notation: **5d**\nExpected format: XdY (e.g., 3d6, 1d100)"
            ... )
        """
        tech_msg = message or f"Invalid dice notation '{notation}': {reason}"
        user_msg = (
            user_message
            or f"❌ Invalid dice notation: **{notation}**\n{reason}\n\n**Valid format:** XdY+Z (e.g., 3d6, 1d100+5, 2d10-2)"
        )

        super().__init__(message=tech_msg, user_message=user_msg, context={"notation": notation, "reason": reason})
        self.notation = notation
        self.reason = reason


class SkillValueException(ValidationException):
    """Raised when a skill value is out of valid range."""

    def __init__(
        self,
        skill_value: int,
        min_value: int = 1,
        max_value: int = 100,
        message: Optional[str] = None,
        user_message: Optional[str] = None,
    ):
        """
        Initialize skill value exception.

        Args:
            skill_value: The invalid skill value
            min_value: Minimum valid value (default 1)
            max_value: Maximum valid value (default 100)
            message: Optional custom technical message
            user_message: Optional custom user message

        Example:
            >>> raise SkillValueException(
            ...     skill_value=150,
            ...     user_message="❌ Skill value 150 is invalid. Must be 1-100."
            ... )
        """
        tech_msg = message or f"Skill value {skill_value} out of range ({min_value}-{max_value})"
        user_msg = (
            user_message or f"❌ Invalid skill value: **{skill_value}**\nMust be between {min_value} and {max_value}."
        )

        super().__init__(
            message=tech_msg,
            user_message=user_msg,
            context={"skill_value": skill_value, "min": min_value, "max": max_value},
        )
        self.skill_value = skill_value
        self.min_value = min_value
        self.max_value = max_value


class DifficultyException(ValidationException):
    """Raised when a difficulty modifier is out of valid range."""

    def __init__(
        self,
        difficulty: int,
        min_value: int = -50,
        max_value: int = 60,
        message: Optional[str] = None,
        user_message: Optional[str] = None,
    ):
        """
        Initialize difficulty exception.

        Args:
            difficulty: The invalid difficulty value
            min_value: Minimum valid value (default -50)
            max_value: Maximum valid value (default 60)
            message: Optional custom technical message
            user_message: Optional custom user message

        Example:
            >>> raise DifficultyException(
            ...     difficulty=100,
            ...     user_message="❌ Difficulty 100 is invalid. Must be -50 to +60."
            ... )
        """
        tech_msg = message or f"Difficulty modifier {difficulty} out of range ({min_value} to {max_value})"
        user_msg = (
            user_message or f"❌ Invalid difficulty: **{difficulty:+d}**\nMust be between {min_value} and +{max_value}."
        )

        super().__init__(
            message=tech_msg,
            user_message=user_msg,
            context={"difficulty": difficulty, "min": min_value, "max": max_value},
        )
        self.difficulty = difficulty
        self.min_value = min_value
        self.max_value = max_value


class RangeException(ValidationException):
    """Raised when a numeric value is out of valid range."""

    def __init__(
        self,
        parameter_name: str,
        value: Any,
        min_value: Any,
        max_value: Any,
        message: Optional[str] = None,
        user_message: Optional[str] = None,
    ):
        """
        Initialize range exception.

        Args:
            parameter_name: Name of the parameter
            value: The invalid value
            min_value: Minimum valid value
            max_value: Maximum valid value
            message: Optional custom technical message
            user_message: Optional custom user message

        Example:
            >>> raise RangeException(
            ...     parameter_name="stage_duration",
            ...     value=15,
            ...     min_value=1,
            ...     max_value=10,
            ...     user_message="❌ Stage duration must be 1-10 days."
            ... )
        """
        tech_msg = message or f"{parameter_name} value {value} out of range ({min_value}-{max_value})"
        user_msg = (
            user_message
            or f"❌ **{parameter_name}** must be between {min_value} and {max_value}.\nYou provided: {value}"
        )

        super().__init__(
            message=tech_msg,
            user_message=user_msg,
            context={"parameter": parameter_name, "value": value, "min": min_value, "max": max_value},
        )
        self.parameter_name = parameter_name
        self.value = value
        self.min_value = min_value
        self.max_value = max_value


# ============================================================================
# SERVICE EXCEPTIONS - Errors in business logic layer
# ============================================================================


class ServiceException(BotException):
    """Base exception for business logic errors."""

    pass


class WeatherGenerationException(ServiceException):
    """Raised when weather generation fails."""

    def __init__(
        self,
        guild_id: str,
        day: Optional[int] = None,
        reason: Optional[str] = None,
        original_error: Optional[Exception] = None,
        message: Optional[str] = None,
        user_message: Optional[str] = None,
    ):
        """
        Initialize weather generation exception.

        Args:
            guild_id: The guild ID
            day: Optional day number that failed
            reason: Optional reason for failure
            original_error: Optional original exception
            message: Optional custom technical message
            user_message: Optional custom user message

        Example:
            >>> raise WeatherGenerationException(
            ...     guild_id="123456789",
            ...     day=5,
            ...     reason="Invalid season data",
            ...     user_message="❌ Failed to generate weather. Please try again."
            ... )
        """
        tech_msg = message or f"Weather generation failed for guild {guild_id}"
        if day:
            tech_msg += f" (day {day})"
        if reason:
            tech_msg += f": {reason}"
        if original_error:
            tech_msg += f" (Original error: {str(original_error)})"

        user_msg = user_message or "❌ Failed to generate weather. Please try again."

        super().__init__(
            message=tech_msg,
            user_message=user_msg,
            context={
                "guild_id": guild_id,
                "day": day,
                "reason": reason,
                "original_error": str(original_error) if original_error else None,
            },
        )
        self.guild_id = guild_id
        self.day = day
        self.reason = reason
        self.original_error = original_error


class RollCalculationException(ServiceException):
    """Raised when dice roll calculation fails."""

    def __init__(
        self,
        dice_notation: str,
        reason: str,
        original_error: Optional[Exception] = None,
        message: Optional[str] = None,
        user_message: Optional[str] = None,
    ):
        """
        Initialize roll calculation exception.

        Args:
            dice_notation: The dice notation that failed
            reason: Reason for failure
            original_error: Optional original exception
            message: Optional custom technical message
            user_message: Optional custom user message

        Example:
            >>> raise RollCalculationException(
            ...     dice_notation="3d6",
            ...     reason="Overflow error in calculation",
            ...     user_message="❌ Failed to calculate roll. Please try again."
            ... )
        """
        tech_msg = message or f"Roll calculation failed for '{dice_notation}': {reason}"
        if original_error:
            tech_msg += f" (Original error: {str(original_error)})"

        user_msg = (
            user_message
            or f"❌ Failed to calculate roll for **{dice_notation}**.\nPlease check your dice notation and try again."
        )

        super().__init__(
            message=tech_msg,
            user_message=user_msg,
            context={
                "dice_notation": dice_notation,
                "reason": reason,
                "original_error": str(original_error) if original_error else None,
            },
        )
        self.dice_notation = dice_notation
        self.reason = reason
        self.original_error = original_error


class BoatHandlingException(ServiceException):
    """Raised when boat handling test execution fails."""

    def __init__(
        self,
        character_name: str,
        reason: str,
        original_error: Optional[Exception] = None,
        message: Optional[str] = None,
        user_message: Optional[str] = None,
    ):
        """
        Initialize boat handling exception.

        Args:
            character_name: The character whose test failed
            reason: Reason for failure
            original_error: Optional original exception
            message: Optional custom technical message
            user_message: Optional custom user message

        Example:
            >>> raise BoatHandlingException(
            ...     character_name="Anara",
            ...     reason="Character has no boat handling skills",
            ...     user_message="❌ Anara has no boat handling skills (Row/Sail)."
            ... )
        """
        tech_msg = message or f"Boat handling test failed for {character_name}: {reason}"
        if original_error:
            tech_msg += f" (Original error: {str(original_error)})"

        user_msg = (
            user_message or f"❌ Failed to perform boat handling test for **{character_name}**.\nReason: {reason}"
        )

        super().__init__(
            message=tech_msg,
            user_message=user_msg,
            context={
                "character": character_name,
                "reason": reason,
                "original_error": str(original_error) if original_error else None,
            },
        )
        self.character_name = character_name
        self.reason = reason
        self.original_error = original_error


# ============================================================================
# DISCORD INTEGRATION EXCEPTIONS - Errors related to Discord API
# ============================================================================


class DiscordIntegrationException(BotException):
    """Base exception for Discord API integration errors."""

    pass


class ChannelNotFoundException(DiscordIntegrationException):
    """Raised when a required channel is not found."""

    def __init__(
        self,
        channel_name: str,
        guild_id: Optional[str] = None,
        message: Optional[str] = None,
        user_message: Optional[str] = None,
    ):
        """
        Initialize channel not found exception.

        Args:
            channel_name: Name of the channel that was not found
            guild_id: Optional guild ID
            message: Optional custom technical message
            user_message: Optional custom user message

        Example:
            >>> raise ChannelNotFoundException(
            ...     channel_name="boat-travelling-log",
            ...     guild_id="123456789",
            ...     user_message="⚠️ Channel #boat-travelling-log not found. Logging disabled."
            ... )
        """
        tech_msg = message or f"Channel not found: {channel_name}"
        if guild_id:
            tech_msg += f" (guild {guild_id})"

        user_msg = user_message or f"⚠️ Channel **#{channel_name}** not found."

        super().__init__(
            message=tech_msg, user_message=user_msg, context={"channel": channel_name, "guild_id": guild_id}
        )
        self.channel_name = channel_name
        self.guild_id = guild_id


class MessageSendException(DiscordIntegrationException):
    """Raised when sending a Discord message fails."""

    def __init__(
        self,
        channel_name: Optional[str] = None,
        reason: Optional[str] = None,
        original_error: Optional[Exception] = None,
        message: Optional[str] = None,
        user_message: Optional[str] = None,
    ):
        """
        Initialize message send exception.

        Args:
            channel_name: Optional channel name
            reason: Optional reason for failure
            original_error: Optional original exception
            message: Optional custom technical message
            user_message: Optional custom user message

        Example:
            >>> raise MessageSendException(
            ...     channel_name="bot-commands",
            ...     reason="Missing permissions",
            ...     user_message="❌ Failed to send message. Bot may lack permissions."
            ... )
        """
        tech_msg = message or "Failed to send Discord message"
        if channel_name:
            tech_msg += f" to channel {channel_name}"
        if reason:
            tech_msg += f": {reason}"
        if original_error:
            tech_msg += f" (Original error: {str(original_error)})"

        user_msg = user_message or "❌ Failed to send message. Please try again or contact an admin."

        super().__init__(
            message=tech_msg,
            user_message=user_msg,
            context={
                "channel": channel_name,
                "reason": reason,
                "original_error": str(original_error) if original_error else None,
            },
            recoverable=False,
        )
        self.channel_name = channel_name
        self.reason = reason
        self.original_error = original_error


class EmbedCreationException(DiscordIntegrationException):
    """Raised when creating a Discord embed fails."""

    def __init__(
        self,
        embed_type: str,
        reason: str,
        original_error: Optional[Exception] = None,
        message: Optional[str] = None,
        user_message: Optional[str] = None,
    ):
        """
        Initialize embed creation exception.

        Args:
            embed_type: Type of embed that failed (e.g., "weather", "roll", "boat_handling")
            reason: Reason for failure
            original_error: Optional original exception
            message: Optional custom technical message
            user_message: Optional custom user message

        Example:
            >>> raise EmbedCreationException(
            ...     embed_type="weather",
            ...     reason="Missing weather data",
            ...     user_message="❌ Failed to create weather display."
            ... )
        """
        tech_msg = message or f"Failed to create {embed_type} embed: {reason}"
        if original_error:
            tech_msg += f" (Original error: {str(original_error)})"

        user_msg = user_message or f"❌ Failed to create {embed_type} display. Please try again."

        super().__init__(
            message=tech_msg,
            user_message=user_msg,
            context={
                "embed_type": embed_type,
                "reason": reason,
                "original_error": str(original_error) if original_error else None,
            },
        )
        self.embed_type = embed_type
        self.reason = reason
        self.original_error = original_error
