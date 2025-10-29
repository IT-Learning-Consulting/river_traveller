# Weather System Refactoring Plan

## 📋 Executive Summary

**Current State:** `weather.py` is 1262 lines with mixed concerns (command handling, display logic, notifications, formatting)  
**Goal:** Refactor into modular, testable components using OOP principles  
**Risk Level:** 🟠 Medium-High (must maintain 100% backward compatibility)  
**Duration:** 2-3 days  
**Testing Strategy:** Run existing 345 tests after each refactoring step

---

## 🎯 Refactoring Objectives

### Primary Goals
1. **Separation of Concerns** - Separate command handling, business logic, and presentation
2. **Single Responsibility** - Each class/module does one thing well
3. **Testability** - Pure functions and dependency injection for easy testing
4. **Maintainability** - Clear structure for adding OpenAI features
5. **Zero Breaking Changes** - All existing tests must pass without modification

### Success Criteria
- ✅ All 345 existing tests pass without changes
- ✅ Code coverage remains ≥87%
- ✅ Main command file <300 lines
- ✅ Each module has clear, documented responsibility
- ✅ New unit tests for each refactored module (30+ new tests)

---

## 🏗️ Proposed Architecture

### Current Structure (Monolithic)
```
commands/weather.py (1262 lines)
├── Command registration
├── Action routing
├── Weather generation logic
├── Display functions (embeds)
├── Notification functions
├── Helper functions (emojis, formatting)
└── Stage configuration
```

### New Structure (Modular)

```
commands/
├── weather.py (250 lines)               # Command registration & routing only
│   └── Uses: WeatherCommandHandler
│
├── weather/                              # NEW: Weather command module
│   ├── __init__.py                       # Exports main classes
│   ├── handler.py (200 lines)           # WeatherCommandHandler class
│   ├── display.py (300 lines)           # WeatherDisplayManager class
│   ├── stages.py (150 lines)            # StageDisplayManager class
│   ├── notifications.py (100 lines)     # NotificationManager class
│   └── formatters.py (100 lines)        # WeatherFormatters utility class
│
tests/
└── test_weather_refactored/             # NEW: Tests for refactored code
    ├── test_handler.py
    ├── test_display.py
    ├── test_stages.py
    ├── test_notifications.py
    └── test_formatters.py
```

---

## 📦 Module Design

### 1. `commands/weather.py` (Entry Point - 250 lines)

**Responsibility:** Discord command registration and routing only

```python
"""
Command: weather
Description: Entry point for weather commands
"""

import discord
from discord import app_commands
from discord.ext import commands

from commands.weather.handler import WeatherCommandHandler


def is_gm(user: discord.Member) -> bool:
    """Check if user is a GM."""
    # Keep existing implementation
    pass


def setup(bot: commands.Bot):
    """Register weather commands with the bot."""
    handler = WeatherCommandHandler()
    
    @bot.tree.command(name="weather", description="Manage daily weather for river travel")
    @app_commands.describe(...)
    @app_commands.choices(...)
    async def weather_slash(interaction, action, season, province, day):
        """Slash command entry point."""
        await handler.handle_command(
            interaction, action, season, province, day, is_slash=True
        )
    
    @bot.command(name="weather")
    async def weather_prefix(ctx, action, season, province, day):
        """Prefix command entry point."""
        await handler.handle_command(
            ctx, action, season, province, day, is_slash=False
        )
    
    @bot.tree.command(name="weather-stage-config", ...)
    async def weather_stage_config_slash(interaction, stage_duration, display_mode):
        """Stage configuration command."""
        await handler.configure_stage(
            interaction, stage_duration, display_mode, is_slash=True
        )
    
    # Prefix version...
```

**Key Changes:**
- Minimal logic - just routing
- Delegates to `WeatherCommandHandler`
- Keeps command registration clean and focused

---

### 2. `commands/weather/handler.py` (Business Logic - 200 lines)

**Responsibility:** Action routing and orchestration

