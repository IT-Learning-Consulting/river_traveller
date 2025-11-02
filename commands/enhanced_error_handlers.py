"""
Enhanced Error Handlers for Discord Bot Commands.

This module provides comprehensive error handling with logging, context tracking,
and user-friendly error messages. Integrates with custom exception classes for
structured error management across all commands.

Features:
    - Structured error handling with custom exception classes
    - Detailed logging with context information
    - User-friendly error messages for Discord
    - Automatic error recovery strategies
    - Stack trace capture for debugging
    - Graceful degradation for Discord API errors
    - Error metrics and tracking

Architecture:
    - Works alongside existing error_handlers.py
    - Adds support for custom exception classes
    - Provides enhanced logging and debugging
    - Maintains backward compatibility

Usage Example:
    from commands.exceptions import JourneyNotFoundException
    from commands.enhanced_error_handlers import handle_bot_exception, ErrorLogger

    try:
        journey = get_journey(guild_id)
        if not journey:
            raise JourneyNotFoundException(
                guild_id=guild_id,
                user_message="❌ No journey in progress."
            )
    except JourneyNotFoundException as e:
        await handle_bot_exception(context, e, is_slash=True, command_name="weather")
        return
"""

import traceback
import logging
from typing import Union, Optional, Dict, Any
from datetime import datetime
import discord
from discord.ext import commands

# Import custom exceptions
from commands.exceptions import (
    BotException,
    CommandException,
    DataException,
    ValidationException,
    ServiceException,
    DiscordIntegrationException,
    JourneyNotFoundException,
    WeatherDataNotFoundException,
    CharacterNotFoundException,
    DiceNotationException,
    InvalidParameterException,
    MissingParameterException,
    PermissionDeniedException,
)

# Setup logger
logger = logging.getLogger(__name__)


# ============================================================================
# ERROR LOGGING AND CONTEXT TRACKING
# ============================================================================


