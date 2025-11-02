# Test Plan for River Traveller Bot

**Date:** 2025-11-01  
**Scope:** Modern code only (commands/, utils/, db/)  
**Test Framework:** pytest with parametrization, fixtures, hypothesis  
**Coverage Goals:** Bug finding over coverage metrics

---

## 1. In-Scope Modules

### 1.1 Commands (commands/)
**Modern, Active Code:**
- ✅ `boat_handling.py` - WFRP boat handling tests (Sail/Row)
- ✅ `roll.py` - Dice rolling with WFRP mechanics
- ✅ `river_encounter.py` - River encounter generation
- ✅ `weather.py` - Weather journey management
- ✅ `help.py` - Bot help command
- ✅ `constants.py` - Shared constants
- ✅ `error_handlers.py` - Error handling utilities
- ✅ `permissions.py` - Permission checking

**Services (commands/services/):**
- ✅ `boat_handling_service.py` - Boat test business logic
- ✅ `roll_service.py` - Dice rolling business logic
- ✅ `encounter_service.py` - Encounter generation logic
- ✅ `command_logger.py` - Command logging

**Weather Modules (commands/weather_modules/):**
- ✅ `handler.py` - Weather command orchestration
- ✅ `models.py` - Weather data models
- ✅ `exceptions.py` - Weather-specific exceptions
- ✅ `formatters.py` - Weather output formatting
- ✅ `stages.py` - Journey stage definitions

**Weather Services (commands/weather_modules/services/):**
- ✅ `journey_service.py` - Journey state management
- ✅ `daily_weather_service.py` - Daily weather generation
- ✅ `display_service.py` - Weather display formatting
- ✅ `notification_service.py` - Weather notifications

### 1.2 Utilities (utils/)
**Modern, Active Code:**
- ✅ `wfrp_mechanics.py` - Core WFRP 4e mechanics
- ✅ `encounter_mechanics.py` - Encounter mechanics
- ✅ `modifier_calculator.py` - Modifier calculations
- ✅ `weather_mechanics.py` - Weather mechanics
- ✅ `weather_modifier_service.py` - Weather modifier service
- ✅ `weather_impact.py` - Weather impact calculations

### 1.3 Database (db/)
**Modern, Active Code:**
- ✅ `character_data.py` - Character data access
- ✅ `encounter_data.py` - Encounter data access
- ✅ `weather_data.py` - Weather data access
- ✅ `weather_storage.py` - Weather state persistence

**Models (db/models/):**
- ✅ `character_models.py` - Character data models
- ✅ `encounter_models.py` - Encounter data models
- ✅ `weather_models.py` - Weather data models

**Repositories (db/repositories/):**
- ✅ `journey_repository.py` - Journey persistence
- ✅ `weather_repository.py` - Weather persistence

---

## 2. Files Missing Tests (Priority Order)

### 🔴 HIGH PRIORITY - Core Bot Commands
1. **commands/boat_handling.py** - Main boat handling command
   - Risk: Critical gameplay mechanic, complex modifier stacking
   - Tests needed: Edge cases, Discord interaction mocking

2. **commands/roll.py** - Dice rolling command
   - Risk: Core mechanic, WFRP doubles detection
   - Tests needed: Boundary cases, doubles logic

3. **commands/river_encounter.py** - Encounter command
   - Risk: Complex formatting, GM notification logic
   - Tests needed: All encounter types, permission checks

4. **commands/weather.py** - Weather command orchestration
   - Risk: Complex subcommand routing, state management
   - Tests needed: Subcommand dispatch, error handling

### 🟠 MEDIUM PRIORITY - Data Access & Business Logic
5. **commands/help.py** - Help command
   - Risk: Low, mostly static content
   - Tests needed: Basic rendering, command listing

6. **commands/weather_modules/handler.py** - Weather handler
   - Risk: Orchestration logic, error propagation
   - Tests needed: Subcommand routing, error handling

7. **commands/weather_modules/formatters.py** - Weather formatters
   - Risk: Display logic, edge cases in formatting
   - Tests needed: Null/empty data, edge cases

8. **commands/weather_modules/stages.py** - Journey stages
   - Risk: Stage validation, time calculations
   - Tests needed: Stage boundaries, time calculations

9. **db/character_data.py** - Character data access
   - Risk: Data integrity, missing characters
   - Tests needed: Invalid lookups, data validation

10. **db/weather_data.py** - Weather data access
    - Risk: Data integrity, invalid lookups
    - Tests needed: Boundary conditions, missing data

11. **db/weather_storage.py** - Weather persistence
    - Risk: File I/O, concurrent access, corruption
    - Tests needed: File operations, error recovery