```python
"""
Weather command handler - orchestrates weather generation and display.
"""

from typing import Optional
import discord

from db.weather_storage import WeatherStorage
from utils.weather_mechanics import (
    generate_daily_wind,
    generate_daily_wind_with_previous,
    roll_weather_condition,
    get_weather_effects,
    roll_temperature_with_special_events,
    apply_wind_chill,
    get_province_base_temperature,
)
from commands.weather.display import WeatherDisplayManager
from commands.weather.stages import StageDisplayManager
from commands.weather.notifications import NotificationManager


class WeatherCommandHandler:
    """
    Main handler for weather commands.
    
    Responsibilities:
    - Route actions to appropriate methods
    - Generate weather data
    - Coordinate display and notifications
    """
    
    def __init__(self):
        self.storage = WeatherStorage()
        self.display = WeatherDisplayManager()
        self.stage_display = StageDisplayManager()
        self.notifications = NotificationManager()
    
    async def handle_command(
        self,
        context,
        action: str,
        season: Optional[str],
        province: Optional[str],
        day: Optional[int],
        is_slash: bool
    ):
        """Route command to appropriate handler method."""
        guild_id = str(context.guild.id) if context.guild else None
        
        if not guild_id:
            await self.display.send_error(
                context, "This command must be used in a server.", is_slash
            )
            return
        
        # Route to action handlers
        action_map = {
            "next": self.generate_next_day,
            "next-stage": self.generate_next_stage,
            "journey": self.start_new_journey,
            "view": self.view_day_weather,
            "end": self.end_journey,
            "override": self.override_weather,
        }
        
        handler_func = action_map.get(action)
        if handler_func:
            await handler_func(context, guild_id, season, province, day, is_slash)
        else:
            await self.display.send_error(context, f"Unknown action: {action}", is_slash)
    
    async def generate_next_day(
        self,
        context,
        guild_id: str,
        season: Optional[str],  # Not used for 'next'
        province: Optional[str],  # Not used for 'next'
        day: Optional[int],  # Not used for 'next'
        is_slash: bool
    ):
        """Generate weather for the next day."""
        try:
            journey = self.storage.get_journey_state(guild_id)
            
            # Auto-start journey if needed
            if not journey:
                await self.display.send_info(
                    context,
                    "⚠️ No journey in progress. Starting new journey with default settings.",
                    is_slash
                )
                self.storage.start_journey(guild_id, "summer", "reikland")
                journey = self.storage.get_journey_state(guild_id)
            
            # Generate weather data
            weather_data = self._generate_daily_weather(guild_id, journey)
            
            # Display to player
            await self.display.show_daily_weather(
                context, weather_data, is_slash
            )
            
            # Send mechanics notification
            await self.notifications.send_mechanics(
                context, weather_data
            )
            
        except Exception as e:
            await self.display.send_error(
                context, f"Error generating weather: {str(e)}", is_slash
            )
    
    def _generate_daily_weather(self, guild_id: str, journey: dict) -> dict:
        """
        Generate weather data for a single day.
        
        Returns:
            dict: Complete weather data including wind, temperature, conditions
        """
        current_day = journey["current_day"]
        season = journey["season"]
        province = journey["province"]
        
        current_weather = self.storage.get_daily_weather(guild_id, current_day)
        
        # Determine day number and wind continuity
        if current_weather:
            new_day = self.storage.advance_day(guild_id)
            previous_midnight = current_weather["wind_timeline"][3]
            wind_timeline = generate_daily_wind_with_previous(previous_midnight)
            continuity_note = (
                f"🔄 Wind carried over from Day {current_day} midnight: "
                f"{previous_midnight['strength']} {previous_midnight['direction']}"
            )
        else:
            new_day = current_day
            wind_timeline = generate_daily_wind()
            continuity_note = None
        
        # Generate temperature with special events
        previous_weather = (
            self.storage.get_daily_weather(guild_id, new_day - 1)
            if new_day > 1 else None
        )
        cold_front_days = (
            previous_weather["cold_front_days_remaining"]
            if previous_weather else 0
        )
        heat_wave_days = (
            previous_weather["heat_wave_days_remaining"]
            if previous_weather else 0
        )
        
        weather_type = roll_weather_condition(season)
        weather_effects = get_weather_effects(weather_type)
        
        (
            actual_temp, temp_category, temp_description,
            temp_roll, cold_front_remaining, heat_wave_remaining
        ) = roll_temperature_with_special_events(
            season, province, cold_front_days, heat_wave_days
        )
        
        base_temp = get_province_base_temperature(province, season)
        wind_strengths = [w["strength"] for w in wind_timeline]
        most_common_wind = max(set(wind_strengths), key=wind_strengths.count)
        perceived_temp = apply_wind_chill(actual_temp, most_common_wind)
        
        # Save to database
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
            "heat_wave_days_remaining": heat_wave_remaining,
        }
        self.storage.save_daily_weather(guild_id, new_day, weather_db_data)
        
        # Return enriched data for display
        return {
            "day": new_day,
            "season": season,
            "province": province,
            "wind_timeline": wind_timeline,
            "weather_type": weather_type,
            "weather_effects": weather_effects,
            "actual_temp": actual_temp,
            "perceived_temp": perceived_temp,
            "base_temp": base_temp,
            "temp_category": temp_category,
            "temp_description": temp_description,
            "most_common_wind": most_common_wind,
            "cold_front_days": cold_front_remaining,
            "heat_wave_days": heat_wave_remaining,
            "continuity_note": continuity_note,
        }
    
    async def generate_next_stage(self, context, guild_id, season, province, day, is_slash):
        """Generate weather for next stage (multi-day)."""
        # Implementation delegates to stage_display
        pass
    
    async def start_new_journey(self, context, guild_id, season, province, day, is_slash):
        """Start a new journey."""
        # Implementation
        pass
    
    async def view_day_weather(self, context, guild_id, season, province, day, is_slash):
        """View specific day's weather."""
        # Implementation
        pass
    
    async def end_journey(self, context, guild_id, season, province, day, is_slash):
        """End current journey."""
        # Implementation
        pass
    
    async def override_weather(self, context, guild_id, season, province, day, is_slash):
        """Override weather (GM only)."""
        # Implementation with GM check
        pass
    
    async def configure_stage(
        self,
        context,
        stage_duration: Optional[int],
        display_mode: Optional[str],
        is_slash: bool
    ):
        """Configure stage settings (GM only)."""
        # Implementation
        pass
```

