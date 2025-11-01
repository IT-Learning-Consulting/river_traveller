"""
Permission Utilities - Centralized permission checks for commands.

Provides reusable permission checking functions to gate access to
GM-only features (weather override, encounter type selection, stage
configuration, etc.).

This module eliminates code duplication by providing a single source
of truth for permission logic across all command modules.

Usage:
    from commands.permissions import is_gm, ROLE_GM

    if is_gm(interaction.user):
        # Allow privileged action
        pass
    else:
        await interaction.response.send_message(
            "❌ Only GMs can use this feature.", ephemeral=True
        )
"""

import discord


# Permission role name
ROLE_GM = "GM"


def is_gm(user: discord.Member) -> bool:
    """
    Check if user has GM permissions (server owner or GM role).

    Used to control access to privileged commands like weather override,
    encounter type selection, and stage configuration.

    Args:
        user: Discord member to check for GM permissions

    Returns:
        True if user is server owner or has GM role, False otherwise

    Example:
        >>> if is_gm(interaction.user):
        ...     # Allow privileged action
        ...     pass
        ... else:
        ...     await interaction.response.send_message(
        ...         "❌ Only GMs can use this feature.", ephemeral=True
        ...     )
    """
    # Server owner is always GM
    if user.guild.owner_id == user.id:
        return True

    # Check for GM role
    gm_role = discord.utils.get(user.guild.roles, name=ROLE_GM)
    if gm_role and gm_role in user.roles:
        return True

    return False
