# TDD Guidelines - Travelling Bot Codebase Specific

## Document Purpose
This document provides **codebase-specific** Test-Driven Development guidelines for the WFRP Travelling Bot. It should be used alongside the general `TDD_Guidelines.md` for context on TDD principles.

**What this document covers:**
- File-by-file testing patterns and use cases
- How components connect and integration points
- Specific pitfalls for this codebase
- Concrete examples from existing tests
- Testing strategies per module type

**How to use this document:**
1. Read general TDD principles from `TDD_Guidelines.md`
2. Consult this document for codebase-specific patterns
3. Reference `CODEBASE_CONTEXT.md` for architectural overview

---

## Table of Contents
1. [main.py - Bot Initialization](#1-mainpy---bot-initialization)
2. [Commands Module](#2-commands-module)
3. [Database Module](#3-database-module)
4. [Utils Module](#4-utils-module)
5. [Integration Testing Patterns](#5-integration-testing-patterns)
6. [Common Pitfalls](#6-common-pitfalls)
7. [Testing Checklist by Feature Type](#7-testing-checklist-by-feature-type)

---

## 1. main.py - Bot Initialization

### File Overview
**Location:** [main.py](main.py)
**Purpose:** Discord bot entry point, command registration, lifecycle events
**Dependencies:**
- `server.py` (Flask keep-alive)
- All command setup functions from `/commands`
- Discord.py library

### What to Test

#### ✅ **Testable Components** (Integration Level)

**1. Command Registration**
```python
def test_all_commands_registered():
    """
    GIVEN: A clean bot instance
    WHEN: All setup functions are called
    THEN: All expected commands are registered

    WHY: Ensures no command module is accidentally skipped in main.py
    """
    # This would be an integration test
    bot = create_test_bot()

    # Call setup functions
    setup_roll(bot)
    setup_boat_handling(bot)
    setup_weather(bot)
    setup_river_encounter(bot)
    setup_help(bot)

    # Verify commands exist
    assert 'roll' in [cmd.name for cmd in bot.tree.get_commands()]
    assert 'boat-handling' in [cmd.name for cmd in bot.tree.get_commands()]
    assert 'weather' in [cmd.name for cmd in bot.tree.get_commands()]
    assert 'river-encounter' in [cmd.name for cmd in bot.tree.get_commands()]
    assert 'help' in [cmd.name for cmd in bot.tree.get_commands()]
```

**2. Hello Command (Example Test)**
```python
@pytest.mark.asyncio
async def test_hello_slash_command_responds_with_greeting():
    """
    GIVEN: A user interaction with /hello
    WHEN: The hello command is triggered
    THEN: Bot responds with personalized greeting

    WHY: Validates the one command that lives in main.py
    """
    # Mock discord interaction
    interaction = MockInteraction(user=MockUser(mention="@TestUser"))

    await hello_slash(interaction)

    assert interaction.response.sent
    assert "@TestUser" in interaction.response.message
    assert "WFRP traveling companion" in interaction.response.message
```

#### ❌ **What NOT to Test** (Framework Responsibilities)

**Don't test:**
- Discord.py's `bot.run()` method
- Discord API connection handling
- Logging framework functionality
- Environment variable loading (`.env` file)
- Flask keep-alive server (test in `server.py` instead)

**Why:** These are external library responsibilities. Testing them creates brittle, maintenance-heavy tests.

### Testing Strategy for main.py

**Level:** Integration/System Tests
**Priority:** P2 (Medium) - Main.py is mostly glue code
**Test Location:** `tests/integration/test_bot_initialization.py`

**Pattern:**
```python
# Use fixtures to create clean bot instances
@pytest.fixture
def test_bot():
    """Create a bot instance for testing without running it"""
    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
    return bot

@pytest.mark.integration
def test_bot_has_correct_prefix(test_bot):
    """Verify bot configuration"""
    assert test_bot.command_prefix == "!"

@pytest.mark.integration
def test_bot_has_message_content_intent(test_bot):
    """Verify required intents are enabled"""
    assert test_bot.intents.message_content == True
```

### Connection Points (How main.py Relates to Other Modules)

```
main.py
  ├─→ commands/roll.py (setup_roll)
  ├─→ commands/boat_handling.py (setup_boat_handling)
  ├─→ commands/weather.py (setup_weather)
  ├─→ commands/river_encounter.py (setup_river_encounter)
  ├─→ commands/help.py (setup_help)
  └─→ server.py (keep_alive)
```

**Integration Test Focus:**
- Test that all `setup()` functions are called
- Test that bot initializes with correct configuration
- Test that command registration doesn't throw errors

### Common Pitfalls for main.py

**Pitfall 1: Testing Discord.py Internals**
```python
# ❌ BAD - Testing framework behavior
def test_bot_connects_to_discord():
    bot = create_bot()
    bot.run(TOKEN)  # This tries to actually connect!
    assert bot.is_ready()

# ✅ GOOD - Test your configuration
def test_bot_configured_with_correct_intents():
    bot = create_bot()
    assert bot.intents.message_content == True
    assert bot.command_prefix == "!"
```

**Pitfall 2: Not Mocking Discord Objects**
```python
# ❌ BAD - Tries to create real Discord objects
def test_hello_command():
    user = discord.User(id=123)  # Requires Discord API

# ✅ GOOD - Use mocks
def test_hello_command():
    user = MockUser(id=123, mention="@TestUser")
    interaction = MockInteraction(user=user)
```

**Pitfall 3: Testing in Production**
```python
# ❌ BAD - Uses production token
def test_bot_starts():
    bot.run(os.getenv("DISCORD_TOKEN"))  # Real bot runs!

# ✅ GOOD - Use test doubles
def test_bot_startup_sequence():
    # Test the setup logic without actually running bot
    assert callable(setup_roll)
    assert callable(setup_boat_handling)
```

### Use Case: Adding New Command Module

**Scenario:** You're adding a new command module `/trade` for trading mechanics.

**TDD Workflow:**

1. **Write Test First (RED)**
```python
def test_trade_command_registered(test_bot):
    """
    GIVEN: Bot instance with trade setup called
    WHEN: Checking registered commands
    THEN: Trade command is present
    """
    from commands.trade import setup as setup_trade
    setup_trade(test_bot)

    commands = [cmd.name for cmd in test_bot.tree.get_commands()]
    assert 'trade' in commands
```

2. **Update main.py (GREEN)**
```python
# In main.py
from commands.trade import setup as setup_trade

# In registration section
setup_trade(bot)
```

3. **Verify (REFACTOR)**
```python
# Run all integration tests
pytest tests/integration/test_bot_initialization.py -v

# Verify no regressions
pytest tests/ -v
```

### Summary: main.py Testing Priorities

| Component | Priority | Test Type | Test Location |
|-----------|----------|-----------|---------------|
| Command registration | P2 | Integration | `tests/integration/` |
| Hello command | P3 | Unit/Integration | `tests/unit/test_main.py` |
| Bot configuration | P2 | Unit | `tests/unit/test_main.py` |
| Event handlers (on_ready, on_message) | P3 | Integration | `tests/integration/` |
| Keep-alive integration | P3 | Integration | `tests/integration/` |

**Key Takeaway:** main.py is mostly **orchestration code**. Focus tests on ensuring modules are wired correctly, not on testing Discord.py functionality.

---

## 2. Commands Module

### Module Overview
**Location:** `/commands`
**Purpose:** All bot commands (slash and prefix versions)
**Pattern:** Each command file has `setup(bot)` function that registers commands

### Common Command Structure Pattern

**Every command file follows this pattern:**
```python
def setup(bot: commands.Bot):
    """Register commands with the bot"""

    @bot.tree.command(name="commandname", description="...")
    async def command_slash(interaction, ...):
        await _perform_command(interaction, ..., is_slash=True)

    @bot.command(name="commandname")
    async def command_prefix(ctx, ...):
        await _perform_command(ctx, ..., is_slash=False)

    async def _perform_command(context, ..., is_slash: bool):
        """Shared logic for both slash and prefix versions"""
        # 1. Validate inputs
        # 2. Execute business logic
        # 3. Format response
        # 4. Send response (handle slash vs prefix)
        # 5. Log to boat-travelling-log channel
```

### Commands Testing Philosophy: Test YOUR Logic, Not Discord.py

**CRITICAL DISTINCTION:**

✅ **DO test**: Your command handler logic (_perform_command functions)
- Input validation
- Business logic integration
- Response formatting
- Error handling
- Slash vs prefix routing

❌ **DON'T test**: Discord.py library internals
- `bot.tree.command()` decorator registration
- `interaction.response.send_message()` Discord API calls
- `discord.Embed.to_dict()` serialization
- Discord API connectivity

**Testing Pattern:**
```python
# ✅ GOOD - Test YOUR command logic with mocks
@pytest.mark.asyncio
async def test_roll_command_logic():
    """Test YOUR business logic, not Discord.py"""
    mock_interaction = MockInteraction()  # Simple test double

    # Test YOUR _perform_roll function
    await _perform_roll(mock_interaction, "1d100", 50, 10, is_slash=True)

    # Assert YOUR logic worked correctly
    assert "Success Level" in str(mock_interaction.response.embed)

# ❌ BAD - Testing Discord.py library
async def test_discord_sends_message():
    """This tests discord.py, not your code!"""
    real_interaction = discord.Interaction(...)  # Real Discord object
    await real_interaction.response.send_message("test")
    # Pointless - testing Discord's library
```

**Why This Approach:**
1. **Fast**: No Discord API calls, tests run in milliseconds
2. **Reliable**: No network dependencies, no flakiness
3. **Focused**: Tests YOUR code, not external libraries
4. **Maintainable**: Changes to Discord.py don't break your tests

### 2.1 commands/roll.py - Dice Rolling

**File:** [commands/roll.py](commands/roll.py:1)
**Existing Tests:** `tests/test_dice.py`, `tests/test_wfrp_mechanics.py`

#### What This File Does

1. **Parse dice notation** (`1d100`, `3d10+5`, `2d6-3`)
2. **Roll dice** using `utils.wfrp_mechanics`
3. **Calculate WFRP Success Levels** when target provided
4. **Detect doubles** (11, 22, 33, etc.) for crits/fumbles
5. **Format Discord embeds** with results
6. **Log commands** to `boat-travelling-log` channel

#### Key Dependencies
```
roll.py
  ├─→ utils.wfrp_mechanics.parse_dice_notation()
  ├─→ utils.wfrp_mechanics.roll_dice()
  ├─→ utils.wfrp_mechanics.check_wfrp_doubles()
  └─→ discord (Embed, Interaction, Context)
```

#### Testing Strategy

**Test Layers:**

1. **Unit Tests** (utils.wfrp_mechanics) - P0 Priority
   - Test dice parsing logic
   - Test SL calculation
   - Test doubles detection
   - **Location:** `tests/test_wfrp_mechanics.py` ✅ EXISTS

2. **Integration Tests** (command flow) - P1 Priority
   - Test command handler receives correct input
   - Test command calls correct utility functions
   - Test command formats response correctly
   - **Location:** `tests/unit/test_roll_command.py` ⚠️ MISSING

3. **Discord Mock Tests** (response handling) - P2 Priority
   - Test slash vs prefix command routing
   - Test error handling
   - Test logging functionality

#### Existing Test Example (from test_wfrp_mechanics.py)

```python
def test_parse_dice_notation_basic():
    """
    GIVEN: Basic dice notation like '3d10'
    WHEN: parse_dice_notation is called
    THEN: Returns correct tuple (num_dice, die_size, modifier)

    WHY: Ensures dice string parsing works for standard notation
    """
    num_dice, die_size, modifier = parse_dice_notation("3d10")
    assert num_dice == 3
    assert die_size == 10
    assert modifier == 0
```

#### What Tests Are Missing (TODO)

**Missing Unit Test - Command Handler:**
```python
# tests/unit/test_roll_command.py (NEEDS TO BE CREATED)

@pytest.mark.asyncio
async def test_roll_command_with_wfrp_target_calculates_success_level():
    """
    GIVEN: User rolls /roll 1d100 45 20
    WHEN: Command handler processes the request
    THEN: Embed includes Success Level calculation

    WHY: Validates integration between command and WFRP mechanics
    """
    mock_interaction = MockInteraction()

    await _perform_roll(
        context=mock_interaction,
        dice="1d100",
        target=45,
        modifier=20,
        is_slash=True
    )

    embed = mock_interaction.response.embed
    assert "Success Level" in embed.fields
    assert "Final Target: 65" in str(embed)  # 45 + 20
```

**Missing Integration Test - Error Handling:**
```python
@pytest.mark.asyncio
async def test_roll_command_handles_invalid_notation():
    """
    GIVEN: Invalid dice notation like 'abc' or '1d'
    WHEN: Command is executed
    THEN: Returns error embed without crashing

    WHY: Prevents bot crashes from user input errors
    """
    mock_interaction = MockInteraction()

    await _perform_roll(
        context=mock_interaction,
        dice="invalid",
        target=None,
        modifier=20,
        is_slash=True
    )

    embed = mock_interaction.response.embed
    assert "Invalid Dice Notation" in embed.title
    assert embed.color == discord.Color.red()
```

#### Use Case: Adding New Dice Type

**Scenario:** Add support for Fate dice (dF) which return -1, 0, or 1.

**TDD Workflow:**

**Step 1: Write Tests (RED)**
```python
# tests/test_wfrp_mechanics.py

def test_parse_dice_notation_fate_dice():
    """Test parsing Fate dice notation like '4dF'"""
    num_dice, die_type, modifier = parse_dice_notation("4dF")
    assert num_dice == 4
    assert die_type == "fate"
    assert modifier == 0

def test_roll_fate_dice_returns_values_in_range():
    """Test Fate dice return -1, 0, or 1"""
    results = roll_fate_dice(4)
    assert len(results) == 4
    assert all(r in [-1, 0, 1] for r in results)
```

**Step 2: Implement (GREEN)**
```python
# utils/wfrp_mechanics.py

def parse_dice_notation(notation: str):
    # Add pattern for Fate dice
    if 'dF' in notation.lower():
        # Parse Fate dice
        ...
    # Existing logic
    ...

def roll_fate_dice(num_dice: int):
    return [random.choice([-1, 0, 1]) for _ in range(num_dice)]
```

**Step 3: Integration Test**
```python
# tests/unit/test_roll_command.py

@pytest.mark.asyncio
async def test_roll_command_supports_fate_dice():
    """Test /roll 4dF command end-to-end"""
    mock_interaction = MockInteraction()

    await _perform_roll(mock_interaction, "4dF", None, 0, True)

    embed = mock_interaction.response.embed
    assert "Fate" in embed.title or "dF" in embed.fields
```

#### Connection Points

```
User Input
   ↓
roll.py (_perform_roll)
   ↓
├─→ wfrp_mechanics.parse_dice_notation() [UNIT TESTED ✅]
├─→ wfrp_mechanics.roll_dice() [UNIT TESTED ✅]
├─→ wfrp_mechanics.calculate_success_level() [UNIT TESTED ✅]
├─→ wfrp_mechanics.check_wfrp_doubles() [UNIT TESTED ✅]
└─→ _send_command_log() [NOT TESTED ⚠️]
   ↓
Discord Response
```

#### Pitfalls for roll.py

**Pitfall 1: Testing Randomness Directly**
```python
# ❌ BAD - Flaky test
def test_roll_dice_returns_valid_results():
    results = roll_dice(3, 10)
    assert results == [5, 7, 3]  # Will fail randomly!

# ✅ GOOD - Test properties
def test_roll_dice_returns_correct_count_and_range():
    results = roll_dice(3, 10)
    assert len(results) == 3
    assert all(1 <= r <= 10 for r in results)
```

**Pitfall 2: Not Testing Both Command Types**
```python
# ❌ BAD - Only tests slash command
async def test_roll_command():
    await roll_slash(interaction, "1d100")

# ✅ GOOD - Test shared logic works for both
async def test_roll_shared_logic_works_for_slash():
    await _perform_roll(context, "1d100", None, 20, is_slash=True)

async def test_roll_shared_logic_works_for_prefix():
    await _perform_roll(context, "1d100", None, 20, is_slash=False)
```

**Pitfall 3: Not Mocking Discord Objects**
```python
# ❌ BAD - Requires Discord API
def test_roll_command():
    interaction = discord.Interaction(...)  # Needs real connection

# ✅ GOOD - Use test doubles
def test_roll_command():
    interaction = MockInteraction(user=MockUser())
```

---

## 2.2 commands/boat_handling.py - Navigation Tests

**File:** [commands/boat_handling.py](commands/boat_handling.py:1)
**Existing Tests:** None found (⚠️ HIGH PRIORITY TO ADD)

#### What This File Does

1. **Looks up character** from `db.character_data`
2. **Determines skill** (Sail or Row) to use
3. **Calculates Lore bonus** (first digit of Lore (Riverways))
4. **Queries weather modifiers** from active journey
5. **Rolls d100** and calculates Success Level
6. **Checks doubles** for crits/fumbles
7. **Determines narrative outcome** based on SL tiers
8. **Formats embed** with flavor text and mechanics
9. **Logs to channel**

#### Key Dependencies
```
boat_handling.py
  ├─→ db.character_data (get_character, get_available_characters)
  ├─→ utils.wfrp_mechanics (check_wfrp_doubles, roll_dice)
  ├─→ utils.modifier_calculator (get_active_weather_modifiers)
  └─→ discord (Embed, Interaction, Context)
```

#### Critical Testing Areas

**1. Character Data Integration (P0)**
```python
def test_boat_handling_uses_sail_if_available():
    """
    GIVEN: Character with Sail skill
    WHEN: Boat handling test is performed
    THEN: Uses Sail, not Row

    WHY: Sail is advanced skill and should be preferred
    """
    char = get_character("emmerich")  # Has Sail: 30
    skill_name, skill_value = get_boat_handling_skill(char)

    assert skill_name == "Sail"
    assert skill_value == 30
```

**2. Weather Modifier Integration (P0)**
```python
@pytest.mark.asyncio
async def test_boat_handling_applies_weather_penalty():
    """
    GIVEN: Active weather with -10 boat handling penalty (calm winds)
    WHEN: Boat handling test is performed
    THEN: Final difficulty includes weather modifier

    WHY: Weather MUST affect boat handling tests per WFRP rules
    """
    # Setup: Create journey with calm wind weather
    storage = WeatherStorage(":memory:")
    storage.start_journey("guild123", "summer", "reikland")
    # ... generate weather with calm winds ...

    mock_interaction = MockInteraction(guild_id="guild123")

    await _perform_boat_handling(
        mock_interaction,
        character="anara",
        difficulty=0,  # Base difficulty
        time_of_day="midday",
        is_slash=True
    )

    embed = mock_interaction.response.embed
    # Should show base difficulty (0) + weather modifier (-10) = -10
    assert "Weather Modifier: -10" in str(embed)
```

**3. Lore (Riverways) Bonus (P1)**
```python
def test_lore_riverways_bonus_calculated_correctly():
    """
    GIVEN: Character with Lore (Riverways) 47
    WHEN: Calculating boat handling target
    THEN: Adds +4 bonus (first digit)

    WHY: Lore skill provides tens-digit bonus per WFRP rules
    """
    char = {"river_travelling_skills": {"Lore (Riverways)": 47}}
    bonus = get_lore_riverways_bonus(char)
    assert bonus == 4
```

**4. Success Level Outcomes (P1)**
```python
def test_boat_handling_marginal_success_has_correct_flavor():
    """
    GIVEN: Roll results in SL +1 (marginal success)
    WHEN: Determining outcome
    THEN: Returns "Marginal Success" with appropriate flavor

    WHY: Different SL tiers have different narrative outcomes
    """
    # Test the outcome determination logic
    outcome = determine_boat_handling_outcome(sl=1, success=True)

    assert outcome["level"] == "Marginal Success"
    assert "effort" in outcome["flavor"].lower()
```

#### Missing Tests (HIGH PRIORITY)

```python
# tests/unit/test_boat_handling_command.py (NEEDS TO BE CREATED)

@pytest.mark.asyncio
async def test_boat_handling_invalid_character_returns_error():
    """Test error handling for nonexistent character"""
    mock_interaction = MockInteraction()

    await _perform_boat_handling(
        mock_interaction,
        character="nonexistent",
        difficulty=0,
        time_of_day="midday",
        is_slash=True
    )

    embed = mock_interaction.response.embed
    assert "not found" in embed.description.lower()

@pytest.mark.asyncio
async def test_boat_handling_without_weather_uses_base_difficulty():
    """Test boat handling works when no active weather journey"""
    # No weather journey started
    mock_interaction = MockInteraction(guild_id="guild999")

    await _perform_boat_handling(
        mock_interaction,
        character="anara",
        difficulty=-20,  # Hard
        time_of_day="midday",
        is_slash=True
    )

    embed = mock_interaction.response.embed
    # Should not crash, should use base difficulty only
    assert embed is not None
    assert "Difficulty: Hard (-20)" in str(embed)
```

#### Connection Points

```
User: /boat-handling anara -10 dusk
         ↓
boat_handling.py
         ↓
    ┌────┴────┬─────────────┬──────────────┐
    ↓         ↓             ↓              ↓
character  wfrp_       modifier_      Discord
_data     mechanics   calculator     Formatting
    ↓         ↓             ↓              ↓
Get char  Roll d100   Get weather    Build embed
stats     Calc SL     penalties      with narrative
```

**Critical Integration Points to Test:**
1. Character data → Skill selection
2. Weather storage → Modifier calculator → Boat handling
3. WFRP mechanics → Success level → Narrative outcome
4. Result → Discord embed format

---

## 2.3 commands/weather.py - Weather Command Interface

**File:** [commands/weather.py](commands/weather.py:1)
**Existing Tests:** `tests/test_handler_integration.py` ✅

#### What This File Does

This file is JUST an interface layer. It:
1. **Defines command signature** (parameters, choices)
2. **Checks GM permissions** for override actions
3. **Delegates to handler** (`WeatherCommandHandler`)

**Key Pattern:** This is a **thin wrapper**. All business logic lives in `commands/weather_modules/handler.py`.

#### Testing Strategy

**DON'T duplicate handler tests here!**

**DO test:**
- GM permission checks
- Command parameter validation
- Correct handler method is called

```python
# tests/unit/test_weather_command.py

@pytest.mark.asyncio
async def test_weather_override_requires_gm_permission():
    """
    GIVEN: Non-GM user tries /weather override
    WHEN: Command is executed
    THEN: Returns permission denied message

    WHY: Override is GM-only feature
    """
    user = MockUser(id=123, is_gm=False)
    interaction = MockInteraction(user=user)

    await weather_slash(
        interaction,
        action="override",
        season="summer",
        province="reikland"
    )

    assert "Only GMs" in interaction.response.message

@pytest.mark.asyncio
async def test_weather_next_delegates_to_handler():
    """
    GIVEN: User runs /weather next
    WHEN: Command is processed
    THEN: Handler.handle_command is called with correct args

    WHY: Ensures delegation works correctly
    """
    mock_handler = Mock(spec=WeatherCommandHandler)
    interaction = MockInteraction()

    # Inject mock handler (dependency injection for testing)
    await weather_slash(interaction, action="next")

    mock_handler.handle_command.assert_called_with(
        interaction, "next", None, None, None, is_slash=True
    )
```

#### What NOT to Test Here

❌ Don't test weather generation logic (that's in `weather_mechanics.py`)
❌ Don't test weather storage (that's in `weather_storage.py`)
❌ Don't test weather display (that's in `weather_modules/display.py`)

✅ DO test command interface concerns only

---

### 2.3a `/commands/weather_modules/` - Weather System Core

**Location:** [commands/weather_modules/](commands/weather_modules/)
**Purpose:** Complete weather system implementation (generation, storage, display, notifications)

This folder contains the **core business logic** for the entire weather system. The top-level `weather.py` is just a thin command interface - everything important happens here.

#### Module Architecture

```
/commands/weather_modules/
├── handler.py         # Orchestrator - coordinates all weather operations
├── formatters.py      # Pure utility functions (emojis, formatting)
├── display.py         # Discord embed creation
├── stages.py          # Multi-day stage display generation
└── notifications.py   # GM channel notifications
```

**Key Pattern:** Separation of Concerns
- **handler.py** = Orchestration (delegates to specialists)
- **formatters.py** = Pure functions (no state, no I/O)
- **display.py** = Presentation layer (Discord-specific)
- **stages.py** = Composite displays (multi-day views)
- **notifications.py** = Side effects (GM notifications)

#### Why This Module Is Critical

This is the **most complex** part of the bot:
1. **Stateful operations** (journey tracking, weather history)
2. **Multiple data sources** (weather_data.py, weather_storage.py, weather_mechanics.py)
3. **Complex orchestration** (generate → store → display → notify)
4. **Discord API integration** (embeds, channels, buttons)

**TDD Approach:** Test each layer independently before testing integration.

---

### 2.3b `handler.py` - Weather Command Orchestrator

**File:** [commands/weather_modules/handler.py](commands/weather_modules/handler.py:1)
**Lines:** ~200 lines
**Pattern:** Orchestrator pattern (delegates to specialized modules)

#### What This File Does

This is the **central coordinator** for all weather operations:

1. **Routes actions** → Determines which handler method to call (`next`, `stage`, `current`, `override`)
2. **Generates weather** → Coordinates with `weather_mechanics.py` and `weather_data.py`
3. **Manages journeys** → Tracks journey state (day counter, stage counter)
4. **Stores weather** → Persists to SQLite via `weather_storage.py`
5. **Displays results** → Delegates to `display.py` for Discord embeds
6. **Sends notifications** → Delegates to `notifications.py` for GM channel

#### Key Methods

```python
class WeatherCommandHandler:
    async def handle_command(interaction, action, season, province, value, is_slash):
        """Routes to correct handler based on action"""

    async def handle_next(interaction, is_slash):
        """Generate next day's weather, increment day counter"""

    async def handle_stage(interaction, stage_duration, season, province, is_slash):
        """Generate multi-day stage (3-7 days)"""

    async def handle_current(interaction, is_slash):
        """Display most recent weather from storage"""

    async def handle_override(interaction, season, province, value, is_slash):
        """GM override: force weather generation for specific conditions"""
```

#### Testing Strategy: What SHOULD Be Tested

**Test Focus:** Orchestration logic, NOT implementation details of delegated modules.

##### Category 1: Action Routing Tests

Test that the handler correctly routes to the appropriate method.

```python
# tests/unit/test_weather_handler.py

@pytest.mark.asyncio
async def test_handler_routes_next_action_correctly():
    """
    GIVEN: User runs /weather action=next
    WHEN: handle_command is called
    THEN: handle_next method is invoked

    WHY: Ensures routing logic works correctly
    """
    handler = WeatherCommandHandler()
    mock_interaction = MockInteraction()

    with patch.object(handler, 'handle_next') as mock_next:
        await handler.handle_command(
            mock_interaction,
            action="next",
            season=None,
            province=None,
            value=None,
            is_slash=True
        )

        mock_next.assert_called_once_with(mock_interaction, True)

@pytest.mark.asyncio
async def test_handler_routes_stage_action_correctly():
    """Test routing for stage action"""
    handler = WeatherCommandHandler()
    mock_interaction = MockInteraction()

    with patch.object(handler, 'handle_stage') as mock_stage:
        await handler.handle_command(
            mock_interaction,
            action="stage",
            season="summer",
            province="reikland",
            value=5,  # 5-day stage
            is_slash=True
        )

        mock_stage.assert_called_once_with(
            mock_interaction, 5, "summer", "reikland", True
        )

@pytest.mark.asyncio
async def test_handler_routes_current_action_correctly():
    """Test routing for current weather display"""
    handler = WeatherCommandHandler()
    mock_interaction = MockInteraction()

    with patch.object(handler, 'handle_current') as mock_current:
        await handler.handle_command(
            mock_interaction,
            action="current",
            season=None,
            province=None,
            value=None,
            is_slash=True
        )

        mock_current.assert_called_once_with(mock_interaction, True)

@pytest.mark.asyncio
async def test_handler_routes_override_action_correctly():
    """Test routing for GM override"""
    handler = WeatherCommandHandler()
    mock_interaction = MockInteraction()

    with patch.object(handler, 'handle_override') as mock_override:
        await handler.handle_command(
            mock_interaction,
            action="override",
            season="winter",
            province="middenland",
            value=None,
            is_slash=True
        )

        mock_override.assert_called_once_with(
            mock_interaction, "winter", "middenland", None, True
        )

@pytest.mark.asyncio
async def test_handler_handles_invalid_action():
    """
    GIVEN: Invalid action string
    WHEN: handle_command is called
    THEN: Returns error message to user

    WHY: Prevents crashes from bad input
    """
    handler = WeatherCommandHandler()
    mock_interaction = MockInteraction()

    await handler.handle_command(
        mock_interaction,
        action="invalid_action",
        season=None,
        province=None,
        value=None,
        is_slash=True
    )

    assert "Unknown action" in mock_interaction.response.message
```

##### Category 2: Weather Generation Coordination Tests

Test that weather generation includes all required components.

```python
@pytest.mark.asyncio
async def test_handler_generates_daily_weather_with_all_components():
    """
    GIVEN: User requests next day's weather
    WHEN: handle_next is called
    THEN: Generated weather includes wind, weather type, temperature, special events

    WHY: Weather must be complete for gameplay
    """
    handler = WeatherCommandHandler()
    mock_interaction = MockInteraction()
    mock_storage = Mock(spec=WeatherStorage)

    # Mock storage to return minimal journey data
    mock_storage.get_journey_state.return_value = {
        "day_number": 1,
        "stage_number": 1,
        "season": "summer",
        "province": "reikland"
    }

    # Inject mock storage
    handler.storage = mock_storage

    await handler.handle_next(mock_interaction, is_slash=True)

    # Verify storage was called with complete weather data
    call_args = mock_storage.store_weather.call_args
    weather_data = call_args[0][0]

    assert "wind_strength" in weather_data
    assert "wind_direction" in weather_data
    assert "weather_type" in weather_data
    assert "temperature" in weather_data
    assert "special_event" in weather_data or weather_data.get("special_event") is None

@pytest.mark.asyncio
async def test_handler_uses_correct_season_and_province():
    """
    GIVEN: Journey has season=winter, province=middenland
    WHEN: handle_next generates weather
    THEN: Uses winter tables and middenland modifiers

    WHY: Weather must match journey context
    """
    handler = WeatherCommandHandler()
    mock_interaction = MockInteraction()
    mock_storage = Mock(spec=WeatherStorage)

    mock_storage.get_journey_state.return_value = {
        "day_number": 3,
        "stage_number": 1,
        "season": "winter",
        "province": "middenland"
    }

    handler.storage = mock_storage

    with patch('utils.weather_mechanics.generate_weather') as mock_generate:
        await handler.handle_next(mock_interaction, is_slash=True)

        # Verify correct season/province passed to weather generation
        mock_generate.assert_called_once()
        call_kwargs = mock_generate.call_args[1]
        assert call_kwargs.get("season") == "winter"
        assert call_kwargs.get("province") == "middenland"

@pytest.mark.asyncio
async def test_handler_increments_day_counter_after_generation():
    """
    GIVEN: Journey is on day 5
    WHEN: handle_next is called
    THEN: Day counter increments to 6

    WHY: Day tracking is critical for journey progression
    """
    handler = WeatherCommandHandler()
    mock_interaction = MockInteraction()
    mock_storage = Mock(spec=WeatherStorage)

    mock_storage.get_journey_state.return_value = {
        "day_number": 5,
        "stage_number": 2,
        "season": "spring",
        "province": "reikland"
    }

    handler.storage = mock_storage

    await handler.handle_next(mock_interaction, is_slash=True)

    # Verify day_number was incremented when storing
    call_args = mock_storage.store_weather.call_args
    stored_data = call_args[0][0]
    assert stored_data["day_number"] == 6
```

##### Category 3: Stage Generation Tests

Test multi-day weather generation.

```python
@pytest.mark.asyncio
async def test_handler_generates_multiple_days_for_stage():
    """
    GIVEN: User requests 5-day stage
    WHEN: handle_stage is called
    THEN: Generates exactly 5 days of weather

    WHY: Stage duration must match request
    """
    handler = WeatherCommandHandler()
    mock_interaction = MockInteraction()
    mock_storage = Mock(spec=WeatherStorage)

    mock_storage.get_journey_state.return_value = {
        "day_number": 10,
        "stage_number": 3,
        "season": "autumn",
        "province": "talabecland"
    }

    handler.storage = mock_storage

    await handler.handle_stage(
        mock_interaction,
        stage_duration=5,
        season="autumn",
        province="talabecland",
        is_slash=True
    )

    # Verify store_weather called 5 times
    assert mock_storage.store_weather.call_count == 5

    # Verify day numbers increment correctly (10→11→12→13→14)
    stored_days = [call[0][0]["day_number"] for call in mock_storage.store_weather.call_args_list]
    assert stored_days == [11, 12, 13, 14, 15]

@pytest.mark.asyncio
async def test_handler_increments_stage_counter_after_stage():
    """
    GIVEN: Journey is on stage 2
    WHEN: handle_stage completes 4-day stage
    THEN: Stage counter increments to 3

    WHY: Stage tracking needed for journey management
    """
    handler = WeatherCommandHandler()
    mock_interaction = MockInteraction()
    mock_storage = Mock(spec=WeatherStorage)

    mock_storage.get_journey_state.return_value = {
        "day_number": 7,
        "stage_number": 2,
        "season": "summer",
        "province": "reikland"
    }

    handler.storage = mock_storage

    await handler.handle_stage(
        mock_interaction,
        stage_duration=4,
        season="summer",
        province="reikland",
        is_slash=True
    )

    # Check final day's stage_number
    final_call = mock_storage.store_weather.call_args_list[-1]
    assert final_call[0][0]["stage_number"] == 3
```

##### Category 4: Display & Notification Coordination Tests

Test that handler correctly delegates to display and notification modules.

```python
@pytest.mark.asyncio
async def test_handler_sends_embed_to_interaction():
    """
    GIVEN: Weather is generated
    WHEN: handle_next completes
    THEN: Sends Discord embed to interaction

    WHY: User must receive weather display
    """
    handler = WeatherCommandHandler()
    mock_interaction = MockInteraction()
    mock_storage = Mock(spec=WeatherStorage)

    mock_storage.get_journey_state.return_value = {
        "day_number": 1,
        "stage_number": 1,
        "season": "spring",
        "province": "reikland"
    }

    handler.storage = mock_storage

    with patch('commands.weather_modules.display.create_weather_embed') as mock_embed:
        mock_embed.return_value = Mock(spec=discord.Embed)

        await handler.handle_next(mock_interaction, is_slash=True)

        # Verify embed was created and sent
        mock_embed.assert_called_once()
        assert mock_interaction.response.embed is not None

@pytest.mark.asyncio
async def test_handler_sends_gm_notification_when_configured():
    """
    GIVEN: GM notification channel exists
    WHEN: Weather is generated
    THEN: Notification sent to GM channel

    WHY: GMs need weather alerts
    """
    handler = WeatherCommandHandler()
    mock_interaction = MockInteraction()
    mock_storage = Mock(spec=WeatherStorage)
    gm_channel = Mock(spec=discord.TextChannel)

    mock_interaction.guild.get_channel.return_value = gm_channel
    mock_storage.get_journey_state.return_value = {
        "day_number": 1,
        "stage_number": 1,
        "season": "winter",
        "province": "middenland"
    }

    handler.storage = mock_storage

    with patch('commands.weather_modules.notifications.send_gm_weather_notification') as mock_notify:
        await handler.handle_next(mock_interaction, is_slash=True)

        # Verify notification was sent
        mock_notify.assert_called_once()
```

##### Category 5: Journey Management Tests

Test journey initialization and state management.

```python
@pytest.mark.asyncio
async def test_handler_initializes_new_journey_when_none_exists():
    """
    GIVEN: No existing journey in database
    WHEN: User runs /weather next
    THEN: Creates new journey starting at day 1, stage 1

    WHY: First command must initialize journey
    """
    handler = WeatherCommandHandler()
    mock_interaction = MockInteraction()
    mock_storage = Mock(spec=WeatherStorage)

    # Simulate no existing journey
    mock_storage.get_journey_state.return_value = None

    handler.storage = mock_storage

    await handler.handle_next(mock_interaction, is_slash=True)

    # Verify new journey was created
    call_args = mock_storage.store_weather.call_args
    stored_data = call_args[0][0]
    assert stored_data["day_number"] == 1
    assert stored_data["stage_number"] == 1

@pytest.mark.asyncio
async def test_handler_continues_existing_journey():
    """
    GIVEN: Journey already at day 8, stage 2
    WHEN: User runs /weather next
    THEN: Continues from day 9 (does not restart)

    WHY: Journey state must persist
    """
    handler = WeatherCommandHandler()
    mock_interaction = MockInteraction()
    mock_storage = Mock(spec=WeatherStorage)

    mock_storage.get_journey_state.return_value = {
        "day_number": 8,
        "stage_number": 2,
        "season": "autumn",
        "province": "talabecland"
    }

    handler.storage = mock_storage

    await handler.handle_next(mock_interaction, is_slash=True)

    # Verify day incremented
    call_args = mock_storage.store_weather.call_args
    stored_data = call_args[0][0]
    assert stored_data["day_number"] == 9
```

#### What NOT to Test in handler.py

❌ **Don't test weather generation algorithms** (that's in `utils/weather_mechanics.py`)
❌ **Don't test SQLite operations** (that's in `weather_storage.py`)
❌ **Don't test embed formatting** (that's in `display.py`)
❌ **Don't test emoji selection** (that's in `formatters.py`)

