# Future Enhancements - Implementation Plan

## Overview
This document outlines the detailed implementation plans for two major enhancements to the weather system:
1. **Track weather across multiple days** - Persistence and multi-day journey tracking
2. **Integration with boat handling** - Automatic application of weather modifiers to boat tests

---

## Enhancement 1: Track Weather Across Multiple Days

### Goal
Enable the bot to remember weather conditions across multiple days, track weather progression, and manage multi-day journeys with realistic weather transitions.

### Use Cases
1. **Multi-day journey**: User generates weather for Day 1, then asks for Day 2, Day 3, etc.
2. **Weather persistence**: Cold fronts and heat waves last 10+1d10 days as per WFRP rules
3. **Weather continuity**: Wind conditions from midnight of Day 1 carry over to dawn of Day 2
4. **Journey tracking**: Track which day of the journey the party is on

### Architecture

#### 1.1 Data Storage Solution

**Option A: JSON File Storage** (Recommended for simplicity)
- **Pros**: Simple, no external dependencies, easy to debug
- **Cons**: Not suitable for multiple servers (but fine for single-server bot)
- **File**: `data/weather_state.json`

**Option B: SQLite Database** (Recommended for scalability)
- **Pros**: Better for multiple guilds, structured queries, concurrent access
- **Cons**: Slightly more complex setup
- **File**: `data/weather.db`

**Decision**: Start with **SQLite** for better scalability

#### 1.2 Data Model

```python
# Guild Weather State (per Discord server)
GuildWeatherState = {
    "guild_id": str,
    "current_day": int,  # Day number of journey
    "journey_start_date": str,  # ISO format timestamp
    "last_weather_date": str,  # ISO format
    "season": str,  # spring, summer, autumn, winter
    "province": str,  # reikland, kislev, etc.
}

# Daily Weather Record
DailyWeatherRecord = {
    "id": int (auto-increment),
    "guild_id": str,
    "day_number": int,
    "generated_at": str,  # ISO timestamp
    "season": str,
    "province": str,
    
    # Wind data (stored as JSON)
    "wind_timeline": List[{
        "time": str,  # Dawn, Midday, Dusk, Midnight
        "strength": str,
        "direction": str,
        "changed": bool
    }],
    
    # Weather data
    "weather_type": str,
    "weather_roll": int,  # Store the d100 roll for reference
    
    # Temperature data
    "temperature_actual": int,
    "temperature_category": str,
    "temperature_roll": int,
    
    # Special conditions
    "cold_front_days_remaining": int,  # 0 if not in cold front
    "heat_wave_days_remaining": int,   # 0 if not in heat wave
}
```

#### 1.3 Database Schema (SQLite)

```sql
-- Guild weather state
CREATE TABLE guild_weather_state (
    guild_id TEXT PRIMARY KEY,
    current_day INTEGER DEFAULT 1,
    journey_start_date TEXT,
    last_weather_date TEXT,
    season TEXT NOT NULL,
    province TEXT NOT NULL
);

-- Daily weather records
CREATE TABLE daily_weather (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL,
    day_number INTEGER NOT NULL,
    generated_at TEXT NOT NULL,
    season TEXT NOT NULL,
    province TEXT NOT NULL,
    
    -- Wind (stored as JSON string)
    wind_timeline TEXT NOT NULL,
    
    -- Weather
    weather_type TEXT NOT NULL,
    weather_roll INTEGER NOT NULL,
    
    -- Temperature
    temperature_actual INTEGER NOT NULL,
    temperature_category TEXT NOT NULL,
    temperature_roll INTEGER NOT NULL,
    
    -- Special conditions
    cold_front_days_remaining INTEGER DEFAULT 0,
    heat_wave_days_remaining INTEGER DEFAULT 0,
    
    UNIQUE(guild_id, day_number),
    FOREIGN KEY(guild_id) REFERENCES guild_weather_state(guild_id)
);

-- Index for faster lookups
CREATE INDEX idx_guild_day ON daily_weather(guild_id, day_number);
```

### Implementation Steps

