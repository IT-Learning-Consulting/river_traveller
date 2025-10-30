# Weather Event System Improvement Plan

## Current State Analysis

### How It Works Now

**Cold Fronts & Heat Waves:**
- Cold Front: Triggered on temperature roll = 2 (1% chance)
- Heat Wave: Triggered on temperature roll = 99 (1% chance)
- Duration: **Calculated each time but NOT stored in database** - Cold fronts roll `1d5` (1-5 days), Heat waves roll `10 + 1d10` (11-20 days)
- Database only stores: `cold_front_days_remaining` (countdown from initial roll)
- Database does NOT store: The original total duration that was rolled
- Display shows formula instead of actual rolled value: "Temperatures remain 'very low' during **1d5 days**" (cold front) or "10+1d10 days" (heat wave)

**Current Flow (THE PROBLEM):**
```
Day 1: Roll = 2 → Cold front starts → Duration calculated: 13 days
       Returns: cold_front_remaining = 13
       
Day 2: Previous cold_front_days = 13 → No new roll check
       Returns: cold_front_remaining = 12
       
Day 3: Previous cold_front_days = 12 → No new roll check
       Returns: cold_front_remaining = 11
       
... continues until cold_front_remaining = 0
```

**Problems Identified:**
1. ❌ **Display shows formula, not actual duration** - Users see "1d5 days" but don't know if it rolled 1, 2, 3, 4, or 5 days
2. ❌ **Total duration not stored in database** - System only stores countdown (`days_remaining`), not the original rolled total
3. ❌ **No way to show progress** - Can't display "Day 2 of 3" because we don't know what "3" was
4. ❌ **No cooldown mechanism** - Cold front can trigger immediately after previous one ends
5. ❌ **Both events can overlap** - Cold front and heat wave can happen simultaneously (conflicting temperature modifiers)
6. ❌ **Poor testing experience** - Can't reliably test without waiting for rare rolls

---

## Proposed Solution

### 1. Store Rolled Duration Instead of Countdown

**Current (Bad):**
```python
if roll == 2 and current_cold_front_days == 0:
    duration = random.randint(1, 5)  # Rolls every time, not stored (1d5)
    return -10, duration
```

**Proposed (Good):**
```python
# Store both remaining days AND total duration
if roll == 2 and current_cold_front_days == 0:
    total_duration = random.randint(1, 5)  # Roll once: e.g., 3
    return -10, total_duration, total_duration  # (modifier, remaining, total)
    
# Display: "Cold Front: Day 1 of 3" instead of "during 1d5 days"
```

### 2. Add Cooldown System

**Purpose:** Prevent events from happening too frequently

**Mechanism:**
```
Cold Front ends → 7-day cooldown starts → No new cold fronts can trigger
Heat Wave ends → 7-day cooldown starts → No new heat waves can trigger
```

**Implementation:**
- Add `days_since_last_cold_front` to database
- Add `days_since_last_heat_wave` to database
- Check cooldown before allowing new events
- Cooldown duration: 7 days (configurable constant)

### 3. Prevent Overlapping Events

**Mutual Exclusivity:**
- If cold front active → Heat wave cannot trigger
- If heat wave active → Cold front cannot trigger
- Prevents conflicting temperature modifiers (-10°C vs +10°C)

### 4. Add Daily Temperature Variation During Events

**Purpose:** Make cold fronts/heat waves feel more natural with day-to-day variation

**Current Behavior:**
- Cold front: Temperature = base_temp + modifier - 10°C (fixed throughout event)
- Example: Reikland summer (21°C base), cold front active → Always 11°C every day

**Problem:**
- ❌ Temperature is static for 1-5 days (cold front) or 11-20 days (heat wave)
- ❌ Unrealistic - real weather varies day-to-day even during persistent patterns
- ❌ Boring gameplay - players see identical temperature readings
- ❌ Lost opportunity for tension ("Is it getting worse?" "Is it ending?")

**Proposed Behavior:**
- Cold front still applies -10°C modifier
- BUT temperature rolls still happen daily using normal d100 system
- Daily roll determines variation: ±5°C from base cold front temperature
- Net effect: Temperature varies mildly but stays within cold front range

**Example Flow:**
```
Reikland Summer, Cold Front Active (3 days)

Day 1: Roll = 45 (Average, 0 modifier)
  Base temp: 21°C
  Cold front modifier: -10°C
  Daily variation: 0°C (average roll)
  Final temp: 11°C
  Display: "11°C (Average) - Cold Front: Day 1 of 3"

Day 2: Roll = 15 (Low, -5 modifier)
  Base temp: 21°C
  Cold front modifier: -10°C
  Daily variation: -5°C (low roll)
  Final temp: 6°C
  Display: "6°C (Cool) - Cold Front: Day 2 of 3"

Day 3: Roll = 85 (High, +5 modifier)
  Base temp: 21°C
  Cold front modifier: -10°C
  Daily variation: +5°C (high roll)
  Final temp: 16°C
  Display: "16°C (Mild) - Cold Front: Day 3 of 3 (Final Day)"
```

**Benefits:**
1. **More realistic weather patterns** - Daily variation within persistent cold
2. **Gameplay tension** - "It's getting colder... is the cold front worsening?"
3. **Better storytelling** - "The cold front continues, though today brings brief respite"
4. **Preserves mechanics** - Cold front still consistently reduces temperature
5. **Works with heat waves too** - Same logic applies (+10°C with daily variation)