✅ **DO test orchestration logic:**
- Correct method routing
- Correct delegation to specialized modules
- Journey state management
- Data flow between modules

#### Common Pitfalls

```python
# ❌ BAD - Testing implementation details of delegated module
@pytest.mark.asyncio
async def test_handler_generates_wind_with_1d100_roll():
    """This tests weather_mechanics.py, not handler.py!"""
    handler = WeatherCommandHandler()
    # ... test wind generation dice ...

# ✅ GOOD - Testing coordination
@pytest.mark.asyncio
async def test_handler_includes_wind_in_generated_weather():
    """Tests that handler ensures wind is present"""
    handler = WeatherCommandHandler()
    mock_interaction = MockInteraction()

    await handler.handle_next(mock_interaction, is_slash=True)

    # Verify wind was included (don't care HOW it was generated)
    stored_weather = handler.storage.store_weather.call_args[0][0]
    assert "wind_strength" in stored_weather
```

---

### 2.3c `formatters.py` - Pure Utility Functions

**File:** [commands/weather_modules/formatters.py](commands/weather_modules/formatters.py:1)
**Pattern:** Static utility class (all `@staticmethod`)

#### What This File Does

Pure functions for formatting weather data:
- `get_weather_emoji(weather_type)` → Returns emoji for weather type
- `get_wind_emoji(wind_strength)` → Returns emoji for wind strength
- `format_temperature(temp)` → Returns formatted temperature string
- `format_wind_description(wind_data)` → Returns human-readable wind info

