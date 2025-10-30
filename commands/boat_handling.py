"""
Command: boat-handling
Description: WFRP Boat Handling Test for river navigation
"""

import random
import discord
from discord import app_commands
from discord.ext import commands

# Import from our modules
from db.character_data import (
    get_character,
    get_available_characters,
)
from utils.wfrp_mechanics import check_wfrp_doubles, roll_dice
from utils.modifier_calculator import (
    get_active_weather_modifiers,
    format_weather_impact_for_embed,
)


def setup(bot: commands.Bot):
    """
    Register boat-handling command with the bot.
    Called from main.py during bot initialization.
    """

    # Slash command
    @bot.tree.command(
        name="boat-handling",
        description="Make a WFRP Boat Handling Test for a character",
    )
    @app_commands.describe(
        character="Character name (anara, emmerich, hildric, oktavian, lupus)",
        difficulty="Test difficulty modifier (default: +0 Challenging)",
        time_of_day="Time of day (affects wind conditions, default: midday)",
    )
    @app_commands.choices(
        character=[
            app_commands.Choice(name="Anara of Sānxiá", value="anara"),
            app_commands.Choice(name="Emmerich Falkenrath", value="emmerich"),
            app_commands.Choice(name="Hildric Sokhlundt", value="hildric"),
            app_commands.Choice(name="Oktavian Babel", value="oktavian"),
            app_commands.Choice(name="Lupus Leonard Joachim Rohrig", value="lupus"),
        ],
        time_of_day=[
            app_commands.Choice(name="Dawn", value="dawn"),
            app_commands.Choice(name="Midday", value="midday"),
            app_commands.Choice(name="Dusk", value="dusk"),
            app_commands.Choice(name="Midnight", value="midnight"),
        ],
    )
    async def boat_handling_slash(
        interaction: discord.Interaction,
        character: str,
        difficulty: int = 0,
        time_of_day: str = "midday",
    ):
        """Make a Boat Handling Test (Row or Sail) for a character."""
        await _perform_boat_handling(
            interaction, character, difficulty, time_of_day, is_slash=True
        )

    # Prefix command
    @bot.command(name="boat-handling")
    async def boat_handling_prefix(
        ctx, character: str, difficulty: int = 0, time_of_day: str = "midday"
    ):
        """Make a Boat Handling Test (Row or Sail) for a character."""
        await _perform_boat_handling(
            ctx, character, difficulty, time_of_day, is_slash=False
        )

    async def _perform_boat_handling(
        context, character: str, difficulty: int, time_of_day: str, is_slash: bool
    ):
        """Shared logic for boat handling tests."""
        try:
            # Get active weather modifiers if available
            guild_id = str(context.guild.id) if context.guild else None
            weather_mods = None
            if guild_id:
                weather_mods = get_active_weather_modifiers(guild_id, time_of_day)

            # Apply weather-based difficulty modifier
            original_difficulty = difficulty
            if weather_mods and weather_mods["boat_handling_penalty"] != 0:
                difficulty += weather_mods["boat_handling_penalty"]

            # Normalize character name
            char_key = character.lower().strip()

            # Check if character exists
            char = get_character(char_key)
            if char is None:
                available = ", ".join(get_available_characters())
                raise ValueError(
                    f"Character '{character}' not found. Available: {available}"
                )

            char_name = char["name"]

            # Determine which skill to use (Row is basic, all have it; Sail is advanced)
            river_skills = char.get("river_travelling_skills", {})
            row_skill = river_skills.get("Row")
            sail_skill = river_skills.get("Sail")
            lore_riverways = river_skills.get("Lore (Riverways)", 0)

            # Use Sail if they have it, otherwise Row
            if sail_skill:
                base_skill = sail_skill
                skill_name = "Sail"
            elif row_skill:
                base_skill = row_skill
                skill_name = "Row"
            else:
                raise ValueError(f"{char_name} has no Row or Sail skill!")

            # Calculate Lore (Riverways) bonus (first digit)
            # Handle None case (skill not learned yet)
            lore_bonus = (
                lore_riverways // 10 if (lore_riverways and lore_riverways > 0) else 0
            )

            # Calculate final target
            final_target = base_skill + difficulty + lore_bonus
            final_target = max(1, min(100, final_target))

            # Roll d100
            roll_result = random.randint(1, 100)

            # Calculate Success Level (SL)
            # SL = (tens digit of target) - (tens digit of roll)
            sl = (final_target // 10) - (roll_result // 10)

            # Determine outcome
            if roll_result <= final_target:
                # Success
                if sl >= 6:
                    outcome = "Astounding Success"
                    color = discord.Color.gold()
                    flavor = f"🌟 {char_name} expertly navigates the vessel with masterful control! The boat glides through the water as if guided by the gods themselves."
                    mechanics = "**Vessel maintained perfectly.** No issues, and the party may even gain time or avoid hazards."
                elif sl >= 4:
                    outcome = "Impressive Success"
                    color = discord.Color.green()
                    flavor = f"⚓ {char_name} handles the vessel with exceptional skill, anticipating every current and wind shift perfectly."
                    mechanics = "**Vessel under full control.** The journey proceeds smoothly without incident."
                elif sl >= 2:
                    outcome = "Success"
                    color = discord.Color.green()
                    flavor = f"✓ {char_name} maintains steady control of the vessel, navigating confidently through the waters."
                    mechanics = "**Vessel controlled.** The boat continues on course as planned."
                else:
                    outcome = "Marginal Success"
                    color = discord.Color.green()
                    flavor = f"~ {char_name} keeps the vessel under control, though it takes some effort and concentration."
                    mechanics = "**Barely maintained control.** Minor issues but nothing serious."
            else:
                # Failure
                if sl <= -6:
                    outcome = "Astounding Failure"
                    color = discord.Color.dark_red()
                    flavor = f"💀 {char_name} loses complete control! The vessel lurches dangerously, and panic ensues as water splashes over the sides!"
                    mechanics = "**CRITICAL FAILURE!** Vessel damaged or capsized. Possible injuries. GM determines consequences (collision, taking on water, cargo lost, etc.)."
                elif sl <= -4:
                    outcome = "Impressive Failure"
                    color = discord.Color.red()
                    flavor = f"⚠️ {char_name} struggles badly with the vessel! It veers off course alarmingly, and everyone aboard holds on tight."
                    delay_hours = roll_dice(2, 12)
                    delay_total = sum(delay_hours)
                    mechanics = f"**Severe loss of control.** Vessel forced off course. **Delay: {delay_total} hours**. Possible damage to vessel or cargo. May require repairs."
                elif sl <= -2:
                    outcome = "Failure"
                    color = discord.Color.orange()
                    flavor = f"✗ {char_name} fails to maintain proper control. The vessel drifts or slows, requiring corrective action."
                    mechanics = "**Loss of control.** Vessel goes off course owr slows significantly. Delay of 1-2 hours to correct. Minor damage possible."
                else:
                    outcome = "Marginal Failure"
                    color = discord.Color.orange()
                    flavor = f"≈ {char_name} barely loses control, but manages to avoid the worst consequences through sheer luck."
                    mechanics = "**Near miss.** Brief loss of control but quickly recovered. Small delay (~30 minutes) or minor course correction needed."

            # Check for doubles (critical/fumble)
            doubles_result = check_wfrp_doubles(roll_result, final_target)
            is_critical = doubles_result == "crit"
            is_fumble = doubles_result == "fumble"

            # Build embed
            embed = discord.Embed(
                title=f"🚢 Boat Handling Test: {char_name}", color=color
            )

            # Character info
            embed.add_field(
                name="Character",
                value=f"{char_name}\n{char['species']} • {char['status']}",
                inline=True,
            )

            # Skill breakdown
            skill_breakdown = f"**{skill_name}:** {base_skill}"
            if lore_bonus > 0:
                skill_breakdown += f"\n**Lore (Riverways) Bonus:** +{lore_bonus}"

            # Show difficulty (base and modified if weather applies)
            difficulty_map = {
                -50: "Impossible",
                -40: "Futile",
                -30: "Very Difficult",
                -20: "Hard",
                -10: "Difficult",
                0: "Challenging",
                20: "Average",
                40: "Easy",
                60: "Very Easy",
            }

            # Always show difficulty if it's not default Challenging or if weather is active
            if original_difficulty != 0 or weather_mods:
                diff_name = difficulty_map.get(
                    original_difficulty, f"{original_difficulty:+d}"
                )

                # Show weather-modified difficulty if weather is active
                if weather_mods:
                    if weather_mods["boat_handling_penalty"] != 0:
                        # Weather has a penalty - show base, modifier, and final
                        modified_diff_name = difficulty_map.get(
                            difficulty, f"{difficulty:+d}"
                        )
                        skill_breakdown += f"\n**Base Difficulty:** {diff_name} ({original_difficulty:+d})"
                        skill_breakdown += f"\n**Weather Modifier:** {weather_mods['boat_handling_penalty']:+d}"
                        skill_breakdown += f"\n**Final Difficulty:** {modified_diff_name} ({difficulty:+d})"
                    else:
                        # Weather is active but no penalty
                        skill_breakdown += (
                            f"\n**Difficulty:** {diff_name} ({original_difficulty:+d})"
                        )
                        skill_breakdown += "\n**Weather Modifier:** 0 (no penalty)"
                else:
                    # No weather, just show difficulty
                    skill_breakdown += (
                        f"\n**Difficulty:** {diff_name} ({original_difficulty:+d})"
                    )

            embed.add_field(name="Skill Check", value=skill_breakdown, inline=True)

            # Roll result
            embed.add_field(
                name="Target / Roll",
                value=f"**{final_target}** / **{roll_result}**",
                inline=True,
            )

            # Outcome
            sl_display = f"{sl:+d}" if sl != 0 else "0"
            outcome_text = f"**{outcome}**\nSuccess Level: {sl_display}"

            if is_critical:
                outcome_text += "\n⚡ **CRITICAL SUCCESS!**"
                color = discord.Color.gold()
                embed.color = color
            elif is_fumble:
                outcome_text += "\n💀 **FUMBLE!**"
                color = discord.Color.dark_red()
                embed.color = color

            embed.add_field(name="Result", value=outcome_text, inline=False)

            # Flavor text
            embed.add_field(name="Narrative", value=flavor, inline=False)

            # Mechanical consequences
            embed.add_field(name="Mechanical Effect", value=mechanics, inline=False)

            # Weather impact (if active)
            if weather_mods:
                weather_text = format_weather_impact_for_embed(weather_mods)
                embed.add_field(
                    name=f"🌦️ Weather Impact ({time_of_day.title()})",
                    value=weather_text,
                    inline=False,
                )

            # Footer
            if is_slash:
                embed.set_footer(text=f"Test by {context.user.display_name}")
                await context.response.send_message(embed=embed)
            else:
                embed.set_footer(text=f"Test by {context.author.display_name}")
                await context.send(embed=embed)

            # Send command log to boat-travelling-log channel
            await _send_command_log(
                context,
                character,
                difficulty,
                time_of_day,
                original_difficulty,
                is_slash,
            )

        except ValueError as e:
            error_embed = discord.Embed(
                title="❌ Invalid Boat Handling Test",
                description=str(e),
                color=discord.Color.red(),
            )
            error_embed.add_field(
                name="Usage",
                value="• `/boat-handling anara`\n• `/boat-handling emmerich -20`\n• `/boat-handling hildric 0`",
                inline=False,
            )
            if is_slash:
                await context.response.send_message(embed=error_embed, ephemeral=True)
            else:
                await context.send(embed=error_embed)

        except (discord.DiscordException, KeyError, AttributeError) as e:
            if is_slash:
                await context.response.send_message(
                    f"❌ An error occurred: {str(e)}", ephemeral=True
                )
            else:
                await context.send(f"❌ An error occurred: {str(e)}")

    async def _send_command_log(
        context,
        character: str,
        difficulty: int,
        time_of_day: str,
        original_difficulty: int,
        is_slash: bool,
    ):
        """Send command details to boat-travelling-log channel."""
        try:
            # Find the log channel
            log_channel = discord.utils.get(
                context.guild.text_channels, name="boat-travelling-log"
            )
            if not log_channel:
                return  # Silently fail if log channel doesn't exist

            # Get username
            if is_slash:
                username = context.user.display_name
                user_id = context.user.id
            else:
                username = context.author.display_name
                user_id = context.author.id

            # Build command string
            if is_slash:
                command_str = f"/boat-handling character:{character}"
                if difficulty != 0:
                    command_str += f" difficulty:{original_difficulty}"
                if time_of_day != "midday":
                    command_str += f" time_of_day:{time_of_day}"
            else:
                command_str = f"!boat-handling {character}"
                if difficulty != 0:
                    command_str += f" {original_difficulty}"
                if time_of_day != "midday":
                    command_str += f" {time_of_day}"

            # Create log embed
            log_embed = discord.Embed(
                title="📋 Command Log: Boat Handling",
                description=f"**User:** {username} (`{user_id}`)\n**Command:** `{command_str}`",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow(),
            )

            log_embed.add_field(name="Character", value=character.title(), inline=True)
            log_embed.add_field(
                name="Difficulty", value=f"{original_difficulty:+d}", inline=True
            )
            log_embed.add_field(
                name="Time of Day", value=time_of_day.title(), inline=True
            )

            await log_channel.send(embed=log_embed)

        except (discord.Forbidden, discord.HTTPException, AttributeError):
            # Silently fail - logging is not critical
            pass
