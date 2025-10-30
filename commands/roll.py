"""
Command: roll
Description: Roll dice with WFRP mechanics support
"""

from typing import Optional
import discord
from discord import app_commands
from discord.ext import commands

# Import from our modules
from utils.wfrp_mechanics import (
    parse_dice_notation,
    roll_dice,
    check_wfrp_doubles,
)


def setup(bot: commands.Bot):
    """
    Register roll command with the bot.
    Called from main.py during bot initialization.
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
        modifier: int = 20,
    ):
        """
        Roll dice with flexible notation support.

        Examples:
            /roll 1d100
            /roll 3d10
            /roll 2d6+5
            /roll 1d20-3
            /roll 1d100 45        (Average: +20, final target = 65)
            /roll 1d100 45 -20    (Hard: final target = 25)
        """
        await _perform_roll(interaction, dice, target, modifier, is_slash=True)

    # Prefix command
    @bot.command(name="roll")
    async def roll_prefix(
        ctx, dice: str, target: Optional[int] = None, modifier: int = 20
    ):
        """Roll dice with flexible notation support."""
        await _perform_roll(ctx, dice, target, modifier, is_slash=False)

    async def _perform_roll(
        context, dice: str, target: Optional[int], modifier: int, is_slash: bool
    ):
        """Shared logic for both slash and prefix roll commands."""
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
            if num_dice <= 20:
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
                final_target = max(1, min(100, final_target))

                # Show WFRP info
                difficulty_map = {
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
                difficulty_name = difficulty_map.get(modifier, f"{modifier:+d}")

                embed.add_field(
                    name="WFRP Target",
                    value=f"Skill: {target} | Difficulty: {difficulty_name} ({modifier:+d})\n**Final Target: {final_target}**",
                    inline=False,
                )

                roll_val = results[0]

                # Validate target range
                if target < 1 or target > 100:
                    raise ValueError("Target must be between 1 and 100")

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
                if roll_val == 100:
                    classification = "fumble"
                else:
                    # treat 1 as the low double (01) and detect matching-digit doubles
                    is_double = roll_val == 1 or (roll_val // 10) == (roll_val % 10)
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

        except (discord.DiscordException, AttributeError) as e:
            # Handle unexpected errors
            if is_slash:
                await context.response.send_message(
                    f"❌ An error occurred: {str(e)}", ephemeral=True
                )
            else:
                await context.send(f"❌ An error occurred: {str(e)}")

    async def _send_command_log(
        context, dice: str, target: Optional[int], modifier: int, is_slash: bool
    ):
        """Send command details to boat-travelling-log channel."""
        try:
            # Find the log channel
            log_channel = discord.utils.get(
                context.guild.text_channels, name="boat-travelling-log"
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
                if modifier != 20:
                    command_str += f" modifier:{modifier}"
            else:
                command_str = f"!roll {dice}"
                if target is not None:
                    command_str += f" {target}"
                if modifier != 20:
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