**Key Features:**
- Clean separation: generates data, delegates display
- Returns structured dictionaries instead of passing 15+ parameters
- Easy to test each method in isolation
- Clear data flow: storage → generation → display

---

### 3. `commands/weather/display.py` (Display Logic - 300 lines)

**Responsibility:** Create and send Discord embeds for weather display

```python
"""
Weather display manager - handles all Discord embed creation and sending.
"""

import discord
from typing import Optional

from commands.weather.formatters import WeatherFormatters
from db.weather_data import WIND_STRENGTH, WIND_DIRECTION
from utils.weather_mechanics import (
    get_temperature_description_text,
    get_wind_chill_note,
    get_wind_modifiers,
)


class WeatherDisplayManager:
    """
    Manages all weather display operations.
    
    Responsibilities:
    - Create weather embeds
    - Format weather data for display
    - Send messages to Discord channels
    """
    
    def __init__(self):
        self.formatters = WeatherFormatters()
    
    async def show_daily_weather(
        self,
        context,
        weather_data: dict,
        is_slash: bool,
        is_historical: bool = False
    ):
        """
        Display daily weather embed.
        
        Args:
            context: Discord context
            weather_data: Complete weather data dictionary
            is_slash: Whether this is a slash command
            is_historical: Whether this is a historical view
        """
        embed = self._create_daily_weather_embed(weather_data, is_historical)
        
        # Add user footer
        user_name = (
            context.user.display_name if is_slash
            else context.author.display_name
        )
        embed.set_footer(text=f"Generated by {user_name}")
        
        await self._send_embed(context, embed, is_slash)
    
    def _create_daily_weather_embed(
        self,
        weather_data: dict,
        is_historical: bool
    ) -> discord.Embed:
        """
        Create Discord embed for daily weather.
        
        Args:
            weather_data: Weather data dictionary with all fields
            is_historical: Whether this is a historical view
            
        Returns:
            discord.Embed: Formatted weather embed
        """
        title_prefix = "📜 " if is_historical else "📅 "
        title = (
            f"{title_prefix}Day {weather_data['day']} - "
            f"{weather_data['season'].title()} in "
            f"{weather_data['province'].replace('_', ' ').title()}"
        )
        
        color = (
            discord.Color.greyple() if is_historical
            else discord.Color.blue()
        )
        
        embed = discord.Embed(title=title, color=color)
        
        # Continuity note
        if weather_data.get('continuity_note'):
            embed.description = weather_data['continuity_note']
        
        # Wind conditions field
        wind_text = self._format_wind_conditions(weather_data['wind_timeline'])
        embed.add_field(
            name="🌬️ Wind Conditions",
            value=wind_text,
            inline=False
        )
        
        # Weather condition field
        weather_text = self._format_weather_condition(
            weather_data['weather_type'],
            weather_data['weather_effects']
        )
        embed.add_field(
            name=f"{self.formatters.get_weather_emoji(weather_data['weather_type'])} Weather Condition",
            value=weather_text,
            inline=False
        )
        
        # Weather effects field
        if weather_data['weather_effects']['effects']:
            effects_text = self._format_weather_effects(
                weather_data['weather_effects']['effects']
            )
            embed.add_field(
                name="⚠️ Effects",
                value=effects_text,
                inline=False
            )
        
        # Temperature field
        temp_text = self._format_temperature(weather_data)
        embed.add_field(
            name=f"{self.formatters.get_temperature_emoji(weather_data['actual_temp'])} Temperature",
            value=temp_text,
            inline=False
        )
        
        return embed
    
    def _format_wind_conditions(self, wind_timeline: list) -> str:
        """Format wind timeline for display."""
        wind_lines = []
        for wind_entry in wind_timeline:
            strength_name = WIND_STRENGTH[wind_entry["strength"]]
            direction_name = WIND_DIRECTION[wind_entry["direction"]]
            modifiers = get_wind_modifiers(
                wind_entry["strength"], wind_entry["direction"]
            )
            
            change_indicator = " 🔄" if wind_entry["changed"] else ""
            wind_lines.append(
                f"**{wind_entry['time']}:** {strength_name} {direction_name}{change_indicator}\n"
                f"  ↳ {modifiers['modifier']}"
            )
        
        return "\n".join(wind_lines)
    
    def _format_weather_condition(
        self,
        weather_type: str,
        weather_effects: dict
    ) -> str:
        """Format weather condition description."""
        return f"**{weather_effects['name']}**\n{weather_effects['description']}"
    
    def _format_weather_effects(self, effects: list) -> str:
        """Format weather effects list."""
        return "\n".join(f"• {effect}" for effect in effects)
    
    def _format_temperature(self, weather_data: dict) -> str:
        """Format temperature information."""
        actual_temp = weather_data['actual_temp']
        perceived_temp = weather_data['perceived_temp']
        base_temp = weather_data['base_temp']
        
        temp_feel_text = get_temperature_description_text(actual_temp, base_temp)
        
        lines = [
            f"**{actual_temp}°C** ({temp_feel_text})",
            f"*{weather_data['temp_description']}*"
        ]
        
        # Wind chill
        if perceived_temp != actual_temp:
            wind_chill_note = get_wind_chill_note(weather_data['most_common_wind'])
            lines.append(f"**Feels like:** {perceived_temp}°C{wind_chill_note}")
        
        # Special events
        if weather_data['cold_front_days'] > 0:
            lines.append(
                f"\n❄️ **Cold Front:** {weather_data['cold_front_days']} days remaining"
            )
        if weather_data['heat_wave_days'] > 0:
            lines.append(
                f"\n🔥 **Heat Wave:** {weather_data['heat_wave_days']} days remaining"
            )
        
        return "\n".join(lines)
    
    async def _send_embed(
        self,
        context,
        embed: discord.Embed,
        is_slash: bool
    ):
        """Send embed to Discord channel."""
        if is_slash:
            if hasattr(context, "response") and not context.response.is_done():
                await context.response.send_message(embed=embed)
            else:
                await context.followup.send(embed=embed)
        else:
            await context.send(embed=embed)
    
    async def send_error(self, context, message: str, is_slash: bool):
        """Send error message."""
        embed = discord.Embed(
            title="❌ Error",
            description=message,
            color=discord.Color.red()
        )
        await self._send_embed(context, embed, is_slash)
    
    async def send_info(self, context, message: str, is_slash: bool):
        """Send info message."""
        embed = discord.Embed(
            title="ℹ️ Info",
            description=message,
            color=discord.Color.blue()
        )
        await self._send_embed(context, embed, is_slash)
```

