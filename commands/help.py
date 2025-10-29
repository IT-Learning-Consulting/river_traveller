"""
Command: help
Description: Display information about all available bot commands
"""

from typing import Optional
import discord
from discord import app_commands
from discord.ext import commands


def setup(bot: commands.Bot):
    """
    Register help command with the bot.
    Called from main.py during bot initialization.
    """

    # Slash command
    @bot.tree.command(name="help", description="Show all available bot commands")
    @app_commands.describe(
        command="Optional: Get detailed help for a specific command (roll, boat-handling, weather, river-encounter)"
    )
    @app_commands.choices(
        command=[
            app_commands.Choice(name="roll", value="roll"),
            app_commands.Choice(name="boat-handling", value="boat-handling"),
            app_commands.Choice(name="weather", value="weather"),
            app_commands.Choice(name="river-encounter", value="river-encounter"),
        ]
    )
    async def help_slash(
        interaction: discord.Interaction, command: Optional[str] = None
    ):
        """Display help information about all bot commands."""
        if command:
            embed = _create_detailed_help_embed(command)
        else:
            embed = _create_general_help_embed()
        await interaction.response.send_message(embed=embed)

    # Prefix command
    @bot.command(name="help")
    async def help_prefix(ctx, command: Optional[str] = None):
        """Display help information about all bot commands."""
        if command:
            # Normalize command name (remove leading slash or exclamation if present)
            command = command.lstrip("/!").lower()
            embed = _create_detailed_help_embed(command)
        else:
            embed = _create_general_help_embed()
        await ctx.send(embed=embed)


def _create_general_help_embed() -> discord.Embed:
    """
    Create the general help information embed showing all commands.

    Returns:
        Discord embed with all command information
    """
    embed = discord.Embed(
        title="🚢 River Travel Bot - Command Guide",
        description="A WFRP (Warhammer Fantasy Roleplay) bot for managing river travel adventures.\n\n"
        "💡 **Tip:** Use `/help <command>` for detailed information about a specific command.",
        color=discord.Color.blue(),
    )

    # Roll command
    embed.add_field(
        name="🎲 /roll",
        value=(
            "Roll dice with WFRP mechanics support.\n"
            "Use `/help roll` for detailed examples."
        ),
        inline=False,
    )

    # Boat handling command
    embed.add_field(
        name="⛵ /boat-handling",
        value=(
            "Make WFRP Boat Handling Tests for navigation.\n"
            "Use `/help boat-handling` for character details and examples."
        ),
        inline=False,
    )

    # Weather command
    embed.add_field(
        name="🌦️ /weather & /weather-stage-config",
        value=(
            "Generate and manage weather for river journeys.\n"
            "• `/weather next` - Daily progression\n"
            "• `/weather next-stage` - Multi-day travel (stage-based)\n"
            "• `/weather-stage-config` - 🔒 GM: Configure stages\n"
            "Use `/help weather` for full details, stage modes, and province list."
        ),
        inline=False,
    )

    # River encounter command
    embed.add_field(
        name="🌊 /river-encounter",
        value=(
            "Generate random river travel encounters.\n"
            "Use `/help river-encounter` for encounter types and mechanics."
        ),
        inline=False,
    )

    # GM Features
    embed.add_field(
        name="🎭 GM Features",
        value=(
            "Commands marked with 🔒 have restricted parameters.\n"
            "**Who can use:** Server owner or users with the **GM** role\n\n"
            "• **Weather Override** - Manually set all weather parameters\n"
            "• **Stage Config** - Control multi-day progression and display\n"
            "• **Encounter Override** - Force specific encounter types"
        ),
        inline=False,
    )

    # Footer with usage info
    embed.add_field(
        name="💡 Quick Tips",
        value=(
            "• Commands work as both `/command` (slash) and `!command` (prefix)\n"
            "• Weather and encounters affect boat handling modifiers\n"
            "• Use `/weather next` or `/weather next-stage` to progress time\n"
            "• Use `/help weather` to learn about stage-based travel"
        ),
        inline=False,
    )

    embed.set_footer(
        text="🗺️ Safe travels on the rivers of the Empire! | WFRP 4th Edition"
    )

    return embed


def _create_detailed_help_embed(command: str) -> discord.Embed:
    """
    Create detailed help information for a specific command.

    Args:
        command: Name of the command to show details for

    Returns:
        Discord embed with detailed command information
    """
    command = command.lower()

    if command == "roll":
        return _create_roll_help()
    elif command == "boat-handling":
        return _create_boat_handling_help()
    elif command == "weather":
        return _create_weather_help()
    elif command == "river-encounter":
        return _create_river_encounter_help()
    else:
        # Unknown command, return general help
        return _create_general_help_embed()


