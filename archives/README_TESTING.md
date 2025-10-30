# Weather System Testing Guide - TDD Approach

## Overview

This document explains the Test-Driven Development (TDD) approach for implementing the weather event system improvements. All tests are written **before** implementation to guide AI-assisted coding and prevent bugs.

## Why TDD for This Project?

### The AI Context Problem

When using AI to implement large features:
- **Context window limits**: AI can't see all interconnected files at once
- **Assumption drift**: Each session might make different assumptions
- **Subtle state bugs**: Complex interactions (cooldowns + events + variation) easy to break

### How Tests Guide AI

1. **Executable specifications**: Tests define exact behavior
2. **Regression prevention**: AI can't break existing features without failing tests
3. **Iterative refinement**: "Make test X pass" is clearer than vague requirements
4. **Living documentation**: Future sessions understand intent from tests

## Test Structure

```
tests/
├── conftest.py                        # Shared fixtures and helpers
├── test_weather_storage_schema.py     # Phase 1: Database tests
├── test_weather_mechanics_events.py   # Phase 2: Core logic tests (CRITICAL)
├── test_handler_integration.py        # Phase 3: Integration tests
└── test_display_formatting.py         # Phase 4: Display tests
```

### Test Coverage by Phase

| Phase | Test File | Tests | Risk Level | Priority |
|-------|-----------|-------|------------|----------|
| Phase 1 | `test_weather_storage_schema.py` | 15 | Medium | **CRITICAL** |
| Phase 2 | `test_weather_mechanics_events.py` | 30 | **Very High** | **CRITICAL** |
| Phase 3 | `test_handler_integration.py` | 18 | High | **CRITICAL** |
| Phase 4 | `test_display_formatting.py` | 15 | Low-Medium | HIGH |
| **Total** | - | **78 tests** | - | - |

## TDD Workflow: Step-by-Step

### Step 1: Run Tests (All Failing - Red Phase)

```bash
# From project root
pytest tests/ -v

# Expected output: All tests skipped/failing (code not implemented yet)
```

### Step 2: Implement Phase 1 (Database)

**Goal**: Make `test_weather_storage_schema.py` pass

```bash
# Run only Phase 1 tests
pytest tests/test_weather_storage_schema.py -v

# Implement db/weather_storage.py changes
# - Add 4 new columns (cold_front_total_duration, heat_wave_total_duration, days_since_last_cold_front, days_since_last_heat_wave)
# - Add migration logic
# - Add cooldown tracking methods (get_cooldown_status, increment_cooldown, reset_cooldown)

# Re-run tests until all pass
pytest tests/test_weather_storage_schema.py -v
```

**Success Criteria**: All 15 database tests passing ✅

### Step 3: Implement Phase 2 (Core Mechanics)

**Goal**: Make `test_weather_mechanics_events.py` pass

```bash
# Run only Phase 2 tests
pytest tests/test_weather_mechanics_events.py -v

# Implement utils/weather_mechanics.py changes
# - Modify handle_cold_front() signature and logic
# - Modify handle_heat_wave() signature and logic
# - Modify roll_temperature_with_special_events() for daily variation
# - Add get_category_from_actual_temp() helper

# Re-run tests incrementally
pytest tests/test_weather_mechanics_events.py::TestColdFrontTriggering -v  # Start with triggering tests
pytest tests/test_weather_mechanics_events.py::TestDailyTemperatureVariation -v  # Then variation tests
pytest tests/test_weather_mechanics_events.py -v  # Finally all tests
```

**Success Criteria**: All 30 mechanics tests passing ✅

**Critical Tests to Watch**:
- `test_roll_2_during_active_cold_front_does_NOT_trigger_nested_event` (THE NESTING BUG)
- `test_special_roll_suppressed_during_cold_front` (Daily variation safety)
- `test_category_recalculated_from_final_temperature` (Display correctness)

### Step 4: Implement Phase 3 (Handler Integration)

**Goal**: Make `test_handler_integration.py` pass

```bash
# Run only Phase 3 tests
pytest tests/test_handler_integration.py -v

# Implement commands/weather_modules/handler.py changes
# - Extract state from storage
# - Pass cooldowns to mechanics
# - Update cooldown trackers after each day
# - Save new fields to database

# Re-run tests
pytest tests/test_handler_integration.py -v

# Also verify Phases 1-2 still pass (regression check)
pytest tests/test_weather_storage_schema.py tests/test_weather_mechanics_events.py -v
```

**Success Criteria**: All 18 integration tests passing ✅

### Step 5: Implement Phase 4 (Display)

**Goal**: Make `test_display_formatting.py` pass

