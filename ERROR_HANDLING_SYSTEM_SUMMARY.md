# Error Handling System - Summary

## What Was Created

### 1. Custom Exception Classes (`commands/exceptions.py`)

A comprehensive hierarchy of 20+ custom exception classes organized into 5 main categories:

**CommandException** (4 classes)
- `InvalidParameterException` - Wrong parameter values
- `MissingParameterException` - Required parameters missing
- `PermissionDeniedException` - Permission issues
- `CommandNotAvailableException` - Feature not implemented

**DataException** (4 classes)
- `JourneyNotFoundException` - No active journey
- `WeatherDataNotFoundException` - Weather data not found
- `CharacterNotFoundException` - Character not in database
- `DatabaseException` - Database operation failures

**ValidationException** (4 classes)
- `DiceNotationException` - Invalid dice notation
- `SkillValueException` - Skill value out of range
- `DifficultyException` - Difficulty modifier out of range
- `RangeException` - Generic range validation

**ServiceException** (3 classes)
- `WeatherGenerationException` - Weather generation failures
- `RollCalculationException` - Dice roll calculation errors
- `BoatHandlingException` - Boat handling test errors

**DiscordIntegrationException** (3 classes)
- `ChannelNotFoundException` - Required channel not found
- `MessageSendException` - Failed to send Discord message
- `EmbedCreationException` - Failed to create embed

All exceptions include:
- `message` - Technical error for logs
- `user_message` - User-friendly message
- `context` - Dict with debugging data
- `recoverable` - Whether error can be recovered from

### 2. Enhanced Error Handlers (`commands/enhanced_error_handlers.py`)

**Core Handlers:**
- `handle_bot_exception()` - Main handler for custom exceptions
- `handle_validation_error()` - Validation/ValueError handling
- `handle_database_error()` - Database error handling
- `handle_discord_api_error()` - Discord API error handling
- `handle_generic_error()` - Catch-all for unexpected errors

**Enhanced Embed Senders:**
- `send_error_embed()` - Red error embeds with timestamps
- `send_warning_embed()` - Orange warning embeds
- Both return True/False for error recovery logic

**Logging System:**
- `ErrorLogger` class - Centralized error logging
  - Tracks error count and types
  - Logs full context and stack traces
  - Provides error statistics
- `error_logger` - Global instance

**Recovery Utilities:**
- `ErrorRecovery` class - Automatic recovery strategies
  - `auto_create_journey_if_missing()` - Create default journey
  - Extensible for other recovery patterns

**Helper Functions:**
- `format_error_for_user()` - Format exceptions for display
- `get_error_category()` - Categorize errors for metrics
- `with_error_handling()` - Decorator for automatic handling (future use)

### 3. Documentation

**`ERROR_HANDLING_GUIDE.md`** (Comprehensive Guide)
- Complete system overview
- Exception hierarchy explanation
- Usage examples for all exception types
- Handler usage examples
- Migration guide from old to new
- Best practices
- Testing strategies
- Performance considerations

**`ERROR_HANDLING_QUICK_REF.md`** (Quick Reference)
- 10 common error patterns with code
- Error recovery patterns
- Logging patterns
- Testing patterns
- Cheat sheet table
- Quick checklist

**`ERROR_HANDLING_MIGRATION.md`** (Migration Checklist)
- Step-by-step migration plan
- Priority levels (high/medium/low)
- Detailed steps for each command
- Progress tracking tables
- Success criteria
- Timeline estimates
- Rollback plan

## Key Features

### 1. Structured Error Information

Every exception carries:
```python
{
    "message": "Technical error description",
    "user_message": "❌ User-friendly message",
    "context": {
        "parameter": "value",
        "guild_id": "123",
        "other_data": "..."
    },
    "recoverable": True/False
}
```

### 2. Comprehensive Logging

All errors logged with:
- Error count (tracked)
- Error type (tracked for metrics)
- Command name
- Guild ID
- User ID
- Context data
- Stack trace

Example log:
```
[ERROR #42] Type: JourneyNotFoundException | Command: weather | Guild: 123456789 | User: 987654321
Error Message: No journey found for guild 123456789
Exception Context: {'guild_id': '123456789'}
Additional Context: {'action': 'next', 'auto_create': False}
Stack Trace:
...
```

### 3. User-Friendly Messages

All error messages follow patterns:
- Start with emoji (❌ ⚠️ 🔒 📦 etc.)
- Bold important information
- Provide actionable guidance
- Include examples where helpful
- Show what to do next

Example:
```
❌ No journey in progress.

Start a new journey:
`/weather journey season:summer province:reikland`
```

### 4. Error Recovery

Automatic recovery for common issues:
- Auto-create missing journey with defaults
- Retry failed operations
- Fallback to alternative methods
- Graceful degradation

### 5. Error Metrics

Track errors for analysis:
```python
stats = error_logger.get_stats()
# {
#     "total": 42,
#     "by_type": {
#         "ValueError": 15,
#         "JourneyNotFoundException": 10,
#         "DiceNotationException": 8,
#         ...
#     }
# }
```

### 6. Backward Compatible

- Old `handle_value_error()` still works
- Old `send_error_embed()` enhanced but compatible
- Can mix old and new error handling
- Gradual migration supported
- No breaking changes

## Benefits

### For Users
✅ Clear, actionable error messages
✅ Helpful guidance on what went wrong
✅ Examples showing correct usage
✅ Better overall experience

### For Developers
✅ Detailed error logs with full context
✅ Stack traces for debugging
✅ Error metrics for identifying patterns
✅ Structured exceptions easy to handle
✅ Less boilerplate code
✅ Consistent error handling patterns