**Key Features:**
- All embed creation in one place
- Pure functions for formatting (easy to test)
- Receives structured data, not 15+ parameters
- Reusable formatting methods

---

### 4. `commands/weather/stages.py` (Stage Display - 150 lines)

**Responsibility:** Display multi-day stage weather

```python
"""
Stage display manager - handles multi-day weather display.
"""

import discord
from typing import List, Tuple

from commands.weather.formatters import WeatherFormatters
from db.weather_data import WIND_STRENGTH
from utils.weather_mechanics import get_weather_effects


class StageDisplayManager:
    """
    Manages multi-day stage weather display.
    
    Responsibilities:
    - Display stage summary views
    - Display stage detailed views
    - Format multi-day weather data
    """
    
    def __init__(self):
        self.formatters = WeatherFormatters()
    
    async def show_stage_summary(
        self,
        context,
        stage_data: dict,
        is_slash: bool
    ):
        """
        Display summary view of stage weather.
        
        Args:
            context: Discord context
            stage_data: Dict with stage_num, start_day, duration, season, province, weathers
            is_slash: Whether this is a slash command
        """
        embed = self._create_stage_summary_embed(stage_data)
        await self._send_embed(context, embed, is_slash)
    
    async def show_stage_detailed(
        self,
        context,
        stage_data: dict,
        is_slash: bool
    ):
        """Display detailed view of stage weather."""
        embed = self._create_stage_detailed_embed(stage_data)
        await self._send_embed(context, embed, is_slash)
    
    def _create_stage_summary_embed(self, stage_data: dict) -> discord.Embed:
        """Create summary embed for stage."""
        stage_num = stage_data['stage_num']
        start_day = stage_data['start_day']
        duration = stage_data['duration']
        end_day = start_day + duration - 1
        
        embed = discord.Embed(
            title=f"🗺️ Stage {stage_num} Complete (Days {start_day}-{end_day})",
            description=(
                f"**{stage_data['season'].title()}** in "
                f"**{stage_data['province'].replace('_', ' ').title()}**\n\n"
                f"Weather generated for {duration} days of travel."
            ),
            color=discord.Color.purple()
        )
        
        # Add each day's summary
        for day_num, weather_data in stage_data['weathers']:
            day_summary = self._format_day_summary(day_num, weather_data)
            embed.add_field(
                name=f"Day {day_num}",
                value=day_summary,
                inline=False
            )
        
        # Navigation info
        self._add_navigation_footer(embed, stage_num, start_day, "simple")
        
        return embed
    
    def _create_stage_detailed_embed(self, stage_data: dict) -> discord.Embed:
        """Create detailed embed for stage."""
        # Similar to summary but with more details per day
        pass
    
    def _format_day_summary(self, day_num: int, weather_data: dict) -> str:
        """Format a single day's summary."""
        weather_type = weather_data["weather_type"]
        weather_emoji = self.formatters.get_weather_emoji(weather_type)
        temp_emoji = self.formatters.get_temperature_emoji(
            weather_data["temperature_actual"]
        )
        
        weather_effects = get_weather_effects(weather_type)
        
        summary = (
            f"{weather_emoji} {weather_effects['name']} | "
            f"{temp_emoji} {weather_data['temperature_actual']}°C"
        )
        
        # Special events
        if weather_data["cold_front_days_remaining"] > 0:
            summary += " | ❄️ Cold Front"
        if weather_data["heat_wave_days_remaining"] > 0:
            summary += " | 🔥 Heat Wave"
        
        return summary
    
    def _add_navigation_footer(
        self,
        embed: discord.Embed,
        stage_num: int,
        start_day: int,
        mode: str
    ):
        """Add navigation instructions to embed."""
        mode_toggle = (
            "detailed" if mode == "simple" else "simple"
        )
        
        embed.add_field(
            name="📖 Next Steps",
            value=(
                f"• Use `/weather view {start_day}` to see detailed weather for any day\n"
                f"• Use `/weather next-stage` to advance to Stage {stage_num + 1}\n"
                f"• Use `/weather next` for day-by-day progression\n"
                f"• Use `/weather-stage-config display_mode:{mode_toggle}` to switch view mode"
            ),
            inline=False
        )
    
    async def _send_embed(self, context, embed: discord.Embed, is_slash: bool):
        """Send embed to Discord."""
        if is_slash:
            if hasattr(context, "response") and not context.response.is_done():
                await context.response.send_message(embed=embed)
            else:
                await context.followup.send(embed=embed)
        else:
            await context.send(embed=embed)
```

