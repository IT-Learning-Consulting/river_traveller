# BUG-001: Fumbles Don't Override Success in WFRP Rolls

**Priority:** 🔴 CRITICAL
**Status:** Open
**Discovered:** 2025-11-01
**Category:** Game Mechanics / Business Logic
**Affected Component:** `commands/services/roll_service.py`

---

## Summary

When a character rolls 100 on a d100 WFRP skill test, the code correctly identifies it as a fumble (`is_fumble=True`) but fails to override the `success` field to `False`. This means characters with high skills can succeed on rolls that should always fail according to WFRP 4th Edition rules.

## Impact

- **Severity:** HIGH - Violates core WFRP game rules
- **Frequency:** Rare (1% chance per roll when target ≥ 100)
- **User Impact:** Game balance broken for high-skill characters
- **Data Corruption:** None
- **Security Impact:** None

## Technical Details

**Location:** `commands/services/roll_service.py:217-259`

**Root Cause:**
After calculating `success = roll_value <= final_target` (line 218), the code sets fumble detection flags but never updates the `success` boolean variable.

```python
# Lines 227-231 (CURRENT CODE - BUGGY)
if roll_value == WFRP_ROLL_FUMBLE:
    is_double = True
    is_fumble = True
    doubles_classification = "fumble"
    # BUG: success is NOT set to False here!
```

**Expected Behavior:**
According to WFRP 4th Edition rules:
- Rolling 100 is ALWAYS a fumble
- Fumbles ALWAYS fail, regardless of target value
- Criticals (doubles ≤ target) ALWAYS succeed

**Actual Behavior:**
- Rolling 100 with target=100 → `success=True, is_fumble=True` (contradictory state)
- The outcome text shows "✅ Success | SL: +0 | 💀 Fumble!" which is nonsensical

## Reproduction Steps

1. Create a character with skill value of 100 (or 90+ with modifiers)
2. Roll a WFRP skill test
3. When the roll is exactly 100:
   - Check `result.is_fumble` → `True` ✓
   - Check `result.success` → `True` ✗ (should be `False`)
   - Observe outcome text shows both success and fumble

**Test Code:**
```python
from commands.services.roll_service import RollService
from unittest.mock import patch

service = RollService()
with patch('commands.services.roll_service.roll_dice', return_value=[100]):
    result = service.roll_wfrp_test("1d100", target=100, difficulty=0)
    print(f"success={result.success}, is_fumble={result.is_fumble}")
    # Output: success=True, is_fumble=True (WRONG!)
```

## Evidence

**Failed Tests:**
- `tests/commands/services/test_roll_service.py::test_roll_of_100_always_fumble` (XFAIL)
- `tests/commands/services/test_roll_service.py::test_fumble_overrides_success` (XFAIL)
- `tests/commands/services/test_roll_service.py::test_maximum_possible_skill_target_100` (XFAIL)

**Test Output:**
```
AssertionError: assert True is False
  where True = RollResult(..., success=True, is_fumble=True, ...).success
```

## Recommended Fix

Add success override logic after fumble/critical detection:

```python
# After line 242 (after doubles detection)
# Fumbles always fail, criticals always succeed (WFRP 4e rules)
if is_fumble:
    success = False
elif is_critical:
    success = True
```

**Complete Fix (lines 244-250):**
```python
# Build outcome text
outcome_parts = []

# Apply fumble/critical overrides BEFORE generating outcome text
if is_fumble:
    success = False  # NEW: Fumbles always fail
elif is_critical:
    success = True   # NEW: Criticals always succeed

if success:
    outcome_parts.append(f"✅ Success | SL: {success_level:+d}")
else:
    outcome_parts.append(f"❌ Failure | SL: {success_level:+d}")
```

## Related Issues

- **BUG-002** (Potential): Same pattern may exist in `boat_handling_service.py` (needs verification)
- **BUG-003** (Potential): Critical success override may also be missing (needs testing)

## Additional Context

**WFRP 4th Edition Rules (p. 151-152):**
> "If you roll a double (11, 22, 33, etc.) on a Test, you may have scored a Critical, or a Fumble, depending on whether you succeed or fail. [...] A roll of 100 is always a Fumble, and always fails."

**Game Impact:**
This bug makes high-skill characters (skill 90+) significantly more powerful than intended, as they can succeed on rolls that should catastrophically fail. This could affect:
- Combat outcomes
- Dangerous skill tests (climbing, navigation, etc.)
- Dramatic moments where fumbles create narrative tension

## References

- Test file: `tests/commands/services/test_roll_service.py`
- Source file: `commands/services/roll_service.py`
- WFRP 4e Core Rulebook, p. 151-152 (Success & Failure)
- Bug tracking doc: `BUGS_FOUND_BY_TESTS.md`
