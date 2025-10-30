"""
Command Constants - Centralized constants for Discord commands.

Provides channel names, role names, and other magic strings used
across multiple command modules. This eliminates hardcoded strings
and provides a single source of truth for configuration values.

Usage:
    from commands.constants import (
        CHANNEL_COMMAND_LOG,
        CHANNEL_GM_NOTIFICATIONS,
        DIFFICULTY_AVERAGE,
        VALID_TIMES
    )
"""

# ============================================================================
# Discord Configuration
# ============================================================================

# Discord channel names
CHANNEL_COMMAND_LOG = "boat-travelling-log"
CHANNEL_GM_NOTIFICATIONS = "boat-travelling-notifications"

# Discord role names
ROLE_GM = "GM"


# ============================================================================
# WFRP Mechanics Constants
# ============================================================================

# WFRP difficulty modifiers (following WFRP 4e rules)
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

# Human-readable difficulty names
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

# WFRP skill value constraints
WFRP_SKILL_MIN = 1
WFRP_SKILL_MAX = 100
WFRP_ROLL_FUMBLE = 100
WFRP_ROLL_MIN_DOUBLE = 1  # 01 counts as doubles


# ============================================================================
# Display Configuration
# ============================================================================

# Display thresholds
MAX_DICE_DISPLAY = 20  # Show individual dice results only if ≤20 dice


# ============================================================================
# Time of Day Options
# ============================================================================

# Valid time of day values
TIME_DAWN = "dawn"
TIME_MIDDAY = "midday"
TIME_DUSK = "dusk"
TIME_MIDNIGHT = "midnight"

DEFAULT_TIME = TIME_MIDDAY

VALID_TIMES = [TIME_DAWN, TIME_MIDDAY, TIME_DUSK, TIME_MIDNIGHT]


# ============================================================================
# Weather Configuration
# ============================================================================

# Stage configuration limits
STAGE_DURATION_MIN = 1
STAGE_DURATION_MAX = 10
STAGE_DURATION_DEFAULT = 3

# Display modes
DISPLAY_MODE_SIMPLE = "simple"
DISPLAY_MODE_DETAILED = "detailed"
DISPLAY_MODE_DEFAULT = DISPLAY_MODE_SIMPLE

VALID_DISPLAY_MODES = [DISPLAY_MODE_SIMPLE, DISPLAY_MODE_DETAILED]
