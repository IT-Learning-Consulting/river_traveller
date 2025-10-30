"""
Boat Handling Service - Business logic for WFRP boat handling tests.

This service separates boat handling business logic from Discord interaction code,
making it testable and reusable. Handles character skill selection, Lore bonuses,
WFRP test mechanics, and narrative outcome generation.

Usage Example:
    >>> service = BoatHandlingService()
    >>> result = service.perform_boat_test(
    ...     character_data=char,
    ...     difficulty=0,
    ...     lore_riverways=25,
    ...     weather_penalty=-10
    ... )
    >>> print(f"Outcome: {result.outcome}, SL: {result.success_level}")
"""

import random
from dataclasses import dataclass
from typing import Dict, Any, Optional

from utils.wfrp_mechanics import check_wfrp_doubles


@dataclass
class BoatHandlingResult:
    """
    Result of a boat handling test with WFRP mechanics and narrative outcome.

    Attributes:
        character_name: Full character name
        character_species: Character's species
        character_status: Character's social status
        skill_name: Which skill was used ("Sail" or "Row")
        skill_value: Base skill value before modifiers
        lore_bonus: Bonus from Lore (Riverways) skill
        base_difficulty: Original difficulty modifier
        weather_penalty: Penalty from weather conditions
        final_difficulty: Total difficulty after weather
        final_target: Target number after all modifiers
        roll_value: The d100 roll result
        success: True if test succeeded
        success_level: WFRP Success Level (SL)
        is_double: True if roll has matching digits
        is_critical: True if critical success (doubles ≤ target)
        is_fumble: True if fumble (100 or doubles > target)
        doubles_classification: "crit", "fumble", or "none"
        outcome: Narrative outcome description ("Astounding Success", "Failure", etc.)
        outcome_color: Discord color name for the outcome
        flavor_text: Rich narrative description
        mechanics_text: Mechanical consequences description
        delay_hours: Optional delay in hours (for failures)

    Example:
        BoatHandlingResult(
            character_name="Anara of Sānxiá",
            character_species="Human",
            character_status="Brass 3",
            skill_name="Sail",
            skill_value=45,
            lore_bonus=2,
            base_difficulty=0,
            weather_penalty=-10,
            final_difficulty=-10,
            final_target=37,  # 45 + 0 - 10 + 2
            roll_value=22,
            success=True,
            success_level=1,  # (37//10) - (22//10) = 3-2 = 1
            is_double=True,
            is_critical=True,
            is_fumble=False,
            doubles_classification="crit",
            outcome="Success",
            outcome_color="green",
            flavor_text="⚓ Anara handles the vessel...",
            mechanics_text="**Vessel controlled.**",
            delay_hours=None,
        )
    """

    # Character info
    character_name: str
    character_species: str
    character_status: str

    # Skill details
    skill_name: str
    skill_value: int
    lore_bonus: int

    # Difficulty breakdown
    base_difficulty: int
    weather_penalty: int
    final_difficulty: int
    final_target: int

    # Roll results
    roll_value: int
    success: bool
    success_level: int

    # Doubles detection
    is_double: bool
    is_critical: bool
    is_fumble: bool
    doubles_classification: str

    # Narrative outcome
    outcome: str
    outcome_color: str  # "gold", "green", "orange", "red", "dark_red"
    flavor_text: str
    mechanics_text: str
    delay_hours: Optional[int] = None