```bash
# Run only Phase 4 tests
pytest tests/test_display_formatting.py -v

# Implement display changes
# - commands/weather_modules/stages.py: Add day counters to summaries
# - commands/weather_modules/notifications.py: Add special events section to GM embeds

# Re-run tests
pytest tests/test_display_formatting.py -v

# Full regression test
pytest tests/ -v
```

**Success Criteria**: All 15 display tests passing ✅

### Step 6: Full Test Suite

```bash
# Run ALL tests
pytest tests/ -v

# Expected: ~78 tests passing
```

## Using Tests to Guide AI

### Template Prompts for AI

#### Starting a Phase

```
I need to implement Phase X: [Phase Name].

Here are the tests that must pass:
[Paste test file content]

The existing code is in [file path].

Please implement the changes to make these tests pass.
```

#### Fixing Failing Tests

```
Tests are failing:
- test_X: [Error message]
- test_Y: [Error message]

Current implementation:
[Paste relevant code]

Fix the code to make these tests pass WITHOUT breaking the currently passing tests.
```

#### Refactoring

```
All tests are passing, but I want to refactor [function/module].

Here are the tests that must continue passing:
[Paste test file]

Refactor the code while keeping all tests green.
```

## Test Anatomy: Example Explained

Let's break down a critical test:

```python
def test_roll_2_during_active_cold_front_does_NOT_trigger_nested_event(self):
    """
    GIVEN: Active cold front (day 2 of 3), roll = 2
    WHEN: handle_cold_front() is called
    THEN: Existing cold front continues, NO new cold front triggered
    
    THIS IS THE MOST IMPORTANT TEST - PREVENTS NESTING BUG!
    """
    modifier, remaining, total = handle_cold_front(
        roll=2,  # Special trigger roll
        current_cold_front_days=2,  # But cold front already active!
        current_total_duration=3,
        days_since_last_cold_front=0,
        heat_wave_active=False
    )
    
    # Should decrement existing event, NOT start new one
    assert modifier == -10
    assert remaining == 1, "Should decrement existing cold front"
    assert total == 3, "Should preserve original total, NOT roll new duration"
```

**Structure**:
- **Given/When/Then**: Clear setup → action → expected outcome
- **Docstring explains WHY**: Not just what, but why this test matters
- **Specific assertions**: Check exact values, not just "truthy"
- **Failure messages**: Explain what went wrong

## Running Tests: Quick Reference

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_weather_mechanics_events.py -v

# Specific test class
pytest tests/test_weather_mechanics_events.py::TestColdFrontTriggering -v

# Specific test function
pytest tests/test_weather_mechanics_events.py::TestColdFrontTriggering::test_cold_front_triggers_on_roll_2_when_cooldown_expired -v

# Stop on first failure
pytest tests/ -x

# Show print statements
pytest tests/ -v -s

# Run only tests matching pattern
pytest tests/ -v -k "cold_front"

# Show coverage
pytest tests/ --cov=utils --cov=db --cov=commands/weather_modules

# Generate HTML coverage report
pytest tests/ --cov=utils --cov=db --cov=commands/weather_modules --cov-report=html
# Open htmlcov/index.html in browser
```

## Test Coverage Expectations

### Minimum Coverage Targets

| Module | Target Coverage | Priority |
|--------|-----------------|----------|
| `utils/weather_mechanics.py` | 95%+ | **CRITICAL** |
| `db/weather_storage.py` | 90%+ | **CRITICAL** |
| `commands/weather_modules/handler.py` | 85%+ | **CRITICAL** |
| `commands/weather_modules/stages.py` | 80%+ | HIGH |
| `commands/weather_modules/notifications.py` | 80%+ | HIGH |

### What to Test

✅ **DO Test**:
- Event triggering logic (cold front/heat wave)
- Cooldown mechanics
- Mutual exclusivity
- Daily temperature variation
- State transitions (active → cooldown → expired)
- Database migrations
- Display formatting

❌ **DON'T Test**:
- Discord.py library internals
- External API responses (mock instead)
- UI pixel-perfect appearance (test content only)

## Critical Test Scenarios

### The "Nesting Bug" Prevention

**Test**: `test_roll_2_during_active_cold_front_does_NOT_trigger_nested_event`

**Why Critical**: Without this, rolling d100=2 during an active cold front would trigger a NEW cold front inside the existing one, creating invalid state.

**What It Tests**:
```python
# Day 2 of 3-day cold front
roll = 2  # Normally triggers cold front

# Should: Decrement existing cold front (2 → 1 day remaining)
# NOT: Start new 3-day cold front (nested/broken)
```

### The "Daily Variation" Correctness

**Test**: `test_category_recalculated_from_final_temperature`

**Why Critical**: Temperature category displayed to players must reflect the FINAL temperature (after event + daily variation), not the base temperature.

**What It Tests**:
```python
# Base temp: 21°C (average)
# Cold front: -10°C
# Daily variation: +5°C (high roll)
# Final: 16°C

