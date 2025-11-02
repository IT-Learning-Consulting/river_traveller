"""
River Encounter Command

Generates random river encounters with a dual-message system:
- Players see cryptic, atmospheric flavor text with minimal mechanics
- GMs receive detailed notifications with full mechanical breakdowns

This separation maintains narrative immersion while providing GMs with
the information they need to adjudicate encounters.

Usage Examples:
    Slash Commands:
        /river-encounter
        /river-encounter stage:"Day 2 Afternoon"
        /river-encounter encounter_type:accident stage:"Night 1"  # GM only

    Prefix Commands:
        !river-encounter
        !river-encounter Day 2 Morning
        !river-encounter harmful Day 3  # GM only

Encounter Types:
    - Positive (1-10): Beneficial events, travel bonuses
    - Coincidental (11-40): Neutral events, flavor encounters
    - Uneventful (41-75): No mechanical impact, atmospheric text
    - Harmful (76-90): Minor setbacks, tests required
    - Accident (91-100): Major incidents with complex mechanics

Channel Requirements:
    - boat-travelling-notifications: GM notification channel (optional)
    - boat-travelling-log: Command logging channel (optional)

Permissions:
    - Server owner or GM role can override encounter type
    - All users can generate random encounters
"""

import discord
from typing import Literal, Optional
from discord import app_commands
from discord.ext import commands
from utils.encounter_mechanics import (
    get_encounter_emoji,
    get_severity_color,
    format_encounter_type_name,
    format_effects_list,
    format_test_requirement,
    format_damage_result,
    format_mechanics_summary,
)
from commands.permissions import is_gm
from commands.constants import CHANNEL_GM_NOTIFICATIONS
from commands.enhanced_error_handlers import (
    error_logger,
    handle_bot_exception,
    handle_generic_error,
)
from commands.exceptions import PermissionDeniedException
from commands.services.command_logger import CommandLogger
from commands.services.encounter_service import EncounterService


# Footer hints for each encounter type
FOOTER_HINTS = {
    "positive": "Something stirs along the riverbank...",
    "coincidental": "The river reveals its mysteries...",
    "uneventful": "Another mile of murky water...",
    "harmful": "The river demands its toll...",
    "accident": "Something vital fails at the worst moment...",
}

DEFAULT_FOOTER_HINT = "The journey continues..."

# Test emoji indicators
EMOJI_TEST_PRIMARY = "1️⃣"
EMOJI_TEST_SECONDARY = "2️⃣"
EMOJI_TEST_REPAIR = "🔧"
EMOJI_TEST_EACH_ROUND = "🔄"
EMOJI_TEST_EXTINGUISH = "🔥"
EMOJI_TEST_OVERBOARD = "🌊"
EMOJI_TEST_RESCUE = "🆘"

# Field emojis
EMOJI_DICE = "🎲"
EMOJI_TARGET = "🎯"
EMOJI_MECHANICS = "⚙️"
EMOJI_ADDITIONAL_HAZARDS = "⚠️"
EMOJI_CARGO_LOSS = "💰"


def format_player_flavor_embed(
    encounter_type: Literal["positive", "coincidental", "uneventful", "harmful", "accident"],
    flavor_text: str,
    stage: Optional[str] = None,
) -> discord.Embed:
    """
    Format the cryptic player message embed.

    Players receive atmospheric text without mechanical details to maintain
    immersion and narrative tension. The footer provides subtle hints about
    the encounter's nature without spoiling outcomes.

    Args:
        encounter_type: Type of encounter (positive, coincidental, uneventful, harmful, accident)
        flavor_text: Random grimdark flavor text from encounter data
        stage: Optional stage/time identifier (e.g., "Day 2 Afternoon")

    Returns:
        Discord embed with cryptic flavor text for public channel

    Example:
        >>> embed = format_player_flavor_embed("harmful", "Dark shapes circle...", "Day 3")
        >>> embed.title
        '⚠️ River Journey - Day 3'
    """
    emoji = get_encounter_emoji(encounter_type)
    color = get_severity_color(encounter_type)

    # Build title
    title = f"{emoji} River Journey"
    if stage:
        title += f" - {stage}"

    # Create embed with minimal info
    embed = discord.Embed(title=title, description=flavor_text, color=color)

    # Add cryptic footer hint
    embed.set_footer(text=FOOTER_HINTS.get(encounter_type, DEFAULT_FOOTER_HINT))

    return embed


