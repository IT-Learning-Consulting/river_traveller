# Travelling-Bot Codebase Context

## Overview
A Discord bot for Warhammer Fantasy Roleplay (WFRP) 4th Edition river traveling assistance. The bot handles dice rolling, boat navigation tests, weather generation, river encounters, and journey management with WFRP-specific mechanics.

---

## 1. Entry Point

### [main.py](main.py)
**Purpose:** Bot initialization and command registration

**Overview:**
This is the entry point for the entire Discord bot application. It serves as the orchestrator that brings together all the modular command systems and handles the bot's lifecycle from startup to shutdown. The file is intentionally kept minimal, delegating all complex logic to specialized modules, which makes the codebase maintainable and testable. It implements both the Discord bot using discord.py and a Flask keep-alive server for cloud hosting compatibility (specifically for Render.com's free tier which requires an HTTP endpoint).

The bot uses Discord's modern slash command system (application commands) while maintaining backward compatibility with traditional prefix commands (!command). This dual-command system ensures users can interact with the bot through Discord's native command interface while also supporting legacy text-based commands. The initialization sequence is carefully ordered: environment variables are loaded first, then the Discord client is configured with proper intents, logging is set up, all command modules are registered, and finally the keep-alive server is started before the bot connects to Discord.

**Key Responsibilities:**
- Initializes Discord bot with intents and logging
- Registers all command modules via their `setup()` functions
- Handles bot lifecycle events (`on_ready`, `on_message`)
- Starts Flask keep-alive server for hosting (Render deployment)
- Contains only `/hello` command directly (all others modularized)

**Command Registration:**
```python
setup_roll(bot)              # Dice rolling
setup_boat_handling(bot)     # Navigation tests
setup_weather(bot)           # Weather management
setup_river_encounter(bot)   # Random encounters
setup_help(bot)              # Help system
```

**Dependencies:**
- Uses `server.py` for keep-alive functionality
- Loads `.env` for Discord token

---

## 2. Commands Directory (`/commands`)

### Overview
All bot commands are modularized here. Each command has both slash (/) and prefix (!) versions.

### 2.1 [commands/roll.py](commands/roll.py)
**Purpose:** Dice rolling with WFRP mechanics

**Overview:**
This module implements the core dice rolling functionality that underpins all probability-based mechanics in the bot. It handles everything from simple dice notation (like "3d6") to complex WFRP 4th Edition skill tests with difficulty modifiers. The implementation is carefully designed to match the official WFRP rules, including special edge cases like treating a roll of 1 as a low double (01) and roll of 100 as an automatic fumble regardless of skill level. This is critical for maintaining game balance and authenticity.

The module serves as a general-purpose dice roller but excels at WFRP skill tests, which are central to the game system. When performing a skill test, it calculates Success Levels (SL) by comparing the tens digits of the roll versus the target number, detects doubles for critical successes and fumbles, and provides narrative feedback appropriate to the outcome. The dice rolling logic is separated into the utils.wfrp_mechanics module for testability, while this file focuses on Discord interaction and presentation.

**Features:**
- Flexible dice notation: `XdY`, `XdY+Z`, `XdY-Z`
- WFRP skill tests with target and difficulty modifiers
- Success Level (SL) calculation
- Doubles detection (11, 22, 33, etc.) for crits/fumbles
- Special handling: Roll of 1 = low double (01), 100 = always fumble

**Dependencies:**
- `utils.wfrp_mechanics`: Core dice and success calculation
- Logs commands to `boat-travelling-log` channel

**Example Usage:**
```
/roll 1d100              # Simple d100 roll
/roll 1d100 45 20        # Roll against skill 45, Average difficulty (+20)
/roll 3d10               # Roll 3d10 dice
```

### 2.2 [commands/boat_handling.py](commands/boat_handling.py)
**Purpose:** WFRP Boat Handling Tests for river navigation

**Overview:**
This command implements one of the most frequently used mechanics in river-based campaigns: boat handling tests. In WFRP, navigating a river requires periodic skill checks, and this module automates the entire process including character selection, skill determination (Sail vs Row), bonus calculation from Navigation skills, and integration with the active weather system. The module knows about all five party members and their skills, automatically selecting the most appropriate skill (preferring Sail if available, otherwise Row) for each character.

The real power of this module comes from its deep integration with the weather system. Every boat handling test queries the current weather conditions and automatically applies modifiers from wind strength, wind direction, and adverse weather effects. This creates meaningful gameplay where weather conditions directly impact navigation difficulty - a strong headwind during a storm makes boat handling significantly more challenging than calm weather with a tailwind. The module provides rich narrative feedback based on success levels, from masterful navigation to catastrophic failures, making the mechanical results feel cinematic and engaging.

The character system is hardcoded with five predefined party members (Anara, Emmerich, Hildric, Oktavian, Lupus), each with unique skill distributions. The Lore (Riverways) skill provides a bonus equal to its first digit (e.g., 47 in Lore gives +4), representing the character's knowledge of river currents, hazards, and navigation tricks. This encourages specialization and makes certain characters naturally better at specific times of day or conditions.

**Features:**
- Tests for all party characters (5 predefined)
- Automatically selects Sail or Row skill
- Applies Lore (Riverways) bonus (first digit of skill)
- Integrates weather modifiers from active journey
- Difficulty scaling with descriptive outcomes
- Success/failure with narrative flavor text

**Weather Integration:**
- Queries `get_active_weather_modifiers()` for current conditions
- Applies boat handling penalties from wind/weather
- Shows both base and weather-modified difficulty

**Character System:**
- Uses `db.character_data` for character stats
- Each character has different Sail/Row/Navigation skills
- Chooses Sail if available, otherwise Row

**Dependencies:**
- `db.character_data`: Character lookup
- `utils.wfrp_mechanics`: Doubles detection, dice rolling
- `utils.modifier_calculator`: Weather modifier extraction
- Logs to `boat-travelling-log` channel

### 2.3 [commands/weather.py](commands/weather.py)
**Purpose:** Weather command interface (delegates to handler)

**Overview:**
This file serves as a thin interface layer between Discord's command system and the complex weather generation logic. It's intentionally kept minimal, acting as a router that validates permissions, parses user input, and delegates all business logic to the WeatherCommandHandler class. This separation of concerns makes the codebase more maintainable - Discord-specific code (interaction handling, permission checking, embed formatting) is isolated from the core weather mechanics, which are tested independently.

