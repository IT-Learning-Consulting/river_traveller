"""
Command Logger Service - Centralized logging for Discord commands.

This service handles command logging to the boat-travelling-log channel,
eliminating duplicate logging code across command files. Provides graceful
failure handling when log channels don't exist or permissions are missing.

Usage Example:
    >>> logger = CommandLogger()
    >>> await logger.log_command(
    ...     guild=interaction.guild,
    ...     user_name="TestUser",
    ...     user_id=12345,
    ...     command_name="roll",
    ...     command_string="/roll 1d100",
    ...     fields={"Dice": "1d100"}
    ... )
"""

from typing import Optional, Dict, Any, Union
from dataclasses import dataclass

import discord


@dataclass
class CommandLogEntry:
    """
    Data for a command log entry.

    Attributes:
        guild: Discord guild where command was executed
        user_name: Display name of user who ran command
        user_id: Discord user ID
        command_name: Name of the command (e.g., "roll", "boat-handling")
        command_string: Full command string with parameters
        fields: Optional dict of field name/value pairs for the embed
        color: Optional Discord color for the embed (default: blue)

    Example:
        CommandLogEntry(
            guild=interaction.guild,
            user_name="Anara",
            user_id=123456789,
            command_name="roll",
            command_string="/roll 1d100 target:45 modifier:20",
            fields={"Dice": "1d100", "Target": "45", "Modifier": "+20"},
            color=discord.Color.blue(),
        )
    """

    guild: discord.Guild
    user_name: str
    user_id: int
    command_name: str
    command_string: str
    fields: Optional[Dict[str, str]] = None
    color: Optional[discord.Color] = None


class CommandLogger:
    """
    Service for logging Discord commands to a designated channel.

    Handles all command logging with graceful failure (no exceptions thrown
    if channel missing or permissions denied). Logs include user info,
    command details, and optional custom fields.

    Example:
        logger = CommandLogger()
        await logger.log_command(
            guild=ctx.guild,
            user_name=ctx.author.display_name,
            user_id=ctx.author.id,
            command_name="roll",
            command_string="!roll 2d6+5",
            fields={"Dice": "2d6+5"}
        )
    """

    # Channel name for command logs (configured via Discord)
    LOG_CHANNEL_NAME = "boat-travelling-log"

    def __init__(self):
        """Initialize the CommandLogger service."""
        pass

    async def log_command(
        self,
        guild: discord.Guild,
        user_name: str,
        user_id: int,
        command_name: str,
        command_string: str,
        fields: Optional[Dict[str, str]] = None,
        color: Optional[discord.Color] = None,
    ) -> bool:
        """
        Log a command execution to the boat-travelling-log channel.

        Creates an embed with command details and sends it to the log channel.
        Fails silently if channel doesn't exist or bot lacks permissions.

        Args:
            guild: Discord guild where command was executed
            user_name: Display name of the user who ran the command
            user_id: Discord user ID
            command_name: Name of the command (e.g., "roll", "boat-handling")
            command_string: Full command string with all parameters
            fields: Optional dict of field name/value pairs to add to embed
            color: Optional Discord color for the embed (default: blue)

        Returns:
            True if log was successfully sent, False if it failed silently

        Example:
            success = await logger.log_command(
                guild=interaction.guild,
                user_name="TestUser",
                user_id=123456,
                command_name="roll",
                command_string="/roll 1d100",
                fields={"Dice": "1d100"},
                color=discord.Color.blue()
            )
        """
        try:
            # Find the log channel
            log_channel = discord.utils.get(
                guild.text_channels, name=self.LOG_CHANNEL_NAME
            )
            if not log_channel:
                return False  # Channel doesn't exist, fail silently

            # Use blue as default color
            embed_color = color if color else discord.Color.blue()

            # Create log embed
            log_embed = discord.Embed(
                title=f"📋 Command Log: {command_name.title()}",
                description=f"**User:** {user_name} (`{user_id}`)\n**Command:** `{command_string}`",
                color=embed_color,
                timestamp=discord.utils.utcnow(),
            )

            # Add optional fields
            if fields:
                for field_name, field_value in fields.items():
                    log_embed.add_field(name=field_name, value=field_value, inline=True)

            await log_channel.send(embed=log_embed)
            return True

        except (discord.Forbidden, discord.HTTPException, AttributeError):
            # Silently fail - logging is not critical
            # Forbidden: Bot lacks permissions
            # HTTPException: Discord API error
            # AttributeError: Guild or channel structure issues
            return False

    async def log_command_from_context(
        self,
        context: Union[discord.Interaction, Any],
        command_name: str,
        command_string: str,
        fields: Optional[Dict[str, str]] = None,
        color: Optional[discord.Color] = None,
        is_slash: bool = True,
    ) -> bool:
        """
        Convenience method to log from a Discord context (Interaction or Context).

        Extracts user info from context and calls log_command().

        Args:
            context: Discord Interaction (slash) or commands.Context (prefix)
            command_name: Name of the command
            command_string: Full command string with parameters
            fields: Optional dict of field name/value pairs
            color: Optional Discord color for the embed
            is_slash: True if context is Interaction, False if commands.Context

        Returns:
            True if log was successfully sent, False otherwise

        Example:
            await logger.log_command_from_context(
                context=interaction,
                command_name="roll",
                command_string="/roll 1d100",
                fields={"Dice": "1d100"},
                is_slash=True
            )
        """
        if not context.guild:
            return False  # No guild, can't log

        # Extract user info based on context type
        if is_slash:
            user_name = context.user.display_name
            user_id = context.user.id
        else:
            user_name = context.author.display_name
            user_id = context.author.id

        return await self.log_command(
            guild=context.guild,
            user_name=user_name,
            user_id=user_id,
            command_name=command_name,
            command_string=command_string,
            fields=fields,
            color=color,
        )
