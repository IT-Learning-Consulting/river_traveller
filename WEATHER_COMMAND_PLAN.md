# Weather Generator Command - Implementation Plan

## Overview
Create a `/weather` command that generates realistic daily weather for WFRP river travel, including wind conditions (with mechanics), general weather, and temperature.

## Command Structure
```
/weather <season> [province]
```
- **season**: spring, summer, autumn, winter (required)
- **province**: reikland (default), nordland, ostland, etc. (optional)

## Data Requirements

### 1. Wind Mechanics (Core Gameplay Impact)
**Wind Table (2d10)**
- Strength: d10 (1-2 Calm, 3-4 Light, 5-6 Bracing, 7-8 Strong, 9-10 Very Strong)
- Direction: d10 (1-3 Tailwind, 4-7 Sidewind, 8-10 Headwind)

**Movement Modifiers:**
- Calm + Drift: -10 penalty, 25% speed
- Light + Tailwind: +5% speed
- Light + Headwind: -5% speed
- Bracing + Tailwind: +10% speed
- Bracing + Sidewind: +5% + tacking required
- Bracing + Headwind: -10% speed
- Strong + Tailwind: +20% speed
- Strong + Sidewind: +10% + tacking required
- Strong + Headwind: -20% speed
- Very Strong + Tailwind: +25% speed
- Very Strong + Sidewind: Requires successful test (Note 4)
- Very Strong + Headwind: -25% speed

**Wind Changes:**
- Check at: dawn, mid-day, dusk, midnight
- Roll d10, on 1: wind changes one step (50% stronger, 50% lighter)
- Calm can only → Light
- Very Strong can only → Strong

### 2. Weather Conditions (Flavor + Some Mechanics)
**Weather Table (d100) - Seasonal**

Spring: 
- 01-10: Dry (-10 Forage)
- 11-30: Fair (no effects)
- 31-90: Rain (-10 ranged, 75ft visibility)
- 91-95: Downpour (-10 all physical, -20 ranged, near-zero visibility)
- 96-00: Snow (150ft visibility, no faster than Walk, Average +20 Endurance or Fatigued)

Summer:
- 01-40: Dry (-10 Forage)
- 41-70: Fair (no effects)
- 71-95: Rain (-10 ranged, 75ft visibility)
- 96-00: Downpour (-10 all physical, -20 ranged)

Autumn:
- 01-30: Dry (-10 Forage)
- 31-60: Fair (no effects)
- 61-90: Rain (-10 ranged, 75ft visibility)
- 91-98: Downpour (-10 all physical, -20 ranged)
- 99-00: Snow (150ft visibility, no faster than Walk)

Winter:
- 01-10: Fair (no effects)
- 11-60: Rain (-10 ranged, 75ft visibility)
- 61-65: Downpour (-10 all physical, -20 ranged)
- 66-90: Snow (150ft visibility, no faster than Walk)
- 91-00: Blizzard (Snow effects + worse)

### 3. Temperature System
**Temperature Roll (d100)**
- 01: Extremely Low (-15°C from average)
- 02: Cold Front (Very Low for 10+d10 days)
- 03-10: Very Low (-10°C from average)
- 11-25: Low (-5°C from average)
- 26-75: Average (with 33=cold night, 66=warm night)
- 76-90: High (+5°C from average)
- 91-98: Very High (+10°C from average)
- 99: Heat Wave (Very High for 10+d10 days)
- 00: Extremely High (+15°C from average)

**Wind Chill Modifiers:**
- Light/Bracing: -5°C perceived
- Strong/Very Strong: -10°C perceived

**Province Average Temperatures (°C) by Season:**
```
Province        | Spring | Summer | Autumn | Winter
----------------|--------|--------|--------|--------
Reikland        | 9      | 21     | 11     | 0
Middenland      | 7      | 21     | 14     | -2
Talabecland     | 10     | 22     | 13     | -2
Averland        | 11     | 22     | 13     | -1
Ostland         | 8      | 21     | 10     | -2
Nordland        | 7      | 19     | 10     | -1
(etc - add all provinces)
```

## Implementation Steps

### Step 1: Create Data Module (`db/weather_data.py`) ✅ COMPLETED
- [x] Wind conditions table (strength × direction matrix)
- [x] Wind modifier lookup (movement % and special notes)
- [x] Weather conditions by season
- [x] Province temperature averages by season (15 provinces)
- [x] Temperature description lookup
- [x] Helper functions: `get_wind_strength_from_roll()`, `get_wind_direction_from_roll()`, `get_weather_from_roll()`, `get_temperature_category_from_roll()`, `get_province_base_temperature()`, `get_available_provinces()`

