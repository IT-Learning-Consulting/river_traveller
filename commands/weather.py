"""
Command: weather
Description: Generate daily weather conditions for WFRP river travel with multi-day journey tracking
"""

import discord
from discord import app_commands
from discord.ext import commands

from utils.weather_mechanics import (
    generate_daily_wind,
    generate_daily_wind_with_previous,
    roll_weather_condition,
    get_weather_effects,
    roll_temperature_with_special_events,
    apply_wind_chill,
    get_temperature_description_text,
    get_wind_chill_note,
    get_wind_modifiers,
)
from db.weather_data import (
    WIND_STRENGTH,
    WIND_DIRECTION,
    get_province_base_temperature,
)
from db.weather_storage import WeatherStorage


def is_gm(user: discord.Member) -> bool:
    """
    Check if user is a GM (server owner or has GM role).

    Args:
        user: Discord member to check

    Returns:
        True if user is GM, False otherwise
    """
    # Server owner is always GM
    if user.guild.owner_id == user.id:
        return True

    # Check for GM role
    gm_role = discord.utils.get(user.guild.roles, name="GM")
    if gm_role and gm_role in user.roles:
        return True

    return False


def setup(bot: commands.Bot):
    """
    Register weather command with the bot.
    Called from main.py during bot initialization.
    """

    # Slash command
    @bot.tree.command(
        name="weather", description="Manage daily weather for river travel journeys"
    )
    @app_commands.describe(
        action="What to do",
        season="Season (for 'journey' and 'override' actions)",
        province="Province (for 'journey' and 'override' actions)",
        day="Day number to view (for 'view' action)",
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name="Generate Next Day", value="next"),
            app_commands.Choice(name="Start New Journey", value="journey"),
            app_commands.Choice(name="View Day", value="view"),
            app_commands.Choice(name="End Journey", value="end"),
            app_commands.Choice(name="Override Weather", value="override"),
        ],
        season=[
            app_commands.Choice(name="Spring", value="spring"),
            app_commands.Choice(name="Summer", value="summer"),
            app_commands.Choice(name="Autumn", value="autumn"),
            app_commands.Choice(name="Winter", value="winter"),
        ],
        province=[
            app_commands.Choice(name="Reikland", value="reikland"),
            app_commands.Choice(name="Nordland", value="nordland"),
            app_commands.Choice(name="Ostland", value="ostland"),
            app_commands.Choice(name="Middenland", value="middenland"),
            app_commands.Choice(name="Hochland", value="hochland"),
            app_commands.Choice(name="Talabecland", value="talabecland"),
            app_commands.Choice(name="Ostermark", value="ostermark"),
            app_commands.Choice(name="Stirland", value="stirland"),
            app_commands.Choice(name="Sylvania", value="sylvania"),
            app_commands.Choice(name="Wissenland", value="wissenland"),
            app_commands.Choice(name="Averland", value="averland"),
            app_commands.Choice(name="Solland", value="solland"),
            app_commands.Choice(name="Kislev", value="kislev"),
            app_commands.Choice(name="Wasteland", value="wasteland"),
            app_commands.Choice(name="Border Princes", value="border_princes"),
        ],
    )
    async def weather_slash(
        interaction: discord.Interaction,
        action: str = "next",
        season: str = None,
        province: str = None,
        day: int = None,
    ):
        """Manage weather for multi-day journeys."""
        await _perform_weather_action(
            interaction, action, season, province, day, is_slash=True
        )

    # Prefix command
    @bot.command(name="weather")
    async def weather_prefix(
        ctx,
        action: str = "next",
        season: str = None,
        province: str = None,
        day: int = None,
    ):
        """Manage weather for multi-day journeys."""
        await _perform_weather_action(
            ctx, action, season, province, day, is_slash=False
        )

    async def _perform_weather_action(
        context, action: str, season: str, province: str, day: int, is_slash: bool
    ):
        """Route to appropriate weather action handler."""
        guild_id = str(context.guild.id) if context.guild else None

        if not guild_id:
            await _send_error(
                context, "This command must be used in a server.", is_slash
            )
            return

        if action == "next":
            await _generate_next_day(context, guild_id, is_slash)
        elif action == "journey":
            await _start_new_journey(context, guild_id, season, province, is_slash)
        elif action == "view":
            await _view_day_weather(context, guild_id, day, is_slash)
        elif action == "end":
            await _end_journey(context, guild_id, is_slash)
        elif action == "override":
            # Check GM permissions for override action
            user = context.user if is_slash else context.author
            if context.guild and not is_gm(user):
                error_msg = "❌ Only the server owner or users with the GM role can override weather."
                await _send_error(context, error_msg, is_slash)
                return
            await _override_weather(context, guild_id, season, province, is_slash)
        else:
            await _send_error(context, f"Unknown action: {action}", is_slash)

    async def _generate_next_day(context, guild_id: str, is_slash: bool):
        """Generate weather for the next day of the journey."""
        try:
            storage = WeatherStorage()
            journey = storage.get_journey_state(guild_id)

            # If no journey exists, auto-start one with defaults
            if not journey:
                await _send_info(
                    context,
                    "⚠️ No journey in progress. Starting new journey with default settings (Summer in Reikland).\nUse `/weather journey` to customize.",
                    is_slash,
                )
                storage.start_journey(guild_id, "summer", "reikland")
                journey = storage.get_journey_state(guild_id)

            current_day = journey["current_day"]
            season = journey["season"]
            province = journey["province"]

            # Check if we need to generate for current day or advance
            current_weather = storage.get_daily_weather(guild_id, current_day)

            if current_weather:
                # Advance to next day
                new_day = storage.advance_day(guild_id)

                # Get previous midnight wind for continuity
                previous_midnight = current_weather["wind_timeline"][
                    3
                ]  # Midnight is 4th entry
                wind_timeline = generate_daily_wind_with_previous(previous_midnight)

                continuity_note = f"🔄 Wind carried over from Day {current_day} midnight: {WIND_STRENGTH[previous_midnight['strength']]} {WIND_DIRECTION[previous_midnight['direction']]}"
            else:
                # Generate for current day (first day)
                new_day = current_day
                wind_timeline = generate_daily_wind()
                continuity_note = None

            # Generate weather with cold fronts/heat waves
            previous_weather = (
                storage.get_daily_weather(guild_id, new_day - 1)
                if new_day > 1
                else None
            )
            cold_front_days = (
                previous_weather["cold_front_days_remaining"] if previous_weather else 0
            )
            heat_wave_days = (
                previous_weather["heat_wave_days_remaining"] if previous_weather else 0
            )

            weather_type = roll_weather_condition(season)
            weather_effects = get_weather_effects(weather_type)

            (
                actual_temp,
                temp_category,
                temp_description,
                temp_roll,
                cold_front_remaining,
                heat_wave_remaining,
            ) = roll_temperature_with_special_events(
                season, province, cold_front_days, heat_wave_days
            )

            base_temp = get_province_base_temperature(province, season)

            # Apply wind chill
            wind_strengths = [w["strength"] for w in wind_timeline]
            most_common_wind = max(set(wind_strengths), key=wind_strengths.count)
            perceived_temp = apply_wind_chill(actual_temp, most_common_wind)

            # Save to database
            weather_data = {
                "season": season,
                "province": province,
                "wind_timeline": wind_timeline,
                "weather_type": weather_type,
                "weather_roll": 0,  # We don't expose the roll anymore
                "temperature_actual": actual_temp,
                "temperature_category": temp_category,
                "temperature_roll": temp_roll,
                "cold_front_days_remaining": cold_front_remaining,
                "heat_wave_days_remaining": heat_wave_remaining,
            }
            storage.save_daily_weather(guild_id, new_day, weather_data)

            # Display weather
            await _display_weather(
                context,
                new_day,
                season,
                province,
                wind_timeline,
                weather_type,
                weather_effects,
                actual_temp,
                perceived_temp,
                base_temp,
                temp_category,
                temp_description,
                most_common_wind,
                cold_front_remaining,
                heat_wave_remaining,
                continuity_note,
                is_slash,
            )

            # Send mechanics notification
            temp_feel_text = get_temperature_description_text(actual_temp, base_temp)
            await send_mechanics_notification(
                context,
                season,
                province,
                wind_timeline,
                weather_effects,
                temp_feel_text,
            )

        except Exception as e:  # pylint: disable=broad-exception-caught
            await _send_error(context, f"Error generating weather: {str(e)}", is_slash)

    async def _start_new_journey(
        context, guild_id: str, season: str, province: str, is_slash: bool
    ):
        """Start a new journey with specified season and province."""
        try:
            if not season or not province:
                await _send_error(
                    context,
                    "Please specify both season and province when starting a journey.\nExample: `/weather journey summer reikland`",
                    is_slash,
                )
                return

            season = season.lower()
            province = province.lower().replace(" ", "_")

            # Validate inputs
            if season not in ["spring", "summer", "autumn", "winter"]:
                await _send_error(
                    context,
                    "Invalid season. Must be: spring, summer, autumn, or winter",
                    is_slash,
                )
                return

            storage = WeatherStorage()
            storage.start_journey(guild_id, season, province)

            # Generate Day 1 weather
            await _generate_next_day(context, guild_id, is_slash)

            # Add journey started message
            embed = discord.Embed(
                title="🧭 New Journey Started!",
                description=f"Season: **{season.title()}** in **{province.replace('_', ' ').title()}**\n\nUse `/weather next` to advance to the next day.",
                color=discord.Color.green(),
            )

            if is_slash:
                await context.followup.send(embed=embed, ephemeral=True)
            else:
                await context.send(embed=embed)

        except Exception as e:  # pylint: disable=broad-exception-caught
            await _send_error(context, f"Error starting journey: {str(e)}", is_slash)

    async def _view_day_weather(context, guild_id: str, day: int, is_slash: bool):
        """View weather for a specific day."""
        try:
            storage = WeatherStorage()
            journey = storage.get_journey_state(guild_id)

            if not journey:
                await _send_error(
                    context,
                    "No journey in progress. Use `/weather journey` to start one.",
                    is_slash,
                )
                return

            # If no day specified, show current day
            if day is None:
                day = journey["current_day"]

            weather = storage.get_daily_weather(guild_id, day)

            if not weather:
                await _send_error(
                    context,
                    f"No weather data for Day {day}. Current journey is on Day {journey['current_day']}.",
                    is_slash,
                )
                return

            season = weather["season"]
            province = weather["province"]
            wind_timeline = weather["wind_timeline"]
            weather_type = weather["weather_type"]
            weather_effects = get_weather_effects(weather_type)
            actual_temp = weather["temperature_actual"]
            temp_category = weather["temperature_category"]

            # Recalculate derived values
            base_temp = get_province_base_temperature(province, season)
            wind_strengths = [w["strength"] for w in wind_timeline]
            most_common_wind = max(set(wind_strengths), key=wind_strengths.count)
            perceived_temp = apply_wind_chill(actual_temp, most_common_wind)

            # Get temperature description from data
            from db.weather_data import TEMPERATURE_DESCRIPTIONS

            temp_description = TEMPERATURE_DESCRIPTIONS.get(temp_category, "Average")

            cold_front_remaining = weather["cold_front_days_remaining"]
            heat_wave_remaining = weather["heat_wave_days_remaining"]

            # Display with historical marker
            await _display_weather(
                context,
                day,
                season,
                province,
                wind_timeline,
                weather_type,
                weather_effects,
                actual_temp,
                perceived_temp,
                base_temp,
                temp_category,
                temp_description,
                most_common_wind,
                cold_front_remaining,
                heat_wave_remaining,
                None,
                is_slash,
                is_historical=True,
            )

        except Exception as e:  # pylint: disable=broad-exception-caught
            await _send_error(context, f"Error viewing weather: {str(e)}", is_slash)

    async def _end_journey(context, guild_id: str, is_slash: bool):
        """End the current journey."""
        try:
            storage = WeatherStorage()
            days = storage.end_journey(guild_id)

            if days == 0:
                await _send_error(context, "No journey in progress.", is_slash)
                return

            embed = discord.Embed(
                title="🏁 Journey Ended",
                description=f"Your journey lasted **{days} days**.\n\nAll weather data has been cleared.\nUse `/weather journey` to start a new journey.",
                color=discord.Color.orange(),
            )

            if is_slash:
                await context.response.send_message(embed=embed)
            else:
                await context.send(embed=embed)

        except Exception as e:  # pylint: disable=broad-exception-caught
            await _send_error(context, f"Error ending journey: {str(e)}", is_slash)

    async def _override_weather(
        context, guild_id: str, season: str, province: str, is_slash: bool
    ):
        """Manually override weather for current day (GM tool)."""
        try:
            if not season or not province:
                await _send_error(
                    context,
                    "Please specify both season and province for override.\nExample: `/weather override winter kislev`",
                    is_slash,
                )
                return

            season = season.lower()
            province = province.lower().replace(" ", "_")

            storage = WeatherStorage()
            journey = storage.get_journey_state(guild_id)

            if not journey:
                await _send_error(
                    context,
                    "No journey in progress. Use `/weather journey` to start one first.",
                    is_slash,
                )
                return

            current_day = journey["current_day"]

            # Generate new weather with override
            wind_timeline = generate_daily_wind()
            weather_type = roll_weather_condition(season)
            weather_effects = get_weather_effects(weather_type)

            actual_temp, temp_category, temp_description, temp_roll, _, _ = (
                roll_temperature_with_special_events(season, province, 0, 0)
            )

            base_temp = get_province_base_temperature(province, season)
            wind_strengths = [w["strength"] for w in wind_timeline]
            most_common_wind = max(set(wind_strengths), key=wind_strengths.count)
            perceived_temp = apply_wind_chill(actual_temp, most_common_wind)

            # Save override
            weather_data = {
                "season": season,
                "province": province,
                "wind_timeline": wind_timeline,
                "weather_type": weather_type,
                "weather_roll": 0,
                "temperature_actual": actual_temp,
                "temperature_category": temp_category,
                "temperature_roll": temp_roll,
                "cold_front_days_remaining": 0,
                "heat_wave_days_remaining": 0,
            }
            storage.save_daily_weather(guild_id, current_day, weather_data)

            # Display
            await _display_weather(
                context,
                current_day,
                season,
                province,
                wind_timeline,
                weather_type,
                weather_effects,
                actual_temp,
                perceived_temp,
                base_temp,
                temp_category,
                temp_description,
                most_common_wind,
                0,
                0,
                "⚠️ Weather manually overridden by GM",
                is_slash,
            )

        except Exception as e:  # pylint: disable=broad-exception-caught
            await _send_error(context, f"Error overriding weather: {str(e)}", is_slash)

    async def _display_weather(
        context,
        day: int,
        season: str,
        province: str,
        wind_timeline: list,
        weather_type: str,
        weather_effects: dict,
        actual_temp: int,
        perceived_temp: int,
        base_temp: int,
        _temp_category: str,  # Unused but kept for parameter consistency
        temp_description: str,
        most_common_wind: str,
        cold_front_days: int,
        heat_wave_days: int,
        continuity_note: str,
        is_slash: bool,
        is_historical: bool = False,
    ):
        """Display weather embed."""
        title_prefix = "📜 " if is_historical else "📅 "
        title = f"{title_prefix}Day {day} - {season.title()} in {province.replace('_', ' ').title()}"

        embed = discord.Embed(
            title=title,
            color=(
                discord.Color.blue() if not is_historical else discord.Color.greyple()
            ),
        )

        # Add continuity note if present
        if continuity_note:
            embed.description = continuity_note

        # Wind conditions section
        wind_text = ""
        for wind_entry in wind_timeline:
            strength_name = WIND_STRENGTH[wind_entry["strength"]]
            direction_name = WIND_DIRECTION[wind_entry["direction"]]
            modifiers = get_wind_modifiers(
                wind_entry["strength"], wind_entry["direction"]
            )

            change_indicator = " 🔄" if wind_entry["changed"] else ""
            wind_text += f"**{wind_entry['time']}:** {strength_name} {direction_name}{change_indicator}\n"
            wind_text += f"  ↳ {modifiers['modifier']}\n"

        embed.add_field(
            name="🌬️ Wind Conditions",
            value=wind_text.strip(),
            inline=False,
        )

        # Weather condition section
        weather_emoji = get_weather_emoji(weather_type)
        weather_text = (
            f"**{weather_effects['name']}**\n{weather_effects['description']}"
        )

        embed.add_field(
            name=f"{weather_emoji} Weather Condition",
            value=weather_text,
            inline=False,
        )

        # Weather effects
        if weather_effects["effects"]:
            effects_text = "\n".join(
                f"• {effect}" for effect in weather_effects["effects"]
            )
            embed.add_field(
                name="⚠️ Effects",
                value=effects_text,
                inline=False,
            )

        # Temperature section
        temp_emoji = get_temperature_emoji(actual_temp)
        temp_feel_text = get_temperature_description_text(actual_temp, base_temp)
        wind_chill_note = get_wind_chill_note(most_common_wind)

        temp_text = f"**{actual_temp}°C** ({temp_feel_text})\n"
        temp_text += f"*{temp_description}*"

        if perceived_temp != actual_temp:
            temp_text += f"\n**Feels like:** {perceived_temp}°C{wind_chill_note}"

        # Add cold front/heat wave info
        if cold_front_days > 0:
            temp_text += f"\n\n❄️ **Cold Front:** {cold_front_days} days remaining"
        if heat_wave_days > 0:
            temp_text += f"\n\n🔥 **Heat Wave:** {heat_wave_days} days remaining"

        embed.add_field(
            name=f"{temp_emoji} Temperature",
            value=temp_text,
            inline=False,
        )

        # Footer
        if is_slash:
            embed.set_footer(text=f"Generated by {context.user.display_name}")
        else:
            embed.set_footer(text=f"Generated by {context.author.display_name}")

        # Send embed
        if is_slash:
            if hasattr(context, "response") and not context.response.is_done():
                await context.response.send_message(embed=embed)
            else:
                await context.followup.send(embed=embed)
        else:
            await context.send(embed=embed)

    async def _send_error(context, message: str, is_slash: bool):
        """Send error message."""
        embed = discord.Embed(
            title="❌ Error", description=message, color=discord.Color.red()
        )

        if is_slash:
            if hasattr(context, "response") and not context.response.is_done():
                await context.response.send_message(embed=embed, ephemeral=True)
            else:
                await context.followup.send(embed=embed, ephemeral=True)
        else:
            await context.send(embed=embed)

    async def _send_info(context, message: str, is_slash: bool):
        """Send info message."""
        embed = discord.Embed(
            title="ℹ️ Info", description=message, color=discord.Color.blue()
        )

        if is_slash:
            if hasattr(context, "response") and not context.response.is_done():
                await context.response.send_message(embed=embed, ephemeral=True)
            else:
                await context.followup.send(embed=embed, ephemeral=True)
        else:
            await context.send(embed=embed)