def format_gm_simple_embed(encounter_data: dict, stage: Optional[str] = None) -> discord.Embed:
    """
    Format GM notification for simple encounters.

    Simple encounters include positive, coincidental, harmful, and uneventful
    types with straightforward mechanics. Provides full encounter details,
    effects, and roll information for GM adjudication.

    Args:
        encounter_data: Complete encounter data with type, title, description, effects, mechanics
        stage: Optional stage/time identifier (e.g., "Day 2 Midday")

    Returns:
        Discord embed for GM notifications channel

    Example:
        >>> data = {
        ...     "type": "positive",
        ...     "title": "Swift Current",
        ...     "description": "The river aids your journey.",
        ...     "effects": ["+10 to next Row test"],
        ...     "type_roll": 5,
        ...     "detail_roll": 42
        ... }
        >>> embed = format_gm_simple_embed(data, "Day 1")
        >>> "Swift Current" in embed.description
        True
    """
    encounter_type = encounter_data["type"]
    emoji = get_encounter_emoji(encounter_type)
    color = get_severity_color(encounter_type)
    type_name = format_encounter_type_name(encounter_type)

    # Build title
    title = f"{emoji} River Encounter - {type_name}"
    if stage:
        title += f"\nStage: {stage}"

    # Create embed
    embed = discord.Embed(
        title=title,
        description=f"**{encounter_data.get('title', 'Unknown')}**\n\n{encounter_data.get('description', 'No description')}",
        color=color,
    )

    # Add effects if any
    effects = encounter_data.get("effects", [])
    if effects:
        embed.add_field(name="Effects", value=format_effects_list(effects), inline=False)

    # Add mechanics if any
    mechanics = encounter_data.get("mechanics")
    if mechanics:
        embed.add_field(
            name=f"{EMOJI_MECHANICS} Mechanics",
            value=format_mechanics_summary(mechanics),
            inline=False,
        )

    # Add roll information
    roll_info = f"{EMOJI_DICE} Encounter Type Roll: {encounter_data['type_roll']} ({type_name})"
    if encounter_data.get("detail_roll"):
        roll_info += (
            f"\n{EMOJI_TARGET} Detail Roll: {encounter_data['detail_roll']} ({encounter_data.get('title', 'Unknown')})"
        )

    embed.add_field(name="Rolls", value=roll_info, inline=False)

    return embed


