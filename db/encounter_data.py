"""
River Encounter Data Module

Comprehensive river encounter system for the /river-encounter command with probability-based
d100 encounter tables, flavor texts, and mechanical data for WFRP 4th Edition river travel.

Key Responsibilities:
    - Encounter type determination (positive, coincidental, uneventful, harmful, accident)
    - Flavor text generation (player-facing cryptic/grimdark descriptions)
    - GM mechanical data (encounter details, effects, tests, damage)
    - d100 table lookups for all encounter categories

Encounter Categories:
    - Positive (1-10): Beneficial encounters that help the party
    - Coincidental (11-25): Neutral, curious events with no mechanical impact
    - Uneventful (26-85): Nothing happens (most common outcome)
    - Harmful (86-95): Dangerous encounters requiring tests or causing damage
    - Accident (96-100): Critical boat/crew accidents with complex mechanics

Data Structure:
    - Each encounter category has flavor texts (player-facing) and detail tables (GM-facing)
    - Encounter tables use (min_roll, max_roll) tuple keys for d100 ranges
    - Each encounter contains: title, description, effects list, mechanics dict
    - Accident encounters have the most complex mechanics with nested test/failure chains

Usage:
    1. Roll d100 to determine encounter type:
       encounter_type = get_encounter_type_from_roll(roll)

    2. Get player flavor text:
       flavor = get_random_flavor_text(encounter_type)

    3. Get GM mechanics (if needed):
       if encounter_type == "positive":
           details = get_positive_encounter_from_roll(detail_roll)
       elif encounter_type == "harmful":
           details = get_harmful_encounter_from_roll(detail_roll)
       # etc.

Design Principles:
    - Player flavor texts reveal no mechanics (grimdark atmosphere only)
    - GM data is comprehensive with all mechanical details
    - Encounter ranges complete (no gaps in d100 tables)
    - Accidents have most complex mechanics (critical hits, drowning, fire)
    - Uneventful is most common (60% chance)
"""

from typing import Dict
import random

# =============================================================================
# MODULE-LEVEL CONSTANTS
# =============================================================================

# Encounter Type Roll Ranges (d100)
ENCOUNTER_TYPE_POSITIVE_MIN = 1
ENCOUNTER_TYPE_POSITIVE_MAX = 10
ENCOUNTER_TYPE_COINCIDENTAL_MIN = 11
ENCOUNTER_TYPE_COINCIDENTAL_MAX = 25
ENCOUNTER_TYPE_UNEVENTFUL_MIN = 26
ENCOUNTER_TYPE_UNEVENTFUL_MAX = 85
ENCOUNTER_TYPE_HARMFUL_MIN = 86
ENCOUNTER_TYPE_HARMFUL_MAX = 95
ENCOUNTER_TYPE_ACCIDENT_MIN = 96
ENCOUNTER_TYPE_ACCIDENT_MAX = 100

# Encounter Type Names
ENCOUNTER_TYPE_POSITIVE = "positive"
ENCOUNTER_TYPE_COINCIDENTAL = "coincidental"
ENCOUNTER_TYPE_UNEVENTFUL = "uneventful"
ENCOUNTER_TYPE_HARMFUL = "harmful"
ENCOUNTER_TYPE_ACCIDENT = "accident"

# Dice Roll Validation
D100_MIN = 1
D100_MAX = 100

# Encounter Detail Keys
KEY_TITLE = "title"
KEY_DESCRIPTION = "description"
KEY_EFFECTS = "effects"
KEY_MECHANICS = "mechanics"
KEY_ROLL = "roll"

# =============================================================================
# PLAYER FLAVOR TEXT TABLES
# These are shown to players - cryptic, grimdark, no mechanics revealed
# =============================================================================

POSITIVE_FLAVOR_TEXTS = [
    "The stench of the river seems... almost bearable today. How peculiar.",
    "A rare moment of peace. Suspicious, really. The gods must be planning something worse.",
    "For once, the water doesn't look like it wants to kill you. Enjoy it while it lasts.",
    "Something fortunate happens. You're not sure whether to be grateful or terrified of the price.",
    "The river grants a small mercy. Best not to question it in these dark times.",
    "A stroke of luck befalls the crew. Probably won't last—nothing good ever does.",
    "The journey eases, if only briefly. Savor it; Morr's garden awaits us all.",
    "Things go surprisingly well. The Gods of Chaos must be laughing at something else today.",
]