**Implementation Notes:**
- Daily temperature roll (d100) still happens during events
- Roll determines category (very_low, low, average, high, very_high)
- Category modifier applies AFTER event modifier
- Special rolls (2, 99) ignored during active events (can't trigger new event)
- Temperature category description reflects final temperature, not base

### 5. Improve Display Messages

**Current:**
```
❄️ Cold Front: Temperatures remain 'very low' during 1d5 days.
```

**Proposed:**
```
❄️ Cold Front: Day 1 of 3 - Temperatures remain 'very low'. Sky filled with flocks of emigrating birds.

❄️ Cold Front: Day 2 of 3 - Temperatures remain 'very low'

❄️ Cold Front: Day 3 of 3 (Final Day) - Temperatures remain 'very low'
```

---

## Files to Modify

### Summary Table

| File | Changes Required | Priority | Complexity |
|------|------------------|----------|------------|
| `db/weather_storage.py` | Add 4 new columns, cooldown methods | CRITICAL | Medium |
| `utils/weather_mechanics.py` | Update event handlers, cooldown logic, **daily variation** | CRITICAL | **Very High** |
| `commands/weather_modules/handler.py` | Track cooldowns, pass context | HIGH | Medium |
| `commands/weather_modules/stages.py` | Display day counters in stage summaries | MEDIUM | Low |
| `commands/weather_modules/display.py` | **No changes needed** (verification only) | LOW | None |
| `commands/weather_modules/notifications.py` | Add special events section (+ optional temp breakdown) | MEDIUM | Low-Medium |
| `commands/weather_modules/formatters.py` | **No changes needed** | NONE | None |
| `db/weather_data.py` | Update documentation strings, verify ranges | LOW | Trivial |

**Total Files to Modify:** 5 files (1 with major complexity increase)  
**Files to Verify:** 2 files  
**Files Unchanged:** 2 files

**Complexity Notes:**
- `utils/weather_mechanics.py` complexity increased from High to **Very High** due to:
  - Daily temperature variation logic during events
  - Special roll suppression (roll=2, roll=99)
  - Category recalculation based on final temperature
  - New helper function `get_category_from_actual_temp()`

---

### 1. **Database Schema** (`db/weather_storage.py`)

**Changes Required:**
- Add `cold_front_total_duration` column to `daily_weather` table
- Add `heat_wave_total_duration` column to `daily_weather` table
- Add `days_since_last_cold_front` column to `guild_weather_state` table
- Add `days_since_last_heat_wave` column to `guild_weather_state` table
- Add migration logic for existing databases

**SQL Changes:**
```sql
-- In daily_weather table
ALTER TABLE daily_weather ADD COLUMN cold_front_total_duration INTEGER DEFAULT 0;
ALTER TABLE daily_weather ADD COLUMN heat_wave_total_duration INTEGER DEFAULT 0;

-- In guild_weather_state table  
ALTER TABLE guild_weather_state ADD COLUMN days_since_last_cold_front INTEGER DEFAULT 99;
ALTER TABLE guild_weather_state ADD COLUMN days_since_last_heat_wave INTEGER DEFAULT 99;
```

**New Methods Needed:**
```python
def update_cooldown_trackers(guild_id: str, cold_front_increment: bool, heat_wave_increment: bool)
def get_cooldown_status(guild_id: str) -> tuple[int, int]
def reset_cooldown(guild_id: str, event_type: str)
```

### 2. **Weather Mechanics** (`utils/weather_mechanics.py`)

**Functions to Modify:**

#### `handle_cold_front()`
**Current Signature:**
```python
def handle_cold_front(roll: int, current_cold_front_days: int) -> Tuple[int, int]
```

**New Signature:**
```python
def handle_cold_front(
    roll: int, 
    current_cold_front_days: int,
    current_total_duration: int,
    days_since_last_cold_front: int,
    heat_wave_active: bool
) -> Tuple[int, int, int]:
    """
    Returns: (temperature_modifier, days_remaining, total_duration)
    """
```

**New Logic:**
```python
COLD_FRONT_COOLDOWN = 7  # Days before another cold front can occur

def handle_cold_front(...):
    # Continuing cold front
    if current_cold_front_days > 0:
        return -10, current_cold_front_days - 1, current_total_duration
    
    # Check if new cold front can trigger
    if roll == 2:
        # Prevent if heat wave active
        if heat_wave_active:
            return 0, 0, 0
        
        # Check cooldown
        if days_since_last_cold_front < COLD_FRONT_COOLDOWN:
            return 0, 0, 0  # Still in cooldown
        
        # New cold front!
        total_duration = random.randint(1, 5)  # 1d5 days
        return -10, total_duration, total_duration
    
    # No cold front
    return 0, 0, 0
```

#### `handle_heat_wave()`
**Same pattern as `handle_cold_front()`**

#### `roll_temperature_with_special_events()`
**Current Signature:**
```python
def roll_temperature_with_special_events(
    season: str, 
    province: str, 
    cold_front_days: int = 0, 
    heat_wave_days: int = 0
) -> Tuple[int, str, str, int, int, int]
```

**New Signature:**
```python
def roll_temperature_with_special_events(
    season: str,
    province: str,
    cold_front_days: int = 0,
    cold_front_total: int = 0,
    heat_wave_days: int = 0,
    heat_wave_total: int = 0,
    days_since_last_cold_front: int = 99,
    days_since_last_heat_wave: int = 99
) -> Tuple[int, str, str, int, int, int, int, int]:
    """
    Returns: (
        actual_temp, 
        category, 
        description, 
        roll,
        cold_front_remaining,
        cold_front_total_duration,
        heat_wave_remaining,
        heat_wave_total_duration
    )
    """
```

**New Display Logic:**
```python
# Add special event information with day count
if cold_front_remaining > 0:
    days_elapsed = cold_front_total - cold_front_remaining + 1
    
    if days_elapsed == 1:
        # First day
        description += f"\n*❄️ Cold Front: Day {days_elapsed} of {cold_front_total} - Temperatures remain 'very low'. Sky filled with flocks of emigrating birds.*"
    elif cold_front_remaining == 1:
        # Last day
        description += f"\n*❄️ Cold Front: Day {days_elapsed} of {cold_front_total} (Final Day) - Temperatures remain 'very low'.*"
    else:
        # Middle days (only for 3+ day cold fronts)
        description += f"\n*❄️ Cold Front: Day {days_elapsed} of {cold_front_total} - Temperatures remain 'very low'.*"
```

**NEW - Daily Variation Logic:**
```python
def roll_temperature_with_special_events(...):
    """Roll temperature with daily variation during events."""
    roll = random.randint(1, 100)
    
    # During active cold front or heat wave, ignore special event triggers
    if cold_front_days > 0:
        # Ignore roll = 2 (can't trigger new cold front during existing one)
        if roll == 2:
            roll = 3  # Treat as very_low instead
    
    if heat_wave_days > 0:
        # Ignore roll = 99 (can't trigger new heat wave during existing one)
        if roll == 99:
            roll = 98  # Treat as very_high instead
    
    # Get daily variation from normal temperature table
    category, daily_modifier = get_temperature_category_from_roll(roll)
    
    base_temp = get_province_base_temperature(province, season)
    
    # Apply event modifiers first, then daily variation
    cold_mod, cold_front_remaining = handle_cold_front(roll, cold_front_days, ...)
    heat_mod, heat_wave_remaining = handle_heat_wave(roll, heat_wave_days, ...)
    
    # Calculate final temperature: base + event_modifier + daily_variation
    actual_temp = base_temp + cold_mod + heat_mod + daily_modifier
    
    # Determine category based on FINAL temperature (not base)
    final_category = get_category_from_actual_temp(actual_temp, base_temp)
    
    # Build description with event info
    description = TEMPERATURE_DESCRIPTIONS.get(final_category, "Average")
    
    if cold_front_remaining > 0:
        days_elapsed = cold_front_total - cold_front_remaining + 1
        description += f"\n*❄️ Cold Front: Day {days_elapsed} of {cold_front_total}*"
        if days_elapsed == 1:
            description += " - Sky filled with flocks of emigrating birds"
    
    return (actual_temp, final_category, description, roll, 
            cold_front_remaining, cold_front_total_new,
            heat_wave_remaining, heat_wave_total_new)
```

**New Helper Function Needed:**
```python
def get_category_from_actual_temp(actual_temp: int, base_temp: int) -> str:
    """
    Determine temperature category based on difference from base.
    
    Args:
        actual_temp: Final calculated temperature
        base_temp: Province/season base temperature
        
    Returns:
        Category string (very_cold, cold, cool, average, warm, hot, very_hot)
    """
    diff = actual_temp - base_temp
    
    if diff <= -15:
        return "extremely_low"
    elif diff <= -10:
        return "very_low"
    elif diff <= -5:
        return "low"
    elif diff <= -2:
        return "cool"
    elif diff <= 2:
        return "average"
    elif diff <= 5:
        return "warm"
    elif diff <= 10:
        return "high"
    elif diff <= 15:
        return "very_high"
    else:
        return "extremely_high"
```

### 3. **Weather Handler** (`commands/weather_modules/handler.py`)

**Function to Modify:** `_generate_daily_weather()`

**Current Logic (Lines 505-570):**
```python
previous_weather = self.storage.get_daily_weather(guild_id, new_day - 1) if new_day > 1 else None
cold_front_days = previous_weather["cold_front_days_remaining"] if previous_weather else 0
heat_wave_days = previous_weather["heat_wave_days_remaining"] if previous_weather else 0

(
    actual_temp, temp_category, temp_description, temp_roll,
    cold_front_remaining, heat_wave_remaining,
) = roll_temperature_with_special_events(
    season, province, cold_front_days, heat_wave_days
)
```

**New Logic:**
```python
# Get previous weather and cooldown status
previous_weather = self.storage.get_daily_weather(guild_id, new_day - 1) if new_day > 1 else None
journey_state = self.storage.get_journey_state(guild_id)

# Extract cold front state
cold_front_days = previous_weather.get("cold_front_days_remaining", 0) if previous_weather else 0
cold_front_total = previous_weather.get("cold_front_total_duration", 0) if previous_weather else 0

# Extract heat wave state
heat_wave_days = previous_weather.get("heat_wave_days_remaining", 0) if previous_weather else 0
heat_wave_total = previous_weather.get("heat_wave_total_duration", 0) if previous_weather else 0

# Get cooldown trackers
days_since_cf = journey_state.get("days_since_last_cold_front", 99)
days_since_hw = journey_state.get("days_since_last_heat_wave", 99)

# Roll temperature with all context
(
    actual_temp, temp_category, temp_description, temp_roll,
    cold_front_remaining, cold_front_total_new,
    heat_wave_remaining, heat_wave_total_new,
) = roll_temperature_with_special_events(
    season, province, 
    cold_front_days, cold_front_total,
    heat_wave_days, heat_wave_total,
    days_since_cf, days_since_hw
)

# Update cooldown trackers
if cold_front_remaining == 0 and cold_front_days > 0:
    # Cold front just ended, reset cooldown
    self.storage.reset_cooldown(guild_id, "cold_front")
elif cold_front_days == 0 and cold_front_remaining > 0:
    # New cold front started, reset cooldown
    self.storage.reset_cooldown(guild_id, "cold_front")
else:
    # Increment cooldown counter
    self.storage.increment_cooldown(guild_id, "cold_front")

# Same for heat wave...

# Save with new fields
weather_db_data = {
    "season": season,
    "province": province,
    "wind_timeline": wind_timeline,
    "weather_type": weather_type,
    "weather_roll": 0,
    "temperature_actual": actual_temp,
    "temperature_category": temp_category,
    "temperature_roll": temp_roll,
    "cold_front_days_remaining": cold_front_remaining,
    "cold_front_total_duration": cold_front_total_new,  # NEW
    "heat_wave_days_remaining": heat_wave_remaining,
    "heat_wave_total_duration": heat_wave_total_new,    # NEW
}
```

### 4. **Stage Display** (`commands/weather_modules/stages.py`)

**Current State:**
- File handles multi-day stage summary displays
- `_format_day_summary()` creates condensed view of each day
- Currently does NOT display cold front/heat wave information
- Has no logic to extract or show special event data

**Functions to Modify:**

#### `_format_day_summary()` (Lines ~103-145)
**Current Code:**
```python
def _format_day_summary(day_data: Dict[str, Any]) -> str:
    weather_type = day_data.get("weather_type", "fair")
    temperature = day_data.get("actual_temp", day_data.get("temperature", 15))
    wind_timeline = day_data.get("wind_timeline", [])
    weather_effects = day_data.get("weather_effects", [])
    
    # Build summary parts
    parts = [f"{weather_emoji} **{weather_name}** | {temp_emoji} {temperature}°C"]
    
    # Add wind summary
    wind_summary = StageDisplayManager._format_condensed_wind(wind_timeline)
    if wind_summary:
        parts.append(f"💨 {wind_summary}")
    
    # Add effects if any
    if weather_effects:
        # ... effect display logic
    
    return "\n".join(parts)
```

**NEW - Add special event section:**
```python
def _format_day_summary(day_data: Dict[str, Any]) -> str:
    # ... existing code ...
    
    # Add special weather events (NEW)
    cold_front_days = day_data.get("cold_front_days_remaining", 0)
    cold_front_total = day_data.get("cold_front_total_duration", 0)
    heat_wave_days = day_data.get("heat_wave_days_remaining", 0)
    heat_wave_total = day_data.get("heat_wave_total_duration", 0)
    
    special_events = []
    if cold_front_days > 0 and cold_front_total > 0:
        days_elapsed = cold_front_total - cold_front_days + 1
        special_events.append(f"❄️ Cold Front (Day {days_elapsed}/{cold_front_total})")
    
    if heat_wave_days > 0 and heat_wave_total > 0:
        days_elapsed = heat_wave_total - heat_wave_days + 1
        special_events.append(f"🔥 Heat Wave (Day {days_elapsed}/{heat_wave_total})")
    
    if special_events:
        parts.extend(special_events)
    
    return "\n".join(parts)
```

**Impact:** Stage summaries will now show "❄️ Cold Front (Day 5/13)" for each affected day

---

### 5. **Weather Display** (`commands/weather_modules/display.py`)

**Current State:**
- File handles daily weather embed creation
- `_format_temperature()` displays temperature with description (Lines ~240-270)
- Uses `temp_description` field from weather_data dict
- Currently shows basic temperature category + optional description

**Function to Verify:** `_format_temperature()` (Lines ~238-270)

**Current Code:**
```python
def _format_temperature(weather_data: Dict[str, Any]) -> str:
    actual_temp = weather_data.get("actual_temp", weather_data.get("temperature", 15))
    perceived_temp = weather_data.get("perceived_temp", actual_temp)
    temp_description = weather_data.get("temp_description", "")  # <-- Gets description
    temp_category = weather_data.get("temp_category", "")
    
    # Base temperature with category
    if temp_category:
        category_display = temp_category.replace("_", " ").title()
        temp_text = f"**{actual_temp}°C** ({category_display} for the season)"
    else:
        temp_text = f"**{actual_temp}°C**"
    
    # Add description if available
    if temp_description:
        temp_text += f"\n*{temp_description}*"  # <-- Displays description
    
    # Add wind chill if different...
    return temp_text
```

**Analysis:**
- ✅ Already displays `temp_description` field correctly
- ✅ No changes needed in this file
- ✅ Will automatically show improved messages from `roll_temperature_with_special_events()`

**Verification Steps:**
1. Ensure `weather_data["temp_description"]` contains day counter text
2. Test daily weather display shows "Cold Front: Day X of Y"
3. Verify formatting matches expected style

---

### 6. **GM Notifications** (`commands/weather_modules/notifications.py`)

**Current State:**
- File handles GM channel notifications
- `_create_notification_embed()` builds mechanics-focused embed (Lines ~70-150)
- Currently does NOT display cold front/heat wave event details
- Shows temperature, wind, effects but missing special events

**Function to Modify:** `_create_notification_embed()` (Lines ~70-150)

**Current Code Structure:**
```python
def _create_notification_embed(weather_data: Dict[str, Any]) -> discord.Embed:
    day = weather_data.get("day", 1)
    province = weather_data.get("province", "Unknown")
    season = weather_data.get("season", "spring")
    weather_type = weather_data.get("weather_type", "fair")
    actual_temp = weather_data.get("actual_temp", 15)
    perceived_temp = weather_data.get("perceived_temp", actual_temp)
    temp_category = weather_data.get("temp_category", "")
    wind_timeline = weather_data.get("wind_timeline", [])
    weather_effects = weather_data.get("weather_effects", [])
    
    # ... creates embed with temperature, wind, effects ...
```

**NEW - Add special events section:**
```python
def _create_notification_embed(weather_data: Dict[str, Any]) -> discord.Embed:
    # ... existing extraction code ...
    
    # Extract special event data (NEW)
    cold_front_days = weather_data.get("cold_front_days", 0)
    cold_front_total = weather_data.get("cold_front_total_duration", 0)
    heat_wave_days = weather_data.get("heat_wave_days", 0)
    heat_wave_total = weather_data.get("heat_wave_total_duration", 0)
    
    # ... create embed ...
    
    # Add special events field if active (NEW)
    special_events = []
    if cold_front_days > 0 and cold_front_total > 0:
        days_elapsed = cold_front_total - cold_front_days + 1
        special_events.append(f"❄️ **Cold Front:** Day {days_elapsed} of {cold_front_total}")
        special_events.append(f"   └─ Temperature modifier: -10°C")
        if days_elapsed == 1:
            special_events.append(f"   └─ Flocks of emigrating birds fill the sky")
    
    if heat_wave_days > 0 and heat_wave_total > 0:
        days_elapsed = heat_wave_total - heat_wave_days + 1
        special_events.append(f"🔥 **Heat Wave:** Day {days_elapsed} of {heat_wave_total}")
        special_events.append(f"   └─ Temperature modifier: +10°C")
    
    if special_events:
        embed.add_field(
            name="🌡️ Special Weather Events",
            value="\n".join(special_events),
            inline=False
        )
    
    return embed
```

**Impact:** GM notifications will include dedicated section showing active special events with day counters

---

### 7. **Weather Formatters** (`commands/weather_modules/formatters.py`)

**Current State:**
- File contains pure utility functions for formatting
- No cold front/heat wave logic
- All functions are static helpers

**Analysis:**
- ✅ No changes needed
- ✅ No special event formatting logic required here
- ✅ Existing emoji/text formatters sufficient

**Verification:** Confirm no dependencies on special event data

---

### 8. **Daily Temperature Variation - Additional Changes**

This section covers the additional changes needed to implement daily temperature variation during cold fronts and heat waves.

#### **`utils/weather_mechanics.py` - Temperature Variation Logic**

**New Function to Add:**
```python
def get_category_from_actual_temp(actual_temp: int, base_temp: int) -> str:
    """
    Determine temperature category based on difference from base temperature.
    
    Used during cold fronts/heat waves to categorize the final temperature
    after event modifiers and daily variation have been applied.
    
    Args:
        actual_temp: Final calculated temperature (°C)
        base_temp: Province/season base temperature (°C)
        
    Returns:
        Category string for display
        
    Examples:
        >>> get_category_from_actual_temp(6, 21)  # 15° below base
        'extremely_low'
        
        >>> get_category_from_actual_temp(11, 21)  # 10° below base
        'very_low'
        
        >>> get_category_from_actual_temp(18, 21)  # 3° below base
        'cool'
    """
    diff = actual_temp - base_temp
    
    if diff <= -15:
        return "extremely_low"
    elif diff <= -10:
        return "very_low"
    elif diff <= -6:
        return "low"
    elif diff <= -3:
        return "cool"
    elif diff <= 2:
        return "average"
    elif diff <= 5:
        return "warm"
    elif diff <= 9:
        return "high"
    elif diff <= 14:
        return "very_high"
    else:
        return "extremely_high"
```

**Modified:** `roll_temperature_with_special_events()`

**Key Changes:**
1. Always roll d100 for daily variation (even during events)
2. Suppress special event triggers (roll=2, roll=99) during active events
3. Apply daily modifier AFTER event modifier
4. Recalculate category based on final temperature
5. Update description to reflect final category + event status

**Detailed Logic Flow:**
```python
def roll_temperature_with_special_events(
    season: str,
    province: str,
    cold_front_days: int = 0,
    cold_front_total: int = 0,
    heat_wave_days: int = 0,
    heat_wave_total: int = 0,
    days_since_last_cold_front: int = 99,
    days_since_last_heat_wave: int = 99
) -> Tuple[int, str, str, int, int, int, int, int]:
    """
    Roll for temperature with special events and daily variation.
    
    During active events, temperature still varies day-to-day but within
    the event's influence (e.g., cold front keeps it cold but not static).
    """
    # 1. Roll for daily temperature variation
    roll = random.randint(1, 100)
    original_roll = roll
    
    # 2. Suppress event triggers during active events
    if cold_front_days > 0 and roll == 2:
        roll = 3  # Treat as very_low instead of triggering new cold front
    if heat_wave_days > 0 and roll == 99:
        roll = 98  # Treat as very_high instead of triggering new heat wave
    
    # 3. Get daily variation from temperature table
    _, daily_modifier = get_temperature_category_from_roll(roll)
    
    # 4. Get base temperature
    base_temp = get_province_base_temperature(province, season)
    
    # 5. Handle special events (cold fronts/heat waves)
    cold_mod, cold_front_remaining, cold_front_total_new = handle_cold_front(
        original_roll, cold_front_days, cold_front_total,
        days_since_last_cold_front, heat_wave_days > 0
    )
    
    heat_mod, heat_wave_remaining, heat_wave_total_new = handle_heat_wave(
        original_roll, heat_wave_days, heat_wave_total,
        days_since_last_heat_wave, cold_front_days > 0
    )
    
    # 6. Calculate final temperature: base + event + daily_variation
    actual_temp = base_temp + cold_mod + heat_mod + daily_modifier
    
    # 7. Determine category based on final temperature (not base)
    final_category = get_category_from_actual_temp(actual_temp, base_temp)
    
    # 8. Build description
    description = TEMPERATURE_DESCRIPTIONS.get(
        final_category, TEMPERATURE_DESCRIPTIONS["average"]
    )
    
    # 9. Add special event information
    if cold_front_remaining > 0:
        days_elapsed = cold_front_total_new - cold_front_remaining + 1
        
        if days_elapsed == 1:
            description += f"\n*❄️ Cold Front: Day {days_elapsed} of {cold_front_total_new} - Sky filled with flocks of emigrating birds*"
        elif cold_front_remaining == 1:
            description += f"\n*❄️ Cold Front: Day {days_elapsed} of {cold_front_total_new} (Final Day)*"
        else:
            description += f"\n*❄️ Cold Front: Day {days_elapsed} of {cold_front_total_new}*"
    
    if heat_wave_remaining > 0:
        days_elapsed = heat_wave_total_new - heat_wave_remaining + 1
        
        if days_elapsed == 1:
            description += f"\n*🔥 Heat Wave: Day {days_elapsed} of {heat_wave_total_new}*"
        elif heat_wave_remaining == 1:
            description += f"\n*🔥 Heat Wave: Day {days_elapsed} of {heat_wave_total_new} (Final Day)*"
        else:
            description += f"\n*🔥 Heat Wave: Day {days_elapsed} of {heat_wave_total_new}*"
    
    return (
        actual_temp,
        final_category,
        description,
        original_roll,  # Return original roll for debugging/logging
        cold_front_remaining,
        cold_front_total_new,
        heat_wave_remaining,
        heat_wave_total_new,
    )
```

**Why This Works:**
- **Event consistency**: Cold front modifier (-10°C) always applies
- **Daily realism**: Temperature varies ±5°C day-to-day from normal table
- **No conflict**: Can't trigger new event during existing event
- **Correct categorization**: Final temp determines display category
- **Natural feel**: "Cold with mild relief" vs "Cold and getting colder"

#### **`db/weather_data.py` - Temperature Categories**

**Current State:**
- `TEMPERATURE_RANGES` table maps d100 rolls to modifiers
- Used for initial temperature determination
- Works well for normal weather

**Analysis:**
- ✅ No changes needed to TEMPERATURE_RANGES table
- ✅ Table still used for daily variation rolls
- ✅ New `get_category_from_actual_temp()` function supplements (not replaces) this

**Verification:** Existing table provides good ±5°C spread for daily variation

#### **`commands/weather_modules/handler.py` - No Additional Changes**

**Analysis:**
- ✅ Handler already passes all necessary data to `roll_temperature_with_special_events()`
- ✅ Returns actual_temp, category, description - all correctly populated
- ✅ No changes needed beyond those already planned for cooldown tracking

**Verification:** Handler treats temperature function as black box - internal logic changes don't affect it

#### **`commands/weather_modules/display.py` - No Additional Changes**

**Analysis:**
- ✅ Display uses `temp_description` field which includes event info
- ✅ Shows actual_temp which is correctly calculated with variation
- ✅ Category display reflects final temperature automatically

**Example Output:**
```
🌡️ Temperature: 6°C (Low for the season)
Cool temperatures persist.
❄️ Cold Front: Day 2 of 3
```

#### **`commands/weather_modules/notifications.py` - Enhanced GM Info**

**Potential Enhancement (Optional):**
Add breakdown of temperature calculation to GM notifications:

```python
def _create_notification_embed(weather_data: Dict[str, Any]) -> discord.Embed:
    # ... existing code ...
    
    # Add temperature breakdown during events (OPTIONAL)
    if cold_front_days > 0 or heat_wave_days > 0:
        temp_breakdown = []
        base_temp = weather_data.get("base_temp", 0)
        actual_temp = weather_data.get("actual_temp", 0)
        
        temp_breakdown.append(f"Base Temperature: {base_temp}°C")
        
        if cold_front_days > 0:
            temp_breakdown.append(f"Cold Front Modifier: -10°C")
        if heat_wave_days > 0:
            temp_breakdown.append(f"Heat Wave Modifier: +10°C")
        
        daily_var = actual_temp - base_temp - (cold_front_days * -10) - (heat_wave_days * 10)
        if daily_var != 0:
            temp_breakdown.append(f"Daily Variation: {'+' if daily_var > 0 else ''}{daily_var}°C")
        
        temp_breakdown.append(f"**Final Temperature: {actual_temp}°C**")
        
        embed.add_field(
            name="🌡️ Temperature Calculation",
            value="\n".join(temp_breakdown),
            inline=False
        )
```

**Example GM Notification:**
```
🌡️ Temperature Calculation
Base Temperature: 21°C (Reikland, Summer)
Cold Front Modifier: -10°C
Daily Variation: -5°C (low roll)
Final Temperature: 6°C
```

#### **`commands/weather_modules/stages.py` - No Additional Changes**

**Analysis:**
- ✅ Stage summary shows temperature per day
- ✅ Each day's temperature is independently calculated with variation
- ✅ Players will see natural variation: "Day 1: 11°C, Day 2: 6°C, Day 3: 16°C"
- ✅ Cold front indicator shows on all affected days

---

### 9. **Database Data** (`db/weather_data.py`)

**Update Documentation Strings:**
```python
SPECIAL_EVENTS = {
    "cold_front": "Cold Front: Temperatures remain 'very low' during cold front period. Sky is filled by flocks of emigrating birds",
    "heat_wave": "Heat Wave: Temperature remains 'very high' during heat wave period. Both in summer and winter this can be disastrous",
}
```

---

## Implementation Steps

### Phase 1: Database Schema (Core Foundation)
**Priority: CRITICAL**

1. **Modify `weather_storage.py`:**
   - Add new columns to `daily_weather` table
   - Add new columns to `guild_weather_state` table
   - Create migration logic in `init_database()`
   - Add new methods for cooldown management

2. **Test migration:**
   - Create test database
   - Run migration
   - Verify columns exist
   - Test with existing journey data

### Phase 2: Weather Mechanics (Core Logic)
**Priority: CRITICAL**

1. **Add `get_category_from_actual_temp()` helper in `weather_mechanics.py`:**
   - Maps final temperature to category based on difference from base
   - Used during events to categorize temperature after all modifiers
   - Test with various temperature differentials

2. **Modify `handle_cold_front()` in `weather_mechanics.py`:**
   - Add cooldown parameter
   - Add heat_wave_active parameter
   - Add total_duration return value
   - Implement cooldown check
   - Implement mutual exclusivity check
   - **Accept original_roll parameter to check for trigger (roll=2)**

3. **Modify `handle_heat_wave()` in `weather_mechanics.py`:**
   - Same changes as cold front
   - **Accept original_roll parameter to check for trigger (roll=99)**

4. **Modify `roll_temperature_with_special_events()` in `weather_mechanics.py`:**
   - Update function signature
   - Update return tuple
   - **Implement daily variation logic:**
     - Always roll d100 for temperature
     - Suppress special event triggers during active events (roll=2 → 3, roll=99 → 98)
     - Get daily_modifier from temperature table
     - Apply event modifier + daily modifier
     - Recalculate category using `get_category_from_actual_temp()`
   - Improve display message formatting
   - Add day counter logic
   - **Pass original_roll to event handlers**

5. **Test mechanics:**
   - Unit test cooldown logic
   - Unit test mutual exclusivity
   - Unit test day counter display
   - **Unit test daily variation during cold fronts**
     - Cold front active, roll=45 (average) → temp = base - 10 + 0
     - Cold front active, roll=15 (low) → temp = base - 10 - 5
     - Cold front active, roll=85 (high) → temp = base - 10 + 5
   - **Unit test special roll suppression**
     - Cold front active, roll=2 → treated as roll=3, no new cold front
     - Heat wave active, roll=99 → treated as roll=98, no new heat wave
   - **Unit test category recalculation**
     - Verify final category matches actual temperature, not base

### Phase 3: Handler Integration (Glue Layer)
**Priority: HIGH**

1. **Modify `_generate_daily_weather()` in `handler.py`:**
   - Extract cooldown trackers from journey state
   - Pass all context to temperature roll
   - Update cooldown trackers after roll
   - Save new fields to database

2. **Test handler:**
   - Test cold front start → cooldown reset
   - Test cold front end → cooldown increment
   - Test cooldown preventing new events
   - Test events saved correctly

### Phase 4: Display Updates (User Experience)
**Priority: MEDIUM**

1. **Modify `_format_day_summary()` in `stages.py`:**
   - Extract cold_front_days_remaining and cold_front_total_duration
   - Extract heat_wave_days_remaining and heat_wave_total_duration
   - Calculate days_elapsed for each active event
   - Append day counter format to special_events list
   - Update display: "❄️ Cold Front (Day X/Y)"

2. **Add special events section in `notifications.py`:**
   - Extract event data from weather_data dict
   - Calculate days_elapsed for display
   - Create special events embed field
   - Include temperature modifiers
   - Add flavor text for first day of events

3. **Verify `display.py` shows day counts:**
   - Check player channel messages
   - Confirm temp_description contains day counter
   - Verify formatting consistency
   - No code changes needed (uses temp_description from mechanics)

4. **Test display:**
   - Generate multi-day stage with active cold front
   - Verify day counts appear correctly in stage summary
   - Verify day counts increment properly across days
   - Check GM notifications show special events section
   - Verify player channel shows improved messages

---

### Phase 5: Testing & Validation (Quality Assurance)
**Priority: HIGH**

1. **Manual testing scenarios:**
   - Start journey → Force cold front (override?)
   - Verify: "Day 1 of X" appears
   - Generate 5 days → Verify counter increments
   - Wait for cold front to end → Verify cooldown active
   - Generate 7 days → Verify new cold front can trigger
   - Test heat wave same way
   - Test mutual exclusivity (force both somehow)

2. **Edge cases:**
   - Journey with 100+ days
   - Multiple stage progressions during events
   - Bot restart mid-cold-front
   - Database migration from old format

3. **Test case updates:**
   - Update `TEST_GUIDE.md` TC-W03
   - Add new test cases for cooldown
   - Add test cases for day counter display

---

## Weather Modules Architecture

### Module Responsibilities

The `commands/weather_modules/` directory contains specialized modules for weather display:

```
commands/weather_modules/
├── __init__.py              # Module initialization
├── handler.py               # Core weather generation logic (✏️ MODIFY)
├── display.py               # Player-facing embeds (✓ VERIFY ONLY)
├── notifications.py         # GM channel notifications (✏️ MODIFY)
├── stages.py                # Multi-day stage displays (✏️ MODIFY)
└── formatters.py            # Utility formatting functions (✓ NO CHANGES)
```

### Data Flow

**Weather Generation → Display Pipeline:**

```
1. User runs /weather next
   ↓
2. handler.py generates weather data
   ├─ Calls roll_temperature_with_special_events() in weather_mechanics.py
   ├─ Gets (temp, category, description, roll, cf_remaining, cf_total, hw_remaining, hw_total)
   ├─ Stores data in weather_storage.py database
   └─ Builds weather_data dict with all fields
   ↓
3. display.py creates player embed
   ├─ Reads weather_data["temp_description"]  # Contains "Cold Front: Day X of Y"
   ├─ Calls _format_temperature() to display
   └─ Sends embed to player channel
   ↓
4. notifications.py creates GM embed
   ├─ Reads weather_data["cold_front_days"], ["cold_front_total_duration"]
   ├─ Calculates days_elapsed for display
   ├─ Creates special events field
   └─ Sends embed to GM channel
```

**Stage Generation → Display Pipeline:**

```
1. User runs /weather next-stage
   ↓
2. handler.py generates multiple days
   ├─ Calls _generate_daily_weather() for each day
   ├─ Each day gets cold_front/heat_wave tracking
   └─ Returns list of weather_data dicts
   ↓
3. stages.py creates stage summary
   ├─ Iterates over stage_data list
   ├─ For each day: calls _format_day_summary()
   ├─ Extracts cold_front_days, cold_front_total from day_data
   ├─ Calculates days_elapsed
   ├─ Appends "❄️ Cold Front (Day X/Y)" to summary
   └─ Sends consolidated embed to player channel
   ↓
4. notifications.py creates GM embeds
   └─ Sends separate notification for each day (3 embeds for 3-day stage)
```

### Key Data Structures

**weather_data dict (passed between modules):**
```python
{
    "day": 15,
    "season": "summer",
    "province": "reikland",
    "weather_type": "rain",
    "actual_temp": 1,                        # With cold front modifier applied
    "perceived_temp": -4,                     # With wind chill
    "temp_category": "very_cold",
    "temp_description": "Very Cold\n*❄️ Cold Front: Day 5 of 13*",  # NEW FORMAT
    "wind_timeline": [...],
    "weather_effects": [...],
    "cold_front_days_remaining": 9,          # Existing (countdown)
    "cold_front_total_duration": 13,         # NEW (rolled once at start)
    "heat_wave_days_remaining": 0,           # Existing
    "heat_wave_total_duration": 0,           # NEW
}
```

**Database schema (stored per day):**
```sql
daily_weather:
    cold_front_days_remaining: 9          -- Days left
    cold_front_total_duration: 13         -- NEW: Total duration rolled
    heat_wave_days_remaining: 0
    heat_wave_total_duration: 0           -- NEW
    
guild_weather_state:
    days_since_last_cold_front: 0         -- NEW: Cooldown tracker
    days_since_last_heat_wave: 99         -- NEW: Cooldown tracker (99 = never)
```

### Module Interactions

**handler.py responsibilities:**
- Generate weather using mechanics functions
- Track cooldowns via storage methods
- Build complete weather_data dict
- Save to database
- Return data to display modules

**display.py responsibilities:**
- Create player-facing embeds
- Format temperature with temp_description
- Display wind timeline
- Show weather effects
- **Does NOT calculate days_elapsed** (uses pre-formatted description)

**notifications.py responsibilities:**
- Create GM-facing embeds
- Show mechanical details
- **DOES calculate days_elapsed** (for detailed special events section)
- Include dice rolls and modifiers
- Boat handling reference table

**stages.py responsibilities:**
- Create multi-day summaries
- Condensed format for quick viewing
- **DOES calculate days_elapsed** (for stage view day counters)
- Aggregate wind patterns
- Show special events per day

**formatters.py responsibilities:**
- Pure utility functions
- No business logic
- Emoji selection
- Text formatting
- **No special event logic**

### Why This Architecture?

**Separation of Concerns:**
- `handler.py` = business logic (what data to generate)
- `display.py` = presentation (how to show to players)
- `notifications.py` = GM view (mechanics for running game)
- `stages.py` = multi-day aggregation (overview displays)

**Benefits:**
1. **Single Source of Truth:** Special event duration calculated once in `weather_mechanics.py`
2. **DRY Principle:** Day counter calculation reused in stages.py and notifications.py
3. **Testability:** Each module can be tested independently
4. **Maintainability:** Changes to display don't affect generation logic
5. **Flexibility:** Can add new display modes without touching core mechanics

---

## Database Schema Detail

### New Columns

**`daily_weather` table:**
```sql
CREATE TABLE daily_weather (
    -- ... existing columns ...
    cold_front_days_remaining INTEGER DEFAULT 0,           -- Existing
    cold_front_total_duration INTEGER DEFAULT 0,            -- NEW
    heat_wave_days_remaining INTEGER DEFAULT 0,            -- Existing
    heat_wave_total_duration INTEGER DEFAULT 0              -- NEW
);
```

**`guild_weather_state` table:**
```sql
CREATE TABLE guild_weather_state (
    -- ... existing columns ...
    days_since_last_cold_front INTEGER DEFAULT 99,         -- NEW (99 = never happened)
    days_since_last_heat_wave INTEGER DEFAULT 99           -- NEW (99 = never happened)
);
```

### Data Flow Example

**Scenario: 3-day cold front (rolled 1d5, got 3)**

```
Day 1: Roll = 2 (cold front triggers, 1d5 rolled = 3)
  DB State:
    cold_front_days_remaining: 3
    cold_front_total_duration: 3
    days_since_last_cold_front: 0 (just started)
  Display: "❄️ Cold Front: Day 1 of 3"

Day 2: No new roll
  DB State:
    cold_front_days_remaining: 2
    cold_front_total_duration: 3 (preserved)
    days_since_last_cold_front: 0 (still active)
  Display: "❄️ Cold Front: Day 2 of 3"

Day 3: Final day
  DB State:
    cold_front_days_remaining: 1
    cold_front_total_duration: 3
    days_since_last_cold_front: 0
  Display: "❄️ Cold Front: Day 3 of 3 (Final Day)"

Day 4: Cold front ends
  DB State:
    cold_front_days_remaining: 0
    cold_front_total_duration: 0
    days_since_last_cold_front: 1 (cooldown starts)
  Display: No cold front message

Day 5-10: Cooldown period
  DB State:
    days_since_last_cold_front: 2, 3, 4, 5, 6, 7
  Note: Even if roll = 2, cold front blocked

Day 11+: Cooldown over
  DB State:
    days_since_last_cold_front: 8+
  Note: roll = 2 can trigger new cold front (1d5 days, could be 1-5)
```

---

## Constants & Configuration

**Add to `weather_mechanics.py`:**
```python
# Special event constants
COLD_FRONT_TRIGGER_ROLL = 2           # d100 roll that triggers cold front
HEAT_WAVE_TRIGGER_ROLL = 99           # d100 roll that triggers heat wave

COLD_FRONT_DURATION_DICE = 5          # 1d5 days for cold front
COLD_FRONT_BASE_DURATION = 0          # No base duration (just 1d5)

HEAT_WAVE_BASE_DURATION = 10          # Base days for heat wave
HEAT_WAVE_VARIABLE_DURATION = 10      # 1d10 additional days

COLD_FRONT_COOLDOWN_DAYS = 7          # Days before another cold front can occur
HEAT_WAVE_COOLDOWN_DAYS = 7           # Days before another heat wave can occur

COLD_FRONT_TEMP_MODIFIER = -10        # Temperature change during cold front (°C)
HEAT_WAVE_TEMP_MODIFIER = 10          # Temperature change during heat wave (°C)
```

---

## Benefits of This Approach

### 1. **Clear Communication**
- Users see exact duration: "3 days" instead of "1d5 days" (cold front) or "13 days" instead of "10+1d10 days" (heat wave)
- Progress tracking: "Day 2 of 3" or "Day 5 of 13"
- Expectation management: Players know when events end

### 2. **Realistic Weather Patterns**
- Cooldown prevents unrealistic frequency
- Mutual exclusivity prevents conflicting conditions
- More immersive gameplay experience

### 3. **Better Testing**
- Can verify day counts increment correctly
- Can test cooldown mechanics
- TC-W03 becomes more meaningful

### 4. **Maintainability**
- Single source of truth for duration (stored once)
- Clear separation of concerns (mechanics vs display)
- Easy to adjust cooldown constants

### 5. **Stage System Compatibility**
- Multi-day stages show event progress
- Stage summaries include day counters
- Consistent display across single/multi-day commands

---

## Backward Compatibility

### Migration Strategy

**For existing journeys:**
1. Check if new columns exist
2. If `cold_front_days_remaining > 0` but `cold_front_total_duration = 0`:
   - Assume mid-event with unknown total
   - Set `cold_front_total_duration = cold_front_days_remaining` (conservative estimate)
3. Set `days_since_last_cold_front = 99` (assume cooldown expired)

**SQL Migration:**
```sql
-- Add columns with default values
ALTER TABLE daily_weather ADD COLUMN cold_front_total_duration INTEGER DEFAULT 0;
ALTER TABLE daily_weather ADD COLUMN heat_wave_total_duration INTEGER DEFAULT 0;

-- Fix active events with unknown totals
UPDATE daily_weather 
SET cold_front_total_duration = cold_front_days_remaining 
WHERE cold_front_days_remaining > 0 AND cold_front_total_duration = 0;

UPDATE daily_weather 
SET heat_wave_total_duration = heat_wave_days_remaining 
WHERE heat_wave_days_remaining > 0 AND heat_wave_total_duration = 0;
```

---

## Testing Checklist

### Unit Tests
- [ ] `handle_cold_front()` with cooldown active → Returns (0, 0, 0)
- [ ] `handle_cold_front()` with heat wave active → Returns (0, 0, 0)
- [ ] `handle_cold_front()` with roll=2 and cooldown expired → Returns (-10, duration, duration)
- [ ] `handle_cold_front()` with continuing event → Returns (-10, remaining-1, total)
- [ ] Same tests for `handle_heat_wave()`
- [ ] **`roll_temperature_with_special_events()` with active cold front:**
  - [ ] Roll=45 (average) → temp = base - 10 + 0
  - [ ] Roll=15 (low) → temp = base - 10 - 5  
  - [ ] Roll=85 (high) → temp = base - 10 + 5
  - [ ] Roll=2 → treated as roll=3, no new cold front triggered
- [ ] **`get_category_from_actual_temp()` accuracy:**
  - [ ] 15° below base → "extremely_low"
  - [ ] 10° below base → "very_low"
  - [ ] 3° below base → "cool"
  - [ ] ±2° from base → "average"

### Integration Tests
- [ ] Start journey → Force cold front → Verify duration stored
- [ ] Continue journey 5 days → Verify day counter increments
- [ ] **During cold front: Verify temperature varies day-to-day (not static)**
- [ ] **During cold front: Verify temperature stays within cold range (not jumping to hot)**
- [ ] Cold front ends → Verify cooldown starts
- [ ] Generate 7 days → Verify cooldown blocks new event
- [ ] Generate 8th day → Verify new event can trigger
- [ ] Active cold front → Try heat wave → Verify blocked

### Display Tests
- [ ] Day 1 of cold front shows: "Day 1 of X"
- [ ] Day 5 of cold front shows: "Day 5 of X"
- [ ] Final day shows: "Day X of X (Final Day)"
- [ ] **Temperature description matches final temp (e.g., "Cool" for 16°C, not "Very Low")**
- [ ] **Stage summary shows different temps across cold front days (e.g., 11°C, 6°C, 16°C)**
- [ ] Stage summary shows day counters
- [ ] GM notifications include day counters
- [ ] **(Optional) GM notifications show temperature calculation breakdown**

### Edge Case Tests
- [ ] Bot restart mid-cold-front → Resume correctly
- [ ] **Cold front with extreme daily variation (roll=1 vs roll=100 on consecutive days)**
- [ ] **Heat wave with daily variation (verify +10°C base + daily modifier)**
- [ ] Migration from old format → Preserves active events
- [ ] Overlapping stage and event boundary
- [ ] **Roll=2 during active cold front → Should NOT trigger nested cold front**
- [ ] **Roll=99 during active heat wave → Should NOT trigger nested heat wave**

---

## Risk Assessment

### Low Risk
- Database schema additions (uses DEFAULT values)
- Display changes (cosmetic)
- Constants configuration (easy to tune)

### Medium Risk
- Handler logic changes (must track cooldowns correctly)
- Migration logic (must handle existing data)

### High Risk
- Weather mechanics signature changes (affects multiple files)
- Mutual exclusivity logic (could break event generation)

### Mitigation
- Add comprehensive unit tests before implementation
- Test migration on copy of production database
- Implement feature flag for new vs old behavior
- Rollback plan: Keep old functions as `_legacy` versions

---

## Estimated Effort

- **Phase 1 (Database):** 2-3 hours
- **Phase 2 (Mechanics):** 3-4 hours
- **Phase 3 (Handler):** 2-3 hours
- **Phase 4 (Display):** 1-2 hours
- **Phase 5 (Testing):** 3-4 hours

**Total:** ~11-16 hours (1.5-2 full dev days)

---

## Future Enhancements

### Optional Improvements
1. **Configurable cooldowns:** GM command to set cooldown duration
2. **Event history:** Track all past cold fronts/heat waves
3. **Seasonal adjustments:** Winter cold fronts last longer
4. **Intensity variations:** Some cold fronts are -15°C instead of -10°C
5. **Visual calendar:** Show event timeline for entire journey

### Extended Mechanics
1. **Snow accumulation:** Track snow depth during winter cold fronts
2. **Heat exhaustion:** Track crew fatigue during heat waves
3. **Ice formation:** River freezing during prolonged cold fronts
4. **Crop impact:** Mention harvest effects for immersion

---

## Summary

This plan converts the weather event system from **showing formulas** to **storing and displaying actual rolled values**, while adding **cooldown mechanics** to prevent unrealistic frequency and **mutual exclusivity** to prevent conflicting events.

**Key Changes:**
1. Store total duration in database
2. Display progress as "Day X of Y"
3. Add 7-day cooldown after events end
4. Prevent cold front + heat wave overlap
5. Update display across all views (daily, stage, GM)

**Result:** More immersive, predictable, and testable weather system that better serves the WFRP narrative experience.

---

## Quick Reference: Files Affected

### Core System Files (5 modifications)
```
✏️  db/weather_storage.py              - Add 4 columns, cooldown methods
✏️  utils/weather_mechanics.py         - Update handlers, add cooldown checks
✏️  commands/weather_modules/handler.py - Track cooldowns, pass context
✏️  commands/weather_modules/stages.py  - Display day counters
✏️  commands/weather_modules/notifications.py - Add special events section
```

### Peripheral Files (2 verifications, 1 trivial update)
```
✓   commands/weather_modules/display.py - Verify temp_description display
✓   commands/weather_modules/formatters.py - No changes needed
📝  db/weather_data.py                  - Update doc strings
```

### Implementation Order
```
Phase 1: Database (storage.py)           - Foundation
Phase 2: Mechanics (weather_mechanics.py) - Core logic  
Phase 3: Handler (handler.py)            - Integration
Phase 4: Display (stages.py, notifications.py) - User experience
Phase 5: Testing                         - Validation
```

### Testing Focus Areas
```
- Day counter increments correctly (1/3, 2/3, 3/3 for 3-day cold front)
- Cold fronts last 1-5 days (test multiple rolls to see variation)
- Cooldown prevents events for 7 days
- Events don't overlap (mutual exclusivity)
- Stage view shows counters
- GM notifications show special events section
- Display formats match expected style
- Single-day cold fronts display correctly (Day 1 of 1)
```