class BoatHandlingService:
    """
    Service for boat handling test logic and narrative generation.

    Provides methods for determining boat handling skills, calculating bonuses,
    executing tests, and generating rich narrative outcomes based on success levels.
    """

    # Success Level thresholds for outcome descriptions
    SL_ASTOUNDING = 6
    SL_IMPRESSIVE = 4
    SL_SUCCESS = 2
    SL_MARGINAL = 0

    def determine_skill(self, river_skills: Dict[str, int]) -> tuple[str, int]:
        """
        Determine which boat handling skill to use (Sail preferred, Row fallback).

        Args:
            river_skills: Dictionary of river travel skills
                         {"Row": 35, "Sail": 45, "Lore (Riverways)": 20}

        Returns:
            Tuple of (skill_name, skill_value)

        Raises:
            ValueError: If character has neither Row nor Sail skill

        Examples:
            >>> service = BoatHandlingService()
            >>> service.determine_skill({"Row": 30, "Sail": 45})
            ("Sail", 45)
            >>> service.determine_skill({"Row": 30})
            ("Row", 30)
        """
        row_skill = river_skills.get("Row")
        sail_skill = river_skills.get("Sail")

        # Prefer Sail if available, fallback to Row
        if sail_skill is not None and sail_skill > 0:
            return ("Sail", sail_skill)
        elif row_skill is not None and row_skill > 0:
            return ("Row", row_skill)
        else:
            raise ValueError("Character has no Row or Sail skill!")

    def calculate_lore_bonus(self, lore_riverways: Optional[int]) -> int:
        """
        Calculate Lore (Riverways) bonus (first digit of skill value).

        Args:
            lore_riverways: Lore (Riverways) skill value (0-100), or None if not learned

        Returns:
            Bonus value (0-9)

        Examples:
            >>> service = BoatHandlingService()
            >>> service.calculate_lore_bonus(25)
            2
            >>> service.calculate_lore_bonus(0)
            0
            >>> service.calculate_lore_bonus(None)
            0
        """
        if lore_riverways is None or lore_riverways <= 0:
            return 0
        return lore_riverways // 10

    def perform_boat_test(
        self,
        character_data: Dict[str, Any],
        difficulty: int,
        weather_penalty: int = 0,
    ) -> BoatHandlingResult:
        """
        Perform a complete boat handling test with narrative outcome generation.

        Args:
            character_data: Character dictionary from character_data.py
                           Must contain: name, species, status, river_travelling_skills
            difficulty: Base difficulty modifier (-50 to +60)
            weather_penalty: Additional penalty from weather conditions (usually negative)

        Returns:
            BoatHandlingResult with complete test outcome

        Raises:
            ValueError: If character has no boat handling skills

        Example:
            >>> service = BoatHandlingService()
            >>> char = {
            ...     "name": "Anara of Sānxiá",
            ...     "species": "Human",
            ...     "status": "Brass 3",
            ...     "river_travelling_skills": {
            ...         "Row": 30,
            ...         "Sail": 45,
            ...         "Lore (Riverways)": 20
            ...     }
            ... }
            >>> result = service.perform_boat_test(char, difficulty=-10, weather_penalty=-5)
            >>> print(result.outcome)
            Success
        """
        # Extract character info
        char_name = character_data["name"]
        char_species = character_data["species"]
        char_status = character_data["status"]
        river_skills = character_data.get("river_travelling_skills", {})

        # Determine skill to use
        skill_name, skill_value = self.determine_skill(river_skills)

        # Calculate Lore bonus
        lore_riverways = river_skills.get("Lore (Riverways)", 0)
        lore_bonus = self.calculate_lore_bonus(lore_riverways)

        # Calculate final difficulty and target
        final_difficulty = difficulty + weather_penalty
        final_target = skill_value + final_difficulty + lore_bonus
        final_target = max(1, min(100, final_target))  # Clamp to 1-100

        # Roll d100
        roll_value = random.randint(1, 100)

        # Calculate Success Level
        success_level = (final_target // 10) - (roll_value // 10)
        success = roll_value <= final_target

        # Check for doubles (critical/fumble)
        doubles_classification = check_wfrp_doubles(roll_value, final_target)
        is_double = doubles_classification != "none"
        is_critical = doubles_classification == "crit"
        is_fumble = doubles_classification == "fumble"

        # Fumbles always fail, criticals always succeed
        if is_fumble:
            success = False
        elif is_critical:
            success = True

        # Generate narrative outcome
        outcome_data = self._generate_outcome(
            char_name, success, success_level, is_critical, is_fumble
        )

        return BoatHandlingResult(
            character_name=char_name,
            character_species=char_species,
            character_status=char_status,
            skill_name=skill_name,
            skill_value=skill_value,
            lore_bonus=lore_bonus,
            base_difficulty=difficulty,
            weather_penalty=weather_penalty,
            final_difficulty=final_difficulty,
            final_target=final_target,
            roll_value=roll_value,
            success=success,
            success_level=success_level,
            is_double=is_double,
            is_critical=is_critical,
            is_fumble=is_fumble,
            doubles_classification=doubles_classification,
            outcome=outcome_data["outcome"],
            outcome_color=outcome_data["color"],
            flavor_text=outcome_data["flavor"],
            mechanics_text=outcome_data["mechanics"],
            delay_hours=outcome_data.get("delay_hours"),
        )

    def _generate_outcome(
        self,
        char_name: str,
        success: bool,
        success_level: int,
        is_critical: bool,
        is_fumble: bool,
    ) -> Dict[str, Any]:
        """
        Generate narrative outcome based on test results.

        Args:
            char_name: Character's name for flavor text
            success: Whether the test succeeded
            success_level: WFRP Success Level
            is_critical: Whether this is a critical success
            is_fumble: Whether this is a fumble

        Returns:
            Dictionary with outcome, color, flavor, mechanics, and optional delay_hours

        Note:
            Colors are string names that correspond to discord.Color methods:
            "gold", "green", "orange", "red", "dark_red"
        """
        if success:
            # Success outcomes
            if success_level >= self.SL_ASTOUNDING:
                return {
                    "outcome": "Astounding Success",
                    "color": "gold",
                    "flavor": f"🌟 {char_name} expertly navigates the vessel with masterful control! The boat glides through the water as if guided by the gods themselves.",
                    "mechanics": "**Vessel maintained perfectly.** No issues, and the party may even gain time or avoid hazards.",
                }
            elif success_level >= self.SL_IMPRESSIVE:
                return {
                    "outcome": "Impressive Success",
                    "color": "green",
                    "flavor": f"⚓ {char_name} handles the vessel with exceptional skill, anticipating every current and wind shift perfectly.",
                    "mechanics": "**Vessel under full control.** The journey proceeds smoothly without incident.",
                }
            elif success_level >= self.SL_SUCCESS:
                return {
                    "outcome": "Success",
                    "color": "green",
                    "flavor": f"✓ {char_name} maintains steady control of the vessel, navigating confidently through the waters.",
                    "mechanics": "**Vessel controlled.** The boat continues on course as planned.",
                }
            else:
                return {
                    "outcome": "Marginal Success",
                    "color": "green",
                    "flavor": f"~ {char_name} keeps the vessel under control, though it takes some effort and concentration.",
                    "mechanics": "**Barely maintained control.** Minor issues but nothing serious.",
                }
        else:
            # Failure outcomes
            if success_level <= -self.SL_ASTOUNDING:
                return {
                    "outcome": "Astounding Failure",
                    "color": "dark_red",
                    "flavor": f"💀 {char_name} loses complete control! The vessel lurches dangerously, and panic ensues as water splashes over the sides!",
                    "mechanics": "**CRITICAL FAILURE!** Vessel damaged or capsized. Possible injuries. GM determines consequences (collision, taking on water, cargo lost, etc.).",
                }
            elif success_level <= -self.SL_IMPRESSIVE:
                # Roll for delay (2d12 hours)
                delay_hours = sum([random.randint(1, 12), random.randint(1, 12)])
                return {
                    "outcome": "Impressive Failure",
                    "color": "red",
                    "flavor": f"⚠️ {char_name} struggles badly with the vessel! It veers off course alarmingly, and everyone aboard holds on tight.",
                    "mechanics": f"**Severe loss of control.** Vessel forced off course. **Delay: {delay_hours} hours**. Possible damage to vessel or cargo. May require repairs.",
                    "delay_hours": delay_hours,
                }
            elif success_level <= -self.SL_SUCCESS:
                return {
                    "outcome": "Failure",
                    "color": "orange",
                    "flavor": f"✗ {char_name} fails to maintain proper control. The vessel drifts or slows, requiring corrective action.",
                    "mechanics": "**Loss of control.** Vessel goes off course or slows significantly. Delay of 1-2 hours to correct. Minor damage possible.",
                }
            else:
                return {
                    "outcome": "Marginal Failure",
                    "color": "orange",
                    "flavor": f"≈ {char_name} barely loses control, but manages to avoid the worst consequences through sheer luck.",
                    "mechanics": "**Near miss.** Brief loss of control but quickly recovered. Small delay (~30 minutes) or minor course correction needed.",
                }
