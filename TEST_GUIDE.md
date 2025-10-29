# River Travel Bot - Manual Testing Guide

## Overview
This guide provides comprehensive test cases for all bot commands. Use this to verify functionality after updates or deployments.

**Bot Version:** Post-Refactoring (Weather Module v2.0)  
**Test Date:** _____________________  
**Tester:** _____________________

---

## ✅ Pre-Testing Setup

### Requirements
- [ ] Bot is online and connected to Discord
- [ ] Test server has the following channels:
  - Player channel (for commands)
  - `#boat-travelling-notifications` (GM channel)
- [ ] Test user has GM role (for testing restricted features)
- [ ] Test user without GM role available (for permission testing)

### Initial State
- [ ] No active journey (run `/weather end` if needed)
- [ ] Bot responds to commands
- [ ] All 7 commands synced (check console: "Synced X command(s)")

---

## 🎲 Command: /roll

**Purpose:** Roll dice with WFRP mechanics support

### Test Cases

#### TC-R01: Basic Dice Roll
- **Command:** `/roll dice:1d100`
- **Expected:** 
  - [ ] Embed displays with dice roll results
  - [ ] Shows "Roll: 1d100"
  - [ ] Shows result number (1-100)
  - [ ] Shows total
  - [ ] Footer shows roller's name

#### TC-R02: Multiple Dice
- **Command:** `/roll dice:3d10`
- **Expected:**
  - [ ] Shows individual results [X, Y, Z]
  - [ ] Shows correct total
  - [ ] No WFRP special rules (no target provided)

#### TC-R03: Dice with Modifier (Addition)
- **Command:** `/roll dice:2d6+5`
- **Expected:**
  - [ ] Shows "Roll: 2d6+5"
  - [ ] Shows individual dice results
  - [ ] Shows "Dice Modifier: +5"
  - [ ] Total = sum of dice + 5

#### TC-R04: Dice with Modifier (Subtraction)
- **Command:** `/roll dice:1d20-3`
- **Expected:**
  - [ ] Shows "Roll: 1d20-3"
  - [ ] Shows "Dice Modifier: -3"
  - [ ] Total = dice result - 3

#### TC-R05: WFRP Skill Test (Average Difficulty)
- **Command:** `/roll dice:1d100 target:45 modifier:20`
- **Expected:**
  - [ ] Shows WFRP Target section
  - [ ] Shows "Skill: 45 | Difficulty: Average (+20)"
  - [ ] Shows "Final Target: 65" (45 + 20)
  - [ ] If doubles rolled, shows crit/fumble appropriately

#### TC-R06: WFRP Skill Test (Hard Difficulty)
- **Command:** `/roll dice:1d100 target:45 modifier:-20`
- **Expected:**
  - [ ] Shows "Difficulty: Hard (-20)"
  - [ ] Shows "Final Target: 25" (45 - 20)
  - [ ] Correct crit/fumble detection based on 25 target

#### TC-R07: WFRP Critical Success (Manual)
- **Command:** Roll until you get doubles ≤ target (e.g., 22 with target 50)
- **Expected:**
  - [ ] Shows "⚡ Doubles!" section
  - [ ] Shows "🎉 Critical Success!"
  - [ ] Embed color changes to green

#### TC-R08: WFRP Fumble (Manual)
- **Command:** Roll until you get doubles > target (e.g., 88 with target 50)
- **Expected:**
  - [ ] Shows "⚡ Doubles!" section
  - [ ] Shows "💀 Fumble!"
  - [ ] Embed color changes to dark red

#### TC-R09: WFRP Roll 100 (Always Fumble)
- **Command:** Keep rolling until you get 100 (or note when you see it)
- **Expected:**
  - [ ] Always shows fumble, regardless of target
  - [ ] Even if target is 100+

#### TC-R10: Invalid Dice Notation
- **Command:** `/roll dice:banana`
- **Expected:**
  - [ ] Error embed: "❌ Invalid Dice Notation"
  - [ ] Shows examples of valid notation
  - [ ] Ephemeral message (only visible to user)

#### TC-R11: Large Dice Pool
- **Command:** `/roll dice:25d6`
- **Expected:**
  - [ ] Shows "*25 dice rolled*" instead of individual results
  - [ ] Correct total calculated
  - [ ] No performance issues

---

## ⛵ Command: /boat-handling

**Purpose:** Make WFRP Boat Handling Tests for navigation

### Test Cases

#### TC-B01: Basic Boat Handling Test
- **Command:** `/boat-handling character:anara`
- **Expected:**
  - [ ] Shows character name: "Anara of Sānxiá"
  - [ ] Shows skill used (Row or Sail based on wind)
  - [ ] Shows base skill value
  - [ ] Shows d100 roll result
  - [ ] Shows success/failure
  - [ ] If no active weather, uses default calm conditions