**Key Features:**
- Dedicated to multi-day display
- Reuses formatters for consistency
- Clean data structures in/out

---

### 5. `commands/weather/notifications.py` (Notifications - 100 lines)

**Responsibility:** Send notifications to GM channel

```python
"""
Notification manager - handles GM channel notifications.
"""

import discord
from typing import Optional

from commands.weather.formatters import WeatherFormatters
from db.weather_data import WIND_STRENGTH, WIND_DIRECTION
from utils.weather_mechanics import get_wind_modifiers


class NotificationManager:
    """
    Manages notifications to GM channels.
    
    Responsibilities:
    - Send mechanics notifications
    - Format modifier information
    - Handle channel not found gracefully
    """
    
    def __init__(self):
        self.formatters = WeatherFormatters()
    
    async def send_mechanics(
        self,
        context,
        weather_data: dict
    ):
        """
        Send mechanics notification to GM channel.
        
        Args:
            context: Discord context
            weather_data: Weather data dictionary
        """
        guild = context.guild
        if not guild:
            return
        
        channel = self._find_notifications_channel(guild)
        if not channel:
            return  # Silently skip if channel doesn't exist
        
        embed = self._create_mechanics_embed(weather_data)
        
        try:
            await channel.send(embed=embed)
        except (discord.DiscordException, AttributeError):
            pass  # Silently fail
    
    def _find_notifications_channel(
        self,
        guild: discord.Guild
    ) -> Optional[discord.TextChannel]:
        """Find the GM notifications channel."""
        return discord.utils.get(
            guild.text_channels,
            name="boat-travelling-notifications"
        )
    
    def _create_mechanics_embed(self, weather_data: dict) -> discord.Embed:
        """Create mechanics notification embed."""
        embed = discord.Embed(
            title="⚠️ Active Weather Mechanics",
            description=(
                f"Weather conditions for {weather_data['season'].title()} in "
                f"{weather_data['province'].replace('_', ' ').title()}"
            ),
            color=discord.Color.gold()
        )
        
        # Wind modifiers
        wind_text = self._format_wind_modifiers(weather_data['wind_timeline'])
        embed.add_field(
            name="🚢 Boat Handling Modifiers",
            value=wind_text,
            inline=False
        )
        
        # Weather penalties
        effects = weather_data['weather_effects']['effects']
        if effects and effects[0] != "No weather-related hazards":
            effects_text = "\n".join(f"• {effect}" for effect in effects)
            embed.add_field(
                name="🎯 Active Penalties & Conditions",
                value=effects_text,
                inline=False
            )
        
        # Temperature
        temp_description = weather_data.get('temp_feel_text', '')
        if temp_description:
            embed.add_field(
                name="🌡️ Temperature",
                value=temp_description,
                inline=False
            )
        
        # Notes
        embed.add_field(
            name="💡 Notes",
            value="• Wind may change at midday, dusk, or midnight (10% chance each check)",
            inline=False
        )
        
        return embed
    
    def _format_wind_modifiers(self, wind_timeline: list) -> str:
        """Format wind modifiers for mechanics display."""
        lines = []
        for wind_entry in wind_timeline:
            modifiers = get_wind_modifiers(
                wind_entry["strength"], wind_entry["direction"]
            )
            strength_name = WIND_STRENGTH[wind_entry["strength"]]
            direction_name = WIND_DIRECTION[wind_entry["direction"]]
            
            lines.append(
                f"**{wind_entry['time']}:** {strength_name} {direction_name}"
            )
            
            modifier_display = self.formatters.format_modifier_for_display(
                modifiers["modifier"]
            )
            lines.append(f"  └─ {modifier_display}")
            
            if modifiers["notes"]:
                lines.append(f"  └─ *{modifiers['notes']}*")
        
        return "\n".join(lines)
```

**Key Features:**
- Isolated notification logic
- Graceful failure if channel missing
- Reuses formatters for consistency

---

### 6. `commands/weather/formatters.py` (Utilities - 100 lines)

**Responsibility:** Pure formatting functions