**Status:** File created with 322 lines, all data tables implemented

### Step 2: Create Weather Mechanics (`utils/weather_mechanics.py`) ✅ COMPLETED
- [x] `generate_wind_conditions()` -> Returns initial wind (strength, direction)
- [x] `check_wind_change(current_strength)` -> Returns bool and new strength if changed
- [x] `get_wind_modifiers(strength, direction)` -> Returns movement %, penalties, special notes
- [x] `generate_daily_wind()` -> Returns wind at dawn, midday, dusk, midnight
- [x] `roll_weather_condition(season)` -> Returns weather type
- [x] `get_weather_effects(weather_type)` -> Returns mechanical effects
- [x] `roll_temperature(season, province)` -> Returns actual temp
- [x] `apply_wind_chill(temp, wind_strength)` -> Returns perceived temp
- [x] `get_temperature_description_text(temp, average)` -> Returns description
- [x] `get_wind_chill_note(wind_strength)` -> Returns wind chill note text

**Status:** File created with 244 lines, all mechanics functions working correctly

### Step 3: Create Weather Command (`commands/weather.py`) ✅ COMPLETED
- [x] Slash command: `/weather <season> [province]`
- [x] Prefix command: `/weather <season> [province]`
- [x] Generate complete daily weather:
  - Initial wind at dawn
  - Wind changes throughout day (with chance rolls)
  - Weather condition
  - Temperature (actual and perceived)
- [x] Format main embed with:
  - Season and location
  - Wind conditions timeline (dawn/midday/dusk/midnight)
  - Weather condition with effects
  - Temperature (with wind chill)
  - Visual indicators (emojis for wind/weather/temp)
- [x] Send mechanics summary to #boat-travelling-notifications:
  - Active movement modifiers
  - Active penalties
  - Special conditions (tacking required, tests needed, etc.)
- [x] Error handling for invalid inputs
- [x] Helper functions: `get_weather_emoji()`, `get_temperature_emoji()`, `send_mechanics_notification()`

**Status:** File created with 322 lines, full command implementation complete

### Step 4: Embed Design ✅ COMPLETED
**Main Weather Embed:**
```
🌤️ Daily Weather - Summer in Reikland

🌬️ Wind Conditions:
Dawn:     Light Tailwind      (+5% speed)
Midday:   Bracing Tailwind    (+10% speed, tacking if needed)
Dusk:     Bracing Tailwind    (+10% speed, tacking if needed)  
Midnight: Light Sidewind      (no modifier)

☁️ Weather: Fair
Clear skies, no weather-related hazards.

🌡️ Temperature: 18°C (Average for season)
Feels like: 13°C (wind chill from Bracing wind)
Comfortable travelling conditions.
```

**Notifications Channel Embed:**
```
⚠️ Active Mechanics - Daily Weather

🚢 Boat Handling Modifiers:
• Dawn-Dusk: +10% movement speed (Bracing Tailwind)
• Tacking required for speed bonus (successful Boat Handling Test)
• Midnight: Normal speed (Light Sidewind)

🎯 Combat/Test Modifiers:
• None (Fair weather)

💡 Notes:
• Wind may change at midday, dusk, or midnight (10% chance each)
• Temperature comfortable for travel
```

**Status:** Embeds fully implemented with emojis, formatting, and all required fields

### Step 5: Helper Functions ✅ COMPLETED
- [x] Format wind strength name (uses WIND_STRENGTH dict)
- [x] Format wind direction name (uses WIND_DIRECTION dict)
- [x] Format weather emoji (`get_weather_emoji()`)
- [x] Format temperature emoji (`get_temperature_emoji()`)
- [x] Format effects list (inline in embed generation)
- [x] Calculate time of day from check number (handled in wind timeline)

**Status:** All helper functions implemented

