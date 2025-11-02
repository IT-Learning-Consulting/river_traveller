"""
Roll Dice Command

Implements flexible dice rolling with full WFRP 4th Edition mechanics support.
Handles standard dice notation (XdY+Z) and integrates with WFRP skill tests,
success levels, and doubles classification (criticals/fumbles).

Usage Examples:
    Slash Commands:
        /roll 1d100                         # Simple d100 roll
        /roll 3d10                          # Roll 3d10
        /roll 2d6+5                         # Roll with modifier
        /roll 1d100 target:45 modifier:20   # WFRP skill test (Average difficulty)
        /roll 1d100 target:45 modifier:-20  # WFRP hard test

    Prefix Commands:
        !roll 1d100
        !roll 3d10
        !roll 2d6+5
        !roll 1d100 45 20                   # WFRP skill test with Average (+20)
        !roll 1d100 45 -20                  # WFRP hard test

WFRP 4th Edition Mechanics:
    - Success Level (SL) = (Final Target ÷ 10) - (Roll ÷ 10)
    - Difficulty modifiers: -50 (Impossible) to +60 (Very Easy)
    - Default modifier: +20 (Average difficulty)
    - Doubles on d100 can trigger criticals or fumbles
    - Roll of 100 is always a fumble
    - Roll of 01 counts as doubles

Difficulty Reference:
    +60: Very Easy
    +40: Easy
    +20: Average (default)
      0: Challenging
    -10: Difficult
    -20: Hard
    -30: Very Difficult
    -40: Futile
    -50: Impossible

Channel Requirements:
    - boat-travelling-log: Command logging channel (optional)
"""

from typing import Optional, Union
import discord
from discord import app_commands
from discord.ext import commands

# Import from our modules
from commands.services.roll_service import RollService, RollResult
from commands.services.command_logger import CommandLogger
from commands.constants import (
    DIFFICULTY_NAMES,
    DEFAULT_DIFFICULTY,
    MAX_DICE_DISPLAY,
)
from commands.error_handlers import handle_discord_error

# Enhanced error handling
from commands.enhanced_error_handlers import (
    handle_validation_error,
    handle_generic_error,
)