COINCIDENTAL_FLAVOR_TEXTS = [
    "Something odd catches your eye along the riverbank. Nothing you can quite explain.",
    "The river reveals one of its many peculiarities. You're not sure what to make of it.",
    "An unusual sight breaks the monotony. At least it's not trying to eat you... yet.",
    "Something strange, but ultimately inconsequential. The river has shown you stranger.",
    "You witness something curious on your journey. File it away for later nightmares.",
    "The river's mysteries manifest before you. Whether blessing or curse, who can say?",
    "An oddity presents itself. In these lands, even the mundane carries an air of dread.",
    "Something catches your attention. Probably means nothing. Probably.",
]

UNEVENTFUL_FLAVOR_TEXTS = [
    "The river flows, you float, nothing tries to kill you. A good day by Reikland standards.",
    "Remarkably unremarkable. The most you can hope for in these wretched times.",
    "Nothing happens. You're almost disappointed. Almost.",
    "The journey continues in blessed tedium. Better boring than dead, as they say.",
    "Another uneventful stretch. Pray to Ranald it stays that way.",
    "The gods ignore you today. Sometimes that's the best outcome.",
    "Mile after sodden mile of nothing. Just as Morr intended.",
    "Peace, quiet, and the gentle lapping of possibly-diseased water. Paradise.",
]

HARMFUL_FLAVOR_TEXTS = [
    "Trouble. Of course there's trouble. There's always trouble on these thrice-damned rivers.",
    "Something wicked this way comes. And you're on a boat with nowhere to run.",
    "The river demands its toll in blood and tears. Mostly yours.",
    "Danger presents itself with the inevitability of death and taxes. Usually both.",
    "Your day takes a turn for the worse. Which, on the river, is saying something.",
    "The other shoe drops. Along with several sharp objects aimed at your head.",
    "Misfortune strikes like a drunken flagellant—unexpected and violent.",
    "The river shows its teeth. Time to see if Shallya's mercy extends to fools on boats.",
]

ACCIDENT_FLAVOR_TEXTS = [
    "Something on the boat breaks. Because of course it does. Nothing works properly in this forsaken land.",
    "CRACK! That didn't sound good. That didn't sound good at all.",
    "The boat protests its existence with alarming sounds. You sympathize, but now's not the time.",
    "Something vital chooses this exact moment to fail catastrophically. Typical.",
    "The ship groans ominously. Either it's falling apart or possessed. Possibly both.",
    "A critical failure occurs at the worst possible moment. As is tradition.",
    "Murphy's Law strikes with the precision of a ratcatcher's blade. Something's broken.",
    "The boat decides today is a good day to test your crisis management skills. It is not.",
    "Disaster strikes from an unexpected quarter. Mostly because you're too poor to afford a boat that works properly.",
]

# =============================================================================
# ENCOUNTER TYPE PROBABILITIES
# =============================================================================


def get_encounter_type_from_roll(roll: int) -> str:
    """
    Determine encounter type from a d100 roll using standard WFRP encounter probabilities.

    The encounter distribution is:
        - Positive: 1-10 (10% chance) - Beneficial encounters
        - Coincidental: 11-25 (15% chance) - Neutral curiosities
        - Uneventful: 26-85 (60% chance) - Nothing happens
        - Harmful: 86-95 (10% chance) - Dangerous encounters
        - Accident: 96-100 (5% chance) - Critical boat accidents

    Args:
        roll: The d100 roll result (1-100)

    Returns:
        Encounter type string: "positive", "coincidental", "uneventful", "harmful", or "accident"

    Raises:
        ValueError: If roll is outside 1-100 range

    Examples:
        >>> get_encounter_type_from_roll(5)
        'positive'
        >>> get_encounter_type_from_roll(50)
        'uneventful'
        >>> get_encounter_type_from_roll(97)
        'accident'
    """
    if roll < D100_MIN or roll > D100_MAX:
        raise ValueError(f"Roll must be between {D100_MIN} and {D100_MAX}, got {roll}")

    if ENCOUNTER_TYPE_POSITIVE_MIN <= roll <= ENCOUNTER_TYPE_POSITIVE_MAX:
        return ENCOUNTER_TYPE_POSITIVE
    elif ENCOUNTER_TYPE_COINCIDENTAL_MIN <= roll <= ENCOUNTER_TYPE_COINCIDENTAL_MAX:
        return ENCOUNTER_TYPE_COINCIDENTAL
    elif ENCOUNTER_TYPE_UNEVENTFUL_MIN <= roll <= ENCOUNTER_TYPE_UNEVENTFUL_MAX:
        return ENCOUNTER_TYPE_UNEVENTFUL
    elif ENCOUNTER_TYPE_HARMFUL_MIN <= roll <= ENCOUNTER_TYPE_HARMFUL_MAX:
        return ENCOUNTER_TYPE_HARMFUL
    else:  # 96-100
        return ENCOUNTER_TYPE_ACCIDENT


