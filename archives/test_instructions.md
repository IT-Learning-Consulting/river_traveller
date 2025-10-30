🧪 Test-Driven Development Instructions for Weather System Implementation
Your Role
You are implementing a weather event system for a Discord bot using Test-Driven Development (TDD). Your primary directive is to make tests pass while maintaining clean, maintainable code. Tests are your specification - they define what "correct" means.
Core Principles You Must Follow
1. Tests Are Your Contract

Never modify a test to make code pass (unless the test itself is wrong)
If a test fails, the code is wrong, not the test
All existing passing tests must remain green when adding new features
If you're unsure about requirements, ask before implementing

2. Red-Green-Refactor Cycle
For each feature:

RED: Run tests, confirm they fail (proves test works)
GREEN: Write minimal code to make tests pass
REFACTOR: Clean up code while keeping tests green

3. Isolation and Dependencies

Test each function independently using mocks/patches
Mock external dependencies (database, Discord API, random.randint)
Each test should be runnable in isolation
Use fixtures for common setup

4. Clear Communication
When you implement:

State which tests you're targeting
Explain your approach briefly
Show which tests pass/fail after changes
Flag any assumptions you're making


Project Context
What We're Building
A weather event system for a Warhammer Fantasy Roleplay Discord bot that:

Generates daily weather with temperature variations
Triggers rare weather events (Cold Fronts at 1% chance, Heat Waves at 1% chance)
Tracks event duration with proper day counters ("Day 2 of 5")
Prevents event overlap (mutual exclusivity)
Implements cooldown periods after events end
Adds daily temperature variation within events for realism

Current Problems We're Fixing

❌ Display shows formulas instead of actual values ("1d5 days" instead of "3 days")
❌ Total duration not stored - only countdown exists, so can't show "Day X of Y"
❌ No cooldown mechanism - events can trigger back-to-back unrealistically
❌ Events can overlap - cold front and heat wave can occur simultaneously
❌ No daily variation during events - temperature is static for entire event duration
❌ Hard to test - requires waiting for rare random rolls

Key Technical Details
Event Mechanics:

Cold Front: Triggered on roll=2 (d100), lasts 1-5 days, applies -10°C modifier
Heat Wave: Triggered on roll=99 (d100), lasts 11-20 days, applies +10°C modifier
Cooldown: 7 days after event ends before another can trigger
Mutual Exclusivity: Only one event type can be active at a time

Daily Temperature Variation (NEW FEATURE):

Base temperature calculated from region/season
Event modifier applies (-10°C for cold front, +10°C for heat wave)
Daily roll (d100) adds variation: ±5°C based on category (low/average/high)
Final temperature determines display category (cool, mild, hot, etc.)
Special rolls (2, 99) are suppressed during active events to prevent nesting

Database Schema Changes:
python# daily_weather table
cold_front_days_remaining: int      # Countdown: 3, 2, 1, 0
cold_front_total_duration: int      # NEW: Stores original roll (e.g., 3)
heat_wave_days_remaining: int       # Countdown: 15, 14, 13...
heat_wave_total_duration: int       # NEW: Stores original roll (e.g., 15)

# guild_weather_state table
days_since_last_cold_front: int     # NEW: Cooldown counter
days_since_last_heat_wave: int      # NEW: Cooldown counter

Implementation Plan: File-by-File Approach
You will implement in this order:
Phase 1: Database Layer (db/weather_storage.py)
Changes:

Add 4 new columns to schema
Add migration logic with DEFAULT values
Add methods to get/set cooldown counters

Tests to Pass:
python- test_new_columns_exist_after_migration()
- test_store_cold_front_saves_both_remaining_and_total()
- test_fetch_weather_returns_cooldown_fields()
- test_migration_preserves_active_events()

Phase 2: Core Mechanics (utils/weather_mechanics.py)
⚠️ HIGHEST COMPLEXITY - Most Critical Testing
Changes:

Update handle_cold_front() signature to return (modifier, remaining, total)
Add cooldown checking before triggering new events
Add mutual exclusivity checks
Implement daily temperature variation during events
Suppress special rolls (2, 99) during active events
Add get_category_from_actual_temp() helper function

Critical Tests to Pass:
Event Triggering:
pythondef test_cold_front_triggers_on_roll_2_when_cooldown_expired():
    """Cold front starts when roll=2 and cooldown > 7 days"""
    modifier, remaining, total = handle_cold_front(
        roll=2,
        current_days=0,
        cooldown_days=8
    )
    assert modifier == -10
    assert 1 <= remaining <= 5  # Duration is 1-5 days
    assert remaining == total  # First day

def test_cold_front_blocked_during_cooldown():
    """Cold front cannot trigger during 7-day cooldown"""
    modifier, remaining, total = handle_cold_front(
        roll=2,
        current_days=0,
        cooldown_days=3  # Only 3 days since last event
    )
    assert modifier == 0
    assert remaining == 0
    assert total == 0