### 🔵 LOW PRIORITY - Utilities
12. **utils/weather_impact.py** - Weather impact calculations
    - Risk: Calculation accuracy
    - Tests needed: Edge cases, modifier stacking

13. **utils/weather_mechanics.py** - Weather mechanics
    - Risk: Calculation accuracy
    - Tests needed: Edge cases, boundary conditions

14. **db/models/encounter_models.py** - Encounter models
    - Risk: Data validation
    - Tests needed: Model validation, edge cases

---

## 3. Key Risks Per Module

### 3.1 Commands Layer
**Boat Handling (`boat_handling.py`)**
- ⚠️ **Modifier Stacking**: Weather + Difficulty + Lore bonus calculation errors
- ⚠️ **Character Validation**: Missing characters, invalid names
- ⚠️ **Discord Interaction**: Slash vs prefix command parity
- ⚠️ **Doubles Detection**: Critical/fumble classification edge cases

**Roll Command (`roll.py`)**
- ⚠️ **Dice Parsing**: Invalid notation (0d6, 1d0, negative dice)
- ⚠️ **WFRP Mechanics**: Success level calculation with boundary targets
- ⚠️ **Doubles Classification**: Roll of 01, 100, other doubles
- ⚠️ **Modifier Edge Cases**: Very large/small modifiers

**River Encounter (`river_encounter.py`)**
- ⚠️ **Permission Bypass**: Non-GM users overriding encounter types
- ⚠️ **GM Notification Failure**: Missing channel, permission errors
- ⚠️ **Encounter Type Validation**: Invalid type strings
- ⚠️ **Formatting Edge Cases**: Null/missing encounter data

**Weather Command (`weather.py`)**
- ⚠️ **Subcommand Routing**: Invalid subcommands, missing parameters
- ⚠️ **State Management**: Journey state corruption
- ⚠️ **Permission Checks**: Non-GM users accessing GM commands
- ⚠️ **Error Propagation**: Service errors not properly handled

### 3.2 Services Layer
**Boat Handling Service (`boat_handling_service.py`)**
- ⚠️ **Skill Selection**: No Sail or Row skill available
- ⚠️ **Lore Bonus**: Edge cases (skill 0-9, 100+)
- ⚠️ **Outcome Generation**: Consistent narrative for same SL

**Roll Service (`roll_service.py`)**
- ⚠️ **Dice Parsing**: Malformed notation, injection attempts
- ⚠️ **Overflow**: Very large dice counts/sizes
- ⚠️ **WFRP Calculation**: Off-by-one in SL calculation

**Encounter Service (`encounter_service.py`)**
- ⚠️ **Roll Distribution**: Bias in random generation
- ⚠️ **Data Integrity**: Missing encounter data for roll result
- ⚠️ **Type Override**: Invalid type strings

### 3.3 Database Layer
**Weather Storage (`weather_storage.py`)**
- ⚠️ **File Corruption**: Malformed JSON recovery
- ⚠️ **Concurrent Access**: Race conditions in read/write
- ⚠️ **Disk Full**: Write failures and rollback
- ⚠️ **Encoding Issues**: Unicode in guild IDs or data

**Character Data (`character_data.py`)**
- ⚠️ **Missing Data**: Character not found handling
- ⚠️ **Data Validation**: Invalid skill values
- ⚠️ **Case Sensitivity**: Character name lookups

**Weather Data (`weather_data.py`)**
- ⚠️ **Missing Conditions**: Incomplete weather data
- ⚠️ **Invalid Lookups**: Out of range weather types
- ⚠️ **Data Integrity**: Modifier calculation consistency

### 3.4 Utilities Layer
**WFRP Mechanics (`wfrp_mechanics.py`)**
- ⚠️ **SL Calculation**: Integer division edge cases
- ⚠️ **Doubles Detection**: Boundary cases (01, 100)
- ⚠️ **Target Clamping**: Targets outside 1-100 range

**Modifier Calculator (`modifier_calculator.py`)**
- ⚠️ **Weather Modifier Lookup**: Missing journey data
- ⚠️ **Time of Day**: Invalid time strings
- ⚠️ **Modifier Stacking**: Multiple weather effects

---

## 4. Test Techniques Per Risk

### 4.1 Boundary & Edge Case Testing
**Targets:**
- WFRP skill values: 0, 1, 99, 100, 101
- Dice counts: 0, 1, 100, 1000
- Modifiers: -50, 0, +60
- Success levels: -10, 0, +10
- Roll results: 1, 01, 50, 99, 100

