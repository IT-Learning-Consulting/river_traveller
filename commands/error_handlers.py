"""
Error Handling Utilities - Standardized error responses for commands.

Provides reusable error handling to eliminate duplicate try-except
blocks and ensure consistent error messaging across all commands.

This module centralizes error handling patterns that were previously
duplicated across multiple command files (~250 lines of boilerplate).

Usage:
    from commands.error_handlers import (
        send_error_embed,
        handle_value_error,
        handle_discord_error
    )

    try:
        # Command logic
        result = service.do_something(params)
    except ValueError as e:
        await handle_value_error(
            context, e, is_slash, "CommandName",
            usage_examples=["/command example1", "/command example2"]
        )
    except (discord.DiscordException, AttributeError) as e:
        await handle_discord_error(context, e, is_slash)
"""

import discord
from typing import Union, Optional, Dict
from discord.ext import commands


async def send_error_embed(
    context: Union[discord.Interaction, commands.Context],
    title: str,
    description: str,
    is_slash: bool,
    fields: Optional[Dict[str, str]] = None,
    ephemeral: bool = True,
) -> None:
    """
    Send standardized error embed to user.

    Creates a red-colored error embed with consistent formatting across
    all commands. Handles both slash and prefix command contexts.

    Args:
        context: Discord interaction or command context
        title: Error title (e.g., "❌ Invalid Dice Notation")
        description: Error description/message
        is_slash: True if slash command, False if prefix
        fields: Optional dict of field_name: field_value pairs to add to embed
        ephemeral: Whether to send as ephemeral (slash only, default True)

    Example:
        >>> await send_error_embed(
        ...     interaction,
        ...     "❌ Invalid Input",
        ...     "Character not found",
        ...     is_slash=True,
        ...     fields={"Valid Characters": "anara, emmerich, hildric"}
        ... )
    """
    embed = discord.Embed(
        title=title, description=description, color=discord.Color.red()
    )

    if fields:
        for name, value in fields.items():
            embed.add_field(name=name, value=value, inline=False)

    if is_slash:
        # Check if response already sent to avoid errors
        if context.response.is_done():
            await context.followup.send(embed=embed, ephemeral=ephemeral)
        else:
            await context.response.send_message(embed=embed, ephemeral=ephemeral)
    else:
        await context.send(embed=embed)


async def send_info_embed(
    context: Union[discord.Interaction, commands.Context],
    title: str,
    description: str,
    is_slash: bool,
    fields: Optional[Dict[str, str]] = None,
    ephemeral: bool = False,
) -> None:
    """
    Send standardized info embed to user.

    Creates a blue-colored info embed with consistent formatting.
    Similar to send_error_embed but for informational messages.

    Args:
        context: Discord interaction or command context
        title: Info title (e.g., "ℹ️ Journey Status")
        description: Info description/message
        is_slash: True if slash command, False if prefix
        fields: Optional dict of field_name: field_value pairs
        ephemeral: Whether to send as ephemeral (slash only, default False)
    """
    embed = discord.Embed(
        title=title, description=description, color=discord.Color.blue()
    )

    if fields:
        for name, value in fields.items():
            embed.add_field(name=name, value=value, inline=False)

    if is_slash:
        if context.response.is_done():
            await context.followup.send(embed=embed, ephemeral=ephemeral)
        else:
            await context.response.send_message(embed=embed, ephemeral=ephemeral)
    else:
        await context.send(embed=embed)


async def handle_value_error(
    context: Union[discord.Interaction, commands.Context],
    error: ValueError,
    is_slash: bool,
    command_name: str,
    usage_examples: Optional[list] = None,
) -> None:
    """
    Handle ValueError with user-friendly formatting.

    ValueErrors typically indicate invalid user input (bad dice notation,
    invalid character name, out-of-range values, etc.). This handler
    formats them nicely with optional usage examples.

    Args:
        context: Discord interaction or command context
        error: The ValueError that was raised
        is_slash: True if slash command
        command_name: Name of command for error title (e.g., "Roll", "Boat Handling")
        usage_examples: Optional list of example command usages

    Example:
        >>> await handle_value_error(
        ...     context,
        ...     ValueError("Invalid dice notation"),
        ...     is_slash=True,
        ...     command_name="Roll",
        ...     usage_examples=["/roll 1d100", "/roll 3d6+2"]
        ... )
    """
    fields = {}
    if usage_examples:
        examples_text = "\n".join(f"• `{ex}`" for ex in usage_examples)
        fields["Examples"] = examples_text

    await send_error_embed(
        context,
        f"❌ Invalid {command_name} Command",
        str(error),
        is_slash,
        fields=fields,
    )


async def handle_discord_error(
    context: Union[discord.Interaction, commands.Context],
    error: Exception,
    is_slash: bool,
) -> None:
    """
    Handle Discord API errors with fallback mechanisms.

    Tries multiple strategies to inform the user of the error:
    1. response.send_message (if not already done)
    2. followup.send (if response already sent)
    3. Silent failure (if both fail - better than crashing)

    This is resilient error handling for Discord-specific exceptions
    that can occur during command execution (rate limits, permissions,
    network issues, etc.).

    Args:
        context: Discord interaction or command context
        error: The exception that was raised (DiscordException, AttributeError, etc.)
        is_slash: True if slash command

    Example:
        >>> try:
        ...     await interaction.response.send_message("test")
        ... except (discord.DiscordException, AttributeError) as e:
        ...     await handle_discord_error(interaction, e, is_slash=True)
    """
    error_message = f"❌ An error occurred: {str(error)}"

    if is_slash:
        try:
            if context.response.is_done():
                # Response already sent, use followup
                await context.followup.send(error_message, ephemeral=True)
            else:
                # Send initial response
                await context.response.send_message(error_message, ephemeral=True)
        except Exception:  # noqa: BLE001
            # Even followup failed - fail silently rather than crashing
            # This is the last resort fallback
            pass
    else:
        try:
            await context.send(error_message)
        except Exception:  # noqa: BLE001
            # Can't send message - fail silently
            pass


async def handle_permission_error(
    context: Union[discord.Interaction, commands.Context],
    is_slash: bool,
    required_permission: str = "GM",
) -> None:
    """
    Handle permission denied errors with standardized message.

    Used when a user attempts to use a GM-only command without
    proper permissions.

    Args:
        context: Discord interaction or command context
        is_slash: True if slash command
        required_permission: Name of required permission/role (default: "GM")

    Example:
        >>> if not is_gm(interaction.user):
        ...     await handle_permission_error(interaction, is_slash=True)
        ...     return
    """
    await send_error_embed(
        context,
        "❌ Permission Denied",
        f"This command requires {required_permission} permissions.\n\n"
        f"Only the server owner or users with the `{required_permission}` role can use this command.",
        is_slash,
        ephemeral=True,
    )
