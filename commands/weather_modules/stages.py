"""
Stage Display Manager for Weather Commands

This module handles multi-day stage displays for weather data.
When journeys are broken into stages, this provides consolidated
views of multiple days of weather at once.

Design Principles:
- Efficient display: Show multiple days in compact format
- Clear navigation: Users can see progress through stages
- Consistency: Uses same formatters as single-day displays
"""

from typing import List, Dict, Any, Optional
import discord
from datetime import datetime, timezone

from .formatters import WeatherFormatters


class StageDisplayManager:
    """
    Manages multi-day stage displays for weather data.

    This class is responsible for:
    - Creating stage summary embeds showing multiple days
    - Formatting condensed weather information
    - Providing overview of weather patterns across stages
    """

    COLOR_STAGE = 0x9B59B6  # Purple for stages

    @staticmethod
    async def show_stage_summary(
        context,
        stage_number: int,
        stage_data: List[Dict[str, Any]],
        is_slash: bool = False,
    ) -> None:
        """
        Display a summary of weather for an entire stage.

        Args:
            context: Discord context (can be ctx for prefix or interaction for slash)
            stage_number: The stage number being displayed
            stage_data: List of weather data dictionaries, one per day
            is_slash: Whether this is a slash command response
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
                title=f"🚢 Stage {stage_number}",
                description="No weather data available for this stage.",
                color=StageDisplayManager.COLOR_STAGE,
            )

        # Get basic info from first day
        first_day = stage_data[0]
        province = first_day.get("province", "Unknown")
        season = first_day.get("season", "spring")

        province_name = WeatherFormatters.format_province_name(province)
        season_name = WeatherFormatters.format_season_name(season)

        # Create embed
        embed = discord.Embed(
            title=f"🚢 Stage {stage_number} Weather Summary",
            description=f"**{province_name}** | **{season_name}** | {len(stage_data)} day{'s' if len(stage_data) != 1 else ''}",
            color=StageDisplayManager.COLOR_STAGE,
            timestamp=datetime.now(timezone.utc),
        )

        # Add each day as a field
        for day_data in stage_data:
            day_text = StageDisplayManager._format_day_summary(day_data)
            day_num = day_data.get("day", "?")

            embed.add_field(name=f"📅 Day {day_num}", value=day_text, inline=False)

        # Add footer
        embed.set_footer(
            text="Use /weather [day] to see detailed weather for a specific day"
        )

        return embed

    @staticmethod
    def _format_day_summary(day_data: Dict[str, Any]) -> str:
        """
        Format a single day's weather into a condensed summary.

        Args:
            day_data: Dictionary containing weather information

        Returns:
            str: Condensed weather summary
        """
        weather_type = day_data.get("weather_type", "fair")
        temperature = day_data.get("temperature", 15)
        wind_timeline = day_data.get("wind_timeline", {})
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
            parts.append(f"💨 {wind_summary}")

        # Add effects if any (show count if many)
        if weather_effects:
            if len(weather_effects) <= 2:
                for effect in weather_effects:
                    parts.append(f"⚠️ {effect}")
            else:
                parts.append(f"⚠️ {len(weather_effects)} weather effects")

        return "\n".join(parts)

    @staticmethod
    def _format_condensed_wind(wind_timeline: Dict[str, Dict[str, Any]]) -> str:
        """
        Format wind conditions into a very condensed format for stage view.

        Args:
            wind_timeline: Dictionary with wind data for each time of day

        Returns:
            str: Ultra-condensed wind summary (e.g., "Light N → Bracing NE")
        """
        if not wind_timeline:
            return "Calm"

        # Get unique wind conditions
        conditions = []
        seen = set()

        time_order = ["dawn", "morning", "afternoon", "evening", "night"]
        for time_of_day in time_order:
            if time_of_day not in wind_timeline:
                continue

            wind_data = wind_timeline[time_of_day]
            strength = wind_data.get("strength", "calm")
            direction = wind_data.get("direction", "")

            if strength.lower() == "calm":
                condition_key = "calm"
                condition_str = "Calm"
            else:
                condition_key = f"{strength}_{direction}"
                strength_display = strength.replace("_", " ").title()
                condition_str = f"{strength_display} {direction}"

            if condition_key not in seen:
                conditions.append(condition_str)
                seen.add(condition_key)

        if not conditions:
            return "Calm"

        if len(conditions) == 1:
            return conditions[0]
        else:
            return " → ".join(conditions)

    @staticmethod
    async def show_all_stages(
        context, stages_data: Dict[int, List[Dict[str, Any]]], is_slash: bool = False
    ) -> None:
        """
        Display an overview of all stages in the journey.

        Args:
            context: Discord context
            stages_data: Dictionary mapping stage numbers to lists of day data
            is_slash: Whether this is a slash command response
        """
        embed = StageDisplayManager._create_all_stages_embed(stages_data)
        await StageDisplayManager._send_embed(context, embed, is_slash)

    @staticmethod
    def _create_all_stages_embed(
        stages_data: Dict[int, List[Dict[str, Any]]],
    ) -> discord.Embed:
        """
        Create an embed showing overview of all stages.

        Args:
            stages_data: Dictionary mapping stage numbers to day data lists

        Returns:
            discord.Embed: Overview embed
        """
        if not stages_data:
            return discord.Embed(
                title="🗺️ Journey Overview",
                description="No journey data available.",
                color=StageDisplayManager.COLOR_STAGE,
            )

        total_stages = len(stages_data)
        total_days = sum(len(days) for days in stages_data.values())

        # Get province/season from first stage
        first_stage_data = stages_data[min(stages_data.keys())]
        if first_stage_data:
            province = first_stage_data[0].get("province", "Unknown")
            season = first_stage_data[0].get("season", "spring")
            province_name = WeatherFormatters.format_province_name(province)
            season_name = WeatherFormatters.format_season_name(season)
            description = f"**{province_name}** | **{season_name}**\n{total_stages} stages | {total_days} days total"
        else:
            description = f"{total_stages} stages | {total_days} days total"

        embed = discord.Embed(
            title="🗺️ Journey Overview",
            description=description,
            color=StageDisplayManager.COLOR_STAGE,
            timestamp=datetime.now(timezone.utc),
        )

        # Add each stage as a field
        for stage_num in sorted(stages_data.keys()):
            stage_days = stages_data[stage_num]
            stage_summary = StageDisplayManager._format_stage_overview(stage_days)

            embed.add_field(
                name=f"🚢 Stage {stage_num}", value=stage_summary, inline=True
            )

        embed.set_footer(
            text="Use /weather stage [number] to see details for a specific stage"
        )

        return embed

    @staticmethod
    def _format_stage_overview(stage_days: List[Dict[str, Any]]) -> str:
        """
        Format a very brief overview of a stage.

        Args:
            stage_days: List of day data for this stage

        Returns:
            str: Brief stage summary
        """
        if not stage_days:
            return "No data"

        num_days = len(stage_days)

        # Count weather types
        weather_counts = {}
        for day in stage_days:
            weather = day.get("weather_type", "fair")
            weather_counts[weather] = weather_counts.get(weather, 0) + 1

        # Get most common weather
        most_common = max(weather_counts.items(), key=lambda x: x[1])
        weather_emoji = WeatherFormatters.get_weather_emoji(most_common[0])

        # Get temperature range
        temps = [day.get("temperature", 15) for day in stage_days]
        min_temp = min(temps)
        max_temp = max(temps)

        if min_temp == max_temp:
            temp_str = f"{min_temp}°C"
        else:
            temp_str = f"{min_temp}-{max_temp}°C"

        return f"{num_days} day{'s' if num_days != 1 else ''}\n{weather_emoji} {most_common[0].replace('_', ' ').title()}\n🌡️ {temp_str}"

    @staticmethod
    async def _send_embed(
        context, embed: discord.Embed, is_slash: bool = False
    ) -> None:
        """
        Send an embed to Discord, handling both slash and prefix commands.

        Args:
            context: Discord context (ctx or interaction)
            embed: The embed to send
            is_slash: Whether this is a slash command
        """
        if is_slash:
            if context.response.is_done():
                await context.followup.send(embed=embed)
            else:
                await context.response.send_message(embed=embed)
        else:
            await context.send(embed=embed)