```python
"""
Weather formatters - utility functions for formatting weather data.
"""


class WeatherFormatters:
    """
    Utility class for weather formatting.
    
    All methods are static/pure functions for easy testing.
    """
    
    @staticmethod
    def get_weather_emoji(weather_type: str) -> str:
        """Get emoji for weather type."""
        emojis = {
            "dry": "☀️",
            "fair": "🌤️",
            "rain": "🌧️",
            "downpour": "⛈️",
            "snow": "❄️",
            "blizzard": "🌨️",
        }
        return emojis.get(weather_type, "🌤️")
    
    @staticmethod
    def get_temperature_emoji(temp: int) -> str:
        """Get emoji for temperature."""
        if temp < -5:
            return "🥶"
        elif temp < 5:
            return "❄️"
        elif temp < 15:
            return "🌡️"
        elif temp < 25:
            return "☀️"
        else:
            return "🔥"
    
    @staticmethod
    def format_modifier_for_display(modifier_str: str) -> str:
        """
        Format wind modifier for clearer display.
        
        Args:
            modifier_str: Raw modifier string like "-10 penalty, 25% speed"
            
        Returns:
            Formatted string with clear explanations
        """
        if "penalty" in modifier_str.lower():
            parts = modifier_str.split(",")
            penalty_part = parts[0].strip()
            speed_part = parts[1].strip() if len(parts) > 1 else None
            
            penalty_num = penalty_part.split()[0]
            
            result = f"**Movement Speed:** {speed_part}\n"
            result += f"  └─ **Boat Handling Tests:** {penalty_num}"
            return result
        elif modifier_str == "—":
            return "No modifier to movement or tests"
        else:
            return f"**Movement Speed:** {modifier_str}"
    
    @staticmethod
    def format_province_name(province: str) -> str:
        """Format province name for display."""
        return province.replace("_", " ").title()
    
    @staticmethod
    def format_season_name(season: str) -> str:
        """Format season name for display."""
        return season.title()
```

**Key Features:**
- Static methods (no state)
- Easy to test in isolation
- Single source of truth for formatting

---

## 🧪 Testing Strategy

### Phase 1: Preserve Existing Tests
**Goal:** Ensure all 345 existing tests pass without modification

**Approach:**
1. Run full test suite before refactoring: `pytest tests/ -v`
2. Capture baseline coverage: `pytest --cov=. --cov-report=html`
3. After each refactoring step, re-run tests
4. Any failures indicate broken backward compatibility

### Phase 2: New Unit Tests for Refactored Modules
**Goal:** Achieve >90% coverage for new modules

#### Test Files to Create:

**1. `tests/test_weather_refactored/test_handler.py` (15-20 tests)**
```python
"""Tests for WeatherCommandHandler."""

class TestWeatherCommandHandler:
    def test_handler_initialization(self):
        """Test handler creates dependencies."""
        handler = WeatherCommandHandler()
        assert handler.storage is not None
        assert handler.display is not None
        assert handler.notifications is not None
    
    def test_handle_command_routes_correctly(self, mock_context):
        """Test action routing works."""
        # Test each action routes to correct method
        pass
    
    def test_generate_daily_weather_structure(self):
        """Test _generate_daily_weather returns correct structure."""
        # Verify all required keys present
        pass
    
    def test_generate_daily_weather_continuity(self):
        """Test wind continuity from previous day."""
        pass
    
    def test_generate_daily_weather_special_events(self):
        """Test cold front/heat wave handling."""
        pass
    
    def test_auto_start_journey_on_first_next(self):
        """Test journey auto-starts with defaults."""
        pass
    
    # 10-15 more tests...
```

**2. `tests/test_weather_refactored/test_display.py` (20-25 tests)**
```python
"""Tests for WeatherDisplayManager."""

class TestWeatherDisplayManager:
    def test_create_daily_weather_embed_structure(self):
        """Test embed has correct structure."""
        display = WeatherDisplayManager()
        weather_data = {...}  # Sample data
        embed = display._create_daily_weather_embed(weather_data, False)
        
        assert embed.title.startswith("📅")
        assert len(embed.fields) >= 3  # Wind, Weather, Temperature
    
    def test_format_wind_conditions(self):
        """Test wind formatting."""
        pass
    
    def test_format_temperature_with_wind_chill(self):
        """Test temperature display with wind chill."""
        pass
    
    def test_format_temperature_without_wind_chill(self):
        """Test temperature display without wind chill."""
        pass
    
    def test_format_special_events_cold_front(self):
        """Test cold front display."""
        pass
    
    def test_format_special_events_heat_wave(self):
        """Test heat wave display."""
        pass
    
    def test_historical_embed_styling(self):
        """Test historical marker shows correctly."""
        pass
    
    # 15-20 more tests...
```

**3. `tests/test_weather_refactored/test_stages.py` (10-15 tests)**
```python
"""Tests for StageDisplayManager."""

class TestStageDisplayManager:
    def test_stage_summary_embed_structure(self):
        """Test stage summary embed."""
        pass
    
    def test_stage_detailed_embed_structure(self):
        """Test stage detailed embed."""
        pass
    
    def test_format_day_summary(self):
        """Test day summary formatting."""
        pass
    
    def test_navigation_footer_content(self):
        """Test navigation instructions."""
        pass
    
    # 8-12 more tests...
```

**4. `tests/test_weather_refactored/test_notifications.py` (8-12 tests)**
```python
"""Tests for NotificationManager."""

class TestNotificationManager:
    def test_find_notifications_channel_exists(self):
        """Test channel found when exists."""
        pass
    
    def test_find_notifications_channel_not_exists(self):
        """Test graceful handling when channel missing."""
        pass
    
    def test_mechanics_embed_structure(self):
        """Test mechanics embed format."""
        pass
    
    def test_format_wind_modifiers(self):
        """Test wind modifier formatting."""
        pass
    
    # 5-9 more tests...
```

