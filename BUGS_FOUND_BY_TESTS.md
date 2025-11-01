# Bugs Found by Test Suite

This document tracks real bugs discovered while creating comprehensive tests for the Travelling Bot.

## Critical Bugs

### 1. Fumbles Don't Override Success (WFRP Roll Service)
**Severity:** HIGH - Affects game mechanics
**Location:** `commands/services/roll_service.py`, lines 217-259
**Found by:** `test_roll_service.py::test_roll_of_100_always_fumble`

**Description:**
When a character rolls 100 on a d100 WFRP skill test, the code correctly identifies it as a fumble (`is_fumble=True`) but does not override the `success` field. If the character's target is 100, the roll succeeds (100 ≤ 100) even though it should always fail.

**Impact:**
- Rolling 100 with a skill of 100 (or 90+ with bonuses) incorrectly succeeds
- Violates WFRP 4th Edition rules (100 is always a fumble)
- Could make high-skill characters too powerful
- Similarly, criticals may not override failures properly

**Root Cause:**
After calculating `success = roll_value <= final_target` (line 218), the code sets fumble flags but never updates the `success` variable. The code needs to add:
```python
# After lines 228-242 (fumble/critical detection)
# Fumbles always fail, criticals always succeed
if is_fumble:
    success = False
elif is_critical:
    success = True
```

**Evidence:**
```python
# Current code (lines 228-231):
if roll_value == WFRP_ROLL_FUMBLE:
    is_double = True
    is_fumble = True
    doubles_classification = "fumble"
# Success is NOT set to False!
```

**Related Tests:**
- `test_roll_of_100_always_fumble` (XFAIL)
- `test_fumble_overrides_success` (XFAIL)
- `test_maximum_possible_skill_target_100` (XFAIL)

---

## Test Coverage Summary

### Roll Service Tests
- **Total Tests:** 39
- **Passing:** 36
- **Known Bugs (XFAIL):** 3
- **Coverage Areas:**
  - Simple dice rolling (8 tests)
  - WFRP skill test mechanics (10 tests)
  - Doubles detection (criticals/fumbles) (8 tests)
  - Outcome text generation (4 tests)
  - Edge cases and boundaries (9 tests)

---

## Recommendations

1. **Fix fumble/critical override logic** - High priority, affects core game mechanics
2. **Add similar tests for boat handling service** - May have same pattern
3. **Test critical success override** - Verify criticals also properly override failures
4. **Integration test** - Test full Discord command flow with fumble scenarios