def format_gm_accident_embed(encounter_data: dict, stage: Optional[str] = None) -> discord.Embed:
    """
    Format GM notification for accident encounters with complex mechanics.

    Accidents (91-100 roll) involve multiple tests, damage, cargo loss, and
    cascading failures. This formatter presents all mechanical details in
    an organized, actionable format for the GM.

    Args:
        encounter_data: Complete accident data including mechanics, tests, damage, cargo loss
        stage: Optional stage/time identifier (e.g., "Night 2")

    Returns:
        Discord embed for GM notifications channel with detailed mechanics

    Example:
        >>> data = {
        ...     "type": "accident",
        ...     "title": "Broken Rudder",
        ...     "description": "The rudder snaps.",
        ...     "detail_roll": 93,
        ...     "mechanics": {
        ...         "primary_test": {"skill": "Sail", "difficulty": "+0"},
        ...         "primary_failure": {"damage": {"amount": "1d10", "target": "Hull"}}
        ...     }
        ... }
        >>> embed = format_gm_accident_embed(data)
        >>> "Broken Rudder" in embed.description
        True
    """
    emoji = get_encounter_emoji("accident")
    color = get_severity_color("accident")

    # Build title
    title = f"{emoji} River Accident!"
    if stage:
        title += f"\nStage: {stage}"

    # Create embed
    embed = discord.Embed(
        title=title,
        description=f"**{encounter_data.get('title', 'Unknown')}**\n\n{encounter_data.get('description', 'No description')}",
        color=color,
    )

    mechanics = encounter_data.get("mechanics", {})

    # Add required tests section
    tests_text = ""

    # Primary test
    if "primary_test" in mechanics:
        primary_test = mechanics["primary_test"]
        tests_text += f"{EMOJI_TEST_PRIMARY} **{format_test_requirement(primary_test)}**\n"

        # Primary failure
        if "primary_failure" in mechanics:
            failure = mechanics["primary_failure"]
            if "damage" in failure:
                tests_text += f"   • Failure: {format_damage_result(failure['damage'], failure.get('hits', 1))}\n"
            if "effect" in failure:
                tests_text += f"   • Failure: {failure['effect']}\n"

        tests_text += "\n"

    # Secondary test
    if "secondary_test" in mechanics:
        secondary_test = mechanics["secondary_test"]
        tests_text += f"{EMOJI_TEST_SECONDARY} **{format_test_requirement(secondary_test)}**\n"

        if "trigger" in secondary_test:
            tests_text += f"   • Trigger: {secondary_test['trigger']}\n"

        # Secondary failure
        if "secondary_failure" in mechanics:
            failure = mechanics["secondary_failure"]
            if "effect" in failure:
                tests_text += f"   • Failure: {failure['effect']}\n"

    # Single test for simpler accidents
    if "repair_test" in mechanics:
        repair = mechanics["repair_test"]
        tests_text += f"{EMOJI_TEST_REPAIR} **Repair: {format_test_requirement(repair)}**\n"
        if "time" in repair:
            tests_text += f"   • Time required: {repair['time']}\n"

    if "test_each_round" in mechanics:
        test = mechanics["test_each_round"]
        tests_text += f"{EMOJI_TEST_EACH_ROUND} **Each Round: {format_test_requirement(test)}**\n"

    if "extinguish_test" in mechanics:
        test = mechanics["extinguish_test"]
        tests_text += f"{EMOJI_TEST_EXTINGUISH} **To Extinguish: {format_test_requirement(test)}**\n"

    if "overboard_character" in mechanics:
        test = mechanics["overboard_character"]
        tests_text += f"{EMOJI_TEST_OVERBOARD} **Overboard Character: {format_test_requirement(test)}**\n"

    if "rescue_test" in mechanics:
        test = mechanics["rescue_test"]
        tests_text += f"{EMOJI_TEST_RESCUE} **Rescue: {format_test_requirement(test)}**\n"

    if tests_text:
        embed.add_field(
            name=f"{EMOJI_TARGET} Required Tests",
            value=tests_text.strip(),
            inline=False,
        )

    # Add cargo loss calculation if present
    if "cargo_loss" in encounter_data:
        cargo = encounter_data["cargo_loss"]
        cargo_text = "• **Formula:** 10 + ⌊(1d100 + 5) / 10⌋ × 10\n"
        cargo_text += f"• **Roll:** {cargo['roll']}\n"
        cargo_text += f"• **Calculated Loss:** {cargo['encumbrance_lost']} encumbrance"

        embed.add_field(
            name=f"{EMOJI_CARGO_LOSS} Cargo Loss Calculation",
            value=cargo_text,
            inline=False,
        )

    # Add mechanics summary
    summary_parts = []

    if "damage_type" in mechanics:
        summary_parts.append(f"• Damage type: {mechanics['damage_type']}")

    if "immediate_effect" in mechanics:
        summary_parts.append(f"• Immediate: {mechanics['immediate_effect']}")

    if "reference" in mechanics:
        summary_parts.append(f"• Reference: {mechanics['reference']}")

    if "duration" in mechanics:
        summary_parts.append(f"• Duration: {mechanics['duration']}")

    if "damage_per_turn" in mechanics:
        dmg = mechanics["damage_per_turn"]
        summary_parts.append(f"• Damage per turn: {dmg['amount']} to {dmg['target']}")

    if summary_parts:
        embed.add_field(
            name=f"{EMOJI_MECHANICS} Mechanics Summary",
            value="\n".join(summary_parts),
            inline=False,
        )

    # Add additional hazards if present
    if "additional_hazards" in mechanics:
        hazards = mechanics["additional_hazards"]
        hazard_text = hazards.get("risk", "")
        if "effects" in hazards:
            hazard_text += "\n" + "\n".join(f"• {effect}" for effect in hazards["effects"])

        embed.add_field(
            name=f"{EMOJI_ADDITIONAL_HAZARDS} Additional Hazards",
            value=hazard_text,
            inline=False,
        )

    # Add roll information
    roll_info = (
        f"{EMOJI_DICE} Accident Roll: {encounter_data['detail_roll']} ({encounter_data.get('title', 'Unknown')})"
    )

    if "cargo_loss" in encounter_data:
        cargo = encounter_data["cargo_loss"]
        roll_info += f"\n{EMOJI_DICE} Cargo Roll: {cargo['roll']} → {cargo['encumbrance_lost']} encumbrance lost"

    embed.set_footer(text=roll_info)

    return embed