**5. `tests/test_weather_refactored/test_formatters.py` (10-15 tests)**
```python
"""Tests for WeatherFormatters."""

class TestWeatherFormatters:
    def test_get_weather_emoji_all_types(self):
        """Test emoji for each weather type."""
        assert WeatherFormatters.get_weather_emoji("dry") == "☀️"
        assert WeatherFormatters.get_weather_emoji("fair") == "🌤️"
        # ... all types
    
    def test_get_temperature_emoji_ranges(self):
        """Test temperature emoji ranges."""
        assert WeatherFormatters.get_temperature_emoji(-10) == "🥶"
        assert WeatherFormatters.get_temperature_emoji(0) == "❄️"
        # ... all ranges
    
    def test_format_modifier_with_penalty(self):
        """Test modifier formatting with penalty."""
        result = WeatherFormatters.format_modifier_for_display("-10 penalty, 25% speed")
        assert "Movement Speed: 25% speed" in result
        assert "Boat Handling Tests: -10" in result
    
    def test_format_modifier_simple(self):
        """Test simple modifier formatting."""
        result = WeatherFormatters.format_modifier_for_display("+10%")
        assert "Movement Speed: +10%" in result
    
    def test_format_modifier_no_modifier(self):
        """Test no modifier case."""
        result = WeatherFormatters.format_modifier_for_display("—")
        assert "No modifier" in result
    
    # 6-11 more tests...
```

**Total New Tests:** ~65-85 tests

### Phase 3: Integration Tests
**Goal:** Verify modules work together correctly

```python
"""Integration tests for refactored weather system."""

class TestWeatherIntegration:
    def test_full_next_day_flow(self, mock_bot):
        """Test complete /weather next flow."""
        # From command → handler → display → notification
        pass
    
    def test_full_stage_flow(self, mock_bot):
        """Test complete /weather next-stage flow."""
        pass
    
    def test_view_historical_day(self, mock_bot):
        """Test viewing past day."""
        pass
    
    # 5-8 more integration tests...
```

---

## 📋 Implementation Steps

### Step 1: Create Module Structure (1 hour)
```bash
# Create new directory
mkdir -p commands/weather

# Create __init__.py
touch commands/weather/__init__.py

# Create module files
touch commands/weather/handler.py
touch commands/weather/display.py
touch commands/weather/stages.py
touch commands/weather/notifications.py
touch commands/weather/formatters.py

# Create test directory
mkdir -p tests/test_weather_refactored
touch tests/test_weather_refactored/__init__.py
touch tests/test_weather_refactored/test_handler.py
touch tests/test_weather_refactored/test_display.py
touch tests/test_weather_refactored/test_stages.py
touch tests/test_weather_refactored/test_notifications.py
touch tests/test_weather_refactored/test_formatters.py
```

### Step 2: Implement Formatters First (2 hours)
**Why first?** No dependencies, pure functions, easy to test

1. Implement `formatters.py`
2. Write tests for `test_formatters.py`
3. Run tests: `pytest tests/test_weather_refactored/test_formatters.py -v`
4. Verify 100% coverage for formatters

### Step 3: Implement Display Manager (4 hours)
**Dependencies:** formatters.py

1. Implement `display.py`
2. Write tests for `test_display.py`
3. Run tests
4. Verify display logic works in isolation

### Step 4: Implement Notifications Manager (2 hours)
**Dependencies:** formatters.py

1. Implement `notifications.py`
2. Write tests for `test_notifications.py`
3. Run tests

### Step 5: Implement Stage Manager (3 hours)
**Dependencies:** formatters.py

1. Implement `stages.py`
2. Write tests for `test_stages.py`
3. Run tests

### Step 6: Implement Handler (6 hours)
**Dependencies:** All above modules

1. Implement `handler.py`
2. Write tests for `test_handler.py`
3. Run tests
4. This is the most complex module

### Step 7: Update Main Command File (2 hours)
**Critical:** This connects everything

1. Update `commands/weather.py` to use new handler
2. Keep same command signatures
3. No changes to Discord command registration

### Step 8: Run All Tests (1 hour)
```bash
# Run ALL tests including existing ones
pytest tests/ -v

# Check coverage
pytest --cov=. --cov-report=html

# Verify no regressions
# All 345 existing tests MUST pass
```

### Step 9: Integration Testing (2 hours)
1. Manually test each command in Discord
2. Verify all channels work
3. Check edge cases

### Step 10: Documentation (1 hour)
1. Update docstrings
2. Add module-level documentation
3. Update COMMANDS_DOCUMENTATION.md if needed

**Total Estimated Time:** 24 hours (~3 days)

---

## 🎯 Success Metrics

### Must-Have (Critical)
- [ ] All 345 existing tests pass without modification
- [ ] New tests achieve >90% coverage for new modules
- [ ] Code compiles with 0 errors
- [ ] All commands work identically from user perspective
- [ ] No performance degradation

### Should-Have (Important)
- [ ] Main `weather.py` file < 300 lines
- [ ] Each module has clear, single responsibility
- [ ] New tests total 65+ tests
- [ ] Documentation updated
- [ ] Type hints added where appropriate

