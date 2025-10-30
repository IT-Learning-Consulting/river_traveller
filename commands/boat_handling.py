"""
Boat Handling Command Module for WFRP River Travel.

This module implements boat handling tests for river navigation, which are central
to WFRP river-based campaigns. Characters use either Sail or Row skills to navigate
the river, with bonuses from Navigation knowledge and penalties from weather conditions.

The module handles:
- Character skill selection (Sail preferred, Row as fallback)
- Lore (Riverways) bonus calculation (first digit of skill value)
- Weather modifier integration from active journeys
- WFRP Success Level calculation and doubles detection
- Rich narrative outcomes based on success/failure degrees
- Command logging to boat-travelling-log channel

Example usage:
    /boat-handling anara           # Basic test at default difficulty
    /boat-handling emmerich -20    # Hard difficulty test
    /boat-handling hildric 0 dusk  # Test at specific time of day
"""

from typing import Union

import discord
from discord import app_commands
from discord.ext import commands

# Import from our modules
from db.character_data import (
    get_character,
    get_available_characters,
)
from utils.modifier_calculator import (
    get_active_weather_modifiers,
    format_weather_impact_for_embed,
)
from commands.constants import DEFAULT_TIME
from commands.error_handlers import handle_discord_error, handle_value_error
from commands.services.boat_handling_service import (
    BoatHandlingService,
    BoatHandlingResult,
)
from commands.services.command_logger import CommandLogger


# ============================================================================
# CONSTANTS
# ============================================================================

# Difficulty tier names for display
DIFFICULTY_TIERS = {
    -50: "Impossible",
    -40: "Futile",
    -30: "Very Difficult",
    -20: "Hard",
    -10: "Difficult",
    0: "Challenging",
    20: "Average",
    40: "Easy",
    60: "Very Easy",
}

# Color mapping from service color names to Discord colors
COLOR_MAP = {
    "gold": discord.Color.gold(),
    "green": discord.Color.green(),
    "orange": discord.Color.orange(),
    "red": discord.Color.red(),
    "dark_red": discord.Color.dark_red(),
}


# ============================================================================
# COMMAND SETUP
# ============================================================================