def setup(bot: commands.Bot) -> None:
    """
    Register roll command with the bot.

    Registers both slash (/) and prefix (!) versions of the roll command.
    Called automatically from main.py during bot initialization.

    Args:
        bot: The Discord bot instance to register commands with
    """

    # Slash command
    @bot.tree.command(name="roll", description="Roll dice (e.g., 1d100, 3d10, 2d6+5)")
    @app_commands.describe(
        dice="Dice notation (e.g., 1d100, 3d10, 2d6+5, 1d20-3)",
        target="Optional WFRP skill target (1-100) to classify d100 doubles as crit/fumble",
        modifier="WFRP difficulty modifier (default: +20 Average). Use -50 to +60 for task difficulty",
    )
    async def roll_slash(
        interaction: discord.Interaction,
        dice: str,
        target: Optional[int] = None,
        modifier: int = DEFAULT_DIFFICULTY,
    ) -> None:
        """
        Slash command for rolling dice with WFRP mechanics.

        Supports standard dice notation (XdY+Z) and optional WFRP skill tests
        with difficulty modifiers and doubles classification.

        Args:
            interaction: Discord interaction from slash command
            dice: Dice notation string (e.g., "1d100", "2d6+3")
            target: Optional WFRP skill value (1-100) for success/failure checks
            modifier: WFRP difficulty modifier (+20 Average by default)

        Examples:
            /roll 1d100                        # Simple roll
            /roll 1d100 45                     # Skill test vs 45 (Average +20)
            /roll 1d100 45 -20                 # Hard skill test
        """
        await _perform_roll(interaction, dice, target, modifier, is_slash=True)

    # Prefix command
    @bot.command(name="roll")
    async def roll_prefix(
        ctx: commands.Context,
        dice: str,
        target: Optional[int] = None,
        modifier: int = DEFAULT_DIFFICULTY,
    ) -> None:
        """
        Prefix command for rolling dice with WFRP mechanics.

        Usage:
            !roll 1d100
            !roll 2d6+5
            !roll 1d100 45 20    # Skill test with Average difficulty

        Args:
            ctx: Command context
            dice: Dice notation string
            target: Optional WFRP skill value (1-100)
            modifier: WFRP difficulty modifier
        """
        await _perform_roll(ctx, dice, target, modifier, is_slash=False)

    async def _perform_roll(
        context: Union[discord.Interaction, commands.Context],
        dice: str,
        target: Optional[int],
        modifier: int,
        is_slash: bool,
    ) -> None:
        """
        Shared logic for both slash and prefix roll commands.

        Delegates business logic to RollService and handles Discord
        interaction (embed creation and sending).

        Args:
            context: Discord interaction or command context
            dice: Dice notation string to parse and roll
            target: Optional WFRP skill target for success checks
            modifier: WFRP difficulty modifier to apply to target
            is_slash: True for slash commands, False for prefix commands
        """
        try:
            # Delegate to RollService for business logic
            service = RollService()

            if target is not None:
                # WFRP skill test
                result = service.roll_wfrp_test(dice, target, modifier)
            else:
                # Simple dice roll
                result = service.roll_simple_dice(dice)

            # Build Discord embed from result
            embed = _build_roll_embed(result, context, is_slash)

            # Send the embed
            if is_slash:
                await context.response.send_message(embed=embed)
            else:
                await context.send(embed=embed)

            # Send command log using CommandLogger service
            bot = context.client if is_slash else context.bot
            logger = CommandLogger(bot=bot)
            fields = {"Dice": dice}
            if target is not None:
                fields["Target"] = str(target)
                fields["Modifier"] = f"{modifier:+d}"

            # Build command string
            if is_slash:
                command_str = f"/roll dice:{dice}"
                if target is not None:
                    command_str += f" target:{target}"
                if modifier != DEFAULT_DIFFICULTY:
                    command_str += f" modifier:{modifier}"
            else:
                command_str = f"!roll {dice}"
                if target is not None:
                    command_str += f" {target}"
                if modifier != DEFAULT_DIFFICULTY:
                    command_str += f" {modifier}"

            await logger.log_command_from_context(
                context=context,
                command_name="roll",
                command_string=command_str,
                fields=fields,
                is_slash=is_slash,
            )

        except ValueError as e:
            # Handle parsing errors with enhanced validation handler
            await handle_validation_error(
                context,
                e,
                is_slash,
                "roll",
                usage_examples=[
                    "/roll 1d100",
                    "/roll 3d10",
                    "/roll 2d6+5",
                    "/roll 1d100 target:45 modifier:20",
                ],
            )

        except discord.DiscordException as e:
            # Handle Discord API errors
            await handle_discord_error(context, e, is_slash)

        except Exception as e:  # noqa: BLE001
            # Catch-all for unexpected errors with enhanced logging
            await handle_generic_error(context, e, is_slash, "roll")

    def _build_roll_embed(
        result: RollResult,
        context: Union[discord.Interaction, commands.Context],
        is_slash: bool,
    ) -> discord.Embed:
        """
        Build a Discord embed from a RollResult.

        Creates a formatted embed showing dice roll details, WFRP mechanics,
        and outcome information with appropriate colors.

        Args:
            result: The roll result from RollService
            context: Discord interaction or command context (for user info)
            is_slash: True for slash commands, False for prefix commands

        Returns:
            discord.Embed ready to send to Discord
        """
        # Start with blue color (will change based on result)
        embed = discord.Embed(title="🎲 Dice Roll", color=discord.Color.blue())

        # Add the roll details
        notation_display = f"{result.num_dice}d{result.die_size}"
        if result.dice_modifier != 0:
            notation_display += f"{result.dice_modifier:+d}"

        embed.add_field(name="Roll", value=f"`{notation_display}`", inline=False)

        # Show individual results if reasonable
        if result.num_dice <= MAX_DICE_DISPLAY:
            results_str = ", ".join(str(r) for r in result.individual_rolls)
            embed.add_field(name="Results", value=f"[{results_str}]", inline=False)
        else:
            embed.add_field(name="Results", value=f"*{result.num_dice} dice rolled*", inline=False)

        # Show dice modifier if present
        if result.dice_modifier != 0:
            modifier_str = f"{result.dice_modifier:+d}"
            embed.add_field(name="Dice Modifier", value=modifier_str, inline=True)

        # Show total
        embed.add_field(name="**Total**", value=f"**{result.total}**", inline=True)

        # WFRP-specific information
        if result.is_wfrp_test:
            # Show target and difficulty
            difficulty_name = DIFFICULTY_NAMES.get(result.difficulty, f"{result.difficulty:+d}")
            embed.add_field(
                name="WFRP Target",
                value=f"Skill: {result.target} | Difficulty: {difficulty_name} ({result.difficulty:+d})\n**Final Target: {result.final_target}**",
                inline=False,
            )

            # Show result with SL and set color
            if result.success:
                result_text = f"✅ **Success** | SL: **{result.success_level:+d}**"
                embed.color = discord.Color.green()
            else:
                result_text = f"❌ **Failure** | SL: **{result.success_level:+d}**"
                embed.color = discord.Color.red()

            embed.add_field(name="Result", value=result_text, inline=False)

            # Show doubles (criticals/fumbles)
            if result.is_critical:
                roll_val = result.individual_rolls[0]
                desc = f"🎉 **Critical Success!** (Rolled {roll_val:02d} ≤ {result.final_target})"
                embed.add_field(name="⚡ Doubles!", value=desc, inline=False)
                embed.color = discord.Color.green()
            elif result.is_fumble:
                roll_val = result.individual_rolls[0]
                desc = f"💀 **Fumble!** (Rolled {roll_val:02d})"
                embed.add_field(name="⚡ Doubles!", value=desc, inline=False)
                embed.color = discord.Color.dark_red()

        # Add footer with roller info
        if is_slash:
            embed.set_footer(text=f"Rolled by {context.user.display_name}")
        else:
            embed.set_footer(text=f"Rolled by {context.author.display_name}")

        return embed