def get_random_flavor_text(encounter_type: str) -> str:
    """
    Get a random player-facing flavor text for the given encounter type.

    Flavor texts are cryptic, grimdark descriptions that set atmosphere without
    revealing mechanics. They're designed for WFRP's dark fantasy tone.

    Args:
        encounter_type: Type of encounter ("positive", "coincidental", "uneventful",
                       "harmful", or "accident")

    Returns:
        Random flavor text string from the appropriate table

    Raises:
        ValueError: If encounter_type is not recognized

    Examples:
        >>> flavor = get_random_flavor_text("positive")
        >>> # Returns one of 8 positive flavor texts randomly
        >>> flavor = get_random_flavor_text("harmful")
        >>> # Returns one of 8 harmful flavor texts randomly
    """
    flavor_map = {
        ENCOUNTER_TYPE_POSITIVE: POSITIVE_FLAVOR_TEXTS,
        ENCOUNTER_TYPE_COINCIDENTAL: COINCIDENTAL_FLAVOR_TEXTS,
        ENCOUNTER_TYPE_UNEVENTFUL: UNEVENTFUL_FLAVOR_TEXTS,
        ENCOUNTER_TYPE_HARMFUL: HARMFUL_FLAVOR_TEXTS,
        ENCOUNTER_TYPE_ACCIDENT: ACCIDENT_FLAVOR_TEXTS,
    }

    if encounter_type not in flavor_map:
        raise ValueError(f"Unknown encounter type: {encounter_type}")

    return random.choice(flavor_map[encounter_type])


# =============================================================================
# POSITIVE ENCOUNTERS TABLE (GM DATA)
# =============================================================================

POSITIVE_ENCOUNTERS = {
    (1, 10): {
        "title": "Friendly Fisherfolk",
        "description": "The Characters encounter a group of friendly fisherfolk who share their catch, providing a hearty meal and good company.",
        "effects": ["Meal provided", "Morale boost"],
        "mechanics": None,
    },
    (11, 20): {
        "title": "River Gossip",
        "description": "The Characters overhear some useful gossip from passing boatmen about the river ahead, gaining valuable information about safe passages and potential dangers.",
        "effects": ["Information about river ahead", "Knowledge of safe passages"],
        "mechanics": None,
    },
    (21, 30): {
        "title": "Picturesque Stop",
        "description": "The Characters find a particularly beautiful and peaceful spot along the river, perfect for resting and recovering their spirits.",
        "effects": ["Peaceful rest", "Stress reduction", "Scenic beauty"],
        "mechanics": None,
    },
    (31, 40): {
        "title": "Trading Post",
        "description": "The Characters come across a small trading post where they can buy supplies at reasonable prices and sell any goods they've acquired.",
        "effects": ["Access to supplies", "Trading opportunity", "Reasonable prices"],
        "mechanics": None,
    },
    (41, 50): {
        "title": "Experienced Guide",
        "description": "The Characters meet an experienced river guide who offers advice on navigating the upcoming stretches of river, providing helpful tips and warnings.",
        "effects": [
            "Navigation advice",
            "Warnings about hazards",
            "Route optimization",
        ],
        "mechanics": {"bonus": "+10 to next Boat Handling Test"},
    },
    (51, 60): {
        "title": "A Helping Hand",
        "description": "The Characters encounter other travelers who lend assistance with a minor repair or task, saving time and effort.",
        "effects": ["Minor repairs completed", "Time saved", "Goodwill earned"],
        "mechanics": None,
    },
    (61, 70): {
        "title": "Hidden Cove",
        "description": "The Characters discover a hidden cove that provides excellent shelter from weather and prying eyes, perfect for a safe rest.",
        "effects": ["Safe shelter", "Weather protection", "Privacy"],
        "mechanics": None,
    },
    (71, 80): {
        "title": "Clear Skies",
        "description": "The weather clears up unexpectedly, providing perfect conditions for travel with good visibility and calm waters.",
        "effects": ["Weather improvement", "Calm waters", "Good visibility"],
        "mechanics": {"bonus": "+10 to Boat Handling Tests for remainder of day"},
    },
    (81, 90): {
        "title": "Healer's Touch",
        "description": "The Characters meet a traveling healer who offers to tend to any wounds or ailments, restoring their health and vigor.",
        "effects": ["Wounds healed", "Ailments treated", "Health restored"],
        "mechanics": {"healing": "1d10 Wounds healed per character"},
    },
    (91, 100): {
        "title": "Blessed Journey",
        "description": "The Characters' journey is particularly smooth and peaceful, and they feel a sense of divine favor. They heal all Wounds and recover all Fatigued Conditions.",
        "effects": [
            "Heal all Wounds",
            "Recover all Fatigued Conditions",
            "Divine favor",
        ],
        "mechanics": {"heal_wounds": "all", "remove_conditions": ["Fatigued"]},
    },
}


