"""
A Discord bot for warhammer fantasy rpg river traveling assistance.
Handles dice rolling, boat navigation, trading, and journey management.
"""

import os
import logging
import re
from typing import List, Tuple, Optional
import random
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv


load_dotenv()
token = os.getenv("DISCORD_TOKEN")

handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)

# Tables
characters_data = {
    "anara": {
        "name": "Anara of Sānxiá",
        "species": "High Elf",
        "status": "Silver 1",
        "characteristics": {
            "WS": 55,
            "BS": 33,
            "S": 45,
            "T": 31,
            "I": 61,
            "AG": 47,
            "DEX": 39,
            "INT": 47,
            "WP": 48,
            "FEL": 32,
        },
        "trading_skills": {
            "Haggle": 35,
            "Charm": 33,
            "Gossip": 32,
            "Bribery": 32,
            "Intuition": 61,
        },
        "river_travelling_skills": {
            "Row": 45,
            "Swim": 48,
            "Navigation": 61,
            "Outdoor Survival": 47,
            "Perception": 76,
            "Dodge": 57,
        },
    },
    "emmerich": {
        "name": "Emmerich Falkenrath",
        "species": "Human",
        "status": "Brass 3",
        "characteristics": {
            "WS": 47,
            "BS": 25,
            "S": 37,
            "T": 34,
            "I": 40,
            "AG": 36,
            "DEX": 29,
            "INT": 45,
            "WP": 37,
            "FEL": 34,
        },
        "trading_skills": {
            "Haggle": 37,
            "Charm": 39,
            "Gossip": 42,
            "Bribery": 34,
            "Intuition": 45,
            "Evaluate": 50,
        },
        "river_travelling_skills": {
            "Row": 42,
            "Swim": 47,
            "Navigation": 45,
            "Outdoor Survival": 55,
            "Perception": 50,
            "Dodge": 41,
            "Lore (Geography)": 50,
        },
    },
    "hildric": {
        "name": "Hildric Sokhlundt",
        "species": "Human",
        "status": "Brass 2",
        "characteristics": {
            "WS": 28,
            "BS": 30,
            "S": 32,
            "T": 36,
            "I": 42,
            "AG": 30,
            "DEX": 42,
            "INT": 42,
            "WP": 37,
            "FEL": 40,
        },
        "trading_skills": {
            "Haggle": 40,
            "Charm": 45,
            "Gossip": 45,
            "Bribery": 40,
            "Intuition": 48,
            "Evaluate": 45,
        },
        "river_travelling_skills": {
            "Row": 32,
            "Navigation": 42,
            "Outdoor Survival": 52,
            "Perception": 47,
            "Dodge": 30,
        },
    },
    "oktavian": {
        "name": "Oktavian Babel",
        "species": "Human",
        "status": "Silver 1",
        "characteristics": {
            "WS": 27,
            "BS": 34,
            "S": 30,
            "T": 40,
            "I": 40,
            "AG": 55,
            "DEX": 42,
            "INT": 31,
            "WP": 49,
            "FEL": 33,
        },
        "trading_skills": {
            "Haggle": 33,
            "Charm": 36,
            "Gossip": 38,
            "Bribery": 33,
            "Intuition": 50,
            "Evaluate": 32,
        },
        "river_travelling_skills": {
            "Row": 31,
            "Navigation": 40,
            "Outdoor Survival": 31,
            "Perception": 50,
            "Dodge": 65,
        },
    },
    "lupus": {
        "name": "Lupus Leonard Joachim Rohrig",
        "species": "Human",
        "status": "Gold 3",
        "characteristics": {
            "WS": 40,
            "BS": 34,
            "S": 33,
            "T": 30,
            "I": 40,
            "AG": 25,
            "DEX": 33,
            "INT": 30,
            "WP": 33,
            "FEL": 50,
        },
        "trading_skills": {
            "Haggle": 53,
            "Charm": 55,
            "Gossip": 53,
            "Bribery": 60,
            "Intuition": 40,
        },
        "river_travelling_skills": {
            "Row": 33,
            "Navigation": 40,
            "Outdoor Survival": 30,
            "Perception": 40,
            "Dodge": 25,
        },
    },
}


