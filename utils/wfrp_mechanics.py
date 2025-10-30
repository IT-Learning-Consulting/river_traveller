"""
WFRP (Warhammer Fantasy Roleplay) 4th Edition game mechanics and utilities.

Implements core WFRP mechanics for dice rolling, skill tests, and success calculation.

Key Responsibilities:
    - Parse and validate dice notation (XdY+Z format)
    - Roll dice with configurable number and size
    - Calculate Success Levels (SL) from d100 tests
    - Identify criticals and fumbles (doubles system)
    - Format difficulty and success names

Design Principles:
    - Pure functions: No side effects or state
    - Type safety: Full type hints
    - Validation: Comprehensive input checking
    - WFRP 4e rules compliance

WFRP Success System:
    1. Roll d100 (1-100)
    2. Compare to target (character skill + modifiers)
    3. Success Level (SL) = (target tens digit) - (roll tens digit)
       - Example: Roll 29 vs Target 41 → SL = 4 - 2 = +2
    4. Doubles (11, 22, 33...99):
       - If double ≤ target: Critical Success
       - If double > target: Fumble
    5. Special cases:
       - Roll of 1: Treated as critical low double (01)
       - Roll of 100: Always a fumble

Difficulty Modifiers (WFRP Standard):
    - Very Easy: +60
    - Easy: +40
    - Average: +20
    - Challenging: +0
    - Difficult: -10
    - Hard: -20
    - Very Difficult: -30
    - Futile: -40
    - Impossible: -50

Usage Example:
    >>> # Parse dice
    >>> num, size, mod = parse_dice_notation("2d10+5")
    >>> print(num, size, mod)
    2 10 5

    >>> # Roll dice
    >>> results = roll_dice(2, 10)
    >>> total = sum(results) + 5

    >>> # Skill test
    >>> roll = 29
    >>> target = 45
    >>> sl = calculate_success_level(roll, target)
    >>> print(f"SL: {sl}")
    SL: 2

    >>> # Check for critical/fumble
    >>> outcome = check_wfrp_doubles(roll, target)
    >>> print(outcome)
    none
"""

import re
from typing import List, Tuple
import random

# Dice notation validation ranges
MIN_DICE: int = 1
MAX_DICE: int = 100
MIN_DIE_SIZE: int = 2
MAX_DIE_SIZE: int = 1000

# D100 special rolls
D100_FUMBLE_ROLL: int = 100
D100_LOW_DOUBLE: int = 1  # Treated as 01 for critical purposes

# Dice roll ranges
D100_MIN: int = 1
D100_MAX: int = 100

# Success level thresholds
SL_ASTOUNDING: int = 6
SL_IMPRESSIVE: int = 4
SL_SUCCESS: int = 2

# Difficulty modifiers (WFRP standard)
DIFF_IMPOSSIBLE: int = -50
DIFF_FUTILE: int = -40
DIFF_VERY_DIFFICULT: int = -30
DIFF_HARD: int = -20
DIFF_DIFFICULT: int = -10
DIFF_CHALLENGING: int = 0
DIFF_AVERAGE: int = 20
DIFF_EASY: int = 40
DIFF_VERY_EASY: int = 60

# Difficulty names mapping
DIFFICULTY_NAMES: dict = {
    DIFF_IMPOSSIBLE: "Impossible",
    DIFF_FUTILE: "Futile",
    DIFF_VERY_DIFFICULT: "Very Difficult",
    DIFF_HARD: "Hard",
    DIFF_DIFFICULT: "Difficult",
    DIFF_CHALLENGING: "Challenging",
    DIFF_AVERAGE: "Average",
    DIFF_EASY: "Easy",
    DIFF_VERY_EASY: "Very Easy",
}

# Result types
RESULT_CRIT: str = "crit"
RESULT_FUMBLE: str = "fumble"
RESULT_NONE: str = "none"

# Tens digit divisor
TENS_DIVISOR: int = 10


