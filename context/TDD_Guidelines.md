Test-Driven Development (TDD) Instructions for Claude 4.5
Overview
This document provides universal TDD guidelines for implementing new features or modifying existing code. These instructions apply to all projects regardless of technology stack or domain.
Purpose: Ensure code quality, prevent regressions, and maintain a clear specification through executable tests.
When to use: Before implementing any new feature, refactoring existing code, or fixing bugs.

Core TDD Principles
1. Red-Green-Refactor Cycle
❌ RED    → Write a failing test that defines desired behavior
✅ GREEN  → Write minimal code to make the test pass
♻️ REFACTOR → Improve code quality while keeping tests green
```

### 2. **Test-First Mindset**
- Tests are **specifications**, not afterthoughts
- Tests document **intent** before implementation
- Tests guide **design** by forcing you to think about interfaces first

### 3. **Incremental Development**
- One test at a time
- Small, focused tests
- Build complexity gradually

---

## TDD Workflow for AI-Assisted Development

### Phase 0: Preparation & Analysis

**BEFORE writing any tests or code:**

1. **Read the implementation plan** (provided separately by user)
   - Identify all files that need modification
   - Understand dependencies between components
   - Note complexity ratings and risk areas

2. **Review existing project context** (provided separately by user)
   - Understand current architecture
   - Identify existing patterns and conventions
   - Note any existing test infrastructure

3. **Identify test boundaries**
```
   Ask yourself:
   - What are the PUBLIC interfaces that need testing?
   - What are the edge cases mentioned in the plan?
   - What are the state transitions that could break?
   - What are the integration points between modules?

Create a test priority list

P0 (Critical): Core logic, state changes, data persistence
P1 (High): Integration points, error handling, edge cases
P2 (Medium): Display logic, formatting, user-facing strings
P3 (Low): Documentation, logging, cosmetic changes




Phase 1: Test Design (RED Phase)
Goal: Write tests that will fail because the feature doesn't exist yet
Step 1.1: Write Test Skeleton
python# Template for test design
def test_<feature>_<scenario>_<expected_result>():
    """
    GIVEN: <initial state/preconditions>
    WHEN: <action taken>
    THEN: <expected outcome>
    
    WHY THIS TEST: <explain what bug this prevents or requirement it enforces>
    """
    # Arrange (setup)
    
    # Act (execute)
    
    # Assert (verify)
Step 1.2: Follow Test Design Checklist
For each function/feature to implement, write tests covering:

 Happy path: Normal, expected use case
 Edge cases: Boundary values (0, empty, max, negative)
 Error cases: Invalid inputs, missing data, constraint violations
 State transitions: Before/after changes, side effects
 Integration: How it interacts with other components

Step 1.3: Test Naming Convention
Use descriptive names that read like specifications:
python✅ GOOD:
test_cold_front_blocks_new_event_during_cooldown_period()
test_temperature_varies_daily_during_active_cold_front()
test_migration_preserves_active_events_with_missing_total_duration()

❌ BAD:
test_cold_front()
test_temp()
test_migration()
Step 1.4: Write Tests in Dependency Order
Order matters! Test from foundation upward:

Data Models (schemas, DTOs, entities)

python   test_weather_event_model_validates_duration_range()
   test_weather_state_includes_cooldown_fields()

Core Business Logic (pure functions, algorithms)

python   test_calculate_final_temperature_applies_modifiers_in_correct_order()
   test_event_trigger_logic_respects_cooldown()

Persistence Layer (database, storage)

python   test_save_weather_persists_all_required_fields()
   test_fetch_weather_returns_complete_state()

Integration Points (handlers, controllers)

python   test_weather_handler_updates_cooldown_after_event_ends()
   test_handler_passes_complete_context_to_display_layer()

Presentation Layer (formatters, display)

python   test_format_message_shows_day_counter_correctly()
Step 1.5: Test Quality Checks
Before proceeding, verify each test:

 Is it independent? Can run in any order without setup dependencies
 Is it focused? Tests ONE behavior, not multiple things
 Is it readable? Name and body clearly communicate intent
 Is it maintainable? Doesn't depend on implementation details
 Does it have a clear assertion? Not just "doesn't crash"

Step 1.6: Run Tests (Should FAIL)
bashpytest tests/test_<module>.py -v