**Key Characteristic:** NO side effects, NO state, NO I/O. Pure input → output transformations.

#### Testing Strategy: Easiest File to Test

These are **perfect unit test candidates**:
- No mocking needed
- No async needed
- No Discord API
- No database

```python
# tests/unit/test_weather_formatters.py

def test_get_weather_emoji_returns_correct_emoji_for_all_types():
    """
    GIVEN: All possible weather types from WFRP tables
    WHEN: get_weather_emoji is called
    THEN: Returns appropriate emoji for each type

    WHY: Visual consistency in Discord embeds
    """
    from commands.weather_modules.formatters import WeatherFormatters

    # Test all weather types
    assert WeatherFormatters.get_weather_emoji("dry") == "☀️"
    assert WeatherFormatters.get_weather_emoji("drizzle") == "🌦️"
    assert WeatherFormatters.get_weather_emoji("rain") == "🌧️"
    assert WeatherFormatters.get_weather_emoji("downpour") == "⛈️"
    assert WeatherFormatters.get_weather_emoji("snow") == "❄️"
    assert WeatherFormatters.get_weather_emoji("blizzard") == "🌨️"
    assert WeatherFormatters.get_weather_emoji("fog") == "🌫️"
    assert WeatherFormatters.get_weather_emoji("mist") == "🌁"

def test_get_weather_emoji_handles_unknown_type():
    """
    GIVEN: Unknown weather type
    WHEN: get_weather_emoji is called
    THEN: Returns default emoji (cloud)

    WHY: Graceful degradation for data errors
    """
    assert WeatherFormatters.get_weather_emoji("unknown_type") == "☁️"
    assert WeatherFormatters.get_weather_emoji("") == "☁️"
    assert WeatherFormatters.get_weather_emoji(None) == "☁️"

def test_get_wind_emoji_returns_correct_emoji_for_all_strengths():
    """Test wind strength emoji mapping"""
    assert WeatherFormatters.get_wind_emoji("Light") == "🍃"
    assert WeatherFormatters.get_wind_emoji("Moderate") == "💨"
    assert WeatherFormatters.get_wind_emoji("Strong") == "🌬️"
    assert WeatherFormatters.get_wind_emoji("Gale") == "🌪️"

def test_format_temperature_includes_unit():
    """
    GIVEN: Temperature value
    WHEN: format_temperature is called
    THEN: Returns string with °C

    WHY: User needs to know unit
    """
    assert "°C" in WeatherFormatters.format_temperature(15)
    assert "15" in WeatherFormatters.format_temperature(15)
    assert "-5" in WeatherFormatters.format_temperature(-5)

def test_format_wind_description_combines_strength_and_direction():
    """
    GIVEN: Wind data with strength and direction
    WHEN: format_wind_description is called
    THEN: Returns readable description like "Strong wind from the North"

    WHY: Players need natural language descriptions
    """
    wind_data = {
        "strength": "Strong",
        "direction": "North"
    }

    result = WeatherFormatters.format_wind_description(wind_data)

    assert "Strong" in result
    assert "North" in result
    assert "wind" in result.lower()
```

