"""
DisplayService - Weather Display Layer

Handles all Discord embed creation and user-facing displays for weather data.
Provides clean separation between business logic and presentation layer.

Responsibilities:
    - Daily weather embed creation and display
    - Stage summary displays
    - Journey overview displays
    - Wind timeline formatting
    - Temperature and effects formatting
    - Error and info message displays
    - Color schemes and emoji consistency
    - Slash vs prefix command handling

Service Pattern:
    - Static methods only (no state)
    - Returns embeds or sends directly to Discord
    - Handles both Interaction (slash) and Context (prefix) types
    - Defensive with missing data (provides defaults)

Usage:
    >>> await DisplayService.show_daily_weather(ctx, weather_data, is_slash=False)
    >>> await DisplayService.send_error(ctx, "Journey not found")
"""

from typing import Any, Dict, List, Optional, Union
import discord
from datetime import datetime, timezone
from discord.ext import commands

from ..formatters import WeatherFormatters
from db.weather_data import WEATHER_EFFECTS


# Display color scheme
COLOR_DEFAULT = discord.Color.blue().value  # Blue - Default weather display
COLOR_PURPLE = discord.Color.purple().value  # Purple - Stage summaries
COLOR_ERROR = discord.Color.red().value  # Red - Error messages
COLOR_INFO = discord.Color.light_grey().value  # Gray - Informational messages

# Display emojis
EMOJI_HISTORICAL = "📜"
EMOJI_DAILY = "🌤️"
EMOJI_WIND = "💨"
EMOJI_EFFECTS = "⚠️"
EMOJI_ERROR = "❌"
EMOJI_INFO = "ℹ️"
EMOJI_CALM_WIND = "🌊"
EMOJI_STAGE = "🗺️"
EMOJI_JOURNEY = "🧭"
EMOJI_TEMPERATURE = "🌡️"

# Temperature difference thresholds
TEMP_DIFF_SIGNIFICANT = 10  # °C difference considered significant for wind chill

# Default display values
DEFAULT_PROVINCE = "Unknown"
DEFAULT_SEASON = "spring"
DEFAULT_WEATHER = "fair"
DEFAULT_TEMPERATURE = 15
DEFAULT_DAY = 1

# Footer text
FOOTER_TEXT = "Warhammer Fantasy Roleplay 4e | River Travel"