# ============================================================
# DICE ROLLING UTILITIES
# ============================================================
def parse_dice_notation(notation: str) -> Tuple[int, int, int]:
    """
    Parse dice notation like '3d10' or '1d100+5' or '2d6-3'

    Returns:
        (num_dice, die_size, modifier)

    Raises:
        ValueError: If notation is invalid
    """
    # Remove spaces and convert to lowercase
    notation = notation.strip().lower().replace(" ", "")

    # Pattern: XdY or XdY+Z or XdY-Z
    pattern = r"^(\d+)d(\d+)([\+\-]\d+)?$"
    match = re.match(pattern, notation)

    if not match:
        raise ValueError(f"Invalid dice notation: {notation}")

    num_dice = int(match.group(1))
    die_size = int(match.group(2))
    modifier = int(match.group(3)) if match.group(3) else 0

    # Validation
    if num_dice < 1 or num_dice > 100:
        raise ValueError("Number of dice must be between 1 and 100")
    if die_size < 2 or die_size > 1000:
        raise ValueError("Die size must be between 2 and 1000")

    return num_dice, die_size, modifier


def roll_dice(num_dice: int, die_size: int) -> List[int]:
    """
    Roll dice and return individual results.

    Args:
        num_dice: Number of dice to roll
        die_size: Size of each die (e.g., 10 for d10)

    Returns:
        List of individual roll results
    """
    return [random.randint(1, die_size) for _ in range(num_dice)]


def check_wfrp_doubles(roll_result: int, target: int) -> str:
    """
    Determine whether a d100 roll is a WFRP double and whether it is a
    critical success or a fumble relative to a character's skill target.

    Rules implemented:
      - Doubles are matching digits (11, 22, 33, ... 99). The roll of 1 is
        treated as a special low double (01/1) for the purposes of criticals.
      - 100 is always a fumble.
      - If a double's numeric value is less than or equal to the character's
        target, it counts as a critical success ('crit').
      - If a double's numeric value is greater than the character's target,
        it counts as a fumble ('fumble').
      - Non-doubles return 'none'.

    Args:
        roll_result: The d100 roll result (1-100).
        target: The character's skill target (1-100).

    Returns:
        One of the strings: 'crit', 'fumble', or 'none'.
    """
    # 100 (00) is a fumble
    if roll_result == 100:
        return "fumble"

    # Treat a roll of 1 as the low double (01) for critical checks per user rule
    if roll_result == 1:
        is_double = True
    else:
        tens = roll_result // 10
        ones = roll_result % 10
        is_double = tens == ones

    if not is_double:
        return "none"

    # For doubles: if the roll is <= target -> crit, else -> fumble
    return "crit" if roll_result <= target else "fumble"


@bot.event
async def on_ready():
    """
    Handle the bot's ready event.
    This asynchronous event handler is called when the bot has successfully connected
    to Discord and is fully initialized. It prints a readiness message to standard
    output that includes the bot's username.
    Returns:
        None
    Side effects:
        Prints a formatted message to stdout, e.g. "We are ready to go in <bot.user.name>".
    """
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

    print(f"We are ready to go in {bot.user.name}")


@bot.event
async def on_message(message):
    """
    Handle incoming messages.
    This asynchronous event handler is called whenever a message is sent in a channel
    that the bot has access to. It ignores messages sent by the bot itself to prevent
    infinite loops. For other messages, it prints the content of the message to standard
    output.
    Args:
        message (discord.Message): The message object representing the incoming message.
    Returns:
        None
    Side effects:
        Prints the content of the message to stdout.
    """
    if message.author == bot.user:
        return

    print(f"Message received: {message.content}")

    await bot.process_commands(message)


# ==================== COMMANDS ====================
# Slash command version
@bot.tree.command(name="hello", description="Greet the traveling bot")
async def hello_slash(interaction: discord.Interaction):
    """A simple greeting command."""
    await interaction.response.send_message(
        f"Hello {interaction.user.mention}! 🚢 I am your WFRP traveling companion."
    )


# Prefix command version (fallback for /hello as text)
@bot.command(name="hello")
async def hello_prefix(ctx):
    """A simple greeting command."""
    await ctx.send(
        f"Hello {ctx.author.mention}! 🚢 I am your WFRP traveling companion."
    )


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


# Prefix command version (fallback for /roll as text)
@bot.command(name="roll")
async def roll_prefix(ctx, dice: str, target: Optional[int] = None, modifier: int = 20):
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

    except Exception as e:
        # Handle unexpected errors
        if is_slash:
            await context.response.send_message(
                f"❌ An error occurred: {str(e)}", ephemeral=True
            )
        else:
            await context.send(f"❌ An error occurred: {str(e)}")


if __name__ == "__main__":

    bot.run(token, log_handler=handler, log_level=logging.DEBUG)
