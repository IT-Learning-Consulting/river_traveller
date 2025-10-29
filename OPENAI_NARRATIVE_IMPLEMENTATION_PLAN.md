# OpenAI Narrative Integration - Complete Implementation Plan

## 📋 Executive Summary

This document provides a comprehensive implementation plan for integrating OpenAI's API to transform weather system data into narrative text for the WFRP Discord bot. The system will implement a three-channel architecture where players receive AI-generated atmospheric narratives, GMs receive mechanics notifications (unchanged), and a log channel stores machine-readable JSON data.

**Document Version:** 1.0  
**Last Updated:** October 29, 2025  
**Target Completion:** TBD

---

## 🎯 Project Goals

### Primary Objectives
1. **JSON Serialization Infrastructure** - Create structured JSON representations of all weather data
2. **Three-Channel System** - Implement player (narrative), GM (mechanics), and log (JSON) channels
3. **OpenAI Integration** - Generate atmospheric narrative text from weather data
4. **Zero Breaking Changes** - Maintain all existing functionality during implementation
5. **Comprehensive Testing** - Ensure system reliability and prevent regressions

### Success Criteria
- ✅ JSON data appears in log channel (`boat-travelling-log`)
- ✅ GM channel (`boat-travelling-notifications`) remains unchanged with mechanics only
- ✅ Player channel shows current embed during Phases 1-3, then narrative in Phase 4
- ✅ All existing tests pass without modification
- ✅ New tests achieve >90% coverage for new code
- ✅ OpenAI narratives are contextually appropriate and immersive
- ✅ System gracefully degrades if OpenAI API is unavailable

---

## 🏗️ System Architecture Analysis

### Current Weather System Components

#### 1. **Data Layer** (`db/`)
- **`weather_data.py`** - Static weather tables (wind, temperature, effects)
- **`weather_storage.py`** - SQLite persistence for journeys and daily weather
- **Database Schema:**
  - `guild_weather_state` - Journey configuration per guild
  - `daily_weather` - Weather records for each day

#### 2. **Business Logic** (`utils/`)
- **`weather_mechanics.py`** - Weather generation algorithms
- **`modifier_calculator.py`** - Extracts modifiers for boat handling tests

#### 3. **Command Layer** (`commands/`)
- **`weather.py`** - Discord command handlers
  - `/weather next` - Generate next day
  - `/weather next-stage` - Generate multi-day stage
  - `/weather view` - View historical day
  - `/weather journey` - Start new journey
  - `/weather override` - GM manual override
  - `/weather-stage-config` - Configure stage settings

#### 4. **Presentation Layer**
- **Display Functions:**
  - `_display_weather()` - Single day detailed view
  - `_display_stage_summary()` - Multi-day summary
  - `_display_stage_detailed()` - Multi-day detailed view
- **Notification System:**
  - `send_mechanics_notification()` - Sends to `boat-travelling-notifications`

### Current Channel System

The bot currently uses **two channels**:

1. **Player Channel** - Where `/weather` command is invoked
   - Shows rich Discord embed with all weather details
   
2. **GM Notifications Channel** (`boat-travelling-notifications`)
   - Receives mechanics summary via `send_mechanics_notification()`
   - Shows boat handling modifiers, weather penalties, temperature notes

### Existing Multi-Channel Pattern Reference

The bot **already implements** a multi-channel system in `river_encounter.py`:

```python
# Player gets cryptic flavor text
player_embed = format_player_flavor_embed(encounter_data["type"], encounter_data["flavor_text"])
await interaction.response.send_message(embed=player_embed)

# GM gets detailed mechanics
await send_gm_notification(guild, encounter_data, stage)
```

**Key Insight:** We will extend this pattern by adding a third log channel for JSON data.

---

## 🎭 Three-Channel Architecture

### Channel Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    /weather next Command                         │
└──────────────────────┬──────────────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┬────────────────────────┐
        │                             │                        │
        ▼                             ▼                        ▼
┌───────────────┐         ┌───────────────────┐    ┌────────────────────┐
│ PLAYER        │         │ GM NOTIFICATIONS  │    │ LOG CHANNEL        │
│ CHANNEL       │         │ CHANNEL           │    │                    │
│               │         │                   │    │ boat-travelling-   │
│ (where        │         │ boat-travelling-  │    │ log                │
│ command       │         │ notifications     │    │                    │
│ invoked)      │         │                   │    │                    │
├───────────────┤         ├───────────────────┤    ├────────────────────┤
│               │         │                   │    │                    │
│ Phase 1-3:    │         │ UNCHANGED:        │    │ Phase 2+:          │
│ Rich embed    │         │ • Boat handling   │    │ JSON weather data  │
│ (current)     │         │   modifiers       │    │ for OpenAI         │
│               │         │ • Wind penalties  │    │ processing         │
│ Phase 4:      │         │ • Weather effects │    │                    │
│ AI narrative  │         │ • Temperature     │    │ Debugging &        │
│ (replaces     │         │                   │    │ verification       │
│ embed)        │         │ NO JSON added     │    │                    │
│               │         │                   │    │                    │
└───────────────┘         └───────────────────┘    └────────────────────┘
```

### Channel Responsibilities

| Channel | Name | Purpose | Content | Changes |
|---------|------|---------|---------|---------|
| **Player** | *(command channel)* | Main weather display | Rich embed → AI narrative | Phase 4 |
| **GM** | `boat-travelling-notifications` | Mechanics for GM | Boat modifiers, penalties | **NONE** |
| **Log** | `boat-travelling-log` | Machine-readable data | JSON for OpenAI + debugging | Phase 2 (NEW) |

### Phase-by-Phase Channel Evolution

**Phase 1:** JSON creation only (no channel changes)
- Player: Embed (unchanged)
- GM: Mechanics (unchanged)
- Log: *(doesn't exist yet)*

**Phase 2:** Add log channel
- Player: Embed (unchanged)
- GM: Mechanics (unchanged)
- Log: JSON data ✨ **NEW**

**Phase 3:** OpenAI integration prep
- Player: Embed (unchanged)
- GM: Mechanics (unchanged)
- Log: JSON data (unchanged)

**Phase 4:** Narrative display
- Player: AI narrative ✨ **CHANGED**
- GM: Mechanics (unchanged)
- Log: JSON data (unchanged)

---

## 📊 Phase-by-Phase Implementation Plan

---

## **PHASE 1: JSON Serialization Infrastructure**
**Goal:** Create structured JSON representations of weather data  
**Duration:** 1-2 days  
**Risk Level:** 🟢 Low

### 1.1 Create Weather JSON Serializer

**New File:** `utils/weather_serializer.py`

#### JSON Schema Design

```json
{
  "day": 1,
  "stage": 1,
  "season": "summer",
  "province": "reikland",
  "wind": {
    "dawn": {
      "strength": "light",
      "direction": "tailwind",
      "speed_modifier": "+5%",
      "boat_handling_penalty": 0,
      "requires_tacking": true,
      "changed": false
    },
    "midday": { /* same structure */ },
    "dusk": { /* same structure */ },
    "midnight": { /* same structure */ }
  },
  "weather": {
    "type": "fair",
    "name": "Fair",
    "description": "For once, the weather is being kind...",
    "effects": ["No weather-related hazards"]
  },
  "temperature": {
    "actual": 21,
    "perceived": 16,
    "base": 21,
    "category": "average",
    "description": "Comfortable for the season",
    "wind_chill_applied": true
  },
  "special_events": {
    "cold_front": {
      "active": false,
      "days_remaining": 0
    },
    "heat_wave": {
      "active": false,
      "days_remaining": 0
    }
  },
  "metadata": {
    "generated_at": "2025-10-29T14:30:00Z",
    "generated_by": "User#1234",
    "is_override": false,
    "continuity_from_previous_day": true
  }
}
```

#### Function Signatures

```python
def serialize_daily_weather(
    day: int,
    season: str,
    province: str,
    wind_timeline: list,
    weather_type: str,
    weather_effects: dict,
    actual_temp: int,
    perceived_temp: int,
    base_temp: int,
    temp_category: str,
    temp_description: str,
    cold_front_days: int,
    heat_wave_days: int,
    continuity_note: str = None,
    generated_by: str = None,
    is_override: bool = False,
    stage: int = None
) -> dict:
    """
    Serialize daily weather into structured JSON.
    
    Args:
        day: Day number in journey
        season: Season name
        province: Province name
        wind_timeline: List of wind conditions for 4 time periods
        weather_type: Weather condition key
        weather_effects: Weather effects dict from weather_data
        actual_temp: Actual temperature in Celsius
        perceived_temp: Temperature with wind chill applied
        base_temp: Average temperature for season/province
        temp_category: Temperature category key
        temp_description: Human-readable temperature description
        cold_front_days: Days remaining in cold front
        heat_wave_days: Days remaining in heat wave
        continuity_note: Optional continuity note
        generated_by: Discord username
        is_override: Whether this is a GM override
        stage: Optional stage number
        
    Returns:
        Dictionary matching JSON schema
    """