#### Parameterized Testing Pattern

Since these are pure functions with many similar test cases, use `pytest.mark.parametrize`:

```python
import pytest

@pytest.mark.parametrize("weather_type,expected_emoji", [
    ("dry", "☀️"),
    ("drizzle", "🌦️"),
    ("rain", "🌧️"),
    ("downpour", "⛈️"),
    ("snow", "❄️"),
    ("blizzard", "🌨️"),
    ("fog", "🌫️"),
    ("mist", "🌁"),
    ("unknown", "☁️"),
    (None, "☁️"),
    ("", "☁️"),
])
def test_get_weather_emoji_all_cases(weather_type, expected_emoji):
    """Parameterized test for all weather emoji mappings"""
    assert WeatherFormatters.get_weather_emoji(weather_type) == expected_emoji

@pytest.mark.parametrize("wind_strength,expected_emoji", [
    ("Light", "🍃"),
    ("Moderate", "💨"),
    ("Strong", "🌬️"),
    ("Gale", "🌪️"),
    ("unknown", "💨"),  # Default
    (None, "💨"),
])
def test_get_wind_emoji_all_cases(wind_strength, expected_emoji):
    """Parameterized test for all wind emoji mappings"""
    assert WeatherFormatters.get_wind_emoji(wind_strength) == expected_emoji
```

#### Test Coverage Target: 100%

This file should have **complete test coverage** because:
1. Pure functions (easy to test)
2. Limited branching (mostly dictionary lookups)
3. Critical for UI consistency

**Goal:** Every weather type, wind strength, and edge case covered.

---

### 2.3d `display.py` - Discord Embed Creation

**File:** [commands/weather_modules/display.py](commands/weather_modules/display.py:1)
**Lines:** ~330 lines
**Pattern:** Static display manager (all presentation logic)

#### What This File Does

Handles **all Discord embed creation** for weather displays:

1. **Creates daily weather embeds** → Main weather display with all formatted data
2. **Formats embed fields** → Temperature, wind conditions, weather effects
3. **Handles command types** → Works with both slash and prefix commands
4. **Sends embeds** → Auto-detects interaction vs. context
5. **Error/info messages** → Standardized error and informational embeds

**Key Class:** `WeatherDisplayManager` (all static methods)

#### Testing Strategy: UI Consistency & Data Formatting

**Test Focus:** Embed structure, field formatting, data display accuracy.

Tests for display.py should verify embed structure, data formatting, and command type handling. Focus on ensuring all weather data fields are correctly formatted and displayed, and that the system properly handles both slash and prefix commands.

#### What NOT to Test in display.py

❌ **Don't test Discord API internals** (embed.to_dict(), discord.py library behavior)
❌ **Don't test weather data generation** (that's in `weather_mechanics.py`)
❌ **Don't test emoji selection logic** (that's in `formatters.py`)

✅ **DO test display concerns:**
- Embed structure and field presence
- Data formatting accuracy
- Command type handling
- Error message formatting

---

### 2.3e `stages.py` - Multi-Day Stage Displays

**File:** [commands/weather_modules/stages.py](commands/weather_modules/stages.py:1)
**Lines:** ~336 lines
**Pattern:** Stage display manager (composite weather views)

#### What This File Does

Creates **multi-day weather summaries** for journey stages:

1. **Stage summary embeds** → Show 3-7 days of weather at once
2. **Condensed formatting** → Compact display for multiple days
3. **Journey overview** → High-level view of all stages
4. **Weather pattern analysis** → Show trends across days

**Key Class:** `StageDisplayManager` (all static methods)

#### Testing Strategy: Composite Display Logic

**Test Focus:** Multi-day aggregation, condensed formatting, data summarization.

Tests for stages.py should verify multi-day aggregation, condensed wind/weather formatting, and journey overview displays. Focus on testing that multiple days are correctly summarized and that weather patterns across stages are accurately represented.

#### What NOT to Test in stages.py

❌ **Don't test single-day weather display** (that's in `display.py`)
❌ **Don't test emoji selection** (that's in `formatters.py`)
❌ **Don't test weather data retrieval** (that's in `weather_storage.py`)

✅ **DO test stage display concerns:**
- Multi-day aggregation
- Condensed formatting
- Weather pattern analysis
- Journey overview logic

---

### 2.3f `notifications.py` - GM Channel Notifications

**File:** [commands/weather_modules/notifications.py](commands/weather_modules/notifications.py:1)
**Lines:** ~424 lines
**Pattern:** Notification manager (side effects - Discord messages)

#### What This File Does

Sends **GM-focused notifications** to designated Discord channel:

1. **Weather notifications** → Mechanical details for GMs (boat handling modifiers, penalties)
2. **Stage notifications** → Stage completion alerts
3. **Journey notifications** → Journey start/end alerts
4. **Channel finding** → Locates GM channel by name

**Key Class:** `NotificationManager` (all static methods)

#### Testing Strategy: Side Effect Testing with Mocks

**Test Focus:** Channel finding, message formatting, notification sending.

Tests for notifications.py should verify channel finding and error handling, notification content (boat handling modifiers, penalties, special events), and delivery confirmation. All Discord channel operations should be mocked.

#### What NOT to Test in notifications.py

❌ **Don't test Discord.py channel finding internals** (discord.utils.get)
❌ **Don't test weather data generation** (that's in `weather_mechanics.py`)
❌ **Don't test embed field creation logic** (that's Discord API)

✅ **DO test notification concerns:**
- Channel finding and error handling
- Message content and formatting
- Permission error handling
- Notification delivery confirmation

---

### Summary: Weather Modules Testing Overview

The weather_modules folder is the **core** of the weather system. Testing should focus on:

| Module | Test Priority | Key Focus |
|--------|--------------|-----------|
| handler.py | 🔴 HIGH | Orchestration logic, journey state management |
| formatters.py | 🟢 LOW (easy) | Pure functions, 100% coverage target |
| display.py | 🟡 MEDIUM | Embed structure, data formatting |
| stages.py | 🟡 MEDIUM | Multi-day aggregation, condensed displays |
| notifications.py | 🟡 MEDIUM | Channel finding, GM notification content |

**Integration Testing:** After unit testing each module, create integration tests that verify the complete flow: handler → formatters → display → notifications.

---

### 2.4 commands/river_encounter.py - Random Encounters

**File:** [commands/river_encounter.py](commands/river_encounter.py:1)
**Existing Tests:** `tests/test_encounter_mechanics.py`, `tests/test_encounter_data.py` ✅

#### What This File Does

1. **Validates GM permission** for encounter type override
2. **Generates encounter** via `utils.encounter_mechanics`
3. **Formats player message** (cryptic flavor)
4. **Formats GM message** (full mechanics)
5. **Sends to appropriate channels**
6. **Logs command**

#### Key Pattern: Dual-Message System

```
Player Channel (Public)
├─→ Cryptic flavor text
├─→ Emoji/atmosphere only
└─→ NO mechanical details

GM Channel (boat-travelling-notifications)
├─→ Full encounter type
├─→ Required tests & difficulties
├─→ Damage/cargo loss calculations
└─→ Mechanical effects
```

#### Testing Strategy

**Test Focus: Message Routing & Formatting**

```python
@pytest.mark.asyncio
async def test_encounter_sends_cryptic_message_to_player_channel():
    """
    GIVEN: Encounter is generated
    WHEN: Command completes
    THEN: Player receives flavor text without mechanics

    WHY: Players shouldn't see mechanical details
    """
    mock_interaction = MockInteraction()
    mock_guild = MockGuild(channels=[
        MockChannel(name="general"),
        MockChannel(name="boat-travelling-notifications")
    ])
    mock_interaction.guild = mock_guild

    await river_encounter_slash(mock_interaction, stage="Day 1", encounter_type=None)

    player_embed = mock_interaction.response.embed
    assert "stirs along the riverbank" in player_embed.description.lower()
    assert "Test:" not in player_embed.description  # No mechanical info
    assert "Damage:" not in player_embed.description

@pytest.mark.asyncio
async def test_encounter_sends_full_details_to_gm_channel():
    """
    GIVEN: Encounter is generated
    WHEN: Command completes
    THEN: GM channel receives full mechanical details

    WHY: GM needs complete info to run encounter
    """
    mock_interaction = MockInteraction()
    gm_channel = MockChannel(name="boat-travelling-notifications")
    mock_guild = MockGuild(channels=[gm_channel])
    mock_interaction.guild = mock_guild

    await river_encounter_slash(
        mock_interaction,
        stage="Day 1",
        encounter_type="accident"  # GM forcing accident
    )

    gm_message = gm_channel.sent_messages[-1]
    assert "Required Tests" in gm_message.embed.fields
    assert "Damage" in str(gm_message.embed) or "Effect" in str(gm_message.embed)
```

#### Integration Test: End-to-End

```python
@pytest.mark.integration
async def test_encounter_full_flow_from_command_to_channels():
    """
    Integration test covering full encounter flow

    GIVEN: User runs /river-encounter
    WHEN: Encounter is processed
    THEN:
      - Player message sent to interaction channel
      - GM message sent to notifications channel
      - Log entry created
      - Both messages reference same encounter

    WHY: Validates complete command pipeline
    """
    # Setup full mock environment
    mock_interaction = MockInteraction()
    log_channel = MockChannel(name="boat-travelling-log")
    gm_channel = MockChannel(name="boat-travelling-notifications")
    mock_guild = MockGuild(channels=[log_channel, gm_channel])
    mock_interaction.guild = mock_guild

    # Execute command
    await river_encounter_slash(mock_interaction, stage="Day 2")

    # Verify player message
    assert mock_interaction.response.sent
    player_embed = mock_interaction.response.embed

    # Verify GM message
    assert len(gm_channel.sent_messages) == 1
    gm_embed = gm_channel.sent_messages[0].embed

    # Verify log message
    assert len(log_channel.sent_messages) == 1

    # Verify consistency (same encounter in both messages)
    # Check encounter type matches
    assert player_embed.color == gm_embed.color  # Same severity color
```

#### Pitfall: Testing Randomness in Encounters

```python
# ❌ BAD - Flaky due to randomness
def test_encounter_returns_positive_type():
    encounter = generate_encounter()
    assert encounter["type"] == "positive"  # Random! Will fail 90% of time

# ✅ GOOD - Test distribution or use override
def test_encounter_type_distribution():
    """Test encounter types follow probability rules"""
    types = [generate_encounter()["type"] for _ in range(1000)]
    positive_count = types.count("positive")

    # Positive should be ~10% (1-10 on d100)
    assert 80 <= positive_count <= 120  # Allow variance

# ✅ GOOD - Test specific type with override
def test_encounter_override_forces_type():
    """Test GM can force specific encounter type"""
    encounter = generate_encounter(encounter_type="accident")
    assert encounter["type"] == "accident"
```

---

### 2.5 commands/help.py - Help System

**File:** [commands/help.py](commands/help.py:1)
**Existing Tests:** `tests/test_help.py` ✅

#### What This File Does

1. **Generates help embeds** (general and command-specific)
2. **Routes to correct help** based on parameter
3. **Formats examples** and usage information

#### Testing Strategy

**Focus: Content Correctness**

```python
def test_general_help_lists_all_commands():
    """
    GIVEN: User runs /help with no parameter
    WHEN: General help embed is created
    THEN: All main commands are listed

    WHY: Users need to discover all available commands
    """
    embed = _create_general_help_embed()

    content = str(embed.to_dict())
    assert "/roll" in content
    assert "/boat-handling" in content
    assert "/weather" in content
    assert "/river-encounter" in content

def test_command_specific_help_shows_examples():
    """
    GIVEN: User runs /help roll
    WHEN: Roll-specific help is created
    THEN: Includes examples of dice notation

    WHY: Examples are critical for user understanding
    """
    embed = _create_detailed_help_embed("roll")

    content = str(embed.to_dict())
    assert "1d100" in content
    assert "3d10" in content
    assert "2d6+5" in content
```

**Low Priority:** Help system has existing tests and is low-risk.

---

## Summary: Commands Module Testing Checklist

| Command File | Existing Tests | Priority Gaps | Integration Tests Needed |
|--------------|----------------|---------------|--------------------------|
| roll.py | ✅ Unit (wfrp_mechanics) | ⚠️ Command handler | Yes - full command flow |
| boat_handling.py | ❌ None | 🔴 HIGH - All tests | Yes - weather integration |
| weather.py | ✅ Handler tests | ⚠️ Permission checks | Yes - storage → handler → display |
| river_encounter.py | ✅ Mechanics & data | ⚠️ Message routing | Yes - dual-channel system |
| help.py | ✅ Content tests | ✅ Complete | No - low risk |

### Next Section Preview

In the next section, I'll cover:
- **Database Module (`/db`)** testing patterns
- Character data, weather data, encounter data
- Weather storage (SQLite) testing strategies
- Schema migration testing

---

**Status:** Section 2 (Commands) complete. Section 3 (Database Module) in progress.

---

## 3. Database Module (`/db`)

### Module Overview
**Location:** `/db`
**Purpose:** Data storage and lookup (characters, weather tables, encounters, SQLite persistence)
**Pattern:** Mix of static data dictionaries and dynamic database operations

### File Structure
```
/db
├── __init__.py
├── character_data.py      # Static character stats (5 characters)
├── weather_data.py        # WFRP weather tables and constants
├── weather_storage.py     # SQLite persistence for journeys
└── encounter_data.py      # River encounter tables
```

---

## 3.1 db/character_data.py - Character Statistics

**File:** [db/character_data.py](db/character_data.py:1)
**Existing Tests:** `tests/test_character_data.py` ✅ **EXCELLENT COVERAGE**

### What This File Does

1. **Stores character data** (5 characters: anara, emmerich, hildric, oktavian, lupus)
2. **Provides lookup functions** (`get_character`, `get_available_characters`)
3. **Calculates boat handling skill** (Sail preferred over Row)
4. **Calculates Lore bonus** (tens digit of Lore (Riverways))

### Data Structure
```python
characters_data = {
    "anara": {
        "name": str,
        "species": str,
        "status": str,
        "characteristics": {WS, BS, S, T, I, AG, DEX, INT, WP, FEL},
        "trading_skills": {Haggle, Charm, Gossip, Bribery, Intuition, Evaluate},
        "river_travelling_skills": {Row, Sail, Navigation, Swim, Lore (Riverways), ...}
    },
    # ... 4 more characters
}
```

### Testing Strategy

**Priority:** P0 - Character data is foundational for boat handling

**Test Categories (All Implemented ✅):**