#### TC-B02: Test Each Character
- **Commands:** Test all five characters:
  - `/boat-handling character:anara`
  - `/boat-handling character:emmerich`
  - `/boat-handling character:hildric`
  - `/boat-handling character:oktavian`
  - `/boat-handling character:lupus`
- **Expected:**
  - [ ] Each character displays correct name
  - [ ] Each shows their specific skill values
  - [ ] All have Lore (Riverways) bonus if applicable
  - [ ] All calculate correctly

#### TC-B03: Difficulty Modifier
- **Command:** `/boat-handling character:anara difficulty:-20`
- **Expected:**
  - [ ] Shows "Hard (-20)" difficulty
  - [ ] Target reduced by 20 from base skill
  - [ ] Correct success/failure calculation

#### TC-B04: Time of Day - Dawn
- **Command:** `/boat-handling character:emmerich time_of_day:dawn`
- **Expected:**
  - [ ] Uses dawn wind conditions from weather
  - [ ] If no weather: defaults to calm
  - [ ] Shows time in embed or context

#### TC-B05: Time of Day - Midday
- **Command:** `/boat-handling character:hildric time_of_day:midday`
- **Expected:**
  - [ ] Uses midday wind conditions (default)
  - [ ] Appropriate modifiers applied

#### TC-B06: Time of Day - Dusk
- **Command:** `/boat-handling character:oktavian time_of_day:dusk`
- **Expected:**
  - [ ] Uses dusk wind conditions
  - [ ] Correct wind-based modifiers

#### TC-B07: Time of Day - Midnight
- **Command:** `/boat-handling character:lupus time_of_day:midnight`
- **Expected:**
  - [ ] Uses midnight wind conditions
  - [ ] Correct modifiers

#### TC-B08: With Active Weather Journey
- **Setup:** Start a journey first: `/weather journey season:summer province:reikland`
- **Command:** `/boat-handling character:anara time_of_day:midday`
- **Expected:**
  - [ ] Shows "Weather Impact" section
  - [ ] Shows current wind conditions
  - [ ] Shows weather-based modifiers
  - [ ] Boat handling penalty applied to difficulty
  - [ ] Modified target calculated correctly

#### TC-B09: Calm Wind (Uses Row)
- **Setup:** Generate weather until you get calm wind
- **Command:** `/boat-handling character:anara`
- **Expected:**
  - [ ] Uses "Row" skill
  - [ ] Shows Row skill value
  - [ ] Explanation mentions calm conditions

#### TC-B10: Any Wind (Uses Sail)
- **Setup:** Generate weather with wind (not calm)
- **Command:** `/boat-handling character:emmerich`
- **Expected:**
  - [ ] Uses "Sail" skill
  - [ ] Shows Sail skill value
  - [ ] Includes wind direction and strength

#### TC-B11: Invalid Character Name
- **Command:** `/boat-handling character:gandalf`
- **Expected:**
  - [ ] Error message
  - [ ] Lists available characters
  - [ ] Ephemeral error (if slash command)

#### TC-B12: Critical Success (Doubles)
- **Command:** Roll until doubles ≤ target achieved
- **Expected:**
  - [ ] Shows "⚡ Doubles!" section
  - [ ] Shows "🎉 Critical Success!"
  - [ ] Green embed color

#### TC-B13: Fumble (Doubles)
- **Command:** Roll until doubles > target achieved
- **Expected:**
  - [ ] Shows "⚡ Doubles!" section
  - [ ] Shows "💀 Fumble!"
  - [ ] Dark red embed color

---

## 🌦️ Command: /weather (Daily Progression)

**Purpose:** Generate and manage weather for river journeys

### Test Cases - Basic Journey

#### TC-W01: Start New Journey
- **Command:** `/weather journey season:summer province:reikland`
- **Expected:**
  - [ ] Success message: "New journey started"
  - [ ] Shows season: Summer
  - [ ] Shows province: Reikland
  - [ ] Shows starting day: 1
  - [ ] Initial weather generated for day 1
  - [ ] Weather displayed with full details
  - [ ] **GM Channel:** Notification in `#boat-travelling-notifications` with mechanics

#### TC-W02: Generate Next Day Weather
- **Setup:** Start journey first (TC-W01)
- **Command:** `/weather next`
- **Expected:**
  - [ ] Day increments (Day 2)
  - [ ] New weather generated
  - [ ] Shows weather type (Fair, Overcast, Rain, etc.)
  - [ ] Shows temperature with category
  - [ ] Shows wind timeline (dawn, midday, dusk, midnight)
  - [ ] Shows weather effects list
  - [ ] Shows boat handling modifiers
  - [ ] **GM Channel:** Mechanics notification sent