async def send_gm_notification(guild: discord.Guild, encounter_data: dict, stage: Optional[str] = None) -> bool:
    """
    Send full encounter details to GM notifications channel.

    Attempts to find the boat-travelling-notifications channel and send
    detailed mechanical information for GM use. Handles missing channels
    and permission errors gracefully.

    Args:
        guild: Discord guild where command was invoked
        encounter_data: Complete encounter data from generate_encounter()
        stage: Optional stage/time identifier (e.g., "Day 2 Morning")

    Returns:
        True if notification sent successfully, False otherwise

    Note:
        This function fails silently on errors to avoid breaking the main
        command flow. The player message is always sent regardless of
        whether GM notification succeeds.

    Example:
        >>> # In async context
        >>> success = await send_gm_notification(guild, encounter_data, "Day 1")
        >>> if success:
        ...     print("GM notified")
    """
    # Find notifications channel
    channel = discord.utils.get(guild.text_channels, name=CHANNEL_GM_NOTIFICATIONS)

    if not channel:
        # Log warning but don't fail - GM notifications are optional
        error_logger.log_warning(
            message=f"GM notification channel '{CHANNEL_GM_NOTIFICATIONS}' not found",
            command_name="river-encounter",
            context_data={
                "guild_id": guild.id,
                "guild_name": guild.name,
            },
        )
        return False

    # Format appropriate embed based on encounter type
    if encounter_data["type"] == "accident":
        embed = format_gm_accident_embed(encounter_data, stage)
    else:
        embed = format_gm_simple_embed(encounter_data, stage)

    # Send to notifications channel
    try:
        await channel.send(embed=embed)
        return True
    except discord.errors.Forbidden as e:
        # Bot doesn't have permission to send in that channel
        error_logger.log_warning(
            message=f"Missing permissions to send to GM notifications channel: {e}",
            command_name="river-encounter",
            context_data={
                "channel_id": channel.id,
                "channel_name": channel.name,
                "guild_id": guild.id,
                "error_type": type(e).__name__,
            },
        )
        return False
    except Exception as e:  # noqa: BLE001
        # Other error, log but don't fail (broad exception intentional for resilience)
        error_logger.log_error(
            error=e,
            command_name="river-encounter",
            guild_id=str(guild.id),
            context_data={
                "channel_id": channel.id if channel else None,
                "error_type": type(e).__name__,
            },
        )
        return False