def test_cold_front_blocked_when_heat_wave_active():
    """Mutual exclusivity: cold front blocked if heat wave active"""
    modifier, remaining, total = handle_cold_front(
        roll=2,
        current_days=0,
        cooldown_days=99,
        active_heat_wave=True  # Heat wave currently active
    )
    assert modifier == 0
    assert remaining == 0
    assert total == 0

def test_roll_2_suppressed_during_active_cold_front():
    """CRITICAL: Prevents nested events! Roll=2 during cold front acts like roll=3"""
    modifier, remaining, total = handle_cold_front(
        roll=2,  # Special roll
        current_days=2,  # Cold front already active (2 days remaining)
        cooldown_days=0
    )
    # Should decrement existing event, NOT trigger new one
    assert remaining == 1  # 2 - 1 = 1 day left
    assert total == 3  # Preserves original duration
    assert modifier == -10  # Event still active
Daily Temperature Variation:
pythondef test_daily_variation_during_cold_front_average_roll():
    """Cold front + average roll = base - 10 + 0"""
    base_temp = 21  # Reikland summer
    
    temp, category = roll_temperature_with_special_events(
        base_temp=21,
        roll=45,  # Average roll (no modifier)
        active_cold_front=True,
        cold_front_remaining=2,
        cold_front_total=3
    )
    
    assert temp == 11  # 21 - 10 + 0
    assert category == "cool"

def test_daily_variation_during_cold_front_low_roll():
    """Cold front + low roll = base - 10 - 5"""
    temp, category = roll_temperature_with_special_events(
        base_temp=21,
        roll=15,  # Low roll (-5 modifier)
        active_cold_front=True,
        cold_front_remaining=2,
        cold_front_total=3
    )
    
    assert temp == 6  # 21 - 10 - 5
    assert category == "very_cool"

def test_daily_variation_during_cold_front_high_roll():
    """Cold front + high roll = base - 10 + 5"""
    temp, category = roll_temperature_with_special_events(
        base_temp=21,
        roll=85,  # High roll (+5 modifier)
        active_cold_front=True,
        cold_front_remaining=2,
        cold_front_total=3
    )
    
    assert temp == 16  # 21 - 10 + 5
    assert category == "mild"

def test_special_roll_during_cold_front_treated_as_normal():
    """Roll=2 during cold front should act like roll=3 (no new event)"""
    temp, category = roll_temperature_with_special_events(
        base_temp=21,
        roll=2,  # Would normally trigger cold front
        active_cold_front=True,  # But one is already active
        cold_front_remaining=1,
        cold_front_total=3
    )
    
    # Should treat as roll=3 (very low, but not special)
    assert temp == 6  # 21 - 10 - 5 (very low category)
    # Should NOT trigger nested cold front event
Category Recalculation:
pythondef test_get_category_from_actual_temp_correctly_maps():
    """Category must be based on FINAL temp, not base temp"""
    base_temp = 21  # Reikland summer (would be "average" normally)
    
    # After cold front: 21 - 10 = 11°C
    category = get_category_from_actual_temp(
        actual_temp=11,
        base_temp=21
    )
    
    # 11°C is 10° below base (21°C)
    assert category == "cool"  # NOT "average"

Phase 3: Handler Integration (commands/weather_modules/handler.py)
Changes:

Track cooldown counters and pass to mechanics functions
Update storage after event changes
Reset cooldown when events end

Tests to Pass:
python- test_cooldown_starts_when_event_ends()
- test_cooldown_increments_daily()
- test_handler_passes_cooldown_to_mechanics()

Phase 4: Display Updates (stages.py, notifications.py)
Changes:

Display "Day X of Y" in stage summaries
Add special events section to GM notifications
Show final temperature category (not base)

Tests to Pass:
python- test_day_counter_displays_in_stage_view()
- test_final_day_shows_final_day_marker()
- test_gm_notification_includes_event_progress()
```

---

## Critical Edge Cases You MUST Handle

### 1. **The Nesting Bug** (Highest Priority)
```
Scenario: Roll=2 occurs during an active cold front
WRONG: Start new cold front (nested event)
RIGHT: Treat as roll=3, continue existing event
```

### 2. **The Overlap Bug**
```
Scenario: Heat wave active, roll=2 occurs
WRONG: Start cold front alongside heat wave
RIGHT: Block cold front trigger, continue heat wave
```

### 3. **The Zero-Day Edge Case**
```
Scenario: Cold front rolls duration=1 (only 1 day)
Display: "Cold Front: Day 1 of 1 (Final Day)"
NOT: "Day 1 of 1" then "Day 2 of 1" (impossible)
```

### 4. **The Migration Bug**
```
Scenario: Existing database has active cold front (remaining=3) but no total
WRONG: Crash or show "Day 3 of 0"
RIGHT: Set total=remaining (conservative estimate)
```

### 5. **The Category Mismatch Bug**
```
Scenario: Cold front active, final temp = 16°C
WRONG: Display "very_low" (based on event name)
RIGHT: Display "mild" (based on actual 16°C)

Test Writing Guidelines
Structure Each Test Like This:
pythondef test_specific_behavior_under_specific_conditions():
    """
    GIVEN: Initial state and preconditions
    WHEN: Action or function call
    THEN: Expected outcome
    """
    # Arrange - Set up test data
    
    # Act - Call function under test
    
    # Assert - Verify expectations
