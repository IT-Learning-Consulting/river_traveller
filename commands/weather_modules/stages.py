"""
Stage Display Manager for Weather Commands

This module handles multi-day stage displays for weather data. When journeys
are broken into stages, this provides consolidated views of multiple days of
weather at once for efficient planning and review.

Key Responsibilities:
    - Display consolidated weather summaries for multi-day stages
    - Show progress through journey stages
    - Provide overview of weather patterns across entire journeys
    - Format condensed weather information for quick scanning

Design Principles:
    - Efficient display: Show multiple days in compact format
    - Clear navigation: Users can see progress through stages
    - Consistency: Uses same formatters as single-day displays
    - Scalability: Handles variable stage durations gracefully

Display Modes:
    - Stage Summary: Shows all days in a single stage with condensed info
    - Journey Overview: Shows all stages in journey with statistics
    - Day Summary: Individual day condensed into 3-4 lines

Usage Example:
    >>> # Show stage summary
    >>> await StageDisplayManager.show_stage_summary(ctx, 2, stage_days, False)
    >>> # Show all stages
    >>> await StageDisplayManager.show_all_stages(ctx, all_stages, True)
"""

from typing import Any, Dict, List, Optional, Union

import discord
from discord.ext import commands
from datetime import datetime, timezone

from .formatters import WeatherFormatters

# Embed colors
COLOR_STAGE = 0x9B59B6  # Purple for stages

# Default values
DEFAULT_PROVINCE = "Unknown"
DEFAULT_SEASON = "spring"
DEFAULT_WEATHER = "fair"
DEFAULT_TEMPERATURE = 15
DEFAULT_DAY = 1

# Display messages
MSG_NO_STAGE_DATA = "No weather data available for this stage."
MSG_NO_JOURNEY_DATA = "No journey data available."
MSG_NO_DATA = "No data"
MSG_CALM_WIND = "Calm"

# Footer messages
FOOTER_VIEW_DAY = "Use /weather [day] to see detailed weather for a specific day"
FOOTER_VIEW_STAGE = "Use /weather stage [number] to see details for a specific stage"

# Emoji
EMOJI_SHIP = "🚢"
EMOJI_MAP = "🗺️"
EMOJI_CALENDAR = "📅"
EMOJI_TEMPERATURE = "🌡️"
EMOJI_WARNING = "⚠️"
EMOJI_WIND = "💨"
EMOJI_COLD_FRONT = "❄️"
EMOJI_HEAT_WAVE = "🔥"


