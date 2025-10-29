# Bot Commands Documentation

This document provides a comprehensive guide to all available commands in the Travelling Bot for Warhammer Fantasy Roleplay (WFRP).

## Table of Contents

- [Command Architecture](#command-architecture)
- [Available Commands](#available-commands)
  - [Hello Command](#hello-command)
  - [Roll Command](#roll-command)
  - [Boat-Handling Command](#boat-handling-command)
  - [Weather Command](#weather-command)
- [Supporting Systems](#supporting-systems)

---

## Command Architecture

### Command Registration System

Commands are organized in a modular architecture with the following structure:

```
travelling-bot/
├── main.py                      # Command registration hub
├── commands/                    # Command modules
│   ├── roll.py                  # Dice rolling
│   ├── boat_handling.py         # Boat navigation
│   └── weather.py               # Weather management
├── db/                          # Data storage
├── utils/                       # Utility functions
└── tests/                       # Test suite
```

### Dual Command Support

All commands support both **slash commands** (`/command`) and **prefix commands** (`!command`):

- **Slash Commands**: Modern Discord interaction model with autocomplete and validation
- **Prefix Commands**: Traditional text-based commands for backwards compatibility

### Design Pattern

Each command follows a standardized pattern:

```python
def setup(bot: commands.Bot):
    # Slash command handler
    @bot.tree.command(name="...", description="...")
    async def command_slash(interaction: discord.Interaction, ...):
        await _perform_action(interaction, ..., is_slash=True)

    # Prefix command handler
    @bot.command(name="...")
    async def command_prefix(ctx, ...):
        await _perform_action(ctx, ..., is_slash=False)

    # Shared implementation
    async def _perform_action(context, ..., is_slash: bool):
        # Unified logic for both command types
        pass
```

---

## Available Commands

### Hello Command

**Description:** A simple greeting command to test bot connectivity.

**Location:** [main.py](travelling-bot/main.py#L63-L76)

**Usage:**
```
/hello
```

**Example:**
```
User: /hello
Bot: Hello @User! 🚢 I am your WFRP traveling companion.
```

**Features:**
- Mentions the user who invoked the command
- Confirms bot is online and responsive
- Available in both slash and prefix formats

---

### Roll Command

**Description:** Flexible dice rolling system supporting standard dice notation and WFRP-specific skill checks.

**Location:** [commands/roll.py](travelling-bot/commands/roll.py)

**Usage:**
```
/roll <dice_notation> [target] [modifier]
```

**Parameters:**
- `dice_notation` (required): Dice to roll (e.g., `1d100`, `2d6+5`, `3d10-2`)
- `target` (optional): Target number for WFRP skill check
- `modifier` (optional): Difficulty modifier (e.g., `-20` for Hard, `+20` for Easy)

**Supported Dice Notation:**
- Standard dice: `1d100`, `2d6`, `3d10`, etc.
- Modifiers: `2d6+5`, `1d20-3`
- Multiple dice types: `1d6+1d8+5`

**WFRP Difficulty Modifiers:**
| Difficulty | Modifier |
|------------|----------|
| Very Easy | +60 |
| Easy | +40 |
| Average | +20 |
| Challenging | +0 |
| Difficult | -10 |
| Hard | -20 |
| Very Hard | -30 |

**Examples:**

**Basic Dice Roll:**
```
/roll 1d100
Result: Rolled 1d100: 47
```

**Multiple Dice:**
```
/roll 3d6+5
Result: Rolled 3d6+5: [4, 2, 6] + 5 = 17
```

**WFRP Skill Check:**
```
/roll 1d100 45 -20
Result:
Rolled 1d100: 67
Target (45 - 20): 25
Result: Failure
Success Levels: -4
```

**Critical/Fumble Detection:**
```
/roll 1d100 50 0
Result (if doubles rolled):
Rolled 1d100: 33
Target: 50
Result: Success ⚡ CRITICAL SUCCESS! (doubles)
Success Levels: +1
```

**Features:**
- Automatic WFRP doubles detection (00-99)
- Success Level (SL) calculation
- Clear formatting with Discord embeds
- Support for complex dice expressions
- Error handling for invalid notation

---

### Boat-Handling Command

**Description:** Character-based boat navigation skill checks with weather, time-of-day, and environmental modifiers.

**Location:** [commands/boat_handling.py](travelling-bot/commands/boat_handling.py)

**Usage:**
```
/boat-handling <character> [difficulty] [time_of_day]
```

**Parameters:**
- `character` (required): Character name
  - Options: `anara`, `emmerich`, `hildric`, `oktavian`, `lupus`
- `difficulty` (optional): Test difficulty modifier (default: `0` Challenging)
- `time_of_day` (optional): Time period affecting wind conditions
  - Options: `dawn`, `midday`, `dusk`, `midnight`
  - Default: `midday`

**Available Characters:**

| Character | Row Skill | Sail Skill | Lore (Rivers) |
|-----------|-----------|------------|---------------|
| Anara | 41 | 31 | 40 |
| Emmerich | 38 | 42 | 36 |
| Hildric | 30 | 25 | 0 |
| Oktavian | 25 | 30 | 35 |
| Lupus | 0 | 0 | 0 |

**Skill Selection Logic:**
1. If only rowing possible (wind conditions prevent sailing): Use Row
2. If both available: Use highest skill value
3. Automatic Lore (Rivers) bonus if higher than selected skill

**Examples:**

**Basic Test:**
```
/boat-handling anara
Result:
Character: Anara
Skill Used: Row (41)
Difficulty: +0 (Challenging)
Weather Modifier: -10 (Strong Wind)
Final Target: 31
Roll: 28
Result: Success
Success Levels: +0
Outcome: Marginal Success - You maintain course but progress is slow
```

**With Difficulty Modifier:**
```
/boat-handling emmerich -20
Result:
Character: Emmerich
Skill Used: Sail (42)
Difficulty: -20 (Hard)
Weather Modifier: -10 (Strong Wind)
Final Target: 12
Roll: 45
Result: Failure
Success Levels: -3
Outcome: Failure - The boat veers off course. The party loses 1 hour of travel time.
```

**Time-of-Day Effects:**
```
/boat-handling hildric 0 dawn
Result:
Time of Day: Dawn
Wind Conditions: Light Breeze (may affect sailing viability)
[Rest of test resolution...]
```

**Success Level Outcomes:**

| Success Levels | Category | Mechanical Effect |
|----------------|----------|-------------------|
| +6 or more | Astounding Success | +2 hours progress, no fatigue |
| +4 to +5 | Impressive Success | +1 hour progress |
| +2 to +3 | Success | Normal progress, smooth sailing |
| +0 to +1 | Marginal Success | Maintain course, slow progress |
| -1 to 0 | Marginal Failure | Minor setback, -30 minutes |
| -2 to -3 | Failure | Veer off course, lose 1 hour |
| -4 to -5 | Impressive Failure | Lost badly, -2 hours, 1 fatigue |
| -6 or less | Astounding Failure | Crisis! -3 hours, 2 fatigue, potential damage |

**Weather Integration:**
- Automatically applies current weather modifiers from active journey
- Wind strength affects sailing viability
- Temperature extremes may cause additional penalties
- Weather effects displayed in test results

**Features:**
- Character skill database integration
- Intelligent skill selection (Row vs Sail vs Lore)
- Dynamic weather modifier application
- Time-of-day wind variation
- Narrative outcomes with mechanical consequences
- Critical/fumble detection on doubles
- Detailed embed formatting with character portraits

---

### Weather Command

**Description:** Comprehensive journey weather management system for multi-day river travel.

**Location:** [commands/weather.py](travelling-bot/commands/weather.py)

**Usage:**
```
/weather <action> [parameters...]
```

**Available Actions:**

#### 1. Next - Generate Next Day's Weather

**Usage:**
```
/weather next
```

**Description:** Advances the journey to the next day and generates weather conditions.

**Example:**
```
/weather next

Result:
Day 3 of Summer Journey in Reikland

🌡️ Temperature: 18°C (Fair)
💨 Wind Timeline:
  Dawn: Light Breeze (SW)
  Midday: Moderate Wind (SW) ⬅️ You are here
  Dusk: Moderate Wind (SW)
  Midnight: Strong Wind (W)

☁️ Condition: Fair Weather
No special weather events.

🎲 Impact on Tests:
- Boat Handling: -10 (Moderate Wind)
- Outdoor Tests: No modifier
```

**Features:**
- Sequential day progression
- Dynamic wind changes (10% chance at each time period transition)
- Temperature calculations with seasonal variation
- Weather condition generation (dry, fair, rain, downpour, snow, blizzard)
- Cold front/heat wave tracking
- Wind chill effects
- Automatic notification to `boat-travelling-notifications` channel

#### 2. Journey - Start New Journey

**Usage:**
```
/weather journey <season> <province>
```

**Parameters:**
- `season` (required): `spring`, `summer`, `autumn`, `winter`
- `province` (required): One of 15 provinces

**Available Provinces:**
- Reikland
- Nordland
- Ostland
- Middenland
- Hochland
- Talabecland
- Ostermark
- Stirland
- Sylvania
- Wissenland
- Averland
- Solland
- Kislev
- Wasteland
- Border Princes

**Example:**
```
/weather journey summer reikland

Result:
Journey Started!
Season: Summer
Province: Reikland

Day 1 Weather:
[Weather details for day 1...]

Use /weather next to advance to the next day.
```

**Features:**
- Initializes journey state
- Generates day 1 weather
- Stores journey parameters for continuity
- Validates season and province inputs

#### 3. View - Display Specific Day's Weather

**Usage:**
```
/weather view <day_number>
```

**Example:**
```
/weather view 3

Result:
Day 3 of Summer Journey in Reikland
[Full weather details for day 3...]
```

**Features:**
- Retrieves historical weather data
- Maintains wind timeline accuracy
- Shows current time period marker

#### 4. End - Conclude Journey

**Usage:**
```
/weather end
```

**Example:**
```
/weather end

Result:
Journey Ended!
Total Duration: 5 days
Season: Summer
Province: Reikland

Safe travels!
```

**Features:**
- Clears journey state
- Provides journey summary
- Frees up for new journey

#### 5. Override - GM Weather Control

**Usage:**
```
/weather override <season> <province>
```

**Example:**
```
/weather override winter kislev

Result:
Weather Override Applied!
Current conditions set to:
Season: Winter
Province: Kislev

The weather has been manually adjusted by the GM.
```

**Features:**
- GM tool for narrative control
- Changes current day's weather
- Maintains journey continuity
- Can be used mid-journey

**Weather System Details:**

**Wind Strength Levels:**
| Level | Description | Boat Handling Modifier |
|-------|-------------|------------------------|
| 0 | Calm | +10 |
| 1 | Light Breeze | +0 |
| 2 | Moderate Wind | -10 |
| 3 | Strong Wind | -20 |
| 4 | Gale | -30 (sailing impossible) |

**Wind Directions:**
- North (N), Northeast (NE), East (E), Southeast (SE)
- South (S), Southwest (SW), West (W), Northwest (NW)

**Weather Conditions:**
| Condition | Temperature Range | Visibility | Effects |
|-----------|-------------------|------------|---------|
| Dry | High | Excellent | +10 outdoor perception |
| Fair | Normal | Good | No modifiers |
| Rain | Normal | Reduced | -10 ranged attacks |
| Downpour | Low | Poor | -20 ranged, -10 perception |
| Snow | Cold | Reduced | -10 movement |
| Blizzard | Very Cold | Minimal | -20 all tests, -30 perception |

**Temperature Effects:**

**Wind Chill Calculation:**
```
Apparent Temperature = Base Temperature - (Wind Strength × 2)

Example:
Base: 5°C, Strong Wind (3) → 5 - (3 × 2) = -1°C apparent
```

**Cold/Heat Events:**
- Cold Front: -5°C for 1d3 days
- Heat Wave: +5°C for 1d3 days
- Tracked across journey continuity

**Time Period Transitions:**
- Dawn → Midday (6 hours)
- Midday → Dusk (6 hours)
- Dusk → Midnight (6 hours)
- Midnight → Dawn (6 hours, advances to next day)

**Features:**
- Persistent journey state across bot restarts
- Multi-day continuity tracking
- Dynamic weather progression
- Regional seasonal variation
- Automatic mechanics notifications
- Rich embed formatting
- Historical weather access
- GM override capabilities

---

## Supporting Systems

### Character Database

**Location:** [db/character_data.py](travelling-bot/db/character_data.py)

**Stored Data:**
- Character names
- River Travelling Skills (Row, Sail)
- Lore (Rivers) skill values
- Character portrait URLs (for embeds)

**Characters:**
1. **Anara** - Balanced skills, high Row (41)
2. **Emmerich** - Best Sail (42), solid all-around
3. **Hildric** - Moderate skills, no Lore
4. **Oktavian** - Balanced with good Lore (35)
5. **Lupus** - Unskilled (all 0s)

### Weather Storage

**Location:** [db/weather_storage.py](travelling-bot/db/weather_storage.py)

**Functionality:**
- Persistent journey state
- Daily weather caching
- Multi-day continuity
- Journey metadata storage

**Stored Per Journey:**
- Season and province
- Current day number
- Daily weather records:
  - Wind timeline (4 periods)
  - Temperature
  - Weather condition
  - Special events (cold fronts, heat waves)
  - Wind chill effects

### WFRP Mechanics Utilities

**Location:** [utils/wfrp_mechanics.py](travelling-bot/utils/wfrp_mechanics.py)

**Functions:**
- `parse_dice_notation()` - Parse dice strings
- `roll_dice()` - Generate random rolls
- `check_wfrp_doubles()` - Critical/fumble detection on d100 doubles

**WFRP Rules Implemented:**
- Success Level calculation: `(Target - Roll) / 10` rounded down
- Doubles detection: Both digits match (00, 11, 22, ..., 99)
- Critical Success: Doubles when successful
- Fumble: Doubles when failed

### Weather Mechanics Utilities

**Location:** [utils/weather_mechanics.py](travelling-bot/utils/weather_mechanics.py)

**Functions:**
- `generate_daily_wind()` - Create 4-period wind timeline
- `roll_weather_condition()` - Generate weather type
- `roll_temperature_with_special_events()` - Temperature + events
- `apply_wind_chill()` - Adjust temperatures for wind

**Weather Generation:**
- Seasonal base temperatures
- Provincial climate variation
- Random weather table rolls
- Wind direction and strength randomization
- Event tracking (cold fronts, heat waves)

### Modifier Calculator

**Location:** [utils/modifier_calculator.py](travelling-bot/utils/modifier_calculator.py)

**Functions:**
- `get_active_weather_modifiers()` - Calculate weather penalties
- `format_weather_impact_for_embed()` - Format for display

**Modifier Sources:**
1. Wind strength (sailing/rowing penalties)
2. Weather condition (visibility, ranged attacks)
3. Temperature extremes (fatigue, exposure)
4. Time of day (perception, navigation)

**Example Calculation:**
```
Moderate Wind (-10) + Rain (-10) + Cold (-5) = -25 total modifier
```

---

## Command Flow Examples

### Example 1: Starting a Journey

```
User: /weather journey summer reikland
Bot: [Day 1 weather generated]

User: /boat-handling anara
Bot: [Boat handling test with day 1 weather modifiers]

User: /weather next
Bot: [Day 2 weather generated]

User: /boat-handling emmerich -10
Bot: [Boat handling test with day 2 weather modifiers and difficulty]

User: /weather view 1
Bot: [Display day 1 weather again for reference]

User: /weather end
Bot: [Journey concluded, 2 days total]
```

### Example 2: Combat with Weather

```
User: /weather journey winter kislev
Bot: [Day 1 - Blizzard conditions, -10°C]

User: /roll 1d100 40 -20
Bot: [Attack roll with -20 from blizzard visibility]

User: /weather override spring reikland
Bot: [GM changes weather for narrative reasons]

User: /roll 1d100 40 0
Bot: [Attack roll now with fair conditions]
```

### Example 3: Skill Progression

```
User: /boat-handling lupus
Bot: [All skills 0, automatic failure likely]

User: /boat-handling anara
Bot: [Experienced sailor, better chances]

User: /boat-handling emmerich 0 dusk
Bot: [Evening sailing with weather modifiers]
```

---

## Error Handling

All commands include comprehensive error handling:

**Invalid Parameters:**
```
User: /roll abc
Bot: ❌ Invalid dice notation: abc
```

**No Active Journey:**
```
User: /weather next
Bot: ❌ No active journey. Use /weather journey <season> <province> to start.
```

**Invalid Character:**
```
User: /boat-handling nobody
Bot: ❌ Character 'nobody' not found in database.
```

**Out of Range:**
```
User: /weather view 999
Bot: ❌ Day 999 not found in journey records.
```

---

## Best Practices

1. **Start Journey Before Tests:** Use `/weather journey` before `/boat-handling` to ensure weather modifiers apply
2. **Check Weather Regularly:** Use `/weather view` to reference current conditions during tests
3. **Use Appropriate Difficulty:** Apply difficulty modifiers based on narrative circumstances
4. **Consider Time of Day:** Dawn/dusk/midnight can significantly affect wind conditions
5. **Track Multi-Day Journeys:** Use `/weather next` daily to maintain continuity
6. **GM Override Sparingly:** Use `/weather override` for special narrative moments, not routine adjustments

---

## Technical Notes

- **Discord.py Version:** 2.0+
- **Command Sync:** Slash commands require one-time sync with Discord API
- **Persistence:** Weather data stored in local database (survives bot restarts)
- **Notifications:** Mechanical updates sent to `boat-travelling-notifications` channel
- **Embeds:** All responses use Discord rich embeds for formatting
- **Error Recovery:** All commands fail gracefully with user-friendly messages

---

## Future Enhancements

Potential additions based on current architecture:

- [ ] Multi-party support (separate journeys per channel)
- [ ] Random encounter integration with weather
- [ ] Fatigue tracking system
- [ ] Boat damage/repair mechanics
- [ ] Cargo weight affecting boat handling
- [ ] River current effects on travel time
- [ ] Character experience/advancement tracking
- [ ] Custom character creation
- [ ] Weather forecasting (Lore skill check)
- [ ] Storm event mechanics

---

## Support & Contact

For issues, feature requests, or questions about command usage, contact the bot administrator or consult the WFRP rulebook for mechanical interpretations.

**Version:** 1.0
**Last Updated:** 2025-10-29
**WFRP Edition:** 4th Edition