#### Step 1: Create Database Module (`db/weather_storage.py`)
```python
"""
Weather persistence and storage for multi-day journeys.
"""
import sqlite3
import json
from typing import Optional, Dict, List
from datetime import datetime
from pathlib import Path

class WeatherStorage:
    def __init__(self, db_path: str = "data/weather.db"):
        """Initialize database connection."""
        # Create data directory if it doesn't exist
        Path(db_path).parent.mkdir(exist_ok=True)
        
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Create tables if they don't exist."""
        # Implementation here
    
    def start_journey(self, guild_id: str, season: str, province: str):
        """Start a new journey for a guild."""
    
    def save_daily_weather(self, guild_id: str, day_number: int, weather_data: Dict):
        """Save weather for a specific day."""
    
    def get_daily_weather(self, guild_id: str, day_number: int) -> Optional[Dict]:
        """Retrieve weather for a specific day."""
    
    def get_current_day(self, guild_id: str) -> int:
        """Get current day number for guild."""
    
    def advance_day(self, guild_id: str):
        """Increment day counter for guild."""
    
    def get_journey_state(self, guild_id: str) -> Optional[Dict]:
        """Get current journey state for guild."""
    
    def end_journey(self, guild_id: str):
        """Clear journey data for guild."""
```

**Files to create:**
- `db/weather_storage.py` (main storage class)
- `data/` directory (auto-created)
- `data/weather.db` (auto-created on first run)

#### Step 2: Update Weather Mechanics for Continuity (`utils/weather_mechanics.py`)

**New functions:**
```python
def generate_daily_wind_with_previous(previous_midnight_wind: Dict) -> List[Dict]:
    """
    Generate wind for a new day, starting from previous day's midnight wind.
    
    Args:
        previous_midnight_wind: Dict with 'strength' and 'direction' from yesterday
    
    Returns:
        Wind timeline for the new day starting with the carried-over conditions
    """

def apply_special_temperature_effects(
    base_temp: int, 
    cold_front_days: int, 
    heat_wave_days: int
) -> Tuple[int, int, int]:
    """
    Apply cold front or heat wave effects to temperature.
    
    Returns:
        (actual_temp, cold_front_remaining, heat_wave_remaining)
    """
```

#### Step 3: Update Weather Command (`commands/weather.py`)

**New command options:**
```python
@bot.tree.command(name="weather")
@app_commands.describe(
    action="What to do (generate, next, view, journey)",
    season="Season (for new journey only)",
    province="Province (for new journey only)",
    day="Specific day to view (optional)"
)
@app_commands.choices(
    action=[
        app_commands.Choice(name="Generate Next Day", value="next"),
        app_commands.Choice(name="Start New Journey", value="journey"),
        app_commands.Choice(name="View Day", value="view"),
        app_commands.Choice(name="End Journey", value="end"),
    ]
)
```

**Command behaviors:**

1. **`/weather next`** - Generate next day's weather
   - Check if journey exists, auto-start if not
   - Load previous day's midnight wind
   - Generate weather with continuity
   - Handle cold fronts/heat waves
   - Save to database
   - Increment day counter

2. **`/weather journey <season> <province>`** - Start new journey
   - Clear any existing journey data
   - Set season and province
   - Generate Day 1 weather
   - Save initial state

3. **`/weather view [day]`** - View historical weather
   - If no day specified, show current day
   - Load weather from database
   - Display in same format as current weather

4. **`/weather end`** - End current journey
   - Clear journey data
   - Provide summary of journey days

#### Step 4: Update Weather Data for Special Conditions

**Handle Cold Fronts:**
```python
def handle_cold_front(roll: int, current_cold_front_days: int) -> Tuple[int, int]:
    """
    Check for cold front and manage duration.
    
    Returns:
        (temperature_modifier, days_remaining)
    """
    if roll == 2 and current_cold_front_days == 0:
        # New cold front starting
        duration = 10 + random.randint(1, 10)
        return -10, duration
    elif current_cold_front_days > 0:
        # Cold front continuing
        return -10, current_cold_front_days - 1
    else:
        # No cold front
        return 0, 0
```

**Handle Heat Waves:** (Similar pattern)

#### Step 5: Testing

**New test files:**
- `tests/test_weather_storage.py` - Database operations
- `tests/test_weather_continuity.py` - Multi-day weather generation

**Test scenarios:**
1. Journey start/end lifecycle
2. Day advancement
3. Weather continuity (midnight → dawn)
4. Cold front duration (10+1d10 days)
5. Heat wave duration
6. Multiple guilds (isolation)
7. Data persistence across bot restarts

### User Interface Examples

**Starting a journey:**
```
User: /weather journey summer reikland
Bot: 🧭 New Journey Started!
     Season: Summer in Reikland
     Day 1 weather has been generated.
     Use /weather next to advance to the next day.
     
     [Shows Day 1 weather embed]
```

