# AI-Guided TDD: Quick Reference Card

## 🎯 The Golden Rule
**Tests define the behavior. AI implements to pass tests. No exceptions.**

---

## 📋 Implementation Order

### Phase 1: Database (2-3 hours)
```bash
pytest tests/test_weather_storage_schema.py -v
```
**File to modify**: `db/weather_storage.py`
**Tests to pass**: 15 database schema tests

### Phase 2: Core Mechanics (4-6 hours) ⚠️ MOST COMPLEX
```bash
pytest tests/test_weather_mechanics_events.py -v
```
**File to modify**: `utils/weather_mechanics.py`
**Tests to pass**: 30 mechanics tests
**Critical**: Nesting bug prevention, daily variation

### Phase 3: Handler Integration (2-3 hours)
```bash
pytest tests/test_handler_integration.py -v
```
**File to modify**: `commands/weather_modules/handler.py`
**Tests to pass**: 18 integration tests

### Phase 4: Display Updates (2-3 hours)
```bash
pytest tests/test_display_formatting.py -v
```
**Files to modify**: `commands/weather_modules/stages.py`, `commands/weather_modules/notifications.py`
**Tests to pass**: 15 display tests

---

## 🤖 AI Prompt Templates

### Starting a Phase
```
I'm implementing Phase X from longer_weather_plan.md.

Here are the tests that must pass:
[Paste relevant test file: tests/test_XXXXX.py]

Current code to modify:
[Paste existing file content]

Implement changes to make ALL tests pass. Follow the test specifications exactly.
```

### Fixing Failing Tests
```
X tests are failing:

Test: test_function_name
Error: [paste error message]
Expected: [what test expects]
Got: [what code returned]

Current implementation:
[paste relevant code section]

Fix the implementation to make this test pass WITHOUT breaking currently passing tests.
```

### Verifying Implementation
```
I've implemented [feature]. Run these verification steps:

1. Check test results:
   pytest tests/test_XXXXX.py -v

2. If tests pass, verify:
   - No other tests broke: pytest tests/ -v
   - Coverage is good: pytest tests/ --cov=[module]

3. If tests fail, provide:
   - Failed test names
   - Error messages
   - Relevant code sections
```

---

## 🚨 Critical Tests (Must Monitor)

### 1. The Nesting Bug (Phase 2)
```python
test_roll_2_during_active_cold_front_does_NOT_trigger_nested_event
```
**What it prevents**: Roll=2 during active cold front shouldn't trigger NEW cold front

### 2. Daily Variation Correctness (Phase 2)
```python
test_category_recalculated_from_final_temperature
```
**What it prevents**: Display showing wrong temperature category (base vs final)

### 3. Special Roll Suppression (Phase 2)
```python
test_special_roll_suppressed_during_cold_front
test_special_roll_suppressed_during_heat_wave
```
**What it prevents**: Event triggers from daily variation rolls during active events

### 4. Cooldown Lifecycle (Phase 3)
```python
test_10_day_journey_with_cold_front_lifecycle
```
**What it prevents**: Cooldown tracking failures over multi-day journeys

---

## 🔧 Useful Commands

```bash
# Run all tests
pytest tests/ -v

# Run specific phase
pytest tests/test_weather_storage_schema.py -v

# Run one test
pytest tests/test_file.py::TestClass::test_function -v

# Stop on first failure
pytest tests/ -x

# Show print statements (debugging)
pytest tests/ -v -s

# Run with coverage
pytest tests/ --cov=utils --cov=db --cov=commands/weather_modules

# HTML coverage report
pytest tests/ --cov=utils --cov=db --cov=commands/weather_modules --cov-report=html
# Open htmlcov/index.html

# Debug with pdb
pytest tests/test_file.py::test_function --pdb
```

---

## ✅ Success Criteria by Phase

