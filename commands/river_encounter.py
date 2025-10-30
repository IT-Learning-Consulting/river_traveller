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
from typing import Literal, Optional, Union
from discord import app_commands
from discord.ext import commands
from utils.encounter_mechanics import (
    generate_encounter,
    get_encounter_emoji,
    get_severity_color,
    format_encounter_type_name,
    format_effects_list,
    format_test_requirement,
    format_damage_result,
    format_mechanics_summary,
)


# Encounter type constants
ENCOUNTER_TYPE_POSITIVE = "positive"
ENCOUNTER_TYPE_COINCIDENTAL = "coincidental"
ENCOUNTER_TYPE_UNEVENTFUL = "uneventful"
ENCOUNTER_TYPE_HARMFUL = "harmful"
ENCOUNTER_TYPE_ACCIDENT = "accident"

VALID_ENCOUNTER_TYPES = [
    ENCOUNTER_TYPE_POSITIVE,
    ENCOUNTER_TYPE_COINCIDENTAL,
    ENCOUNTER_TYPE_UNEVENTFUL,
    ENCOUNTER_TYPE_HARMFUL,
    ENCOUNTER_TYPE_ACCIDENT,
]

# Footer hints for each encounter type
FOOTER_HINTS = {
    ENCOUNTER_TYPE_POSITIVE: "Something stirs along the riverbank...",
    ENCOUNTER_TYPE_COINCIDENTAL: "The river reveals its mysteries...",
    ENCOUNTER_TYPE_UNEVENTFUL: "Another mile of murky water...",
    ENCOUNTER_TYPE_HARMFUL: "The river demands its toll...",
    ENCOUNTER_TYPE_ACCIDENT: "Something vital fails at the worst moment...",
}

DEFAULT_FOOTER_HINT = "The journey continues..."

# Channel names
CHANNEL_GM_NOTIFICATIONS = "boat-travelling-notifications"
CHANNEL_COMMAND_LOG = "boat-travelling-log"

# Role name
ROLE_GM = "GM"

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
    encounter_type: Literal[
        "positive", "coincidental", "uneventful", "harmful", "accident"
    ],
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


def format_gm_simple_embed(
    encounter_data: dict, stage: Optional[str] = None
) -> discord.Embed:
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
        embed.add_field(
            name="Effects", value=format_effects_list(effects), inline=False
        )

    # Add mechanics if any
    mechanics = encounter_data.get("mechanics")
    if mechanics:
        embed.add_field(
            name=f"{EMOJI_MECHANICS} Mechanics",
            value=format_mechanics_summary(mechanics),
            inline=False,
        )

    # Add roll information
    roll_info = (
        f"{EMOJI_DICE} Encounter Type Roll: {encounter_data['type_roll']} ({type_name})"
    )
    if encounter_data.get("detail_roll"):
        roll_info += f"\n{EMOJI_TARGET} Detail Roll: {encounter_data['detail_roll']} ({encounter_data.get('title', 'Unknown')})"

    embed.add_field(name="Rolls", value=roll_info, inline=False)

    return embed