def _create_roll_help() -> discord.Embed:
    """Create detailed help for the roll command."""
    embed = discord.Embed(
        title="🎲 /roll - Dice Rolling Command",
        description="Roll dice with flexible notation and WFRP mechanics support.",
        color=discord.Color.blue(),
    )

    embed.add_field(
        name="📋 Basic Usage",
        value=(
            "**Syntax:** `/roll <dice> [target] [modifier]`\n\n"
            "**Parameters:**\n"
            "• `dice` - Dice notation (e.g., 1d100, 3d10, 2d6+5)\n"
            "• `target` - Optional: WFRP skill value (1-100)\n"
            "• `modifier` - Optional: Difficulty modifier (default: +20 Average)"
        ),
        inline=False,
    )

    embed.add_field(
        name="📖 Examples",
        value=(
            "`/roll 1d100` - Simple d100 roll\n"
            "`/roll 3d10` - Roll 3d10 dice\n"
            "`/roll 2d6+5` - Roll 2d6 and add 5\n"
            "`/roll 1d20-3` - Roll 1d20 and subtract 3\n\n"
            "**WFRP Skill Tests:**\n"
            "`/roll 1d100 45` - Roll against skill 45 (Average +20, target 65)\n"
            "`/roll 1d100 45 0` - Roll against skill 45 (Challenging, target 45)\n"
            "`/roll 1d100 45 -20` - Roll against skill 45 (Hard, target 25)\n"
            "`/roll 1d100 45 40` - Roll against skill 45 (Easy, target 85)"
        ),
        inline=False,
    )

    embed.add_field(
        name="🎯 WFRP Difficulty Modifiers",
        value=(
            "`+60` Very Easy | `+40` Easy | `+20` Average (default)\n"
            "`+0` Challenging | `-10` Difficult | `-20` Hard\n"
            "`-30` Very Difficult | `-40` Futile | `-50` Impossible"
        ),
        inline=False,
    )

    embed.add_field(
        name="⚡ Special Rules",
        value=(
            "• **Doubles (11, 22, 33, etc.)** are automatically detected\n"
            "• Doubles ≤ target = **Critical Success** ✨\n"
            "• Doubles > target = **Fumble** 💥\n"
            "• **100 is always a Fumble**, regardless of target\n"
            "• Success levels are calculated (Marginal, Success, Impressive, Astounding)"
        ),
        inline=False,
    )

    embed.set_footer(text="💡 Tip: You can also use !roll for prefix commands")

    return embed


def _create_boat_handling_help() -> discord.Embed:
    """Create detailed help for the boat-handling command."""
    embed = discord.Embed(
        title="⛵ /boat-handling - Navigation Test Command",
        description="Make WFRP Boat Handling Tests (Row or Sail) for river navigation.",
        color=discord.Color.green(),
    )

    embed.add_field(
        name="📋 Basic Usage",
        value=(
            "**Syntax:** `/boat-handling <character> [difficulty] [time_of_day]`\n\n"
            "**Parameters:**\n"
            "• `character` - Character name (required)\n"
            "• `difficulty` - Modifier to test (default: +0 Challenging)\n"
            "• `time_of_day` - Time for wind conditions (default: midday)"
        ),
        inline=False,
    )

    embed.add_field(
        name="👥 Available Characters",
        value=(
            "**Anara of Sānxiá** - Skilled navigator\n"
            "**Emmerich Falkenrath** - Experienced sailor\n"
            "**Hildric Sokhlundt** - Strong rower\n"
            "**Oktavian Babel** - Versatile traveler\n"
            "**Lupus Leonard Joachim Rohrig** - Resourceful adventurer"
        ),
        inline=False,
    )

    embed.add_field(
        name="🕐 Time of Day Options",
        value=(
            "**Dawn** - Morning winds\n"
            "**Midday** - Afternoon conditions (default)\n"
            "**Dusk** - Evening winds\n"
            "**Midnight** - Night conditions\n\n"
            "Different times have different wind patterns!"
        ),
        inline=False,
    )

    embed.add_field(
        name="📖 Examples",
        value=(
            "`/boat-handling anara` - Test with Anara, default settings\n"
            "`/boat-handling emmerich -10` - Test with Emmerich, Difficult\n"
            "`/boat-handling hildric 0 dawn` - Test with Hildric at dawn\n"
            "`/boat-handling oktavian -20 midnight` - Hard test at midnight"
        ),
        inline=False,
    )

    embed.add_field(
        name="⚙️ How It Works",
        value=(
            "• Bot automatically chooses **Sail** or **Row** based on weather\n"
            "• **Calm wind** = use Row skill\n"
            "• **Any wind** = use Sail skill\n"
            "• Weather modifiers from `/weather` are automatically applied\n"
            "• Lore (Riverways) skill provides bonus if available\n"
            "• Results include success level and WFRP doubles detection"
        ),
        inline=False,
    )

    embed.set_footer(
        text="💡 Tip: Use /weather to set journey conditions for accurate modifiers"
    )

    return embed