1. **Data Integrity Tests**
```python
def test_all_characters_have_required_fields():
    """
    GIVEN: Character database
    WHEN: Checking all characters
    THEN: Each has characteristics, trading_skills, river_travelling_skills

    WHY: Prevents incomplete character data from breaking commands
    """
    required_fields = ["characteristics", "trading_skills", "river_travelling_skills"]
    for char_name in get_available_characters():
        character = get_character(char_name)
        for field in required_fields:
            assert field in character
```

2. **Lookup Function Tests**
```python
def test_get_character_case_insensitive():
    """
    GIVEN: Character name in any case (ANARA, Anara, anara)
    WHEN: get_character is called
    THEN: Returns same character regardless of case

    WHY: Discord usernames may vary in capitalization
    """
    assert get_character("ANARA") == get_character("anara")
```

3. **Business Logic Tests**
```python
def test_get_boat_handling_prefers_sail():
    """
    GIVEN: Character with both Sail and Row skills
    WHEN: Determining boat handling skill
    THEN: Sail is selected (advanced skill preferred)

    WHY: WFRP rules specify Sail is the advanced skill
    """
    test_char = {
        "river_travelling_skills": {"Row": 30, "Sail": 50}
    }
    skill_name, skill_value = get_boat_handling_skill(test_char)
    assert skill_name == "Sail"
    assert skill_value == 50
```

4. **Edge Case Tests**
```python
def test_lore_riverways_bonus_zero_when_no_skill():
    """
    GIVEN: Character without Lore (Riverways)
    WHEN: Calculating lore bonus
    THEN: Returns 0 (no bonus)

    WHY: Not all characters have this skill
    """
    test_char = {"river_travelling_skills": {"Row": 30}}
    bonus = get_lore_riverways_bonus(test_char)
    assert bonus == 0
```

5. **Parameterized Tests for All Characters**
```python
@pytest.mark.parametrize("char_name", ["anara", "emmerich", "hildric", "oktavian", "lupus"])
def test_all_characters_have_boat_handling(char_name):
    """
    GIVEN: Each character in the database
    WHEN: Getting boat handling skill
    THEN: Character has either Row or Sail

    WHY: Ensures no character is missing navigation skills
    """
    char = get_character(char_name)
    skill_name, skill_value = get_boat_handling_skill(char)
    assert skill_name in ["Row", "Sail"]
    assert skill_value > 0
```

### Key Testing Patterns

**Pattern 1: Parameterized Testing for All Characters**
```python
# Instead of 5 separate tests, use parametrize
@pytest.mark.parametrize("char_name", get_available_characters())
def test_character_property(char_name):
    # Test runs once per character
    char = get_character(char_name)
    assert some_property(char)
```

**Pattern 2: Test Data Structure Integrity**
```python
def test_characteristics_structure():
    """Validate WFRP characteristic stats are complete"""
    expected_stats = ["WS", "BS", "S", "T", "I", "AG", "DEX", "INT", "WP", "FEL"]

    for char_name in get_available_characters():
        char = get_character(char_name)
        for stat in expected_stats:
            assert stat in char["characteristics"]
            assert isinstance(char["characteristics"][stat], int)
```

**Pattern 3: Test Helper Functions Independently**
```python
# Don't just test get_character
# Test the helper functions with custom data
def test_lore_bonus_calculation():
    """Test lore bonus formula with known values"""
    test_char = {"river_travelling_skills": {"Lore (Riverways)": 47}}
    bonus = get_lore_riverways_bonus(test_char)
    assert bonus == 4  # 47 // 10 = 4
```

### Use Case: Adding New Character

**Scenario:** Adding a new character "Magnus the Red" for a new player.

**TDD Workflow:**

**Step 1: Write Test (RED)**
```python
def test_magnus_character_exists():
    """Test new character Magnus is available"""
    char = get_character("magnus")
    assert char["name"] == "Magnus the Red"
    assert "characteristics" in char
    assert "river_travelling_skills" in char

def test_magnus_has_boat_handling():
    """Test Magnus can navigate"""
    char = get_character("magnus")
    skill_name, skill_value = get_boat_handling_skill(char)
    assert skill_name in ["Row", "Sail"]
    assert skill_value > 0
```

**Step 2: Add Character Data (GREEN)**
```python
# db/character_data.py
characters_data = {
    # ... existing characters ...
    "magnus": {
        "name": "Magnus the Red",
        "species": "Human",
        "status": "Silver 2",
        "characteristics": {
            "WS": 45, "BS": 40, "S": 42, "T": 38,
            "I": 50, "AG": 35, "DEX": 40, "INT": 48,
            "WP": 52, "FEL": 38
        },
        "trading_skills": {
            "Haggle": 48, "Charm": 40, "Gossip": 45,
            "Bribery": 38, "Intuition": 50
        },
        "river_travelling_skills": {
            "Row": 40, "Navigation": 50, "Perception": 55,
            "Swim": 42, "Outdoor Survival": 48, "Dodge": 40
        }
    }
}
```

**Step 3: Verify with Existing Tests (REFACTOR)**
```bash
# All existing parameterized tests automatically include Magnus!
pytest tests/test_character_data.py -v

# These tests now run for 6 characters instead of 5:
# - test_all_characters_have_required_fields
# - test_all_characters_have_boat_handling
# - test_all_characters_lore_bonus
```

### Connection Points

```
boat_handling.py
       ↓
get_character("anara")
       ↓
character_data.py
       ↓
    ┌──┴───┬────────────┐
    ↓      ↓            ↓
  name   skills   characteristics
         ↓
get_boat_handling_skill()
         ↓
    (Sail or Row)
         ↓
get_lore_riverways_bonus()
         ↓
   (tens digit)
```

### Pitfalls for character_data.py

**Pitfall 1: Hardcoding Character Names**
```python
# ❌ BAD - Breaks when characters change
def test_character_skills():
    anara = get_character("anara")
    emmerich = get_character("emmerich")
    # ... 5 separate tests

# ✅ GOOD - Scales with character list
@pytest.mark.parametrize("char_name", get_available_characters())
def test_character_skills(char_name):
    char = get_character(char_name)
    # Test applies to all characters
```

**Pitfall 2: Not Testing Error Cases**
```python
# ❌ BAD - Only tests happy path
def test_get_character():
    char = get_character("anara")
    assert char is not None

# ✅ GOOD - Tests invalid input
def test_get_invalid_character():
    with pytest.raises(ValueError, match="not found"):
        get_character("nonexistent")
```

**Pitfall 3: Testing Implementation Details**
```python
# ❌ BAD - Tests internal dictionary structure
def test_characters_data_is_dict():
    assert isinstance(characters_data, dict)
    assert "anara" in characters_data

# ✅ GOOD - Tests public API
def test_get_available_characters():
    characters = get_available_characters()
    assert "anara" in characters
```

---

## 3.2 db/weather_data.py - Weather Tables

**File:** [db/weather_data.py](db/weather_data.py:1)
**Existing Tests:** `tests/test_weather_data.py` ✅ **COMPREHENSIVE**

### What This File Does

This file contains **ONLY static data** - no database operations. It provides:

1. **Wind tables** (strength, direction, modifiers)
2. **Weather tables** (by season: dry, fair, rain, snow, etc.)
3. **Temperature tables** (by province and season)
4. **Lookup functions** (convert dice rolls to weather conditions)

### Data Categories

**Wind Data:**
- `WIND_STRENGTH`: 5 levels (calm to very strong)
- `WIND_DIRECTION`: 3 types (tailwind, sidewind, headwind)
- `WIND_MODIFIERS`: 15 combinations (strength × direction) with speed modifiers and special notes

**Weather Data:**
- `WEATHER_RANGES`: d100 tables per season
- `WEATHER_EFFECTS`: Descriptions and mechanical effects
- Special events: Cold fronts, heat waves

**Temperature Data:**
- `PROVINCE_TEMPERATURES`: Base temps for 15 provinces × 4 seasons
- `TEMPERATURE_RANGES`: d100 table with ±15°C variation

### Testing Strategy

**Priority:** P1 - Critical for weather generation accuracy

**Test Categories:**

**1. Data Completeness Tests**
```python
def test_wind_modifiers_completeness():
    """
    GIVEN: Wind strength and direction combinations
    WHEN: Checking WIND_MODIFIERS dictionary
    THEN: All 15 combinations exist (5 strengths × 3 directions)

    WHY: Missing combinations cause KeyError in weather generation
    """
    strengths = ["calm", "light", "bracing", "strong", "very_strong"]
    directions = ["tailwind", "sidewind", "headwind"]

    for strength in strengths:
        for direction in directions:
            assert (strength, direction) in WIND_MODIFIERS
            modifier_data = WIND_MODIFIERS[(strength, direction)]
            assert isinstance(modifier_data, tuple)
            assert len(modifier_data) == 2  # (speed_mod, notes)
```

**2. Range Coverage Tests**
```python
def test_weather_ranges_cover_full_d100():
    """
    GIVEN: Weather ranges for a season
    WHEN: Checking roll coverage
    THEN: All rolls 1-100 map to exactly one weather type

    WHY: Gaps or overlaps cause incorrect weather generation
    """
    for season in ["spring", "summer", "autumn", "winter"]:
        ranges = WEATHER_RANGES[season]

        # Check coverage: create set of all covered rolls
        covered_rolls = set()
        for min_roll, max_roll, weather_type in ranges:
            for roll in range(min_roll, max_roll + 1):
                assert roll not in covered_rolls, f"Overlap at {roll}"
                covered_rolls.add(roll)

        # Verify full coverage
        assert covered_rolls == set(range(1, 101))
```

**3. Lookup Function Tests**
```python
def test_wind_strength_from_roll():
    """
    GIVEN: d10 roll results
    WHEN: Converting to wind strength
    THEN: Correct strength returned per WFRP tables

    WHY: Validates dice-to-condition mapping
    """
    # Calm: 1-2
    assert get_wind_strength_from_roll(1) == "calm"
    assert get_wind_strength_from_roll(2) == "calm"

    # Light: 3-4
    assert get_wind_strength_from_roll(3) == "light"
    assert get_wind_strength_from_roll(4) == "light"

    # ... test all ranges
```

**4. Province Data Validation**
```python
def test_all_provinces_have_all_seasons():
    """
    GIVEN: Province temperature table
    WHEN: Checking each province
    THEN: All 4 seasons have temperature data

    WHY: Missing season data crashes weather generation
    """
    seasons = ["spring", "summer", "autumn", "winter"]

    for province_key, temp_data in PROVINCE_TEMPERATURES.items():
        for season in seasons:
            assert season in temp_data, f"{province_key} missing {season}"
            assert isinstance(temp_data[season], int)
```

**5. Data Integrity Tests**
```python
def test_temperature_ranges_sequential():
    """
    GIVEN: Temperature range table
    WHEN: Checking roll ranges
    THEN: Ranges are sequential with no gaps

    WHY: Gaps cause some rolls to return default values
    """
    prev_max = 0
    for min_roll, max_roll, category, modifier in TEMPERATURE_RANGES:
        assert min_roll == prev_max + 1, f"Gap before {min_roll}"
        assert min_roll <= max_roll
        prev_max = max_roll

    assert prev_max == 100  # Covers full d100
```

### Key Testing Patterns

**Pattern 1: Test Lookup Functions with Boundary Values**
```python
def test_weather_roll_boundaries():
    """Test edge cases at range boundaries"""
    # Spring: dry (1-10), fair (11-30), rain (31-90), etc.
    assert get_weather_from_roll("spring", 1) == "dry"
    assert get_weather_from_roll("spring", 10) == "dry"
    assert get_weather_from_roll("spring", 11) == "fair"  # Boundary
    assert get_weather_from_roll("spring", 30) == "fair"
    assert get_weather_from_roll("spring", 31) == "rain"  # Boundary
```