def get_positive_encounter_from_roll(roll: int) -> Dict:
    """
    Get positive encounter GM details from a d100 roll.

    Positive encounters are beneficial events that help the party through healing,
    information, assistance, or favorable conditions. Range covers full d100 (1-100)
    with 10 different positive encounters.

    Args:
        roll: The d100 roll result (1-100)

    Returns:
        Dictionary containing encounter details with keys:
            - title: Encounter name
            - description: Full GM description
            - effects: List of mechanical effects
            - mechanics: Dict with mechanical details (bonuses, healing, etc.) or None
            - roll: The original roll value

    Raises:
        ValueError: If roll is outside 1-100 range or no encounter found

    Examples:
        >>> encounter = get_positive_encounter_from_roll(45)
        >>> encounter['title']
        'Experienced Guide'
        >>> encounter['mechanics']['bonus']
        '+10 to next Boat Handling Test'
    """
    if roll < D100_MIN or roll > D100_MAX:
        raise ValueError(f"Roll must be between {D100_MIN} and {D100_MAX}, got {roll}")

    for (min_roll, max_roll), encounter in POSITIVE_ENCOUNTERS.items():
        if min_roll <= roll <= max_roll:
            return {**encounter, KEY_ROLL: roll}

    # Should never reach here if data is complete
    raise ValueError(f"No positive encounter found for roll {roll}")


# =============================================================================
# COINCIDENTAL ENCOUNTERS TABLE (GM DATA)
# =============================================================================

COINCIDENTAL_ENCOUNTERS = {
    (1, 10): {
        "title": "Mysterious Ruins",
        "description": "The Characters spot ancient ruins along the riverbank, covered in moss and mystery. They seem abandoned but intriguing.",
        "effects": ["Curiosity piqued", "Possible exploration opportunity"],
        "mechanics": None,
    },
    (11, 20): {
        "title": "Abandoned Boat",
        "description": "An empty boat drifts past or is found moored to the bank. There's no sign of its crew, and it appears to have been abandoned recently.",
        "effects": ["Mystery", "Salvage opportunity", "Unease"],
        "mechanics": None,
    },
    (21, 30): {
        "title": "Traveling Caravan",
        "description": "The Characters encounter a caravan traveling along the riverside road. They exchange waves but don't interact further.",
        "effects": ["Sight of other travelers", "Momentary companionship"],
        "mechanics": None,
    },
    (31, 40): {
        "title": "Unusual Wildlife",
        "description": "The Characters spot unusual or rare wildlife along the river—perhaps a white stag, strange fish, or exotic birds.",
        "effects": ["Interesting observation", "Natural wonder"],
        "mechanics": None,
    },
    (41, 50): {
        "title": "Strange Lights",
        "description": "Mysterious lights appear along the riverbank or in the water. They don't seem threatening, just... odd.",
        "effects": ["Mystery", "Slight unease", "Curiosity"],
        "mechanics": None,
    },
    (51, 60): {
        "title": "Religious Procession",
        "description": "A religious procession is visible on the shore—priests or pilgrims traveling to some sacred site.",
        "effects": ["Cultural observation", "Religious significance"],
        "mechanics": None,
    },
    (61, 70): {
        "title": "Fisher's Folly",
        "description": "The Characters witness a local fisherman's mishap—falling into water, losing catch, or tangling lines. Amusing but harmless.",
        "effects": ["Entertainment", "Local color", "Brief distraction"],
        "mechanics": None,
    },
    (71, 80): {
        "title": "Weather Change",
        "description": "The weather shifts noticeably—clouds roll in, fog lifts, or wind changes direction—but without significant impact on travel.",
        "effects": ["Weather shift", "Atmospheric change"],
        "mechanics": None,
    },
    (81, 90): {
        "title": "Drifting Debris",
        "description": "Various debris drifts past in the current—logs, barrels, remnants of someone else's journey. Nothing valuable or dangerous.",
        "effects": ["River flotsam", "Signs of other travelers"],
        "mechanics": None,
    },
    (91, 100): {
        "title": "Lost Item",
        "description": "The Characters find a minor lost item floating in the water or on the bank—a boot, a hat, a wooden cup. Worthless but curious.",
        "effects": ["Curiosity", "Minor find", "Story potential"],
        "mechanics": None,
    },
}