def _create_weather_help() -> discord.Embed:
    """Create detailed help for the weather command."""
    embed = discord.Embed(
        title="🌦️ /weather - Journey Weather Management",
        description="Generate and track weather conditions for multi-day river journeys with stage-based progression.",
        color=discord.Color.gold(),
    )

    embed.add_field(
        name="📋 Daily Progression",
        value=(
            "**`/weather next`** - Generate weather for the next day\n"
            "**`/weather view <day>`** - View weather for specific day\n"
            "**`/weather journey <season> <province>`** - Start new journey\n"
            "**`/weather override <season> <province>`** - 🔒 GM only - Manual weather"
        ),
        inline=False,
    )

    embed.add_field(
        name="🗺️ Stage-Based Travel",
        value=(
            "**`/weather next-stage`** - Advance multiple days at once\n"
            "**`/weather-stage-config`** - 🔒 GM only - Configure stage settings\n\n"
            "**Stages** let you generate weather for multiple days of travel simultaneously!\n"
            "• Default: 3 days per stage (configurable 1-10 days)\n"
            "• Two display modes: Simple summary or detailed breakdown\n"
            "• Perfect for fast-forwarding travel or planning ahead"
        ),
        inline=False,
    )

    embed.add_field(
        name="🌍 Seasons",
        value="**Spring** | **Summer** | **Autumn** | **Winter**\n\nEach season has different weather patterns and temperatures.",
        inline=False,
    )

    embed.add_field(
        name="🗺️ Provinces",
        value=(
            "**Reikland** | **Averland** | **Wissenland** | **Stirland**\n"
            "**Talabecland** | **Ostland** | **Hochland** | **Middenland** | **Nordland**\n\n"
            "Each province has different base temperatures and regional characteristics."
        ),
        inline=False,
    )

    embed.add_field(
        name="📖 Examples - Daily",
        value=(
            "`/weather journey summer reikland` - Start summer journey in Reikland\n"
            "`/weather next` - Generate next day's weather\n"
            "`/weather view 3` - View weather for day 3\n"
            "`/weather override autumn talabecland` - 🔒 GM: Manually set weather"
        ),
        inline=False,
    )

    embed.add_field(
        name="📖 Examples - Stage Progression",
        value=(
            "`/weather next-stage` - Generate weather for next stage (3 days default)\n"
            "`/weather-stage-config` - 🔒 GM: View current stage settings\n"
            "`/weather-stage-config stage_duration:5` - 🔒 GM: Set 5 days per stage\n"
            "`/weather-stage-config display_mode:detailed` - 🔒 GM: Show full info\n"
            "`/weather-stage-config stage_duration:3 display_mode:simple` - 🔒 GM: Both"
        ),
        inline=False,
    )

    embed.add_field(
        name="⚙️ Weather Tracking",
        value=(
            "The bot tracks:\n"
            "• **Wind strength & direction** (changes throughout day)\n"
            "• **Temperature** with wind chill effects\n"
            "• **Weather conditions** (Fair, Overcast, Rain, etc.)\n"
            "• **Special events** (Cold fronts, heat waves)\n"
            "• **Boat handling modifiers** based on conditions\n\n"
            "Wind is tracked at 4 times: Dawn, Midday, Dusk, Midnight"
        ),
        inline=False,
    )

    embed.add_field(
        name="🎨 Stage Display Modes",
        value=(
            "**Simple (Default):** Brief summary per day\n"
            "• Weather type with emoji (🌤️ ☁️ 🌧️)\n"
            "• Temperature and special events\n"
            "• Quick overview for fast travel\n\n"
            "**Detailed:** Complete breakdown per day\n"
            "• Full wind timeline (dawn, noon, dusk, midnight)\n"
            "• Weather effects and modifiers\n"
            "• Temperature categories and special event details\n"
            "• Perfect for planning or important travel days\n\n"
            "💡 Switch anytime: `/weather-stage-config display_mode:<simple|detailed>`"
        ),
        inline=False,
    )

    embed.add_field(
        name="🔒 GM Features",
        value=(
            "**Who can use:** Server owner or users with **GM** role\n\n"
            "**Override Weather:** Manually set all weather parameters\n"
            "• Choose wind strength and direction for each time\n"
            "• Set temperature and weather conditions\n"
            "• Perfect for crafting specific scenarios\n\n"
            "**Stage Configuration:** Control multi-day progression\n"
            "• Set stage duration (1-10 days per stage)\n"
            "• Choose display mode (simple summary or detailed)\n"
            "• Configure once, affects all future `/weather next-stage` commands\n"
            "• Mix with daily progression (`/weather next`) as needed"
        ),
        inline=False,
    )

    embed.set_footer(
        text="💡 Tip: Weather affects boat-handling tests and encounter probabilities"
    )

    return embed