**Pattern 2: Validate Data Structure**
```python
def test_wind_modifier_tuple_structure():
    """Each modifier entry must be (str, str|None)"""
    for (strength, direction), modifier_data in WIND_MODIFIERS.items():
        assert isinstance(modifier_data, tuple)
        assert len(modifier_data) == 2

        speed_mod, notes = modifier_data
        assert isinstance(speed_mod, str)
        assert notes is None or isinstance(notes, str)
```

**Pattern 3: Test All Enum Values**
```python
def test_all_wind_strengths_have_display_names():
    """Validate all wind strengths can be displayed"""
    strengths = ["calm", "light", "bracing", "strong", "very_strong"]

    for strength in strengths:
        assert strength in WIND_STRENGTH
        display_name = WIND_STRENGTH[strength]
        assert len(display_name) > 0
        assert display_name != strength  # Should be capitalized/formatted
```

### Use Case: Adding New Province

**Scenario:** Adding "Bretonnia" province with custom temperatures.

**TDD Workflow:**

**Step 1: Write Test (RED)**
```python
def test_bretonnia_province_exists():
    """Test new Bretonnia province has temperature data"""
    provinces = get_available_provinces()
    assert "Bretonnia" in provinces

def test_bretonnia_all_seasons():
    """Test Bretonnia has data for all seasons"""
    seasons = ["spring", "summer", "autumn", "winter"]
    for season in seasons:
        temp = get_province_base_temperature("bretonnia", season)
        assert isinstance(temp, int)
        assert -20 <= temp <= 40  # Reasonable temperature range
```

**Step 2: Add Province Data (GREEN)**
```python
# db/weather_data.py
PROVINCE_TEMPERATURES = {
    # ... existing provinces ...
    "bretonnia": {
        "spring": 11,
        "summer": 22,
        "autumn": 13,
        "winter": 4
    }
}
```

**Step 3: Existing Tests Validate (REFACTOR)**
```python
# Existing test automatically checks new province!
def test_all_provinces_have_all_seasons():
    # Now tests 16 provinces instead of 15
    for province_key, temp_data in PROVINCE_TEMPERATURES.items():
        # ... validation runs for Bretonnia too
```

### Connection Points

```
weather_mechanics.py (generation)
           ↓
    Roll d100 for weather
           ↓
get_weather_from_roll(season, 53)
           ↓
    WEATHER_RANGES["summer"]
           ↓
    Returns "rain"
           ↓
    WEATHER_EFFECTS["rain"]
           ↓
    {name, description, effects}
```

### Pitfalls for weather_data.py

**Pitfall 1: Not Testing Range Gaps**
```python
# ❌ BAD - Doesn't catch gaps
def test_weather_ranges_exist():
    assert "spring" in WEATHER_RANGES
    assert len(WEATHER_RANGES["spring"]) > 0

# ✅ GOOD - Ensures complete coverage
def test_weather_ranges_no_gaps():
    covered = set()
    for min_r, max_r, _ in WEATHER_RANGES["spring"]:
        covered.update(range(min_r, max_r + 1))
    assert covered == set(range(1, 101))
```

**Pitfall 2: Not Testing All Combinations**
```python
# ❌ BAD - Only tests one combination
def test_wind_modifier():
    mod = WIND_MODIFIERS[("calm", "tailwind")]
    assert mod is not None

# ✅ GOOD - Tests all 15 combinations exist
def test_all_wind_combinations_exist():
    for strength in STRENGTHS:
        for direction in DIRECTIONS:
            assert (strength, direction) in WIND_MODIFIERS
```

**Pitfall 3: Hardcoding Expected Values**
```python
# ❌ BAD - Brittle if data changes
def test_reikland_summer():
    assert PROVINCE_TEMPERATURES["reikland"]["summer"] == 21

# ✅ GOOD - Tests properties, not exact values
def test_reikland_summer_temperature_reasonable():
    temp = PROVINCE_TEMPERATURES["reikland"]["summer"]
    assert 15 <= temp <= 30  # Summer should be warm
    # Winter should be colder than summer
    assert temp > PROVINCE_TEMPERATURES["reikland"]["winter"]
```

---

## 3.3 db/weather_storage.py - SQLite Persistence

**File:** [db/weather_storage.py](db/weather_storage.py:1)
**Existing Tests:** `tests/test_weather_storage.py`, `tests/test_weather_storage_schema.py` ✅ **EXCELLENT**

### What This File Does

**Critical Database Operations:**
1. **Journey management** (start, end, get state)
2. **Daily weather persistence** (save, retrieve)
3. **Day/stage advancement** (increment counters)
4. **Schema migrations** (add columns safely)
5. **Cooldown tracking** (special events)

### Database Schema

**Table: guild_weather_state**
```sql
CREATE TABLE guild_weather_state (
    guild_id TEXT PRIMARY KEY,
    current_day INTEGER DEFAULT 1,
    current_stage INTEGER DEFAULT 1,
    stage_duration INTEGER DEFAULT 3,
    stage_display_mode TEXT DEFAULT 'simple',
    journey_start_date TEXT,
    last_weather_date TEXT,
    season TEXT NOT NULL,
    province TEXT NOT NULL,
    days_since_last_cold_front INTEGER DEFAULT 99,
    days_since_last_heat_wave INTEGER DEFAULT 99
)
```

**Table: daily_weather**
```sql
CREATE TABLE daily_weather (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL,
    day_number INTEGER NOT NULL,
    generated_at TEXT NOT NULL,
    season TEXT NOT NULL,
    province TEXT NOT NULL,
    wind_timeline TEXT NOT NULL,  -- JSON
    weather_type TEXT NOT NULL,
    weather_roll INTEGER NOT NULL,
    temperature_actual INTEGER NOT NULL,
    temperature_category TEXT NOT NULL,
    temperature_roll INTEGER NOT NULL,
    cold_front_days_remaining INTEGER DEFAULT 0,
    cold_front_total_duration INTEGER DEFAULT 0,
    heat_wave_days_remaining INTEGER DEFAULT 0,
    heat_wave_total_duration INTEGER DEFAULT 0,
    UNIQUE(guild_id, day_number),
    FOREIGN KEY(guild_id) REFERENCES guild_weather_state(guild_id)
)
```

### Testing Strategy

**Priority:** P0 - Database corruption breaks entire weather system

**Test Approach: Use In-Memory Database**
```python
@pytest.fixture
def storage():
    """Create temporary test database"""
    return WeatherStorage(":memory:")  # No file creation
```

**Test Categories:**

**1. Schema Tests**
```python
def test_database_tables_created(storage):
    """
    GIVEN: New WeatherStorage instance
    WHEN: Database is initialized
    THEN: Both tables exist with correct schema

    WHY: Schema errors prevent all database operations
    """
    # Try basic operations to verify tables exist
    journey = storage.get_journey_state("test")
    assert journey is None  # No data, but no error

    # Verify we can save data
    storage.start_journey("test", "summer", "reikland")
    journey = storage.get_journey_state("test")
    assert journey is not None
```

**2. CRUD Operation Tests**
```python
def test_save_and_retrieve_weather(storage):
    """
    GIVEN: Active journey
    WHEN: Weather data is saved and retrieved
    THEN: All fields match exactly (including JSON wind_timeline)

    WHY: Data integrity is critical for weather system
    """
    storage.start_journey("guild123", "summer", "reikland")

    weather_data = {
        "season": "summer",
        "province": "reikland",
        "wind_timeline": [
            {"time": "Dawn", "strength": "light", "direction": "tailwind"},
            {"time": "Midday", "strength": "bracing", "direction": "sidewind"},
        ],
        "weather_type": "fair",
        "weather_roll": 50,
        "temperature_actual": 21,
        "temperature_category": "average",
        "temperature_roll": 45,
        "cold_front_days_remaining": 0,
        "heat_wave_days_remaining": 0,
    }

    storage.save_daily_weather("guild123", 1, weather_data)
    retrieved = storage.get_daily_weather("guild123", 1)

    assert retrieved["season"] == "summer"
    assert retrieved["wind_timeline"] == weather_data["wind_timeline"]  # JSON parsed correctly
    assert retrieved["temperature_actual"] == 21
```

**3. Migration Tests**
```python
def test_schema_migration_adds_new_columns(temp_db):
    """
    GIVEN: Database created with old schema (missing columns)
    WHEN: WeatherStorage is initialized
    THEN: New columns are added without losing data

    WHY: Schema changes must not break existing journeys
    """
    # Create old-style database
    old_storage = WeatherStorage(temp_db)
    old_storage.start_journey("guild123", "summer", "reikland")
    old_storage.save_daily_weather("guild123", 1, sample_weather_data)

    # Simulate migration: create new storage instance
    # (init_database runs migrations)
    new_storage = WeatherStorage(temp_db)

    # Verify old data still exists
    journey = new_storage.get_journey_state("guild123")
    assert journey["season"] == "summer"

    # Verify new columns exist with defaults
    assert "stage_duration" in journey
    assert journey["stage_duration"] == 3  # Default value
```

**4. Isolation Tests (Multi-Guild)**
```python
def test_multiple_guilds_isolated(storage):
    """
    GIVEN: Multiple guilds with different journeys
    WHEN: Each guild saves/retrieves data
    THEN: Data does not leak between guilds

    WHY: Guild isolation is critical for Discord bots
    """
    storage.start_journey("guild_A", "summer", "reikland")
    storage.start_journey("guild_B", "winter", "kislev")

    journey_A = storage.get_journey_state("guild_A")
    journey_B = storage.get_journey_state("guild_B")

    assert journey_A["season"] == "summer"
    assert journey_B["season"] == "winter"
    assert journey_A["season"] != journey_B["season"]
```

**5. Atomic Operation Tests**
```python
def test_start_journey_clears_old_data(storage):
    """
    GIVEN: Guild with existing journey and weather data
    WHEN: start_journey is called again
    THEN: Old journey AND old weather are deleted atomically

    WHY: Prevents data corruption from mixing old/new journey data
    """
    # First journey
    storage.start_journey("guild123", "summer", "reikland")
    storage.save_daily_weather("guild123", 1, sample_weather)
    storage.save_daily_weather("guild123", 2, sample_weather)

    # Start new journey
    storage.start_journey("guild123", "winter", "kislev")

    # Old data should be gone
    assert storage.get_daily_weather("guild123", 1) is None
    assert storage.get_daily_weather("guild123", 2) is None

    # New journey should exist
    journey = storage.get_journey_state("guild123")
    assert journey["season"] == "winter"
    assert journey["current_day"] == 1  # Reset
```

**6. Edge Case Tests**
```python
def test_get_nonexistent_journey_returns_none(storage):
    """
    GIVEN: Guild ID that has never started a journey
    WHEN: get_journey_state is called
    THEN: Returns None without error

    WHY: Commands must handle "no active journey" gracefully
    """
    journey = storage.get_journey_state("nonexistent_guild")
    assert journey is None

def test_advance_day_without_journey_returns_zero(storage):
    """
    GIVEN: Guild with no active journey
    WHEN: advance_day is called
    THEN: Returns 0 without crashing

    WHY: Prevents crashes if command called out of order
    """
    new_day = storage.advance_day("nonexistent_guild")
    assert new_day == 0
```