class DisplayService:
    """
    Service for creating and sending weather-related Discord embeds.

    All methods are static. This service maintains no state and serves
    purely as a utility for display formatting and message delivery.

    Methods fall into three categories:
    1. Public display methods (show_daily_weather, show_stage_summary, etc.)
    2. Private embed creation (_create_daily_weather_embed, etc.)
    3. Private formatting helpers (_format_wind_timeline, etc.)
    """

    @staticmethod
    async def show_daily_weather(
        context: Union[discord.Interaction, commands.Context],
        weather_data: Dict[str, Any],
        is_slash: bool = False,
        is_historical: bool = False,
        ephemeral: bool = False,
    ) -> None:
        """
        Display daily weather information in a formatted embed.

        Args:
            context: Discord context or interaction to respond to
            weather_data: Weather information dictionary with keys:
                - day: Journey day number
                - province: Location name
                - season: Current season
                - weather_type: Weather condition
                - actual_temp: Current temperature
                - perceived_temp: Temperature with wind chill
                - wind_timeline: List of wind conditions by time period
                - weather_effects: List of effect strings
                - temp_category: Temperature category (optional)
                - temp_description: Temperature description (optional)
            is_slash: Whether this is a slash command response
            is_historical: Whether this is historical weather display
            ephemeral: Whether message should be ephemeral (slash only)
        """
        embed = DisplayService._create_daily_weather_embed(weather_data, is_historical)
        await DisplayService._send_embed(context, embed, is_slash, ephemeral)

    @staticmethod
    async def show_stage_summary(
        context: Union[discord.Interaction, commands.Context],
        stage_number: int,
        stage_data: List[Dict[str, Any]],
        is_slash: bool = False,
    ) -> None:
        """
        Display stage summary with condensed weather for multiple days.

        Args:
            context: Discord context or interaction to respond to
            stage_number: The stage number to display
            stage_data: List of weather data dicts for each day in the stage
            is_slash: Whether this is a slash command response
        """
        embed = DisplayService._create_stage_embed(stage_number, stage_data)
        await DisplayService._send_embed(context, embed, is_slash)

    @staticmethod
    async def show_journey_overview(
        context: Union[discord.Interaction, commands.Context],
        all_stages: Union[List[List[Dict[str, Any]]], Dict[int, List[Dict[str, Any]]]],
        is_slash: bool = False,
    ) -> None:
        """
        Display journey overview with all stages.

        Args:
            context: Discord context or interaction to respond to
            all_stages: List of stages or dict mapping stage numbers to day lists
            is_slash: Whether this is a slash command response
        """
        embed = DisplayService._create_journey_overview_embed(all_stages)
        await DisplayService._send_embed(context, embed, is_slash)

    @staticmethod
    async def send_error(
        context: Union[discord.Interaction, commands.Context],
        message: str,
        is_slash: bool = False,
    ) -> None:
        """
        Send an error message in a red embed.

        Args:
            context: Discord context or interaction to respond to
            message: Error message text
            is_slash: Whether this is a slash command response
        """
        embed = discord.Embed(
            title=f"{EMOJI_ERROR} Error",
            description=message,
            color=COLOR_ERROR,
        )
        await DisplayService._send_embed(context, embed, is_slash)

    @staticmethod
    async def send_info(
        context: Union[discord.Interaction, commands.Context],
        message: str,
        title: str = None,
        is_slash: bool = False,
        ephemeral: bool = False,
    ) -> None:
        """
        Send an informational message in a gray embed.

        Args:
            context: Discord context or interaction to respond to
            message: Info message text
            title: Custom title (default: "ℹ️ Information")
            is_slash: Whether this is a slash command response
            ephemeral: Whether message should be ephemeral (slash only)
        """
        if title is None:
            title = f"{EMOJI_INFO} Information"

        embed = discord.Embed(
            title=title,
            description=message,
            color=COLOR_INFO,
        )
        await DisplayService._send_embed(context, embed, is_slash, ephemeral)

    # ==================== PRIVATE EMBED CREATION METHODS ====================

    @staticmethod
    def _create_daily_weather_embed(
        weather_data: Dict[str, Any],
        is_historical: bool = False,
    ) -> discord.Embed:
        """
        Create a Discord embed for daily weather display.

        Args:
            weather_data: Weather information dictionary
            is_historical: If True, shows "Historical Weather" title

        Returns:
            discord.Embed configured with weather information
        """
        # Extract data with defaults
        day = weather_data.get("day", DEFAULT_DAY)
        province = weather_data.get("province", DEFAULT_PROVINCE)
        season = weather_data.get("season", DEFAULT_SEASON)
        weather_type = weather_data.get("weather_type", DEFAULT_WEATHER)
        weather_effects = weather_data.get("weather_effects", [])
        wind_timeline = weather_data.get("wind_timeline", [])

        # Format display names
        province_name = WeatherFormatters.format_province_name(province)
        season_name = WeatherFormatters.format_season_name(season)

        # Get actual temperature for emoji selection
        actual_temp = weather_data.get("actual_temp", weather_data.get("temperature", DEFAULT_TEMPERATURE))

        # Get emojis
        weather_emoji = WeatherFormatters.get_weather_emoji(weather_type)
        temp_emoji = WeatherFormatters.get_temperature_emoji(actual_temp)

        # Create title
        title_prefix = f"{EMOJI_HISTORICAL} Historical Weather" if is_historical else f"{EMOJI_DAILY} Daily Weather"
        title = f"{title_prefix} - Day {day}"

        # Create embed
        embed = discord.Embed(
            title=title,
            description=f"**{province_name}** | **{season_name}**",
            color=COLOR_DEFAULT,
            timestamp=datetime.now(timezone.utc),
        )

        # Add weather condition field
        weather_text = DisplayService._format_weather_condition(weather_type, weather_effects)
        embed.add_field(
            name=f"{weather_emoji} Weather Condition",
            value=weather_text,
            inline=False,
        )

        # Add temperature field
        temp_text = DisplayService._format_temperature(
            actual_temp,
            weather_data.get("perceived_temp", actual_temp),
            weather_data.get("temp_category", ""),
        )
        embed.add_field(
            name=f"{temp_emoji} Temperature",
            value=temp_text,
            inline=True,
        )

        # Add wind conditions field
        wind_text = DisplayService._format_wind_timeline(wind_timeline)
        embed.add_field(
            name=f"{EMOJI_WIND} Wind Conditions",
            value=wind_text,
            inline=True,
        )

        # Add weather effects field if any
        if weather_effects:
            effects_text = DisplayService._format_weather_effects(weather_effects)
            embed.add_field(
                name=f"{EMOJI_EFFECTS} Weather Effects",
                value=effects_text,
                inline=False,
            )

        # Add special event fields
        if weather_data.get("cold_front_days"):
            days_remaining = weather_data["cold_front_days"]
            embed.add_field(
                name="❄️ Cold Front",
                value=f"Active for {days_remaining} more day{'s' if days_remaining != 1 else ''}",
                inline=False,
            )

        if weather_data.get("heat_wave_days"):
            days_remaining = weather_data["heat_wave_days"]
            embed.add_field(
                name="🌞 Heat Wave",
                value=f"Active for {days_remaining} more day{'s' if days_remaining != 1 else ''}",
                inline=False,
            )

        # Add footer
        embed.set_footer(text=FOOTER_TEXT)

        return embed

    @staticmethod
    def _create_stage_embed(
        stage_number: int,
        stage_data: List[Dict[str, Any]],
    ) -> discord.Embed:
        """
        Create a Discord embed for stage summary display.

        Args:
            stage_number: The stage number
            stage_data: List of weather data dicts for each day in the stage

        Returns:
            discord.Embed configured with stage summary
        """
        duration = len(stage_data)

        # Create title
        title = f"{EMOJI_STAGE} Stage {stage_number}"
        description = f"Duration: {duration} day{'s' if duration != 1 else ''}"

        # Create embed with purple color for stages
        embed = discord.Embed(
            title=title,
            description=description,
            color=COLOR_PURPLE,
            timestamp=datetime.now(timezone.utc),
        )

        # Add condensed day summaries
        if stage_data:
            for day_data in stage_data:
                day_num = day_data.get("day", "?")
                condensed = DisplayService._format_condensed_day_summary(day_data)
                embed.add_field(
                    name=f"Day {day_num}",
                    value=condensed,
                    inline=False,
                )
        else:
            embed.description = "No weather data available for this stage"

        embed.set_footer(text=FOOTER_TEXT)
        return embed

    @staticmethod
    def _create_journey_overview_embed(
        all_stages: Union[List[List[Dict[str, Any]]], Dict[int, List[Dict[str, Any]]]],
    ) -> discord.Embed:
        """
        Create a Discord embed for journey overview display.

        Args:
            all_stages: Either a list of stages or dict mapping stage numbers to day lists

        Returns:
            discord.Embed configured with journey overview
        """
        # Handle both dict and list formats
        if isinstance(all_stages, dict):
            stage_items = all_stages.items()
            total_stages = len(all_stages)
            total_days = sum(len(days) for days in all_stages.values())
        else:
            stage_items = enumerate(all_stages, 1)
            total_stages = len(all_stages)
            total_days = sum(len(stage) for stage in all_stages)

        # Create title
        title = f"{EMOJI_JOURNEY} Journey Overview"
        description = f"Stages: {total_stages} | Total Duration: {total_days} days"

        # Create embed
        embed = discord.Embed(
            title=title,
            description=description,
            color=COLOR_PURPLE,
            timestamp=datetime.now(timezone.utc),
        )

        # Add stage summaries
        if all_stages:
            for stage_num, stage_days in stage_items:
                stage_duration = len(stage_days)
                embed.add_field(
                    name=f"Stage {stage_num}",
                    value=f"{stage_duration} day{'s' if stage_duration != 1 else ''}",
                    inline=True,
                )
        else:
            embed.description = "Journey has no configured stages"

        embed.set_footer(text=FOOTER_TEXT)
        return embed

    # ==================== PRIVATE FORMATTING METHODS ====================

    @staticmethod
    def _format_wind_timeline(wind_timeline: List[Dict[str, Any]]) -> str:
        """
        Format wind conditions timeline for display.

        Args:
            wind_timeline: List of wind data dicts with keys:
                - time: Time period name (Dawn, Midday, Dusk, Midnight)
                - strength: Wind strength (calm, light, bracing, strong, very_strong)
                - direction: Wind direction (tailwind, sidewind, headwind)
                - changed: Whether wind changed from previous period

        Returns:
            Formatted string showing wind timeline
        """
        if not wind_timeline:
            return f"{EMOJI_CALM_WIND} Calm throughout the day"

        # Check if all periods have same wind
        if len(wind_timeline) > 0:
            first_strength = wind_timeline[0].get("strength", "")
            first_direction = wind_timeline[0].get("direction", "")

            all_same = all(
                w.get("strength") == first_strength and w.get("direction") == first_direction for w in wind_timeline
            )

            if all_same and first_strength.lower() == "calm":
                return f"{EMOJI_CALM_WIND} Calm throughout the day"

        # Format each time period
        lines = []
        for wind_data in wind_timeline:
            time_display = wind_data.get("time", "").title()
            strength = wind_data.get("strength", "calm")
            direction = wind_data.get("direction", "")
            changed = wind_data.get("changed", False)

            # Format strength and direction for display
            strength_display = strength.replace("_", " ").title()
            direction_display = direction.replace("_", " ").title()

            # Create line
            if strength.lower() == "calm":
                line = f"**{time_display}:** Calm"
            else:
                line = f"**{time_display}:** {strength_display} {direction_display}"

            # Add change indicator
            if changed:
                line += " ⚡"

            lines.append(line)

        return "\n".join(lines)

    @staticmethod
    def _format_weather_condition(
        weather_type: str,
        weather_effects: List[str],
    ) -> str:
        """
        Format weather condition description.

        Args:
            weather_type: Weather type key (e.g., 'fair', 'rain', 'snow')
            weather_effects: List of effect strings

        Returns:
            Formatted weather condition text
        """
        # Capitalize weather type for display
        weather_display = weather_type.replace("_", " ").title()

        # Get description from WEATHER_EFFECTS if available
        base_description = ""
        if weather_type in WEATHER_EFFECTS:
            effect_data = WEATHER_EFFECTS[weather_type]
            if isinstance(effect_data, dict) and "description" in effect_data:
                base_description = effect_data["description"]
            elif isinstance(effect_data, str):
                base_description = effect_data

        if base_description:
            return f"**{weather_display}**\n{base_description}"
        else:
            return f"**{weather_display}**"

    @staticmethod
    def _format_temperature(
        actual_temp: int,
        perceived_temp: int,
        temp_category: str = "",
    ) -> str:
        """
        Format temperature information including wind chill.

        Args:
            actual_temp: Actual temperature in Celsius
            perceived_temp: Perceived temperature with wind chill
            temp_category: Temperature category (e.g., "mild", "cold")

        Returns:
            Formatted temperature text
        """
        # Base temperature with category
        if temp_category:
            category_display = temp_category.replace("_", " ").title()
            temp_text = f"**{actual_temp}°C** ({category_display})"
        else:
            temp_text = f"**{actual_temp}°C**"

        # Add wind chill if different
        if perceived_temp != actual_temp:
            temp_diff = abs(perceived_temp - actual_temp)
            colder_or_warmer = "colder" if perceived_temp < actual_temp else "warmer"
            temp_text += f"\n**Feels like: {perceived_temp}°C** ({temp_diff}°C {colder_or_warmer})"

        return temp_text

    @staticmethod
    def _format_weather_effects(effects: List[str]) -> str:
        """
        Format weather effects as bulleted list.

        Args:
            effects: List of effect strings

        Returns:
            Formatted effects text with bullet points
        """
        if not effects:
            return "*No special effects*"

        # Add bullet points
        formatted_effects = [f"• {effect}" for effect in effects]
        return "\n".join(formatted_effects)

    @staticmethod
    def _format_condensed_day_summary(day_data: Dict[str, Any]) -> str:
        """
        Format condensed one-line day summary for stage displays.

        Args:
            day_data: Weather data for a single day

        Returns:
            Condensed summary string
        """
        weather_type = day_data.get("weather_type", DEFAULT_WEATHER)
        actual_temp = day_data.get("actual_temp", DEFAULT_TEMPERATURE)
        day_num = day_data.get("day", "?")

        # Get primary wind (midday or first available)
        wind_timeline = day_data.get("wind_timeline", [])
        wind_strength = "calm"
        wind_direction = ""

        if wind_timeline:
            # Try to find midday wind
            midday_wind = next(
                (w for w in wind_timeline if w.get("time", "").lower() == "midday"),
                wind_timeline[0],  # Fallback to first
            )
            wind_strength = midday_wind.get("strength", "calm")
            wind_direction = midday_wind.get("direction", "")

        # Format components
        weather_display = weather_type.replace("_", " ").title()
        wind_display = wind_strength.replace("_", " ").title()
        direction_display = wind_direction.replace("_", " ").title()

        # Build summary with day number
        if wind_strength.lower() == "calm":
            summary = f"**Day {day_num}**\n{weather_display} | {actual_temp}°C | Calm winds"
        else:
            summary = f"**Day {day_num}**\n{weather_display} | {actual_temp}°C | {wind_display} {direction_display}"

        return summary

    @staticmethod
    def _create_error_embed(message: str) -> discord.Embed:
        """
        Create an error embed with red color.

        Args:
            message: Error message text

        Returns:
            discord.Embed configured as error message
        """
        return discord.Embed(
            title=f"{EMOJI_ERROR} Error",
            description=message,
            color=COLOR_ERROR,
        )

    @staticmethod
    def _create_info_embed(message: str, title: str = None) -> discord.Embed:
        """
        Create an info embed with gray color.

        Args:
            message: Info message text
            title: Custom title (default: "ℹ️ Information")

        Returns:
            discord.Embed configured as info message
        """
        if title is None:
            title = f"{EMOJI_INFO} Information"

        return discord.Embed(
            title=title,
            description=message,
            color=COLOR_INFO,
        )

    # ==================== PRIVATE UTILITY METHODS ====================

    @staticmethod
    async def _send_embed(
        context: Union[discord.Interaction, commands.Context],
        embed: discord.Embed,
        is_slash: bool = False,
        ephemeral: bool = False,
    ) -> None:
        """
        Send an embed to Discord, handling both slash and prefix commands.

        Args:
            context: Discord context or interaction to respond to
            embed: Discord embed to send
            is_slash: Whether this is a slash command response
            ephemeral: Whether message should be ephemeral (slash only)
        """
        # Auto-detect context type
        if hasattr(context, "response"):
            # This is an Interaction (slash command)
            # Check if response is done (handle both sync property and async mock)
            try:
                is_done = context.response.is_done()
                # Handle AsyncMock by checking if it's awaitable
                if hasattr(is_done, "__await__"):
                    is_done = False  # Default to not done for mocks
            except:
                is_done = False

            if is_done:
                await context.followup.send(embed=embed, ephemeral=ephemeral)
            else:
                await context.response.send_message(embed=embed, ephemeral=ephemeral)
        else:
            # This is a Context (prefix command)
            await context.send(embed=embed)
