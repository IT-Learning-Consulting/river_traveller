# Coding Conventions for Travelling-Bot

> **Purpose:** Comprehensive code style guide, naming conventions, and project standards for WFRP Discord bot development
> **Target Audience:** AI agents (Claude 4.5 Sonnet) and human developers
> **Companion Documents:** [CODEBASE_CONTEXT.md](CODEBASE_CONTEXT.md) (architecture) | [refactor_plan.md](../../refactor_plan.md) (refactoring guide)
> **Last Updated:** October 30, 2025
> **Version:** 2.0.0

---

## Quick Start for AI Agents

**If you're an AI agent working on this codebase:**

1. **Read this entire document first** (20-30 minutes) - it contains critical patterns you must follow
2. **Reference CODEBASE_CONTEXT.md** when you need to understand where code lives or how systems integrate
3. **Follow naming conventions strictly** - inconsistent naming creates technical debt
4. **Use the provided templates** - they ensure consistency across the codebase
5. **Test everything** - no exceptions

**Most Important Sections:**
- [File Organization](#file-organization) - Where to put code
- [Naming Conventions](#naming-conventions) - How to name things
- [Code Organization Patterns](#code-organization-patterns) - Standard templates
- [Type Hints and Documentation](#type-hints-and-documentation) - Required docstring format
- [Discord Patterns](#discord-patterns) - Discord-specific conventions

---

## Table of Contents
1. [AI Agent Best Practices](#ai-agent-best-practices) ⭐ **START HERE**
2. [File Organization](#file-organization)
3. [Naming Conventions](#naming-conventions)
4. [Code Organization Patterns](#code-organization-patterns)
5. [Type Hints and Documentation](#type-hints-and-documentation)
6. [Error Handling](#error-handling)
7. [Discord Patterns](#discord-patterns)
8. [Testing Standards](#testing-standards)
9. [Git Commit Conventions](#git-commit-conventions)
10. [Code Style Guidelines](#code-style-guidelines)
11. [Configuration Files](#configuration-files)
12. [Deployment](#deployment)

---

## AI Agent Best Practices

**⭐ CRITICAL FOR AI AGENTS** - This section explains how to work effectively with this codebase.

### Understanding the Codebase

**Before making any changes:**

1. **Read the architecture docs** (30-45 minutes total):
   - [CODEBASE_CONTEXT.md](CODEBASE_CONTEXT.md) - Complete codebase map with file-by-file explanations
   - This file (CONVENTIONS.md) - Coding standards and patterns
   - [refactor_plan.md](../../refactor_plan.md) - If doing refactoring work

2. **Understand the domain**:
   - This is a **Warhammer Fantasy Roleplay (WFRP) 4th Edition** bot
   - Implements specific WFRP rules (d100 tests, Success Levels, doubles for crits/fumbles)
   - Domain knowledge is embedded in comments and docstrings - READ THEM

3. **Identify the subsystem** you're working in:
   - **Commands** (`/commands`) - Discord interaction layer
   - **Utils** (`/utils`) - Pure game mechanics
   - **Database** (`/db`) - Data persistence and lookup tables
   - **Weather** (`/commands/weather_modules`) - Complex multi-day weather system
   - Each subsystem has different patterns and responsibilities

### Making Changes Safely

**Step-by-step process for any code change:**

1. **Locate existing code**:
   ```bash
   # Find files by pattern
   grep -r "function_name" --include="*.py"

   # Find class definitions
   grep -r "class ClassName" --include="*.py"
   ```

2. **Read surrounding context**:
   - Don't just read the function - read the whole file
   - Understand the module's purpose (check docstring at top)
   - Look for related functions and how they interact
   - Check imports to understand dependencies

3. **Identify tests**:
   - Tests mirror source structure: `commands/roll.py` → `tests/commands/test_roll.py`
   - Read existing tests to understand expected behavior
   - Tests document the API contract - don't break them!

4. **Make minimal changes**:
   - Change ONLY what's necessary
   - Don't "improve" unrelated code (scope creep)
   - One logical change per commit

5. **Update tests immediately**:
   - Modify existing tests if behavior changed
   - Add new tests for new functionality
   - Run tests BEFORE moving to next task: `pytest tests/`

6. **Verify manually** (for Discord commands):
   - Bot commands need manual testing in Discord
   - Test both slash (`/command`) and prefix (`!command`) versions
   - Test error cases (invalid input, missing data, etc.)

### Common AI Agent Mistakes (Avoid These!)

**1. Ignoring Existing Patterns**
```python
# ❌ BAD - Inventing new patterns
def get_data(id):
    return data_store[id]

# ✅ GOOD - Following existing conventions
def get_character(character_key: str) -> Dict[str, Any]:
    """Get character data by key (follows existing pattern)."""
    if character_key not in CHARACTERS:
        raise ValueError(f"Character '{character_key}' not found")
    return CHARACTERS[character_key]
```

**2. Breaking Type Safety**
```python
# ❌ BAD - Returning anonymous dicts
def generate_weather():
    return {"temp": 15, "wind": "strong"}

# ✅ GOOD - Using dataclasses
@dataclass
class WeatherCondition:
    temperature: int
    wind_strength: str

def generate_weather() -> WeatherCondition:
    return WeatherCondition(temperature=15, wind_strength="strong")
```

**3. Mixing Concerns**
```python
# ❌ BAD - Discord code in business logic
def calculate_boat_penalty(wind: str) -> int:
    channel = discord.utils.get(guild.channels, name="log")
    penalty = WIND_PENALTIES[wind]
    await channel.send(f"Penalty: {penalty}")
    return penalty

# ✅ GOOD - Pure business logic
def calculate_boat_penalty(wind: str) -> int:
    """Calculate penalty from wind (pure function, no I/O)."""
    return WIND_PENALTIES.get(wind, 0)
```

**4. Not Testing**
```python
# ❌ BAD - Writing code without tests
def complex_weather_calculation(params):
    # 50 lines of complex logic
    # No tests = bugs waiting to happen
    pass

# ✅ GOOD - TDD approach
def test_weather_calculation_cold_front():
    """Test weather calculation during cold front."""
    result = calculate_weather(season="winter", event="cold_front")
    assert result.temperature < 0
    assert result.modifier == -10

def calculate_weather(season: str, event: str) -> WeatherResult:
    """Calculate weather (tested function)."""
    pass
```

**5. Hardcoding Values**
```python
# ❌ BAD - Magic numbers
def check_cold_front(roll):
    if roll == 2:  # What is 2? Why 2?
        return True

# ✅ GOOD - Named constants
COLD_FRONT_TRIGGER_ROLL = 2  # 1% chance on d100
COLD_FRONT_COOLDOWN_DAYS = 7

def check_cold_front(roll: int, cooldown_days: int) -> bool:
    """Check if cold front triggers (1% chance, 7-day cooldown)."""
    return roll == COLD_FRONT_TRIGGER_ROLL and cooldown_days >= COLD_FRONT_COOLDOWN_DAYS
```

### Understanding Discord Bot Patterns

**This bot uses a dual-command system:**
- **Slash commands** (`/roll 3d6`) - Modern Discord UI, uses `discord.Interaction`
- **Prefix commands** (`!roll 3d6`) - Legacy text-based, uses `discord.ext.commands.Context`

**Every command file follows this pattern:**
```python
def setup(bot: commands.Bot):
    """Entry point called by main.py."""

    @bot.tree.command(name="roll")  # Slash command
    async def roll_slash(interaction: discord.Interaction, dice: str):
        await _perform_roll(interaction, dice, is_slash=True)

    @bot.command(name="roll")  # Prefix command
    async def roll_prefix(ctx, dice: str):
        await _perform_roll(ctx, dice, is_slash=False)

    async def _perform_roll(context, dice: str, is_slash: bool):
        """Shared logic for both command types."""
        # Business logic here
        pass
```

**Why this matters:**
- Changes to ONE command must support BOTH interfaces
- The `is_slash` parameter controls response method:
  - Slash: `interaction.response.send_message()`
  - Prefix: `ctx.send()`
- Test both versions when making changes!

### Project-Specific Knowledge

**WFRP 4e Game Rules (critical for implementation):**
- **d100 Tests:** Roll ≤ (skill + modifier) to succeed
- **Success Levels (SL):** (target tens digit) - (roll tens digit)
  - Example: Roll 35 vs target 62 → SL = 6 - 3 = +3
- **Doubles:** Matching digits (11, 22, 33, etc.)
  - Doubles ≤ target = critical success
  - Doubles > target = fumble
- **Special cases:**
  - Roll of 1 treated as 01 (low double)
  - Roll of 100 always fumble (even if skill is 100+)

**Weather System Complexity:**
- Multi-day journeys with persistent state
- 4 time periods per day (dawn/midday/dusk/midnight)
- Special events (cold fronts 1-5 days, heat waves 11-20 days)
- 7-day cooldown between events
- Daily temperature variation during events
- Mutual exclusivity (only one event type at a time)
- See [CODEBASE_CONTEXT.md](CODEBASE_CONTEXT.md) Section 13 for details

**Database Architecture:**
- SQLite for journey persistence (`data/weather.db`)
- Python dicts for static game data (`db/character_data.py`, `db/weather_data.py`)
- Context managers for connections (prevents resource warnings)
- Migration-friendly schema (can add columns with defaults)

### Code Review Checklist

**Before submitting code, verify:**

- [ ] **Follows existing patterns** - Matches similar code in the codebase
- [ ] **Type hints** - All function signatures have type annotations
- [ ] **Docstrings** - Google-style with Args/Returns/Raises/Examples
- [ ] **Tests** - New code has tests, existing tests still pass
- [ ] **No Discord in business logic** - Services are pure Python
- [ ] **No magic numbers** - Constants have descriptive names
- [ ] **Error handling** - Try-except with appropriate error messages
- [ ] **Separation of concerns** - Code in correct layer (command/service/data)
- [ ] **Manual testing** - If Discord command, tested in actual Discord
- [ ] **No regressions** - Existing functionality still works
- [ ] **Commit message** - Follows conventions (feat/fix/refactor/test/docs)

### When You Get Stuck

**If you encounter issues:**

1. **Read the error message carefully** - It usually tells you exactly what's wrong
2. **Check existing similar code** - Find a working example and follow its pattern
3. **Review relevant documentation section**:
   - Unclear where code goes? → [File Organization](#file-organization)
   - Don't know naming convention? → [Naming Conventions](#naming-conventions)
   - Unsure about Discord patterns? → [Discord Patterns](#discord-patterns)
   - Need test examples? → [Testing Standards](#testing-standards)
4. **Check CODEBASE_CONTEXT.md** - Has detailed explanations of every module
5. **Look at git history** - `git log --follow <file>` shows evolution and rationale
6. **Try multiple approaches** - Spend 10-15 minutes debugging before asking
7. **Document and move on** - If blocked, document the issue and continue with other tasks
8. **Ask for clarification ONLY if** - You've exhausted all options and it's blocking critical work

### Autonomous Operation Guidelines

**The user expects minimal interaction. Work independently by:**

1. **Making reasonable decisions** - Use your judgment when documentation provides guidance
2. **Following existing patterns** - When in doubt, copy what's already working
3. **Testing frequently** - Catch issues early with `pytest tests/`
4. **Using todo lists** - Keep the user informed via TodoWrite tool
5. **Documenting assumptions** - Leave comments explaining your choices
6. **Maintaining momentum** - Complete full sections without pausing

**Decision-making framework:**
```
Can I find an example in the codebase?
  → YES: Copy that pattern
  → NO: Check documentation

Is it in documentation?
  → YES: Follow documented approach
  → NO: Is there a clear "best practice"?

Is it a minor implementation detail?
  → YES: Make reasonable choice, document in comment
  → NO: Is it blocking critical work?

Will my choice break existing functionality?
  → NO: Proceed, test thoroughly
  → YES: Try alternative approach or document as blocker
```

**You should proceed without asking about:**
- Variable/function/class names (follow naming conventions)
- Code organization within files
- Which test cases to write
- Error message wording
- Helper function structure
- Import organization
- Comment placement
- Formatting choices

**Only ask if:**
- Fundamental architectural decision with no documentation guidance
- Breaking change that affects external APIs/users
- Critical information is missing from all documentation
- Multiple valid approaches with significant trade-offs

---

## File Organization

### Directory Structure
```
travelling-bot/
├── commands/                          # Command modules
│   ├── {feature}.py                   # Command implementation files
│   ├── weather_modules/               # Weather subsystem
│   │   ├── handler.py                 # Business logic
│   │   ├── display.py                 # Discord embed formatting
│   │   ├── stages.py                  # Stage generation
│   │   ├── notifications.py           # Log channel messages
│   │   ├── formatters.py              # Formatting utilities
│   │   └── __init__.py                # Module exports
│   ├── weather_original.py            # [Deprecated] Legacy weather implementation
│   └── __init__.py                    # Package initialization
├── db/                                # Database and data tables
│   ├── {feature}_data.py              # Static data/lookup tables
│   ├── {feature}_storage.py           # Database persistence
│   └── __init__.py                    # Package initialization
├── utils/                             # Utilities and mechanics
│   ├── {feature}_mechanics.py         # Core game mechanics
│   └── __init__.py                    # Package initialization
├── tests/                             # Test suite (when active)
│   ├── test_{module}.py               # Test files
│   └── conftest.py                    # Pytest fixtures
├── data/                              # Persistent storage
│   └── weather.db                     # SQLite database
├── context/                           # AI Agent Documentation
│   ├── CODEBASE_CONTEXT.md            # Comprehensive codebase map
│   ├── CONVENTIONS.md                 # This file - coding standards
│   ├── TDD_Guidelines.md              # Universal TDD principles
│   └── TDD_GUIDELINES_CODEBASE_SPECIFIC.md  # Project-specific TDD
├── docs/                              # User-facing documentation
│   ├── COMMANDS_DOCUMENTATION.md      # User command guide
│   ├── DEPLOYMENT_GUIDE.md            # Render deployment
│   └── DEPLOYMENT_GUIDE_FLASK.md      # Flask keep-alive setup
├── archives/                          # Historical planning documents
│   ├── longer_weather_plan.md         # Weather implementation plan
│   ├── PHASE_3_4_TEST_SUMMARY.md      # Test phase summaries
│   ├── README_TESTING.md              # Testing documentation
│   ├── TDD_QUICK_REFERENCE.md         # Quick TDD reference
│   ├── TEST_GUIDE.md                  # Testing strategies
│   ├── test_instructions.md           # Test instructions
│   └── WEATHER_REFACTORING_PLAN.md    # Weather refactoring plan
├── tasks/                             # Future planning documents
│   └── OPENAI_NARRATIVE_IMPLEMENTATION_PLAN.md
├── htmlcov/                           # Coverage HTML reports
├── __pycache__/                       # Python bytecode cache
├── .pytest_cache/                     # Pytest cache
├── .git/                              # Git repository
├── main.py                            # Bot entry point
├── server.py                          # Flask keep-alive server
├── requirements.txt                   # Python dependencies
├── render.yaml                        # Render.com deployment config
├── .env                               # Environment variables (not in git)
├── .gitignore                         # Git ignore patterns
├── .coveragerc                        # Coverage configuration
├── run_coverage.sh                    # Coverage test runner script
├── bot.log                            # Bot runtime logs
└── discord.log                        # Discord API logs
```

### File Naming Conventions
- **Commands:** `{feature}.py` (e.g., `roll.py`, `boat_handling.py`, `river_encounter.py`)
- **Utils:** `{purpose}_mechanics.py` (e.g., `weather_mechanics.py`, `wfrp_mechanics.py`)
- **Database:** `{feature}_data.py` or `{feature}_storage.py`
- **Tests:** `test_{module}.py` (e.g., `test_weather_storage_schema.py`)
- **Modules:** Use underscores for multi-word files (e.g., `boat_handling.py`)
- **Documentation:** `UPPER_CASE.md` for important docs (e.g., `CONVENTIONS.md`, `CODEBASE_CONTEXT.md`)
- **Scripts:** `.sh` extension for bash scripts (e.g., `run_coverage.sh`)

### Module Organization
- **Commands** are in `/commands/` and define Discord command interfaces
- **Business logic** goes in `/utils/` or `/commands/{feature}_modules/`
- **Data tables** go in `/db/{feature}_data.py`
- **Persistence** goes in `/db/{feature}_storage.py`
- **Tests** mirror the structure they test (when active)
- **Documentation** splits into:
  - `/context/` - AI agent documentation (architecture, conventions, TDD)
  - `/docs/` - User-facing documentation (commands, deployment)
  - `/archives/` - Historical plans and test summaries
  - `/tasks/` - Future implementation plans

### Package Initialization (`__init__.py`)
All Python packages should have an `__init__.py` file with:
- Module docstring explaining package purpose
- Optional imports for convenience
- Optional `__all__` list for explicit exports

```python
"""
Package docstring explaining purpose.
"""

# Optional convenience imports
from .module import ClassName

# Optional explicit exports
__all__ = ["ClassName", "function_name"]
```

---

## Naming Conventions

### Python Code

#### Classes: `PascalCase`
```python
class WeatherCommandHandler:
    pass

class WeatherStorage:
    pass

class StageDisplayManager:
    pass

class NotificationManager:
    pass
```

#### Functions: `snake_case`
```python
def generate_daily_weather():
    pass

def get_active_weather_modifiers():
    pass

def roll_temperature_with_special_events():
    pass

def format_weather_embed():
    pass
```

#### Constants: `UPPER_SNAKE_CASE`
```python
COLD_FRONT_TRIGGER_ROLL = 2
HEAT_WAVE_TRIGGER_ROLL = 99
COLD_FRONT_COOLDOWN_DAYS = 7
WIND_STRENGTH = {...}
PROVINCE_TEMPERATURES = {...}
```

#### Private/Internal Functions: `_leading_underscore`
```python
def _perform_boat_handling():
    """Internal logic shared by slash and prefix commands."""
    pass

def _parse_speed_modifier():
    """Internal helper for modifier parsing."""
    pass

def _create_notification_embed():
    """Internal method for notification formatting."""
    pass

def _update_cooldown_trackers():
    """Internal helper for cooldown state management."""
    pass
```

#### Variables: `snake_case`
```python
weather_data = {...}
guild_id = "123456789"
cold_front_days = 3
time_of_day = "midday"
```

### Discord Commands

#### Slash Commands: `kebab-case`
```python
@bot.tree.command(name="boat-handling", description="...")
@bot.tree.command(name="river-encounter", description="...")
@bot.tree.command(name="weather-stage-config", description="...")
```

#### Command Parameters: `snake_case`
```python
@app_commands.describe(
    time_of_day="Time of day affecting wind conditions",
    stage_duration="Number of days in the stage",
    cold_front_days="Days remaining in cold front"
)
```

### Database

#### Tables: `snake_case`
```sql
CREATE TABLE guild_weather_state (...)
CREATE TABLE daily_weather (...)
```

#### Columns: `snake_case`
```sql
guild_id TEXT PRIMARY KEY
current_day INTEGER
days_since_last_cold_front INTEGER
cold_front_total_duration INTEGER
```

---

## Code Organization Patterns

### Command Structure

Every command file follows this standard pattern:

```python
"""
Command: {command-name}
Description: Brief description of command purpose
"""

import discord
from discord import app_commands
from discord.ext import commands

# Imports from project modules
from utils.{module} import ...
from db.{module} import ...


def setup(bot: commands.Bot):
    """
    Register command with the bot.
    Called from main.py during bot initialization.
    
    This is the entry point for the command module.
    main.py calls setup_command_name(bot) which calls this function.
    """

    # 1. Slash Command Handler (thin wrapper)
    @bot.tree.command(name="{command-name}", description="...")
    @app_commands.describe(
        param1="Parameter description",
        param2="Parameter description"
    )
    async def {command}_slash(
        interaction: discord.Interaction,
        param1: str,
        param2: int = 0
    ):
        """Brief docstring for slash command."""
        await _perform_{command}(interaction, param1, param2, is_slash=True)

    # 2. Prefix Command Handler (thin wrapper)
    @bot.command(name="{command-name}")
    async def {command}_prefix(ctx, param1: str, param2: int = 0):
        """Brief docstring for prefix command."""
        await _perform_{command}(ctx, param1, param2, is_slash=False)

    # 3. Shared Business Logic
    async def _perform_{command}(
        context, param1: str, param2: int, is_slash: bool
    ):
        """
        Shared logic for both slash and prefix commands.
        
        Args:
            context: Discord context (interaction or ctx)
            param1: Description
            param2: Description
            is_slash: Whether this is a slash command
        """
        try:
            # Business logic here
            
            # Create embed
            embed = _create_embed(data)
            
            # Send response
            await _send_response(context, embed, is_slash)
            
            # Log command
            await _log_command(context, ...)
            
        except Exception as e:
            # Error handling
            await _send_error(context, str(e), is_slash)

    # 4. Helper Functions
    def _create_embed(data) -> discord.Embed:
        """Create Discord embed for display."""
        pass

    async def _send_response(context, embed, is_slash):
        """Send response handling slash vs prefix differences."""
        if is_slash:
            await context.response.send_message(embed=embed)
        else:
            await context.send(embed=embed)

    async def _log_command(context, action, details):
        """Log command to boat-travelling-log channel."""
        pass
```

### Main Entry Point (`main.py`)

The bot entry point follows this pattern:

```python
"""
Main entry point for WFRP Traveling Bot.
Initializes Discord bot and registers all commands.
"""

import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Import command setup functions
from commands.roll import setup as setup_roll
from commands.boat_handling import setup as setup_boat_handling
from commands.weather import setup as setup_weather
from commands.river_encounter import setup as setup_river_encounter
from commands.help import setup as setup_help

# Load environment variables
load_dotenv()

# Configure bot with intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Register all commands
setup_roll(bot)
setup_boat_handling(bot)
setup_weather(bot)
setup_river_encounter(bot)
setup_help(bot)

@bot.event
async def on_ready():
    """Called when bot successfully connects to Discord."""
    print(f"Logged in as {bot.user}")
    await bot.tree.sync()  # Sync slash commands
    print("Commands synced!")

# Start keep-alive server for Render
from server import keep_alive
keep_alive()

# Run bot
bot.run(os.getenv('DISCORD_TOKEN'))
```

**Conventions:**
- Import all command setup functions at top
- Register commands before `bot.run()`
- Call `bot.tree.sync()` in `on_ready()` to register slash commands
- Start keep-alive server before running bot
- Use descriptive print statements for startup feedback

### Class Structure

For classes with static methods (managers, utilities):

```python
class FeatureManager:
    """
    Brief description of class purpose.
    
    This class is responsible for:
    - Responsibility 1
    - Responsibility 2
    - Responsibility 3
    """
    
    # Class constants
    COLOR_DEFAULT = 0x3498DB
    COLOR_ERROR = 0xE74C3C
    
    @staticmethod
    def public_method(param: str) -> str:
        """Public API method with full docstring."""
        pass
    
    @staticmethod
    def _internal_method(param: str) -> str:
        """Internal helper method."""
        pass
```

For classes with instance state (storage, handlers):

```python
class FeatureHandler:
    """Brief description of class purpose."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize handler with configuration.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.storage = FeatureStorage()
    
    def public_method(self, param: str) -> Dict:
        """Public API method."""
        pass
    
    def _internal_method(self, param: str) -> Dict:
        """Internal helper method."""
        pass
```

---

## Type Hints and Documentation

### Type Hints

Use type hints for all function signatures:

```python
from typing import Optional, Dict, List, Tuple, Any

def handle_cold_front(
    roll: int,
    current_days: int,
    total_duration: int,
    cooldown_days: int,
    heat_wave_active: bool = False
) -> Tuple[int, int, int]:
    """
    Handle cold front event logic.
    
    Args:
        roll: D100 roll result
        current_days: Days remaining in current event
        total_duration: Original rolled duration
        cooldown_days: Days since last cold front
        heat_wave_active: Whether heat wave is active
        
    Returns:
        Tuple of (modifier, remaining_days, total_duration)
    """
    pass
```

### Docstring Format: Google Style

```python
def function_name(param1: str, param2: int = 0) -> Dict[str, Any]:
    """
    Brief one-line summary of function purpose.
    
    Longer description providing context, usage notes, or important
    details about the function's behavior. Can span multiple lines.
    
    Args:
        param1: Description of param1
        param2: Description of param2 (default: 0)
        
    Returns:
        Dictionary containing:
            - key1: Description of key1
            - key2: Description of key2
            
    Raises:
        ValueError: When param1 is invalid
        KeyError: When required data is missing
        
    Examples:
        >>> result = function_name("test", 5)
        >>> print(result["key1"])
        "value1"
    """
    pass
```

### Comments

- **Explain WHY, not WHAT:** Code should be self-documenting for what it does
- **Use comments for complex logic:** Explain non-obvious algorithms or business rules
- **Document WFRP rules:** Reference rulebook sections when implementing game mechanics

```python
# Good: Explains WHY
# WFRP Rule: Roll of 1 is treated as low double (01) for doubles detection
if roll_result == 1:
    roll_result = 1  # Treat as 01

# Bad: Explains WHAT (obvious from code)
# Set roll result to 1
if roll_result == 1:
    roll_result = 1
```

### Inline Documentation for Complex Logic

```python
def roll_temperature_with_special_events(...):
    """Handle temperature with special events."""
    
    # Extract previous event state
    # This is needed because events span multiple days and we need to
    # determine if we're continuing an existing event or potentially
    # starting a new one
    cold_front_remaining = cold_front_days
    
    # Check if we should trigger a new cold front
    # WFRP Rule: Roll = 2 triggers cold front (1% chance)
    # Suppressed during active events to prevent nesting bug
    if roll == COLD_FRONT_TRIGGER_ROLL and cold_front_days == 0:
        # Check cooldown period (7 days minimum between events)
        if days_since_last_cold_front >= COLD_FRONT_COOLDOWN_DAYS:
            # Mutual exclusivity: Cannot start if heat wave active
            if heat_wave_days == 0:
                # Trigger new cold front
                ...
```

---

## Error Handling

### Try-Except in Command Handlers

All command handlers should wrap logic in try-except:

```python
async def _perform_command(context, params, is_slash: bool):
    """Shared command logic."""
    try:
        # Main logic here
        result = perform_operation(params)
        
        # Success response
        embed = create_success_embed(result)
        await send_response(context, embed, is_slash)
        
    except ValueError as e:
        # User input errors (show to user)
        await send_error(context, str(e), is_slash)
        
    except KeyError as e:
        # Data lookup errors
        await send_error(context, f"Data not found: {e}", is_slash)
        
    except Exception as e:
        # Unexpected errors (log but don't expose details)
        print(f"Error in {command}: {e}")
        await send_error(
            context,
            "An unexpected error occurred. Please try again.",
            is_slash
        )
```

### Error Embeds

```python
def create_error_embed(message: str) -> discord.Embed:
    """
    Create standardized error embed.
    
    Args:
        message: User-friendly error message
        
    Returns:
        Discord embed with error styling
    """
    embed = discord.Embed(
        title="❌ Error",
        description=message,
        color=0xE74C3C  # Red
    )
    return embed
```

### Validation

Validate inputs early and provide helpful error messages:

```python
def get_character(character_key: str) -> Dict[str, Any]:
    """Get character data by key."""
    character_key = character_key.lower().strip()
    
    if character_key not in characters_data:
        available = ", ".join(get_available_characters())
        raise ValueError(
            f"Character '{character_key}' not found. "
            f"Available characters: {available}"
        )
    
    return characters_data[character_key]
```

---

## Discord Patterns

### Embed Colors

Use consistent colors across the bot:

```python
# Standard colors
COLOR_DEFAULT = 0x3498DB    # Blue - default/info
COLOR_SUCCESS = 0x2ECC71    # Green - success states
COLOR_ERROR = 0xE74C3C      # Red - errors
COLOR_WARNING = 0xF39C12    # Orange - warnings
COLOR_INFO = 0x95A5A6       # Gray - neutral info

# Using discord.Color enum
discord.Color.blue()        # 0x3498DB
discord.Color.green()       # 0x2ECC71
discord.Color.red()         # 0xE74C3C
discord.Color.orange()      # 0xF39C12
discord.Color.gold()        # 0xFFD700 - exceptional success
```

### Embed Structure

```python
embed = discord.Embed(
    title="🎲 Title with Emoji",
    description="Brief description of content",
    color=COLOR_DEFAULT
)

# Add fields for structured data
embed.add_field(
    name="Field Name",
    value="Field content",
    inline=True  # or False for full-width
)

# Add footer for metadata
embed.set_footer(text="Additional info or instructions")

# Add timestamp for time-sensitive data
from datetime import datetime, timezone
embed.timestamp = datetime.now(timezone.utc)
```

### Channel Names (Hardcoded)

The bot expects these specific channel names:

```python
# Log channel for command history (user-visible)
LOG_CHANNEL_NAME = "boat-travelling-log"

# GM notifications channel (GM-only details)
GM_CHANNEL_NAME = "boat-travelling-notifications"
```

### Permission Checks

```python
def is_gm(user: discord.Member) -> bool:
    """
    Check if user has GM permissions.
    
    Args:
        user: Discord member to check
        
    Returns:
        True if user is server owner or has "GM" role
    """
    # Server owner always has GM permissions
    if user.guild.owner_id == user.id:
        return True
    
    # Check for GM role
    gm_role = discord.utils.get(user.guild.roles, name="GM")
    if gm_role and gm_role in user.roles:
        return True
    
    return False
```

### Response Handling (Slash vs Prefix)

```python
async def send_response(
    context,
    embed: discord.Embed,
    is_slash: bool,
    ephemeral: bool = False
):
    """
    Send response handling slash/prefix command differences.
    
    Args:
        context: Discord context (interaction or ctx)
        embed: Embed to send
        is_slash: Whether this is a slash command
        ephemeral: Whether message should be ephemeral (slash only)
    """
    if is_slash:
        # Slash commands use interaction.response
        await context.response.send_message(
            embed=embed,
            ephemeral=ephemeral
        )
    else:
        # Prefix commands use ctx.send
        await context.send(embed=embed)
```

---

## Testing Standards

### Test File Organization

```
tests/
├── conftest.py                          # Shared fixtures
├── test_weather_storage_schema.py       # Phase 1: Database tests
├── test_weather_mechanics_events.py     # Phase 2: Mechanics tests
├── test_handler_integration.py          # Phase 3: Integration tests
└── test_display_formatting.py           # Phase 4: Display tests
```

**Note:** Tests directory may be empty between development cycles. Tests are typically:
1. Created during TDD implementation phases
2. Run to verify functionality (88 tests passing)
3. May be archived after successful completion
4. Recreated when adding new features

**Test Phase Organization:**
- **Phase 1:** Database schema and storage layer
- **Phase 2:** Core mechanics and business logic
- **Phase 3:** Integration between components
- **Phase 4:** Display formatting and user-facing output

### Test Naming Convention

```python
def test_{feature}_{specific_behavior}_{conditions}():
    """Test description following Given-When-Then format."""
    pass

# Examples:
def test_cold_front_triggers_on_roll_2_when_cooldown_expired():
    """GIVEN: No active events and cooldown expired
       WHEN: Roll = 2
       THEN: Cold front triggers with duration 1-5 days"""
    pass

def test_cooldown_increments_when_no_event_active():
    """GIVEN: No active events
       WHEN: Day advances
       THEN: Cooldown counter increments by 1"""
    pass
```

### Test Structure: Arrange-Act-Assert

```python
def test_feature():
    """
    GIVEN: Initial conditions
    WHEN: Action occurs
    THEN: Expected outcome
    """
    # Arrange - Set up test data and mocks
    storage = WeatherStorage(":memory:")
    guild_id = "test_guild_123"
    
    with patch('random.randint', return_value=3):
        # Act - Perform the action being tested
        result = function_under_test(guild_id)
    
    # Assert - Verify expected outcome
    assert result["cold_front_days"] == 3
    assert result["cold_front_total"] == 3
```

### Fixtures (conftest.py)

```python
@pytest.fixture
def initialized_db():
    """Database with tables already created."""
    import tempfile
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    temp_path = temp_file.name
    temp_file.close()
    
    storage = WeatherStorage(temp_path)
    yield storage
    
    os.unlink(temp_path)

@pytest.fixture
def sample_weather_data():
    """Sample weather data for testing."""
    return {
        "day": 5,
        "season": "summer",
        "province": "reikland",
        "temperature": 21,
        "cold_front_days_remaining": 0,
        "cold_front_total_duration": 0
    }
```

### Mock Usage

```python
from unittest.mock import patch, Mock

def test_with_controlled_randomness():
    """Test with mocked random values for deterministic results."""
    with patch('random.randint', return_value=2):
        # Now all random.randint() calls return 2
        result = roll_for_cold_front()
        assert result["event_triggered"] is True
```

---

## Git Commit Conventions

### Commit Message Format

```
{type}: {description}

{optional body}

{optional footer}
```

### Commit Types

- **feat:** New feature
- **fix:** Bug fix
- **test:** Adding or updating tests
- **refactor:** Code refactoring (no functional changes)
- **docs:** Documentation changes
- **chore:** Maintenance tasks (dependencies, configs)
- **style:** Code style changes (formatting, no logic changes)
- **perf:** Performance improvements

### Examples

```bash
# Feature additions
feat: add heat wave special event with 11-20 day duration
feat: implement day counter display in stage summaries
feat: add emigrating birds flavor text on cold front day 1

# Bug fixes
fix: correct wind change probability from 15% to 10%
fix: prevent nested cold fronts during active event (nesting bug)
fix: cooldown counter now resets when new event starts

# Tests
test: add boat handling integration tests
test: add Phase 4 display formatting tests (19 tests)
test: verify cooldown state machine transitions

# Refactoring
refactor: extract weather display logic to separate module
refactor: move formatters to dedicated utility class
refactor: simplify cooldown tracking with state machine

# Documentation
docs: update CODEBASE_CONTEXT with weather event changes
docs: add comprehensive explanations for all files
docs: create CONVENTIONS.md for coding standards

# Chores
chore: update dependencies to latest versions
chore: add .coveragerc for test coverage configuration
chore: clean up deprecated weather_original.py file
```

### Commit Body Guidelines

Use the body for:
- Explaining WHY the change was made
- Providing context for complex changes
- Listing related changes
- Referencing issues or planning documents

```bash
feat: implement daily temperature variation during events

Cold fronts and heat waves now have daily temperature variation (±5°C)
based on the d100 roll category. This makes events feel more realistic
and dynamic rather than having static temperatures for 1-20 days.

Changes:
- Add daily roll during active events
- Suppress special rolls (2, 99) to prevent nesting
- Recalculate category from actual temperature
- Update display to show varied temperatures

Refs: longer_weather_plan.md, Phase 2 implementation
```

---

## Code Style Guidelines

### Legacy and Deprecated Code

**Deprecated Files:**
- `commands/weather_original.py` - Original monolithic weather implementation
  - **Status:** Deprecated but kept for reference
  - **Reason:** Refactored into modular `weather_modules/` structure
  - **Action:** Do NOT modify. Use `weather_modules/` instead

**Handling Deprecated Code:**
```python
# Mark deprecated functions/classes with warnings
import warnings

@deprecated
def old_function():
    """
    DEPRECATED: Use new_function() instead.
    
    This function will be removed in version 2.0.
    """
    warnings.warn(
        "old_function is deprecated, use new_function instead",
        DeprecationWarning,
        stacklevel=2
    )
    # Implementation...
```

**Conventions:**
- Keep deprecated files for 1-2 release cycles
- Document deprecation in docstring and comments
- Provide migration path to new implementation
- Eventually remove after sufficient transition period

### Python Style

Follow PEP 8 with project-specific conventions:

```python
# Line length: 88 characters (Black formatter default)
# Indentation: 4 spaces (no tabs)

# Imports: Organize in order
import os                           # 1. Standard library
import sys
from datetime import datetime

import discord                      # 2. Third-party packages
from discord.ext import commands

from utils.wfrp_mechanics import   # 3. Local imports
from db.character_data import

# Blank lines: 2 before top-level classes/functions
def function_one():
    pass


def function_two():
    pass


class MyClass:
    pass
```

### String Formatting

Use f-strings for readability:

```python
# Preferred
message = f"Character {name} rolled {roll} vs target {target}"
description = f"Day {day_num}/{total_days} (Final Day)"

# Avoid (unless necessary for backwards compatibility)
message = "Character {} rolled {} vs target {}".format(name, roll, target)
message = "Character %s rolled %d vs target %d" % (name, roll, target)
```

### List/Dict Comprehensions

Use comprehensions for simple transformations:

```python
# Good
available_chars = [char["name"] for char in characters.values()]
weather_dict = {day: generate_weather(day) for day in range(1, 8)}

# Avoid for complex logic (use loops instead)
# Bad - too complex for comprehension
results = [
    process_complex_data(item, config)
    if validate_item(item) and check_conditions(item)
    else default_value
    for item in items
    if item is not None
]

# Better - use regular loop
results = []
for item in items:
    if item is None:
        continue
    if validate_item(item) and check_conditions(item):
        results.append(process_complex_data(item, config))
    else:
        results.append(default_value)
```

### Boolean Expressions

```python
# Explicit comparisons for clarity
if count == 0:
    pass

# Implicit for None, empty containers
if weather_data:  # not None and not empty
    pass

if character is None:
    pass
```

### Context Managers

Use context managers for resources:

```python
# Database connections
with self._get_connection() as conn:
    cursor = conn.cursor()
    # Work with connection
    # Automatic commit/rollback and close

# File operations
with open("data.json", "r") as f:
    data = json.load(f)
    # File automatically closed
```

---

## Configuration Files

### Python Dependencies (`requirements.txt`)

List all Python packages with no version pinning (allows flexible updates):

```txt
discord.py
python-dotenv
flask
pytest
coverage
pytest-cov
```

**Conventions:**
- One package per line
- No version constraints unless specifically needed
- Keep list alphabetical for readability
- Separate into sections with comments if needed:
  ```txt
  # Core dependencies
  discord.py
  python-dotenv
  
  # Web server
  flask
  
  # Testing
  pytest
  coverage
  pytest-cov
  ```

### Logging

**Log Files:**
- `bot.log` - General bot activity and errors
- `discord.log` - Discord API interactions (detailed)

**Usage in Code:**
```python
import logging

# Simple print for debugging during development
print(f"Debug: {variable}")

# For production logging (if logging is configured)
logging.info("Bot command executed")
logging.error(f"Error occurred: {e}")
```

**Conventions:**
- Use `print()` for simple debugging during development
- Log files are in `.gitignore` (not committed)
- Both log files generated automatically by Discord.py and bot code
- Check logs when debugging deployment issues

### Environment Variables (`.env`)

**Never commit to git!** Listed in `.gitignore`.

```bash
# Discord bot token
DISCORD_TOKEN=your_bot_token_here

# Optional: Port for Flask server (default: 8080)
PORT=8080
```

**Conventions:**
- UPPER_SNAKE_CASE for variable names
- Comments explain each variable
- Template file can be committed as `.env.example`

### Git Ignore (`.gitignore`)

Exclude generated files and secrets:

```gitignore
# Secrets
.env

# Logs
discord.log
bot.log
*.log

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python

# Testing
.pytest_cache/
.coverage
.coverage.*
htmlcov/
coverage.xml
*.cover

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Database (if needed)
# data/*.db
```

**Rationale for exclusions:**
- **Secrets:** `.env` contains API tokens
- **Logs:** Generated at runtime, can be large
- **Python bytecode:** `__pycache__/` is regenerated automatically
- **Testing artifacts:** Coverage reports and cache files
- **IDE files:** Editor-specific configurations
- **Database:** Can include if using as seed data, exclude if user-generated

### Coverage Configuration (`.coveragerc`)

Configure pytest-cov behavior:

```ini
[run]
source = .
omit = 
    */tests/*
    */test_*.py
    */__pycache__/*
    */.venv/*
    */venv/*
    setup.py
    */site-packages/*
    */docs/*
    */tasks/*
    */context/*
    
    # Exclude Discord command infrastructure
    commands/*
    main.py

[report]
exclude_lines =
    # Have to re-enable the standard pragma
    pragma: no cover
    
    # Don't complain about missing debug-only code:
    def __repr__
    
    # Don't complain if tests don't hit defensive assertion code:
    raise AssertionError
    raise NotImplementedError
    
    # Don't complain if non-runnable code isn't run:
    if __name__ == .__main__.:
    if TYPE_CHECKING:
    
    # Don't complain about abstract methods
    @abstractmethod

[html]
directory = htmlcov
```

**Key Sections:**
- `[run]` - What to include/exclude from coverage
- `[report]` - Lines to exclude from coverage reports
- `[html]` - HTML report configuration

**Rationale:**
- Exclude Discord command handlers (thin wrappers, hard to test in isolation)
- Focus coverage on core mechanics and business logic
- Exclude boilerplate code (repr, abstract methods, if __name__ == __main__)

### Test Runner Script (`run_coverage.sh`)

Bash script for running tests with coverage:

```bash
#!/bin/bash
# Run tests with coverage and open HTML report

echo "Running tests with coverage (excluding Discord infrastructure)..."
pytest --cov=. --cov-report=term-missing --cov-report=html

echo ""
echo "Coverage report generated in htmlcov/index.html"
echo "To view the report, open htmlcov/index.html in your browser"
echo ""
echo "Quick summary:"
coverage report --skip-covered
```

**Usage:**
```bash
bash run_coverage.sh
```

**Conventions:**
- Shebang at top: `#!/bin/bash`
- Echo messages for user feedback
- Generate both terminal and HTML reports
- Skip covered files in summary for clarity

---

## Deployment

### Render.com Configuration (`render.yaml`)

Infrastructure-as-code for Render deployment:

```yaml
services:
  - type: web
    name: wfrp-traveling-bot
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python main.py
    envVars:
      - key: DISCORD_TOKEN
        sync: false
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: PORT
        value: 8080
```

**Key Fields:**
- `type: web` - Web service (keeps bot alive via HTTP endpoint)
- `buildCommand` - Install dependencies
- `startCommand` - Run bot
- `envVars` - Environment variables (sync: false = set in dashboard)

**Conventions:**
- Use Python 3.11+ for modern features
- Keep secrets out of yaml (`sync: false`)
- Default PORT to 8080 for Flask keep-alive server

### Keep-Alive Server (`server.py`)

Flask server to prevent Render free tier from spinning down:

```python
"""
Flask web server to keep the bot alive on Render's free tier.
This allows external services to ping the bot and prevent it from spinning down.
"""

from flask import Flask
from threading import Thread
import os

app = Flask(__name__)


@app.route('/')
def home():
    """Health check endpoint."""
    return "WFRP Traveling Bot is alive! 🚢"


@app.route('/health')
def health():
    """Health check endpoint for monitoring services."""
    return {"status": "healthy", "bot": "WFRP Traveling Bot"}


def run():
    """Run the Flask server."""
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)


def keep_alive():
    """Start the Flask server in a separate thread."""
    server = Thread(target=run)
    server.daemon = True
    server.start()
```

**Usage in `main.py`:**
```python
from server import keep_alive

# Start keep-alive server before bot
keep_alive()

# Run Discord bot
bot.run(os.getenv('DISCORD_TOKEN'))
```

**Conventions:**
- Two endpoints: `/` (user-friendly) and `/health` (machine-readable)
- Run in daemon thread to not block bot
- Port from environment variable with default
- Start before bot.run() in main.py

### Deployment Checklist

**Before deploying:**
1. ✅ Set `DISCORD_TOKEN` in Render dashboard
2. ✅ Verify `render.yaml` has correct service name
3. ✅ Test locally with `.env` file
4. ✅ Ensure `requirements.txt` is up to date
5. ✅ Verify database migrations in `weather_storage.py`
6. ✅ Check logs with `print()` statements or `logging`

**After deploying:**
1. ✅ Check Render logs for errors
2. ✅ Test `/health` endpoint (should return 200)
3. ✅ Test bot commands in Discord
4. ✅ Monitor for 24 hours to ensure stability

---

## Quick Reference

### Common Patterns

**Command Setup:**
```python
def setup(bot: commands.Bot):
    @bot.tree.command(name="command-name", description="...")
    async def command_slash(interaction, param: str):
        await _perform_command(interaction, param, is_slash=True)
```

**Main.py Registration:**
```python
from commands.feature import setup as setup_feature
setup_feature(bot)
```

**Package Init:**
```python
"""Package docstring."""
from .module import ClassName
__all__ = ["ClassName"]
```

**Error Handling:**
```python
try:
    result = operation()
except ValueError as e:
    await send_error(context, str(e), is_slash)
```

**Type Hints:**
```python
def function(param: str) -> Dict[str, Any]:
    pass
```

**Tests:**
```python
def test_feature_behavior_condition():
    # Arrange
    setup_data()
    # Act
    result = function()
    # Assert
    assert result == expected
```

**Commit:**
```bash
git commit -m "feat: add new feature"
git commit -m "fix: correct bug in module"
git commit -m "test: add integration tests"
git commit -m "docs: update CONVENTIONS.md"
```

**Run Tests with Coverage:**
```bash
bash run_coverage.sh
# or
pytest --cov=. --cov-report=html
```

**Deploy to Render:**
1. Push to git repository
2. Set DISCORD_TOKEN in Render dashboard
3. Render auto-deploys on push
4. Check `/health` endpoint

**File Organization:**
- Commands: `/commands/{feature}.py`
- Utilities: `/utils/{feature}_mechanics.py`
- Database: `/db/{feature}_storage.py`
- Data tables: `/db/{feature}_data.py`
- Tests: `/tests/test_{module}.py` (when active)
- Docs (AI): `/context/*.md`
- Docs (User): `/docs/*.md`
- Docs (Archive): `/archives/*.md`

---

## Related Documentation

### AI Agent Documentation (`/context/`)
- **CODEBASE_CONTEXT.md** - Comprehensive codebase structure and file purposes
- **CONVENTIONS.md** - This file - coding standards and project conventions
- **TDD_Guidelines.md** - Universal TDD principles for all projects
- **TDD_GUIDELINES_CODEBASE_SPECIFIC.md** - Project-specific TDD patterns

### User-Facing Documentation (`/docs/`)
- **COMMANDS_DOCUMENTATION.md** - Complete user guide for all bot commands
- **DEPLOYMENT_GUIDE.md** - Render.com deployment instructions
- **DEPLOYMENT_GUIDE_FLASK.md** - Flask keep-alive server setup guide

### Historical Documentation (`/archives/`)
- **longer_weather_plan.md** - Original weather system implementation plan (4 phases)
- **PHASE_3_4_TEST_SUMMARY.md** - Test results from Phase 3 and 4
- **README_TESTING.md** - Testing documentation and strategies
- **TEST_GUIDE.md** - Detailed testing patterns (88 tests across 4 phases)
- **TDD_QUICK_REFERENCE.md** - Quick reference for TDD workflow
- **test_instructions.md** - Test implementation instructions
- **WEATHER_REFACTORING_PLAN.md** - Weather module refactoring plan

### Future Planning (`/tasks/`)
- **OPENAI_NARRATIVE_IMPLEMENTATION_PLAN.md** - Planned OpenAI integration for narrative generation

---

**Last Updated:** October 30, 2025  
**Version:** 1.1.0  
**Maintainer:** Project Team
