# River Encounter Command - Implementation Plan

## Overview
Create a `/river-encounter` command that generates random encounters during WFRP river travel stages. The system uses a weighted probability system to determine encounter types, then rolls on specific tables for details. Some encounters (accidents) include complex mechanics with damage rolls, tests, and consequences.

## Command Structure
```
/river-encounter [stage]
```
- **stage**: Optional stage number/name for tracking (e.g., "Day 2 Afternoon")
- If no stage provided, just generates an encounter

## Player vs GM Information Split

**IMPORTANT DESIGN DECISION:**
- **Players** receive only vague, atmospheric flavor text (grimdark/dark humor style)
- **GM** receives full mechanical details in #boat-travelling-notifications channel
- This creates mystery and tension for players while giving GM all needed info

### Player Message Design Philosophy
- Cryptic hints about encounter type
- Dark humor and grimdark atmosphere (WFRP style)
- No mechanical details revealed
- No specific encounter names
- Multiple random flavor texts per encounter type (variety)
- Short and atmospheric (3-4 sentences max)

## Encounter System Architecture

### 1. Encounter Type Determination
**Probability Table (Roll d100):**
```
01-10:  Positive Encounter      (10%)
11-25:  Coincidental Encounter  (15%)
26-85:  Uneventful             (60%)
86-95:  Harmful Encounter       (10%)
96-100: Accident                (5%)
```

### 2. Encounter Detail Tables

#### 2.1 Positive Encounters (1d100)
Based on provided image data:
- 01-10: Friendly Fisherfolk
- 11-20: River Gossip
- 21-30: Picturesque Stop
- 31-40: Trading Post
- 41-50: Experienced Guide
- 51-60: A Helping Hand
- 61-70: Hidden Cove
- 71-80: Clear Skies (weather bonus)
- 81-90: Healer's Touch
- 91-100: Blessed Journey (heal Wounds & Fatigued)

#### 2.2 Coincidental Encounters (1d100)
Based on provided image data:
- 01-10: Mysterious Ruins
- 11-20: Abandoned Boat
- 21-30: Traveling Caravan
- 31-40: Unusual Wildlife
- 41-50: Strange Lights
- 51-60: Religious Procession
- 61-70: Fisher's Folly
- 71-80: Weather Change
- 81-90: Drifting Debris
- 91-100: Lost Item

#### 2.3 Harmful Encounters (1d100)
Based on provided image data:
- 01-10: Blocked Path (Fatigued Condition risk)
- 11-20: River Pirates (combat)
- 21-30: Unfriendly Waters (ambush risk)
- 31-40: Poisoned Waters (sickness/disease)
- 41-50: Natural Hazard (storm/rapid)
- 51-60: Equipment Failure (repair needed)
- 61-70: Infestation (insects/creatures)
- 71-80: Hostile Wildlife (crocodiles/serpents)
- 81-90: Disease Outbreak (illness)
- 91-100: Sabotage (leak/malfunction)

#### 2.4 Accident Table (1d100) - **COMPLEX MECHANICS**
Based on provided data with detailed mechanics:

**01-10: STEERING**
- Tiller bar breaks or rudder falls off
- Treat as Critical Hit to boat's steering
- **Mechanics**: Reference boat damage rules (page 29)

**11-20: BROKEN RIGGING**
- Ropes controlling sail break
- Boat loses speed, sail may collapse
- Treat as Critical Hit to boat's rigging
- **Mechanics**: Reference boat damage rules (page 29)

**21-30: SWINGING BOOM**
- Sudden crosswind swings boom across deck
- **Test Required**: Challenging (+0) Dodge Test
- **Failure**: +5 Damage hit
- **Additional Test**: Challenging (+0) Athletics Test or knocked into river

**31-40: SNAGGED ANCHOR**
- Anchor snags on submerged obstacle
- **Test Required**: Challenging (+0) Athletics Test (all crew)
- **Failure**: Knocked prone + 1 hit for +3 Damage
- **Additional Effect**: Anchor line may snap (boat drifts)

**41-50: CARGO SHIFT**
- Unsecured cargo shifts violently
- **Test Required**: Challenging (+0) Dodge Test (characters in cargo area)
- **Failure**: Hit by cargo for +4 Damage
- **Additional Effect**: Hazardous cargo may cause fires/spills
- **Cargo Loss**: Roll `10 + floor((1d100 + 5) / 10) * 10` encumbrance lost

**51-60: LOOSE PLANKING**
- Planks on deck/hull come loose
- **Test Required**: Challenging (+0) Trade (Carpentry) Test for repairs
- **Failure**: Boat takes on water, may lead to "Holed" condition

**61-70: NAVIGATIONAL ERROR**
- Boat strikes hidden rock or sandbar
- **Damage**: Roll on Boat Hit Location Chart
- **Additional**: May be grounded (Strength Test to refloat)

**71-80: MAN OVERBOARD**
- Crew member falls into river
- **Test Required**: Challenging (+0) Swim Test (overboard character)
- **Rescue Test**: Challenging (+0) Strength or Dexterity Test (rescuers)
- **Failure**: Drowning or swept away