| Phase | Passing Tests | Files Modified | Ready for Next Phase |
|-------|---------------|----------------|----------------------|
| Phase 1 | 15/15 ✅ | `weather_storage.py` | ✅ Move to Phase 2 |
| Phase 2 | 30/30 ✅ | `weather_mechanics.py` | ✅ Move to Phase 3 |
| Phase 3 | 18/18 ✅ | `handler.py` | ✅ Move to Phase 4 |
| Phase 4 | 15/15 ✅ | `stages.py`, `notifications.py` | ✅ Ready for deployment |

**Final Goal**: 78/78 tests passing, 90%+ coverage

---

## 🐛 Common AI Mistakes to Watch For

### Mistake 1: Not handling edge cases
**Test fails**: `test_single_day_cold_front_displays_correctly`
**Fix**: Ensure code handles minimum duration (1 day) correctly

### Mistake 2: Breaking existing functionality
**Test fails**: Previously passing test now fails
**Fix**: Tell AI: "This change broke test_X. Revert and fix without breaking existing tests."

### Mistake 3: Incorrect state transitions
**Test fails**: `test_cooldown_starts_incrementing_after_cold_front_ends`
**Fix**: Review state machine logic (active → ended → cooldown → expired)

### Mistake 4: Off-by-one errors
**Test fails**: `test_cold_front_continues_existing_event`
**Fix**: Check if decrementing happens at right time (before/after return)

### Mistake 5: Missing None checks
**Test fails**: `AttributeError: 'NoneType' object has no attribute 'get'`
**Fix**: Add defensive `.get()` or None checks before accessing dict keys

---

## 📊 Test Status Tracking

Use this checklist while implementing:

### Phase 1: Database
- [ ] Schema columns exist
- [ ] Migration preserves data
- [ ] Cooldown methods work
- [ ] Data persistence correct
- [ ] Edge cases handled
- **Status**: ___/15 passing

### Phase 2: Mechanics
- [ ] Cold front triggers correctly
- [ ] Heat wave triggers correctly
- [ ] Cooldown blocks events
- [ ] Mutual exclusivity works
- [ ] **Nesting bug prevented** ⚠️
- [ ] Daily variation works
- [ ] **Special rolls suppressed** ⚠️
- [ ] **Category recalculated** ⚠️
- [ ] Display messages correct
- [ ] Edge cases handled
- **Status**: ___/30 passing

### Phase 3: Handler
- [ ] State extraction correct
- [ ] Cooldowns passed to mechanics
- [ ] Cooldowns updated after each day
- [ ] New fields saved to database
- [ ] Multi-day stages work
- [ ] Full journey lifecycle works
- **Status**: ___/18 passing

### Phase 4: Display
- [ ] Stage day counters show
- [ ] GM notifications correct
- [ ] Player display correct
- [ ] Consistency across channels
- [ ] Edge cases handled
- **Status**: ___/15 passing

---

## 🎓 Remember

1. **Tests first, code second** - Never write code without a test to guide it
2. **One test at a time** - Fix tests incrementally, not all at once
3. **Green before refactor** - Only refactor when all tests pass
4. **AI follows tests** - Tests are the AI's instructions, not suggestions
5. **Regression checks** - Always verify old tests still pass after changes

---

## 🆘 When Stuck

1. **Read the test docstring** - It explains WHY the test exists
2. **Check test fixtures** - Understand the input data
3. **Run in isolation** - `pytest tests/test_file.py::test_function -v -s`
4. **Add debug prints** - Temporary `print()` statements in test
5. **Ask AI to explain** - "Explain what test_X is checking and why it's failing"

---

## 📈 Progress Tracking

Current Phase: _____
Tests Passing: ___/78
Coverage: ___%

Next Steps:
1. ___________________________
2. ___________________________
3. ___________________________

---

**Quick Win**: Start with Phase 1. It's the easiest and builds foundation for everything else.
**Hard Part**: Phase 2 (daily variation). Take your time, use tests as guide.
**Finish Line**: When you see "78 passed" you're done! 🎉
