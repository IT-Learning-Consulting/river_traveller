"""
Command Logger Service - Centralized logging to Discord channels.

Encapsulates all logging-to-channel behavior, making it injectable
and testable. Commands use this instead of directly accessing channels.

Design Principles:
    - Fail-safe: Never raises exceptions (logging is non-critical)
    - Async-first: All methods are async for Discord API
    - Testable: Easy to mock for testing
    - Configurable: Channel names as constants

Usage:
    >>> logger = CommandLogger(bot)
    >>> await logger.log_command(guild, user, "roll", {"dice": "3d6"}, "Rolled 15")
    >>> await logger.log_gm_notification(guild, "Weather", "New weather generated")
"""

import discord
from typing import Optional, Dict
from datetime import datetime, timezone


class CommandLogger:
    """
    Service for logging commands to Discord channels.

    Handles logging to both user-visible and GM-only channels.
    All methods are fail-safe and will not raise exceptions if
    channels are missing.

    Attributes:
        bot: Discord bot client for channel access
        log_channel_name: Name of user-visible log channel
        gm_channel_name: Name of GM-only notification channel
    """

    def __init__(self, bot: discord.Client):
        """
        Initialize logger with bot instance.

        Args:
            bot: Discord bot client for channel access
        """
        self.bot = bot
        self.log_channel_name = "boat-travelling-log"
        self.gm_channel_name = "boat-travelling-notifications"

    async def log_command(
        self,
        guild: discord.Guild,
        user: discord.Member,
        command_name: str,
        parameters: Dict,
        result_summary: str
    ) -> bool:
        """
        Log command execution to user-visible channel.

        Creates a formatted embed with command details and sends it to
        the designated log channel. Fails silently if channel not found.

        Args:
            guild: Discord guild where command was run
            user: User who executed command
            command_name: Name of command (e.g., "roll", "weather")
            parameters: Command parameters as dict
            result_summary: Brief summary of result

        Returns:
            bool: True if logged successfully, False otherwise

        Example:
            >>> await logger.log_command(
            ...     guild=ctx.guild,
            ...     user=ctx.author,
            ...     command_name="roll",
            ...     parameters={"dice": "3d6+2"},
            ...     result_summary="Rolled 14"
            ... )
        """
        try:
            # Find log channel
            channel = discord.utils.get(guild.channels, name=self.log_channel_name)
            if not channel:
                return False  # Logging is non-critical, fail silently

            # Create embed
            embed = discord.Embed(
                title=f"Command: {command_name}",
                color=0x3498DB,
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="User", value=user.display_name, inline=True)
            embed.add_field(name="Parameters", value=str(parameters), inline=False)
            embed.add_field(name="Result", value=result_summary, inline=False)

            # Send to channel
            await channel.send(embed=embed)
            return True

        except Exception:
            # Logging failures should not crash commands
            return False

    async def log_command_from_context(
        self,
        context,
        command_name: str,
        command_string: str,
        fields: Optional[Dict] = None,
        color: Optional[discord.Color] = None,
        is_slash: bool = False
    ) -> bool:
        """
        Log command execution from Discord context (convenience wrapper).

        Extracts guild and user from context and logs command with custom fields.

        Args:
            context: Discord interaction context
            command_name: Name of command
            command_string: Full command string executed
            fields: Optional dict of additional fields to display
            color: Optional embed color

        Returns:
            bool: True if logged successfully, False otherwise
        """
        try:
            guild = context.guild
            user = context.user

            # Find log channel
            channel = discord.utils.get(guild.channels, name=self.log_channel_name)
            if not channel:
                return False

            # Create embed
            embed = discord.Embed(
                title=f"Command: {command_name}",
                description=f"`{command_string}`",
                color=color.value if color else 0x3498DB,
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="User", value=user.display_name, inline=True)

            # Add custom fields
            if fields:
                for field_name, field_value in fields.items():
                    embed.add_field(name=field_name, value=str(field_value), inline=True)

            # Send to channel
            await channel.send(embed=embed)
            return True

        except Exception:
            return False  # Logging is non-critical, fail silently

    async def log_gm_notification(
        self,
        guild: discord.Guild,
        title: str,
        description: str,
        fields: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Send notification to GM-only channel.

        Creates a formatted embed with notification details and sends it to
        the designated GM notification channel. Fails silently if channel not found.

        Args:
            guild: Discord guild
            title: Notification title
            description: Notification description
            fields: Optional dict of field_name: field_value pairs

        Returns:
            bool: True if sent successfully, False otherwise

        Example:
            >>> await logger.log_gm_notification(
            ...     guild=ctx.guild,
            ...     title="Weather Generated",
            ...     description="Day 5 weather created",
            ...     fields={"Season": "Spring", "Province": "Reikland"}
            ... )
        """
        try:
            # Find GM notification channel
            channel = discord.utils.get(guild.channels, name=self.gm_channel_name)
            if not channel:
                return False  # Fail silently

            # Create embed
            embed = discord.Embed(
                title=title,
                description=description,
                color=0xF39C12,
                timestamp=datetime.now(timezone.utc)
            )

            # Add optional fields
            if fields:
                for name, value in fields.items():
                    embed.add_field(name=name, value=value, inline=False)

            # Send to channel
            await channel.send(embed=embed)
            return True

        except Exception:
            # Logging failures should not crash commands
            return False