def get_coincidental_encounter_from_roll(roll: int) -> Dict:
    """
    Get coincidental encounter GM details from a d100 roll.

    Coincidental encounters are neutral, curious events that add flavor without
    mechanical impact. These are interesting observations, mysteries, or oddities
    that enrich the journey narrative.

    Args:
        roll: The d100 roll result (1-100)

    Returns:
        Dictionary containing encounter details with keys:
            - title: Encounter name
            - description: Full GM description
            - effects: List of atmospheric/narrative effects
            - mechanics: Always None for coincidental encounters
            - roll: The original roll value

    Raises:
        ValueError: If roll is outside 1-100 range or no encounter found

    Examples:
        >>> encounter = get_coincidental_encounter_from_roll(15)
        >>> encounter['title']
        'Abandoned Boat'
        >>> encounter['mechanics']
        None
    """
    if roll < D100_MIN or roll > D100_MAX:
        raise ValueError(f"Roll must be between {D100_MIN} and {D100_MAX}, got {roll}")

    for (min_roll, max_roll), encounter in COINCIDENTAL_ENCOUNTERS.items():
        if min_roll <= roll <= max_roll:
            return {**encounter, KEY_ROLL: roll}

    # Should never reach here if data is complete
    raise ValueError(f"No coincidental encounter found for roll {roll}")


# =============================================================================
# UNEVENTFUL ENCOUNTER (GM DATA)
# =============================================================================

UNEVENTFUL_ENCOUNTER = {
    "title": "Uneventful Travel",
    "description": "The Characters travel along the river without incident. The journey continues smoothly with nothing of note occurring.",
    "effects": [],
    "mechanics": None,
}


def get_uneventful_encounter() -> Dict:
    """
    Get the uneventful encounter details (nothing happens).

    This is the most common encounter type (60% probability). Journey continues
    smoothly with no mechanical or narrative events.

    Returns:
        Dictionary containing encounter details with keys:
            - title: "Uneventful Travel"
            - description: Standard uneventful description
            - effects: Empty list (no effects)
            - mechanics: None

    Examples:
        >>> encounter = get_uneventful_encounter()
        >>> encounter['title']
        'Uneventful Travel'
        >>> encounter['effects']
        []
    """
    return {**UNEVENTFUL_ENCOUNTER}


# =============================================================================
# HARMFUL ENCOUNTERS TABLE (GM DATA)
# =============================================================================

