# Error Handling System Documentation

## Overview

This bot now has a comprehensive, two-layer error handling system:

1. **`commands/error_handlers.py`** - Original, basic handlers (backward compatible)
2. **`commands/exceptions.py`** - Custom exception classes with structured data
3. **`commands/enhanced_error_handlers.py`** - Advanced handlers with logging and recovery

## Architecture

```
User Input → Command
            ↓
    Business Logic (Service Layer)
            ↓
    Raises Exception
            ↓
    Exception Handler
            ↓
    1. Log with context
    2. Format user message
    3. Send Discord embed
    4. Track metrics
```

## Custom Exception Classes

### Exception Hierarchy

```
BotException (base)
├── CommandException
│   ├── InvalidParameterException
│   ├── MissingParameterException
│   ├── PermissionDeniedException
│   └── CommandNotAvailableException
├── DataException
│   ├── JourneyNotFoundException
│   ├── WeatherDataNotFoundException
│   ├── CharacterNotFoundException
│   └── DatabaseException
├── ValidationException
│   ├── DiceNotationException
│   ├── SkillValueException
│   ├── DifficultyException
│   └── RangeException
├── ServiceException
│   ├── WeatherGenerationException
│   ├── RollCalculationException
│   └── BoatHandlingException
└── DiscordIntegrationException
    ├── ChannelNotFoundException
    ├── MessageSendException
    └── EmbedCreationException
```

### Exception Attributes

All custom exceptions inherit from `BotException` and have:
- `message`: Technical error message for logs
- `user_message`: User-friendly message for Discord
- `context`: Dict with additional debugging info
- `recoverable`: Whether the error can be recovered from

## Usage Examples

### 1. Raising Custom Exceptions

```python
from commands.exceptions import JourneyNotFoundException, InvalidParameterException

def get_weather(guild_id: str):
    journey = storage.get_journey_state(guild_id)
    if not journey:
        raise JourneyNotFoundException(
            guild_id=guild_id,
            user_message="❌ No journey in progress. Use `/weather journey` to start one."
        )
    return journey

def validate_difficulty(difficulty: int):
    if not -50 <= difficulty <= 60:
        raise InvalidParameterException(
            parameter_name="difficulty",
            parameter_value=difficulty,
            expected="Value between -50 and +60",
            user_message=f"❌ Difficulty must be between -50 and +60.\nYou provided: {difficulty}"
        )
```

### 2. Handling Custom Exceptions

```python
from commands.enhanced_error_handlers import handle_bot_exception

async def weather_command(context, action, season, province, day, is_slash):
    try:
        journey = get_weather(guild_id)
        # ... command logic
    except BotException as e:
        await handle_bot_exception(context, e, is_slash, command_name="weather")
        return
```

### 3. Handling Validation Errors

```python
from commands.enhanced_error_handlers import handle_validation_error

async def roll_command(context, dice, target, modifier, is_slash):
    try:
        result = service.roll_simple_dice(dice)
        # ... command logic
    except ValueError as e:
        await handle_validation_error(
            context, 
            e, 
            is_slash, 
            command_name="roll",
            usage_examples=["/roll 1d100", "/roll 3d6+2", "/roll 1d20-3"]
        )
        return
```

### 4. Handling Database Errors

```python
from commands.enhanced_error_handlers import handle_database_error

async def save_weather(guild_id, weather_data):
    try:
        storage.save_daily_weather(guild_id, weather_data)
    except sqlite3.Error as e:
        await handle_database_error(
            context,
            e,
            is_slash,
            operation="save_weather_data",
            recoverable=True  # User can retry
        )
        return
```

### 5. Handling Discord API Errors

```python
from commands.enhanced_error_handlers import handle_discord_api_error

async def send_notification(guild, channel_name, embed):
    try:
        channel = discord.utils.get(guild.channels, name=channel_name)
        await channel.send(embed=embed)
    except discord.Forbidden as e:
        await handle_discord_api_error(
            context,
            e,
            is_slash,
            operation=f"send message to #{channel_name}"
        )
        return
```

### 6. Using Error Logger

```python
from commands.enhanced_error_handlers import error_logger

# Manually log errors
error_logger.log_error(
    error=exception,
    command_name="weather",
    guild_id="123456789",
    user_id="987654321",
    context_data={"season": "summer", "day": 5}
)

# Log warnings
error_logger.log_warning(
    "Auto-starting journey with default settings",
    command_name="weather",
    context_data={"reason": "No active journey"}
)

# Get error statistics
stats = error_logger.get_stats()
print(f"Total errors: {stats['total']}")
print(f"ValueError count: {stats['by_type'].get('ValueError', 0)}")
```

### 7. Error Recovery

```python
from commands.enhanced_error_handlers import ErrorRecovery

# Auto-create journey if missing
recovery = ErrorRecovery()
created = await recovery.auto_create_journey_if_missing(
    storage=storage,
    guild_id=guild_id,
    season="summer",
    province="reikland"
)

if created:
    await send_warning_embed(
        context,
        "⚠️ Journey Auto-Created",
        "No journey was in progress. Started a new journey with default settings.",
        is_slash
    )
```

## Migration Guide

### Converting Existing Commands

**Before (old style):**
```python
try:
    result = dangerous_operation()
except ValueError as e:
    await handle_value_error(
        context, 
        e, 
        is_slash, 
        "CommandName",
        usage_examples=["/command example"]
    )
```