```

```python
def serialize_stage_weather(
    stage_num: int,
    start_day: int,
    stage_duration: int,
    season: str,
    province: str,
    stage_weathers: list,
    generated_by: str = None
) -> dict:
    """
    Serialize multi-day stage weather into structured JSON.
    
    Args:
        stage_num: Stage number
        start_day: First day of stage
        stage_duration: Number of days in stage
        season: Season name
        province: Province name
        stage_weathers: List of (day_num, weather_data) tuples
        generated_by: Discord username
        
    Returns:
        Dictionary with stage summary and daily weather array
    """
```

### 1.2 Testing Strategy for Phase 1

**New File:** `tests/test_weather_serializer.py`

#### Test Cases

```python
class TestWeatherSerializer:
    def test_serialize_daily_weather_structure()
    def test_serialize_daily_weather_all_fields_present()
    def test_serialize_daily_weather_calm_wind()
    def test_serialize_daily_weather_with_cold_front()
    def test_serialize_daily_weather_with_heat_wave()
    def test_serialize_daily_weather_wind_chill()
    def test_serialize_daily_weather_no_continuity()
    def test_serialize_daily_weather_with_continuity()
    def test_serialize_daily_weather_gm_override()
    
class TestStageWeatherSerializer:
    def test_serialize_stage_weather_structure()
    def test_serialize_stage_weather_multiple_days()
    def test_serialize_stage_weather_summary_accuracy()
    
class TestJSONValidity:
    def test_json_serializable()
    def test_json_round_trip()
    def test_json_schema_validation()
```

**Estimated Tests:** 15-20  
**Coverage Target:** >95%

### 1.3 Integration Points

**Files to Modify:**
- **`commands/weather.py`**
  - Import `weather_serializer`
  - Update `_display_weather()` to generate JSON
  - Update `_display_stage_summary()` to generate JSON
  - Update `_display_stage_detailed()` to generate JSON

**Changes Required:**
```python
# In _display_weather() after line 357
from utils.weather_serializer import serialize_daily_weather

# After calculating all values, before creating embed:
weather_json = serialize_daily_weather(
    day=day,
    season=season,
    province=province,
    wind_timeline=wind_timeline,
    weather_type=weather_type,
    weather_effects=weather_effects,
    actual_temp=actual_temp,
    perceived_temp=perceived_temp,
    base_temp=base_temp,
    temp_category=_temp_category,
    temp_description=temp_description,
    cold_front_days=cold_front_days,
    heat_wave_days=heat_wave_days,
    continuity_note=continuity_note,
    generated_by=context.user.display_name if is_slash else context.author.display_name,
    is_override=False
)
```

---

## **PHASE 2: Three-Channel JSON Output**
**Goal:** Send JSON to new log channel for OpenAI consumption  
**Duration:** 1 day  
**Risk Level:** 🟢 Low

### 2.1 Create Weather Log Notification Function

**File:** `commands/weather.py`

```python
async def send_weather_log(
    guild: discord.Guild,
    weather_json: dict,
    notification_type: str = "daily"
) -> bool:
    """
    Send weather JSON to log channel for debugging and OpenAI processing.
    
    Args:
        guild: Discord guild
        weather_json: Serialized weather data
        notification_type: 'daily', 'stage_summary', or 'stage_detailed'
        
    Returns:
        True if log sent, False otherwise
    """
    # Find log channel
    channel = discord.utils.get(
        guild.text_channels, name="boat-travelling-log"
    )
    
    if not channel:
        return False
    
    # Create embed with JSON in code block
    embed = discord.Embed(
        title=f"📊 Weather Data (Day {weather_json['day']})",
        description="Machine-readable weather data for OpenAI processing",
        color=discord.Color.blue()
    )
    
    # Add summary
    embed.add_field(
        name="Summary",
        value=f"**{weather_json['season'].title()}** in **{weather_json['province'].replace('_', ' ').title()}**",
        inline=False
    )
    
    # Add JSON in code block (formatted)
    json_str = json.dumps(weather_json, indent=2)
    
    # Discord has 1024 char limit per field, split if needed
    if len(json_str) <= 1018:  # Leave room for ```json and ```
        embed.add_field(
            name="JSON Data",
            value=f"```json\n{json_str}\n```",
            inline=False
        )
    else:
        # Send as file attachment instead
        json_file = discord.File(
            io.StringIO(json_str),
            filename=f"weather_day_{weather_json['day']}.json"
        )
        await channel.send(embed=embed, file=json_file)
        return True
    
    await channel.send(embed=embed)
    return True
```

### 2.2 Update Display Functions

**Changes to `_display_weather()`:**

```python
async def _display_weather(
    context,
    day: int,
    # ... existing parameters ...
):
    # Existing embed creation code (UNCHANGED)
    # Player sees the same rich embed as before
    
    # NEW: Generate JSON
    weather_json = serialize_daily_weather(
        day=day,
        season=season,
        province=province,
        # ... all parameters ...
    )
    
    # NEW: Send to log channel
    if context.guild:
        await send_weather_log(
            context.guild,
            weather_json,
            notification_type="daily"
        )
    
    # Existing embed send code (UNCHANGED)
    # Existing mechanics notification (UNCHANGED)
