# Error Handling Quick Reference

## Common Error Patterns

### Pattern 1: Command With No Active Journey

```python
from commands.exceptions import JourneyNotFoundException
from commands.enhanced_error_handlers import handle_bot_exception

async def weather_command(context, action, is_slash):
    guild_id = str(context.guild.id)
    
    try:
        journey = storage.get_journey_state(guild_id)
        if not journey:
            raise JourneyNotFoundException(
                guild_id=guild_id,
                user_message="❌ No journey in progress.\nUse `/weather journey season:summer province:reikland` to start one."
            )
        
        # Command logic continues...
        
    except JourneyNotFoundException as e:
        await handle_bot_exception(context, e, is_slash, "weather")
        return
```

### Pattern 2: Invalid User Input (Dice Notation)

```python
from commands.exceptions import DiceNotationException
from commands.enhanced_error_handlers import handle_validation_error

async def roll_command(context, dice, is_slash):
    try:
        # Parse dice notation
        num_dice, die_size, modifier = parse_dice_notation(dice)
        
    except ValueError as e:
        # Convert to DiceNotationException
        error = DiceNotationException(
            notation=dice,
            reason=str(e),
            user_message=f"❌ Invalid dice notation: **{dice}**\n\nValid format: XdY+Z (e.g., 3d6, 1d100+5, 2d10-2)"
        )
        await handle_bot_exception(context, error, is_slash, "roll")
        return
```

### Pattern 3: Character Not Found

```python
from commands.exceptions import CharacterNotFoundException
from commands.enhanced_error_handlers import handle_bot_exception

async def boat_handling_command(context, character_name, is_slash):
    try:
        character = get_character(character_name)
        if not character:
            available = get_available_characters()
            raise CharacterNotFoundException(
                character_name=character_name,
                available_characters=available,
                user_message=f"❌ Character **{character_name}** not found.\n\n**Available:** {', '.join(available)}"
            )
        
        # Command logic continues...
        
    except CharacterNotFoundException as e:
        await handle_bot_exception(context, e, is_slash, "boat-handling")
        return
```

### Pattern 4: Out of Range Parameter

```python
from commands.exceptions import RangeException
from commands.enhanced_error_handlers import handle_bot_exception

async def stage_config_command(context, stage_duration, is_slash):
    try:
        if not 1 <= stage_duration <= 10:
            raise RangeException(
                parameter_name="stage_duration",
                value=stage_duration,
                min_value=1,
                max_value=10,
                user_message=f"❌ Stage duration must be between 1 and 10 days.\nYou provided: {stage_duration}"
            )
        
        # Command logic continues...
        
    except RangeException as e:
        await handle_bot_exception(context, e, is_slash, "weather-stage-config")
        return
```

### Pattern 5: Database Operation Failed

```python
from commands.exceptions import DatabaseException
from commands.enhanced_error_handlers import handle_database_error
import sqlite3

async def save_weather_command(context, weather_data, is_slash):
    try:
        storage.save_daily_weather(guild_id, weather_data)
        
    except sqlite3.Error as e:
        error = DatabaseException(
            operation="save_weather_data",
            original_error=e,
            user_message="❌ Failed to save weather data. Please try again."
        )
        await handle_bot_exception(context, error, is_slash, "weather")
        return
```

### Pattern 6: Permission Denied

```python
from commands.exceptions import PermissionDeniedException
from commands.enhanced_error_handlers import handle_bot_exception

async def override_weather_command(context, is_slash):
    try:
        if not is_gm(context.user):
            raise PermissionDeniedException(
                command_name="weather override",
                required_permission="GM role or server owner",
                user_message="🔒 Only GMs can override weather.\n\nThis command requires the **GM** role."
            )
        
        # Command logic continues...
        
    except PermissionDeniedException as e:
        await handle_bot_exception(context, e, is_slash, "weather")
        return
```

### Pattern 7: Service Operation Failed

```python
from commands.exceptions import WeatherGenerationException
from commands.enhanced_error_handlers import handle_bot_exception

async def generate_weather_command(context, is_slash):
    guild_id = str(context.guild.id)
    
    try:
        weather_data = weather_service.generate_daily_weather(guild_id, journey)
        
    except Exception as e:
        error = WeatherGenerationException(
            guild_id=guild_id,
            day=journey.current_day,
            reason="Weather generation failed",
            original_error=e,
            user_message="❌ Failed to generate weather. Please try again."
        )
        await handle_bot_exception(context, error, is_slash, "weather")
        return
```

### Pattern 8: Missing Required Channel

```python
from commands.exceptions import ChannelNotFoundException
from commands.enhanced_error_handlers import error_logger

async def send_notification(guild, channel_name, embed):
    try:
        channel = discord.utils.get(guild.channels, name=channel_name)
        if not channel:
            # Log warning but don't fail the command
            error_logger.log_warning(
                f"Channel #{channel_name} not found",
                command_name="notification",
                context_data={"guild_id": str(guild.id)}
            )
            return False  # Notification skipped
        
        await channel.send(embed=embed)
        return True
        
    except discord.Forbidden as e:
        error_logger.log_error(
            error=e,
            command_name="send_notification",
            guild_id=str(guild.id),
            context_data={"channel": channel_name}
        )
        return False
```

### Pattern 9: Generic Catch-All

```python
from commands.enhanced_error_handlers import handle_generic_error

async def complex_command(context, params, is_slash):
    try:
        # Complex command logic with multiple operations
        result1 = operation1()
        result2 = operation2()
        result3 = operation3()
        
    except BotException as e:
        # Handle known exceptions
        await handle_bot_exception(context, e, is_slash, "complex-command")
        return
    except Exception as e:
        # Handle unexpected exceptions
        await handle_generic_error(context, e, is_slash, "complex-command")
        return
```