# Should display: "Cool" or "Mild" (reflects 16°C)
# NOT: "Very Low" (would be wrong, based on base temp)
```

### The "Cooldown Tracking" Integrity

**Test**: `test_10_day_journey_with_cold_front_lifecycle`

**Why Critical**: Full journey lifecycle test ensures cooldowns, events, and state transitions all work together.

**What It Tests**:
- Days 1-2: Normal weather
- Day 3: Cold front starts (cooldown resets to 0)
- Days 4-5: Cold front continues (cooldown stays 0)
- Days 6-12: Cooldown increments (1, 2, 3... 7)
- Day 13+: Cooldown expired, new event can trigger

## Debugging Failing Tests

### Common Failure Patterns

#### 1. Assertion Error

```
AssertionError: assert 5 == 3
```

**Fix**:
1. Read test docstring to understand intent
2. Check if implementation has off-by-one error
3. Verify state transitions (e.g., decrementing too early)

#### 2. AttributeError

```
AttributeError: 'NoneType' object has no attribute 'get'
```

**Fix**:
1. Check if database returns None when expecting dict
2. Add defensive None checks in code
3. Verify fixtures provide correct mock data

#### 3. KeyError

```
KeyError: 'cold_front_total_duration'
```

**Fix**:
1. Database migration not run (missing column)
2. Handler not passing all required fields
3. Use `.get()` with defaults instead of direct access

### Test Debugging Workflow

```bash
# 1. Run failing test in isolation
pytest tests/test_file.py::test_function -v -s

# 2. Add print statements to test
def test_something():
    result = function_under_test()
    print(f"DEBUG: result = {result}")  # Temporary debug
    assert result == expected

# 3. Use pytest's --pdb flag to drop into debugger
pytest tests/test_file.py::test_function --pdb

# 4. Check test fixtures
pytest tests/test_file.py::test_function -v -s --fixtures

# 5. Run with coverage to see what code is executed
pytest tests/test_file.py::test_function --cov=module --cov-report=term-missing
```

## Continuous Integration (Future)

When setting up CI/CD:

```yaml
# .github/workflows/tests.yml
name: Run Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v --cov=utils --cov=db --cov=commands/weather_modules
```

## Test Maintenance

### When to Update Tests

✅ **Update tests when**:
- Requirements change (e.g., cold front duration changes from 1d5 to 1d10)
- New features added (e.g., snow accumulation during cold fronts)
- Bugs discovered (write test that exposes bug, then fix)

❌ **DON'T change tests to make code pass** (defeats purpose of TDD)

### Refactoring Tests

If tests become hard to maintain:

1. **Extract common setup**:
```python
@pytest.fixture
def active_3_day_cold_front():
    return {
        "cold_front_days_remaining": 2,
        "cold_front_total_duration": 3,
    }
```

2. **Use parametrize for similar tests**:
```python
@pytest.mark.parametrize("duration", [1, 2, 3, 4, 5])
def test_cold_front_duration(duration):
    # Test runs 5 times with different durations
```

3. **Add helper assertions** (in `conftest.py`):
```python
def assert_cold_front_display_format(description, day_num, total_days):
    assert f"Day {day_num} of {total_days}" in description
```

## Quick Start Checklist

- [ ] Read `longer_weather_plan.md` to understand features
- [ ] Run `pytest tests/ -v` to see all tests (currently failing/skipped)
- [ ] Start with Phase 1: `pytest tests/test_weather_storage_schema.py -v`
- [ ] Implement database changes to make Phase 1 pass
- [ ] Move to Phase 2: `pytest tests/test_weather_mechanics_events.py -v`
- [ ] Pay special attention to nesting bug and variation tests
- [ ] Continue through Phases 3-4
- [ ] Run full suite: `pytest tests/ -v` (target: 78/78 passing)
- [ ] Check coverage: `pytest tests/ --cov=utils --cov=db --cov=commands/weather_modules`

## Resources

- **pytest documentation**: https://docs.pytest.org/
- **TDD overview**: https://martinfowler.com/bliki/TestDrivenDevelopment.html
- **Mocking with unittest.mock**: https://docs.python.org/3/library/unittest.mock.html

## Success Metrics

✅ **Phase 1 Complete**: 15/15 database tests passing
✅ **Phase 2 Complete**: 30/30 mechanics tests passing (including nesting bug prevention)
✅ **Phase 3 Complete**: 18/18 integration tests passing
✅ **Phase 4 Complete**: 15/15 display tests passing
✅ **Full Implementation**: 78/78 tests passing, 90%+ coverage on critical modules

---

**Remember**: Tests are your AI's guidebook. When the AI asks "What should this function do?", point to the test. When something breaks, the test will tell you exactly what and where.