**Advancing to next day:**
```
User: /weather next
Bot: 📅 Day 2 - Summer in Reikland
     
     Wind continuity from Day 1:
     • Yesterday's midnight: Light Sidewind
     • Today's dawn: Light Sidewind (carried over)
     
     [Shows Day 2 weather embed]
```

**Viewing previous day:**
```
User: /weather view 1
Bot: 📜 Historical Weather - Day 1
     
     [Shows Day 1 weather embed from database]
```

---

## Enhancement 2: Integration with Boat Handling Command

### Goal
Automatically apply active weather modifiers to boat handling tests, with clear indication of what modifiers are being applied.

### Architecture

#### 2.1 Modifier System

**Active Modifiers Structure:**
```python
ActiveWeatherModifiers = {
    "wind_modifier_percent": int,  # -25 to +25
    "wind_strength": str,
    "wind_direction": str,
    "requires_tacking": bool,
    "requires_test": bool,  # Very Strong Sidewind
    "boat_handling_penalty": int,  # e.g., -10 for Calm
    "weather_penalties": List[str],  # From weather conditions
    "special_notes": List[str],
}
```

#### 2.2 Modifier Calculation Module

**New file: `utils/modifier_calculator.py`**
```python
def get_active_weather_modifiers(
    guild_id: str, 
    time_of_day: str = "midday"
) -> Optional[Dict]:
    """
    Get currently active weather modifiers for a guild.
    
    Args:
        guild_id: Discord guild ID
        time_of_day: dawn, midday, dusk, midnight
    
    Returns:
        Dict of active modifiers or None if no active weather
    """

def calculate_total_boat_handling_modifier(
    base_difficulty: int,
    weather_modifiers: Dict,
    character_skill: int
) -> Tuple[int, List[str]]:
    """
    Calculate total modifier for boat handling test.
    
    Returns:
        (total_modifier, explanation_list)
    """
```

### Implementation Steps

#### Step 1: Create Modifier Calculation Module

**File: `utils/modifier_calculator.py`**
```python
from typing import Optional, Dict, List, Tuple
from db.weather_storage import WeatherStorage

def get_active_weather_modifiers(
    guild_id: str,
    time_of_day: str = "midday"
) -> Optional[Dict]:
    """Get active weather modifiers for boat handling."""
    storage = WeatherStorage()
    
    # Get current day weather
    current_day = storage.get_current_day(guild_id)
    weather = storage.get_daily_weather(guild_id, current_day)
    
    if not weather:
        return None
    
    # Extract wind for specific time
    wind_data = _get_wind_for_time(weather["wind_timeline"], time_of_day)
    
    # Get wind modifiers
    from utils.weather_mechanics import get_wind_modifiers
    wind_mods = get_wind_modifiers(
        wind_data["strength"],
        wind_data["direction"]
    )
    
    # Parse wind modifier (e.g., "+10%" → 10)
    speed_mod = _parse_speed_modifier(wind_mods["modifier"])
    
    # Check for special conditions
    requires_tacking = "tacking" in wind_mods["notes"].lower() if wind_mods["notes"] else False
    requires_test = "must be made" in wind_mods["notes"].lower() if wind_mods["notes"] else False
    
    # Get boat handling penalty (from Calm winds)
    bh_penalty = _extract_boat_handling_penalty(wind_mods["modifier"])
    
    # Get weather penalties
    from utils.weather_mechanics import get_weather_effects
    weather_effects = get_weather_effects(weather["weather_type"])
    
    return {
        "wind_modifier_percent": speed_mod,
        "wind_strength": wind_data["strength"],
        "wind_direction": wind_data["direction"],
        "requires_tacking": requires_tacking,
        "requires_test": requires_test,
        "boat_handling_penalty": bh_penalty,
        "weather_effects": weather_effects["effects"],
        "wind_notes": wind_mods["notes"],
    }
```

#### Step 2: Update Boat Handling Command

**File: `commands/boat_handling.py`**

**Changes needed:**

1. **Add time_of_day parameter:**
```python
@app_commands.describe(
    character="Character name",
    difficulty="Test difficulty modifier",
    time_of_day="Time of day (affects wind conditions)"
)
@app_commands.choices(
    time_of_day=[
        app_commands.Choice(name="Dawn", value="dawn"),
        app_commands.Choice(name="Midday", value="midday"),
        app_commands.Choice(name="Dusk", value="dusk"),
        app_commands.Choice(name="Midnight", value="midnight"),
    ]
)
async def boat_handling_slash(
    interaction: discord.Interaction,
    character: str,
    difficulty: int = 0,
    time_of_day: str = "midday",
):
```