**After (enhanced style):**
```python
from commands.exceptions import ValidationException
from commands.enhanced_error_handlers import handle_validation_error

try:
    result = dangerous_operation()
except (ValueError, ValidationException) as e:
    await handle_validation_error(
        context, 
        e, 
        is_slash, 
        "command_name",
        usage_examples=["/command example"]
    )
```

### Adding Custom Exceptions to Services

**Before:**
```python
def get_journey(guild_id):
    journey = storage.get_journey_state(guild_id)
    if not journey:
        raise ValueError(f"No journey found for guild {guild_id}")
    return journey
```

**After:**
```python
from commands.exceptions import JourneyNotFoundException

def get_journey(guild_id):
    journey = storage.get_journey_state(guild_id)
    if not journey:
        raise JourneyNotFoundException(
            guild_id=guild_id,
            user_message="❌ No journey in progress. Use `/weather journey` to start one."
        )
    return journey
```

## Best Practices

### 1. Always Provide User-Friendly Messages

```python
# ❌ Bad
raise ValueError("Invalid target value")

# ✅ Good
raise SkillValueException(
    skill_value=target,
    user_message="❌ Skill value must be between 1 and 100.\nYou provided: 150"
)
```

### 2. Include Context Information

```python
# ❌ Bad
raise WeatherGenerationException("Failed to generate weather")

# ✅ Good
raise WeatherGenerationException(
    guild_id=guild_id,
    day=5,
    reason="Invalid season data",
    user_message="❌ Failed to generate weather. Please try again."
)
```

### 3. Use Specific Exception Types

```python
# ❌ Bad
raise Exception("Something went wrong")

# ✅ Good
raise DatabaseException(
    operation="save_weather_data",
    original_error=e,
    user_message="❌ Failed to save weather data. Please try again."
)
```

### 4. Log Errors Appropriately

```python
# ❌ Bad - No logging
try:
    result = operation()
except Exception:
    pass  # Silent failure

# ✅ Good - Log with context
try:
    result = operation()
except Exception as e:
    error_logger.log_error(
        error=e,
        command_name="command_name",
        guild_id=guild_id,
        context_data={"param": value}
    )
    await handle_generic_error(context, e, is_slash, "command_name")
```

### 5. Provide Recovery Options

```python
# ❌ Bad - No guidance
raise JourneyNotFoundException(guild_id=guild_id)

# ✅ Good - Tell user what to do
raise JourneyNotFoundException(
    guild_id=guild_id,
    user_message=(
        "❌ No journey in progress.\n\n"
        "**Start a new journey:**\n"
        "`/weather journey season:summer province:reikland`"
    )
)
```

## Error Message Templates

### User-Facing Messages

```python
# Not Found Errors
"❌ No {item} found.\nUse `{command}` to {action}."

# Validation Errors
"❌ Invalid {parameter}: **{value}**\nExpected: {expected}"

# Permission Errors
"🔒 Permission Denied\nThis command requires **{permission}** role."

# Range Errors
"❌ **{parameter}** must be between {min} and {max}.\nYou provided: {value}"

# Missing Parameter Errors
"❌ Missing required parameter: **{parameter}**\n\n**Example:** `{example}`"
```

### Log Messages

```python
# Error Logs
f"[ERROR] Command: {command_name} | Guild: {guild_id} | Error: {error_type}"

# Warning Logs
f"[WARNING] {message} | Command: {command_name} | Context: {context_data}"

# Info Logs
f"[INFO] {operation} completed | Guild: {guild_id} | Result: {result}"
```

## Testing Error Handling

### Unit Test Example

```python
import pytest
from commands.exceptions import JourneyNotFoundException
from commands.enhanced_error_handlers import handle_bot_exception

@pytest.mark.asyncio
async def test_journey_not_found_exception():
    # Create mock context
    mock_context = MockInteraction()
    
    # Create exception
    error = JourneyNotFoundException(
        guild_id="123",
        user_message="❌ No journey found."
    )
    
    # Handle exception
    success = await handle_bot_exception(
        mock_context, 
        error, 
        is_slash=True, 
        command_name="weather"
    )
    
    # Assert
    assert success is True
    assert mock_context.response.was_called()
    assert "No journey found" in mock_context.response.embed.description
```

## Performance Considerations

1. **Error Logging:** Logs are written asynchronously to not block command execution
2. **Context Data:** Only essential context is logged to avoid memory bloat
3. **Stack Traces:** Only logged for debugging, not sent to users
4. **Error Metrics:** Lightweight counters that don't impact performance

## Future Enhancements

Possible improvements for the error handling system:

1. **Error Reporting Dashboard:** Web interface to view error statistics
2. **Automatic Bug Reports:** Send critical errors to a dedicated channel
3. **Error Retrying:** Automatic retry logic for transient failures
4. **User Error History:** Track per-user error patterns for debugging
5. **Error Analytics:** Analyze error patterns to identify systemic issues

## Summary

This error handling system provides:

✅ **Structured Exceptions:** Clear hierarchy of error types
✅ **User-Friendly Messages:** Helpful, actionable error messages
✅ **Comprehensive Logging:** Full context for debugging
✅ **Error Recovery:** Automatic recovery strategies
✅ **Backward Compatibility:** Works with existing code
✅ **Easy Migration:** Simple to convert old error handling
✅ **Best Practices:** Encourages good error handling patterns

The system makes debugging easier and provides better user experience when errors occur.