#### TC-W03: Progress Multiple Days
- **Setup:** Active journey
- **Command:** Run `/weather next` five times
- **Expected:**
  - [ ] Day counter increments correctly (2, 3, 4, 5, 6)
  - [ ] Each day has unique weather
  - [ ] Weather continuity (cold fronts, heat waves persist)
  - [ ] All notifications sent to GM channel

#### TC-W04: View Historical Weather
- **Setup:** Journey with at least 3 days
- **Command:** `/weather view day:1`
- **Expected:**
  - [ ] Shows weather for day 1
  - [ ] All details preserved (temperature, wind, effects)
  - [ ] Matches original day 1 weather

#### TC-W05: View Invalid Day
- **Command:** `/weather view day:999`
- **Expected:**
  - [ ] Error message: "No weather data for day 999"
  - [ ] Suggests checking current day

#### TC-W06: View Without Day Parameter
- **Command:** `/weather view` (without day parameter)
- **Expected:**
  - [ ] Error message: "Day number is required"
  - [ ] Shows example usage

#### TC-W07: End Journey
- **Setup:** Active journey
- **Command:** `/weather end`
- **Expected:**
  - [ ] Confirmation: "Journey ended"
  - [ ] Shows journey summary (total days, season, province)
  - [ ] **GM Channel:** Journey end notification
  - [ ] Next `/weather next` should fail (no active journey)

#### TC-W08: Next Without Active Journey
- **Setup:** No active journey (run `/weather end` first)
- **Command:** `/weather next`
- **Expected:**
  - [ ] Error: "No active journey"
  - [ ] Suggests using `/weather journey` to start

### Test Cases - Different Seasons

#### TC-W09: Spring Journey
- **Command:** `/weather journey season:spring province:talabecland`
- **Expected:**
  - [ ] Shows "Spring" season
  - [ ] Temperature ranges appropriate for spring
  - [ ] Weather types match spring patterns

#### TC-W10: Summer Journey
- **Command:** `/weather journey season:summer province:averland`
- **Expected:**
  - [ ] Shows "Summer" season
  - [ ] Higher temperatures
  - [ ] Summer weather patterns

#### TC-W11: Autumn Journey
- **Command:** `/weather journey season:autumn province:wissenland`
- **Expected:**
  - [ ] Shows "Autumn" season
  - [ ] Moderate temperatures
  - [ ] Autumn weather patterns

#### TC-W12: Winter Journey
- **Command:** `/weather journey season:winter province:ostland`
- **Expected:**
  - [ ] Shows "Winter" season
  - [ ] Lower temperatures
  - [ ] Winter weather patterns (snow, ice possible)

### Test Cases - Different Provinces

#### TC-W13: Test All Provinces
- **Commands:** Start journeys in each province (same season for comparison)
  - `/weather journey season:summer province:reikland`
  - `/weather journey season:summer province:averland`
  - `/weather journey season:summer province:wissenland`
  - `/weather journey season:summer province:stirland`
  - `/weather journey season:summer province:talabecland`
  - `/weather journey season:summer province:ostland`
  - `/weather journey season:summer province:hochland`
  - `/weather journey season:summer province:middenland`
  - `/weather journey season:summer province:nordland`
- **Expected:**
  - [ ] Each province shows different base temperatures
  - [ ] Regional characteristics reflected
  - [ ] All provinces work correctly

### Test Cases - Special Weather Events

#### TC-W14: Cold Front Detection
- **Command:** Generate weather until cold front appears (run `/weather next` multiple times)
- **Expected:**
  - [ ] Shows "❄️ Cold Front Active" in special events
  - [ ] Temperature significantly lower than normal
  - [ ] Persists for multiple days

#### TC-W15: Heat Wave Detection
- **Command:** Generate weather until heat wave appears (summer recommended)
- **Expected:**
  - [ ] Shows "🔥 Heat Wave" in special events
  - [ ] Temperature significantly higher than normal
  - [ ] Persists for multiple days

### Test Cases - Weather Types

#### TC-W16: Weather Variety
- **Command:** Generate 10+ days of weather (`/weather next` x10)
- **Expected:**
  - [ ] Multiple weather types observed:
    - [ ] Fair/Clear (🌤️)
    - [ ] Overcast (☁️)
    - [ ] Rain (🌧️)
    - [ ] Storm (⛈️)
    - [ ] Fog (🌫️)
    - [ ] Snow (❄️) - winter only
  - [ ] Each type shows appropriate effects
  - [ ] Weather changes over time (not static)

### Test Cases - Wind Conditions

#### TC-W17: Wind Timeline
- **Command:** Generate any day of weather
- **Expected:**
  - [ ] Shows 4 time periods: Dawn, Midday, Dusk, Midnight
  - [ ] Each has wind direction (N, NE, E, SE, S, SW, W, NW, Calm)
  - [ ] Each has wind strength (Calm, Light, Moderate, Strong, Gale)
  - [ ] Wind can change between time periods