```

**Changes to `_display_stage_summary()` and `_display_stage_detailed()`:**

```python
# After generating stage embed, before sending:
stage_json = serialize_stage_weather(
    stage_num=stage_num,
    start_day=start_day,
    stage_duration=stage_duration,
    season=season,
    province=province,
    stage_weathers=stage_weathers,
    generated_by=context.user.display_name if is_slash else context.author.display_name
)

if context.guild:
    await send_weather_log(
        context.guild,
        stage_json,
        notification_type="stage_summary"  # or "stage_detailed"
    )
```

**Important:** The existing `send_mechanics_notification()` function remains **completely unchanged**. The GM channel continues to receive only mechanics data as it does now.

### 2.3 Testing Strategy for Phase 2

**New File:** `tests/test_weather_json_output.py`

#### Test Cases

```python
class TestLogChannelNotifications:
    def test_log_channel_exists()
    def test_log_channel_not_exists()
    def test_log_notification_json_format()
    def test_log_notification_embed_structure()
    def test_log_notification_large_json_as_file()
    
class TestWeatherCommandJSONOutput:
    def test_weather_next_sends_json()
    def test_weather_next_stage_sends_json()
    def test_weather_view_sends_json()
    def test_weather_override_sends_json()
    
class TestJSONAccuracy:
    def test_json_matches_display_data()
    def test_json_wind_modifiers_correct()
    def test_json_temperature_calculations_correct()
    
class TestChannelIsolation:
    def test_gm_channel_unchanged()
    def test_player_channel_shows_embed()
    def test_log_channel_receives_json()
```

**Estimated Tests:** 15-18  
**Coverage Target:** >90%

### 2.4 Verification Steps

1. **Manual Testing:**
   - Run `/weather next` and verify:
     - Player channel: Rich embed (unchanged)
     - GM channel (`boat-travelling-notifications`): Mechanics only (unchanged)
     - Log channel (`boat-travelling-log`): JSON data
   - Run `/weather next-stage` and verify stage JSON appears in log channel
   - Verify three-channel separation is working correctly

2. **Regression Testing:**
   - Run full test suite: `pytest tests/ -v`
   - Verify all existing tests pass
   - Check code coverage: `pytest --cov=. --cov-report=html`

---

## **PHASE 3: OpenAI Integration Preparation**
**Goal:** Set up infrastructure for OpenAI API (without enabling)  
**Duration:** 2 days  
**Risk Level:** 🟡 Medium

### 3.1 Environment Configuration

**File:** `.env` (create if not exists)

```env
# Discord Bot Configuration
DISCORD_TOKEN=your_token_here

# OpenAI Configuration
OPENAI_API_KEY=sk-...your-key-here
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=500
OPENAI_TEMPERATURE=0.8

# Narrative System Configuration
NARRATIVE_ENABLED=false
NARRATIVE_CACHE_ENABLED=true
NARRATIVE_CACHE_TTL=3600
```

**File:** `requirements.txt` (add OpenAI)

```txt
discord.py
python-dotenv
flask
pytest
coverage
pytest-cov
openai>=1.0.0
```

### 3.2 Create OpenAI Service Module

**New File:** `utils/narrative_generator.py`

```python
"""
OpenAI API integration for generating weather narratives.

This module handles all OpenAI API calls, prompt construction,
error handling, and response parsing.
"""

import os
import openai
import json
from typing import Optional, Dict
from dotenv import load_dotenv

load_dotenv()


class NarrativeGenerator:
    """Handles OpenAI API calls for weather narrative generation."""
    
    def __init__(self):
        """Initialize OpenAI client with API key from environment."""
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "500"))
        self.temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.8"))
        self.enabled = os.getenv("NARRATIVE_ENABLED", "false").lower() == "true"
        
        if self.api_key:
            openai.api_key = self.api_key
        
    def is_enabled(self) -> bool:
        """Check if narrative generation is enabled."""
        return self.enabled and self.api_key is not None
    
    def generate_daily_narrative(
        self,
        weather_json: Dict,
        character_context: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate atmospheric narrative for a single day's weather.
        
        Args:
            weather_json: Serialized weather data
            character_context: Optional context about party (for future use)
            
        Returns:
            Generated narrative text or None if failed
        """
        if not self.is_enabled():
            return None
        
        try:
            prompt = self._build_daily_prompt(weather_json, character_context)
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT_DAILY
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                n=1
            )
            
            narrative = response.choices[0].message.content.strip()
            return narrative
            
        except openai.OpenAIError as e:
            print(f"OpenAI API error: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error in narrative generation: {e}")
            return None
    
    def generate_stage_narrative(
        self,
        stage_json: Dict,
        character_context: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate atmospheric narrative for a multi-day stage.
        
        Args:
            stage_json: Serialized stage weather data
            character_context: Optional context about party
            
        Returns:
            Generated narrative text or None if failed
        """
        if not self.is_enabled():
            return None
        
        try:
            prompt = self._build_stage_prompt(stage_json, character_context)
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT_STAGE
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.max_tokens * 2,  # Longer for multi-day
                temperature=self.temperature,
                n=1
            )
            
            narrative = response.choices[0].message.content.strip()
            return narrative
            
        except openai.OpenAIError as e:
            print(f"OpenAI API error: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error in narrative generation: {e}")
            return None
    
    def _build_daily_prompt(
        self,
        weather_json: Dict,
        character_context: Optional[str]
    ) -> str:
        """Build prompt for daily weather narrative."""
        from utils.narrative_prompts import build_daily_prompt
        return build_daily_prompt(weather_json, character_context)
    
    def _build_stage_prompt(
        self,
        stage_json: Dict,
        character_context: Optional[str]
    ) -> str:
        """Build prompt for stage weather narrative."""
        from utils.narrative_prompts import build_stage_prompt
        return build_stage_prompt(stage_json, character_context)
    
    def test_connection(self) -> bool:
        """
        Test OpenAI API connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        if not self.api_key:
            return False
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": "Test"}
                ],
                max_tokens=5
            )
            return True
        except openai.OpenAIError:
            return False


# System prompts (detailed prompts in narrative_prompts.py)
SYSTEM_PROMPT_DAILY = """You are a narrative generator for a Warhammer Fantasy Roleplay river travel campaign. 
Your task is to transform weather data into atmospheric, immersive narrative text that captures the grim and perilous 
tone of the Warhammer world. Focus on sensory details and environmental storytelling. Keep narratives concise (2-3 paragraphs)."""

SYSTEM_PROMPT_STAGE = """You are a narrative generator for a Warhammer Fantasy Roleplay river travel campaign.
Your task is to transform multi-day weather data into an atmospheric summary that captures the journey's progression.
Maintain the grim and perilous tone of the Warhammer world. Keep narratives concise (3-4 paragraphs)."""
```

### 3.3 Create Prompt Templates Module

**New File:** `utils/narrative_prompts.py`

```python
"""
Prompt templates for OpenAI narrative generation.