**81-90: SUDDEN SQUALL**
- Violent storm hits boat
- **Test Required**: Challenging (+0) Boat Handling Test each turn
- **Failure**: Risk of capsize, may trigger multiple accidents

**91-100: FIRE ON BOARD**
- Fire ignites on boat
- **Damage**: 1d10 damage to superstructure each turn
- **Test Required**: Challenging (+0) Dexterity Test to extinguish
- **Failure**: Fire continues, spreads to rigging/hull

## Data Requirements

### 1. Player Flavor Text Tables

**Purpose**: Cryptic, atmospheric messages shown to players (grimdark WFRP style)

#### 1.1 Positive Encounter Flavor Texts (Random selection)
```python
POSITIVE_FLAVOR_TEXTS = [
    "The stench of the river seems... almost bearable today. How peculiar.",
    "A rare moment of peace. Suspicious, really. The gods must be planning something worse.",
    "For once, the water doesn't look like it wants to kill you. Enjoy it while it lasts.",
    "Something fortunate happens. You're not sure whether to be grateful or terrified of the price.",
    "The river grants a small mercy. Best not to question it in these dark times.",
    "A stroke of luck befalls the crew. Probably won't last—nothing good ever does.",
    "The journey eases, if only briefly. Savor it; Morr's garden awaits us all.",
    "Things go surprisingly well. The Gods of Chaos must be laughing at something else today.",
]
```

#### 1.2 Coincidental Encounter Flavor Texts (Random selection)
```python
COINCIDENTAL_FLAVOR_TEXTS = [
    "Something odd catches your eye along the riverbank. Nothing you can quite explain.",
    "The river reveals one of its many peculiarities. You're not sure what to make of it.",
    "An unusual sight breaks the monotony. At least it's not trying to eat you... yet.",
    "Something strange, but ultimately inconsequential. The river has shown you stranger.",
    "You witness something curious on your journey. File it away for later nightmares.",
    "The river's mysteries manifest before you. Whether blessing or curse, who can say?",
    "An oddity presents itself. In these lands, even the mundane carries an air of dread.",
    "Something catches your attention. Probably means nothing. Probably.",
]
```

#### 1.3 Uneventful Flavor Texts (Random selection)
```python
UNEVENTFUL_FLAVOR_TEXTS = [
    "The river flows, you float, nothing tries to kill you. A good day by Reikland standards.",
    "Remarkably unremarkable. The most you can hope for in these wretched times.",
    "Nothing happens. You're almost disappointed. Almost.",
    "The journey continues in blessed tedium. Better boring than dead, as they say.",
    "Another uneventful stretch. Pray to Ranald it stays that way.",
    "The gods ignore you today. Sometimes that's the best outcome.",
    "Mile after sodden mile of nothing. Just as Morr intended.",
    "Peace, quiet, and the gentle lapping of possibly-diseased water. Paradise.",
]
```

#### 1.4 Harmful Encounter Flavor Texts (Random selection)
```python
HARMFUL_FLAVOR_TEXTS = [
    "Trouble. Of course there's trouble. There's always trouble on these thrice-damned rivers.",
    "Something wicked this way comes. And you're on a boat with nowhere to run.",
    "The river demands its toll in blood and tears. Mostly yours.",
    "Danger presents itself with the inevitability of death and taxes. Usually both.",
    "Your day takes a turn for the worse. Which, on the river, is saying something.",
    "The other shoe drops. Along with several sharp objects aimed at your head.",
    "Misfortune strikes like a drunken flagellant—unexpected and violent.",
    "The river shows its teeth. Time to see if Shallya's mercy extends to fools on boats.",
]
```

#### 1.5 Accident Flavor Texts (Random selection)
```python
ACCIDENT_FLAVOR_TEXTS = [
    "Something on the boat breaks. Because of course it does. Nothing works properly in this forsaken land.",
    "CRACK! That didn't sound good. That didn't sound good at all.",
    "The boat protests its existence with alarming sounds. You sympathize, but now's not the time.",
    "Something vital chooses this exact moment to fail catastrophically. Typical.",
    "The ship groans ominously. Either it's falling apart or possessed. Possibly both.",
    "A critical failure occurs at the worst possible moment. As is tradition.",
    "Murphy's Law strikes with the precision of a ratcatcher's blade. Something's broken.",
    "The boat decides today is a good day to test your crisis management skills. It is not.",
    "Disaster strikes from an unexpected quarter. Mostly because you're too poor to afford a boat that works properly.",
]
```

### 2. Encounter Type Probabilities
```python
ENCOUNTER_TYPES = {
    (1, 10): "positive",
    (11, 25): "coincidental", 
    (26, 85): "uneventful",
    (86, 95): "harmful",
    (96, 100): "accident"
}
```

### 3. Encounter Detail Tables
Each table needs:
- Range (1-100)
- Title
- Description
- Mechanical effects (if any)
- Tests required (if any)
- Damage formulas (if any)
- **NOTE**: Players never see this data directly—only GM gets full details