The command supports multiple actions that cover the entire journey lifecycle: starting journeys with specific seasons and provinces, generating single-day weather, progressing through multi-day stages, viewing historical weather data, ending journeys, and GM overrides for manual control. The stage-based system is particularly important for campaigns where river travel takes weeks - instead of rolling weather day-by-day, GMs can generate a week's worth of weather at once and reference it as needed during gameplay.

**Features:**
- Daily progression: `/weather next`
- Multi-day progression: `/weather next-stage`
- Journey management: start, view, end
- GM-only override for manual weather control
- Stage configuration: `/weather-stage-config`

**Actions:**
- `next`: Generate next day's weather
- `next-stage`: Generate multiple days (stage-based travel)
- `journey`: Start new journey with season/province
- `view`: View specific day's weather
- `end`: End current journey
- `override`: [GM only] Manually set weather

**GM Permissions:**
- Server owner or users with "GM" role
- Can override weather and configure stages

**Dependencies:**
- `commands.weather_modules.handler.WeatherCommandHandler`: All business logic
- Delegates all functionality to handler module

### 2.4 [commands/river_encounter.py](commands/river_encounter.py)
**Purpose:** Random river encounter generation with dual-message system

**Overview:**
This module implements a sophisticated random encounter system designed specifically for river travel campaigns. Unlike traditional encounter systems that simply announce "you meet a monster," this system uses a dual-message approach that separates player experience from GM information. Players receive atmospheric, cryptic messages that build tension and require interpretation, while GMs simultaneously receive detailed mechanical information in a private channel. This creates an information asymmetry that encourages roleplay and investigation rather than immediate mechanical responses.

The encounter system is probability-weighted across five categories, ranging from positive events (beneficial winds, helpful NPCs) through coincidental observations (wildlife sightings, landmarks) to harmful situations (debris, delays) and catastrophic accidents (hull damage, cargo loss). The d100 probability distribution is carefully balanced to make uneventful travel the most common outcome (41-75%), with dangerous encounters being rare but memorable. This matches the typical WFRP experience where most travel is mundane but punctuated by dramatic moments.

The integration with the stage-based journey system allows GMs to pre-generate encounters for an entire week of travel, making session prep more efficient. GMs can also override the random roll to force specific encounter types for narrative purposes, making this system flexible enough for both sandbox and story-driven campaigns.

**Features:**
- 5 encounter types with probabilities
- Dual-message system: cryptic player messages + detailed GM notifications
- GM override to force specific encounter types
- Integrates with stages/days for journey tracking

**Encounter Types (d100):**
1. **Positive (1-10):** Beneficial events (tailwinds, NPCs, shortcuts)
2. **Coincidental (11-40):** Neutral observations (wildlife, landmarks)
3. **Uneventful (41-75):** Nothing of note
4. **Harmful (76-90):** Minor problems (debris, delays)
5. **Accident (91-100):** Major incidents (damage, cargo loss)