#### TC-W18: Calm Wind
- **Command:** Generate until calm wind appears
- **Expected:**
  - [ ] Shows "Calm" for strength
  - [ ] No direction (or N/A)
  - [ ] Boat handling test would use "Row"

#### TC-W19: Strong Wind/Gale
- **Command:** Generate until strong wind or gale appears
- **Expected:**
  - [ ] Shows "Strong" or "Gale"
  - [ ] Shows direction
  - [ ] Significant boat handling penalties

### Test Cases - Temperature

#### TC-W20: Temperature Display
- **Command:** Generate any day
- **Expected:**
  - [ ] Shows numeric temperature (e.g., "18°C")
  - [ ] Shows category (Very Cold, Cold, Cool, Mild, Warm, Hot, Very Hot)
  - [ ] Shows wind chill if applicable
  - [ ] Realistic for season and province

#### TC-W21: Wind Chill Effect
- **Command:** Generate weather with strong wind in winter
- **Expected:**
  - [ ] Shows "Feels like" temperature
  - [ ] Feels like < actual temperature
  - [ ] Wind chill explanation in effects

---

## 🗺️ Command: /weather (Stage-Based Progression)

**Purpose:** Multi-day weather generation with stage system

### Test Cases - Stage Progression

#### TC-WS01: Next Stage (Default Settings)
- **Setup:** Start journey: `/weather journey season:summer province:reikland`
- **Command:** `/weather next-stage`
- **Expected:**
  - [ ] Generates 3 days of weather (default stage duration)
  - [ ] Shows "Stage 1: Days 2-4" (or similar)
  - [ ] All 3 days displayed
  - [ ] Simple display mode (default): Brief summary per day
  - [ ] Each day shows: weather emoji, type, temperature, special events
  - [ ] **GM Channel:** Notifications for each day (3 total)

#### TC-WS02: Multiple Stages
- **Setup:** Active journey
- **Command:** Run `/weather next-stage` three times
- **Expected:**
  - [ ] Stage 1: Days 2-4
  - [ ] Stage 2: Days 5-7
  - [ ] Stage 3: Days 8-10
  - [ ] Day counter increments correctly
  - [ ] No duplicate days
  - [ ] All weather unique per day

#### TC-WS03: View Stage Configuration
- **Command:** `/weather-stage-config` (no parameters)
- **Expected:**
  - [ ] Shows current stage duration (default: 3)
  - [ ] Shows current display mode (default: simple)
  - [ ] Shows description of each setting
  - [ ] Ephemeral message (only you see it)

#### TC-WS04: Mix Daily and Stage Progression
- **Setup:** Active journey, at day 5
- **Command:** 
  - `/weather next` (single day)
  - `/weather next-stage` (3 days)
  - `/weather next` (single day)
- **Expected:**
  - [ ] Day 6 generated (single)
  - [ ] Days 7-9 generated (stage)
  - [ ] Day 10 generated (single)
  - [ ] Seamless integration, no conflicts

### Test Cases - Stage Configuration (GM Only)

#### TC-WS05: Configure Stage Duration
- **Command:** `/weather-stage-config stage_duration:5`
- **Expected:**
  - [ ] Confirmation: "Stage configuration updated"
  - [ ] Shows new duration: 5 days
  - [ ] Next `/weather next-stage` generates 5 days

#### TC-WS06: Configure Display Mode - Detailed
- **Command:** `/weather-stage-config display_mode:detailed`
- **Expected:**
  - [ ] Confirmation: "Display mode set to detailed"
  - [ ] Next `/weather next-stage` shows detailed breakdown:
    - [ ] Full wind timeline per day
    - [ ] Complete weather effects list
    - [ ] Temperature categories
    - [ ] All modifier details

#### TC-WS07: Configure Display Mode - Simple
- **Command:** `/weather-stage-config display_mode:simple`
- **Expected:**
  - [ ] Confirmation: "Display mode set to simple"
  - [ ] Next `/weather next-stage` shows brief summary:
    - [ ] Weather emoji and type
    - [ ] Temperature
    - [ ] Special events only

#### TC-WS08: Configure Both Settings
- **Command:** `/weather-stage-config stage_duration:7 display_mode:detailed`
- **Expected:**
  - [ ] Both settings updated
  - [ ] Confirmation shows both changes
  - [ ] Next `/weather next-stage` uses both new settings

#### TC-WS09: Test All Stage Durations
- **Commands:** Test edge cases and middle values
  - `/weather-stage-config stage_duration:1`
  - `/weather-stage-config stage_duration:5`
  - `/weather-stage-config stage_duration:10`
- **Expected:**
  - [ ] All durations accepted (1-10 range)
  - [ ] Each generates correct number of days
  - [ ] No errors or issues