HARMFUL_ENCOUNTERS = {
    (1, 10): {
        "title": "Blocked Path",
        "description": "The river passage ahead is blocked by debris, fallen trees, or shallow waters. The Characters must find an alternate route or clear the blockage, risking the Fatigued Condition.",
        "effects": [
            "Route blocked",
            "Must clear or detour",
            "Risk of Fatigued Condition",
        ],
        "mechanics": {
            "test": "Challenging (+0) Strength Test to clear",
            "failure": "Gain Fatigued Condition",
        },
    },
    (11, 20): {
        "title": "River Pirates",
        "description": "The Characters are ambushed by river pirates who demand cargo or coin. Combat seems inevitable unless the party can talk or bribe their way out.",
        "effects": ["Combat encounter", "Risk of losing cargo", "Potential violence"],
        "mechanics": {
            "combat": True,
            "enemies": "3-6 River Pirates",
            "alternative": "Bribe of 10 GC per pirate",
        },
    },
    (21, 30): {
        "title": "Unfriendly Waters",
        "description": "The Characters enter a stretch of river known for ambushes and danger. Hostile locals watch from the banks, and the atmosphere is tense.",
        "effects": ["Increased tension", "Ambush risk", "Hostile territory"],
        "mechanics": {
            "test": "Challenging (+0) Perception Test",
            "success": "Spot ambush preparation",
            "failure": "Surprised if attack occurs",
        },
    },
    (31, 40): {
        "title": "Poisoned Waters",
        "description": "The river water here is contaminated with disease or poison. Any character who comes in contact with it risks sickness.",
        "effects": ["Contaminated water", "Disease risk", "Health hazard"],
        "mechanics": {
            "test": "Challenging (+0) Endurance Test",
            "failure": "Contract Minor Infection or The Galloping Trots",
        },
    },
    (41, 50): {
        "title": "Natural Hazard",
        "description": "A sudden storm, dangerous rapids, or other natural hazard threatens the boat and crew.",
        "effects": ["Weather threat", "Rapids danger", "Boat at risk"],
        "mechanics": {
            "test": "Difficult (-10) Boat Handling Test",
            "failure": "1d10 damage to boat, possible capsize",
        },
    },
    (51, 60): {
        "title": "Equipment Failure",
        "description": "A critical piece of equipment fails at an inopportune moment, requiring immediate repair or replacement.",
        "effects": ["Equipment broken", "Repairs needed", "Journey delayed"],
        "mechanics": {
            "test": "Challenging (+0) Trade (Carpentry or Smith) Test",
            "failure": "Cannot continue until repaired",
        },
    },
    (61, 70): {
        "title": "Infestation",
        "description": "The boat has become infested with rats, insects, or other vermin that spread disease and consume supplies.",
        "effects": ["Vermin infestation", "Disease risk", "Supply consumption"],
        "mechanics": {
            "supplies_lost": "1d10 encumbrance",
            "test": "Challenging (+0) Endurance Test per day",
            "failure": "Risk of disease",
        },
    },
    (71, 80): {
        "title": "Hostile Wildlife",
        "description": "Aggressive river creatures—perhaps river trolls, giant snapping turtles, or swarms of flesh-eating fish—attack the boat.",
        "effects": ["Wildlife attack", "Combat encounter", "Boat damage risk"],
        "mechanics": {
            "combat": True,
            "enemies": "1-3 hostile creatures (appropriate to region)",
            "damage_to_boat": "Possible",
        },
    },
    (81, 90): {
        "title": "Disease Outbreak",
        "description": "One or more crew members fall ill with a contagious disease, risking the health of the entire party.",
        "effects": ["Crew illness", "Contagion risk", "Journey delay"],
        "mechanics": {
            "initial_victims": "1d3 crew members",
            "test": "Challenging (+0) Endurance Test for others daily",
            "failure": "Contract same disease",
        },
    },
    (91, 100): {
        "title": "Sabotage",
        "description": "Someone has sabotaged the boat—a leak has been deliberately created, ropes cut, or cargo tampered with. Who did it and why?",
        "effects": ["Deliberate damage", "Mystery", "Trust issues"],
        "mechanics": {
            "damage": "1d10 damage to boat",
            "test": "Challenging (+0) Intuition Test",
            "success": "Identify saboteur",
        },
    },
}


def get_harmful_encounter_from_roll(roll: int) -> Dict:
    """
    Get harmful encounter GM details from a d100 roll.

    Harmful encounters are dangerous events requiring tests, causing damage, or
    threatening the party with disease, combat, or environmental hazards. These
    encounters have mechanical consequences and require player action.

    Args:
        roll: The d100 roll result (1-100)

    Returns:
        Dictionary containing encounter details with keys:
            - title: Encounter name
            - description: Full GM description
            - effects: List of harmful effects and consequences
            - mechanics: Dict with test requirements, damage, combat details, etc.
            - roll: The original roll value

    Raises:
        ValueError: If roll is outside 1-100 range or no encounter found

    Examples:
        >>> encounter = get_harmful_encounter_from_roll(15)
        >>> encounter['title']
        'River Pirates'
        >>> encounter['mechanics']['combat']
        True
        >>> encounter['mechanics']['enemies']
        '3-6 River Pirates'
    """
    if roll < D100_MIN or roll > D100_MAX:
        raise ValueError(f"Roll must be between {D100_MIN} and {D100_MAX}, got {roll}")

    for (min_roll, max_roll), encounter in HARMFUL_ENCOUNTERS.items():
        if min_roll <= roll <= max_roll:
            return {**encounter, KEY_ROLL: roll}

    # Should never reach here if data is complete
    raise ValueError(f"No harmful encounter found for roll {roll}")


# =============================================================================
# ACCIDENT ENCOUNTERS TABLE (GM DATA) - COMPLEX MECHANICS
# =============================================================================