**Approach:**
```python
@pytest.mark.parametrize("skill,expected", [
    (0, 0),      # Minimum skill
    (1, 0),      # No lore bonus
    (9, 0),      # No lore bonus
    (10, 1),     # First lore bonus
    (55, 5),     # Mid-range lore
    (99, 9),     # Maximum normal lore
    (100, 10),   # Edge case
])
def test_lore_bonus_boundaries(skill, expected):
    ...
```

### 4.2 Error Handling & Resilience
**Targets:**
- Invalid character names
- Malformed dice notation
- Missing weather data
- Corrupted JSON files
- Permission denied errors

**Approach:**
```python
def test_missing_character_raises_clear_error():
    with pytest.raises(ValueError, match="Character .* not found"):
        get_character("nonexistent")

def test_corrupted_weather_file_recovery(tmp_path):
    # Write invalid JSON
    # Verify graceful fallback or clear error
    ...
```

### 4.3 Integration Testing
**Targets:**
- Weather journey → modifier calculation → boat test
- Encounter generation → GM notification → logging
- Roll command → WFRP mechanics → doubles detection

**Approach:**
```python
def test_weather_affects_boat_handling_test():
    # Start weather journey with harsh conditions
    # Perform boat test
    # Verify penalty applied
    ...
```

### 4.4 Concurrency Testing (Weather Storage)
**Targets:**
- Concurrent journey creation
- Simultaneous weather updates
- Read-while-write scenarios

**Approach:**
```python
def test_concurrent_journey_creation():
    # Use threading to simulate concurrent writes
    # Verify all journeys saved correctly
    ...
```

### 4.5 Property-Based Testing (Hypothesis)
**Targets:**
- Dice parsing (any valid notation succeeds)
- WFRP SL calculation (mathematical invariants)
- Weather modifier ranges (always within bounds)

**Approach:**
```python
from hypothesis import given
from hypothesis.strategies import integers

@given(
    num_dice=integers(min_value=1, max_value=100),
    die_size=integers(min_value=2, max_value=100)
)
def test_dice_parsing_always_succeeds(num_dice, die_size):
    notation = f"{num_dice}d{die_size}"
    result = parse_dice(notation)
    assert result.num_dice == num_dice
    assert result.die_size == die_size
```

### 4.6 Security & Validation Testing
**Targets:**
- SQL injection in lookups (if DB used)
- Command injection in dice notation
- Path traversal in file operations
- XSS in formatted output

**Approach:**
```python
def test_dice_notation_rejects_injection():
    malicious = "1d100; import os; os.system('rm -rf /')"
    with pytest.raises(ValueError):
        parse_dice(malicious)
```

---

## 5. Test Organization

### 5.1 Directory Structure
```
tests/
├── commands/
│   ├── test_boat_handling.py          # NEW
│   ├── test_roll.py                   # NEW
│   ├── test_river_encounter.py        # NEW
│   ├── test_weather.py                # NEW
│   ├── test_help.py                   # NEW
│   ├── test_constants.py              ✅ EXISTS
│   ├── test_error_handlers.py         ✅ EXISTS
│   ├── test_permissions.py            ✅ EXISTS
│   ├── services/
│   │   ├── test_boat_handling_service.py  ✅ EXISTS
│   │   ├── test_roll_service.py           ✅ EXISTS
│   │   ├── test_encounter_service.py      ✅ EXISTS
│   │   └── test_command_logger.py         ✅ EXISTS
│   └── weather_modules/
│       ├── test_handler.py            # NEW
│       ├── test_formatters.py         # NEW
│       ├── test_stages.py             # NEW
│       ├── test_models.py             ✅ EXISTS
│       ├── test_exceptions.py         ✅ EXISTS
│       └── services/
│           ├── test_journey_service.py    ✅ EXISTS
│           ├── test_daily_weather_service.py  ✅ EXISTS
│           ├── test_display_service.py   ✅ EXISTS
│           └── test_notification_service.py  ✅ EXISTS
├── utils/
│   ├── test_wfrp_mechanics.py         ✅ EXISTS
│   ├── test_encounter_mechanics.py    ✅ EXISTS
│   ├── test_modifier_calculator.py    ✅ EXISTS
│   ├── test_weather_mechanics.py      # NEW
│   ├── test_weather_impact.py         # NEW
│   └── test_weather_modifier_service.py  ✅ EXISTS
├── db/
│   ├── test_character_data.py         # NEW
│   ├── test_weather_data.py           # NEW
│   ├── test_weather_storage.py        # NEW
│   ├── test_encounter_data.py         ✅ EXISTS
│   ├── models/
│   │   ├── test_character_models.py   ✅ EXISTS
│   │   ├── test_weather_models.py     ✅ EXISTS
│   │   └── test_encounter_models.py   # NEW
│   └── repositories/
│       ├── test_journey_repository.py ✅ EXISTS
│       └── test_weather_repository.py ✅ EXISTS
└── integration/
    ├── test_e2e_command_flows.py      ✅ EXISTS
    ├── test_main_composition.py       ✅ EXISTS
    └── test_stateful_weather_journeys.py  ✅ EXISTS
```