This module contains all prompt construction logic, making it easy
to iterate on prompt engineering without touching the API code.
"""

from typing import Dict, Optional


def build_daily_prompt(
    weather_json: Dict,
    character_context: Optional[str] = None
) -> str:
    """
    Build prompt for daily weather narrative generation.
    
    Args:
        weather_json: Serialized weather data
        character_context: Optional party context
        
    Returns:
        Formatted prompt string
    """
    day = weather_json['day']
    season = weather_json['season'].title()
    province = weather_json['province'].replace('_', ' ').title()
    
    # Extract weather details
    weather_name = weather_json['weather']['name']
    weather_desc = weather_json['weather']['description']
    temp_actual = weather_json['temperature']['actual']
    temp_perceived = weather_json['temperature']['perceived']
    temp_description = weather_json['temperature']['description']
    
    # Extract wind details (focus on most impactful times)
    dawn_wind = weather_json['wind']['dawn']
    dusk_wind = weather_json['wind']['dusk']
    
    # Special events
    cold_front = weather_json['special_events']['cold_front']['active']
    heat_wave = weather_json['special_events']['heat_wave']['active']
    
    # Build prompt
    prompt = f"""Generate an atmospheric weather narrative for Day {day} of a river journey.

**Setting:**
- Season: {season}
- Region: {province}
- Journey Context: Traveling by boat along the River Reik

**Weather Conditions:**
- Overall: {weather_name} - {weather_desc}
- Temperature: {temp_actual}°C (feels like {temp_perceived}°C) - {temp_description}
- Wind at Dawn: {dawn_wind['strength'].title()} {dawn_wind['direction'].title()}
- Wind at Dusk: {dusk_wind['strength'].title()} {dusk_wind['direction'].title()}
"""
    
    if cold_front:
        days_remaining = weather_json['special_events']['cold_front']['days_remaining']
        prompt += f"- **Special Event:** Cold front (Day {4 - days_remaining} of 3+) - Bitter cold persists\n"
    
    if heat_wave:
        days_remaining = weather_json['special_events']['heat_wave']['days_remaining']
        prompt += f"- **Special Event:** Heat wave (Day {4 - days_remaining} of 3+) - Oppressive heat continues\n"
    
    prompt += """
**Narrative Requirements:**
1. Write from the perspective of someone experiencing the journey
2. Focus on sensory details (what you see, hear, feel)
3. Maintain Warhammer Fantasy's grim, dark tone
4. Mention how conditions affect the river travel specifically
5. Keep it concise: 2-3 short paragraphs
6. Do NOT include mechanical game effects or dice rolls
7. Do NOT use quotes or dialogue
8. Write in present tense

**Example Style:**
"The morning mist clings to the Reik like a shroud, obscuring the far bank. A light wind ruffles the water's surface, carrying the scent of damp earth and distant smoke. The boat glides downstream with ease, though the crew remains vigilant—the Old World is never truly safe, even on calm waters."

Generate the narrative:"""
    
    return prompt


def build_stage_prompt(
    stage_json: Dict,
    character_context: Optional[str] = None
) -> str:
    """
    Build prompt for multi-day stage narrative generation.
    
    Args:
        stage_json: Serialized stage weather data
        character_context: Optional party context
        
    Returns:
        Formatted prompt string
    """
    stage_num = stage_json['stage']
    start_day = stage_json['start_day']
    end_day = stage_json['end_day']
    days_count = stage_json['days_count']
    season = stage_json['season'].title()
    province = stage_json['province'].replace('_', ' ').title()
    
    # Summarize weather progression
    daily_summaries = []
    for day_data in stage_json['days']:
        day_num = day_data['day']
        weather = day_data['weather']['name']
        temp = day_data['temperature']['actual']
        daily_summaries.append(f"  - Day {day_num}: {weather}, {temp}°C")
    
    weather_summary = "\n".join(daily_summaries)
    
    prompt = f"""Generate an atmospheric narrative summary for Stage {stage_num} of a river journey (Days {start_day}-{end_day}).

**Setting:**
- Season: {season}
- Region: {province}
- Duration: {days_count} days of river travel

**Weather Progression:**
{weather_summary}

**Narrative Requirements:**
1. Summarize the {days_count}-day journey as a cohesive experience
2. Highlight weather transitions and their impact on travel
3. Maintain Warhammer Fantasy's grim atmosphere
4. Focus on the cumulative effect of conditions on crew morale
5. Keep it concise: 3-4 short paragraphs
6. Do NOT include mechanical game effects
7. Write in past tense (describing what happened)