### 4. Accident Mechanics Data
```python
ACCIDENT_MECHANICS = {
    "steering": {
        "test": None,
        "damage": "critical_hit_steering",
        "reference": "page 29"
    },
    "swinging_boom": {
        "test": "Challenging (+0) Dodge",
        "damage": "+5",
        "secondary_test": "Challenging (+0) Athletics",
        "secondary_effect": "knocked_into_river"
    },
    "cargo_shift": {
        "test": "Challenging (+0) Dodge",
        "damage": "+4",
        "cargo_loss_formula": "10 + floor((1d100 + 5) / 10) * 10"
    },
    # etc...
}
```

## Implementation Steps

### Step 1: Create Encounter Data Module (`db/encounter_data.py`)

**Purpose**: Store all encounter tables and mechanical data

**Contents**:
- [x] Encounter type probability table
- [x] **Player flavor text tables (5 types × 8 variations = 40 texts)**
- [x] Positive encounter table (10 entries)
- [x] Coincidental encounter table (10 entries)
- [x] Harmful encounter table (10 entries)
- [x] Accident table (10 entries with mechanics)
- [x] Accident mechanics lookup (damage, tests, effects)
- [x] Helper functions:
  - `get_encounter_type_from_roll(roll: int) -> str`
  - `get_random_flavor_text(encounter_type: str) -> str`
  - `get_positive_encounter_from_roll(roll: int) -> Dict`
  - `get_coincidental_encounter_from_roll(roll: int) -> Dict`
  - `get_harmful_encounter_from_roll(roll: int) -> Dict`
  - `get_accident_from_roll(roll: int) -> Dict`
  - `get_accident_mechanics(accident_type: str) -> Dict`

**Data Structure Example**:
```python
# Player flavor texts - randomly selected
POSITIVE_FLAVOR_TEXTS = [
    "The stench of the river seems... almost bearable today. How peculiar.",
    "A rare moment of peace. Suspicious, really. The gods must be planning something worse.",
    # ... 6 more variations
]

# GM detail tables - sent to notifications channel only
POSITIVE_ENCOUNTERS = {
    (1, 10): {
        "title": "Friendly Fisherfolk",
        "description": "The Characters encounter a group of friendly fisherfolk who share their catch, providing a hearty meal and good company.",
        "effects": ["Meal provided", "Morale boost"],
        "mechanics": None
    },
    (91, 100): {
        "title": "Blessed Journey",
        "description": "The Characters' journey is particularly smooth and peaceful, and they feel a sense of divine favor. They heal all Wounds and recover all Fatigued Conditions.",
        "effects": ["Heal all Wounds", "Recover all Fatigued Conditions"],
        "mechanics": {"heal_wounds": "all", "remove_conditions": ["Fatigued"]}
    },
    # ... more entries
}

ACCIDENT_ENCOUNTERS = {
    (21, 30): {
        "title": "Swinging Boom",
        "description": "A sudden crosswind causes the sail to snap round, swinging the boom across the deck...",
        "mechanics": {
            "primary_test": {
                "name": "Dodge",
                "difficulty": "Challenging (+0)",
                "target": "Characters in path"
            },
            "primary_failure": {
                "damage": "+5",
                "hits": 1
            },
            "secondary_test": {
                "name": "Athletics",
                "difficulty": "Challenging (+0)",
                "trigger": "if_hit"
            },
            "secondary_failure": {
                "effect": "knocked_into_river"
            }
        }
    },
    # ... more entries
}
```

**Estimated Size**: ~600-700 lines (increased due to flavor text tables)

---

### Step 2: Create Encounter Mechanics Module (`utils/encounter_mechanics.py`)

**Purpose**: Generate encounters and calculate mechanical effects

**Functions**:

```python
def roll_encounter_type() -> Tuple[str, int]:
    """
    Roll for encounter type.
    
    Returns:
        (encounter_type, roll_value)
    """

def generate_encounter(encounter_type: str = None) -> Dict:
    """
    Generate complete encounter based on type.
    
    Args:
        encounter_type: Optional specific type, otherwise rolls randomly
    
    Returns:
        Dict with encounter details, type, rolls, mechanics, flavor_text
    """

def get_player_flavor_text(encounter_type: str) -> str:
    """
    Get random flavor text for player message.
    
    Args:
        encounter_type: Type of encounter (positive, coincidental, etc.)
    
    Returns:
        Random grimdark flavor text string
    """

def calculate_cargo_loss() -> int:
    """
    Calculate cargo loss for Cargo Shift accident.
    Formula: 10 + floor((1d100 + 5) / 10) * 10
    
    Returns:
        Encumbrance lost
    """

def format_test_requirement(test_data: Dict) -> str:
    """
    Format test requirement for display.
    
    Args:
        test_data: Dict with test name, difficulty, target
    
    Returns:
        Formatted string like "Challenging (+0) Dodge Test (all crew)"
    """

def format_damage_result(damage: str, hits: int = 1) -> str:
    """
    Format damage for display.
    
    Args:
        damage: Damage value like "+5" or "1d10"
        hits: Number of hits
    
    Returns:
        Formatted string like "1 hit for +5 Damage"
    """

def get_encounter_emoji(encounter_type: str) -> str:
    """
    Get emoji for encounter type.
    
    Returns:
        Emoji string (✨ positive, 🎲 coincidental, 😐 uneventful, ⚔️ harmful, ⚠️ accident)
    """

def get_severity_color(encounter_type: str) -> discord.Color:
    """
    Get embed color for encounter type.
    
    Returns:
        Discord Color (green, blue, grey, orange, red)
    """
```

