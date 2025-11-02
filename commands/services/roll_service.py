"""
Roll Service - Business logic for dice rolling and WFRP skill tests.

This service contains all dice rolling logic extracted from the roll command.
It has no Discord dependencies and returns structured data that commands
can format for display.

Design Principles:
    - No Discord dependencies (pure business logic)
    - Returns structured RollResult objects
    - Delegates to utils.wfrp_mechanics for core logic
    - Fully testable without mocking Discord objects

Usage:
    >>> service = RollService()
    >>> result = service.roll_simple_dice("3d6+2")
    >>> print(f"Rolled {result.total}")

    >>> result = service.roll_wfrp_test(target=50, difficulty=20)
    >>> print(f"Roll: {result.roll_value}, SL: {result.success_level}")
"""

from dataclasses import dataclass
from typing import Optional, List
from utils.wfrp_mechanics import (
    parse_dice_notation,
    roll_dice,
    calculate_success_level,
    check_wfrp_doubles,
    get_success_level_name,
    RESULT_CRIT,
    RESULT_FUMBLE,
)


@dataclass
class RollResult:
    """
    Result of a dice roll operation.

    Attributes:
        roll_value: Primary result value
        dice_notation: Original dice notation string
        individual_rolls: List of individual die results
        total: Total of all rolls plus modifiers
        num_dice: Number of dice rolled
        die_size: Size of each die
        dice_modifier: Modifier applied to dice total
        is_wfrp_test: Whether this was a WFRP skill test
        target: Target number for skill test (None for simple rolls)
        difficulty: Difficulty modifier for skill test (None for simple rolls)
        final_target: Final target after difficulty modifier (None for simple rolls)
        success: Whether the test succeeded (None for simple rolls)
        success_level: WFRP Success Level (None for simple rolls)
        is_double: Whether the roll was a double (None for simple rolls)
        is_critical: Whether it was a critical success (None for simple rolls)
        is_fumble: Whether it was a fumble (None for simple rolls)
        outcome_text: Human-readable outcome description
    """
    roll_value: int
    dice_notation: str
    individual_rolls: List[int]
    total: int
    num_dice: int
    die_size: int
    dice_modifier: int = 0
    is_wfrp_test: bool = False
    target: Optional[int] = None
    difficulty: Optional[int] = None
    final_target: Optional[int] = None
    success: Optional[bool] = None
    success_level: Optional[int] = None
    is_double: Optional[bool] = None
    is_critical: Optional[bool] = None
    is_fumble: Optional[bool] = None
    outcome_text: Optional[str] = None


class RollService:
    """
    Service for handling dice rolling and WFRP skill tests.

    This service is pure business logic with no Discord dependencies.
    All methods return structured RollResult objects that can be
    formatted by the command layer.

    Methods:
        roll_simple_dice: Roll standard dice notation (XdY�Z)
        roll_wfrp_test: Perform WFRP 4e skill test (d100 vs target)
    """

    def roll_simple_dice(self, notation: str) -> RollResult:
        """
        Roll dice using standard notation (e.g., "3d6+2").

        Parses notation, rolls dice, and returns structured result.

        Args:
            notation: Dice notation string (XdY�Z format)
                - X = number of dice (1-100)
                - Y = die size (2-1000)
                - Z = optional modifier (-999 to +999)

        Returns:
            RollResult: Roll details with individual rolls and total

        Raises:
            ValueError: If notation is invalid or out of valid ranges

        Examples:
            >>> service = RollService()
            >>> result = service.roll_simple_dice("3d6")
            >>> print(result.total)  # Sum of 3d6

            >>> result = service.roll_simple_dice("1d100+5")
            >>> print(result.total)  # 1d100 + 5
        """
        # Parse dice notation (may raise ValueError)
        num_dice, die_size, modifier = parse_dice_notation(notation)

        # Roll the dice
        rolls = roll_dice(num_dice, die_size)

        # Calculate total
        total = sum(rolls) + modifier

        return RollResult(
            roll_value=total,
            dice_notation=notation,
            individual_rolls=rolls,
            total=total,
            num_dice=num_dice,
            die_size=die_size,
            dice_modifier=modifier,
            is_wfrp_test=False
        )

    def roll_wfrp_test(
        self,
        dice: str,
        target: int,
        difficulty: int = 0
    ) -> RollResult:
        """
        Perform a WFRP 4e skill test (d100 vs modified target).

        Rolls d100, applies difficulty modifier, calculates Success Level (SL),
        and checks for criticals/fumbles (doubles system).

        WFRP 4e Rules:
            - Roll d100 (1-100)
            - Modified target = base target + difficulty modifier
            - Success if roll <= modified target
            - SL = (target tens) - (roll tens)
            - Doubles (11, 22, etc.):
                - If <= target: Critical Success
                - If > target: Fumble
            - Roll of 100 is always fumble

        Args:
            dice: Dice notation (should be "1d100" for WFRP tests)
            target: Base skill value (1-100)
            difficulty: Difficulty modifier (-50 to +60)
                - Positive makes test easier (Easy +40, Average +20)
                - Negative makes test harder (Hard -20, Difficult -10)

        Returns:
            RollResult: Complete test results including SL, doubles, outcome

        Examples:
            >>> service = RollService()
            >>> result = service.roll_wfrp_test("1d100", target=50, difficulty=0)
            >>> print(f"Success: {result.success}, SL: {result.success_level}")

            >>> result = service.roll_wfrp_test("1d100", target=50, difficulty=-20)  # Hard test
            >>> print(result.outcome_text)  # "Success (+2 SL)" or similar
        """
        # Parse dice notation to validate it's 1d100 (or use it if different)
        num_dice, die_size, dice_mod = parse_dice_notation(dice)

        # Roll the dice
        rolls = roll_dice(num_dice, die_size)
        roll_value = rolls[0] if num_dice == 1 else sum(rolls)

        # Calculate modified target
        modified_target = target + difficulty

        # Check for doubles (crits/fumbles)
        doubles_result = check_wfrp_doubles(roll_value, modified_target)
        is_double = doubles_result in (RESULT_CRIT, RESULT_FUMBLE)
        is_critical = doubles_result == RESULT_CRIT
        is_fumble = doubles_result == RESULT_FUMBLE

        # Calculate success
        success = roll_value <= modified_target

        # Calculate success level
        success_level = calculate_success_level(roll_value, modified_target)

        # Get descriptive outcome
        outcome_text = get_success_level_name(success_level, success)

        return RollResult(
            roll_value=roll_value,
            dice_notation=dice,
            individual_rolls=rolls,
            total=roll_value,
            num_dice=num_dice,
            die_size=die_size,
            dice_modifier=dice_mod,
            is_wfrp_test=True,
            target=target,
            difficulty=difficulty,
            final_target=modified_target,
            success=success,
            success_level=success_level,
            is_double=is_double,
            is_critical=is_critical,
            is_fumble=is_fumble,
            outcome_text=outcome_text
        )