# Expected output: ALL RED ❌
# This confirms tests are actually validating something
⚠️ CRITICAL: If tests pass before implementation, they're either:

Testing something that already exists (not new feature)
Not actually testing anything (false positive)
Using mocks incorrectly


Phase 2: Implementation (GREEN Phase)
Goal: Write minimal code to make tests pass
Step 2.1: Implement ONE Test at a Time
DO NOT try to implement everything at once. Instead:

Pick the simplest failing test
Write just enough code to make it pass
Run that specific test: pytest tests/test_module.py::test_name -v
When green ✅, move to next test

Step 2.2: Implementation Checklist

 Start with the simplest case first

python  # Don't implement all edge cases at once
  # Start with: test_happy_path()
  # Then add: test_edge_case_empty_input()
  # Then add: test_error_case_invalid_type()

 Use the test as your spec

python  # Test says function should return (modifier, remaining, total)
  # So function signature must be:
  def handle_event() -> Tuple[int, int, int]:

 Avoid premature optimization

python  # Just make it work first
  # Optimize in refactor phase

 Update tests if you discover better design

python  # Sometimes implementation reveals test was wrong
  # That's OK! TDD is iterative
  # Update test, then re-implement
Step 2.3: Integration with Existing Code
When modifying existing files:

Check for existing tests first

bash   # Look for tests covering the file you're changing
   find tests/ -name "*<filename>*"

Run existing tests BEFORE making changes

bash   pytest tests/ -v
   # Get baseline: X tests passing

After implementing new feature, run ALL tests

bash   pytest tests/ -v
   # Verify: X + new_tests passing, 0 failing

If existing tests fail, STOP

You've introduced a regression
Fix the issue before proceeding
Do NOT disable failing tests



Step 2.4: Dealing with Dependencies
When your code depends on external systems:
Option A: Mock External Dependencies
pythonfrom unittest.mock import patch, MagicMock

def test_weather_api_fetch_handles_network_error():
    with patch('requests.get') as mock_get:
        mock_get.side_effect = ConnectionError("Network down")
        
        result = fetch_weather_data()
        
        assert result.error == "Network unavailable"
Option B: Use Test Doubles (Fakes)
pythonclass FakeWeatherStorage:
    """In-memory storage for testing"""
    def __init__(self):
        self.data = {}
    
    def save_weather(self, guild_id, weather):
        self.data[guild_id] = weather

def test_weather_handler_saves_correctly():
    storage = FakeWeatherStorage()  # No real database
    handler = WeatherHandler(storage)
    
    handler.generate_weather(guild_id=123)
    
    assert 123 in storage.data
Option C: Integration Tests with Real Systems
python@pytest.mark.integration  # Mark as slow test
def test_database_roundtrip():
    db = WeatherStorage(":memory:")  # Use in-memory DB
    
    db.save_weather(guild_id=123, weather=example_weather)
    result = db.fetch_weather(guild_id=123)
    
    assert result == example_weather
Step 2.5: Implementation Progress Tracking
Keep a mental (or written) checklist:
markdown## Implementation Status

### Core Logic (weather_mechanics.py)
- [x] test_cold_front_triggers_on_roll_2 ✅
- [x] test_cold_front_blocks_during_cooldown ✅
- [ ] test_daily_variation_during_event ❌ (IN PROGRESS)
- [ ] test_special_roll_suppression ⏳ (NEXT)

### Database (weather_storage.py)
- [x] test_new_columns_exist ✅
- [x] test_migration_preserves_data ✅
- [ ] test_fetch_returns_all_fields ⏳

Phase 3: Refactor (REFACTOR Phase)
Goal: Improve code quality WITHOUT changing behavior
Step 3.1: When to Refactor
Refactor when you notice:

Duplicated code patterns
Functions longer than ~30 lines
Complex conditionals (>3 nested ifs)
Unclear variable names
Magic numbers without constants

Step 3.2: Refactoring Checklist

 Run tests before refactoring (ensure green ✅)
 Make ONE refactoring change at a time
 Run tests after EACH change
 If tests fail, revert immediately
 Commit when tests pass

