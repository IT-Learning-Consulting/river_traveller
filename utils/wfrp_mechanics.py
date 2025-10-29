"""
WFRP (Warhammer Fantasy Roleplay) game mechanics and utilities.
Contains dice rolling, success level calculation, and game rule implementations.
"""

import re
from typing import List, Tuple
import random


def parse_dice_notation(notation: str) -> Tuple[int, int, int]:
    """
    Parse dice notation like '3d10' or '1d100+5' or '2d6-3'

    Args:
        notation: Dice notation string (e.g., '3d10', '1d100+5', '2d6-3')

    Returns:
        Tuple of (num_dice, die_size, modifier)

    Raises:
        ValueError: If notation is invalid or out of valid ranges
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


def calculate_success_level(roll: int, target: int) -> int:
    """
    Calculate WFRP Success Level (SL).

    SL is calculated by subtracting the 10s digit of the roll from
    the 10s digit of the target.

    Args:
        roll: The d100 roll result (1-100)
        target: The target number (1-100)

    Returns:
        Success Level as an integer (positive = success, negative = failure)

    Example:
        roll=29, target=41 -> SL = 4 - 2 = +2
        roll=82, target=39 -> SL = 3 - 8 = -5
    """
    target_tens = target // 10
    roll_tens = roll // 10
    return target_tens - roll_tens


def get_success_level_name(sl: int, success: bool) -> str:
    """
    Get the descriptive name for a Success Level.

    Args:
        sl: The success level value
        success: Whether the test succeeded

    Returns:
        Name of the outcome (e.g., "Astounding Success", "Failure")
    """
    if success:
        if sl >= 6:
            return "Astounding Success"
        elif sl >= 4:
            return "Impressive Success"
        elif sl >= 2:
            return "Success"
        else:
            return "Marginal Success"
    else:
        if sl <= -6:
            return "Astounding Failure"
        elif sl <= -4:
            return "Impressive Failure"
        elif sl <= -2:
            return "Failure"
        else:
            return "Marginal Failure"


def get_difficulty_name(modifier: int) -> str:
    """
    Get the descriptive name for a difficulty modifier.

    Args:
        modifier: The difficulty modifier value

    Returns:
        Name of the difficulty (e.g., "Average", "Hard")
    """
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
    return difficulty_map.get(modifier, f"{modifier:+d}")