**Message System:**
- **Players (public):** Atmospheric flavor text only, no mechanics
- **GMs (#boat-travelling-notifications):** Full details with tests, damage, effects

**Dependencies:**
- `utils.encounter_mechanics`: Encounter generation and formatting
- `db.encounter_data`: Encounter tables
- Logs to `boat-travelling-log` channel

### 2.5 [commands/help.py](commands/help.py)
**Purpose:** Comprehensive help system

**Overview:**
The help system is more than just a command reference - it's an in-Discord manual that explains both how to use the bot and the underlying WFRP rules. This is critical because WFRP has complex mechanics (Success Levels, doubles, difficulty modifiers) that aren't intuitive to new players. The help system provides context-sensitive information, allowing users to get general overviews or drill down into specific commands with detailed examples.

The module is structured hierarchically with a general help overview listing all commands, and detailed help for each command that includes syntax, examples, and rule explanations. For instance, the boat handling help doesn't just say "roll a boat test" - it explains which characters have which skills, how Lore bonuses work, when to use different times of day, and how weather affects tests. This educational approach reduces the learning curve and empowers players to use the bot effectively without constantly asking the GM for clarification.

**Features:**
- General overview of all commands
- Detailed help per command with examples
- WFRP rules explanations
- GM feature documentation

**Help Topics:**
- `roll`: Dice notation, WFRP skill tests, doubles
- `boat-handling`: Characters, difficulty, time of day
- `weather`: Daily/stage progression, seasons, provinces
- `river-encounter`: Encounter types, dual-message system

### 2.6 Commands Weather Modules (`/commands/weather_modules`)

This subdirectory contains refactored weather system components:

#### [handler.py](commands/weather_modules/handler.py)
**Purpose:** Main weather command handler (business logic)

**Overview:**
This is the brain of the weather system, containing all the complex business logic for weather generation, journey management, and state tracking. The handler acts as an orchestrator that coordinates between the database layer (weather_storage), the mechanics layer (weather_mechanics), and the presentation layer (display, stages, notifications). It's responsible for maintaining data consistency, managing the lifecycle of weather events (cold fronts, heat waves), and ensuring that cooldown periods are properly tracked across days and stages.

The handler implements a sophisticated state machine for weather events. When a cold front triggers, the handler resets the cooldown counter, tracks the event across multiple days, applies daily temperature variations, and begins incrementing the cooldown counter once the event ends. This ensures events feel realistic (multi-day duration, gradual temperature changes) while preventing unrealistic back-to-back occurrences through the 7-day cooldown system. The handler also enforces mutual exclusivity - a cold front and heat wave can never occur simultaneously, preventing conflicting temperature modifiers.

The stage-based generation system is particularly complex, as it must generate consistent weather across multiple days while properly handling events that span day boundaries. If a cold front starts on day 2 of a 5-day stage and lasts 3 days, the handler ensures the event continues through day 4 and then ends, with cooldown tracking properly maintained across the entire stage. This requires careful state management and is thoroughly tested in the integration test suite.

**Key Methods:**
- `handle_command()`: Routes weather actions
- `configure_stage()`: Manages stage settings
- `_generate_next_day()`: Daily weather generation with event tracking
- `_generate_next_stage()`: Multi-day stage generation
- `_handle_journey_start()`: Initialize new journey
- `_handle_override()`: GM manual weather control
- **NEW:** `_generate_daily_weather()`: Core weather generation with cooldown integration
- **NEW:** `_update_cooldown_trackers()`: Manages cooldown state machine

**Weather Generation Flow:**
1. Extract state from previous day (cold_front_total, heat_wave_total)
2. Get cooldown status from journey state
3. Pass 8 parameters to `roll_temperature_with_special_events()`:
   - season, province
   - cold_front_days, cold_front_total
   - heat_wave_days, heat_wave_total
   - days_since_last_cold_front, days_since_last_heat_wave
4. Unpack 8 return values:
   - actual_temp, temp_category, temp_description, temp_roll
   - cold_front_remaining, cold_front_total_new
   - heat_wave_remaining, heat_wave_total_new
5. Update cooldown trackers (state machine)
6. Save new fields to database

**Cooldown State Machine:**
- **Event starts:** `reset_cooldown()` → 0
- **Event active:** Keep cooldown at 0
- **Event ends:** `increment_cooldown()` → 1, 2, 3...
- **No event:** Continue incrementing daily

**Dependencies:**
- Uses `weather_storage`, `weather_mechanics`, `display`, `stages`, `notifications`

#### [display.py](commands/weather_modules/display.py)
**Purpose:** Format weather data for Discord embeds

**Overview:**
This module is responsible for transforming raw weather data (temperatures, wind speeds, weather types) into beautifully formatted Discord embeds that players actually want to read. It uses Discord's embed system with colors, emojis, and structured fields to present complex weather information in a scannable, visually appealing format. The module makes heavy use of the formatters utilities to ensure consistent presentation across all weather displays.

The display system supports multiple presentation modes: simple daily weather for quick reference, detailed stage summaries that show a week's worth of weather in one message, and condensed formats for stage overviews. Each format is optimized for its use case - daily weather includes full wind timelines for all four time periods (dawn, midday, dusk, midnight), while stage summaries condense this into highlights. The module also handles special event formatting, ensuring cold fronts and heat waves are prominently displayed with day counters and modifiers.

**Key Functions:**
- `format_weather_embed()`: Daily weather display
- `format_stage_summary_embed()`: Simple stage overview
- `format_stage_detailed_embed()`: Detailed stage breakdown

#### [formatters.py](commands/weather_modules/formatters.py)
**Purpose:** Small formatting utilities

**Overview:**
This is a collection of pure, stateless formatting functions that convert raw data into human-readable strings. These utilities are used throughout the weather system to ensure consistent formatting - whether displaying temperature in stages.py, notifications.py, or display.py, the same formatting function is used. This prevents inconsistencies like showing "21°C" in one place and "21 degrees" in another, and makes it easy to change formatting globally by modifying a single function.

The formatters handle common tasks like converting wind directions to emojis (tailwind → ⬆️, headwind → ⬇️), formatting temperature ranges with appropriate emojis (❄️ for cold, 🔥 for hot), and creating condensed text for special events. These seem like small details, but consistent, polished formatting significantly improves the user experience and makes the bot feel professional rather than cobbled together.

**Functions:**
- Wind timeline formatting
- Temperature display
- Special event text

#### [notifications.py](commands/weather_modules/notifications.py)
**Purpose:** Send weather updates to log channels with GM notifications

**Features:**
- Sends to `boat-travelling-log` channel
- Different formats for daily vs. stage weather
- **NEW:** Special events section in GM notifications

**GM Notification Enhancements:**
- Dedicated "🌨️ Special Weather Events" field for active events
- Shows event progress: "Cold Front: Day 2 of 3"
- Displays temperature modifier: "-10°C" or "+10°C"
- **NEW:** Flavor text on day 1 of cold front: "Sky filled with flocks of emigrating birds"
- **NEW:** "(Final Day)" marker when event ends

**Example Special Events Field:**
```
❄️ Cold Front: Day 2 of 3
• Temperature modifier: -10°C
• (Final Day)
```

#### [stages.py](commands/weather_modules/stages.py)
**Purpose:** Multi-day stage generation and display logic

**Overview:**
This module implements the stage-based weather system, which is essential for campaigns where river travel takes weeks or months. Instead of forcing GMs to generate weather one day at a time during sessions (which breaks immersion), they can pre-generate a week's worth of weather and reference it as needed. The module handles all the complexity of generating consistent weather across multiple days, including events that span multiple days and cooldown tracking that persists across stage boundaries.

The stage generation logic is more sophisticated than simply calling the daily weather generator multiple times. It must track state across days - if a cold front starts on day 2 and lasts 4 days, the module ensures the event continues through day 5, updates the cooldown counter appropriately, and prevents new cold fronts from triggering during the cooldown period. The module also handles the recent enhancement to display day counters ("Cold Front: Day 2 of 4") and final day markers, making it easy for GMs to track event progression at a glance.

The `_format_day_summary()` function is particularly important as it creates condensed weather summaries for stage views. These summaries balance brevity with completeness - showing the essential information (weather type, temperature, wind, special events) without the full wind timeline and effect descriptions that daily weather displays include. This makes stage summaries scannable while still providing enough detail for gameplay decisions.

**Key Functions:**
- `generate_stage_weather()`: Create weather for multiple days
- Handles cold fronts/heat waves across stages
- Manages cooldown tracking
- **NEW:** `_format_day_summary()`: Formats day summaries with event counters

**Display Features:**
- Shows day counters for active events: "❄️ Cold Front (Day 2/3)"
- Adds "(Final Day)" marker when event ends
- Displays both cold fronts and heat waves if applicable
- Condensed format for stage overviews

**Example Output:**
```
☀️ **Fair** | 🌡️ 21°C
💨 Light Tailwind
❄️ Cold Front (Day 2/3)
```

---

## 3. Database Directory (`/db`)

### 3.1 [db/character_data.py](db/character_data.py)
**Purpose:** Character statistics and lookup

**Overview:**
This module defines the five player characters in the campaign as Python dictionaries containing their complete stat blocks. While it might seem odd to hardcode character data rather than storing it in a database, this approach has several advantages: it's version-controlled, easily readable, quickly accessible without database queries, and most importantly, these characters rarely change during gameplay (WFRP advancement happens slowly). The stat blocks include all WFRP characteristics (Weapon Skill, Ballistic Skill, Strength, etc.), trading skills (for negotiation), and river-specific skills (Row, Sail, Navigation).

Each character has a unique skill distribution that makes them better at different aspects of river travel. Anara, the High Elf, has exceptional Navigation and Perception, making her ideal for scouting and route planning. Emmerich has strong Sailing skills, making him better in sailboats. Hildric excels at Rowing, useful when wind is absent. This diversity encourages players to choose different characters for different situations rather than always using the "best" character, creating more varied gameplay and roleplay opportunities.

The module provides helper functions that abstract away the details of character data structure, allowing other modules to query "what boat handling skill does this character use?" without needing to understand the internal dictionary format. This encapsulation makes it easy to change the data structure later (e.g., moving to a database) without breaking calling code.

**Characters:**
1. **Anara of Sānxiá** - High Elf, skilled navigator
2. **Emmerich Falkenrath** - Human, Sail skill
3. **Hildric Sokhlundt** - Human, strong rower
4. **Oktavian Babel** - Human, versatile
5. **Lupus Leonard Joachim Rohrig** - Human, trader

**Data Structure:**
- Characteristics (WS, BS, S, T, I, AG, DEX, INT, WP, FEL)
- Trading skills (Haggle, Charm, Gossip, Bribery, Intuition, Evaluate)
- River travelling skills (Row, Sail, Navigation, Swim, Outdoor Survival, Perception, Dodge, Lore)

**Functions:**
- `get_character(key)`: Lookup character by name
- `get_available_characters()`: List all character keys
- `get_boat_handling_skill(char)`: Determine Sail vs Row
- `get_lore_riverways_bonus(char)`: Calculate Lore bonus

### 3.2 [db/weather_data.py](db/weather_data.py)
**Purpose:** WFRP weather tables and constants

**Overview:**
This module is essentially a Python representation of the weather tables from the WFRP rulebooks, adapted specifically for river travel. It contains extensive lookup tables that define how weather works in the WFRP world - what weather types occur in each season, how wind affects boat speed, what temperature ranges are expected in each province, and what mechanical effects different weather conditions impose. These tables are the foundation of the entire weather system, translating dice rolls into concrete game effects.

The data is organized hierarchically by game concepts: wind (strength and direction with their modifiers), weather types (dry, fair, rain, snow, etc. with seasonal probabilities), and temperature (base values per province/season plus variation tables). The wind modifier tables are particularly important for boat handling - they show exactly how much each wind condition affects travel speed and difficulty. A strong tailwind might give +25% speed and -10 to boat handling difficulty (making navigation easier), while a strong headwind gives -25% speed and +20 difficulty (much harder to navigate).

The province temperature data covers 15 distinct regions of the WFRP world, each with seasonal variations. Reikland (the heartland) has temperate weather, while Kislev (the frozen north) is much colder. This regional variation makes geography meaningful - traveling through Kislev in winter is genuinely more dangerous than summer in Reikland, and the weather system reflects this through different base temperatures and weather type probabilities. The module also includes the special event tables (cold fronts, heat waves) with their probabilities and effects.

**Data Tables:**
- **Wind Strength:** Calm, Light, Bracing, Strong, Very Strong
- **Wind Direction:** Tailwind, Sidewind, Headwind
- **Wind Modifiers:** Speed and penalty matrix for all combinations
- **Weather by Season:** Dry, Fair, Rain, Downpour, Snow, Blizzard
- **Weather Effects:** Descriptions and mechanical impacts
- **Province Temperatures:** Base temps for 15 provinces by season
- **Temperature Ranges:** d100 table with special events (cold fronts, heat waves)

**Functions:**
- `get_wind_strength_from_roll(d10)`
- `get_wind_direction_from_roll(d10)`
- `get_weather_from_roll(season, d100)`
- `get_temperature_category_from_roll(d100)`
- `get_province_base_temperature(province, season)`

### 3.3 [db/weather_storage.py](db/weather_storage.py)
**Purpose:** SQLite database for persistent weather tracking

**Database Schema:**

**Table: guild_weather_state**
- Tracks current journey per Discord guild
- Fields: guild_id, current_day, current_stage, stage_duration, stage_display_mode, season, province
- **NEW:** Cooldown tracking fields:
  - `days_since_last_cold_front`: Counter for cold front cooldown (default 99)
  - `days_since_last_heat_wave`: Counter for heat wave cooldown (default 99)

**Table: daily_weather**
- Stores weather for each day of journey
- Fields: guild_id, day_number, season, province, wind_timeline (JSON), weather_type, temperature, special events
- **NEW:** Event duration tracking fields:
  - `cold_front_days_remaining`: Countdown of remaining cold front days
  - `cold_front_total_duration`: Original rolled duration (1-5 days)
  - `heat_wave_days_remaining`: Countdown of remaining heat wave days
  - `heat_wave_total_duration`: Original rolled duration (11-20 days)

**Key Methods:**
- `start_journey()`: Initialize new journey
- `save_daily_weather()`: Store day's weather (includes new duration fields)
- `get_daily_weather()`: Retrieve specific day
- `advance_day()`: Increment day counter
- `advance_stage()`: Multi-day progression
- `get_journey_state()`: Current journey info
- `end_journey()`: Clear journey data
- **NEW:** Cooldown management:
  - `get_cooldown_status(guild_id)`: Returns (cold_front_days, heat_wave_days)
  - `increment_cooldown(guild_id, event_type)`: Increases cooldown counter by 1
  - `reset_cooldown(guild_id, event_type)`: Sets cooldown to 0 when event starts

**Migration Support:**
- Automatically adds new columns with DEFAULT values
- Handles existing databases gracefully
- Backfills active events with conservative estimates (remaining = total)

### 3.4 [db/encounter_data.py](db/encounter_data.py)
**Purpose:** River encounter tables with rich narrative content

**Overview:**
This module contains the extensive encounter tables that define what happens during river travel. Unlike simple random encounter tables that just list monsters, this system includes five categories of encounters (positive, coincidental, uneventful, harmful, accident) with dozens of specific events in each category. Each encounter includes both atmospheric flavor text for players and detailed mechanical information for GMs, supporting the dual-message system implemented in river_encounter.py.

The encounters are designed specifically for river travel rather than generic wilderness encounters. Positive encounters might include finding a helpful river guide or catching a favorable current. Coincidental encounters include wildlife sightings, passing merchant vessels, or notable landmarks. Harmful encounters involve river hazards like debris, sandbars, or aggressive wildlife. Accidents are catastrophic events like hull breaches, cargo loss, or character injuries that require immediate mechanical resolution (damage rolls, skill tests, etc.).

The probability distribution (positive 1-10, coincidental 11-40, uneventful 41-75, harmful 76-90, accident 91-100) ensures that most travel is safe but eventful, with dangerous situations being rare but memorable. This matches WFRP's tone where travel is usually routine but punctuated by dramatic moments that drive stories forward. The extensive variety within each category prevents repetition across long campaigns.

**Contains:**
- Encounter type probabilities
- Positive encounters (beneficial)
- Coincidental encounters (neutral)
- Harmful encounters (problems)
- Accident encounters (major incidents with damage, tests, cargo loss)
- Flavor text for player messages
- GM mechanical details

---

## 4. Utils Directory (`/utils`)

### 4.1 [utils/wfrp_mechanics.py](utils/wfrp_mechanics.py)
**Purpose:** Core WFRP game mechanics

**Overview:**
This is the mathematical and logical heart of the bot, implementing the core rules of WFRP 4th Edition in pure, testable Python functions. The module is intentionally kept free of Discord-specific code, making it easy to unit test and potentially reusable in non-Discord contexts. It handles dice parsing, rolling, and interpretation according to WFRP rules, including all the special cases and edge conditions that make WFRP dice rolls interesting (doubles for crits/fumbles, automatic failures, Success Level calculation).

The Success Level (SL) system is central to WFRP and is correctly implemented here. Unlike simple pass/fail systems, WFRP measures degrees of success and failure - rolling 29 vs target 41 gives SL +1 (marginal success), while rolling 19 gives SL +2 (solid success). This granularity allows for nuanced outcomes where better rolls produce better results. The module handles all the edge cases: roll of 1 is treated as 01 (a low double), roll of 100 is always a fumble regardless of skill, and doubles (11, 22, 33, etc.) trigger special outcomes.

The difficulty modifier system is also implemented, ranging from Very Easy (+60) to Impossible (-50). These modifiers are added to skill values before rolling, making tests easier or harder based on circumstances. This is crucial for boat handling tests where weather can add significant penalties, potentially turning a routine navigation test into a challenging one. The module provides helper functions to translate numeric modifiers into descriptive names ("Average", "Difficult", etc.), improving user-facing messages.

**Functions:**
- `parse_dice_notation(str)`: Parse "XdY±Z" format
- `roll_dice(num, size)`: Roll dice and return results
- `check_wfrp_doubles(roll, target)`: Detect crits/fumbles
- `calculate_success_level(roll, target)`: WFRP SL calculation
- `get_success_level_name(sl, success)`: Descriptive outcome names
- `get_difficulty_name(modifier)`: Difficulty tier names

**WFRP Rules Implemented:**
- Doubles: Matching digits (11, 22, 33, etc.)
- Roll of 1 = low double (01)
- Roll of 100 = always fumble
- Doubles ≤ target = crit, > target = fumble
- SL = (target tens digit) - (roll tens digit)

### 4.2 [utils/modifier_calculator.py](utils/modifier_calculator.py)
**Purpose:** Bridge between weather system and boat handling

**Overview:**
This module serves as the critical integration point between the weather system and the boat handling tests. It's responsible for translating weather data (wind strength, direction, weather type, special events) into concrete mechanical modifiers that affect skill tests. This separation of concerns is important - the weather system generates and stores weather data without knowing how it affects boat handling, while the boat handling command uses weather without needing to understand weather generation logic. The modifier calculator bridges these systems.

The calculation process is sophisticated because weather affects boat handling in multiple ways. Wind has both a speed modifier (how fast you can travel) and a difficulty penalty (how hard it is to control the boat). Weather effects like rain or fog add visibility penalties. Cold fronts and heat waves affect crew morale and performance. The module aggregates all these factors into a single, comprehensive modifier package that boat handling can directly apply to skill tests. It also provides human-readable explanations of each modifier, so players understand why their test has a +20 penalty (strong headwind + rain + poor visibility).

The time-of-day parameter is crucial because wind conditions change throughout the day. A morning boat handling test might face calm winds, while afternoon conditions could be much more challenging. The module extracts the appropriate wind data from the weather's four-period timeline (dawn/midday/dusk/midnight) and applies the corresponding modifiers, making time of day a meaningful tactical consideration.

**Key Function: `get_active_weather_modifiers(guild_id, time_of_day)`**

**Returns:**
- Wind modifier percentage (-25% to +25%)
- Wind strength and direction
- Boat handling penalty (from calm winds)
- Whether tacking is required
- Weather effects (visibility, test penalties)
- Special notes for dangerous conditions

**Usage Flow:**
1. Queries WeatherStorage for current day
2. Extracts wind for specific time (dawn/midday/dusk/midnight)
3. Looks up modifiers from weather_data tables
4. Parses penalties and special conditions
5. Returns formatted dictionary for boat handling command

**Other Functions:**
- `get_weather_summary(guild_id)`: All time periods
- `format_weather_impact_for_embed(mods)`: Discord embed formatting

### 4.3 [utils/weather_mechanics.py](utils/weather_mechanics.py)
**Purpose:** Weather generation algorithms with special event mechanics

**Key Features:**
- Daily weather generation logic
- Wind rolling for 4 time periods (dawn/midday/dusk/midnight)
- Temperature calculation with daily variation during events
- Cold front and heat wave mechanics with cooldown system
- Weather type determination by season

**Special Event System:**

**Cold Fronts:**
- Trigger: d100 roll = 2 (1% chance)
- Duration: 1d5 days (1-5 days)
- Effect: -10°C temperature modifier
- Cooldown: 7 days after event ends
- Daily variation: ±5°C based on d100 roll category

**Heat Waves:**
- Trigger: d100 roll = 99 (1% chance)
- Duration: 10+1d10 days (11-20 days)
- Effect: +10°C temperature modifier
- Cooldown: 7 days after event ends
- Daily variation: ±5°C based on d100 roll category

**Key Functions:**
- `handle_cold_front(roll, current_days, total, cooldown, heat_wave_active)`: Returns (modifier, remaining, total)
- `handle_heat_wave(roll, current_days, total, cooldown, cold_front_active)`: Returns (modifier, remaining, total)
- `roll_temperature_with_special_events(season, province, cold_front_days, cold_front_total, heat_wave_days, heat_wave_total, days_since_cf, days_since_hw)`: Returns (actual_temp, category, description, roll, cf_remaining, cf_total, hw_remaining, hw_total)
- `get_category_from_actual_temp(actual_temp, base_temp)`: Recalculates temperature category from final temperature

**Mechanics:**
- **Mutual Exclusivity:** Cold fronts and heat waves cannot overlap
- **Cooldown System:** 7-day cooldown prevents back-to-back events
- **Roll Suppression:** Special rolls (2, 99) ignored during active events to prevent nesting
- **Daily Variation:** Temperature varies ±5°C within events based on d100 roll
- **Category Recalculation:** Final temperature determines display category, not base temperature

**Constants:**
```python
COLD_FRONT_TRIGGER_ROLL = 2
HEAT_WAVE_TRIGGER_ROLL = 99
COLD_FRONT_COOLDOWN_DAYS = 7
HEAT_WAVE_COOLDOWN_DAYS = 7
COLD_FRONT_TEMP_MODIFIER = -10
HEAT_WAVE_TEMP_MODIFIER = 10
```

### 4.4 [utils/encounter_mechanics.py](utils/encounter_mechanics.py)
**Purpose:** Encounter generation and formatting

**Overview:**
This module contains the core logic for generating random river encounters, separate from the Discord command interface. It implements the probability system that weights encounters appropriately (most travel is uneventful, dangerous encounters are rare), selects specific encounters from the tables in encounter_data.py, and formats them for the dual-message system. The separation of encounter logic from Discord interaction makes the system testable and maintainable.

The encounter generation process involves multiple steps: rolling on the encounter type table (d100), selecting a specific encounter within that category, determining any variable elements (number of NPCs, amount of cargo lost, damage values), and formatting both the cryptic player message and the detailed GM notification. For accident encounters, the module also generates the mechanical details - what skill tests are required, what the difficulty is, how much damage is dealt, and what the consequences of failure are.

The formatting logic is particularly important for maintaining the dual-message system's effectiveness. Player messages must be atmospheric and evocative without revealing mechanical details, while GM messages must be comprehensive and immediately actionable during gameplay. The module handles both formatting requirements, ensuring GMs have all the information they need to adjudicate encounters without breaking immersion for players.

**Contains:**
- `generate_encounter()`: Roll encounter type and details
- Encounter formatting for player/GM messages
- Damage calculation for accidents
- Cargo loss formula
- Test requirement formatting

---

## 5. Data Directory (`/data`)

### [data/weather.db](data/weather.db)
**Purpose:** SQLite database file for persistent weather storage

**Overview:**
This is the persistent storage layer for all journey and weather data. SQLite was chosen for its simplicity, reliability, and zero-configuration requirements - the entire database is a single file that can be backed up, versioned, or moved easily. The database allows journeys to persist across bot restarts, meaning campaigns can span weeks or months of real time without losing weather data. It also enables features like viewing historical weather ("what was the weather on day 5?") and ensures state consistency across stage-based generation.

The database schema is carefully designed to handle both current journey state (what day are we on, what season/province) and daily weather records (wind, temperature, events for each specific day). The recent addition of cooldown tracking fields (days_since_last_cold_front, days_since_last_heat_wave) and event duration fields (cold_front_total_duration, heat_wave_total_duration) enables the sophisticated weather event system. The database also supports multiple guilds simultaneously, isolating each Discord server's weather data while using a shared bot instance.

**Size:** ~73 KB  
**Managed By:** `db/weather_storage.py`  
**Contains:**
- Guild journey states
- Daily weather records
- Cooldown tracking for special events

---

## 6. Supporting Files

### [server.py](server.py)
**Purpose:** Flask keep-alive server for hosting

**Overview:**
This is a minimal HTTP server that exists solely to satisfy hosting platform requirements, specifically Render.com's free tier which expects applications to respond to HTTP health checks. Without this server, the hosting platform would assume the bot has crashed and restart it repeatedly. The server runs on a separate thread from the Discord bot, responding to HTTP requests on port 8080 with a simple "Bot is alive!" message while the bot handles Discord events on its websocket connection.

The implementation is intentionally minimal - it doesn't serve any actual functionality, just proves the process is running. This is a common pattern for Discord bots deployed on platforms designed for web applications rather than persistent websocket services. The keep-alive approach allows the use of free hosting tiers that would otherwise be unsuitable for Discord bots.

**Function:**
- Runs minimal HTTP server on port 8080
- Keeps bot alive on Render's free tier
- Started by `main.py` before bot runs

### [requirements.txt](requirements.txt)
**Purpose:** Python dependencies

**Overview:**
This standard Python requirements file lists all external libraries the bot depends on, enabling reproducible deployments across development, testing, and production environments. The dependency list is intentionally minimal to reduce security vulnerabilities, deployment complexity, and startup time. Each dependency serves a specific purpose: discord.py provides the Discord API wrapper, python-dotenv loads environment variables from .env files for local development, and Flask powers the keep-alive server for hosting platform compatibility.

**Dependencies:**
- discord.py
- python-dotenv
- flask (for keep-alive)
- sqlite3 (built-in)

### [render.yaml](render.yaml)
**Purpose:** Render.com deployment configuration

**Overview:**
This Infrastructure-as-Code file defines how the bot should be deployed on Render.com's hosting platform. It specifies runtime environment (Python version), build commands (dependency installation), start commands (running main.py), environment variables (Discord token), and resource allocation. Using a configuration file rather than manual web UI setup ensures deployments are reproducible, version-controlled, and easily replicated across different hosting environments. This approach also enables automated deployments from Git pushes, streamlining the development workflow from code commit to production deployment.

---

## 7. Key Architectural Patterns

### Command Structure
All commands follow this pattern:
1. `setup(bot)` function registers commands
2. Slash command handler (`@bot.tree.command`)
3. Prefix command handler (`@bot.command`)
4. Shared `_perform_*()` logic function
5. Command logging to `boat-travelling-log` channel

### Data Flow Examples

#### Boat Handling Test Flow:
```
User: /boat-handling anara 0 dusk
    ↓
boat_handling.py: _perform_boat_handling()
    ↓
1. character_data.get_character('anara')
2. modifier_calculator.get_active_weather_modifiers(guild_id, 'dusk')
3. Calculate final target: base_skill + difficulty + lore_bonus + weather_penalty
4. wfrp_mechanics.roll_dice(1, 100)
5. wfrp_mechanics.calculate_success_level()
6. wfrp_mechanics.check_wfrp_doubles()
7. Format embed with narrative outcomes
8. Send to channel + log to boat-travelling-log
```

#### Weather Generation Flow:
```
User: /weather next
    ↓
weather.py: weather_slash() → handler.handle_command()
    ↓
handler.py: _generate_next_day() → _generate_daily_weather()
    ↓
1. weather_storage.get_journey_state(guild_id)
2. weather_storage.advance_day(guild_id)
3. Extract previous day state:
   - cold_front_days_remaining, cold_front_total_duration
   - heat_wave_days_remaining, heat_wave_total_duration
4. Get cooldown status:
   - days_since_last_cold_front, days_since_last_heat_wave
5. weather_mechanics.roll_temperature_with_special_events():
   - Roll 4 wind entries (dawn/midday/dusk/midnight)
   - Roll weather type (d100 by season)
   - Roll base temperature (d100 + province base)
   - Check event triggers (roll=2 for cold front, roll=99 for heat wave)
   - Apply cooldown checks (must be >7 days)
   - Check mutual exclusivity (one event at a time)
   - Suppress special rolls during active events (prevent nesting)
   - Apply daily variation (±5°C based on roll category)
   - Calculate final temperature with event modifier
   - Recalculate category from actual temperature
   - Format description with event info ("Cold Front: Day X of Y")
6. _update_cooldown_trackers():
   - Reset cooldown when new event starts
   - Keep at 0 while event active
   - Increment daily when no event active
7. weather_storage.save_daily_weather(guild_id, day, data):
   - Includes cold_front_total_duration, heat_wave_total_duration
8. display.format_weather_embed(data)
9. notifications.send_to_log_channel() (includes special events field)
10. Send to user
```

#### Stage-Based Weather Flow:
```
User: /weather next-stage
    ↓
handler.py: _generate_next_stage()
    ↓
1. weather_storage.get_journey_state(guild_id)
2. stages.generate_stage_weather(guild_id, stage_duration)
   - Loop: generate weather for each day in stage
   - Handle special events spanning multiple days:
     - Track cold_front_total_duration and heat_wave_total_duration
     - Apply cooldown system (7 days after event ends)
     - Enforce mutual exclusivity (one event at a time)
     - Continue events across multiple days
   - Update cooldown counters after each day
   - Calculate day progress (days_elapsed = total - remaining + 1)
3. weather_storage.advance_stage(guild_id)
4. Format based on display_mode:
   - 'simple': display.format_stage_summary_embed()
     - Shows day counters: "❄️ Cold Front (Day 2/3)"
     - Includes "(Final Day)" marker
   - 'detailed': display.format_stage_detailed_embed()
     - Full breakdown of each day
     - Event progress visible for each day
5. Send to user + log (GM gets special events notifications)
```

### Permission System
**GM Role:**
- Server owner always has GM permissions
- Users with "GM" role have GM permissions
- GM-only features:
  - `/weather override`: Manual weather control
  - `/weather-stage-config`: Stage configuration
  - `/river-encounter [type]`: Force encounter types

**Implementation:**
```python
def is_gm(user: discord.Member) -> bool:
    if user.guild.owner_id == user.id:
        return True
    gm_role = discord.utils.get(user.guild.roles, name="GM")
    if gm_role and gm_role in user.roles:
        return True
    return False
```

### Logging System
All commands log to `boat-travelling-log` channel:
- Command name and parameters
- User ID and display name
- Timestamp
- Formatted as Discord embeds

River encounters also log to `boat-travelling-notifications`:
- Full GM details (mechanics, tests, damage)
- Players see only cryptic flavor text in main channel

---

## 8. Implementation Guidelines

### When Implementing New Features:

**1. Dice/WFRP Mechanics:**
- Look in `utils/wfrp_mechanics.py` for core functions
- Follow existing patterns for SL calculation and doubles detection

**2. Character-Related Features:**
- Character data in `db/character_data.py`
- Add skills to appropriate category (trading or river_travelling)
- Update `get_boat_handling_skill()` if modifying boat mechanics

**3. Weather System:**
- **Generation logic:** `utils/weather_mechanics.py`
- **Data tables:** `db/weather_data.py`
- **Storage:** `db/weather_storage.py`
- **Command interface:** `commands/weather.py`
- **Handler logic:** `commands/weather_modules/handler.py`
- **Display:** `commands/weather_modules/display.py`
- **Modifiers for tests:** `utils/modifier_calculator.py`

**4. Encounters:**
- **Tables:** `db/encounter_data.py`
- **Generation:** `utils/encounter_mechanics.py`
- **Command:** `commands/river_encounter.py`

**5. New Commands:**
- Create file in `commands/` with `setup(bot)` function
- Register in `main.py`
- Add to help system in `commands/help.py`
- Implement both slash and prefix versions
- Add command logging

**6. Database Changes:**
- Schema in `db/weather_storage.py` (SQLite)
- Use migrations pattern for adding columns
- Test with existing data

### Testing Guidelines:
- Unit tests in `/tests` directory
- **88 tests total across 4 phases - all passing ✅**
- Test-Driven Development (TDD) approach
- See `TEST_GUIDE.md` and `TDD_QUICK_REFERENCE.md` for patterns

**Test Structure:**
- **Phase 1 (18 tests):** Database schema and cooldown tracking (`test_weather_storage_schema.py`)
- **Phase 2 (36 tests):** Core weather mechanics with events (`test_weather_mechanics_events.py`)
- **Phase 3 (15 tests):** Handler integration layer (`test_handler_integration.py`)
- **Phase 4 (19 tests):** Display formatting and consistency (`test_display_formatting.py`)

**Key Test Coverage:**
- Event triggering with cooldown checks
- Mutual exclusivity (no overlapping events)
- Roll suppression (prevents nesting bug)
- Daily temperature variation during events
- Cooldown state machine transitions
- Display consistency across channels
- Edge cases (1-day event, 20-day event, missing data)

---

## 9. Quick Reference: Where to Look

| Need to... | Look in... |
|------------|-----------|
| Add new command | `commands/` + register in `main.py` |
| Modify dice rolling | `utils/wfrp_mechanics.py` |
| Add character | `db/character_data.py` |
| Change weather generation | `utils/weather_mechanics.py` |
| Modify weather storage | `db/weather_storage.py` |
| Add weather effects | `db/weather_data.py` |
| Modify boat handling test | `commands/boat_handling.py` |
| Add encounter type | `db/encounter_data.py` |
| Change weather display | `commands/weather_modules/display.py` |
| Modify help text | `commands/help.py` |
| Add province/season | `db/weather_data.py` (PROVINCE_TEMPERATURES) |
| Change logging | Look for `boat-travelling-log` channel references |
| **Modify event mechanics** | **`utils/weather_mechanics.py`** |
| **Change cooldown system** | **`db/weather_storage.py` (storage) + `commands/weather_modules/handler.py` (logic)** |
| **Add event display text** | **`commands/weather_modules/stages.py` or `notifications.py`** |
| **Run tests** | **`pytest tests/` (88 tests across 4 phases)** |
| **Debug event issues** | **Check `test_weather_mechanics_events.py` for mechanics, `test_handler_integration.py` for integration** |

---

## 10. Discord Channel Architecture

The bot expects these channels:
- **boat-travelling-log**: All command logs (user-facing)
- **boat-travelling-notifications**: GM-only encounter details

If channels don't exist, logging fails silently (non-critical feature).

---

## 11. WFRP Game Rules Summary

For AI context when implementing features:

**Success Level (SL):**
- SL = (target tens digit) - (roll tens digit)
- Example: Roll 29 vs Target 41 → SL = 4 - 2 = +2

**Doubles:**
- Matching digits: 11, 22, 33, ..., 99
- Roll of 1 treated as low double (01)
- Roll of 100 always fumble
- Doubles ≤ target = critical success
- Doubles > target = fumble

**Difficulty Modifiers:**
- +60: Very Easy
- +40: Easy
- +20: Average
- +0: Challenging
- -10: Difficult
- -20: Hard
- -30: Very Difficult
- -40: Futile
- -50: Impossible

**Boat Handling:**
- Use Sail skill if available, otherwise Row
- Lore (Riverways) gives bonus (first digit: 47 → +4)
- Weather modifiers stack with difficulty
- Different outcomes based on SL

**Weather Events (Custom System):**
- **Cold Fronts:** 1% chance (roll=2), last 1-5 days, -10°C modifier, 7-day cooldown
- **Heat Waves:** 1% chance (roll=99), last 11-20 days, +10°C modifier, 7-day cooldown
- **Daily Variation:** ±5°C based on d100 roll category during events
- **Mutual Exclusivity:** Only one event type can be active at once
- **Roll Suppression:** Special rolls (2, 99) ignored during active events to prevent nesting
- **Category Recalculation:** Final temperature (after modifiers) determines display category

---

## 12. Project Structure Summary

```
travelling-bot/
├── main.py                    # Entry point, bot initialization
├── server.py                  # Flask keep-alive
├── requirements.txt           # Dependencies
├── render.yaml               # Deployment config
├── .env                      # Discord token (not in repo)
│
├── commands/                 # All bot commands
│   ├── __init__.py
│   ├── roll.py              # Dice rolling
│   ├── boat_handling.py     # Navigation tests
│   ├── weather.py           # Weather command interface
│   ├── river_encounter.py   # Random encounters
│   ├── help.py              # Help system
│   └── weather_modules/     # Weather subsystem
│       ├── handler.py       # Weather logic
│       ├── display.py       # Weather formatting
│       ├── formatters.py    # Small formatters
│       ├── notifications.py # Log channel messages
│       └── stages.py        # Multi-day generation
│
├── db/                      # Database and data tables
│   ├── __init__.py
│   ├── character_data.py    # Character stats
│   ├── weather_data.py      # Weather tables
│   ├── weather_storage.py   # SQLite persistence
│   └── encounter_data.py    # Encounter tables
│
├── utils/                   # Utilities and mechanics
│   ├── __init__.py
│   ├── wfrp_mechanics.py    # Core WFRP rules
│   ├── modifier_calculator.py # Weather modifiers
│   ├── weather_mechanics.py  # Weather generation
│   └── encounter_mechanics.py # Encounter generation
│
├── data/                    # Persistent storage
│   └── weather.db          # SQLite database
│
├── tests/                   # Test suite
│   └── [various test files]
│
└── [documentation files]    # .md planning docs
```

---

---

## 13. Recent Major Changes (Weather Event System)

**Date:** October 2025  
**Status:** ✅ Fully Implemented (88/88 tests passing)

### Summary of Weather Event System Overhaul

The weather system was completely overhauled to fix several critical issues and add new features:

**Problems Solved:**
1. ❌ **Display showed formulas instead of actual values** ("1d5 days" → "3 days")
2. ❌ **No day counter support** (couldn't show "Day 2 of 3")
3. ❌ **No cooldown mechanism** (events could trigger back-to-back)
4. ❌ **Events could overlap** (cold front + heat wave simultaneously)
5. ❌ **No daily variation** (temperature static throughout event)
6. ❌ **Nesting bug** (roll=2 during cold front triggered nested event)

**Solutions Implemented:**

**Phase 1: Database Layer**
- Added 4 new columns to track event durations and cooldowns
- `cold_front_total_duration` and `heat_wave_total_duration` store actual rolled values
- `days_since_last_cold_front` and `days_since_last_heat_wave` track cooldown periods
- Migration logic handles existing databases gracefully

**Phase 2: Core Mechanics**
- Updated event handlers to check cooldowns before triggering
- Implemented mutual exclusivity (one event at a time)
- Added daily temperature variation (±5°C during events)
- Roll suppression prevents nesting bug (special rolls ignored during events)
- Category recalculation from final temperature (not base)

**Phase 3: Handler Integration**
- Connected database layer to mechanics layer
- Implemented cooldown state machine (reset → 0 → increment)
- Proper data flow: DB → Handler → Mechanics → Handler → DB
- Saves all new fields after each day

**Phase 4: Display Updates**
- Stage summaries show day counters: "❄️ Cold Front (Day 2/3)"
- GM notifications include special events section
- Flavor text on day 1: "Sky filled with flocks of emigrating birds"
- "(Final Day)" marker when event ends
- Consistent formatting across all channels

**Testing:**
- 88 total tests across 4 phases (all passing)
- Test-Driven Development (TDD) approach
- Comprehensive coverage of edge cases
- 10-day journey lifecycle test validates end-to-end integration

**Files Modified:**
- `db/weather_storage.py` - Schema and cooldown methods
- `utils/weather_mechanics.py` - Event mechanics and daily variation
- `commands/weather_modules/handler.py` - Integration and cooldown state machine
- `commands/weather_modules/stages.py` - Day counter display
- `commands/weather_modules/notifications.py` - GM special events section

**Constants Added:**
```python
COLD_FRONT_TRIGGER_ROLL = 2
HEAT_WAVE_TRIGGER_ROLL = 99
COLD_FRONT_COOLDOWN_DAYS = 7
HEAT_WAVE_COOLDOWN_DAYS = 7
COLD_FRONT_TEMP_MODIFIER = -10
HEAT_WAVE_TEMP_MODIFIER = 10
```

---

## End of Context Document

This document provides a comprehensive map of the codebase for AI agents to understand where to look for specific functionality and how components interact. Use this as a reference when implementing new features or debugging issues.

**Last Updated:** October 30, 2025 - Weather event system overhaul complete (88/88 tests passing)