### Pattern 10: Multiple Exception Types

```python
from commands.exceptions import (
    JourneyNotFoundException,
    WeatherDataNotFoundException,
    DatabaseException
)
from commands.enhanced_error_handlers import handle_bot_exception

async def view_weather_command(context, day, is_slash):
    guild_id = str(context.guild.id)
    
    try:
        # Check journey exists
        journey = storage.get_journey_state(guild_id)
        if not journey:
            raise JourneyNotFoundException(guild_id=guild_id)
        
        # Get weather data
        weather = storage.get_daily_weather(guild_id, day)
        if not weather:
            raise WeatherDataNotFoundException(
                guild_id=guild_id,
                day=day,
                current_day=journey.current_day
            )
        
        # Display weather...
        
    except (JourneyNotFoundException, WeatherDataNotFoundException, DatabaseException) as e:
        await handle_bot_exception(context, e, is_slash, "weather")
        return
```

## Error Recovery Patterns

### Auto-Create Missing Data

```python
from commands.enhanced_error_handlers import ErrorRecovery, send_warning_embed

async def weather_next_command(context, is_slash):
    guild_id = str(context.guild.id)
    
    try:
        journey = storage.get_journey_state(guild_id)
        if not journey:
            # Auto-create with default settings
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
                    "No journey was in progress. Started a new journey with default settings (Summer in Reikland).",
                    is_slash
                )
                journey = storage.get_journey_state(guild_id)
        
        # Continue with command logic...
        
    except Exception as e:
        await handle_generic_error(context, e, is_slash, "weather")
        return
```

### Retry with Fallback

```python
from commands.enhanced_error_handlers import error_logger

async def send_with_retry(channel, embed, max_retries=3):
    """Send message with retry logic."""
    for attempt in range(max_retries):
        try:
            await channel.send(embed=embed)
            return True
        except discord.HTTPException as e:
            if attempt < max_retries - 1:
                error_logger.log_warning(
                    f"Retry attempt {attempt + 1} for message send",
                    context_data={"error": str(e)}
                )
                await asyncio.sleep(1)  # Wait before retry
            else:
                error_logger.log_error(
                    error=e,
                    command_name="send_with_retry",
                    context_data={"attempts": max_retries}
                )
                return False
```

## Logging Patterns

### Log Before Risky Operation

```python
from commands.enhanced_error_handlers import error_logger

async def complex_operation(guild_id, data):
    # Log intent
    error_logger.log_warning(
        "Starting complex operation",
        command_name="complex_operation",
        context_data={"guild_id": guild_id, "data_size": len(data)}
    )
    
    try:
        result = perform_operation(data)
        
        # Log success
        error_logger.log_warning(
            "Complex operation completed successfully",
            command_name="complex_operation",
            context_data={"result": result}
        )
        
        return result
        
    except Exception as e:
        # Error already logged by exception handler
        raise
```

### Conditional Logging

```python
from commands.enhanced_error_handlers import error_logger

async def process_data(data, log_errors=True):
    try:
        return transform_data(data)
    except Exception as e:
        if log_errors:
            error_logger.log_error(
                error=e,
                command_name="process_data",
                context_data={"data_keys": list(data.keys())}
            )
        raise
```

## Testing Error Handlers

### Mock Context for Testing

```python
class MockInteraction:
    """Mock Discord interaction for testing."""
    
    def __init__(self):
        self.guild = MockGuild()
        self.user = MockUser()
        self.response = MockResponse()
        
class MockResponse:
    def __init__(self):
        self.sent_messages = []
        self._is_done = False
    
    def is_done(self):
        return self._is_done
    
    async def send_message(self, **kwargs):
        self.sent_messages.append(kwargs)
        self._is_done = True
```

### Test Error Handling

```python
import pytest

@pytest.mark.asyncio
async def test_journey_not_found_handling():
    # Arrange
    mock_ctx = MockInteraction()
    error = JourneyNotFoundException(
        guild_id="123",
        user_message="❌ No journey found."
    )
    
    # Act
    success = await handle_bot_exception(
        mock_ctx,
        error,
        is_slash=True,
        command_name="weather"
    )
    
    # Assert
    assert success is True
    assert len(mock_ctx.response.sent_messages) == 1
    embed = mock_ctx.response.sent_messages[0]['embed']
    assert "No journey found" in embed.description
```

## Cheat Sheet

| Error Type | Use When | Handler |
|------------|----------|---------|
| `JourneyNotFoundException` | No journey exists | `handle_bot_exception` |
| `WeatherDataNotFoundException` | Weather data missing | `handle_bot_exception` |
| `CharacterNotFoundException` | Character not found | `handle_bot_exception` |
| `DiceNotationException` | Invalid dice notation | `handle_bot_exception` |
| `InvalidParameterException` | Bad parameter value | `handle_bot_exception` |
| `RangeException` | Value out of range | `handle_bot_exception` |
| `PermissionDeniedException` | User lacks permission | `handle_bot_exception` |
| `DatabaseException` | Database error | `handle_database_error` |
| `discord.Forbidden` | Bot lacks permissions | `handle_discord_api_error` |
| `discord.HTTPException` | Discord API error | `handle_discord_api_error` |
| `ValueError` | Generic validation | `handle_validation_error` |
| `Exception` | Unexpected error | `handle_generic_error` |

## Quick Checklist

When adding error handling to a command:

- [ ] Import required exception classes
- [ ] Import required error handlers
- [ ] Wrap risky operations in try/except
- [ ] Raise specific exception types (not generic Exception)
- [ ] Include user-friendly error messages
- [ ] Add context data for debugging
- [ ] Use appropriate error handler
- [ ] Log errors when needed
- [ ] Consider error recovery options
- [ ] Test error scenarios