#### TC-WS10: Invalid Stage Duration
- **Command:** `/weather-stage-config stage_duration:15`
- **Expected:**
  - [ ] Error: Duration must be 1-10
  - [ ] Settings unchanged
  - [ ] Helpful error message

#### TC-WS11: Stage Config Without GM Role
- **Setup:** Use account without GM role or server owner
- **Command:** `/weather-stage-config stage_duration:5`
- **Expected:**
  - [ ] Error: "Only GMs and server owner can configure stages"
  - [ ] Settings unchanged
  - [ ] Ephemeral error message

### Test Cases - Stage Display Comparison

#### TC-WS12: Simple Display Mode Details
- **Setup:** `/weather-stage-config display_mode:simple`
- **Command:** `/weather next-stage`
- **Expected:**
  - [ ] Each day: One line with emoji + type
  - [ ] Temperature shown
  - [ ] Special events only (no full effects list)
  - [ ] Quick to read, good for fast travel
  - [ ] Compact embed

#### TC-WS13: Detailed Display Mode Details
- **Setup:** `/weather-stage-config display_mode:detailed`
- **Command:** `/weather next-stage`
- **Expected:**
  - [ ] Each day: Full breakdown section
  - [ ] Wind timeline (all 4 times)
  - [ ] Complete weather effects list
  - [ ] Temperature category
  - [ ] Special event details
  - [ ] All modifiers shown
  - [ ] Longer embed, comprehensive info

---

## 🔒 Command: /weather override (GM Only)

**Purpose:** Manually set specific weather conditions

### Test Cases - Weather Override

#### TC-WO01: Basic Override
- **Setup:** Active journey at day 5
- **Command:** `/weather override season:winter province:nordland`
- **Expected:**
  - [ ] Interactive message with buttons/dropdowns
  - [ ] Can select wind for each time period
  - [ ] Can set temperature
  - [ ] Can choose weather type
  - [ ] Preview shows selections
  - [ ] Apply button finalizes weather

#### TC-WO02: Override Without GM Role
- **Setup:** User without GM role
- **Command:** `/weather override season:summer province:reikland`
- **Expected:**
  - [ ] Error: "Only GMs and server owner can override weather"
  - [ ] No override interface shown
  - [ ] Ephemeral error

#### TC-WO03: Manual Weather Variety
- **Command:** Create different manual weather scenarios
- **Expected:**
  - [ ] Can create calm conditions
  - [ ] Can create storm with gale winds
  - [ ] Can set extreme temperatures
  - [ ] Can combine unusual weather patterns
  - [ ] All selections persist correctly

#### TC-WO04: Override Then Continue Normal
- **Setup:** Override day 5 weather manually
- **Command:** `/weather next` (for day 6)
- **Expected:**
  - [ ] Day 6 generates normally (not overridden)
  - [ ] Weather continuity maintained if applicable
  - [ ] Override only affected single day

---

## 🌊 Command: /river-encounter

**Purpose:** Generate random river travel encounters

### Test Cases - Basic Encounters