Generate the narrative:"""
    
    return prompt


def get_fallback_narrative(weather_json: Dict, narrative_type: str = "daily") -> str:
    """
    Generate a simple fallback narrative if OpenAI is unavailable.
    
    Args:
        weather_json: Weather data
        narrative_type: 'daily' or 'stage'
        
    Returns:
        Basic narrative text
    """
    if narrative_type == "daily":
        weather = weather_json['weather']['name']
        temp = weather_json['temperature']['actual']
        wind = weather_json['wind']['midday']['strength'].title()
        
        return (
            f"Day {weather_json['day']} brings {weather.lower()} weather. "
            f"The temperature sits at {temp}°C, with {wind.lower()} winds "
            f"accompanying your journey down the Reik. The crew makes steady progress."
        )
    else:
        # Stage fallback
        return (
            f"Over the course of {weather_json['days_count']} days, the party "
            f"navigates the changing conditions of {weather_json['season']} in "
            f"{weather_json['province'].replace('_', ' ').title()}. Despite the challenges, "
            f"they press onward."
        )
```

### 3.4 Testing Strategy for Phase 3

**New File:** `tests/test_narrative_generator.py`

```python
class TestNarrativeGenerator:
    def test_initialization()
    def test_is_enabled_with_key()
    def test_is_enabled_without_key()
    def test_is_enabled_flag_false()
    def test_generate_daily_narrative_disabled()
    def test_generate_stage_narrative_disabled()
    
class TestPromptConstruction:
    def test_build_daily_prompt_structure()
    def test_build_daily_prompt_includes_all_data()
    def test_build_daily_prompt_cold_front()
    def test_build_daily_prompt_heat_wave()
    def test_build_stage_prompt_structure()
    def test_build_stage_prompt_multiple_days()
    
class TestFallbackNarratives:
    def test_fallback_daily_narrative()
    def test_fallback_stage_narrative()
    def test_fallback_contains_key_data()
```

**Note:** Testing actual OpenAI API calls requires mocking. Use `unittest.mock` or `pytest-mock`:

```python
@patch('openai.ChatCompletion.create')
def test_generate_daily_narrative_success(mock_create):
    mock_create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="Generated narrative"))]
    )
    generator = NarrativeGenerator()
    # Set enabled=True for testing
    generator.enabled = True
    generator.api_key = "test-key"
    
    result = generator.generate_daily_narrative(sample_weather_json)
    assert result == "Generated narrative"
```

**Estimated Tests:** 20-25  
**Coverage Target:** >85%

---

## **PHASE 4: OpenAI Narrative Display (Player Channel Replacement)**
**Goal:** Replace player channel embeds with AI narratives when enabled  
**Duration:** 2-3 days  
**Risk Level:** 🟠 High

### 4.1 Configuration Management

**Update:** `.env`

```env
NARRATIVE_ENABLED=true  # Enable this to activate narratives
NARRATIVE_FALLBACK_TO_EMBED=true  # Show embed if generation fails
NARRATIVE_SHOW_DEBUG_INFO=false  # Show JSON in player channel for debugging
```

### 4.2 Channel Flow Overview

When `NARRATIVE_ENABLED=true`:

1. **Player Channel** - AI-generated narrative (replaces embed)
2. **GM Channel** (`boat-travelling-notifications`) - Mechanics only (unchanged)
3. **Log Channel** (`boat-travelling-log`) - JSON data (unchanged)

When `NARRATIVE_ENABLED=false`:

1. **Player Channel** - Rich embed (current behavior)
2. **GM Channel** - Mechanics only (unchanged)
3. **Log Channel** - JSON data (unchanged)

### 4.3 Update Display Functions

**File:** `commands/weather.py`

```python
from utils.narrative_generator import NarrativeGenerator
from utils.narrative_prompts import get_fallback_narrative

async def _display_weather(
    context,
    day: int,
    # ... existing parameters ...
):
    # Generate JSON (Phase 1)
    weather_json = serialize_daily_weather(...)
    
    # Send to log channel (Phase 2)
    if context.guild:
        await send_weather_log(context.guild, weather_json, "daily")
    
    # Send to GM channel (existing, unchanged)
    temp_feel_text = get_temperature_description_text(actual_temp, base_temp)
    await send_mechanics_notification(
        context, season, province, wind_timeline,
        weather_effects, temp_feel_text
    )
    
    # NEW: Check if narrative mode is enabled
    generator = NarrativeGenerator()
    
    if generator.is_enabled():
        # Generate narrative for PLAYER CHANNEL
        narrative = generator.generate_daily_narrative(weather_json)
        
        if narrative:
            # Send narrative to player channel (replaces embed)
            await _send_narrative_message(context, narrative, weather_json, is_slash)
        elif os.getenv("NARRATIVE_FALLBACK_TO_EMBED", "true").lower() == "true":
            # Fallback to embed if generation fails
            await _send_weather_embed(context, embed, is_slash)
        else:
            # Use simple fallback narrative
            fallback = get_fallback_narrative(weather_json, "daily")
            await _send_narrative_message(context, fallback, weather_json, is_slash)
    else:
        # Original embed system (unchanged) for PLAYER CHANNEL
        await _send_weather_embed(context, embed, is_slash)


async def _send_narrative_message(
    context,
    narrative: str,
    weather_json: dict,
    is_slash: bool
):
    """
    Send AI-generated narrative to PLAYER CHANNEL (where command was invoked).
    
    Args:
        context: Discord context
        narrative: Generated narrative text
        weather_json: Weather data for footer
        is_slash: Slash command flag
    """
    embed = discord.Embed(
        title=f"🌊 Day {weather_json['day']} - {weather_json['season'].title()} in {weather_json['province'].replace('_', ' ').title()}",
        description=narrative,
        color=discord.Color.blue()
    )
    
    # Add minimal footer with key info
    footer_text = f"🌡️ {weather_json['temperature']['actual']}°C"
    if weather_json['special_events']['cold_front']['active']:
        footer_text += " | ❄️ Cold Front"
    if weather_json['special_events']['heat_wave']['active']:
        footer_text += " | 🔥 Heat Wave"
    
    embed.set_footer(text=footer_text)
    
    # Optional: Show JSON for debugging (remove in production)
    if os.getenv("NARRATIVE_SHOW_DEBUG_INFO", "false").lower() == "true":
        json_str = json.dumps(weather_json, indent=2)
        if len(json_str) <= 1000:
            embed.add_field(
                name="🔍 Debug: Source JSON",
                value=f"```json\n{json_str}\n```",
                inline=False
            )
    
    if is_slash:
        await context.response.send_message(embed=embed)
    else:
        await context.send(embed=embed)


async def _send_weather_embed(context, embed: discord.Embed, is_slash: bool):
    """Send traditional weather embed to PLAYER CHANNEL (fallback mode)."""
    if is_slash:
        if hasattr(context, "response") and not context.response.is_done():
            await context.response.send_message(embed=embed)
        else:
            await context.followup.send(embed=embed)
    else:
        await context.send(embed=embed)
```
```

### 4.4 Caching System (Performance Optimization)

**New File:** `utils/narrative_cache.py`

```python
"""
Simple in-memory cache for generated narratives.