Step 3.3: Safe Refactoring Techniques
Extract Function
python# BEFORE (hard to test)
def handle_event(roll, current_days, cooldown):
    if roll == 2 and current_days == 0 and cooldown > 7:
        duration = random.randint(1, 5)
        return -10, duration, duration
    # ... more logic

# AFTER (easier to test)
def is_event_trigger_valid(roll, current_days, cooldown):
    return roll == 2 and current_days == 0 and cooldown > 7

def roll_event_duration():
    return random.randint(1, 5)

def handle_event(roll, current_days, cooldown):
    if is_event_trigger_valid(roll, current_days, cooldown):
        duration = roll_event_duration()
        return -10, duration, duration
Extract Constant
python# BEFORE
if cooldown_days > 7:  # Magic number

# AFTER
COOLDOWN_PERIOD_DAYS = 7  # Configurable constant

if cooldown_days > COOLDOWN_PERIOD_DAYS:
Simplify Conditionals
python# BEFORE
if not (cold_front_active or heat_wave_active or cooldown_active):
    trigger_event()

# AFTER
can_trigger_event = not (cold_front_active or heat_wave_active or cooldown_active)
if can_trigger_event:
    trigger_event()
```

#### Step 3.4: Code Quality Metrics

After refactoring, verify:
- [ ] **Cyclomatic complexity**: Functions have <10 decision points
- [ ] **Function length**: Functions are <50 lines (ideally <30)
- [ ] **DRY principle**: No code blocks repeated >2 times
- [ ] **Single Responsibility**: Each function does ONE thing
- [ ] **Clear naming**: Variables/functions explain their purpose

---

## Special Considerations for AI-Assisted TDD

### Challenge 1: Context Window Limitations

**Problem**: AI can't see entire codebase at once

**Solution**: Follow test-first workflow
```
1. User provides: implementation plan + project context
2. AI reads: specific files mentioned in plan
3. AI writes: tests based on plan requirements
4. AI implements: using tests as guide (doesn't need full context)
5. Tests verify: behavior matches plan
Challenge 2: Assumption Drift Across Sessions
Problem: Different sessions might have different assumptions
Solution: Tests are single source of truth
python# This test survives across sessions
def test_cold_front_duration_range():
    """Cold fronts MUST last 1-5 days (per WFRP rules)"""
    for _ in range(100):
        modifier, remaining, total = handle_cold_front(roll=2, ...)
        assert 1 <= total <= 5, "Duration outside valid range"
Even if future AI forgets the rule, the test enforces it.
Challenge 3: Integration Bugs from Piecemeal Changes
Problem: AI modifies file A in session 1, file B in session 2, they don't integrate
Solution: Integration tests catch mismatches
pythondef test_handler_and_storage_agree_on_schema():
    """Ensures handler.py saves what storage.py expects"""
    storage = WeatherStorage(":memory:")
    handler = WeatherHandler(storage)
    
    handler.generate_weather(guild_id=123)
    weather = storage.fetch_weather(guild_id=123)
    
    # If handler saves wrong fields, this fails
    assert hasattr(weather, 'cold_front_total_duration')
    assert hasattr(weather, 'days_since_last_cold_front')
```

---

## Test Organization Best Practices

### Directory Structure
```
project/
├── src/
│   ├── weather/
│   │   ├── mechanics.py
│   │   ├── storage.py
│   │   └── display.py
├── tests/
│   ├── unit/
│   │   ├── test_weather_mechanics.py
│   │   ├── test_weather_storage.py
│   │   └── test_weather_display.py
│   ├── integration/
│   │   └── test_weather_system_integration.py
│   └── fixtures/
│       └── sample_data.py
```

### Test File Naming
```
src/weather/mechanics.py  →  tests/unit/test_weather_mechanics.py
src/db/storage.py         →  tests/unit/test_storage.py
Test Fixtures and Helpers
python# tests/fixtures/weather_fixtures.py
import pytest

@pytest.fixture
def sample_cold_front_state():
    """Reusable test data for cold front scenarios"""
    return {
        'roll': 2,
        'current_days': 0,
        'cooldown_days': 99,
        'base_temp': 21
    }

@pytest.fixture
def mock_storage():
    """In-memory storage for testing"""
    return WeatherStorage(":memory:")

Common TDD Pitfalls to Avoid
❌ Pitfall 1: Testing Implementation Details
python# BAD: Test knows too much about HOW it works
def test_cold_front_uses_random_randint():
    with patch('random.randint') as mock_random:
        mock_random.return_value = 3
        result = handle_cold_front(...)
        mock_random.assert_called_with(1, 5)  # Fragile!

# GOOD: Test focuses on WHAT it does
def test_cold_front_duration_in_valid_range():
    for _ in range(100):  # Test distribution
        _, _, total = handle_cold_front(...)
        assert 1 <= total <= 5
❌ Pitfall 2: Tests That Don't Actually Test Anything
python# BAD: Doesn't verify behavior
def test_generate_weather():
    result = generate_weather()
    assert result is not None  # Useless assertion

# GOOD: Verifies specific behavior
def test_generate_weather_returns_complete_state():
    result = generate_weather(guild_id=123, region='Reikland')
    assert result.temperature is not None
    assert result.precipitation is not None
    assert result.wind_speed is not None
    assert 'Reikland' in result.region_name
❌ Pitfall 3: Over-Mocking
python# BAD: Mocking everything makes test meaningless
def test_calculate_temperature():
    with patch('weather.get_base_temp') as mock_base, \
         patch('weather.get_modifier') as mock_mod, \
         patch('weather.apply_events') as mock_events:
        mock_base.return_value = 20
        mock_mod.return_value = 5
        mock_events.return_value = -10
        
        result = calculate_temperature()
        assert result == 15  # But did the function actually calculate it?

# GOOD: Only mock external dependencies
def test_calculate_temperature():
    # Use real calculation logic, only mock external APIs
    with patch('weather.fetch_from_api') as mock_api:
        mock_api.return_value = {'base': 20}
        result = calculate_temperature(modifiers=[5, -10])
        assert result == 15  # Real calculation verified
❌ Pitfall 4: Test Order Dependencies
python# BAD: Test 2 depends on Test 1 running first
class TestWeatherSystem:
    def test_01_create_weather(self):
        self.weather = create_weather()  # Sets instance variable
    
    def test_02_modify_weather(self):
        self.weather.temperature = 25  # Depends on test_01

# GOOD: Each test is independent
class TestWeatherSystem:
    @pytest.fixture
    def weather(self):
        return create_weather()
    
    def test_create_weather(self, weather):
        assert weather is not None
    
    def test_modify_weather(self, weather):
        weather.temperature = 25
        assert weather.temperature == 25
❌ Pitfall 5: Ignoring Failing Tests
python# BAD: Commenting out failing tests
# def test_cooldown_prevents_duplicate_events():
#     # TODO: Fix this later
#     pass

# GOOD: Fix immediately or document as known issue
@pytest.mark.skip(reason="Bug #123: Cooldown not implemented yet")
def test_cooldown_prevents_duplicate_events():
    # Test stays visible, documents missing feature
    pass

TDD Workflow Summary (Quick Reference)
1️⃣ PREPARE

 Read implementation plan
 Read project context
 Identify files to modify
 List edge cases and risks

2️⃣ DESIGN TESTS (RED)

 Write test names that describe behavior
 Use Given-When-Then format
 Cover happy path, edge cases, errors
 Order tests by dependency (foundation → presentation)
 Run tests (verify they FAIL ❌)

3️⃣ IMPLEMENT (GREEN)

 Pick simplest failing test
 Write minimal code to pass it
 Run test (verify it PASSES ✅)
 Repeat for next test
 Run ALL tests before moving to next file

4️⃣ REFACTOR (CLEAN)

 Extract duplicated code
 Simplify complex logic
 Improve names and structure
 Run tests after EACH change
 Commit when all tests pass

5️⃣ VERIFY

 All new tests passing ✅
 All existing tests still passing ✅
 Code coverage meets threshold (>80% for new code)
 Integration tests pass
 Manual smoke test (if applicable)


When to Deviate from Pure TDD
TDD is powerful but not dogmatic. You may skip tests for:
1. Exploratory Spikes
When you genuinely don't understand the problem space:

Write throwaway prototype first
Learn from it
Delete it
Then TDD the real implementation

2. Trivial Code
Simple getters/setters, data classes, config files:
python# Doesn't need tests (obvious behavior)
@dataclass
class WeatherEvent:
    name: str
    duration: int
3. External Integration Code
Direct API calls, UI rendering:

These need integration tests, not unit tests
Test at higher level

4. Legacy Code Without Tests
Adding tests to untested code is hard:

Write tests for NEW behavior only
Gradually add tests when refactoring old code
Use characterization tests to capture existing behavior


Success Criteria
You've successfully applied TDD when:
✅ Tests are written BEFORE implementation
✅ Tests fail initially, then pass after implementation
✅ All tests pass at end of each phase
✅ Tests are readable and maintainable
✅ Tests catch real bugs (verify by intentionally breaking code)
✅ Tests serve as documentation
✅ Refactoring doesn't break tests
✅ New features don't break existing tests

AI-Specific Communication Protocol
When User Provides Implementation Plan
AI Should:

Read and acknowledge the plan
Ask clarifying questions about:

Ambiguous requirements
Missing edge cases
Testing infrastructure preferences


Propose test structure:

"I'll create 15 tests covering: [list categories]. Does this align with your priorities?"


Wait for confirmation before writing tests

When Writing Tests
AI Should:

Show test structure first:

markdown   ## Proposed Test Suite
   
   ### Core Logic (P0)
   - test_event_triggers_on_roll_2
   - test_event_blocks_during_cooldown
   
   ### Edge Cases (P1)
   - test_event_handles_zero_duration
   - test_overlapping_events_prevented

Write tests incrementally (5-10 at a time)
Explain why each test matters
Request user feedback before proceeding

When Implementing
AI Should:

Announce which test is being addressed:

"Implementing handle_cold_front() to pass test_cold_front_triggers_on_roll_2"


Show implementation
Indicate expected test result:

"This should make test_cold_front_triggers_on_roll_2 pass ✅"


Request user to run tests and report results

When Tests Fail
AI Should:

Ask for exact error message
Analyze failure
Propose fix
Explain what was wrong
Request re-test

AI Should NOT:

Assume tests passed without confirmation
Skip tests to "speed up" development
Disable failing tests
Blame tests for being "wrong" without investigation


Appendix: Test Templates
Template 1: Unit Test
pythondef test_<function>_<scenario>_<expected>():
    """
    GIVEN: <preconditions>
    WHEN: <action>
    THEN: <expected outcome>
    """
    # Arrange
    input_data = create_test_data()
    
    # Act
    result = function_under_test(input_data)
    
    # Assert
    assert result.field == expected_value
    assert result.satisfies_condition()
Template 2: Integration Test
python@pytest.mark.integration
def test_<system>_<interaction>_<outcome>():
    """
    Tests interaction between Component A and Component B
    
    GIVEN: <initial system state>
    WHEN: <components interact>
    THEN: <system produces correct result>
    """
    # Setup system
    storage = create_storage()
    handler = create_handler(storage)
    
    # Execute interaction
    handler.process(data)
    
    # Verify system state
    saved_data = storage.fetch()
    assert saved_data == expected_state
Template 3: Parameterized Test
python@pytest.mark.parametrize("roll,expected_modifier", [
    (2, -10),   # Cold front
    (45, 0),    # Average
    (99, 10),   # Heat wave
])
def test_temperature_modifiers(roll, expected_modifier):
    """Test temperature modifiers for different roll values"""
    result = calculate_temperature_modifier(roll)
    assert result == expected_modifier
Template 4: Error/Exception Test
pythondef test_<function>_raises_error_on_invalid_input():
    """Verify proper error handling for invalid inputs"""
    with pytest.raises(ValueError, match="Duration must be positive"):
        create_event(duration=-5)

Final Checklist for AI Implementation
Before declaring a feature "complete":

 All P0 tests written and passing ✅
 All P1 tests written and passing ✅
 Integration tests passing ✅
 Existing tests still passing ✅
 Code coverage >80% for new code
 Tests follow naming conventions
 Tests are independent (no order dependencies)
 Tests use Given-When-Then format
 Error cases covered
 Edge cases covered
 Documentation updated (if needed)
 User has confirmed tests match requirements


End of TDD Instructions
These guidelines should be read at the start of each implementation session and referenced throughout development. Adapt as needed for specific project constraints, but always maintain the core principle: Test First, Then Code.