### For Maintainability
✅ Centralized error handling logic
✅ Reusable exception classes
✅ Consistent error messages
✅ Easy to add new exception types
✅ Clear error categories
✅ Self-documenting code

## Example Usage

### Before (Old Style)
```python
try:
    journey = storage.get_journey_state(guild_id)
    if not journey:
        await send_error_embed(
            context,
            "❌ Error",
            "No journey found. Use /weather journey to start.",
            is_slash
        )
        return
except ValueError as e:
    await handle_value_error(context, e, is_slash, "Weather")
    return
```

### After (Enhanced Style)
```python
from commands.exceptions import JourneyNotFoundException
from commands.enhanced_error_handlers import handle_bot_exception

try:
    journey = storage.get_journey_state(guild_id)
    if not journey:
        raise JourneyNotFoundException(
            guild_id=guild_id,
            user_message="❌ No journey in progress.\nUse `/weather journey season:summer province:reikland` to start one."
        )
except JourneyNotFoundException as e:
    await handle_bot_exception(context, e, is_slash, "weather")
    return
```

### Benefits of New Style
1. **Structured** - Exception carries all context
2. **Logged** - Automatically logged with details
3. **Tracked** - Added to error metrics
4. **Consistent** - Same pattern everywhere
5. **Testable** - Easy to test exception handling
6. **Maintainable** - Clear what went wrong

## Integration Guide

### Step 1: Import What You Need

```python
from commands.exceptions import (
    JourneyNotFoundException,
    DiceNotationException,
    # ... other exceptions
)
from commands.enhanced_error_handlers import (
    handle_bot_exception,
    handle_validation_error,
    error_logger,
)
```

### Step 2: Raise Specific Exceptions

```python
# Instead of:
raise ValueError("Invalid input")

# Do:
raise DiceNotationException(
    notation=dice,
    reason="Missing die size",
    user_message="❌ Invalid dice notation"
)
```

### Step 3: Handle with Appropriate Handler

```python
try:
    # Command logic
    pass
except BotException as e:
    await handle_bot_exception(context, e, is_slash, "command_name")
    return
```

### Step 4: Log When Needed

```python
error_logger.log_warning(
    "Auto-creating journey with defaults",
    command_name="weather",
    context_data={"season": "summer", "province": "reikland"}
)
```

## Migration Plan

### Phase 1: High Priority Commands (6-8 hours)
1. roll.py
2. boat_handling.py
3. weather.py
4. river_encounter.py

### Phase 2: Services (3-4 hours)
1. roll_service.py
2. boat_handling_service.py
3. daily_weather_service.py
4. journey_service.py

### Phase 3: Utilities (2-3 hours)
1. wfrp_mechanics.py
2. weather_mechanics.py
3. weather_storage.py

### Phase 4: Testing (4-5 hours)
- Test all error scenarios
- Verify logging works
- Check error messages
- Validate recovery strategies

**Total Estimate: 15-20 hours**

## Success Metrics

After full migration:

✅ Zero unhandled exceptions crash bot
✅ All errors logged with context
✅ Users get helpful error messages
✅ Error recovery works automatically
✅ Debugging is faster with detailed logs
✅ Error patterns identified from metrics
✅ Code is more maintainable
✅ Testing is easier

## Files Overview

| File | Lines | Purpose |
|------|-------|---------|
| `commands/exceptions.py` | ~1000 | Exception class definitions |
| `commands/enhanced_error_handlers.py` | ~800 | Error handlers and logging |
| `ERROR_HANDLING_GUIDE.md` | ~600 | Comprehensive documentation |
| `ERROR_HANDLING_QUICK_REF.md` | ~400 | Quick reference guide |
| `ERROR_HANDLING_MIGRATION.md` | ~500 | Migration checklist |
| **Total** | **~3300** | Complete error handling system |

## Quick Start

1. Read `ERROR_HANDLING_QUICK_REF.md` for common patterns
2. Start with one command (e.g., `roll.py`)
3. Import required exceptions and handlers
4. Replace generic exceptions with specific ones
5. Test error scenarios thoroughly
6. Move to next command

## Support Resources

- **Comprehensive Guide**: `ERROR_HANDLING_GUIDE.md`
- **Quick Reference**: `ERROR_HANDLING_QUICK_REF.md`
- **Migration Checklist**: `ERROR_HANDLING_MIGRATION.md`
- **Exception Classes**: `commands/exceptions.py` (well-documented)
- **Error Handlers**: `commands/enhanced_error_handlers.py` (well-documented)

## Notes

- System is production-ready but not yet integrated
- Backward compatible with existing code
- Can be adopted gradually
- No breaking changes to existing functionality
- Focus on improving user experience and debugging
- Comprehensive logging for troubleshooting
- Extensible design for future needs

## Next Steps

1. ✅ Review documentation
2. ✅ Understand exception hierarchy
3. ✅ Study usage examples
4. ⬜ Choose first command to migrate (recommend `roll.py`)
5. ⬜ Test thoroughly
6. ⬜ Continue with other commands
7. ⬜ Monitor error logs
8. ⬜ Gather user feedback
9. ⬜ Adjust as needed

## Conclusion

This error handling system provides:
- **Structure** - Clear exception hierarchy
- **Consistency** - Same patterns everywhere
- **Logging** - Comprehensive error tracking
- **User Experience** - Helpful error messages
- **Maintainability** - Easier to debug and extend
- **Reliability** - Graceful error handling

The system is ready to use and will significantly improve both user experience and development workflow. Migration can be done gradually without breaking existing functionality.