#### TC-E01: Random Encounter
- **Command:** `/river-encounter`
- **Expected:**
  - [ ] **Player Message (Public):**
    - [ ] Cryptic, atmospheric flavor text
    - [ ] Grimdark description
    - [ ] No mechanical details
    - [ ] Appropriate emoji
  - [ ] **GM Message (#boat-travelling-notifications):**
    - [ ] Full encounter details
    - [ ] Encounter type and probability roll
    - [ ] Required skill tests with difficulties
    - [ ] Damage/effects if applicable
    - [ ] Mechanical summary

#### TC-E02: Multiple Random Encounters
- **Command:** Run `/river-encounter` 10 times
- **Expected:**
  - [ ] Variety of encounter types observed
  - [ ] Positive (10% - should see 0-2)
  - [ ] Coincidental (30% - should see 2-4)
  - [ ] Uneventful (35% - should see 3-4)
  - [ ] Harmful (15% - should see 1-2)
  - [ ] Accident (10% - should see 0-2)
  - [ ] Probabilities roughly match expected

#### TC-E03: Encounter Type - Positive
- **Command:** Keep rolling until you see positive encounter (or use override TC-E09)
- **Expected:**
  - [ ] Beneficial event
  - [ ] Helpful NPCs, tailwinds, shortcuts, etc.
  - [ ] Positive emoji (✨)
  - [ ] Green/teal color
  - [ ] May include bonus modifiers

#### TC-E04: Encounter Type - Coincidental
- **Command:** Roll until coincidental encounter
- **Expected:**
  - [ ] Neutral observation
  - [ ] Wildlife, landmarks, passing boats
  - [ ] Informational emoji (👀)
  - [ ] Blue/neutral color
  - [ ] No significant mechanical impact

#### TC-E05: Encounter Type - Uneventful
- **Command:** Roll until uneventful
- **Expected:**
  - [ ] Nothing happens
  - [ ] Simple flavor text
  - [ ] 😴 emoji
  - [ ] Gray color
  - [ ] Quick message

#### TC-E06: Encounter Type - Harmful
- **Command:** Roll until harmful encounter
- **Expected:**
  - [ ] Minor problem
  - [ ] Debris, delays, difficult passages
  - [ ] ⚠️ emoji
  - [ ] Orange/yellow color
  - [ ] May require skill test
  - [ ] Potential minor damage/delays

#### TC-E07: Encounter Type - Accident
- **Command:** Roll until accident (or use override)
- **Expected:**
  - [ ] Major incident
  - [ ] Significant damage
  - [ ] 💥 emoji
  - [ ] Red color
  - [ ] Multiple skill tests possible
  - [ ] Cargo loss formula (if applicable)
  - [ ] Serious consequences

#### TC-E08: Encounter Details - Skill Tests
- **Command:** Generate encounters until you see skill test requirements
- **Expected:**
  - [ ] GM message shows required skill
  - [ ] Shows difficulty modifier
  - [ ] Shows consequences of failure
  - [ ] Examples: Navigate, Row, Swim, Perception, Athletics

### Test Cases - GM Override

#### TC-E09: Override - Positive
- **Command:** `/river-encounter type:positive`
- **Expected:**
  - [ ] Forces positive encounter
  - [ ] All positive encounter features
  - [ ] Only works for GM users

#### TC-E10: Override - Coincidental
- **Command:** `/river-encounter type:coincidental`
- **Expected:**
  - [ ] Forces coincidental encounter
  - [ ] Neutral observation generated

#### TC-E11: Override - Uneventful
- **Command:** `/river-encounter type:uneventful`
- **Expected:**
  - [ ] Forces uneventful day
  - [ ] Nothing happens message

#### TC-E12: Override - Harmful
- **Command:** `/river-encounter type:harmful`
- **Expected:**
  - [ ] Forces harmful encounter
  - [ ] Minor problem generated

#### TC-E13: Override - Accident
- **Command:** `/river-encounter type:accident`
- **Expected:**
  - [ ] Forces accident
  - [ ] Major incident generated
  - [ ] Full accident details in GM message

#### TC-E14: Override Without GM Role
- **Setup:** User without GM role
- **Command:** `/river-encounter type:positive`
- **Expected:**
  - [ ] Error: "Only GMs can override encounter type"
  - [ ] No encounter generated
  - [ ] Ephemeral error message

### Test Cases - Dual Message System

#### TC-E15: Player Message Verification
- **Command:** `/river-encounter`
- **Expected:**
  - [ ] Public message visible to all
  - [ ] No mechanical details
  - [ ] Atmospheric only
  - [ ] No dice rolls shown
  - [ ] No damage numbers
  - [ ] No test difficulties

#### TC-E16: GM Message Verification
- **Command:** `/river-encounter`
- **Expected:**
  - [ ] Message in `#boat-travelling-notifications` only
  - [ ] Not visible to players (wrong channel)
  - [ ] Full mechanics shown
  - [ ] All numbers and tests revealed
  - [ ] Can be used to run encounter

#### TC-E17: Cargo Loss (Accident Only)
- **Command:** Force accident or roll until you get one
- **Expected:**
  - [ ] GM message shows cargo loss calculation
  - [ ] Uses special formula (d10 roll)
  - [ ] Shows percentage or items lost
  - [ ] Only appears in accident encounters

---

## 📖 Command: /help

**Purpose:** Display bot command documentation

### Test Cases - Help System

#### TC-H01: General Help
- **Command:** `/help`
- **Expected:**
  - [ ] Shows overview of all commands
  - [ ] Lists /roll, /boat-handling, /weather, /river-encounter
  - [ ] Shows GM features section
  - [ ] Shows quick tips
  - [ ] Mentions use `/help <command>` for details

#### TC-H02: Help - Roll
- **Command:** `/help command:roll`
- **Expected:**
  - [ ] Detailed /roll documentation
  - [ ] Shows syntax and parameters
  - [ ] Shows examples (basic and WFRP)
  - [ ] Shows difficulty modifiers table
  - [ ] Explains doubles and critical/fumble

#### TC-H03: Help - Boat Handling
- **Command:** `/help command:boat-handling`
- **Expected:**
  - [ ] Detailed boat-handling documentation
  - [ ] Lists all 5 characters
  - [ ] Shows time_of_day options
  - [ ] Explains Row vs Sail selection
  - [ ] Shows examples
  - [ ] Mentions weather integration

#### TC-H04: Help - Weather
- **Command:** `/help command:weather`
- **Expected:**
  - [ ] Comprehensive weather documentation
  - [ ] Shows daily progression commands
  - [ ] Shows stage-based progression
  - [ ] Lists all seasons
  - [ ] Lists all provinces
  - [ ] Explains stage display modes
  - [ ] Shows GM features
  - [ ] Multiple examples

#### TC-H05: Help - River Encounter
- **Command:** `/help command:river-encounter`
- **Expected:**
  - [ ] Detailed encounter documentation
  - [ ] Shows encounter types and probabilities
  - [ ] Explains dual-message system
  - [ ] Shows GM override feature
  - [ ] Lists what GM message contains

#### TC-H06: Help - Invalid Command
- **Command:** `/help command:gandalf`
- **Expected:**
  - [ ] Falls back to general help
  - [ ] No error message
  - [ ] Shows all commands overview

---

## 🔗 Integration Testing

**Purpose:** Test interactions between different commands

### Test Cases - Cross-Command Integration

#### TC-I01: Weather + Boat Handling
- **Setup:** 
  1. Start journey: `/weather journey season:winter province:nordland`
  2. Generate weather: `/weather next`
- **Command:** `/boat-handling character:anara time_of_day:midday`
- **Expected:**
  - [ ] Boat handling uses current weather
  - [ ] Shows "Weather Impact" section
  - [ ] Modifiers from weather applied
  - [ ] Wind affects Row vs Sail selection
  - [ ] Correct total difficulty

#### TC-I02: Stage Progression + Boat Handling
- **Setup:**
  1. Start journey
  2. `/weather next-stage` (generate 3 days)
- **Command:** Test boat handling at different times
- **Expected:**
  - [ ] Can test for any of the 3 generated days
  - [ ] Each day has different weather modifiers
  - [ ] Stage weather properly saved

#### TC-I03: Weather + River Encounter Sequence
- **Setup:** Active weather journey
- **Command:** 
  1. `/weather next`
  2. `/river-encounter`
  3. `/boat-handling character:emmerich`
- **Expected:**
  - [ ] All three work together
  - [ ] Weather affects boat handling
  - [ ] Encounter adds narrative flavor
  - [ ] No conflicts between systems

#### TC-I04: Multiple Guilds/Servers
- **Setup:** Bot in multiple servers
- **Command:** Use weather commands in Server A, then Server B
- **Expected:**
  - [ ] Each server has independent journey state
  - [ ] No cross-contamination
  - [ ] Both servers work simultaneously

#### TC-I05: Concurrent Users
- **Setup:** Multiple users in same server
- **Command:** Two users run boat-handling at same time
- **Expected:**
  - [ ] Both commands complete successfully
  - [ ] No race conditions
  - [ ] Both use current weather correctly

---

## 🛡️ Permission Testing

**Purpose:** Verify GM-only features are properly restricted

### Test Cases - Permission Checks

#### TC-P01: GM Commands - Server Owner
- **Setup:** Use server owner account
- **Commands:** Try all GM-restricted features
  - `/weather override`
  - `/weather-stage-config`
  - `/river-encounter type:accident`
- **Expected:**
  - [ ] All commands work
  - [ ] No permission errors
  - [ ] Full functionality available

#### TC-P02: GM Commands - GM Role
- **Setup:** User with "GM" role (not owner)
- **Commands:** Try all GM-restricted features
- **Expected:**
  - [ ] All commands work
  - [ ] Role properly recognized
  - [ ] Same access as owner

#### TC-P03: GM Commands - No Permission
- **Setup:** Regular user (no GM role, not owner)
- **Commands:** Try restricted features
  - `/weather override`
  - `/weather-stage-config stage_duration:5`
  - `/river-encounter type:positive`
- **Expected:**
  - [ ] All commands blocked
  - [ ] Error: "Only GMs and server owner..."
  - [ ] Ephemeral error messages
  - [ ] No functionality available

#### TC-P04: Public Commands - Anyone
- **Setup:** Regular user
- **Commands:** Try public commands
  - `/weather next`
  - `/weather view day:1`
  - `/weather journey season:summer province:reikland`
  - `/boat-handling character:anara`
  - `/river-encounter`
  - `/roll dice:1d100`
  - `/help`
- **Expected:**
  - [ ] All commands work
  - [ ] No permission checks
  - [ ] Full functionality

---

## 🔍 Edge Cases & Error Handling

**Purpose:** Test boundary conditions and error scenarios

### Test Cases - Edge Cases

#### TC-EC01: Rapid Command Spam
- **Command:** Spam `/weather next` 20 times rapidly
- **Expected:**
  - [ ] All commands process successfully
  - [ ] Days increment correctly (no skips)
  - [ ] No duplicate days
  - [ ] No bot crashes
  - [ ] Performance acceptable

#### TC-EC02: Long Journey
- **Command:** Generate 100 days of weather
- **Expected:**
  - [ ] All days generate successfully
  - [ ] Day counter accurate
  - [ ] Can view historical days
  - [ ] No memory issues
  - [ ] Performance stable

#### TC-EC03: Journey End and Restart
- **Setup:**
  1. Start journey
  2. Progress 10 days
  3. `/weather end`
- **Command:** `/weather journey season:spring province:averland`
- **Expected:**
  - [ ] Old journey completely cleared
  - [ ] New journey starts at day 1
  - [ ] No data from old journey
  - [ ] Clean slate

#### TC-EC04: Invalid Season
- **Command:** Try invalid season (via prefix command if possible)
- **Expected:**
  - [ ] Error message
  - [ ] Lists valid seasons
  - [ ] No journey started

#### TC-EC05: Invalid Province
- **Command:** Try invalid province
- **Expected:**
  - [ ] Error message
  - [ ] Lists valid provinces
  - [ ] No journey started

#### TC-EC06: Bot Restart During Journey
- **Setup:**
  1. Start journey
  2. Generate 5 days
  3. Restart bot (stop and start main.py)
- **Command:** `/weather next`
- **Expected:**
  - [ ] Journey state preserved
  - [ ] Day 6 generates correctly
  - [ ] All historical data intact
  - [ ] No data loss

#### TC-EC07: Missing GM Notification Channel
- **Setup:** Delete or rename `#boat-travelling-notifications` channel
- **Command:** `/weather next` or `/river-encounter`
- **Expected:**
  - [ ] Player message still works
  - [ ] GM notification silently fails OR error logged
  - [ ] Bot doesn't crash
  - [ ] Main functionality unaffected

#### TC-EC08: Very Long Character Name
- **Command:** Use prefix command with very long input
- **Expected:**
  - [ ] Handles gracefully
  - [ ] Error or truncation
  - [ ] No crash

#### TC-EC09: Negative Dice
- **Command:** `/roll dice:-5d6` (if possible)
- **Expected:**
  - [ ] Error: "Invalid dice notation"
  - [ ] Helpful message
  - [ ] No crash

#### TC-EC10: Extreme WFRP Modifier
- **Command:** `/roll dice:1d100 target:50 modifier:100`
- **Expected:**
  - [ ] Handles gracefully
  - [ ] Target clamped to 1-100
  - [ ] No overflow errors

---

## 📊 Three-Channel System Verification

**Purpose:** Verify narrative/mechanics separation

### Test Cases - Channel Routing

#### TC-CH01: Player Channel Output
- **Command:** Any command
- **Expected:**
  - [ ] Narrative output in player channel
  - [ ] No raw dice rolls (for weather/encounters)
  - [ ] User-friendly formatting
  - [ ] Immersive descriptions

#### TC-CH02: GM Channel Output
- **Command:** Weather or encounter command
- **Expected:**
  - [ ] Mechanics in `#boat-travelling-notifications`
  - [ ] Dice rolls shown
  - [ ] Modifiers visible
  - [ ] Tables and formulas
  - [ ] Not visible to players (different channel)

#### TC-CH03: Weather Notification Content
- **Command:** `/weather next`
- **Check:** GM channel message
- **Expected:**
  - [ ] Shows all dice rolls (temperature, weather, wind)
  - [ ] Shows special event rolls
  - [ ] Shows modifier calculations
  - [ ] Comprehensive technical breakdown

#### TC-CH04: Encounter Notification Content
- **Command:** `/river-encounter`
- **Check:** GM channel message
- **Expected:**
  - [ ] Shows d100 roll for encounter type
  - [ ] Shows all sub-rolls (damage, cargo, etc.)
  - [ ] Shows skill test requirements
  - [ ] Full mechanical details

#### TC-CH05: Stage Notification Volume
- **Command:** `/weather next-stage` (3 days)
- **Check:** GM channel
- **Expected:**
  - [ ] 3 separate notifications (one per day)
  - [ ] Each has full mechanics
  - [ ] Can scroll through all 3
  - [ ] Not overwhelming in player channel

---

## 📝 Test Results Summary

### Statistics

- **Total Test Cases:** 155
- **Passed:** _____
- **Failed:** _____
- **Skipped:** _____
- **Success Rate:** _____%

### Critical Issues Found

1. _________________________________
2. _________________________________
3. _________________________________

### Minor Issues Found

1. _________________________________
2. _________________________________
3. _________________________________

### Notes

_______________________________________
_______________________________________
_______________________________________

### Recommendations

_______________________________________
_______________________________________
_______________________________________

---

## ✅ Sign-Off

**Tester Name:** _____________________  
**Date:** _____________________  
**Bot Version:** _____________________  
**Environment:** _____________________  

**Status:** [ ] PASS [ ] FAIL [ ] CONDITIONAL PASS

**Notes:**
_______________________________________
_______________________________________
_______________________________________