def _create_river_encounter_help() -> discord.Embed:
    """Create detailed help for the river-encounter command."""
    embed = discord.Embed(
        title="🌊 /river-encounter - River Events",
        description="Generate random encounters and events during river travel with dual-message system.",
        color=discord.Color.teal(),
    )

    embed.add_field(
        name="📋 Basic Usage",
        value=(
            "**Syntax:** `/river-encounter [type]`\n\n"
            "**Parameters:**\n"
            "• `type` - 🔒 Optional GM override: Force specific encounter type"
        ),
        inline=False,
    )

    embed.add_field(
        name="🎲 Encounter Types & Probabilities",
        value=(
            "**✨ Positive (1-10)** - 10% chance\n"
            "Beneficial events: Tailwinds, helpful NPCs, shortcuts\n\n"
            "**👀 Coincidental (11-40)** - 30% chance\n"
            "Neutral observations: Wildlife, landmarks, passing boats\n\n"
            "**😴 Uneventful (41-75)** - 35% chance\n"
            "Nothing of note happens during travel\n\n"
            "**⚠️ Harmful (76-90)** - 15% chance\n"
            "Minor problems: Debris, delays, difficult passages\n\n"
            "**💥 Accident (91-100)** - 10% chance\n"
            "Major incidents: Damage, cargo loss, critical situations"
        ),
        inline=False,
    )

    embed.add_field(
        name="📖 Examples",
        value=(
            "`/river-encounter` - Generate random encounter\n"
            "`/river-encounter positive` - 🔒 GM: Force positive encounter\n"
            "`/river-encounter accident` - 🔒 GM: Force accident encounter"
        ),
        inline=False,
    )

    embed.add_field(
        name="💬 Dual-Message System",
        value=(
            "**For Players (Public):**\n"
            "• Receive cryptic, atmospheric flavor text\n"
            "• Grimdark descriptions maintain immersion\n"
            "• No mechanical details revealed\n\n"
            "**For GMs (#boat-travelling-notifications):**\n"
            "• Full encounter details and mechanics\n"
            "• Required skill tests and difficulties\n"
            "• Damage rolls, effects, and outcomes\n"
            "• Perfect for managing the encounter"
        ),
        inline=False,
    )

    embed.add_field(
        name="⚙️ Encounter Details",
        value=(
            "Each encounter may include:\n"
            "• **Skill tests** (Navigate, Row, Swim, Perception, etc.)\n"
            "• **Difficulty modifiers** for WFRP tests\n"
            "• **Damage** to boat or characters\n"
            "• **Cargo loss** with special formula (for accidents)\n"
            "• **Travel speed modifiers** (positive/negative)\n"
            "• **Story hooks** for roleplay opportunities"
        ),
        inline=False,
    )

    embed.add_field(
        name="🎭 GM Override Feature",
        value=(
            "**Who can use:** Server owner or users with **GM** role\n\n"
            "Override types:\n"
            "• `positive` - Force beneficial encounter\n"
            "• `coincidental` - Force neutral encounter\n"
            "• `uneventful` - Force uneventful day\n"
            "• `harmful` - Force minor problem\n"
            "• `accident` - Force major incident\n\n"
            "Perfect for story pacing and dramatic moments!"
        ),
        inline=False,
    )

    embed.set_footer(
        text="� Tip: Encounters add flavor and challenge to river journeys"
    )

    return embed