def setup_river_encounter(bot: commands.Bot):
    """
    Set up the river encounter command.

    Args:
        bot: The Discord bot instance
    """

    @bot.tree.command(
        name="river-encounter",
        description="Generate a random river encounter for your journey",
    )
    @app_commands.describe(
        stage="Optional stage/time identifier (e.g., 'Day 2 Afternoon')",
        encounter_type="Override encounter type (GM only: positive, coincidental, uneventful, harmful, accident)",
    )
    @app_commands.choices(
        encounter_type=[
            app_commands.Choice(name="Positive", value="positive"),
            app_commands.Choice(name="Coincidental", value="coincidental"),
            app_commands.Choice(name="Uneventful", value="uneventful"),
            app_commands.Choice(name="Harmful", value="harmful"),
            app_commands.Choice(name="Accident", value="accident"),
        ]
    )
    async def river_encounter_slash(
        interaction: discord.Interaction,
        stage: Optional[str] = None,
        encounter_type: Optional[Literal["positive", "coincidental", "uneventful", "harmful", "accident"]] = None,
    ) -> None:
        """
        Slash command for river encounters.

        Generates a random river encounter with cryptic player text and
        detailed GM notification. GMs can override the encounter type for
        testing or story purposes.

        Args:
            interaction: Discord interaction from slash command
            stage: Optional stage/time identifier
            encounter_type: Optional encounter type override (GM only)
        """
        try:
            # Check if user is trying to override encounter type
            if encounter_type:
                # Verify user has GM permissions
                if not interaction.guild or not is_gm(interaction.user):
                    error = PermissionDeniedException(
                        command_name="river-encounter",
                        required_permission="GM role or server owner",
                        user_id=str(interaction.user.id),
                        user_message="❌ Only the server owner or users with the GM role can override encounter types.",
                    )
                    await handle_bot_exception(interaction, error, is_slash=True)
                    return

            # Generate encounter (with optional type override)
            service = EncounterService()
            encounter_data = service.generate_encounter(encounter_type=encounter_type)

            # Format player flavor embed (cryptic)
            player_embed = format_player_flavor_embed(encounter_data["type"], encounter_data["flavor_text"], stage)

            # Send to player (public)
            await interaction.response.send_message(embed=player_embed)

            # Send full details to GM notifications channel
            if interaction.guild:
                await send_gm_notification(interaction.guild, encounter_data, stage)
                # Send command log
                try:
                    logger = CommandLogger(bot=interaction.client)
                    fields = {"Actual Type": encounter_data["type"].title()}
                    if stage:
                        fields["Stage"] = stage
                    if encounter_type:
                        fields["Override Type"] = encounter_type.title()

                    # Build command string
                    command_str = "/river-encounter"
                    if stage:
                        command_str += f" stage:{stage}"
                    if encounter_type:
                        command_str += f" encounter_type:{encounter_type}"

                    await logger.log_command_from_context(
                        context=interaction,
                        command_name="river-encounter",
                        command_string=command_str,
                        fields=fields,
                        color=discord.Color.teal(),
                        is_slash=True,
                    )
                except (KeyError, AttributeError) as e:
                    # Log warning but don't fail the command
                    error_logger.log_warning(
                        message=f"Failed to log river-encounter command: {e}",
                        command_name="river-encounter",
                        context_data={
                            "user_id": str(interaction.user.id),
                            "error_type": type(e).__name__,
                        },
                    )

        except (discord.Forbidden, discord.HTTPException) as e:
            # Permission errors - encounter already sent, just log the issue
            error_logger.log_warning(
                message=f"Failed to send GM notification or log: {e}",
                command_name="river-encounter",
                context_data={
                    "user_id": str(interaction.user.id),
                    "error_type": type(e).__name__,
                },
            )

        except Exception as e:  # noqa: BLE001
            # Generic exception - inform user (broad exception intentional for user safety)
            await handle_generic_error(interaction, e, is_slash=True, command_name="river-encounter")

    @bot.command(name="river-encounter")
    async def river_encounter_prefix(
        ctx: commands.Context,
        encounter_type: Optional[str] = None,
        *,
        stage: Optional[str] = None,
    ) -> None:
        """
        Prefix command for river encounters.

        Generates a random river encounter with cryptic player text and
        detailed GM notification. GMs can specify encounter type as first
        argument for testing or story purposes.

        Args:
            ctx: Command context
            encounter_type: Optional encounter type (positive/coincidental/uneventful/harmful/accident)
            stage: Optional stage/time identifier (captures remaining text)

        Usage Examples:
            !river-encounter
            !river-encounter Day 2 Afternoon
            !river-encounter positive Morning Journey
            !river-encounter accident Day 3
        """
        # Validate encounter type if provided
        service = EncounterService()
        if encounter_type and not service.is_valid_encounter_type(encounter_type.lower()):
            # If first arg isn't a valid type, treat it as part of the stage
            if stage:
                stage = f"{encounter_type} {stage}"
            else:
                stage = encounter_type
            encounter_type = None
        elif encounter_type:
            encounter_type = encounter_type.lower()

            # Check if user is trying to override encounter type
            if ctx.guild and not is_gm(ctx.author):
                error = PermissionDeniedException(
                    command_name="river-encounter",
                    required_permission="GM role or server owner",
                    user_id=str(ctx.author.id),
                    user_message="❌ Only the server owner or users with the GM role can override encounter types.",
                )
                await handle_bot_exception(ctx, error, is_slash=False)
                return

        # Generate encounter (with optional type override)
        encounter_data = service.generate_encounter(encounter_type=encounter_type)

        # Format player flavor embed (cryptic)
        player_embed = format_player_flavor_embed(encounter_data["type"], encounter_data["flavor_text"], stage)

        # Send to player (public)
        await ctx.send(embed=player_embed)

        # Send full details to GM notifications channel
        if ctx.guild:
            await send_gm_notification(ctx.guild, encounter_data, stage)
            # Send command log
            try:
                logger = CommandLogger(bot=ctx.bot)
                fields = {"Actual Type": encounter_data["type"].title()}
                if stage:
                    fields["Stage"] = stage
                if encounter_type:
                    fields["Override Type"] = encounter_type.title()

                # Build command string
                command_str = "!river-encounter"
                if encounter_type:
                    command_str += f" {encounter_type}"
                if stage:
                    command_str += f" {stage}"

                await logger.log_command_from_context(
                    context=ctx,
                    command_name="river-encounter",
                    command_string=command_str,
                    fields=fields,
                    color=discord.Color.teal(),
                    is_slash=False,
                )
            except (KeyError, AttributeError) as e:
                # Log warning but don't fail the command
                error_logger.log_warning(
                    message=f"Failed to log river-encounter command: {e}",
                    command_name="river-encounter",
                    context_data={
                        "user_id": str(ctx.author.id),
                        "error_type": type(e).__name__,
                    },
                )