def format_gm_accident_embed(
    encounter_data: dict, stage: Optional[str] = None
) -> discord.Embed:
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
    emoji = get_encounter_emoji(ENCOUNTER_TYPE_ACCIDENT)
    color = get_severity_color(ENCOUNTER_TYPE_ACCIDENT)

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
        tests_text += (
            f"{EMOJI_TEST_PRIMARY} **{format_test_requirement(primary_test)}**\n"
        )

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
        tests_text += (
            f"{EMOJI_TEST_SECONDARY} **{format_test_requirement(secondary_test)}**\n"
        )

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
        tests_text += (
            f"{EMOJI_TEST_REPAIR} **Repair: {format_test_requirement(repair)}**\n"
        )
        if "time" in repair:
            tests_text += f"   • Time required: {repair['time']}\n"

    if "test_each_round" in mechanics:
        test = mechanics["test_each_round"]
        tests_text += (
            f"{EMOJI_TEST_EACH_ROUND} **Each Round: {format_test_requirement(test)}**\n"
        )

    if "extinguish_test" in mechanics:
        test = mechanics["extinguish_test"]
        tests_text += f"{EMOJI_TEST_EXTINGUISH} **To Extinguish: {format_test_requirement(test)}**\n"

    if "overboard_character" in mechanics:
        test = mechanics["overboard_character"]
        tests_text += f"{EMOJI_TEST_OVERBOARD} **Overboard Character: {format_test_requirement(test)}**\n"

    if "rescue_test" in mechanics:
        test = mechanics["rescue_test"]
        tests_text += (
            f"{EMOJI_TEST_RESCUE} **Rescue: {format_test_requirement(test)}**\n"
        )

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
            hazard_text += "\n" + "\n".join(
                f"• {effect}" for effect in hazards["effects"]
            )

        embed.add_field(
            name=f"{EMOJI_ADDITIONAL_HAZARDS} Additional Hazards",
            value=hazard_text,
            inline=False,
        )

    # Add roll information
    roll_info = f"{EMOJI_DICE} Accident Roll: {encounter_data['detail_roll']} ({encounter_data.get('title', 'Unknown')})"

    if "cargo_loss" in encounter_data:
        cargo = encounter_data["cargo_loss"]
        roll_info += f"\n{EMOJI_DICE} Cargo Roll: {cargo['roll']} → {cargo['encumbrance_lost']} encumbrance lost"

    embed.set_footer(text=roll_info)

    return embed


async def send_gm_notification(
    guild: discord.Guild, encounter_data: dict, stage: Optional[str] = None
) -> bool:
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
        return False

    # Format appropriate embed based on encounter type
    if encounter_data["type"] == ENCOUNTER_TYPE_ACCIDENT:
        embed = format_gm_accident_embed(encounter_data, stage)
    else:
        embed = format_gm_simple_embed(encounter_data, stage)

    # Send to notifications channel
    try:
        await channel.send(embed=embed)
        return True
    except discord.errors.Forbidden:
        # Bot doesn't have permission to send in that channel
        return False
    except Exception:  # noqa: BLE001
        # Other error, silently fail (broad exception intentional for resilience)
        return False