### Key Testing Patterns

**Pattern 1: Use Fixtures for Database Setup**
```python
@pytest.fixture
def temp_db():
    """Create temporary database file"""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    os.unlink(path)  # Cleanup

@pytest.fixture
def storage(temp_db):
    """Create storage instance with temp DB"""
    return WeatherStorage(db_path=temp_db)

# Tests can now use clean database
def test_something(storage):
    # storage is a fresh WeatherStorage instance
    pass
```

**Pattern 2: Test JSON Serialization**
```python
def test_wind_timeline_json_roundtrip(storage):
    """
    GIVEN: Complex wind timeline structure
    WHEN: Saved to database and retrieved
    THEN: Structure matches exactly (no JSON corruption)

    WHY: Wind timeline is stored as JSON TEXT column
    """
    wind_timeline = [
        {"time": "Dawn", "strength": "calm", "direction": "tailwind", "changed": False},
        {"time": "Midday", "strength": "light", "direction": "sidewind", "changed": True},
    ]

    weather_data = {
        "wind_timeline": wind_timeline,
        # ... other fields
    }

    storage.start_journey("guild123", "summer", "reikland")
    storage.save_daily_weather("guild123", 1, weather_data)
    retrieved = storage.get_daily_weather("guild123", 1)

    # Verify exact structure match
    assert retrieved["wind_timeline"] == wind_timeline
    assert retrieved["wind_timeline"][1]["changed"] == True  # Boolean preserved
```

**Pattern 3: Test Schema Changes**
```python
def test_schema_has_required_columns(storage):
    """
    GIVEN: WeatherStorage initialized
    WHEN: Checking schema
    THEN: All required columns exist

    WHY: Catches schema definition errors early
    """
    # Get column names from table
    columns = storage._get_table_columns("guild_weather_state")

    required_columns = [
        "guild_id", "current_day", "season", "province",
        "stage_duration", "stage_display_mode",
        "days_since_last_cold_front", "days_since_last_heat_wave"
    ]

    for col in required_columns:
        assert col in columns, f"Missing column: {col}"
```

### Use Case: Adding New Schema Column

**Scenario:** Add `journey_name` column to let users name their journeys.

**TDD Workflow:**

**Step 1: Write Tests (RED)**
```python
def test_journey_name_column_exists(storage):
    """Test new journey_name column exists"""
    columns = storage._get_table_columns("guild_weather_state")
    assert "journey_name" in columns

def test_journey_name_stored_and_retrieved(storage):
    """Test journey name can be saved and retrieved"""
    storage.start_journey("guild123", "summer", "reikland", journey_name="Epic Quest")

    journey = storage.get_journey_state("guild123")
    assert journey["journey_name"] == "Epic Quest"

def test_journey_name_defaults_to_none(storage):
    """Test journey_name defaults to None if not provided"""
    storage.start_journey("guild123", "summer", "reikland")  # No name

    journey = storage.get_journey_state("guild123")
    assert journey["journey_name"] is None
```

**Step 2: Add Schema Migration (GREEN)**
```python
# db/weather_storage.py

def init_database(self):
    """Create tables if they don't exist."""
    with self._get_connection() as conn:
        cursor = conn.cursor()

        # Create main table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS guild_weather_state (
                guild_id TEXT PRIMARY KEY,
                -- ... existing columns ...
                journey_name TEXT DEFAULT NULL
            )
        """)

        # Migration: Add column if it doesn't exist
        try:
            cursor.execute("""
                ALTER TABLE guild_weather_state
                ADD COLUMN journey_name TEXT DEFAULT NULL
            """)
        except sqlite3.OperationalError:
            # Column already exists
            pass
```

**Step 3: Update start_journey Method**
```python
def start_journey(self, guild_id: str, season: str, province: str,
                  journey_name: str = None, stage_duration: int = 3):
    """Start a new journey with optional name."""
    with self._get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO guild_weather_state
            (guild_id, season, province, journey_name, stage_duration, ...)
            VALUES (?, ?, ?, ?, ?, ...)
        """, (guild_id, season, province, journey_name, stage_duration, ...))
```

**Step 4: Test Migration with Existing Data**
```python
def test_migration_preserves_existing_journeys(temp_db):
    """
    GIVEN: Database with existing journeys (old schema, no journey_name)
    WHEN: Schema migration runs
    THEN: Existing journeys still work, journey_name defaults to NULL

    WHY: Production databases have existing data
    """
    # Create old schema database
    old_storage = WeatherStorage(temp_db)
    old_storage.start_journey("guild123", "summer", "reikland")

    # Trigger migration (new storage instance)
    new_storage = WeatherStorage(temp_db)

    # Old journey should still work
    journey = new_storage.get_journey_state("guild123")
    assert journey["season"] == "summer"
    assert journey["journey_name"] is None  # Default for old data
```

### Connection Points

```
Commands (weather.py, boat_handling.py)
              ↓
    storage.get_journey_state(guild_id)
              ↓
       guild_weather_state table
              ↓
    {current_day, season, province, ...}
              ↓
    storage.get_daily_weather(guild_id, day)
              ↓
       daily_weather table
              ↓
    {wind_timeline, temperature, ...}
              ↓
    modifier_calculator.get_active_weather_modifiers()
```

### Pitfalls for weather_storage.py

**Pitfall 1: Not Using Transactions**
```python
# ❌ BAD - start_journey might delete old data but fail to insert new
def start_journey(self, guild_id, season, province):
    cursor.execute("DELETE FROM guild_weather_state WHERE guild_id = ?", (guild_id,))
    cursor.execute("DELETE FROM daily_weather WHERE guild_id = ?", (guild_id,))
    # If this fails, data is lost!
    cursor.execute("INSERT INTO guild_weather_state ...")

# ✅ GOOD - Use context manager for transactions
def start_journey(self, guild_id, season, province):
    with self._get_connection() as conn:  # Auto-commits or rolls back
        cursor = conn.cursor()
        cursor.execute("DELETE ...")
        cursor.execute("DELETE ...")
        cursor.execute("INSERT ...")
```

**Pitfall 2: Not Testing with Real File (Only :memory:)**
```python
# ❌ BAD - Only tests in-memory database
@pytest.fixture
def storage():
    return WeatherStorage(":memory:")

# ✅ GOOD - Also test with file database
@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    os.unlink(path)

@pytest.fixture
def storage(temp_db):
    return WeatherStorage(db_path=temp_db)  # Real file
```

**Pitfall 3: Not Testing Migration Edge Cases**
```python
# ❌ BAD - Only tests fresh database
def test_new_database():
    storage = WeatherStorage(":memory:")
    storage.start_journey("guild", "summer", "reikland")

# ✅ GOOD - Tests migration from old schema
def test_migration_from_old_schema(temp_db):
    # Create old schema manually
    conn = sqlite3.connect(temp_db)
    conn.execute("CREATE TABLE guild_weather_state (guild_id TEXT PRIMARY KEY, season TEXT)")
    conn.execute("INSERT INTO guild_weather_state VALUES ('guild1', 'summer')")
    conn.close()

    # Initialize new storage (triggers migration)
    storage = WeatherStorage(temp_db)

    # Old data should still be accessible
    journey = storage.get_journey_state("guild1")
    assert journey["season"] == "summer"
    assert "stage_duration" in journey  # New column with default
```

---

## Summary: Database Module Testing Checklist

| File | Data Type | Test Priority | Key Focus |
|------|-----------|---------------|-----------|
| character_data.py | Static dict | P0 | Data integrity, helper functions, parameterized tests |
| weather_data.py | Static tables | P1 | Range coverage, all combinations exist, lookup functions |
| weather_storage.py | SQLite CRUD | P0 | Schema migrations, transactions, JSON serialization, guild isolation |
| encounter_data.py | Static tables | P1 | (Similar to weather_data.py patterns) |

**Key Takeaways:**
1. **Static data files:** Test completeness, coverage, and lookup functions
2. **Database files:** Test CRUD, migrations, isolation, and edge cases
3. **Use in-memory databases** for fast tests
4. **Test migrations** with existing data
5. **Parameterize tests** for all characters/provinces/seasons

---

**Status:** Section 3 (Database Module) complete.

---

## 4. Utils Module (`/utils`)

### Module Overview
**Location:** `/utils`
**Purpose:** Core game mechanics and business logic (dice, WFRP rules, weather, encounters)
**Pattern:** Pure functions and calculations (highly testable)

### File Structure
```
/utils
├── wfrp_mechanics.py      # WFRP dice rolling and success level calculations
├── modifier_calculator.py  # Extract weather modifiers for boat handling
├── weather_mechanics.py    # Weather generation algorithms
└── encounter_mechanics.py  # River encounter generation
```

**Key Characteristic:** Utils contain **pure business logic** - no Discord API, no database writes. Perfect candidates for unit testing.

---

## 4.1 utils/wfrp_mechanics.py - WFRP Game Rules

**File:** [utils/wfrp_mechanics.py](utils/wfrp_mechanics.py:1)
**Existing Tests:** `tests/test_wfrp_mechanics.py`, `tests/test_dice.py` ✅ **EXCELLENT COVERAGE**

### What This File Does

Implements **core WFRP 4th Edition rules**:
- Dice notation parsing, dice rolling, Success Level calculation
- Doubles detection (crits/fumbles), difficulty naming, success level naming

### Testing Strategy

**Priority:** P0 - Core game mechanics must be 100% correct

Focus on testing business rules, formulas, edge cases, and input validation. Test properties of random results, not exact values. Use parameterized tests for comprehensive coverage of all dice combinations, SL calculations, and doubles scenarios.

### What NOT to Test

❌ Don't test Python standard library (random, re modules)
❌ Don't verify exact die roll results (non-deterministic)

✅ DO test: Input parsing, mathematical formulas, business rules, edge cases

---

## 4.2 utils/modifier_calculator.py - Weather Integration

**File:** [utils/modifier_calculator.py](utils/modifier_calculator.py:1)
**Existing Tests:** `tests/test_modifier_calculator.py` ⚠️ **NEEDS EXPANSION**

### What This File Does

**Bridges weather and boat handling systems**: Fetches active weather, extracts wind conditions for time of day, converts to test modifiers, identifies special conditions, formats for display.

### Testing Strategy

**Priority:** P1 - Critical for boat_handling command accuracy

Test integration between storage and modifiers, data extraction and transformation, edge cases (no weather, invalid time), and formatting output. Use in-memory databases for integration tests.

### What NOT to Test

❌ Don't test WeatherStorage internals
❌ Don't test weather generation
❌ Don't test WIND_MODIFIERS data

✅ DO test: Integration points, data transformations, edge cases, display formatting

---

## Summary: Utils Module Testing Checklist

| File | Test Priority | Key Focus | Coverage Target |
|------|--------------|-----------|-----------------|
| wfrp_mechanics.py | P0 | Pure functions, WFRP rules accuracy | 100% |
| modifier_calculator.py | P1 | Integration, data extraction | 90%+ |
| weather_mechanics.py | P1 | Weather generation algorithms | 85%+ |
| encounter_mechanics.py | P1 | Encounter generation, calculations | 85%+ |

**Key Takeaways for Utils Testing:**
1. Pure functions = Easy to test, aim for 100% coverage
2. Test business rules thoroughly
3. Test properties, not exact random values
4. Parameterize tests for comprehensive coverage
5. Integration points need careful mocking

---

**Status:** Sections 1-4 complete. Document now covers main.py, Commands, Database, and Utils modules with comprehensive TDD guidelines.