class ErrorLogger:
    """
    Centralized error logging with context tracking.

    Provides methods to log errors with full context information,
    stack traces, and structured data for debugging.

    Usage:
        >>> error_logger = ErrorLogger()
        >>> error_logger.log_error(
        ...     error=exception,
        ...     command_name="weather",
        ...     guild_id="123456789",
        ...     user_id="987654321"
        ... )
    """

    def __init__(self):
        """Initialize error logger with metrics tracking."""
        self.error_count = 0
        self.error_types = {}

    def log_error(
        self,
        error: Exception,
        command_name: Optional[str] = None,
        guild_id: Optional[str] = None,
        user_id: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log error with full context information.

        Args:
            error: The exception that occurred
            command_name: Name of the command that failed
            guild_id: Guild where error occurred
            user_id: User who triggered the error
            context_data: Additional context information

        Example:
            >>> logger.log_error(
            ...     error=ValueError("Invalid input"),
            ...     command_name="roll",
            ...     guild_id="123",
            ...     context_data={"dice": "5d", "target": 50}
            ... )
        """
        self.error_count += 1
        error_type = type(error).__name__
        self.error_types[error_type] = self.error_types.get(error_type, 0) + 1

        # Build log message
        log_parts = [
            f"[ERROR #{self.error_count}]",
            f"Type: {error_type}",
        ]

        if command_name:
            log_parts.append(f"Command: {command_name}")
        if guild_id:
            log_parts.append(f"Guild: {guild_id}")
        if user_id:
            log_parts.append(f"User: {user_id}")

        log_message = " | ".join(log_parts)

        # Log the error with full details
        logger.error(log_message)
        logger.error(f"Error Message: {str(error)}")

        # Log context if it's a BotException
        if isinstance(error, BotException) and error.context:
            logger.error(f"Exception Context: {error.context}")

        # Log additional context data
        if context_data:
            logger.error(f"Additional Context: {context_data}")

        # Log stack trace for debugging
        logger.error(f"Stack Trace:\n{traceback.format_exc()}")

    def log_warning(
        self, message: str, command_name: Optional[str] = None, context_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log a warning message.

        Args:
            message: Warning message
            command_name: Optional command name
            context_data: Optional context data
        """
        log_parts = ["[WARNING]", message]
        if command_name:
            log_parts.append(f"Command: {command_name}")

        logger.warning(" | ".join(log_parts))

        if context_data:
            logger.warning(f"Context: {context_data}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get error statistics.

        Returns:
            Dict with error count and breakdown by type

        Example:
            >>> stats = logger.get_stats()
            >>> print(f"Total errors: {stats['total']}")
            >>> print(f"ValueError count: {stats['by_type']['ValueError']}")
        """
        return {"total": self.error_count, "by_type": self.error_types.copy()}


# Global error logger instance
error_logger = ErrorLogger()


# ============================================================================
# ENHANCED EMBED SENDERS
# ============================================================================


async def send_error_embed(
    context: Union[discord.Interaction, commands.Context],
    title: str,
    description: str,
    is_slash: bool,
    fields: Optional[Dict[str, str]] = None,
    ephemeral: bool = True,
    footer: Optional[str] = None,
) -> bool:
    """
    Send standardized error embed to user (enhanced version).

    Creates a red-colored error embed with consistent formatting. Returns
    True if successful, False if failed (for error recovery logic).

    Args:
        context: Discord interaction or command context
        title: Error title (e.g., "❌ Invalid Dice Notation")
        description: Error description/message
        is_slash: True if slash command, False if prefix
        fields: Optional dict of field_name: field_value pairs
        ephemeral: Whether to send as ephemeral (slash only, default True)
        footer: Optional footer text

    Returns:
        bool: True if message sent successfully, False otherwise

    Example:
        >>> success = await send_error_embed(
        ...     interaction,
        ...     "❌ Invalid Input",
        ...     "Character not found",
        ...     is_slash=True,
        ...     fields={"Valid Characters": "anara, emmerich"}
        ... )
        >>> if not success:
        ...     # Fallback error handling
        ...     print("Failed to send error message")
    """
    try:
        embed = discord.Embed(
            title=title, description=description, color=discord.Color.red(), timestamp=datetime.utcnow()
        )

        if fields:
            for name, value in fields.items():
                embed.add_field(name=name, value=value, inline=False)

        if footer:
            embed.set_footer(text=footer)
        else:
            embed.set_footer(text="Need help? Use /help <command>")

        if is_slash:
            if context.response.is_done():
                await context.followup.send(embed=embed, ephemeral=ephemeral)
            else:
                await context.response.send_message(embed=embed, ephemeral=ephemeral)
        else:
            await context.send(embed=embed)

        return True

    except discord.NotFound as e:
        # Interaction expired (took too long to respond) - fail silently
        error_logger.log_warning(
            message=f"Interaction expired: {e}",
            command_name="send_error_embed",
            context_data={"title": title, "interaction_expired": True},
        )
        return False
    except discord.HTTPException as e:
        error_logger.log_error(
            error=e, command_name="send_error_embed", context_data={"title": title, "description": description}
        )
        return False
    except Exception as e:
        error_logger.log_error(
            error=e, command_name="send_error_embed", context_data={"title": title, "unexpected_error": True}
        )
        return False


async def send_warning_embed(
    context: Union[discord.Interaction, commands.Context],
    title: str,
    description: str,
    is_slash: bool,
    fields: Optional[Dict[str, str]] = None,
    ephemeral: bool = False,
) -> bool:
    """
    Send standardized warning embed to user.

    Creates an orange-colored warning embed for non-critical issues.

    Args:
        context: Discord interaction or command context
        title: Warning title (e.g., "⚠️ Auto-Starting Journey")
        description: Warning description/message
        is_slash: True if slash command, False if prefix
        fields: Optional dict of field_name: field_value pairs
        ephemeral: Whether to send as ephemeral (slash only, default False)

    Returns:
        bool: True if message sent successfully, False otherwise
    """
    try:
        embed = discord.Embed(
            title=title, description=description, color=discord.Color.orange(), timestamp=datetime.utcnow()
        )

        if fields:
            for name, value in fields.items():
                embed.add_field(name=name, value=value, inline=False)

        embed.set_footer(text="This is a warning, not an error")

        if is_slash:
            if context.response.is_done():
                await context.followup.send(embed=embed, ephemeral=ephemeral)
            else:
                await context.response.send_message(embed=embed, ephemeral=ephemeral)
        else:
            await context.send(embed=embed)

        return True

    except Exception as e:
        error_logger.log_error(error=e, command_name="send_warning_embed", context_data={"title": title})
        return False


# ============================================================================
# ENHANCED EXCEPTION HANDLERS
# ============================================================================


async def handle_bot_exception(
    context: Union[discord.Interaction, commands.Context],
    error: BotException,
    is_slash: bool,
    command_name: Optional[str] = None,
    log_to_console: bool = True,
) -> bool:
    """
    Handle custom BotException with full context and logging.

    This is the primary handler for all custom bot exceptions. It extracts
    context information, logs the error, and sends appropriate user messages.

    Args:
        context: Discord interaction or command context
        error: The BotException that was raised
        is_slash: True if slash command, False if prefix
        command_name: Optional command name for logging
        log_to_console: Whether to log to console (default True)

    Returns:
        bool: True if error was handled successfully

    Example:
        >>> try:
        ...     raise JourneyNotFoundException(
        ...         guild_id="123",
        ...         user_message="❌ No journey found."
        ...     )
        ... except BotException as e:
        ...     await handle_bot_exception(ctx, e, False, "weather")
    """
    # Extract context data
    guild_id = str(context.guild.id) if context.guild else None
    user_id = str(context.user.id if hasattr(context, "user") else context.author.id)

    # Log the error
    if log_to_console:
        error_logger.log_error(
            error=error, command_name=command_name, guild_id=guild_id, user_id=user_id, context_data=error.context
        )

    # Determine error title based on exception type
    if isinstance(error, PermissionDeniedException):
        title = "🔒 Permission Denied"
    elif isinstance(error, DataException):
        title = "📦 Data Not Found"
    elif isinstance(error, ValidationException):
        title = "❌ Invalid Input"
    elif isinstance(error, ServiceException):
        title = "⚙️ Operation Failed"
    elif isinstance(error, DiscordIntegrationException):
        title = "📡 Discord Error"
    else:
        title = "❌ Error"

    # Build fields from context
    fields = {}
    if error.context:
        # Format context nicely for display
        for key, value in error.context.items():
            if value is not None and key not in ["original_error", "guild_id", "user_id"]:
                fields[key.replace("_", " ").title()] = str(value)

    # Send error message to user
    success = await send_error_embed(
        context=context,
        title=title,
        description=error.user_message,
        is_slash=is_slash,
        fields=fields if fields else None,
        ephemeral=True,
    )

    return success


async def handle_validation_error(
    context: Union[discord.Interaction, commands.Context],
    error: Union[ValidationException, ValueError],
    is_slash: bool,
    command_name: str,
    usage_examples: Optional[list] = None,
) -> bool:
    """
    Handle validation errors with usage examples.

    Formats validation errors nicely with helpful examples and
    expected value ranges.

    Args:
        context: Discord interaction or command context
        error: ValidationException or ValueError
        is_slash: True if slash command
        command_name: Name of the command
        usage_examples: Optional list of usage examples

    Returns:
        bool: True if error was handled successfully

    Example:
        >>> try:
        ...     parse_dice_notation("5d")
        ... except ValueError as e:
        ...     await handle_validation_error(
        ...         ctx, e, False, "roll",
        ...         usage_examples=["/roll 1d100", "/roll 3d6+2"]
        ...     )
    """
    # Convert ValueError to ValidationException if needed
    if isinstance(error, ValueError):
        # Try to extract useful info from ValueError message
        error_msg = str(error)

        # Log the ValueError
        guild_id = str(context.guild.id) if context.guild else None
        user_id = str(context.user.id if hasattr(context, "user") else context.author.id)
        error_logger.log_error(error=error, command_name=command_name, guild_id=guild_id, user_id=user_id)

        # Build fields
        fields = {}
        if usage_examples:
            examples_text = "\n".join(f"• `{ex}`" for ex in usage_examples)
            fields["Examples"] = examples_text

        return await send_error_embed(
            context=context,
            title=f"❌ Invalid {command_name} Input",
            description=error_msg,
            is_slash=is_slash,
            fields=fields,
            ephemeral=True,
        )

    # Handle ValidationException
    elif isinstance(error, ValidationException):
        return await handle_bot_exception(context=context, error=error, is_slash=is_slash, command_name=command_name)

    return False


async def handle_database_error(
    context: Union[discord.Interaction, commands.Context],
    error: Exception,
    is_slash: bool,
    operation: str,
    recoverable: bool = False,
) -> bool:
    """
    Handle database errors with recovery options.

    Args:
        context: Discord interaction or command context
        error: The database exception
        is_slash: True if slash command
        operation: Name of the database operation that failed
        recoverable: Whether the error might be recoverable

    Returns:
        bool: True if error was handled successfully
    """
    guild_id = str(context.guild.id) if context.guild else None
    user_id = str(context.user.id if hasattr(context, "user") else context.author.id)

    error_logger.log_error(
        error=error,
        command_name="database",
        guild_id=guild_id,
        user_id=user_id,
        context_data={"operation": operation, "recoverable": recoverable},
    )

    if recoverable:
        description = (
            "A database error occurred, but you can try again.\n\n"
            f"**Operation:** {operation}\n"
            "If this persists, contact an administrator."
        )
    else:
        description = (
            "A critical database error occurred.\n\n" f"**Operation:** {operation}\n" "Please contact an administrator."
        )

    return await send_error_embed(
        context=context, title="🗄️ Database Error", description=description, is_slash=is_slash, ephemeral=True
    )


async def handle_discord_api_error(
    context: Union[discord.Interaction, commands.Context],
    error: discord.DiscordException,
    is_slash: bool,
    operation: str,
) -> bool:
    """
    Handle Discord API errors with retry suggestions.

    Args:
        context: Discord interaction or command context
        error: The Discord exception
        is_slash: True if slash command
        operation: What was being attempted

    Returns:
        bool: True if error notification sent successfully
    """
    error_logger.log_error(error=error, command_name="discord_api", context_data={"operation": operation})

    # Determine error type and user message
    if isinstance(error, discord.Forbidden):
        description = (
            "The bot lacks permissions for this action.\n\n"
            f"**Operation:** {operation}\n"
            "Please contact a server administrator to grant bot permissions."
        )
    elif isinstance(error, discord.HTTPException):
        if error.status == 429:  # Rate limit
            description = "Too many requests! Please wait a moment and try again.\n\n" f"**Operation:** {operation}"
        else:
            description = (
                "A Discord API error occurred. Please try again.\n\n"
                f"**Operation:** {operation}\n"
                f"**Error:** {error.status} - {error.text}"
            )
    else:
        description = "A Discord error occurred. Please try again.\n\n" f"**Operation:** {operation}"

    try:
        return await send_error_embed(
            context=context, title="📡 Discord API Error", description=description, is_slash=is_slash, ephemeral=True
        )
    except Exception:
        # Even sending the error failed - log it
        error_logger.log_error(
            error=Exception("Failed to send Discord API error message"),
            command_name="handle_discord_api_error",
            context_data={"original_error": str(error)},
        )
        return False


async def handle_generic_error(
    context: Union[discord.Interaction, commands.Context],
    error: Exception,
    is_slash: bool,
    command_name: str,
    show_details: bool = False,
) -> bool:
    """
    Handle unexpected generic errors.

    This is a catch-all handler for unexpected exceptions that don't
    fit other categories. Logs full details but shows simplified message
    to users.

    Args:
        context: Discord interaction or command context
        error: The exception that occurred
        is_slash: True if slash command
        command_name: Name of the command that failed
        show_details: Whether to show error details to user (default False)

    Returns:
        bool: True if error was handled successfully
    """
    guild_id = str(context.guild.id) if context.guild else None
    user_id = str(context.user.id if hasattr(context, "user") else context.author.id)

    error_logger.log_error(
        error=error,
        command_name=command_name,
        guild_id=guild_id,
        user_id=user_id,
        context_data={"unexpected": True, "error_type": type(error).__name__},
    )

    description = f"An unexpected error occurred while executing **{command_name}**.\n\n"

    if show_details:
        description += f"**Error Type:** {type(error).__name__}\n"
        description += f"**Details:** {str(error)}\n\n"

    description += "Please try again or contact an administrator if this persists."

    return await send_error_embed(
        context=context, title="❌ Unexpected Error", description=description, is_slash=is_slash, ephemeral=True
    )


# ============================================================================
# ERROR RECOVERY UTILITIES
# ============================================================================


class ErrorRecovery:
    """
    Utilities for error recovery strategies.

    Provides methods to attempt automatic recovery from certain error
    conditions (e.g., creating missing data, retrying operations).
    """

    @staticmethod
    async def auto_create_journey_if_missing(
        storage, guild_id: str, season: str = "summer", province: str = "reikland"
    ) -> bool:
        """
        Automatically create a journey if none exists.

        Args:
            storage: WeatherStorage instance
            guild_id: Guild ID
            season: Default season (default: summer)
            province: Default province (default: reikland)

        Returns:
            bool: True if journey was created successfully
        """
        try:
            journey = storage.get_journey_state(guild_id)
            if not journey:
                storage.start_journey(guild_id, season, province)
                error_logger.log_warning(
                    f"Auto-created journey for guild {guild_id}", context_data={"season": season, "province": province}
                )
                return True
            return False
        except Exception as e:
            error_logger.log_error(error=e, command_name="auto_create_journey", guild_id=guild_id)
            return False


# ============================================================================
# DECORATOR FOR AUTOMATIC ERROR HANDLING
# ============================================================================


def with_error_handling(command_name: str, auto_log: bool = True):
    """
    Decorator to add automatic error handling to command functions.

    Wraps command functions with comprehensive error handling that
    catches and properly handles all exception types.

    Args:
        command_name: Name of the command for logging
        auto_log: Whether to automatically log errors (default True)

    Usage:
        >>> @with_error_handling("weather")
        >>> async def weather_command(ctx, action):
        ...     # Command logic
        ...     pass

    Note: This is for future use when refactoring existing commands.
    Current commands use try/except blocks with handler functions.
    """

    def decorator(func):
        async def wrapper(context, *args, **kwargs):
            is_slash = isinstance(context, discord.Interaction)
            try:
                return await func(context, *args, **kwargs)
            except BotException as e:
                await handle_bot_exception(context, e, is_slash, command_name, auto_log)
            except discord.DiscordException as e:
                await handle_discord_api_error(context, e, is_slash, command_name)
            except ValueError as e:
                await handle_validation_error(context, e, is_slash, command_name)
            except Exception as e:
                await handle_generic_error(context, e, is_slash, command_name)

        return wrapper

    return decorator


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def format_error_for_user(error: Exception, include_details: bool = False) -> str:
    """
    Format error message for user display.

    Args:
        error: The exception to format
        include_details: Whether to include technical details

    Returns:
        str: Formatted error message
    """
    if isinstance(error, BotException):
        return error.user_message
    elif isinstance(error, ValueError):
        return f"❌ Invalid input: {str(error)}"
    elif isinstance(error, discord.Forbidden):
        return "❌ Bot lacks permissions for this action."
    elif isinstance(error, discord.HTTPException):
        if include_details:
            return f"❌ Discord API error: {error.status} - {error.text}"
        return "❌ A Discord error occurred. Please try again."
    else:
        if include_details:
            return f"❌ Error: {type(error).__name__}: {str(error)}"
        return "❌ An unexpected error occurred. Please try again."


def get_error_category(error: Exception) -> str:
    """
    Get error category for metrics and logging.

    Args:
        error: The exception to categorize

    Returns:
        str: Error category (e.g., "validation", "database", "discord_api")
    """
    if isinstance(error, ValidationException):
        return "validation"
    elif isinstance(error, DataException):
        return "database"
    elif isinstance(error, ServiceException):
        return "service"
    elif isinstance(error, DiscordIntegrationException):
        return "discord_integration"
    elif isinstance(error, discord.DiscordException):
        return "discord_api"
    elif isinstance(error, ValueError):
        return "validation"
    elif isinstance(error, KeyError):
        return "data_access"
    elif isinstance(error, AttributeError):
        return "attribute"
    else:
        return "unexpected"