ACCIDENT_ENCOUNTERS = {
    (1, 10): {
        "title": "Steering",
        "description": "The tiller bar breaks or the rudder falls off completely. The boat loses steering control and must be repaired immediately to avoid drifting into danger.",
        "effects": [
            "Loss of steering",
            "Boat cannot be controlled",
            "Immediate repair needed",
        ],
        "mechanics": {
            "damage_type": "critical_hit_steering",
            "reference": "Page 29 (boat damage rules)",
            "immediate_effect": "Boat drifts uncontrollably",
            "repair_test": {
                "name": "Trade (Carpentry)",
                "difficulty": "Difficult (-10)",
                "time": "1 hour",
            },
        },
    },
    (11, 20): {
        "title": "Broken Rigging",
        "description": "Some of the ropes controlling the sail break, either as a result of neglect or because of a sudden high wind. The boat loses speed, and the sail may come down, possibly snapping the top off the mast and bringing tackle down with it.",
        "effects": [
            "Rigging damaged",
            "Loss of speed",
            "Sail collapse risk",
            "Mast damage",
        ],
        "mechanics": {
            "damage_type": "critical_hit_rigging",
            "reference": "Page 29 (boat damage rules)",
            "immediate_effect": "Boat loses speed",
            "secondary_risk": "Sail may collapse and damage mast",
            "repair_test": {
                "name": "Trade (Sailmaking or Carpentry)",
                "difficulty": "Challenging (+0)",
                "time": "30 minutes",
            },
        },
    },
    (21, 30): {
        "title": "Swinging Boom",
        "description": "A sudden crosswind causes the sail to snap round, swinging the boom across the deck. Characters in the path of the boom must dodge or be struck and potentially knocked overboard.",
        "effects": [
            "Boom swings across deck",
            "Risk of injury",
            "Risk of falling overboard",
        ],
        "mechanics": {
            "primary_test": {
                "name": "Dodge",
                "difficulty": "Challenging (+0)",
                "target": "Characters in path of boom",
            },
            "primary_failure": {"damage": "+5", "hits": 1},
            "secondary_test": {
                "name": "Athletics",
                "difficulty": "Challenging (+0)",
                "trigger": "if_hit",
            },
            "secondary_failure": {"effect": "knocked_into_river"},
        },
    },
    (31, 40): {
        "title": "Snagged Anchor",
        "description": "The anchor snags on a submerged obstacle while being raised or lowered. The sudden jerk threatens to knock crew members off their feet or snap the anchor line entirely.",
        "effects": [
            "Anchor snagged",
            "Risk of falling",
            "Risk of injury",
            "Anchor line may snap",
        ],
        "mechanics": {
            "primary_test": {
                "name": "Athletics",
                "difficulty": "Challenging (+0)",
                "target": "All crew on deck",
            },
            "primary_failure": {"effect": "Knocked prone", "damage": "+3", "hits": 1},
            "secondary_effect": {
                "risk": "Anchor line may snap",
                "consequence": "Lose anchor, boat drifts",
            },
        },
    },
    (41, 50): {
        "title": "Cargo Shift",
        "description": "During a sharp turn or in rough waters, unsecured or poorly secured cargo shifts violently. Characters in the cargo area risk being struck, and some cargo may be lost overboard.",
        "effects": [
            "Cargo shifts violently",
            "Risk of injury",
            "Cargo lost overboard",
            "Potential fires/spills",
        ],
        "mechanics": {
            "primary_test": {
                "name": "Dodge",
                "difficulty": "Challenging (+0)",
                "target": "Characters in cargo area",
            },
            "primary_failure": {"damage": "+4", "hits": 1},
            "cargo_loss": {
                "formula": "10 + floor((1d100 + 5) / 10) * 10",
                "description": "Encumbrance of cargo lost overboard",
            },
            "additional_hazards": {
                "risk": "Hazardous cargo may spill or ignite",
                "effects": ["Fire risk", "Toxic spill risk", "Chemical hazard"],
            },
        },
    },
    (51, 60): {
        "title": "Loose Planking",
        "description": "Planks on the deck or hull come loose, either from wear, poor maintenance, or damage. The boat begins taking on water and requires immediate repairs.",
        "effects": [
            "Planks loose",
            "Taking on water",
            "Risk of Holed condition",
            "Sinking risk",
        ],
        "mechanics": {
            "immediate_effect": "Boat takes on water",
            "repair_test": {
                "name": "Trade (Carpentry)",
                "difficulty": "Challenging (+0)",
                "time": "20 minutes",
            },
            "failure_consequence": {
                "effect": "Boat gains Holed condition",
                "reference": "Page 29 (boat damage rules)",
            },
        },
    },
    (61, 70): {
        "title": "Navigational Error",
        "description": "Due to poor visibility, inaccurate maps, or simple mistake, the boat strikes a hidden rock, sandbar, or other obstacle beneath the water.",
        "effects": [
            "Boat strikes obstacle",
            "Hull damage",
            "Possible grounding",
            "Crew shaken",
        ],
        "mechanics": {
            "damage": {
                "type": "Roll on Boat Hit Location Chart",
                "reference": "Page 29",
            },
            "grounding_risk": {
                "test": "Challenging (+0) Boat Handling Test",
                "failure": "Boat is grounded",
            },
            "refloat_test": {
                "name": "Strength",
                "difficulty": "Difficult (-10)",
                "target": "All crew",
                "time": "1d10 hours",
            },
        },
    },
    (71, 80): {
        "title": "Man Overboard",
        "description": "A crew member falls into the river—whether from a slip, a lurch of the boat, or being knocked overboard. They must swim to safety while the crew attempts rescue.",
        "effects": [
            "Crew overboard",
            "Drowning risk",
            "Rescue needed",
            "Potential loss of crew",
        ],
        "mechanics": {
            "overboard_character": {
                "test": "Challenging (+0) Swim Test",
                "failure": "Begin drowning",
            },
            "rescue_test": {
                "name": "Strength or Dexterity",
                "difficulty": "Challenging (+0)",
                "target": "Rescuing characters",
                "time": "1 round",
            },
            "failure_consequence": {
                "effect": "Character swept away by current or drowns"
            },
        },
    },
    (81, 90): {
        "title": "Sudden Squall",
        "description": "A violent storm hits the boat with little warning. High winds, driving rain, and choppy waters threaten to capsize the vessel. The crew must fight to maintain control.",
        "effects": [
            "Violent storm",
            "High winds",
            "Capsize risk",
            "May trigger other accidents",
        ],
        "mechanics": {
            "duration": "2d10 rounds",
            "test_each_round": {
                "name": "Boat Handling",
                "difficulty": "Challenging (+0)",
                "target": "Helmsman",
            },
            "failure": {
                "effect": "Risk of capsize or additional accidents",
                "additional_roll": "May trigger another accident on the table",
            },
            "penalties": {
                "visibility": "All Perception Tests at -20",
                "actions": "All actions at -10 due to wind and rain",
            },
        },
    },
    (91, 100): {
        "title": "Fire on Board",
        "description": "A fire breaks out on the boat—perhaps from a lantern, cooking fire, or lightning strike. The flames spread quickly and threaten to consume the vessel.",
        "effects": [
            "Fire outbreak",
            "Spreading flames",
            "Smoke and panic",
            "Boat destruction risk",
        ],
        "mechanics": {
            "damage_per_turn": {"amount": "1d10", "target": "Superstructure"},
            "extinguish_test": {
                "name": "Dexterity",
                "difficulty": "Challenging (+0)",
                "target": "Each character fighting fire",
                "time": "1 round",
            },
            "success_threshold": {
                "description": "3 successful tests to extinguish",
                "note": "Fire spreads to new section each round not extinguished",
            },
            "spread_pattern": {
                "round_1": "Origin point",
                "round_2": "Adjacent section",
                "round_3": "Rigging or hull",
                "round_4+": "Multiple sections, boat may be lost",
            },
        },
    },
}