**Estimated Size**: ~300-400 lines

---

### Step 3: Create River Encounter Command (`commands/river_encounter.py`)

**Purpose**: Discord command implementation

**Command Signature**:
```python
@bot.tree.command(
    name="river-encounter",
    description="Generate a random river encounter for your journey"
)
@app_commands.describe(
    stage="Optional stage/time identifier (e.g., 'Day 2 Afternoon')"
)
async def river_encounter_slash(
    interaction: discord.Interaction,
    stage: str = None
):
```

**Also support prefix command**:
```python
@bot.command(name="river-encounter")
async def river_encounter_prefix(ctx, *, stage: str = None):
```

**Core Flow**:
1. Generate encounter (type + details + rolls)
2. Get random flavor text for encounter type
3. Send SHORT cryptic message to players (public response)
4. Send FULL mechanical details to #boat-travelling-notifications (GM only)

**Embed Design**:

**PLAYER MESSAGE** (Public - what players see):
```
🌫️ River Journey - Day 2 Afternoon

The stench of the river seems... almost bearable today. How peculiar.

---
Something stirs along the riverbank...
```

Or for harmful:
```
💀 River Journey - Day 2 Afternoon

Trouble. Of course there's trouble. There's always trouble on these 
thrice-damned rivers.

---
The river demands its toll...
```

Or for accident:
```
⚠️ River Journey - Day 2 Afternoon

CRACK! That didn't sound good. That didn't sound good at all.

---
Something vital fails at the worst moment...
```

**Design Notes for Player Message**:
- Short (2-4 lines max)
- Cryptic and atmospheric
- No mechanical details
- No specific encounter names
- Uses encounter type emoji
- Hints at severity without revealing details
- Grimdark WFRP tone with dark humor

**GM MESSAGE** (Notification Channel - full details):

**Simple Encounters (Positive/Coincidental/Harmful/Uneventful)**:
```
✨ River Encounter - Positive
Stage: Day 2 Afternoon (if provided)

🎣 Friendly Fisherfolk

The Characters encounter a group of friendly fisherfolk who share their catch, providing a hearty meal and good company.

Effects:
• Meal provided
• Morale boost

---
🎲 Encounter Type Roll: 7 (Positive)
🎯 Detail Roll: 5 (Friendly Fisherfolk)
```

**GM MESSAGE - Accident Encounters (Complex)**:
```
⚠️ River Accident - Day 2 Afternoon
[GM ONLY - #boat-travelling-notifications]

⚓ Swinging Boom

A sudden crosswind causes the sail to snap round, swinging the boom across the deck. Characters in the path of the boom must make a successful Challenging (+0) Dodge Test in order to avoid the swinging boom, taking one hit for +5 Damage if the Test is failed.

🎯 Required Tests:
1️⃣ Dodge Test (Challenging +0)
   • Target: Characters in path of boom
   • Failure: 1 hit for +5 Damage

2️⃣ Athletics Test (Challenging +0)
   • Trigger: If hit by boom
   • Failure: Knocked into river

⚙️ Mechanics Summary:
• Primary damage: +5
• Secondary effect: Overboard risk
• Immediate action required

---
🎲 Accident Roll: 25 (Swinging Boom)
```

**GM MESSAGE - Cargo Shift Special (with calculation)**:
```
⚠️ River Accident - Day 2 Afternoon
[GM ONLY - #boat-travelling-notifications]

📦 Cargo Shift

During a sharp turn or rough waters, the unsecured cargo shifts violently, causing potential chaos on deck.

🎯 Required Tests:
Dodge Test (Challenging +0)
   • Target: Characters in cargo area
   • Failure: 1 hit for +4 Damage

💰 Cargo Loss Calculation:
• Formula: 10 + ⌊(1d100 + 5) / 10⌋ × 10
• Roll: 67
• Calculated Loss: 80 encumbrance

⚠️ Additional Hazards:
If cargo contains hazardous materials:
• Risk of fires
• Risk of toxic spills
• Requires immediate attention

---
🎲 Accident Roll: 43 (Cargo Shift)
```

**Uneventful**:
```
😐 Uneventful Journey - Day 2 Afternoon
[GM ONLY - #boat-travelling-notifications]

The Characters travel along the river without incident. The journey continues smoothly.

---
🎲 Encounter Type Roll: 52 (Uneventful)
```

**Key Design Principle**:
- Players see ONLY cryptic flavor text (grimdark, mysterious)
- GM gets FULL mechanical details in notifications channel
- Creates tension and mystery for players
- GM has all info needed to run encounter