async def send_mechanics_notification(
    context,
    season: str,
    province: str,
    wind_timeline: list,
    weather_effects: dict,
    temp_description: str,
):
    """Send mechanics summary to notifications channel."""
    try:
        # Try to find the notifications channel
        guild = context.guild
        if not guild:
            return

        notifications_channel = discord.utils.get(
            guild.text_channels, name="boat-travelling-notifications"
        )

        if not notifications_channel:
            # Channel doesn't exist, skip notification
            return

        # Build mechanics embed
        embed = discord.Embed(
            title="⚠️ Active Weather Mechanics",
            description=f"Weather conditions for {season.title()} in {province.replace('_', ' ').title()}",
            color=discord.Color.gold(),
        )

        # Extract active wind modifiers
        wind_modifiers_text = ""
        for wind_entry in wind_timeline:
            modifiers = get_wind_modifiers(
                wind_entry["strength"], wind_entry["direction"]
            )
            strength_name = WIND_STRENGTH[wind_entry["strength"]]
            direction_name = WIND_DIRECTION[wind_entry["direction"]]

            wind_modifiers_text += (
                f"**{wind_entry['time']}:** {strength_name} {direction_name}\n"
            )
            wind_modifiers_text += f"  └─ {modifiers['modifier']}\n"

            if modifiers["notes"]:
                wind_modifiers_text += f"  └─ *{modifiers['notes']}*\n"

        embed.add_field(
            name="🚢 Boat Handling Modifiers",
            value=wind_modifiers_text.strip(),
            inline=False,
        )

        # Weather penalties
        if (
            weather_effects["effects"]
            and weather_effects["effects"][0] != "No weather-related hazards"
        ):
            effects_text = "\n".join(
                f"• {effect}" for effect in weather_effects["effects"]
            )
            embed.add_field(
                name="🎯 Active Penalties & Conditions",
                value=effects_text,
                inline=False,
            )

        # Temperature note
        embed.add_field(
            name="🌡️ Temperature",
            value=temp_description,
            inline=False,
        )

        # Additional notes
        notes = "• Wind may change at midday, dusk, or midnight (10% chance each check)"
        embed.add_field(name="💡 Notes", value=notes, inline=False)

        await notifications_channel.send(embed=embed)

    except (discord.DiscordException, AttributeError):
        # Silently fail if we can't send to notifications channel
        pass


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
