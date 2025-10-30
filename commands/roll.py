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

from typing import Literal, Optional, Union
import discord
from discord import app_commands
from discord.ext import commands

# Import from our modules
from utils.wfrp_mechanics import (
    parse_dice_notation,
    roll_dice,
    check_wfrp_doubles,
)


# WFRP difficulty modifiers and names
DIFFICULTY_VERY_EASY = 60
DIFFICULTY_EASY = 40
DIFFICULTY_AVERAGE = 20
DIFFICULTY_CHALLENGING = 0
DIFFICULTY_DIFFICULT = -10
DIFFICULTY_HARD = -20
DIFFICULTY_VERY_DIFFICULT = -30
DIFFICULTY_FUTILE = -40
DIFFICULTY_IMPOSSIBLE = -50

DEFAULT_DIFFICULTY = DIFFICULTY_AVERAGE

DIFFICULTY_NAMES = {
    DIFFICULTY_IMPOSSIBLE: "Impossible",
    DIFFICULTY_FUTILE: "Futile",
    DIFFICULTY_VERY_DIFFICULT: "Very Difficult",
    DIFFICULTY_HARD: "Hard",
    DIFFICULTY_DIFFICULT: "Difficult",
    DIFFICULTY_CHALLENGING: "Challenging",
    DIFFICULTY_AVERAGE: "Average",
    DIFFICULTY_EASY: "Easy",
    DIFFICULTY_VERY_EASY: "Very Easy",
}

# WFRP constants
WFRP_SKILL_MIN = 1
WFRP_SKILL_MAX = 100
WFRP_ROLL_FUMBLE = 100
WFRP_ROLL_MIN_DOUBLE = 1  # 01 counts as doubles

# Display thresholds
MAX_DICE_DISPLAY = 20  # Show individual results only if ≤20 dice