### Could-Have (Nice to Have)
- [ ] Pre-commit hooks for linting
- [ ] Automated test running on save
- [ ] Performance benchmarks
- [ ] Module dependency diagram

---

## 🔄 Rollback Plan

If refactoring causes issues:

1. **Keep original `weather.py` as `weather_original.py`**
2. **Git branching:**
   ```bash
   git checkout -b refactor-weather-system
   # Do all work on branch
   # Only merge to main after all tests pass
   ```
3. **Quick rollback:**
   ```bash
   git checkout main
   # Original code preserved
   ```

---

## 💡 Benefits of This Refactoring

### Immediate Benefits
1. **Easier to Add OpenAI Integration**
   - Clear place to add JSON serialization (handler)
   - Clear place to add narrative display (display manager)
   - Clear place to add log channel (notifications manager)

2. **Better Testing**
   - Test each module in isolation
   - Mock dependencies easily
   - Fast test execution

3. **Easier Debugging**
   - Know exactly which module handles what
   - Stack traces more meaningful
   - Clear data flow

### Long-term Benefits
1. **Maintainability**
   - New developers understand structure quickly
   - Changes localized to specific modules
   - Reduced risk of breaking changes

2. **Extensibility**
   - Easy to add new command actions
   - Easy to add new display formats
   - Easy to add new notification channels

3. **Reusability**
   - Formatters used by multiple modules
   - Display logic shareable
   - Handler pattern reusable for other commands

---

## 📝 Example: Before vs After

### Before (Monolithic)
```python
# weather.py - 1262 lines
# Everything mixed together
async def _display_weather(context, day, season, province, wind_timeline, 
                          weather_type, weather_effects, actual_temp, 
                          perceived_temp, base_temp, temp_category, 
                          temp_description, most_common_wind, 
                          cold_front_days, heat_wave_days, 
                          continuity_note, is_slash, is_historical=False):
    # 100 lines of embed creation
    # Mixed with Discord API calls
    # Hard to test
```

### After (Modular)
```python
# commands/weather.py - 250 lines
@bot.tree.command(name="weather", ...)
async def weather_slash(interaction, action, season, province, day):
    await handler.handle_command(interaction, action, season, province, day, True)

# commands/weather/handler.py
class WeatherCommandHandler:
    async def generate_next_day(self, context, guild_id, ...):
        weather_data = self._generate_daily_weather(guild_id, journey)
        await self.display.show_daily_weather(context, weather_data, is_slash)
        await self.notifications.send_mechanics(context, weather_data)

# commands/weather/display.py
class WeatherDisplayManager:
    async def show_daily_weather(self, context, weather_data, is_slash):
        embed = self._create_daily_weather_embed(weather_data, is_historical)
        await self._send_embed(context, embed, is_slash)
    
    def _create_daily_weather_embed(self, weather_data, is_historical):
        # Pure function - easy to test
        # Returns embed - no Discord API calls
```

---

## 🚀 Next Steps After Refactoring

Once refactoring is complete and all tests pass:

1. **Phase 1 of OpenAI Integration becomes easier:**
   - Add JSON serialization in `handler.py`
   - Add to weather_data dict before passing to display
   
2. **Phase 2 of OpenAI Integration becomes easier:**
   - Add new method to `NotificationManager`
   - `send_weather_log(guild, weather_json)`
   
3. **Phase 4 of OpenAI Integration becomes easier:**
   - Add new method to `WeatherDisplayManager`
   - `show_narrative_weather(context, narrative, weather_json, is_slash)`
   - Toggle between `show_daily_weather` and `show_narrative_weather`

---

## ⚠️ Risks and Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Breaking existing functionality | 🔴 High | 🟡 Medium | Run all 345 tests after each step |
| Tests fail after refactoring | 🔴 High | 🟡 Medium | Branch strategy + rollback plan |
| Performance degradation | 🟡 Medium | 🟢 Low | Benchmark before/after |
| Time overrun | 🟡 Medium | 🟡 Medium | Work in small, testable increments |
| Module coupling too tight | 🟡 Medium | 🟢 Low | Use dependency injection |
| Inconsistent data structures | 🟡 Medium | 🟡 Medium | Define clear interfaces early |

---

## 📚 Appendix: Module Dependency Graph

```
commands/weather.py
    └─> WeatherCommandHandler (handler.py)
            ├─> WeatherStorage (db/weather_storage.py)
            ├─> weather_mechanics (utils/weather_mechanics.py)
            ├─> WeatherDisplayManager (display.py)
            │       └─> WeatherFormatters (formatters.py)
            ├─> StageDisplayManager (stages.py)
            │       └─> WeatherFormatters (formatters.py)
            └─> NotificationManager (notifications.py)
                    └─> WeatherFormatters (formatters.py)
```

**Key Insight:** Formatters have no dependencies (pure functions)

---

## ✅ Approval Checklist

Before proceeding with refactoring:

- [ ] Review module responsibilities
- [ ] Confirm test strategy
- [ ] Verify rollback plan
- [ ] Check estimated timeline acceptable
- [ ] Confirm all 345 tests must pass
- [ ] Agree on success metrics
- [ ] Backup current code
- [ ] Create feature branch

**Ready to proceed?** Let's refactor! 🚀