def get_accident_from_roll(roll: int) -> Dict:
    """
    Get accident encounter GM details from a d100 roll.

    Accident encounters are critical boat/crew emergencies with complex mechanics.
    These are the most dangerous encounters (5% chance) with cascading failure
    conditions, multiple tests, and potential for severe consequences including
    sinking, fire, crew loss, or complete boat destruction.

    Mechanics often include:
        - Primary tests (Dodge, Athletics, Boat Handling)
        - Secondary tests triggered by primary failure
        - Damage to boat components (steering, rigging, hull)
        - Environmental hazards (drowning, fire spread, storm duration)
        - References to WFRP boat damage rules (Page 29)

    Args:
        roll: The d100 roll result (1-100)

    Returns:
        Dictionary containing encounter details with keys:
            - title: Accident name
            - description: Full GM description
            - effects: List of critical effects and hazards
            - mechanics: Dict with complex nested test/failure mechanics
            - roll: The original roll value

    Raises:
        ValueError: If roll is outside 1-100 range or no accident found

    Examples:
        >>> accident = get_accident_from_roll(5)
        >>> accident['title']
        'Steering'
        >>> accident['mechanics']['damage_type']
        'critical_hit_steering'
        >>> accident['mechanics']['immediate_effect']
        'Boat drifts uncontrollably'
    """
    if roll < D100_MIN or roll > D100_MAX:
        raise ValueError(f"Roll must be between {D100_MIN} and {D100_MAX}, got {roll}")

    for (min_roll, max_roll), encounter in ACCIDENT_ENCOUNTERS.items():
        if min_roll <= roll <= max_roll:
            return {**encounter, KEY_ROLL: roll}

    # Should never reach here if data is complete
    raise ValueError(f"No accident encounter found for roll {roll}")