**Functions**:
```python
def format_player_flavor_embed(
    encounter_type: str, 
    flavor_text: str, 
    stage: str = None
) -> discord.Embed:
    """Format short cryptic message for players (public)."""

def format_gm_encounter_embed(
    encounter_data: Dict, 
    stage: str = None
) -> discord.Embed:
    """Format full mechanical details for GM (notifications channel)."""

def format_gm_accident_embed(
    accident_data: Dict, 
    stage: str = None
) -> discord.Embed:
    """Format complex accident details for GM (notifications channel)."""

def format_test_section(test_data: Dict) -> str:
    """Format test requirement section for embed."""

def format_mechanics_summary(mechanics: Dict) -> str:
    """Format quick mechanics summary."""

async def send_gm_notification(
    channel, 
    encounter_data: Dict, 
    stage: str
):
    """Send full encounter details to #boat-travelling-notifications (GM only)."""
```

**Message Flow**:
1. Command executed: `/river-encounter Day 2 Afternoon`
2. Generate encounter with all details
3. Get random flavor text for encounter type
4. **Reply to player**: Short cryptic message (public)
5. **Send to notifications**: Full mechanical details (GM only)

**Estimated Size**: ~500-600 lines

---

### Step 4: Notification Channel Integration

**IMPORTANT**: This is the PRIMARY output—GM gets full details here, players only get flavor

