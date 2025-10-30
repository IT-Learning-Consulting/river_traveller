"""
Roll Service - Business logic for dice rolling and WFRP mechanics.

This service separates dice rolling logic from Discord interaction code,
making it testable and reusable. Handles standard dice notation and
WFRP 4th Edition skill test mechanics.

Usage Example:
    >>> service = RollService()
    >>> result = service.roll_simple_dice("2d6+3")
    >>> print(f"Total: {result.total}")
    >>>
    >>> # WFRP skill test
    >>> result = service.roll_wfrp_test("1d100", target=45, difficulty=20)
    >>> print(f"Success: {result.success}, SL: {result.success_level}")
"""

from dataclasses import dataclass
from typing import List, Optional

from utils.wfrp_mechanics import (
    parse_dice_notation,
    roll_dice,
    check_wfrp_doubles,
)
from commands.constants import (
    WFRP_SKILL_MIN,
    WFRP_SKILL_MAX,
    WFRP_ROLL_FUMBLE,
    WFRP_ROLL_MIN_DOUBLE,
)


@dataclass
class RollResult:
    """
    Result of a dice roll with optional WFRP mechanics.

    Attributes:
        dice_notation: Original dice notation string (e.g., "2d6+3")
        num_dice: Number of dice rolled
        die_size: Size of each die (e.g., 6 for d6)
        dice_modifier: Modifier added to roll (e.g., +3)
        individual_rolls: List of individual die results
        total: Sum of all dice plus modifier

        # WFRP-specific fields (only populated for WFRP tests)
        is_wfrp_test: True if this was a WFRP skill test
        target: Original skill target value (before difficulty modifier)
        difficulty: Difficulty modifier applied (-50 to +60)
        final_target: Target after applying difficulty (clamped to 1-100)
        success: True if roll succeeded (roll <= final_target)
        success_level: WFRP Success Level (SL)
        is_double: True if roll has matching digits (e.g., 11, 22, 33)
        is_critical: True if roll is a critical success (doubles ≤ target)
        is_fumble: True if roll is a fumble (100 or doubles > target)
        doubles_classification: "crit", "fumble", or "none"
        outcome_text: Human-readable outcome description

    Example:
        Simple roll:
            RollResult(
                dice_notation="2d6+3",
                num_dice=2,
                die_size=6,
                dice_modifier=3,
                individual_rolls=[4, 5],
                total=12,
                is_wfrp_test=False,
                ...
            )

        WFRP test:
            RollResult(
                dice_notation="1d100",
                num_dice=1,
                die_size=100,
                dice_modifier=0,
                individual_rolls=[33],
                total=33,
                is_wfrp_test=True,
                target=45,
                difficulty=20,
                final_target=65,
                success=True,
                success_level=3,
                is_double=True,
                is_critical=True,
                is_fumble=False,
                doubles_classification="crit",
                outcome_text="✅ Success | SL: +3 | 🎉 Critical Success!",
            )
    """

    # Basic roll information
    dice_notation: str
    num_dice: int
    die_size: int
    dice_modifier: int
    individual_rolls: List[int]
    total: int

    # WFRP-specific fields
    is_wfrp_test: bool = False
    target: Optional[int] = None
    difficulty: Optional[int] = None
    final_target: Optional[int] = None
    success: Optional[bool] = None
    success_level: Optional[int] = None
    is_double: bool = False
    is_critical: bool = False
    is_fumble: bool = False
    doubles_classification: str = "none"
    outcome_text: Optional[str] = None