2. **Apply weather modifiers:**
```python
async def _perform_boat_handling(
    context, character: str, difficulty: int, time_of_day: str, is_slash: bool
):
    # ... existing character lookup ...
    
    # Get active weather modifiers
    from utils.modifier_calculator import get_active_weather_modifiers
    weather_mods = get_active_weather_modifiers(
        str(context.guild.id),
        time_of_day
    )
    
    # Apply weather-based difficulty modifier
    if weather_mods:
        # Add boat handling penalty (e.g., -10 for Calm)
        difficulty += weather_mods["boat_handling_penalty"]
        
        # Track applied modifiers for display
        applied_modifiers = []
        if weather_mods["boat_handling_penalty"] != 0:
            applied_modifiers.append(
                f"Wind penalty: {weather_mods['boat_handling_penalty']:+d}"
            )
    
    # ... rest of existing logic ...
```

3. **Display weather impact in embed:**
```python
# After calculating result, add weather section
if weather_mods:
    weather_text = f"**Wind:** {wind_mods['wind_strength']} {wind_mods['wind_direction']}\n"
    weather_text += f"**Movement modifier:** {weather_mods['wind_modifier_percent']:+d}%\n"
    
    if weather_mods["requires_tacking"]:
        weather_text += "⚓ Tacking required for speed bonus\n"
    
    if weather_mods["requires_test"]:
        weather_text += "⚠️ Special test required!\n"
    
    if weather_mods["weather_effects"] and weather_mods["weather_effects"][0] != "No weather-related hazards":
        weather_text += "\n**Active conditions:**\n"
        weather_text += "\n".join(f"• {e}" for e in weather_mods["weather_effects"])
    
    embed.add_field(
        name="🌦️ Weather Impact",
        value=weather_text,
        inline=False
    )
```

#### Step 3: Add Weather Status Command

**New command: `/weather-status`**
```python
@bot.tree.command(
    name="weather-status",
    description="Check current weather conditions affecting boat handling"
)
async def weather_status(interaction: discord.Interaction):
    """Show current active weather and its mechanical effects."""
    
    from utils.modifier_calculator import get_active_weather_modifiers
    
    # Get weather for all time periods
    times = ["Dawn", "Midday", "Dusk", "Midnight"]
    
    embed = discord.Embed(
        title="🌦️ Active Weather Conditions",
        color=discord.Color.blue()
    )
    
    for time in times:
        mods = get_active_weather_modifiers(
            str(interaction.guild.id),
            time.lower()
        )
        
        if mods:
            text = f"**{mods['wind_strength']} {mods['wind_direction']}**\n"
            text += f"Speed: {mods['wind_modifier_percent']:+d}%\n"
            if mods["boat_handling_penalty"]:
                text += f"BH Test: {mods['boat_handling_penalty']:+d}\n"
            
            embed.add_field(
                name=f"{time}",
                value=text,
                inline=True
            )
    
    await interaction.response.send_message(embed=embed)
```

#### Step 4: Configuration and Toggles

**Add optional auto-apply toggle:**
```python
# In guild settings (future enhancement)
class GuildSettings:
    auto_apply_weather: bool = True  # Auto-apply weather to boat handling
    weather_notifications: bool = True  # Send to notifications channel
```

**Command to toggle:**
```python
@bot.tree.command(name="weather-config")
@app_commands.describe(
    auto_apply="Automatically apply weather to boat handling tests"
)
async def weather_config(
    interaction: discord.Interaction,
    auto_apply: bool
):
    """Configure weather system settings."""
    # Save setting to database
    # Confirm to user
```

### Testing

**New test files:**
- `tests/test_modifier_calculator.py` - Modifier extraction and calculation
- `tests/test_boat_handling_integration.py` - Integration with boat handling

**Test scenarios:**
1. Modifier calculation for all wind combinations
2. Tacking requirement detection
3. Special test requirement detection
4. Penalty stacking (wind + weather)
5. No weather scenario (defaults)
6. Time of day variations

### User Interface Examples

