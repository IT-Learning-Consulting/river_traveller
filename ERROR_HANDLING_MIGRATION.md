# Error Handling Migration Checklist

## Files Created

✅ **`commands/exceptions.py`** - Custom exception classes (70+ exception types)
✅ **`commands/enhanced_error_handlers.py`** - Enhanced error handlers with logging
✅ **`ERROR_HANDLING_GUIDE.md`** - Comprehensive documentation
✅ **`ERROR_HANDLING_QUICK_REF.md`** - Quick reference for common patterns
✅ **`ERROR_HANDLING_MIGRATION.md`** - This checklist

## System Overview

### Exception Classes (commands/exceptions.py)

**Base Exception:**
- `BotException` - All custom exceptions inherit from this

**5 Main Categories:**
1. `CommandException` - Command-level errors (parameters, permissions)
2. `DataException` - Data access errors (not found, database issues)
3. `ValidationException` - Input validation errors (dice notation, ranges)
4. `ServiceException` - Business logic errors (weather gen, roll calc)
5. `DiscordIntegrationException` - Discord API errors (channels, messages)

**Total: 20+ specific exception classes**

### Error Handlers (commands/enhanced_error_handlers.py)

**Core Handlers:**
- `handle_bot_exception()` - Main handler for custom exceptions
- `handle_validation_error()` - Validation and ValueError handling
- `handle_database_error()` - Database operation errors
- `handle_discord_api_error()` - Discord API errors
- `handle_generic_error()` - Catch-all for unexpected errors

**Utilities:**
- `ErrorLogger` - Centralized logging with metrics
- `ErrorRecovery` - Automatic recovery strategies
- `send_error_embed()` - Enhanced error message sender
- `send_warning_embed()` - Warning message sender

## Migration Priority

### High Priority (Core Commands)

These commands handle most user interactions:

- [ ] **commands/roll.py** - Dice rolling
  - Current: Basic ValueError handling
  - Add: DiceNotationException, RangeException
  - Test: Invalid notation, out of range values

- [ ] **commands/boat_handling.py** - Boat handling tests
  - Current: ValueError, basic error handling
  - Add: CharacterNotFoundException, ValidationException
  - Test: Invalid character, missing weather data

- [ ] **commands/weather.py** - Weather management
  - Current: ValueError, generic Exception
  - Add: JourneyNotFoundException, WeatherGenerationException
  - Test: No journey, invalid parameters

- [ ] **commands/river_encounter.py** - River encounters
  - Current: Basic Discord error handling
  - Add: DataException, ServiceException
  - Test: Data access errors, generation failures

### Medium Priority (Services)

These services need exception improvements:

- [ ] **commands/services/roll_service.py**
  - Add: RollCalculationException
  - Replace: Generic ValueError with specific exceptions

- [ ] **commands/services/boat_handling_service.py**
  - Add: BoatHandlingException
  - Replace: ValueError with specific exceptions

- [ ] **commands/weather_modules/services/daily_weather_service.py**
  - Add: WeatherGenerationException
  - Replace: Generic exceptions with specific ones

- [ ] **commands/weather_modules/services/journey_service.py**
  - Add: JourneyNotFoundException, DatabaseException
  - Already has some ValueError - convert to custom exceptions

### Low Priority (Utilities)

These are called by services and don't directly interact with users:

- [ ] **utils/wfrp_mechanics.py**
  - Add: DiceNotationException, SkillValueException
  - Replace: ValueError with specific exceptions

- [ ] **utils/weather_mechanics.py**
  - Add: WeatherGenerationException
  - Currently uses dict returns - consider exceptions

- [ ] **db/weather_storage.py**
  - Add: DatabaseException
  - Wrap sqlite3.Error with custom exceptions

## Step-by-Step Migration for Each Command

### Template Checklist

For each command file (e.g., `roll.py`):

#### 1. Add Imports

```python
# At top of file
from commands.exceptions import (
    # Add specific exceptions you need
    DiceNotationException,
    InvalidParameterException,
    # ...etc
)
from commands.enhanced_error_handlers import (
    handle_bot_exception,
    handle_validation_error,
    handle_generic_error,
    error_logger,
)
```

#### 2. Identify Error Points

- [ ] List all try/except blocks
- [ ] List all error-prone operations (parsing, DB access, API calls)
- [ ] List all validation checks
- [ ] Note current error types (ValueError, KeyError, etc.)

#### 3. Replace Generic Exceptions

**Before:**
```python
if not valid:
    raise ValueError("Invalid input")
```

**After:**
```python
if not valid:
    raise InvalidParameterException(
        parameter_name="dice",
        parameter_value=value,
        expected="XdY format",
        user_message="❌ Invalid dice notation"
    )
```

#### 4. Update Exception Handlers