### Step 6: Integration ✅ COMPLETED
- [x] Register command in `main.py` (`setup_weather(bot)`)
- [x] Add season choices to slash command (Spring/Summer/Autumn/Winter)
- [x] Add province choices to slash command (15 provinces: Reikland, Nordland, Ostland, Middenland, Hochland, Talabecland, Ostermark, Stirland, Sylvania, Wissenland, Averland, Solland, Kislev, Wasteland, Border Princes)
- [x] Handle notification channel (gets #boat-travelling-notifications by name, sends embed)

**Status:** Command fully integrated into bot with all province choices, registered and ready to use

### Step 7: Testing ✅ COMPLETED
- [x] **Write unit tests for weather_data.py** (19 tests)
  - Test wind strength/direction dictionaries
  - Test wind modifier completeness (all 15 combinations)
  - Test weather ranges coverage (1-100 for all seasons)
  - Test province temperature data (15 provinces × 4 seasons)
  - Test temperature ranges and lookup functions
  - Test data integrity (no duplicates, valid strings)
- [x] **Write unit tests for weather_mechanics.py** (32 tests)
  - Test wind generation and change mechanics
  - Test wind change boundaries (Calm → Light, Very Strong → Strong)
  - Test daily wind timeline generation (4 periods)
  - Test weather condition rolls for all seasons
  - Test temperature calculations and wind chill
  - Test probabilistic behavior (10% wind changes, correct distributions)
  - Test edge cases and consistency
- [x] **All existing tests still passing** (139 tests from other modules)

**Status:** ✅ **51 weather tests created and passing** + 139 existing tests = **190 total tests passing**

## File Structure ✅ COMPLETED
```
db/
  weather_data.py          # Weather tables and data (304 lines) ✅

utils/
  weather_mechanics.py     # Weather generation logic (250 lines) ✅

commands/
  weather.py               # Weather command implementation (328 lines) ✅

tests/
  test_weather_data.py     # Data validation tests (19 tests) ✅
  test_weather_mechanics.py # Mechanics logic tests (32 tests) ✅
```

## Implementation Summary

### ✅ Completed Features:

1. **Wind System** - Full implementation with:
   - 5 strength levels (Calm → Very Strong)
   - 3 directions (Tailwind, Sidewind, Headwind)
   - Probabilistic changes (10% per check, 4 checks per day)
   - Movement modifiers (-25% to +25%)
   - Special mechanical notes (tacking, tests, penalties)
   - Wind change indicators (🔄 emoji shows when wind changes)

2. **Weather Conditions** - Seasonal variation with:
   - 6 weather types (Dry, Fair, Rain, Downpour, Snow, Blizzard)
   - Season-specific probability tables
   - Mechanical effects (visibility, penalties, tests)
   - Rich descriptions
   - Weather-appropriate emojis

3. **Temperature System** - Full implementation with:
   - 15 provinces with season-specific averages
   - Temperature variation (±15°C from average)
   - Wind chill effects (-5°C or -10°C)
   - Special events (Cold Front, Heat Wave)
   - Descriptive text generation
   - Temperature emojis based on actual temp

4. **Discord Integration** - Complete with:
   - Slash command with season choices (4 options)
   - Slash command with province choices (15 options)
   - Prefix command support
   - Beautiful embeds with emojis and formatting
   - Notification channel posting to #boat-travelling-notifications
   - Comprehensive error handling
   - Separate mechanics embed for notifications

### 📊 Statistics:
- **Total Lines of Code:** 882 lines (304 + 250 + 328)
- **Test Lines of Code:** 520+ lines (test_weather_data.py + test_weather_mechanics.py)
- **Functions Created:** 15+ functions across all modules
- **Data Tables:** 7 major tables (wind modifiers, weather ranges, temperature ranges, province temps, etc.)
- **Provinces Supported:** 15 with accurate seasonal temperatures
- **Test Coverage:** ✅ **51 weather tests + 139 existing tests = 190 total tests passing**
- **Province Choices:** All 15 provinces available as dropdown choices in Discord

### 🎮 Ready to Use:
```
/weather spring                  # Reikland (default)
/weather summer reikland         # Explicit province
/weather winter talabecland      # Different province
/weather autumn kislev           # Cold province
```

Users can now select from dropdown menus for both season and province in Discord!

The command is fully functional and integrated into the bot!

## Notes
- Wind is the only weather element with direct boat handling mechanics
- Other weather provides flavor and situational modifiers
- Temperature is descriptive with wind chill consideration
- Notification channel message keeps game mechanics visible
- Command should be usable multiple times per day (different stages)
- Wind changes are probabilistic (10% per check period)

## Future Enhancements (Out of Scope)
- Track weather across multiple days
- Weather persistence/storage
- Custom provinces
- Extreme weather events
- Integration with boat handling command for automatic modifiers