Use Mocking for Deterministic Tests:
pythonfrom unittest.mock import patch

def test_cold_front_duration_is_stored():
    # Control randomness for predictable tests
    with patch('random.randint', return_value=3):
        modifier, remaining, total = handle_cold_front(roll=2, ...)
        assert total == 3  # We know it rolled 3

Test One Thing Per Test:
python# GOOD: Single responsibility
def test_cold_front_decrements_remaining_days()
def test_cold_front_preserves_total_duration()

# BAD: Testing too much at once
def test_cold_front_everything()
```

---

## Implementation Workflow

For each phase, follow this process:

### Step 1: Review Tests
```
I will provide you with 3-5 test functions.
Read them carefully and confirm you understand what they're testing.
Ask clarifying questions if any test is ambiguous.
```

### Step 2: Implement to Pass Tests
```
Write minimal code to make tests pass.
Focus on one test at a time if needed.
Do not add features not covered by tests.
```

### Step 3: Report Results
```
After implementing, tell me:
- Which tests now pass ✅
- Which tests still fail ❌
- Any assumptions you made
- Any edge cases you're worried about
```

### Step 4: Refactor (Only When Green)
```
Once all tests pass:
- Suggest improvements to code structure
- Remove duplication
- Improve naming
- But NEVER break passing tests

!Be systematic

Code Style Requirements
Function Signatures Must Match Exactly:
python# OLD signature (wrong)
def handle_cold_front(roll, current_days):
    return modifier, remaining

# NEW signature (correct)
def handle_cold_front(roll, current_days, cooldown_days, active_heat_wave=False):
    return modifier, remaining, total
Use Type Hints:
pythondef handle_cold_front(
    roll: int,
    current_days: int,
    cooldown_days: int,
    active_heat_wave: bool = False
) -> tuple[int, int, int]:
    """Returns (modifier, remaining_days, total_duration)"""
Add Docstrings for Complex Logic:
pythondef get_category_from_actual_temp(actual_temp: int, base_temp: int) -> str:
    """
    Determine temperature category based on actual temperature.
    
    This is crucial during weather events where actual temp differs from base.
    Example: Base=21°C, Cold Front active, Final=11°C → Returns "cool" not "average"
    
    Args:
        actual_temp: Final temperature after all modifiers
        base_temp: Base regional/seasonal temperature
        
    Returns:
        Category string: "extremely_low", "very_low", "cool", "average", etc.
    """

Error Handling
You Must Handle These Cases:
python# 1. Invalid roll values
if roll < 1 or roll > 100:
    raise ValueError(f"Roll must be 1-100, got {roll}")

# 2. Negative days
if current_days < 0:
    raise ValueError(f"Days cannot be negative, got {current_days}")

# 3. Database migration failures
try:
    db.execute(migration_sql)
except sqlite3.OperationalError as e:
    if "duplicate column" in str(e):
        pass  # Column already exists, migration already ran
    else:
        raise
```

---

## Red Flags to Watch For

### 🚨 Stop and Ask If You're About To:
- Modify a test to make code pass (test might be correct, code wrong)
- Add a feature not covered by any test
- Change a function signature without updating all callers
- Ignore a failing test ("I'll fix it later")
- Use actual random.randint in tests (makes tests non-deterministic)
- Write code that passes tests but violates the spec

### ✅ Good Signs You're On Track:
- All tests pass and are green
- Code is simple and readable
- Each function has a single clear purpose
- Edge cases are explicitly handled
- You can explain why each test exists

---

## When You Get Stuck

### If Tests Won't Pass:
1. Check test expectations - are they correct?
2. Add print statements to see actual vs expected values
3. Simplify the implementation - remove complexity
4. Ask: "What's the simplest code that makes this test pass?"

### If You're Unsure About Requirements:
1. Look at the test name and docstring
2. Check the "Project Context" section above
3. Ask me: "Should X behavior do Y or Z when condition Q?"

### If Tests Contradict Each Other:
1. Point out the contradiction
2. Suggest which interpretation makes more sense
3. Wait for clarification before proceeding

---

## Success Criteria

### You've Succeeded When:
- ✅ All provided tests pass
- ✅ No existing functionality breaks
- ✅ Code is clean and well-documented
- ✅ Edge cases are handled gracefully
- ✅ Function signatures match spec
- ✅ You can explain the code's behavior confidently

### Definition of "Done":
```
A feature is done when:
1. All tests for that feature are green
2. All previous tests remain green
3. Code is committed and documented
4. You've confirmed edge cases work

First Task
I will provide you with test cases for Phase 1: Database Layer. Your job is to:

Read the tests carefully
Implement changes to db/weather_storage.py to make them pass
Report which tests pass/fail
Fix any failing tests
Confirm all green before moving to Phase 2

Remember: Tests define correctness. If the test is green, the code is correct. If the test is red, the code needs fixing.
Are you ready to begin? Please confirm you understand these instructions and ask any clarifying questions about the approach.