def is_gm(user: discord.Member) -> bool:
    """
    Check if user has GM permissions (server owner or GM role).

    Used to determine if a user can override encounter types when generating
    encounters. This prevents players from metagaming by forcing specific
    encounter outcomes.

    Args:
        user: Discord member to check for GM permissions

    Returns:
        True if user is server owner or has GM role, False otherwise

    Example:
        >>> # Mock user with GM role
        >>> if is_gm(member):
        ...     # Allow encounter type override
        ...     pass
    """
    # Server owner is always GM
    if user.guild.owner_id == user.id:
        return True

    # Check for GM role
    gm_role = discord.utils.get(user.guild.roles, name=ROLE_GM)
    if gm_role and gm_role in user.roles:
        return True

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
            app_commands.Choice(name="Positive", value=ENCOUNTER_TYPE_POSITIVE),
            app_commands.Choice(name="Coincidental", value=ENCOUNTER_TYPE_COINCIDENTAL),
            app_commands.Choice(name="Uneventful", value=ENCOUNTER_TYPE_UNEVENTFUL),
            app_commands.Choice(name="Harmful", value=ENCOUNTER_TYPE_HARMFUL),
            app_commands.Choice(name="Accident", value=ENCOUNTER_TYPE_ACCIDENT),
        ]
    )
    async def river_encounter_slash(
        interaction: discord.Interaction,
        stage: Optional[str] = None,
        encounter_type: Optional[
            Literal["positive", "coincidental", "uneventful", "harmful", "accident"]
        ] = None,
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
                    await interaction.response.send_message(
                        "❌ Only the server owner or users with the GM role can override encounter types.",
                        ephemeral=True,
                    )
                    return

            # Generate encounter (with optional type override)
            encounter_data = generate_encounter(encounter_type=encounter_type)

            # Format player flavor embed (cryptic)
            player_embed = format_player_flavor_embed(
                encounter_data["type"], encounter_data["flavor_text"], stage
            )

            # Send to player (public)
            await interaction.response.send_message(embed=player_embed)

            # Send full details to GM notifications channel
            if interaction.guild:
                await send_gm_notification(interaction.guild, encounter_data, stage)
                # Send command log
                await _send_command_log(
                    interaction,
                    stage,
                    encounter_type,
                    encounter_data["type"],
                    is_slash=True,
                )

        except (discord.Forbidden, discord.HTTPException):
            # Permission errors - encounter already sent, just log the issue
            pass

        except Exception as e:  # noqa: BLE001
            # Generic exception - inform user (broad exception intentional for user safety)
            try:
                await interaction.followup.send(
                    f"❌ An error occurred: {str(e)}", ephemeral=True
                )
            except Exception:  # noqa: BLE001, S110
                # Even followup failed, give up silently (broad exception intentional)
                pass

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
        if encounter_type and encounter_type.lower() not in VALID_ENCOUNTER_TYPES:
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
                await ctx.send(
                    "❌ Only the server owner or users with the GM role can override encounter types."
                )
                return

        # Generate encounter (with optional type override)
        encounter_data = generate_encounter(encounter_type=encounter_type)

        # Format player flavor embed (cryptic)
        player_embed = format_player_flavor_embed(
            encounter_data["type"], encounter_data["flavor_text"], stage
        )

        # Send to player (public)
        await ctx.send(embed=player_embed)

        # Send full details to GM notifications channel
        if ctx.guild:
            await send_gm_notification(ctx.guild, encounter_data, stage)
            # Send command log
            await _send_command_log(
                ctx, stage, encounter_type, encounter_data["type"], is_slash=False
            )


async def _send_command_log(
    context: Union[discord.Interaction, commands.Context],
    stage: Optional[str],
    encounter_type_override: Optional[str],
    actual_type: str,
    is_slash: bool,
) -> None:
    """
    Send command details to boat-travelling-log channel.

    Logs all river encounter commands with user info, parameters, and
    actual outcome. Helps GMs track command usage and debug issues.

    Args:
        context: Discord interaction or command context
        stage: Optional stage/time identifier provided by user
        encounter_type_override: Encounter type override (if GM forced specific type)
        actual_type: Actual encounter type generated
        is_slash: True if slash command, False if prefix command

    Note:
        Fails silently if log channel doesn't exist or bot lacks permissions.
        Logging is optional and should not break the main command flow.

    Example:
        >>> # In async context
        >>> await _send_command_log(ctx, "Day 2", "harmful", "harmful", False)
    """
    try:
        # Find the log channel
        log_channel = discord.utils.get(
            context.guild.text_channels, name=CHANNEL_COMMAND_LOG
        )
        if not log_channel:
            return  # Silently fail if log channel doesn't exist

        # Get username
        if is_slash:
            username = context.user.display_name
            user_id = context.user.id
        else:
            username = context.author.display_name
            user_id = context.author.id

        # Build command string
        if is_slash:
            command_str = "/river-encounter"
            if stage:
                command_str += f" stage:{stage}"
            if encounter_type_override:
                command_str += f" encounter_type:{encounter_type_override}"
        else:
            command_str = "!river-encounter"
            if encounter_type_override:
                command_str += f" {encounter_type_override}"
            if stage:
                command_str += f" {stage}"

        # Create log embed
        log_embed = discord.Embed(
            title="🌊 Command Log: River Encounter",
            description=f"**User:** {username} (`{user_id}`)\n**Command:** `{command_str}`",
            color=discord.Color.teal(),
            timestamp=discord.utils.utcnow(),
        )

        if stage:
            log_embed.add_field(name="Stage", value=stage, inline=True)

        if encounter_type_override:
            log_embed.add_field(
                name="Override Type", value=encounter_type_override.title(), inline=True
            )

        log_embed.add_field(name="Actual Type", value=actual_type.title(), inline=True)

        await log_channel.send(embed=log_embed)

    except (discord.Forbidden, discord.HTTPException, AttributeError):
        # Silently fail - logging is not critical
        pass
