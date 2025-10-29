"""
River Encounter Command

Generates random river encounters with cryptic player messages and detailed
GM notifications. Implements the dual-message system where players see only
atmospheric flavor text while GMs receive full mechanical details.
"""

import discord
from typing import Optional
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


def format_player_flavor_embed(
    encounter_type: str, flavor_text: str, stage: Optional[str] = None
) -> discord.Embed:
    """
    Format the cryptic player message embed.

    Args:
        encounter_type: Type of encounter
        flavor_text: Random grimdark flavor text
        stage: Optional stage/time identifier

    Returns:
        Discord embed for players (public)
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
    footer_hints = {
        "positive": "Something stirs along the riverbank...",
        "coincidental": "The river reveals its mysteries...",
        "uneventful": "Another mile of murky water...",
        "harmful": "The river demands its toll...",
        "accident": "Something vital fails at the worst moment...",
    }

    embed.set_footer(text=footer_hints.get(encounter_type, "The journey continues..."))

    return embed


def format_gm_simple_embed(
    encounter_data: dict, stage: Optional[str] = None
) -> discord.Embed:
    """
    Format GM notification for simple encounters (positive, coincidental, harmful, uneventful).

    Args:
        encounter_data: Complete encounter data
        stage: Optional stage/time identifier

    Returns:
        Discord embed for GM (notifications channel)
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
            name="⚙️ Mechanics", value=format_mechanics_summary(mechanics), inline=False
        )

    # Add roll information
    roll_info = f"🎲 Encounter Type Roll: {encounter_data['type_roll']} ({type_name})"
    if encounter_data.get("detail_roll"):
        roll_info += f"\n🎯 Detail Roll: {encounter_data['detail_roll']} ({encounter_data.get('title', 'Unknown')})"

    embed.add_field(name="Rolls", value=roll_info, inline=False)

    return embed


def format_gm_accident_embed(
    encounter_data: dict, stage: Optional[str] = None
) -> discord.Embed:
    """
    Format GM notification for accident encounters (complex mechanics).

    Args:
        encounter_data: Complete accident data
        stage: Optional stage/time identifier

    Returns:
        Discord embed for GM (notifications channel)
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
        test_num = "1️⃣"
        primary_test = mechanics["primary_test"]
        tests_text += f"{test_num} **{format_test_requirement(primary_test)}**\n"

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
        test_num = "2️⃣"
        secondary_test = mechanics["secondary_test"]
        tests_text += f"{test_num} **{format_test_requirement(secondary_test)}**\n"

        if "trigger" in secondary_test:
            tests_text += f"   • Trigger: {secondary_test['trigger']}\n"

        # Secondary failure
        if "secondary_failure" in mechanics:
            failure = mechanics["secondary_failure"]
            if "effect" in failure:
                tests_text += f"   • Failure: {failure['effect']}\n"

    # Single test for simpler accidents
    if "repair_test" in mechanics:
        test_num = "🔧"
        repair = mechanics["repair_test"]
        tests_text += f"{test_num} **Repair: {format_test_requirement(repair)}**\n"
        if "time" in repair:
            tests_text += f"   • Time required: {repair['time']}\n"

    if "test_each_round" in mechanics:
        test_num = "🔄"
        test = mechanics["test_each_round"]
        tests_text += f"{test_num} **Each Round: {format_test_requirement(test)}**\n"

    if "extinguish_test" in mechanics:
        test_num = "🔥"
        test = mechanics["extinguish_test"]
        tests_text += f"{test_num} **To Extinguish: {format_test_requirement(test)}**\n"

    if "overboard_character" in mechanics:
        test_num = "🌊"
        test = mechanics["overboard_character"]
        tests_text += (
            f"{test_num} **Overboard Character: {format_test_requirement(test)}**\n"
        )

    if "rescue_test" in mechanics:
        test_num = "🆘"
        test = mechanics["rescue_test"]
        tests_text += f"{test_num} **Rescue: {format_test_requirement(test)}**\n"

    if tests_text:
        embed.add_field(
            name="🎯 Required Tests", value=tests_text.strip(), inline=False
        )

    # Add cargo loss calculation if present
    if "cargo_loss" in encounter_data:
        cargo = encounter_data["cargo_loss"]
        cargo_text = "• **Formula:** 10 + ⌊(1d100 + 5) / 10⌋ × 10\n"
        cargo_text += f"• **Roll:** {cargo['roll']}\n"
        cargo_text += f"• **Calculated Loss:** {cargo['encumbrance_lost']} encumbrance"

        embed.add_field(
            name="💰 Cargo Loss Calculation", value=cargo_text, inline=False
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
            name="⚙️ Mechanics Summary", value="\n".join(summary_parts), inline=False
        )

    # Add additional hazards if present
    if "additional_hazards" in mechanics:
        hazards = mechanics["additional_hazards"]
        hazard_text = hazards.get("risk", "")
        if "effects" in hazards:
            hazard_text += "\n" + "\n".join(
                f"• {effect}" for effect in hazards["effects"]
            )

        embed.add_field(name="⚠️ Additional Hazards", value=hazard_text, inline=False)

    # Add roll information
    roll_info = f"🎲 Accident Roll: {encounter_data['detail_roll']} ({encounter_data.get('title', 'Unknown')})"

    if "cargo_loss" in encounter_data:
        cargo = encounter_data["cargo_loss"]
        roll_info += f"\n🎲 Cargo Roll: {cargo['roll']} → {cargo['encumbrance_lost']} encumbrance lost"

    embed.set_footer(text=roll_info)

    return embed


async def send_gm_notification(
    guild: discord.Guild, encounter_data: dict, stage: Optional[str] = None
) -> bool:
    """
    Send full encounter details to GM notifications channel.

    Args:
        guild: Discord guild
        encounter_data: Complete encounter data
        stage: Optional stage/time identifier

    Returns:
        True if notification sent, False otherwise
    """
    # Find notifications channel
    channel = discord.utils.get(
        guild.text_channels, name="boat-travelling-notifications"
    )

    if not channel:
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
    except discord.errors.Forbidden:
        # Bot doesn't have permission to send in that channel
        return False
    except Exception:
        # Other error, silently fail
        return False


def is_gm(user: discord.Member) -> bool:
    """
    Check if user is a GM (server owner or has GM role).

    Args:
        user: Discord member to check

    Returns:
        True if user is GM, False otherwise
    """
    # Server owner is always GM
    if user.guild.owner_id == user.id:
        return True

    # Check for GM role
    gm_role = discord.utils.get(user.guild.roles, name="GM")
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
        encounter_type="Override encounter type (positive, coincidental, uneventful, harmful, accident)",
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
        encounter_type: Optional[str] = None,
    ):
        """Slash command for river encounters."""
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

    @bot.command(name="river-encounter")
    async def river_encounter_prefix(
        ctx: commands.Context,
        encounter_type: Optional[str] = None,
        *,
        stage: Optional[str] = None,
    ):
        """
        Prefix command for river encounters.

        Usage:
          !river-encounter [stage]
          !river-encounter positive [stage]
          !river-encounter accident Day 2
        """
        # Validate encounter type if provided
        valid_types = ["positive", "coincidental", "uneventful", "harmful", "accident"]
        if encounter_type and encounter_type.lower() not in valid_types:
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