def parse_dice_notation(notation: str) -> Tuple[int, int, int]:
    """
    Parse dice notation like '3d10' or '1d100+5' or '2d6-3'.

    Validates format and ensures values are within reasonable ranges.

    Args:
        notation: Dice notation string. Format: XdY or XdY+Z or XdY-Z where:
            - X = number of dice (1-100)
            - Y = die size (2-1000)
            - Z = optional modifier (-999 to +999)

    Returns:
        Tuple[int, int, int]: (num_dice, die_size, modifier)

    Raises:
        ValueError: If notation is invalid or out of valid ranges

    Example:
        >>> parse_dice_notation("3d10")
        (3, 10, 0)
        >>> parse_dice_notation("1d100+5")
        (1, 100, 5)
        >>> parse_dice_notation("2d6-3")
        (2, 6, -3)
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
    if num_dice < MIN_DICE or num_dice > MAX_DICE:
        raise ValueError(f"Number of dice must be between {MIN_DICE} and {MAX_DICE}")
    if die_size < MIN_DIE_SIZE or die_size > MAX_DIE_SIZE:
        raise ValueError(f"Die size must be between {MIN_DIE_SIZE} and {MAX_DIE_SIZE}")

    return num_dice, die_size, modifier


def roll_dice(num_dice: int, die_size: int) -> List[int]:
    """
    Roll dice and return individual results.

    Each die rolls independently with values from 1 to die_size (inclusive).

    Args:
        num_dice: Number of dice to roll (typically 1-10)
        die_size: Size of each die (e.g., 10 for d10, 100 for d100)

    Returns:
        List[int]: Individual roll results. Length equals num_dice.

    Example:
        >>> results = roll_dice(3, 10)
        >>> print(results)
        [7, 3, 10]  # Three d10 rolls

        >>> print(sum(results))
        20  # Total of all rolls
    """
    return [random.randint(D100_MIN, die_size) for _ in range(num_dice)]


def check_wfrp_doubles(roll_result: int, target: int) -> str:
    """
    Determine whether a d100 roll is a WFRP double (critical/fumble).

    WFRP 4e Rules:
    - Doubles are matching digits: 11, 22, 33, ... 99
    - Roll of 1 is treated as low double (01) for critical purposes
    - Roll of 100 is always a fumble
    - Doubles ≤ target = Critical Success
    - Doubles > target = Fumble
    - Non-doubles = Normal roll

    Args:
        roll_result: The d100 roll result (1-100)
        target: The character's skill target (1-100)

    Returns:
        str: One of:
            - "crit": Critical success (double ≤ target)
            - "fumble": Fumble (double > target or roll = 100)
            - "none": Normal roll (not a double)

    Example:
        >>> check_wfrp_doubles(11, 45)
        'crit'  # 11 is double, 11 ≤ 45

        >>> check_wfrp_doubles(88, 45)
        'fumble'  # 88 is double, 88 > 45

        >>> check_wfrp_doubles(35, 45)
        'none'  # Not a double

        >>> check_wfrp_doubles(100, 95)
        'fumble'  # 100 is always fumble
    """
    # 100 (00) is always a fumble
    if roll_result == D100_FUMBLE_ROLL:
        return RESULT_FUMBLE

    # Treat roll of 1 as the low double (01) for critical checks
    if roll_result == D100_LOW_DOUBLE:
        is_double = True
    else:
        tens = roll_result // TENS_DIVISOR
        ones = roll_result % TENS_DIVISOR
        is_double = tens == ones

    if not is_double:
        return RESULT_NONE

    # For doubles: if the roll is <= target -> crit, else -> fumble
    return RESULT_CRIT if roll_result <= target else RESULT_FUMBLE


def calculate_success_level(roll: int, target: int) -> int:
    """
    Calculate WFRP 4e Success Level (SL) from d100 test.

    Success Level measures the margin of success/failure by comparing
    the tens digits of the roll and target.

    Formula: SL = (target tens) - (roll tens)
    - Positive SL = Success
    - Negative SL = Failure
    - Magnitude = Degree of success/failure

    Args:
        roll: The d100 roll result (1-100)
        target: The target number (skill + modifiers, 1-100)

    Returns:
        int: Success Level (positive = success, negative = failure)

    Example:
        >>> calculate_success_level(29, 45)
        2  # Target 4X, Roll 2X → 4-2 = +2 SL

        >>> calculate_success_level(82, 39)
        -5  # Target 3X, Roll 8X → 3-8 = -5 SL

        >>> calculate_success_level(05, 47)
        4  # Target 4X, Roll 0X → 4-0 = +4 SL
    """
    target_tens = target // TENS_DIVISOR
    roll_tens = roll // TENS_DIVISOR
    return target_tens - roll_tens


def get_success_level_name(sl: int, success: bool) -> str:
    """
    Get the descriptive name for a Success Level (WFRP 4e).

    Success/failure is categorized by SL magnitude:
    - ±6+ : Astounding
    - ±4-5: Impressive
    - ±2-3: Normal
    - ±0-1: Marginal

    Args:
        sl: The success level value (can be positive or negative)
        success: Whether the test succeeded (roll ≤ target)

    Returns:
        str: Descriptive outcome name. Examples:
            - "Astounding Success", "Success", "Marginal Failure"

    Example:
        >>> get_success_level_name(7, True)
        'Astounding Success'

        >>> get_success_level_name(2, True)
        'Success'

        >>> get_success_level_name(-5, False)
        'Impressive Failure'
    """
    if success:
        if sl >= SL_ASTOUNDING:
            return "Astounding Success"
        elif sl >= SL_IMPRESSIVE:
            return "Impressive Success"
        elif sl >= SL_SUCCESS:
            return "Success"
        else:
            return "Marginal Success"
    else:
        if sl <= -SL_ASTOUNDING:
            return "Astounding Failure"
        elif sl <= -SL_IMPRESSIVE:
            return "Impressive Failure"
        elif sl <= -SL_SUCCESS:
            return "Failure"
        else:
            return "Marginal Failure"


def get_difficulty_name(modifier: int) -> str:
    """
    Get the descriptive name for a difficulty modifier (WFRP 4e standard).

    WFRP uses standardized difficulty modifiers applied to skill tests.

    Args:
        modifier: The difficulty modifier value. Standard values:
            - +60: Very Easy
            - +40: Easy
            - +20: Average
            - +0: Challenging (default)
            - -10: Difficult
            - -20: Hard
            - -30: Very Difficult
            - -40: Futile
            - -50: Impossible

    Returns:
        str: Difficulty name or formatted modifier if non-standard

    Example:
        >>> get_difficulty_name(0)
        'Challenging'

        >>> get_difficulty_name(-20)
        'Hard'

        >>> get_difficulty_name(-15)
        '-15'  # Non-standard modifier
    """
    return DIFFICULTY_NAMES.get(modifier, f"{modifier:+d}")