### 5.2 Naming Convention
- **Test files**: `test_<module>.py`
- **Test functions**: `test_<what>__<should>_<expected>()`
- **Fixtures**: `<resource>_<state>` (e.g., `weather_journey_active`)

---

## 6. Test Quality Standards

### 6.1 Determinism
- ✅ Seed all random number generators
- ✅ Mock time with `freezegun`
- ✅ Mock Discord API calls
- ✅ Mock file I/O for consistency

### 6.2 Speed
- ✅ Each test < 100ms target
- ✅ Mock network, disk, external APIs
- ✅ Use in-memory storage where possible

### 6.3 Clarity
- ✅ One logical assertion per test (may be multiple assert statements)
- ✅ Clear test names describing behavior
- ✅ Arrange-Act-Assert structure
- ✅ Minimal fixture complexity

### 6.4 Coverage Goals
- ⚠️ Coverage is **secondary** to bug finding
- Focus on **risk areas**, not line coverage %
- Intentionally skip:
  - Discord bot setup boilerplate
  - Legacy/deprecated code paths
  - Pure data dictionaries

---

## 7. Deliverables Checklist

- [x] Test Plan document (this file)
- [ ] Test files for all missing modules
- [ ] Property-based tests (Hypothesis) for parsers/validators
- [ ] Integration tests for cross-module flows
- [ ] Mutation testing configuration (mutmut)
- [ ] Performance smoke tests for hot paths
- [ ] BUGS_FOUND_BY_TESTS.md with discovered defects
- [ ] Traceability map (test → risk → module)

---

## 8. Implementation Priority Queue

### Phase 1: Critical Command Tests (Week 1)
1. `test_boat_handling.py` - Core mechanic
2. `test_roll.py` - Core mechanic
3. `test_river_encounter.py` - Core mechanic
4. `test_weather.py` - Core mechanic

### Phase 2: Data & Storage (Week 2)
5. `test_weather_storage.py` - High risk (file I/O)
6. `test_character_data.py` - Data integrity
7. `test_weather_data.py` - Data integrity
8. `test_encounter_models.py` - Validation

### Phase 3: Weather Modules (Week 3)
9. `test_handler.py` - Orchestration
10. `test_formatters.py` - Display logic
11. `test_stages.py` - Stage logic
12. `test_weather_mechanics.py` - Calculations
13. `test_weather_impact.py` - Impact calculations

### Phase 4: Polish & Utilities (Week 4)
14. `test_help.py` - Low risk
15. Property-based tests (Hypothesis)
16. Mutation testing
17. Performance smoke tests

---

## 9. Testing Tools & Dependencies

### 9.1 Core Dependencies
```
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-asyncio>=0.21.0
hypothesis>=6.82.0
freezegun>=1.2.0
pytest-mock>=3.11.0
```

### 9.2 Quality Tools
```
mutmut>=2.4.3       # Mutation testing
pytest-benchmark     # Performance testing
pytest-xdist        # Parallel test execution
```

### 9.3 Mocking Tools
```
unittest.mock        # Built-in mocking
pytest-mock         # pytest-specific utilities
discord.py test helpers
```

---

## 10. Intentionally Untested

### 10.1 Discord Bot Boilerplate
- **Rationale**: Framework code, low business logic
- **Files**: Bot setup, command registration decorators

### 10.2 Pure Data Dictionaries
- **Rationale**: No logic to test
- **Files**: `constants.py` (partially), static encounter tables

### 10.3 Legacy/Deprecated Code
- **Rationale**: Not in scope per TEST_RULES.md
- **Files**: Any files in legacy/, deprecated/, v1/, etc. (none found)

---

## 11. Success Metrics

### 11.1 Primary Metrics
- **Bugs Found**: Number of real defects discovered
- **Regression Prevention**: Known bugs have failing tests
- **Risk Coverage**: All identified risks have tests

### 11.2 Secondary Metrics
- **Line Coverage**: > 80% as guideline (not goal)
- **Branch Coverage**: > 70% as guideline
- **Mutation Score**: > 75% for critical modules

### 11.3 Quality Indicators
- **Test Speed**: Full suite < 10 seconds
- **Flakiness**: Zero flaky tests
- **Maintainability**: Tests pass on Python 3.13

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-01  
**Next Review**: After Phase 1 completion