This prevents redundant API calls when viewing the same day multiple times.
"""

import time
from typing import Optional, Dict


class NarrativeCache:
    """Simple TTL-based cache for narratives."""
    
    def __init__(self, ttl: int = 3600):
        """
        Initialize cache.
        
        Args:
            ttl: Time-to-live in seconds (default: 1 hour)
        """
        self._cache: Dict[str, tuple] = {}
        self._ttl = ttl
    
    def get(self, guild_id: str, day: int) -> Optional[str]:
        """
        Get cached narrative if available and not expired.
        
        Args:
            guild_id: Discord guild ID
            day: Day number
            
        Returns:
            Cached narrative or None
        """
        key = f"{guild_id}:{day}"
        
        if key in self._cache:
            narrative, timestamp = self._cache[key]
            
            # Check if expired
            if time.time() - timestamp < self._ttl:
                return narrative
            else:
                # Remove expired entry
                del self._cache[key]
        
        return None
    
    def set(self, guild_id: str, day: int, narrative: str):
        """
        Cache a narrative.
        
        Args:
            guild_id: Discord guild ID
            day: Day number
            narrative: Generated narrative text
        """
        key = f"{guild_id}:{day}"
        self._cache[key] = (narrative, time.time())
    
    def clear(self, guild_id: str):
        """
        Clear all cached narratives for a guild.
        
        Args:
            guild_id: Discord guild ID
        """
        keys_to_remove = [k for k in self._cache.keys() if k.startswith(f"{guild_id}:")]
        for key in keys_to_remove:
            del self._cache[key]
    
    def clear_all(self):
        """Clear entire cache."""
        self._cache.clear()


# Global cache instance
_narrative_cache = NarrativeCache(
    ttl=int(os.getenv("NARRATIVE_CACHE_TTL", "3600"))
)


def get_narrative_cache() -> NarrativeCache:
    """Get global narrative cache instance."""
    return _narrative_cache
```

**Update `narrative_generator.py` to use cache:**

```python
def generate_daily_narrative(
    self,
    weather_json: Dict,
    character_context: Optional[str] = None,
    guild_id: Optional[str] = None,
    use_cache: bool = True
) -> Optional[str]:
    """Generate narrative with caching support."""
    # Check cache first
    if use_cache and guild_id:
        from utils.narrative_cache import get_narrative_cache
        cache = get_narrative_cache()
        cached = cache.get(guild_id, weather_json['day'])
        if cached:
            return cached
    
    # Generate narrative
    narrative = self._generate_from_api(weather_json, character_context)
    
    # Cache if successful
    if narrative and use_cache and guild_id:
        from utils.narrative_cache import get_narrative_cache
        cache = get_narrative_cache()
        cache.set(guild_id, weather_json['day'], narrative)
    
    return narrative
```

### 4.4 Testing Strategy for Phase 4

**New File:** `tests/test_narrative_display.py`

```python
class TestNarrativeDisplay:
    def test_narrative_enabled_generates()
    def test_narrative_disabled_shows_embed()
    def test_narrative_fallback_to_embed()
    def test_narrative_fallback_to_simple()
    def test_narrative_message_structure()
    
class TestNarrativeCache:
    def test_cache_stores_narrative()
    def test_cache_retrieves_narrative()
    def test_cache_expiry()
    def test_cache_clear_guild()
    def test_cache_clear_all()
```

---

## **PHASE 5: System Integration & Testing**
**Goal:** Comprehensive testing and documentation  
**Duration:** 2-3 days  
**Risk Level:** 🟡 Medium

### 5.1 Integration Testing

**New File:** `tests/test_weather_integration.py`

```python
"""
End-to-end integration tests for weather system with narratives.
"""

class TestWeatherCommandIntegration:
    """Test full command flow with all systems."""
    
    @pytest.mark.integration
    def test_weather_next_full_flow():
        """Test /weather next with JSON, GM notification, and narrative."""
        # Setup
        # Execute command
        # Verify:
        #   - Weather data saved to database
        #   - JSON sent to GM channel
        #   - Narrative generated (if enabled)
        #   - Player message sent
    
    @pytest.mark.integration
    def test_weather_next_stage_full_flow():
        """Test /weather next-stage with all systems."""
    
    @pytest.mark.integration
    def test_weather_view_historical():
        """Test viewing historical weather with cache."""
    
    @pytest.mark.integration
    def test_narrative_disabled_regression():
        """Ensure system works exactly as before when narrative disabled."""

class TestDualChannelIntegration:
    """Test dual-channel system (player + GM)."""
    
    def test_player_gets_narrative_gm_gets_json():
        """Verify dual output when narrative enabled."""
    
    def test_player_gets_embed_gm_gets_json():
        """Verify dual output when narrative disabled."""
```

### 5.2 Performance Testing

```python
class TestPerformance:
    """Test system performance under load."""
    
    def test_json_serialization_speed():
        """Ensure JSON generation is fast (<50ms)."""
    
    def test_cache_effectiveness():
        """Verify cache reduces API calls."""
    
    def test_api_timeout_handling():
        """Test graceful degradation if API slow."""
```

### 5.3 Error Handling & Edge Cases

```python
class TestErrorHandling:
    """Test error scenarios."""
    
    def test_openai_api_key_missing():
        """System should work without API key (disabled mode)."""
    
    def test_openai_api_error():
        """Graceful fallback on API errors."""
    
    def test_json_serialization_failure():
        """Handle malformed data gracefully."""
    
    def test_gm_channel_missing():
        """Don't crash if notifications channel doesn't exist."""
```

### 5.4 Documentation Updates

**Update Files:**

1. **`COMMANDS_DOCUMENTATION.md`**
   - Add section on narrative system
   - Document new environment variables
   - Explain GM notifications

2. **`DEPLOYMENT_GUIDE.md`**
   - Add OpenAI API key setup instructions
   - Document narrative configuration
   - Add troubleshooting section

3. **Create: `NARRATIVE_SYSTEM_GUIDE.md`**
   - Detailed guide for GMs on using narrative features
   - How to read JSON in GM channel
   - How to customize prompts
   - Cost management tips

---

## 🔗 System Dependencies & Impacts

### Affected Modules

| Module | Impact Level | Changes Required |
|--------|-------------|------------------|
| `commands/weather.py` | 🔴 High | Add JSON generation, narrative display |
| `db/weather_storage.py` | 🟢 None | No changes needed |
| `db/weather_data.py` | 🟢 None | No changes needed |
| `utils/weather_mechanics.py` | 🟢 None | No changes needed |
| `utils/modifier_calculator.py` | 🟢 None | No changes needed |
| `tests/*` | 🟡 Medium | New test files, existing tests unchanged |
| `requirements.txt` | 🟡 Medium | Add `openai` dependency |
| `.env` | 🟡 Medium | Add OpenAI configuration |

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     User Issues Command                      │
│                    /weather next [args]                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  weather.py Command Handler                  │
│  - Validate inputs                                           │
│  - Get journey state (weather_storage.py)                   │
│  - Generate weather (weather_mechanics.py)                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│               Serialize Weather to JSON (NEW)                │
│  - weather_serializer.py                                    │
│  - Create structured JSON with all weather data             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────┴─────────┐
                    ▼                   ▼
        ┌─────────────────┐   ┌─────────────────────┐
        │ GM Channel (NEW) │   │  Player Channel     │
        │ - Send JSON      │   │  - Check if         │
        │ - Send embed     │   │    narrative enabled│
        │   summary        │   │                     │
        └─────────────────┘   └─────────────────────┘
                                        │
                                        ▼
                          ┌─────────────┴─────────────┐
                          │  Narrative Enabled?       │
                          └─────────────┬─────────────┘
                                   │         │
                            Yes ◄──┘         └──► No
                             │                   │
                             ▼                   ▼
              ┌──────────────────────┐   ┌────────────────┐
              │ Generate Narrative   │   │ Send Original  │
              │ - narrative_generator│   │ Embed (Exists) │
              │ - OpenAI API call    │   └────────────────┘
              │ - Cache result       │
              └──────────────────────┘
                          │
                          ▼
              ┌──────────────────────┐
              │ Send Narrative Embed │
              │ - Atmospheric text   │
              │ - Minimal footer     │
              └──────────────────────┘
```

### Backward Compatibility

**Critical Guarantees:**

1. ✅ **Default Behavior:** With `NARRATIVE_ENABLED=false`, system behaves **exactly** as before
2. ✅ **Database Schema:** No changes to existing database structure
3. ✅ **Existing Commands:** All command syntax remains unchanged
4. ✅ **API Compatibility:** All existing bot features continue to work
5. ✅ **Test Suite:** All 100+ existing tests must pass without modification

---

## 📈 Testing Strategy Summary

### Test Coverage Goals

| Module | Current Coverage | Target Coverage |
|--------|------------------|-----------------|
| `weather_serializer.py` | N/A (new) | >95% |
| `narrative_generator.py` | N/A (new) | >85% |
| `narrative_prompts.py` | N/A (new) | >90% |
| `narrative_cache.py` | N/A (new) | >90% |
| `weather.py` (modified) | ~85% | >85% (maintain) |
| **Overall Project** | **~87%** | **>88%** |

### Test Execution Plan

```bash
# Phase 1: Unit tests for serializer
pytest tests/test_weather_serializer.py -v

# Phase 2: Integration tests for JSON output
pytest tests/test_weather_json_output.py -v

# Phase 3: Unit tests for OpenAI integration
pytest tests/test_narrative_generator.py -v
pytest tests/test_narrative_prompts.py -v

# Phase 4: Display and cache tests
pytest tests/test_narrative_display.py -v
pytest tests/test_narrative_cache.py -v

# Phase 5: Full integration and regression
pytest tests/test_weather_integration.py -v

# Final: Full test suite
pytest tests/ -v --cov=. --cov-report=html
```

### Regression Test Checklist

Before each phase completion, verify:

- [ ] All existing tests pass: `pytest tests/ -v`
- [ ] Code coverage maintained or improved
- [ ] No breaking changes to existing commands
- [ ] Manual testing of `/weather next`, `/weather next-stage`, `/weather view`
- [ ] GM notifications work
- [ ] Player messages display correctly
- [ ] Database operations succeed

---

## 🚨 Risk Analysis & Mitigation

### High-Risk Areas

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **OpenAI API Rate Limits** | 🔴 High | 🟡 Medium | Implement caching, add rate limit handling |
| **API Key Exposure** | 🔴 High | 🟢 Low | Use `.env`, add to `.gitignore`, document security |
| **Cost Overrun** | 🟡 Medium | 🟡 Medium | Use GPT-4o-mini, set max tokens, add usage logging |
| **Narrative Quality** | 🟡 Medium | 🟡 Medium | Iterative prompt engineering, fallback to embeds |
| **Breaking Existing Features** | 🔴 High | 🟢 Low | Comprehensive testing, feature flag system |
| **Performance Degradation** | 🟡 Medium | 🟢 Low | Async API calls, caching, timeout handling |

### Rollback Plan

If issues arise:

1. **Immediate:** Set `NARRATIVE_ENABLED=false` in `.env`
2. **Quick Fix:** Remove OpenAI calls, keep JSON system
3. **Full Rollback:** Revert to last stable commit
4. **Database:** No schema changes = no migration needed

---

## 💰 Cost Estimation (OpenAI)

### API Usage Projection

**Assumptions:**
- Average server: 50 weather generations per day
- GPT-4o-mini pricing: $0.00015 per 1K input tokens, $0.0006 per 1K output tokens
- Average prompt: ~500 tokens input
- Average response: ~300 tokens output

**Monthly Cost per Server:**
```
Daily generations: 50
Input tokens: 50 × 500 = 25,000 tokens/day
Output tokens: 50 × 300 = 15,000 tokens/day

Monthly input: 25,000 × 30 = 750,000 tokens = $0.11
Monthly output: 15,000 × 30 = 450,000 tokens = $0.27

Total per server: ~$0.40/month
```

**Scaling:**
- 10 servers: ~$4/month
- 50 servers: ~$20/month
- 100 servers: ~$40/month

**Cost Control Measures:**
1. Caching (reduces repeat generations by ~30%)
2. Optional feature (servers can disable)
3. Rate limiting (max generations per hour)
4. Fallback to simple narratives

---

## 📝 Implementation Timeline

### Suggested Schedule

| Phase | Duration | Start | End | Deliverables |
|-------|----------|-------|-----|--------------|
| **Phase 1** | 2 days | Day 1 | Day 2 | JSON serializer, tests |
| **Phase 2** | 1 day | Day 3 | Day 3 | GM notifications, JSON output |
| **Phase 3** | 2 days | Day 4 | Day 5 | OpenAI setup, prompt templates |
| **Phase 4** | 3 days | Day 6 | Day 8 | Narrative display, caching |
| **Phase 5** | 2 days | Day 9 | Day 10 | Integration tests, docs |
| **Total** | **10 days** | | | **Full system** |

### Milestone Checkpoints

**Milestone 1 (Day 2):** JSON System Complete
- [ ] `weather_serializer.py` implemented
- [ ] Unit tests passing (>95% coverage)
- [ ] JSON validation confirmed

**Milestone 2 (Day 3):** Dual-Channel Active
- [ ] GM notifications working
- [ ] JSON appears in `boat-travelling-notifications`
- [ ] Player channel unchanged (regression test passed)

**Milestone 3 (Day 5):** OpenAI Ready
- [ ] API integration complete
- [ ] Prompts tested manually
- [ ] Feature flag system working

**Milestone 4 (Day 8):** Narrative System Live
- [ ] AI narratives display correctly
- [ ] Caching operational
- [ ] Fallback system tested

**Milestone 5 (Day 10):** Production Ready
- [ ] All tests passing
- [ ] Documentation complete
- [ ] Performance validated

---

## 🔧 Configuration Reference

### Environment Variables

```bash
# ============================================================================
# OPENAI NARRATIVE SYSTEM CONFIGURATION
# ============================================================================

# OpenAI API Key (required for narrative generation)
# Get your key from: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-proj-...

# Model to use for narrative generation
# Options: gpt-4o-mini (recommended), gpt-4o, gpt-4-turbo
# gpt-4o-mini is 15x cheaper than gpt-4 with similar quality
OPENAI_MODEL=gpt-4o-mini

# Maximum tokens for narrative response
# Daily narratives: 500 tokens (~2-3 paragraphs)
# Stage narratives: 1000 tokens (~4-5 paragraphs)
OPENAI_MAX_TOKENS=500

# Temperature (creativity) setting (0.0-2.0)
# Lower = more focused, Higher = more creative
# Recommended: 0.7-0.9 for atmospheric narratives
OPENAI_TEMPERATURE=0.8

# Enable/disable narrative generation system
# Set to 'false' to use traditional embeds
NARRATIVE_ENABLED=false

# Fallback behavior if API fails
# true = show original embed, false = show simple narrative
NARRATIVE_FALLBACK_TO_EMBED=true

# Enable narrative caching (reduces API calls)
NARRATIVE_CACHE_ENABLED=true

# Cache time-to-live in seconds (default: 1 hour)
NARRATIVE_CACHE_TTL=3600

# Debug: Show JSON in narrative messages (for testing)
NARRATIVE_SHOW_JSON_IN_NARRATIVE=false
```

### File Structure Summary

```
travelling-bot/
├── commands/
│   └── weather.py                    # [MODIFIED] Add JSON + narrative support
├── db/
│   ├── weather_data.py              # [UNCHANGED]
│   └── weather_storage.py           # [UNCHANGED]
├── utils/
│   ├── weather_mechanics.py         # [UNCHANGED]
│   ├── modifier_calculator.py       # [UNCHANGED]
│   ├── weather_serializer.py        # [NEW] JSON generation
│   ├── narrative_generator.py       # [NEW] OpenAI integration
│   ├── narrative_prompts.py         # [NEW] Prompt templates
│   └── narrative_cache.py           # [NEW] Caching system
├── tests/
│   ├── test_weather_serializer.py   # [NEW] JSON tests
│   ├── test_weather_json_output.py  # [NEW] Integration tests
│   ├── test_narrative_generator.py  # [NEW] OpenAI tests
│   ├── test_narrative_display.py    # [NEW] Display tests
│   ├── test_narrative_cache.py      # [NEW] Cache tests
│   └── test_weather_integration.py  # [NEW] E2E tests
├── .env                              # [MODIFIED] Add OpenAI config
├── requirements.txt                  # [MODIFIED] Add openai package
├── NARRATIVE_SYSTEM_GUIDE.md        # [NEW] User documentation
└── OPENAI_NARRATIVE_IMPLEMENTATION_PLAN.md  # [THIS FILE]
```

---

## 🎯 Future Enhancements (Post-MVP)

### Phase 6: Advanced Features (Optional)

1. **Character-Aware Narratives**
   - Track party composition
   - Reference character backgrounds
   - Adapt tone to party experience level

2. **Story Continuity**
   - Reference previous day's events
   - Build narrative arcs across journeys
   - Remember significant moments

3. **GM Customization**
   - Custom prompt templates per server
   - Tone adjustment (dark, neutral, heroic)
   - Length preferences (short, medium, long)

4. **Interactive Regeneration**
   - "Regenerate" button on narratives
   - Alternative narrative versions
   - Save favorite generations

5. **Cost Tracking**
   - Dashboard showing API usage
   - Per-server cost metrics
   - Budget alerts

6. **Multi-Language Support**
   - Translate narratives to player languages
   - Maintain atmospheric tone across languages

---

## 📚 References & Resources

### WFRP Reference Materials
- **Rulebook:** *Warhammer Fantasy Roleplay 4th Edition*
- **Setting:** River Reik, Reikland, and The Empire
- **Tone Guide:** Grim, dark, perilous but not hopeless

### Technical Documentation
- **OpenAI API Docs:** https://platform.openai.com/docs
- **Discord.py Docs:** https://discordpy.readthedocs.io/
- **Python Testing:** https://docs.pytest.org/

### Similar Implementations
- Existing dual-channel system: `commands/river_encounter.py`
- Existing notification system: `send_mechanics_notification()`

---

## ✅ Acceptance Criteria

### Must-Have (MVP)

- [ ] JSON serializer generates valid, complete weather data
- [ ] GM channel receives JSON for all weather commands
- [ ] OpenAI integration works with proper error handling
- [ ] Narrative generation produces atmospheric text
- [ ] Fallback system works when API unavailable
- [ ] All existing tests pass without modification
- [ ] New tests achieve >85% coverage
- [ ] Feature flag system allows enabling/disabling
- [ ] Documentation complete and accurate
- [ ] No performance degradation vs. original system

### Should-Have (Nice to Have)

- [ ] Narrative caching reduces API costs by >25%
- [ ] Generated narratives require minimal regeneration (<10%)
- [ ] GM feedback on JSON utility is positive
- [ ] Player feedback on narratives is positive
- [ ] System handles 50+ daily generations per server

### Could-Have (Future Work)

- [ ] Character-aware narrative generation
- [ ] Story continuity across days
- [ ] Multi-language support
- [ ] Cost tracking dashboard
- [ ] Custom prompt templates per server

---

## 🤝 Collaboration & Communication

### Stakeholders
- **Developer:** Implementation and testing
- **GM (End User):** Feedback on narratives and JSON utility
- **Players (End Users):** Feedback on immersion and readability

### Review Points
1. After Phase 1: Review JSON schema completeness
2. After Phase 2: Verify GM channel notifications work
3. After Phase 3: Test OpenAI integration manually
4. After Phase 4: Gather feedback on narrative quality
5. After Phase 5: Final system review and sign-off

---

## 📖 Appendix

### A. Sample JSON Output

```json
{
  "day": 1,
  "stage": 1,
  "season": "summer",
  "province": "reikland",
  "wind": {
    "dawn": {
      "strength": "light",
      "direction": "tailwind",
      "speed_modifier": "+5%",
      "boat_handling_penalty": 0,
      "requires_tacking": true,
      "changed": false
    },
    "midday": {
      "strength": "bracing",
      "direction": "tailwind",
      "speed_modifier": "+10%",
      "boat_handling_penalty": 0,
      "requires_tacking": true,
      "changed": true
    },
    "dusk": {
      "strength": "bracing",
      "direction": "sidewind",
      "speed_modifier": "+5%",
      "boat_handling_penalty": 0,
      "requires_tacking": true,
      "changed": false
    },
    "midnight": {
      "strength": "strong",
      "direction": "headwind",
      "speed_modifier": "-20%",
      "boat_handling_penalty": 0,
      "requires_tacking": false,
      "changed": true
    }
  },
  "weather": {
    "type": "fair",
    "name": "Fair",
    "description": "For once, the weather is being kind. Clear skies and comfortable conditions.",
    "effects": ["No weather-related hazards"]
  },
  "temperature": {
    "actual": 21,
    "perceived": 16,
    "base": 21,
    "category": "average",
    "description": "Comfortable for the season",
    "wind_chill_applied": true,
    "wind_chill_amount": -5
  },
  "special_events": {
    "cold_front": {
      "active": false,
      "days_remaining": 0
    },
    "heat_wave": {
      "active": false,
      "days_remaining": 0
    }
  },
  "metadata": {
    "generated_at": "2025-10-29T14:30:00Z",
    "generated_by": "GameMaster#1234",
    "is_override": false,
    "continuity_from_previous_day": true,
    "continuity_note": "Wind carried over from Day 0 midnight: Strong Headwind"
  }
}
```

### B. Sample AI Narrative

```
The morning breaks over the Reik with a brisk wind at your back, 
pushing the boat along with unusual ease. The water is calm, 
reflecting the pale summer sky like tarnished silver. As midday 
approaches, the wind strengthens, filling the sails and driving 
you forward with purpose. The crew works in quiet efficiency, 
grateful for the fair conditions—such weather is a rare blessing 
in these dark times.

By evening, the wind shifts to the side, requiring careful 
maneuvering to maintain course. The temperature has dropped 
slightly with the breeze, and the crew pulls their cloaks tighter. 
As darkness falls, the wind turns against you, howling upstream 
like a beast denied its prey. Progress slows to a crawl, and the 
night watch begins with wary eyes on the black waters ahead.
```

### C. Glossary

- **Three-Channel System:** Separate outputs for players (narrative), GMs (mechanics), and logs (JSON)
- **JSON Serialization:** Converting data structures to JSON format for OpenAI consumption
- **Narrative Generation:** Using AI to create atmospheric story text from structured data
- **Feature Flag:** Configuration option to enable/disable a feature
- **Fallback System:** Alternative behavior when primary system fails
- **TTL (Time-To-Live):** How long cached data remains valid
- **GM (Game Master):** The person running the game/campaign
- **Player Channel:** Where the `/weather` command is invoked (receives narrative in Phase 4)
- **GM Notifications Channel:** `boat-travelling-notifications` (mechanics only, unchanged)
- **Log Channel:** `boat-travelling-log` (JSON data for debugging and OpenAI processing)
- **WFRP:** Warhammer Fantasy Roleplay tabletop RPG

---

**End of Implementation Plan**

*For questions or clarifications, please contact the development team.*