# Channel names
CHANNEL_COMMAND_LOG = "boat-travelling-log"


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

        Handles dice parsing, rolling, WFRP mechanics, embed generation,
        and command logging. Implements defensive error handling for Discord
        API failures.

        Args:
            context: Discord interaction or command context
            dice: Dice notation string to parse and roll
            target: Optional WFRP skill target for success checks
            modifier: WFRP difficulty modifier to apply to target
            is_slash: True for slash commands, False for prefix commands
        """
        try:
            # Parse the dice notation
            num_dice, die_size, dice_modifier = parse_dice_notation(dice)

            # Roll the dice
            results = roll_dice(num_dice, die_size)
            total = sum(results) + dice_modifier

            # Build the response embed
            embed = discord.Embed(title="🎲 Dice Roll", color=discord.Color.blue())

            # Add the roll details
            notation_display = f"{num_dice}d{die_size}"
            if dice_modifier != 0:
                notation_display += f"{dice_modifier:+d}"

            embed.add_field(name="Roll", value=f"`{notation_display}`", inline=False)

            # Show individual results if reasonable
            if num_dice <= MAX_DICE_DISPLAY:
                results_str = ", ".join(str(r) for r in results)
                embed.add_field(name="Results", value=f"[{results_str}]", inline=False)
            else:
                embed.add_field(
                    name="Results", value=f"*{num_dice} dice rolled*", inline=False
                )

            # Show dice modifier if present
            if dice_modifier != 0:
                modifier_str = f"{dice_modifier:+d}"
                embed.add_field(name="Dice Modifier", value=modifier_str, inline=True)

            # Show total
            embed.add_field(name="**Total**", value=f"**{total}**", inline=True)

            # WFRP Special: Check for doubles on d100
            if num_dice == 1 and die_size == 100 and target is not None:
                # Apply WFRP difficulty modifier to target
                final_target = target + modifier

                # Clamp to valid range
                final_target = max(WFRP_SKILL_MIN, min(WFRP_SKILL_MAX, final_target))

                # Show WFRP info
                difficulty_name = DIFFICULTY_NAMES.get(modifier, f"{modifier:+d}")

                embed.add_field(
                    name="WFRP Target",
                    value=f"Skill: {target} | Difficulty: {difficulty_name} ({modifier:+d})\n**Final Target: {final_target}**",
                    inline=False,
                )

                roll_val = results[0]

                # Validate target range
                if target < WFRP_SKILL_MIN or target > WFRP_SKILL_MAX:
                    raise ValueError(
                        f"Target must be between {WFRP_SKILL_MIN} and {WFRP_SKILL_MAX}"
                    )

                # Calculate Success Level (SL) - WFRP 4e formula
                sl = (final_target // 10) - (roll_val // 10)
                success = roll_val <= final_target

                # Show result with SL
                if success:
                    result_text = f"✅ **Success** | SL: **{sl:+d}**"
                    if (
                        embed.color == discord.Color.blue()
                    ):  # Only change if not already changed by doubles
                        embed.color = discord.Color.green()
                else:
                    result_text = f"❌ **Failure** | SL: **{sl:+d}**"
                    if (
                        embed.color == discord.Color.blue()
                    ):  # Only change if not already changed by doubles
                        embed.color = discord.Color.red()

                embed.add_field(name="Result", value=result_text, inline=False)

                # 100 is always a fumble
                if roll_val == WFRP_ROLL_FUMBLE:
                    classification = "fumble"
                else:
                    # treat 1 as the low double (01) and detect matching-digit doubles
                    is_double = roll_val == WFRP_ROLL_MIN_DOUBLE or (
                        roll_val // 10
                    ) == (roll_val % 10)
                    if not is_double:
                        classification = "none"
                    else:
                        # Use the final modified target for crit/fumble classification
                        classification = check_wfrp_doubles(roll_val, final_target)

                if classification != "none":
                    if classification == "crit":
                        desc = f"🎉 **Critical Success!** (Rolled {roll_val:02d} ≤ {final_target})"
                        embed.color = discord.Color.green()
                    else:
                        desc = f"💀 **Fumble!** (Rolled {roll_val:02d})"
                        embed.color = discord.Color.dark_red()

                    embed.add_field(name="⚡ Doubles!", value=desc, inline=False)

            # Add footer with roller info
            if is_slash:
                embed.set_footer(text=f"Rolled by {context.user.display_name}")
                await context.response.send_message(embed=embed)
            else:
                embed.set_footer(text=f"Rolled by {context.author.display_name}")
                await context.send(embed=embed)

            # Send command log
            await _send_command_log(context, dice, target, modifier, is_slash)

        except ValueError as e:
            # Handle parsing errors
            error_embed = discord.Embed(
                title="❌ Invalid Dice Notation",
                description=str(e),
                color=discord.Color.red(),
            )
            error_embed.add_field(
                name="Examples",
                value="• `/roll 1d100`\n• `/roll 3d10`\n• `/roll 2d6+5`\n• `/roll 1d20-3`",
                inline=False,
            )
            if is_slash:
                await context.response.send_message(embed=error_embed, ephemeral=True)
            else:
                await context.send(embed=error_embed)

        except (discord.DiscordException, AttributeError) as e:  # noqa: BLE001
            # Handle unexpected errors (broad exception intentional for user safety)
            if is_slash:
                # Use followup if response was already used/failed
                try:
                    if context.response.is_done():
                        await context.followup.send(
                            f"❌ An error occurred: {str(e)}", ephemeral=True
                        )
                    else:
                        await context.response.send_message(
                            f"❌ An error occurred: {str(e)}", ephemeral=True
                        )
                except Exception:  # noqa: BLE001, S110
                    # Even followup failed, last resort attempt (broad exception intentional)
                    await context.followup.send(
                        f"❌ An error occurred: {str(e)}", ephemeral=True
                    )
            else:
                await context.send(f"❌ An error occurred: {str(e)}")

    async def _send_command_log(
        context: Union[discord.Interaction, commands.Context],
        dice: str,
        target: Optional[int],
        modifier: int,
        is_slash: bool,
    ) -> None:
        """
        Send command details to boat-travelling-log channel.

        Logs all roll commands with user info, dice notation, and WFRP
        parameters. Helps track command usage and debug issues.

        Args:
            context: Discord interaction or command context
            dice: Dice notation that was rolled
            target: Optional WFRP target value
            modifier: WFRP difficulty modifier
            is_slash: True for slash commands, False for prefix commands

        Note:
            Fails silently if log channel doesn't exist or bot lacks permissions.
            Logging is optional and should not break the main command flow.
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

            # Create log embed
            log_embed = discord.Embed(
                title="🎲 Command Log: Roll",
                description=f"**User:** {username} (`{user_id}`)\n**Command:** `{command_str}`",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow(),
            )

            log_embed.add_field(name="Dice", value=dice, inline=True)
            if target is not None:
                log_embed.add_field(name="Target", value=str(target), inline=True)
                log_embed.add_field(
                    name="Modifier", value=f"{modifier:+d}", inline=True
                )

            await log_channel.send(embed=log_embed)

        except (discord.Forbidden, discord.HTTPException, AttributeError):
            # Silently fail - logging is not critical
            pass