**Boat handling with weather:**
```
User: /boat-handling anara midday
Bot: [Boat Handling Test embed]
     
     🌦️ Weather Impact
     Wind: Bracing Tailwind
     Movement modifier: +10%
     ⚓ Tacking required for speed bonus
     
     Active conditions:
     • Visibility reduced to 75 ft
     • -10 penalty to ranged weapons
```

**Weather status check:**
```
User: /weather-status
Bot: 🌦️ Active Weather Conditions
     
     Dawn         | Midday       | Dusk         | Midnight
     Light        | Bracing      | Strong       | Strong
     Tailwind     | Tailwind     | Sidewind     | Headwind
     +5%          | +10%         | +10%         | -20%
     BH: -        | BH: -        | BH: -        | BH: -
```

---

## Implementation Timeline

### Phase 1: Weather Persistence (Estimated: 2-3 days)
1. Day 1: Database setup and storage module
2. Day 2: Update weather mechanics for continuity
3. Day 3: Update weather command with new actions
4. Day 3: Testing and bug fixes

### Phase 2: Boat Handling Integration (Estimated: 1-2 days)
1. Day 1: Modifier calculator module
2. Day 1: Update boat handling command
3. Day 2: Weather status command and testing

### Total Estimated Time: 4-5 days of development

---

## Dependencies and Requirements

### New Dependencies
- None! Uses built-in Python `sqlite3` module

### New Files to Create
1. `db/weather_storage.py` (200-300 lines)
2. `utils/modifier_calculator.py` (150-200 lines)
3. `tests/test_weather_storage.py` (100-150 lines)
4. `tests/test_modifier_calculator.py` (80-100 lines)
5. `tests/test_weather_continuity.py` (80-100 lines)
6. `tests/test_boat_handling_integration.py` (80-100 lines)

### Files to Modify
1. `utils/weather_mechanics.py` - Add continuity functions
2. `commands/weather.py` - Add journey management
3. `commands/boat_handling.py` - Add weather integration
4. `requirements.txt` - No changes needed

### Database Files (auto-created)
1. `data/weather.db` - SQLite database

---

## Rollback Plan

Both enhancements are **additive** and don't break existing functionality:

1. **Weather Persistence**: Old `/weather` command still works without database
2. **Boat Handling Integration**: Works with or without active weather

**Rollback steps:**
1. Remove new command actions (keep original `/weather`)
2. Remove weather modifier code from boat handling
3. Delete `db/weather_storage.py` and `utils/modifier_calculator.py`

---

## Future Considerations

### After Phase 2 Completion

1. **Weather Events**: Random events based on weather (e.g., fog encounter, storm damage)
2. **Season Progression**: Auto-advance seasons after certain day counts
3. **Weather Forecasting**: `/weather forecast` to show upcoming days (with uncertainty)
4. **Weather History**: `/weather history` to show past week
5. **Guild-specific Settings**: Different guilds can have different journeys
6. **Travel Speed Calculation**: Integrate weather modifiers into actual distance calculations
7. **Weather-based Encounters**: Trigger special encounters in certain weather

---

## Questions to Consider Before Implementation

1. **Multi-server Support**: Should each Discord server have its own journey, or is this a single-server bot?
   - **Recommendation**: Support multiple guilds from the start (minimal extra effort)

2. **Journey Limits**: Should we limit how many days can be tracked?
   - **Recommendation**: Store last 30 days, auto-delete older

3. **Time Zone Handling**: Should we track real-world time or just day numbers?
   - **Recommendation**: Day numbers only (simpler, game-time not real-time)

4. **Manual Weather Override**: Should GMs be able to manually set weather?
   - **Recommendation**: Add in Phase 3 as `/weather override`

5. **Notification Persistence**: Should weather notifications also be saved to database?
   - **Recommendation**: No, keep notifications ephemeral

---

## Success Metrics

### Phase 1 Success Criteria
- ✅ Weather data persists across bot restarts
- ✅ Multiple guilds can track separate journeys
- ✅ Wind conditions carry over between days correctly
- ✅ Cold fronts and heat waves last correct duration
- ✅ All 190+ tests still passing
- ✅ New tests for storage and continuity passing

### Phase 2 Success Criteria
- ✅ Weather modifiers automatically apply to boat handling
- ✅ Modifiers correctly calculated for all wind combinations
- ✅ Clear display of active weather impact
- ✅ Time of day selection works
- ✅ Works gracefully with or without active weather
- ✅ All tests passing including integration tests