def setup(bot: commands.Bot) -> None:
    """
    Register boat-handling command with the bot.

    This function is called from main.py during bot initialization. It registers
    both slash (/) and prefix (!) command variants, sharing the same logic through
    _perform_boat_handling().

    Args:
        bot: The Discord bot instance to register commands with.

    Note:
        The slash command provides helpful autocomplete choices for character names
        and time of day, improving UX compared to the prefix command.
    """

    # Slash command
    @bot.tree.command(
        name="boat-handling",
        description="Make a WFRP Boat Handling Test for a character",
    )
    @app_commands.describe(
        character="Character name (anara, emmerich, hildric, oktavian, lupus)",
        difficulty="Test difficulty modifier (default: +0 Challenging)",
        time_of_day="Time of day (affects wind conditions, default: midday)",
    )
    @app_commands.choices(
        character=[
            app_commands.Choice(name="Anara of Sānxiá", value="anara"),
            app_commands.Choice(name="Emmerich Falkenrath", value="emmerich"),
            app_commands.Choice(name="Hildric Sokhlundt", value="hildric"),
            app_commands.Choice(name="Oktavian Babel", value="oktavian"),
            app_commands.Choice(name="Lupus Leonard Joachim Rohrig", value="lupus"),
        ],
        time_of_day=[
            app_commands.Choice(name="Dawn", value="dawn"),
            app_commands.Choice(name="Midday", value="midday"),
            app_commands.Choice(name="Dusk", value="dusk"),
            app_commands.Choice(name="Midnight", value="midnight"),
        ],
    )
    async def boat_handling_slash(
        interaction: discord.Interaction,
        character: str,
        difficulty: int = 0,
        time_of_day: str = DEFAULT_TIME,
    ):
        """Make a Boat Handling Test (Row or Sail) for a character."""
        await _perform_boat_handling(
            interaction, character, difficulty, time_of_day, is_slash=True
        )

    # Prefix command
    @bot.command(name="boat-handling")
    async def boat_handling_prefix(
        ctx, character: str, difficulty: int = 0, time_of_day: str = DEFAULT_TIME
    ):
        """Make a Boat Handling Test (Row or Sail) for a character."""
        await _perform_boat_handling(
            ctx, character, difficulty, time_of_day, is_slash=False
        )

    async def _perform_boat_handling(
        context: Union[discord.Interaction, commands.Context],
        character: str,
        difficulty: int,
        time_of_day: str,
        is_slash: bool,
    ) -> None:
        """
        Perform a boat handling test with full WFRP mechanics.

        This is the core logic shared by both slash and prefix commands. It handles:
        1. Weather modifier lookup for the specified time of day
        2. Character validation and skill determination (Sail vs Row)
        3. Lore (Riverways) bonus calculation
        4. Target number calculation with all modifiers
        5. D100 roll and Success Level calculation
        6. Doubles detection for crits/fumbles
        7. Rich narrative outcome generation
        8. Command logging to boat-travelling-log channel

        Args:
            context: Discord interaction (slash) or command context (prefix)
            character: Character key (e.g., "anara", "emmerich")
            difficulty: Base difficulty modifier (-50 to +60)
            time_of_day: When the test occurs ("dawn", "midday", "dusk", "midnight")
            is_slash: True if called from slash command, False if prefix command

        Raises:
            ValueError: If character doesn't exist or has no boat handling skills
            discord.DiscordException: If Discord API call fails

        Note:
            Weather modifiers are automatically applied if a journey is active.
            Errors are caught and displayed as user-friendly embed messages.
        """
        try:
            # Get active weather modifiers if available
            guild_id = str(context.guild.id) if context.guild else None
            weather_mods = None
            if guild_id:
                weather_mods = get_active_weather_modifiers(guild_id, time_of_day)

            # Apply weather-based difficulty modifier
            original_difficulty = difficulty
            weather_penalty = 0
            if weather_mods and weather_mods["boat_handling_penalty"] != 0:
                weather_penalty = weather_mods["boat_handling_penalty"]
                difficulty += weather_penalty

            # Normalize character name
            char_key = character.lower().strip()

            # Check if character exists
            char = get_character(char_key)
            if char is None:
                available = ", ".join(get_available_characters())
                raise ValueError(
                    f"Character '{character}' not found. Available: {available}"
                )

            # Perform boat handling test using service
            service = BoatHandlingService()
            result = service.perform_boat_test(
                character_data=char,
                difficulty=difficulty,
                weather_penalty=weather_penalty,
            )

            # Build and send Discord embed
            embed = _build_boat_handling_embed(
                result=result,
                context=context,
                weather_mods=weather_mods,
                original_difficulty=original_difficulty,
                time_of_day=time_of_day,
                is_slash=is_slash,
            )

            # Send response
            if is_slash:
                await context.response.send_message(embed=embed)
            else:
                await context.send(embed=embed)

            # Send command log to boat-travelling-log channel
            logger = CommandLogger()
            fields = {
                "Character": character.title(),
                "Difficulty": f"{original_difficulty:+d}",
                "Time of Day": time_of_day.title(),
            }

            # Build command string
            if is_slash:
                command_str = f"/boat-handling character:{character}"
                if difficulty != 0:
                    command_str += f" difficulty:{original_difficulty}"
                if time_of_day != DEFAULT_TIME:
                    command_str += f" time_of_day:{time_of_day}"
            else:
                command_str = f"!boat-handling {character}"
                if difficulty != 0:
                    command_str += f" {original_difficulty}"
                if time_of_day != DEFAULT_TIME:
                    command_str += f" {time_of_day}"

            await logger.log_command_from_context(
                context=context,
                command_name="boat-handling",
                command_string=command_str,
                fields=fields,
                is_slash=is_slash,
            )

        except ValueError as e:
            await handle_value_error(
                context,
                e,
                is_slash,
                "Boat Handling",
                usage_examples=[
                    "/boat-handling anara",
                    "/boat-handling emmerich -20",
                    "/boat-handling hildric 0 dusk",
                ],
            )

        except (discord.DiscordException, KeyError, AttributeError) as e:
            await handle_discord_error(context, e, is_slash)

    def _build_boat_handling_embed(
        result: BoatHandlingResult,
        context: Union[discord.Interaction, commands.Context],
        weather_mods: dict,
        original_difficulty: int,
        time_of_day: str,
        is_slash: bool,
    ) -> discord.Embed:
        """
        Build Discord embed from boat handling test result.

        Args:
            result: BoatHandlingResult from service containing all test data
            context: Discord interaction or command context
            weather_mods: Weather modifiers dict (if any)
            original_difficulty: Base difficulty before weather
            time_of_day: Time of day for weather display
            is_slash: True if slash command, False if prefix

        Returns:
            Formatted Discord embed ready to send
        """
        # Get base color from result, override if critical/fumble
        color = COLOR_MAP.get(result.outcome_color, discord.Color.blue())
        if result.is_critical:
            color = discord.Color.gold()
        elif result.is_fumble:
            color = discord.Color.dark_red()

        # Build embed
        embed = discord.Embed(
            title=f"🚢 Boat Handling Test: {result.character_name}",
            color=color,
        )

        # Character info
        embed.add_field(
            name="Character",
            value=f"{result.character_name}\n{result.character_species} • {result.character_status}",
            inline=True,
        )

        # Skill breakdown
        skill_breakdown = f"**{result.skill_name}:** {result.skill_value}"
        if result.lore_bonus > 0:
            skill_breakdown += f"\n**Lore (Riverways) Bonus:** +{result.lore_bonus}"

        # Always show difficulty if it's not default Challenging or if weather is active
        if original_difficulty != 0 or weather_mods:
            diff_name = DIFFICULTY_TIERS.get(
                original_difficulty, f"{original_difficulty:+d}"
            )

            # Show weather-modified difficulty if weather is active
            if weather_mods:
                if result.weather_penalty != 0:
                    # Weather has a penalty - show base, modifier, and final
                    modified_diff_name = DIFFICULTY_TIERS.get(
                        result.final_difficulty, f"{result.final_difficulty:+d}"
                    )
                    skill_breakdown += (
                        f"\n**Base Difficulty:** {diff_name} ({original_difficulty:+d})"
                    )
                    skill_breakdown += (
                        f"\n**Weather Modifier:** {result.weather_penalty:+d}"
                    )
                    skill_breakdown += f"\n**Final Difficulty:** {modified_diff_name} ({result.final_difficulty:+d})"
                else:
                    # Weather is active but no penalty
                    skill_breakdown += (
                        f"\n**Difficulty:** {diff_name} ({original_difficulty:+d})"
                    )
                    skill_breakdown += "\n**Weather Modifier:** 0 (no penalty)"
            else:
                # No weather, just show difficulty
                skill_breakdown += (
                    f"\n**Difficulty:** {diff_name} ({original_difficulty:+d})"
                )

        embed.add_field(name="Skill Check", value=skill_breakdown, inline=True)

        # Roll result
        embed.add_field(
            name="Target / Roll",
            value=f"**{result.final_target}** / **{result.roll_value}**",
            inline=True,
        )

        # Outcome
        sl_display = f"{result.success_level:+d}" if result.success_level != 0 else "0"
        outcome_text = f"**{result.outcome}**\nSuccess Level: {sl_display}"

        if result.is_critical:
            outcome_text += "\n⚡ **CRITICAL SUCCESS!**"
        elif result.is_fumble:
            outcome_text += "\n💀 **FUMBLE!**"

        embed.add_field(name="Result", value=outcome_text, inline=False)

        # Flavor text
        embed.add_field(name="Narrative", value=result.flavor_text, inline=False)

        # Mechanical consequences
        embed.add_field(
            name="Mechanical Effect", value=result.mechanics_text, inline=False
        )

        # Weather impact (if active)
        if weather_mods:
            weather_text = format_weather_impact_for_embed(weather_mods)
            embed.add_field(
                name=f"🌦️ Weather Impact ({time_of_day.title()})",
                value=weather_text,
                inline=False,
            )

        # Footer
        if is_slash:
            embed.set_footer(text=f"Test by {context.user.display_name}")
        else:
            embed.set_footer(text=f"Test by {context.author.display_name}")

        return embed