**Before:**
```python
except ValueError as e:
    await handle_value_error(context, e, is_slash, "Command")
```

**After:**
```python
except (ValueError, ValidationException) as e:
    await handle_validation_error(context, e, is_slash, "command")
```

#### 5. Add Logging

```python
# Add at error points
error_logger.log_error(
    error=e,
    command_name="command_name",
    guild_id=guild_id,
    context_data={"param": value}
)
```

#### 6. Add Error Recovery

```python
# For recoverable errors
try:
    journey = storage.get_journey_state(guild_id)
    if not journey:
        # Auto-recovery
        recovery = ErrorRecovery()
        created = await recovery.auto_create_journey_if_missing(...)
        if created:
            await send_warning_embed(...)
```

#### 7. Test Error Scenarios

- [ ] Test with invalid inputs
- [ ] Test with missing data
- [ ] Test with permission issues
- [ ] Test with API errors
- [ ] Verify error messages are user-friendly
- [ ] Verify logging works correctly

## Detailed Migration Steps by Command

### 1. commands/roll.py

**Error Points:**
- Dice notation parsing
- Target value validation
- Modifier range validation

**Changes:**
```python
# Add imports
from commands.exceptions import (
    DiceNotationException,
    SkillValueException,
    DifficultyException,
)
from commands.enhanced_error_handlers import handle_validation_error

# In _perform_roll:
try:
    if target is not None:
        result = service.roll_wfrp_test(dice, target, modifier)
    else:
        result = service.roll_simple_dice(dice)
        
except ValueError as e:
    # Parse error - convert to DiceNotationException
    error = DiceNotationException(
        notation=dice,
        reason=str(e),
        user_message=f"❌ Invalid dice notation: **{dice}**"
    )
    await handle_bot_exception(context, error, is_slash, "roll")
    return
```

**Test Cases:**
- [ ] `/roll xyz` - Invalid notation
- [ ] `/roll 1d100 target:200` - Invalid target
- [ ] `/roll 1d100 target:50 modifier:100` - Invalid modifier

### 2. commands/boat_handling.py

**Error Points:**
- Character lookup
- Weather data access
- Skill value validation

**Changes:**
```python
# Add imports
from commands.exceptions import (
    CharacterNotFoundException,
    WeatherDataNotFoundException,
)
from commands.enhanced_error_handlers import handle_bot_exception

# In _perform_boat_handling:
try:
    character = get_character(character_name)
    if not character:
        available = get_available_characters()
        raise CharacterNotFoundException(
            character_name=character_name,
            available_characters=available
        )
    
    # ... rest of command logic

except CharacterNotFoundException as e:
    await handle_bot_exception(context, e, is_slash, "boat-handling")
    return
```

**Test Cases:**
- [ ] `/boat-handling bobby` - Invalid character
- [ ] `/boat-handling anara difficulty:100` - Invalid difficulty
- [ ] Test with no active weather

### 3. commands/weather.py

**Error Points:**
- Journey existence check
- Season/province validation
- Day parameter validation

**Changes:**
```python
# Add imports
from commands.exceptions import (
    JourneyNotFoundException,
    MissingParameterException,
    InvalidParameterException,
)
from commands.enhanced_error_handlers import handle_bot_exception

# In handle_command:
try:
    if action == "journey":
        if not season or not province:
            raise MissingParameterException(
                parameter_name="season and province",
                command_name="weather journey",
                example="/weather journey season:summer province:reikland"
            )
    
    # ... route to action handlers

except BotException as e:
    await handle_bot_exception(context, e, is_slash, "weather")
    return
```

**Test Cases:**
- [ ] `/weather next` - No journey (should auto-create)
- [ ] `/weather journey` - Missing parameters
- [ ] `/weather view day:100` - Invalid day

### 4. commands/river_encounter.py

**Error Points:**
- Encounter data access
- Channel lookup for notifications
- Embed creation

**Changes:**
```python
# Add imports
from commands.exceptions import (
    DataException,
    ChannelNotFoundException,
)
from commands.enhanced_error_handlers import (
    handle_bot_exception,
    error_logger,
)

# In command:
try:
    encounter = service.generate_encounter(encounter_type)
    
    # Send to channel
    channel = discord.utils.get(guild.channels, name=CHANNEL_GM_NOTIFICATIONS)
    if not channel:
        # Log warning but don't fail
        error_logger.log_warning(
            f"Channel {CHANNEL_GM_NOTIFICATIONS} not found",
            command_name="river-encounter"
        )
    else:
        await channel.send(embed=gm_embed)

except Exception as e:
    await handle_generic_error(context, e, is_slash, "river-encounter")
    return
```

**Test Cases:**
- [ ] Test with missing notification channel
- [ ] Test with invalid encounter type
- [ ] Test permission errors