**GM Notification Embed Design** (for #boat-travelling-notifications):

**Simple Encounters**:
```
✨ River Encounter (Day 2 Afternoon)

Friendly Fisherfolk
Quick meal and good company provided.
```

**Accidents**:
```
⚠️ RIVER ACCIDENT (Day 2 Afternoon)

🎯 Swinging Boom

Tests Required:
• Dodge (Challenging +0) - or take +5 damage
• Athletics (Challenging +0) - or fall overboard

Immediate action needed!
```

**Cargo Loss Accidents**:
```
⚠️ CARGO ACCIDENT (Day 2 Afternoon)

📦 Cargo Shift
Lost 80 encumbrance of cargo

Test Required:
• Dodge (Challenging +0) - or take +4 damage
```

---

### Step 5: Dice Integration

**Dice Rolls Needed**:
1. Encounter type roll (1d100)
2. Encounter detail roll (1d100)
3. Cargo loss calculation (1d100 for formula)
4. Fire damage (1d10 per turn)

**Use existing dice module** (`utils/dice.py`):
```python
from utils.dice import roll_dice

# Encounter type
type_roll = roll_dice(1, 100)[0]

# Encounter detail
detail_roll = roll_dice(1, 100)[0]

# Cargo loss (for formula)
cargo_roll = roll_dice(1, 100)[0]
cargo_loss = 10 + ((cargo_roll + 5) // 10) * 10

# Fire damage
fire_damage = roll_dice(1, 10)[0]
```

---

### Step 6: Testing Strategy

**Unit Tests** (`tests/test_encounter_data.py`):
- [ ] Test encounter type ranges (1-100 coverage, no gaps)
- [ ] Test all encounter tables (10 entries each)
- [ ] Test probability distribution (10% positive, 15% coincidental, etc.)
- [ ] Test data integrity (all required fields present)
- [ ] Test accident mechanics structure
- [ ] Test helper functions (get_encounter_type_from_roll, etc.)

**Unit Tests** (`tests/test_encounter_mechanics.py`):
- [ ] Test encounter type rolling (correct distribution)
- [ ] Test encounter generation (all types)
- [ ] Test cargo loss calculation (correct formula)
- [ ] Test damage formatting
- [ ] Test test requirement formatting
- [ ] Test emoji and color selection
- [ ] Test edge cases (roll 1, roll 100)

**Integration Tests** (`tests/test_river_encounter_command.py`):
- [ ] Test command registration
- [ ] Test slash command with/without stage
- [ ] Test prefix command
- [ ] Test embed formatting (all encounter types)
- [ ] Test accident embed complexity
- [ ] Test notification channel posting
- [ ] Test error handling

**Estimated Tests**: ~40-50 tests

---

## File Structure

```
db/
  encounter_data.py          # Encounter tables and flavor texts (~600-700 lines)

utils/
  encounter_mechanics.py     # Encounter generation logic (~350-400 lines)

commands/
  river_encounter.py         # Command implementation (~500-600 lines)

tests/
  test_encounter_data.py     # Data validation tests (~150-200 lines, ~15-20 tests)
  test_encounter_mechanics.py # Mechanics logic tests (~150-200 lines, ~15-20 tests)
  test_river_encounter_command.py # Integration tests (~100-150 lines, ~10-15 tests)
```

**Total Estimated Code**: ~1,400-1,700 lines (increased due to flavor text tables and dual message system)  
**Total Estimated Tests**: ~40-50 tests

---

## User Experience Examples

### Example 1: Uneventful Journey
```
User: /river-encounter Day 3 Morning

Bot (Public - Players See):
😐 River Journey - Day 3 Morning

The river flows, you float, nothing tries to kill you. A good day by 
Reikland standards.

---
Another mile of murky water...

---

Bot (Notifications Channel - GM Only):
😐 Uneventful Journey - Day 3 Morning

The Characters travel along the river without incident. The journey 
continues smoothly.

---
🎲 Encounter Type Roll: 47 (Uneventful)
```

### Example 2: Positive Encounter
```
User: /river-encounter Day 3 Afternoon

Bot (Public - Players See):
✨ River Journey - Day 3 Afternoon

For once, the water doesn't look like it wants to kill you. Enjoy it 
while it lasts.

---
A moment of unexpected fortune...

---

Bot (Notifications Channel - GM Only):
✨ Positive Encounter - Day 3 Afternoon

🏥 Healer's Touch

The Characters meet a traveling healer who offers to tend to any 
wounds or ailments, restoring their health and vigor.

Effects:
• Wounds healed
• Ailments restored
• Party vigor refreshed

---
🎲 Encounter Type Roll: 8 (Positive)
🎯 Detail Roll: 85 (Healer's Touch)
```

### Example 3: Harmful Encounter
```
User: /river-encounter

Bot (Public - Players See):
⚔️ River Journey

Trouble. Of course there's trouble. There's always trouble on these 
thrice-damned rivers.

---
Danger approaches from the water...

---

Bot (Notifications Channel - GM Only):
⚔️ Harmful Encounter

☠️ River Pirates

The Characters are ambushed by river pirates. They must defend 
themselves or risk losing their belongings.

Combat Situation:
• Immediate combat encounter
• Risk of losing belongings
• Defense required

---
🎲 Encounter Type Roll: 88 (Harmful)
🎯 Detail Roll: 15 (River Pirates)
```

### Example 4: Simple Accident
```
User: /river-encounter Day 4 Evening

Bot (Public - Players See):
⚠️ River Journey - Day 4 Evening

Something on the boat breaks. Because of course it does. Nothing works 
properly in this forsaken land.

---
The vessel groans ominously...

---

Bot (Notifications Channel - GM Only):
⚠️ River Accident - Day 4 Evening

🔧 Broken Rigging

Some of the ropes controlling the sail break, either as a result of 
neglect or because of a sudden high wind. The boat loses speed, and 
the sail may come down, possibly snapping the top off the mast and 
bringing tackle down with it.

⚙️ Damage:
• Treat as Critical Hit to boat's rigging
• Reference: Page 29 (boat damage rules)

Immediate Effects:
• Boat loses speed
• Sail may collapse
• Mast damage risk

---
🎲 Accident Roll: 18 (Broken Rigging)
```

### Example 5: Complex Accident (Swinging Boom)
```
User: /river-encounter Day 5 Noon

Bot (Public - Players See):
⚠️ River Journey - Day 5 Noon

CRACK! That didn't sound good. That didn't sound good at all.

---
Something swings violently across the deck...

---

Bot (Notifications Channel - GM Only):
⚠️ River Accident - Day 5 Noon

⚓ Swinging Boom

A sudden crosswind causes the sail to snap round, swinging the boom 
across the deck. Characters in the path of the boom must make a 
successful Challenging (+0) Dodge Test in order to avoid the swinging 
boom, taking one hit for +5 Damage if the Test is failed.

🎯 Required Tests:

1️⃣ Dodge Test (Challenging +0)
   • Target: Characters in path of boom
   • Failure: 1 hit for +5 Damage

2️⃣ Athletics Test (Challenging +0)
   • Trigger: If hit by boom
   • Failure: Knocked into river

⚙️ Mechanics Summary:
• Primary damage: +5
• Secondary effect: Overboard risk
• Immediate action required

---
🎲 Accident Roll: 25 (Swinging Boom)
```

### Example 6: Cargo Shift (Most Complex)
```
User: /river-encounter

Bot (Public - Players See):
⚠️ River Journey

The boat protests its existence with alarming sounds. You sympathize, 
but now's not the time.

---
Cargo shifts dangerously...

---

Bot (Notifications Channel - GM Only):
⚠️ River Accident

📦 Cargo Shift

During a sharp turn or rough waters, the unsecured cargo shifts 
violently, causing potential chaos on deck.

🎯 Required Tests:
Dodge Test (Challenging +0)
   • Target: Characters in cargo area
   • Failure: 1 hit for +4 Damage

💰 Cargo Loss Calculation:
• Formula: 10 + ⌊(1d100 + 5) / 10⌋ × 10
• Roll: 67
• Result: 10 + ⌊72 / 10⌋ × 10 = 10 + 7 × 10 = 80
• Lost: 80 encumbrance

⚠️ Additional Hazards:
If cargo contains hazardous materials:
• Risk of fires
• Risk of toxic spills
• Requires immediate attention

---
🎲 Accident Roll: 43 (Cargo Shift)
🎲 Cargo Roll: 67 → 80 encumbrance lost
```

**Key Pattern**:
- **Players**: Get atmospheric, grimdark flavor (mysterious)
- **GM**: Gets full encounter name, description, mechanics, rolls

---

## Implementation Timeline

### Phase 1: Data and Mechanics (Estimated: 2 days)
**Day 1:**
- [ ] Create `db/encounter_data.py`
  - [ ] Encounter type probability table
  - [ ] Positive encounter table (10 entries)
  - [ ] Coincidental encounter table (10 entries)
  - [ ] Uneventful entry
  - [ ] Helper functions for table lookups

**Day 2:**
- [ ] Continue `db/encounter_data.py`
  - [ ] Harmful encounter table (10 entries)
  - [ ] Accident table (10 entries with full mechanics)
  - [ ] Accident mechanics data structure
- [ ] Create `utils/encounter_mechanics.py`
  - [ ] Roll functions
  - [ ] Encounter generation
  - [ ] Cargo loss calculation
  - [ ] Formatting functions

### Phase 2: Command Implementation (Estimated: 2 days)
**Day 3:**
- [ ] Create `commands/river_encounter.py`
  - [ ] Slash command registration
  - [ ] Prefix command support
  - [ ] Basic encounter embed formatting
  - [ ] Simple encounter types (positive, coincidental, uneventful, harmful)

**Day 4:**
- [ ] Continue `commands/river_encounter.py`
  - [ ] Complex accident embed formatting
  - [ ] Test requirement formatting
  - [ ] Cargo loss display
  - [ ] Mechanics summary sections
- [ ] Notification channel integration
- [ ] Integration with main bot

### Phase 3: Testing and Polish (Estimated: 1-2 days)
**Day 5:**
- [ ] Write unit tests (`test_encounter_data.py`)
- [ ] Write mechanics tests (`test_encounter_mechanics.py`)
- [ ] Write integration tests (`test_river_encounter_command.py`)
- [ ] Test all encounter types
- [ ] Test accident mechanics
- [ ] Test cargo loss calculation

**Day 6 (if needed):**
- [ ] Bug fixes
- [ ] Edge case handling
- [ ] Documentation updates
- [ ] Final testing

### Total Estimated Time: 4-6 days of development

---

## Dependencies and Requirements

### Existing Dependencies (No new packages needed)
- `discord.py` - For Discord integration
- `random` - For dice rolls
- `typing` - For type hints
- `utils.dice` - For dice rolling (already exists)

### New Files to Create
1. `db/encounter_data.py` (~600-700 lines)
   - 5 encounter type tables
   - 5 flavor text tables (8 variations each = 40 total texts)
   - Accident mechanics data
2. `utils/encounter_mechanics.py` (~350-400 lines)
   - Encounter generation
   - Flavor text selection
   - Formatting functions
3. `commands/river_encounter.py` (~500-600 lines)
   - Dual message system (player + GM)
   - Embed formatting for both outputs
4. `tests/test_encounter_data.py` (~150-200 lines)
5. `tests/test_encounter_mechanics.py` (~150-200 lines)
6. `tests/test_river_encounter_command.py` (~100-150 lines)

### Files to Modify
1. `main.py` - Register new command with `setup_river_encounter(bot)`

---

## Technical Considerations

### 1. Cargo Loss Formula Implementation
```python
def calculate_cargo_loss() -> Tuple[int, int, int]:
    """
    Calculate cargo loss using formula: 10 + floor((1d100 + 5) / 10) * 10
    
    Returns:
        (cargo_roll, calculated_loss, encumbrance_lost)
    """
    cargo_roll = roll_dice(1, 100)[0]
    intermediate = (cargo_roll + 5) // 10
    encumbrance_lost = 10 + (intermediate * 10)
    
    return cargo_roll, intermediate, encumbrance_lost

# Examples:
# Roll 67: (67 + 5) // 10 = 7  → 10 + 70 = 80 encumbrance
# Roll 5:  (5 + 5) // 10 = 1   → 10 + 10 = 20 encumbrance
# Roll 95: (95 + 5) // 10 = 10 → 10 + 100 = 110 encumbrance
```

### 2. Accident Mechanics Storage
Each accident needs to store:
- Primary test (name, difficulty, targets)
- Primary failure effect (damage/condition)
- Secondary test (if applicable)
- Secondary failure effect
- Immediate effects
- References to rules pages

### 3. Embed Complexity Levels
- **Level 1** (Uneventful): Single field, minimal info
- **Level 2** (Simple encounters): Title, description, effects list
- **Level 3** (Harmful): Title, description, effects, combat notes
- **Level 4** (Simple accidents): Title, description, damage reference
- **Level 5** (Complex accidents): Title, description, multiple tests, damage, effects, calculations

### 4. Notification Channel Logic
```python
async def send_encounter_notification(
    guild: discord.Guild,
    encounter_data: Dict,
    stage: str = None
):
    """Send full encounter details to GM notifications channel."""
    # ALL encounters send to notifications (not just harmful/accident)
    # This is where GM sees everything
    
    channel = discord.utils.get(
        guild.text_channels,
        name="boat-travelling-notifications"
    )
    
    if not channel:
        return  # Silently fail if channel doesn't exist
    
    # Create full detailed embed with ALL mechanics
    # ...
```

**Key Difference from Weather Command**:
- Weather: Details sent to BOTH player and notifications
- Encounters: Flavor to PLAYER, details ONLY to notifications

---

## Success Metrics

### Functionality Checklist
- [ ] All 5 encounter types generate correctly
- [ ] Probability distribution matches requirements (10%, 15%, 60%, 10%, 5%)
- [ ] All 40 flavor texts implemented (8 per type)
- [ ] Flavor text randomly selected for each encounter
- [ ] All 10 positive encounters implemented
- [ ] All 10 coincidental encounters implemented
- [ ] All 10 harmful encounters implemented
- [ ] All 10 accident encounters with full mechanics
- [ ] Cargo loss formula calculates correctly
- [ ] Tests display correctly with difficulty and targets
- [ ] Damage displays correctly
- [ ] **Player messages show only flavor text (cryptic, grimdark)**
- [ ] **GM messages show full mechanics in notifications channel**
- [ ] **Dual message system works (player public, GM notifications)**
- [ ] Embeds format properly for both outputs
- [ ] Notifications send to correct channel for ALL encounters
- [ ] Stage parameter works (optional)
- [ ] Both slash and prefix commands work
- [ ] All tests passing (40-50 tests)

### Quality Checklist
- [ ] Code follows existing patterns (similar to weather command)
- [ ] Error handling for invalid inputs
- [ ] Graceful degradation if notification channel missing
- [ ] Clear, readable embeds with good formatting
- [ ] Helpful roll information displayed
- [ ] Consistent emoji usage
- [ ] Consistent color coding
- [ ] All functions documented
- [ ] Type hints used throughout
- [ ] No hardcoded magic numbers

---

## Future Enhancements (Out of Scope)

1. **Encounter History**: Track past encounters for a journey
2. **Weighted Encounters**: Adjust probabilities based on location/weather
3. **Character-Specific Effects**: Target specific characters in accidents
4. **Boat Damage Tracking**: Track cumulative damage from accidents
5. **Encounter Chains**: Link related encounters together
6. **Custom Encounters**: GMs can add custom encounter tables
7. **Encounter Resolution**: Track whether encounter was resolved
8. **Integration with Weather**: Weather affects encounter chances
9. **Integration with Boat Handling**: Boat handling skill affects accident outcomes
10. **Cargo Tracking**: Track actual cargo and what was lost

---

## Questions Before Implementation

1. **Boat Damage Rules**: Do we need to implement full boat damage tracking, or just reference page 29?
   - **Recommendation**: Just reference for now, implement damage tracking later

2. **Character Selection**: For targeted accidents (swinging boom, man overboard), should we:
   - Ask user to specify affected characters?
   - Randomly select from party?
   - Leave it to GM discretion?
   - **Recommendation**: Leave to GM discretion, display "Characters in path" generically

3. **Test Resolution**: Should the bot track test results, or just display requirements?
   - **Recommendation**: Just display requirements, actual rolling done separately

4. **Cargo Management**: Should we track cargo inventory?
   - **Recommendation**: No, just display encumbrance lost, GM tracks actual cargo

5. **Multiple Accidents**: Should "Sudden Squall" potentially trigger other accidents?
   - **Recommendation**: Display note about "may trigger multiple accidents", leave execution to GM

6. **Notification Channel**: Should all encounters notify, or just harmful/accident?
   - **Recommendation**: Only harmful and accident types

7. **Stage Tracking**: Should we store stage/journey information?
   - **Recommendation**: No, stage is just a label for current encounter

---

## Notes

- Keep encounters descriptive but concise
- Emphasize mechanical effects clearly
- Use visual separators (emojis, lines) to organize complex information
- Accident embeds should be easy to scan for tests and damage
- Cargo loss calculation should show the formula and steps
- Reference page numbers when needed (but don't implement full rules)
- Tests should be displayed clearly with difficulty and target
- Keep notification embeds brief and actionable

---

## Implementation Priority

### Must Have (MVP)
1. All 5 encounter type rolls working
2. All encounter detail tables complete
3. Basic embeds for all types
4. Accident mechanics displayed correctly
5. Cargo loss calculation working

### Should Have
1. Notification channel integration
2. Stage parameter
3. Complex accident formatting
4. Roll information display
5. Full test suite

### Nice to Have
1. Emoji customization
2. Color coding by severity
3. Detailed mechanics breakdowns
4. Formula display for cargo loss
5. Multiple test sequencing display

---

## Validation Before Launch

- [ ] Run all 40-50 tests
- [ ] Test each encounter type manually in Discord
- [ ] Test cargo loss calculation with various rolls
- [ ] Verify notification channel posting
- [ ] Verify embeds display correctly on mobile
- [ ] Test with and without stage parameter
- [ ] Test prefix and slash commands
- [ ] Verify existing commands still work (247 tests)
- [ ] Check for any performance issues
- [ ] Verify all 10 accidents display mechanics correctly

---

## Ready for Implementation? ✅

This plan provides:
- ✅ Complete data structure design
- ✅ Clear implementation steps
- ✅ Detailed embed designs
- ✅ Testing strategy
- ✅ Timeline estimate
- ✅ Technical considerations
- ✅ Success metrics

**Estimated Total**: 4-6 days, ~1,200-1,500 lines of code, 40-50 tests

Ready to proceed with implementation when approved!