class StageDisplayManager:
    """
    Manages multi-day stage displays and journey overviews.

    This class provides static methods for displaying consolidated weather
    information across multiple days (stages) or multiple stages (journeys).
    All displays are condensed for efficient scanning while preserving
    essential mechanical information.

    Responsibilities:
        - Create stage summary embeds showing all days in a stage
        - Format condensed daily weather summaries
        - Display journey overviews with all stages
        - Handle wind, temperature, and effect summarization
        - Show special event progress (cold fronts, heat waves)

    Design Pattern:
        All methods are static as this class maintains no state. It serves
        purely as a utility namespace for stage display operations.

    Display Strategy:
        - Condensed: Each day shown in 3-4 lines
        - Patterns: Shows changing conditions (calm → bracing wind)
        - Statistics: Temperature ranges, weather type counts
        - Progress: Special event day counters

    Example:
        >>> # Display a single stage
        >>> stage_days = [day1_data, day2_data, day3_data]
        >>> await StageDisplayManager.show_stage_summary(ctx, 2, stage_days, False)
        >>> # Display all stages
        >>> all_stages = {1: [...], 2: [...], 3: [...]}
        >>> await StageDisplayManager.show_all_stages(ctx, all_stages, True)
    """

    COLOR_STAGE = COLOR_STAGE

    @staticmethod
    async def show_stage_summary(
        context: Union[discord.Interaction, commands.Context],
        stage_number: int,
        stage_data: List[Dict[str, Any]],
        is_slash: bool = False,
    ) -> None:
        """
        Display a consolidated summary of weather for an entire stage.

        Creates an embed showing condensed weather information for each day
        in the stage. Each day displays weather type, temperature, wind
        patterns, and any special effects in 3-4 lines.

        Args:
            context: Discord context (interaction for slash, ctx for prefix commands)
            stage_number: The stage number being displayed (1-based)
            stage_data: List of weather data dictionaries, one per day.
                Each dict should contain keys like: day, weather_type,
                temperature, wind_timeline, weather_effects
            is_slash: Whether this is a slash command response

        Returns:
            None: Sends embed directly to Discord

        Example:
            >>> stage_days = [
            ...     {"day": 1, "weather_type": "rain", "temperature": 12, ...},
            ...     {"day": 2, "weather_type": "fair", "temperature": 15, ...},
            ...     {"day": 3, "weather_type": "fair", "temperature": 14, ...}
            ... ]
            >>> await StageDisplayManager.show_stage_summary(ctx, 2, stage_days, False)
        """
        embed = StageDisplayManager._create_stage_embed(stage_number, stage_data)
        await StageDisplayManager._send_embed(context, embed, is_slash)

    @staticmethod
    def _create_stage_embed(
        stage_number: int, stage_data: List[Dict[str, Any]]
    ) -> discord.Embed:
        """
        Create a Discord embed for stage summary display.

        Args:
            stage_number: The stage number
            stage_data: List of weather data dictionaries

        Returns:
            discord.Embed: Configured embed ready to send
        """
        if not stage_data:
            return discord.Embed(
                title=f"{EMOJI_SHIP} Stage {stage_number}",
                description=MSG_NO_STAGE_DATA,
                color=StageDisplayManager.COLOR_STAGE,
            )

        # Get basic info from first day
        first_day = stage_data[0]
        province = first_day.get("province", DEFAULT_PROVINCE)
        season = first_day.get("season", DEFAULT_SEASON)

        province_name = WeatherFormatters.format_province_name(province)
        season_name = WeatherFormatters.format_season_name(season)

        # Create embed
        plural = "s" if len(stage_data) != 1 else ""
        embed = discord.Embed(
            title=f"{EMOJI_SHIP} Stage {stage_number} Weather Summary",
            description=f"**{province_name}** | **{season_name}** | {len(stage_data)} day{plural}",
            color=StageDisplayManager.COLOR_STAGE,
            timestamp=datetime.now(timezone.utc),
        )

        # Add each day as a field
        for day_data in stage_data:
            day_text = StageDisplayManager._format_day_summary(day_data)
            day_num = day_data.get("day", DEFAULT_DAY)

            embed.add_field(
                name=f"{EMOJI_CALENDAR} Day {day_num}", value=day_text, inline=False
            )

        # Add footer
        embed.set_footer(text=FOOTER_VIEW_DAY)

        return embed

    @staticmethod
    def _format_day_summary(day_data: Dict[str, Any]) -> str:
        """
        Format a single day's weather into a condensed 3-4 line summary.

        Creates a compact display showing weather type, temperature, wind
        conditions, effects, and any special events. Designed for quick
        scanning while preserving essential information.

        Args:
            day_data: Dictionary containing complete weather information with keys:
                - weather_type: Type of weather (e.g., "rain", "snow")
                - actual_temp or temperature: Temperature value
                - wind_timeline: List of wind conditions
                - weather_effects: List of active effect strings
                - cold_front_days_remaining: Optional cold front counter
                - heat_wave_days_remaining: Optional heat wave counter

        Returns:
            str: Multi-line condensed summary (typically 3-4 lines)

        Example:
            >>> day = {
            ...     "weather_type": "rain",
            ...     "temperature": 12,
            ...     "wind_timeline": [...],
            ...     "weather_effects": ["Visibility reduced"]
            ... }
            >>> StageDisplayManager._format_day_summary(day)
            '🌧️ **Rain** | 🌡️ 12°C\\n💨 Light North → Bracing East\\n⚠️ Visibility reduced'
        """
        weather_type = day_data.get("weather_type", DEFAULT_WEATHER)
        temperature = day_data.get(
            "actual_temp", day_data.get("temperature", DEFAULT_TEMPERATURE)
        )
        wind_timeline = day_data.get("wind_timeline", [])
        weather_effects = day_data.get("weather_effects", [])

        # Get emojis
        weather_emoji = WeatherFormatters.get_weather_emoji(weather_type)
        temp_emoji = WeatherFormatters.get_temperature_emoji(temperature)

        # Format weather type
        weather_name = weather_type.replace("_", " ").title()

        # Build summary parts
        parts = [f"{weather_emoji} **{weather_name}** | {temp_emoji} {temperature}°C"]

        # Add wind summary (condensed)
        wind_summary = StageDisplayManager._format_condensed_wind(wind_timeline)
        if wind_summary:
            parts.append(f"{EMOJI_WIND} {wind_summary}")

        # Add effects if any (show count if many)
        if weather_effects:
            if len(weather_effects) <= 2:
                for effect in weather_effects:
                    parts.append(f"{EMOJI_WARNING} {effect}")
            else:
                parts.append(f"{EMOJI_WARNING} {len(weather_effects)} weather effects")

        # Add special event information with day counters
        cold_front_days = day_data.get("cold_front_days_remaining", 0)
        cold_front_total = day_data.get("cold_front_total_duration", 0)
        heat_wave_days = day_data.get("heat_wave_days_remaining", 0)
        heat_wave_total = day_data.get("heat_wave_total_duration", 0)

        if cold_front_days > 0 and cold_front_total > 0:
            days_elapsed = cold_front_total - cold_front_days + 1
            event_text = (
                f"{EMOJI_COLD_FRONT} Cold Front (Day {days_elapsed}/{cold_front_total})"
            )
            if cold_front_days == 1:
                event_text += " (Final Day)"
            parts.append(event_text)

        if heat_wave_days > 0 and heat_wave_total > 0:
            days_elapsed = heat_wave_total - heat_wave_days + 1
            event_text = (
                f"{EMOJI_HEAT_WAVE} Heat Wave (Day {days_elapsed}/{heat_wave_total})"
            )
            if heat_wave_days == 1:
                event_text += " (Final Day)"
            parts.append(event_text)

        return "\n".join(parts)

    @staticmethod
    def _format_condensed_wind(wind_timeline: list) -> str:
        """
        Format wind conditions into ultra-condensed format for stage view.

        Shows unique wind conditions with arrows between changes. Deduplicates
        identical conditions to show only pattern changes.

        Args:
            wind_timeline: List of wind data dicts with 'time', 'strength', 'direction' keys

        Returns:
            str: Ultra-condensed wind summary. Examples:
                - "Calm" (all day calm)
                - "Light North" (one condition all day)
                - "Light Tailwind → Bracing Sidewind" (changing conditions)

        Example:
            >>> timeline = [
            ...     {'strength': 'light', 'direction': 'north'},
            ...     {'strength': 'bracing', 'direction': 'east'},
            ...     {'strength': 'bracing', 'direction': 'east'}  # duplicate ignored
            ... ]
            >>> StageDisplayManager._format_condensed_wind(timeline)
            'Light North → Bracing East'
        """
        if not wind_timeline:
            return MSG_CALM_WIND

        # Get unique wind conditions
        conditions = []
        seen = set()

        for wind_data in wind_timeline:
            strength = wind_data.get("strength", "calm")
            direction = wind_data.get("direction", "")

            if strength.lower() == "calm":
                condition_key = "calm"
                condition_str = "Calm"
            else:
                condition_key = f"{strength}_{direction}"
                strength_display = strength.replace("_", " ").title()
                direction_display = direction.replace("_", " ").title()
                condition_str = f"{strength_display} {direction_display}"

            if condition_key not in seen:
                conditions.append(condition_str)
                seen.add(condition_key)

        if not conditions:
            return MSG_CALM_WIND

        if len(conditions) == 1:
            return conditions[0]
        else:
            return " → ".join(conditions)

    @staticmethod
    async def show_all_stages(
        context: Union[discord.Interaction, commands.Context],
        stages_data: Dict[int, List[Dict[str, Any]]],
        is_slash: bool = False,
    ) -> None:
        """
        Display condensed overview of all journey stages.

        Creates single embed showing all stages with condensed weather summaries.
        Each stage shows duration and key weather patterns.

        Args:
            context: Discord interaction or context to send response
            stages_data: Dict mapping stage_number -> [days_data]. Each day has
                weather_data dict with weather/wind/temperature info
            is_slash: Whether this is a slash command response (default: False)

        Returns:
            None. Sends embed directly to context channel

        Example:
            >>> journey = {
            ...     1: [day1_data, day2_data],
            ...     2: [day3_data, day4_data, day5_data]
            ... }
            >>> await StageDisplayManager.show_all_stages(ctx, journey)
            # Sends: "🗺️ Journey Overview" embed with 2 stage fields
        """
        embed = StageDisplayManager._create_all_stages_embed(stages_data)
        await StageDisplayManager._send_embed(context, embed, is_slash)

    @staticmethod
    def _create_all_stages_embed(
        stages_data: Dict[int, List[Dict[str, Any]]],
    ) -> discord.Embed:
        """
        Create embed showing overview of all journey stages.

        Displays total stages/days count with province/season context. Each
        stage gets a condensed field showing duration and weather patterns.

        Args:
            stages_data: Dict mapping stage_number -> [days_data]. Each day dict
                contains weather_data with province/season/weather/temp info

        Returns:
            discord.Embed: Journey overview embed with stage summaries

        Example:
            >>> stages = {
            ...     1: [day1, day2],
            ...     2: [day3, day4, day5]
            ... }
            >>> embed = StageDisplayManager._create_all_stages_embed(stages)
            >>> print(embed.title)
            '🗺️ Journey Overview'
        """
        if not stages_data:
            return discord.Embed(
                title=f"{EMOJI_MAP} Journey Overview",
                description=MSG_NO_JOURNEY_DATA,
                color=StageDisplayManager.COLOR_STAGE,
            )

        total_stages = len(stages_data)
        total_days = sum(len(days) for days in stages_data.values())

        # Get province/season from first stage
        first_stage_data = stages_data[min(stages_data.keys())]
        if first_stage_data:
            province = first_stage_data[0].get("province", DEFAULT_PROVINCE)
            season = first_stage_data[0].get("season", DEFAULT_SEASON)
            province_name = WeatherFormatters.format_province_name(province)
            season_name = WeatherFormatters.format_season_name(season)
            description = f"**{province_name}** | **{season_name}**\n{total_stages} stages | {total_days} days total"
        else:
            description = f"{total_stages} stages | {total_days} days total"

        embed = discord.Embed(
            title=f"{EMOJI_MAP} Journey Overview",
            description=description,
            color=StageDisplayManager.COLOR_STAGE,
            timestamp=datetime.now(timezone.utc),
        )

        # Add each stage as a field
        for stage_num in sorted(stages_data.keys()):
            stage_days = stages_data[stage_num]
            stage_summary = StageDisplayManager._format_stage_overview(stage_days)

            embed.add_field(
                name=f"{EMOJI_SHIP} Stage {stage_num}", value=stage_summary, inline=True
            )

        embed.set_footer(text=FOOTER_VIEW_STAGE)

        return embed

    @staticmethod
    def _format_stage_overview(stage_days: List[Dict[str, Any]]) -> str:
        """
        Format very brief overview of a stage for journey summary.

        Shows duration, most common weather, and temperature range in compact
        3-line format. Designed for the all-stages overview display.

        Args:
            stage_days: List of day data dicts for this stage. Each day has
                weather_type, temperature, and other weather data

        Returns:
            str: Brief 3-line stage summary. Format:
                - Line 1: "X day(s)"
                - Line 2: "emoji Weather Type"
                - Line 3: "🌡️ temp-range°C"

        Example:
            >>> days = [
            ...     {"weather_type": "rain", "temperature": 12},
            ...     {"weather_type": "rain", "temperature": 14},
            ...     {"weather_type": "fair", "temperature": 16}
            ... ]
            >>> StageDisplayManager._format_stage_overview(days)
            '3 days\\n🌧️ Rain\\n🌡️ 12-16°C'
        """
        if not stage_days:
            return MSG_NO_DATA

        num_days = len(stage_days)

        # Count weather types
        weather_counts = {}
        for day in stage_days:
            weather = day.get("weather_type", DEFAULT_WEATHER)
            weather_counts[weather] = weather_counts.get(weather, 0) + 1

        # Get most common weather
        most_common = max(weather_counts.items(), key=lambda x: x[1])
        weather_emoji = WeatherFormatters.get_weather_emoji(most_common[0])

        # Get temperature range
        temps = [day.get("temperature", DEFAULT_TEMPERATURE) for day in stage_days]
        min_temp = min(temps)
        max_temp = max(temps)

        if min_temp == max_temp:
            temp_str = f"{min_temp}°C"
        else:
            temp_str = f"{min_temp}-{max_temp}°C"

        return f"{num_days} day{'s' if num_days != 1 else ''}\n{weather_emoji} {most_common[0].replace('_', ' ').title()}\n{EMOJI_TEMPERATURE} {temp_str}"

    @staticmethod
    async def _send_embed(
        context: Union[discord.Interaction, commands.Context],
        embed: discord.Embed,
        is_slash: bool = False,
    ) -> None:
        """
        Send embed to Discord, handling both slash and prefix commands.

        Automatically detects interaction vs context and uses appropriate
        response method. For interactions, uses response or followup based
        on whether initial response was already sent.

        Args:
            context: Discord interaction or context to send response
            embed: The embed to send
            is_slash: Whether this is a slash command (default: False).
                Auto-detected from context type if incorrect

        Returns:
            None. Sends embed directly to Discord channel

        Example:
            >>> embed = discord.Embed(title="Test")
            >>> await StageDisplayManager._send_embed(ctx, embed)
            # Sends embed using ctx.send()
            >>> await StageDisplayManager._send_embed(interaction, embed, is_slash=True)
            # Sends embed using interaction.response or followup
        """
        # Auto-detect if is_slash parameter is incorrect by checking context type
        if hasattr(context, "response"):
            if context.response.is_done():
                await context.followup.send(embed=embed)
            else:
                await context.response.send_message(embed=embed)
        else:
            await context.send(embed=embed)