## Validation After Migration

### For Each Migrated Command:

- [ ] Code compiles without errors
- [ ] Bot starts successfully
- [ ] Command works with valid inputs
- [ ] Error messages are user-friendly
- [ ] Errors are logged correctly
- [ ] Stack traces captured for debugging
- [ ] No information leakage in user messages
- [ ] Recovery strategies work correctly

### Integration Tests:

- [ ] Run all commands with valid inputs
- [ ] Test all error scenarios
- [ ] Check error logs for completeness
- [ ] Verify error counts in statistics
- [ ] Test error recovery mechanisms
- [ ] Check Discord embed formatting
- [ ] Verify ephemeral messages work correctly

## Rollback Plan

If issues arise after migration:

1. **Keep old error_handlers.py** - Don't delete it
2. **Add new handlers gradually** - One command at a time
3. **Test thoroughly** - Before moving to next command
4. **Monitor logs** - Watch for unexpected errors
5. **Easy rollback** - Just remove new imports and handlers

## Backward Compatibility

The new system is backward compatible:

✅ Old `handle_value_error()` still works
✅ Old `handle_discord_error()` still works
✅ Old `send_error_embed()` still works (enhanced version compatible)
✅ Can mix old and new error handling
✅ Gradual migration supported

## Progress Tracking

### Commands Status

| Command | Priority | Status | Notes |
|---------|----------|--------|-------|
| roll.py | High | ✅ Complete | Enhanced error handling, validation, logging |
| boat_handling.py | High | ✅ Complete | CharacterNotFoundException, validation |
| weather.py | High | ✅ Complete | Permission checks, validation migrated |
| weather_modules/handler.py | High | ✅ Complete | Auto-recovery, MissingParameterException |
| river_encounter.py | High | ✅ Complete | PermissionDeniedException, error logging |
| help.py | Low | ⬜ Not Started | Info only, minimal errors |

### Services Status

| Service | Priority | Status | Notes |
|---------|----------|--------|-------|
| roll_service.py | Medium | ⬜ Not Started | Dice logic |
| boat_handling_service.py | Medium | ⬜ Not Started | Test logic |
| daily_weather_service.py | Medium | ⬜ Not Started | Weather gen |
| journey_service.py | Medium | ⬜ Not Started | Journey management |

### Utilities Status

| Utility | Priority | Status | Notes |
|---------|----------|--------|-------|
| wfrp_mechanics.py | Low | ⬜ Not Started | Core mechanics |
| weather_mechanics.py | Low | ⬜ Not Started | Weather logic |
| weather_storage.py | Medium | ⬜ Not Started | Database access |

### Legend

- ⬜ Not Started
- 🟡 In Progress
- ✅ Complete
- ❌ Blocked/Issues

## Next Steps

1. **Start with roll.py** - Simplest command, good test case
2. **Test thoroughly** - Verify error handling works
3. **Move to boat_handling.py** - More complex, multiple error types
4. **Continue with weather.py** - Most complex command
5. **Update services** - After commands are working
6. **Update utilities** - Last, as they're called by services

## Questions to Answer During Migration

- [ ] Are error messages clear and actionable?
- [ ] Is enough context logged for debugging?
- [ ] Are recovery strategies appropriate?
- [ ] Is logging level appropriate (ERROR vs WARNING)?
- [ ] Should errors be ephemeral or public?
- [ ] Are stack traces properly captured?
- [ ] Is performance acceptable?

## Success Criteria

✅ All commands handle errors gracefully
✅ Users get helpful error messages
✅ Developers get detailed logs
✅ Error recovery works automatically where appropriate
✅ No bot crashes from unhandled exceptions
✅ Error statistics tracked correctly
✅ Code is more maintainable
✅ Testing is easier

## Timeline Estimate

**Per Command:**
- High Priority: 1-2 hours each
- Medium Priority: 30-60 minutes each
- Low Priority: 15-30 minutes each

**Total Estimate:**
- Commands: ~6-8 hours
- Services: ~3-4 hours
- Utilities: ~2-3 hours
- Testing: ~4-5 hours
- **Total: 15-20 hours**

## Support

If issues arise during migration:

1. Check `ERROR_HANDLING_GUIDE.md` for detailed patterns
2. Check `ERROR_HANDLING_QUICK_REF.md` for code examples
3. Review exception classes in `commands/exceptions.py`
4. Test error handlers in `commands/enhanced_error_handlers.py`
5. Check logs for error details

## Notes

- Migration can be done gradually (one command at a time)
- Old error handling continues to work during migration
- New system is fully backward compatible
- Focus on user experience (helpful messages)
- Prioritize logging (debugging future issues)
- Test error scenarios thoroughly
- Document any new patterns discovered