class RollService:
    """
    Service for dice rolling and WFRP mechanics.

    Provides methods for simple dice rolling and WFRP skill tests with
    success level calculation and doubles classification.
    """

    def roll_simple_dice(self, notation: str) -> RollResult:
        """
        Roll dice using standard notation (XdY+Z).

        Args:
            notation: Dice notation string (e.g., "2d6+3", "1d100", "3d10-2")

        Returns:
            RollResult with basic roll information

        Raises:
            ValueError: If notation is invalid

        Examples:
            >>> service = RollService()
            >>> result = service.roll_simple_dice("2d6+3")
            >>> print(result.total)
            12
        """
        # Parse the dice notation
        num_dice, die_size, dice_modifier = parse_dice_notation(notation)

        # Roll the dice
        results = roll_dice(num_dice, die_size)
        total = sum(results) + dice_modifier

        return RollResult(
            dice_notation=notation,
            num_dice=num_dice,
            die_size=die_size,
            dice_modifier=dice_modifier,
            individual_rolls=results,
            total=total,
            is_wfrp_test=False,
        )

    def roll_wfrp_test(
        self, notation: str, target: int, difficulty: int = 20
    ) -> RollResult:
        """
        Roll a WFRP 4th Edition skill test with success level calculation.

        Applies WFRP mechanics:
        - Success Level (SL) = (Final Target ÷ 10) - (Roll ÷ 10)
        - Doubles can be criticals (≤ target) or fumbles (> target)
        - Roll of 100 is always a fumble
        - Roll of 01 counts as doubles

        Args:
            notation: Dice notation (should be "1d100" for WFRP tests)
            target: Base skill value (1-100)
            difficulty: Difficulty modifier (-50 to +60, default +20 Average)

        Returns:
            RollResult with WFRP mechanics calculated

        Raises:
            ValueError: If target is not between 1 and 100
            ValueError: If notation is not valid d100 roll

        Examples:
            >>> service = RollService()
            >>> result = service.roll_wfrp_test("1d100", target=45, difficulty=20)
            >>> print(f"Success: {result.success}, SL: {result.success_level}")
            Success: True, SL: +2
            >>>
            >>> # Critical success (doubles ≤ target)
            >>> # If you rolled 33 with final target 65
            >>> print(result.is_critical)
            True
        """
        # Validate target range
        if target < WFRP_SKILL_MIN or target > WFRP_SKILL_MAX:
            raise ValueError(
                f"Target must be between {WFRP_SKILL_MIN} and {WFRP_SKILL_MAX}"
            )

        # Roll the dice (should be 1d100 for WFRP)
        num_dice, die_size, dice_modifier = parse_dice_notation(notation)

        # Validate this is a d100 roll
        if num_dice != 1 or die_size != 100:
            raise ValueError("WFRP tests must use 1d100 notation")

        results = roll_dice(num_dice, die_size)
        roll_value = results[0]
        total = roll_value + dice_modifier

        # Apply difficulty modifier to target and clamp
        final_target = target + difficulty
        final_target = max(WFRP_SKILL_MIN, min(WFRP_SKILL_MAX, final_target))

        # Calculate success and success level
        success = roll_value <= final_target
        success_level = (final_target // 10) - (roll_value // 10)

        # Check for doubles (criticals/fumbles)
        is_double = False
        doubles_classification = "none"
        is_critical = False
        is_fumble = False

        # 100 is always a fumble
        if roll_value == WFRP_ROLL_FUMBLE:
            is_double = True
            is_fumble = True
            doubles_classification = "fumble"
        else:
            # Treat 01 as low double, detect matching-digit doubles
            is_double = roll_value == WFRP_ROLL_MIN_DOUBLE or (roll_value // 10) == (
                roll_value % 10
            )

            if is_double:
                # Use final target for classification
                doubles_classification = check_wfrp_doubles(roll_value, final_target)
                is_critical = doubles_classification == "crit"
                is_fumble = doubles_classification == "fumble"

        # Build outcome text
        outcome_parts = []

        if success:
            outcome_parts.append(f"✅ Success | SL: {success_level:+d}")
        else:
            outcome_parts.append(f"❌ Failure | SL: {success_level:+d}")

        if is_critical:
            outcome_parts.append(
                f"🎉 Critical Success! (Rolled {roll_value:02d} ≤ {final_target})"
            )
        elif is_fumble:
            outcome_parts.append(f"💀 Fumble! (Rolled {roll_value:02d})")

        outcome_text = " | ".join(outcome_parts)

        return RollResult(
            dice_notation=notation,
            num_dice=num_dice,
            die_size=die_size,
            dice_modifier=dice_modifier,
            individual_rolls=results,
            total=total,
            is_wfrp_test=True,
            target=target,
            difficulty=difficulty,
            final_target=final_target,
            success=success,
            success_level=success_level,
            is_double=is_double,
            is_critical=is_critical,
            is_fumble=is_fumble,
            doubles_classification=doubles_classification,
            outcome_text=outcome_text,
        )
