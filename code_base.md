# Codebase Documentation

This document provides a detailed overview of the Python files in the `travelling-bot` codebase.

### `main.py`

**Purpose:**
The main entry point for the WFRP River Travel Discord Bot. This file is responsible for initializing the Discord bot, loading all the command modules, setting up event handlers, and starting the bot. It also initiates a Flask web server to keep the bot alive on hosting platforms like Render.

**Dependencies:**
- **External:** `os`, `logging`, `discord`, `discord.ext.commands`, `dotenv`.
- **Internal:**
  - `server`: For the keep-alive web server.
  - `commands.roll`: Loads the dice rolling commands.
  - `commands.boat_handling`: Loads the boat handling commands.
  - `commands.weather`: Loads the weather simulation commands.
  - `commands.river_encounter`: Loads the river encounter commands.
  - `commands.help`: Loads the custom help command.

**Functions:**
- `on_ready()`: An event handler that is called when the bot has successfully connected to Discord. It syncs the application (slash) commands with Discord's servers.
- `on_message(message)`: An event handler that processes incoming messages. It's used to handle prefix-based commands (e.g., `!roll`). It ignores messages from other bots.
- `hello_slash(interaction)`: A simple slash command (`/hello`) that serves as a basic greeting and readiness check for the bot.
- `hello_prefix(ctx)`: The prefix command version (`!hello`) of the greeting command.

**Architectural Role:**
`main.py` is the central orchestrator of the bot. It's the executable entry point that brings all the different parts of the application—commands, services, and utilities—together. It's responsible for the bot's lifecycle and the initial setup of all its components.

---

### `server.py`

**Purpose:**
Provides a simple Flask web server. Its primary function is to create a health check endpoint that can be pinged by a service like Render to prevent the bot from being put to sleep due to inactivity on free hosting tiers.

**Dependencies:**
- **External:** `flask`, `threading`, `os`.
- **Internal:** None.

**Classes:**
- `Flask(app)`: The main Flask application object.

**Functions:**
- `home()`: Defines the route for the root URL (`/`) and returns a simple "alive" message.
- `health()`: Defines a `/health` endpoint that returns a JSON object indicating the bot's status.
- `run()`: Starts the Flask server.
- `keep_alive()`: A utility function that starts the Flask server in a separate thread, allowing the Discord bot to run concurrently.

**Architectural Role:**
This file provides a crucial infrastructure component for deployment. It ensures the bot remains online on platforms that have an inactivity timeout. It's a supporting module, not part of the core bot logic itself.

---

## `commands/`

This directory contains all the user-facing commands for the bot.

### `commands/boat_handling.py`

**Purpose:**
Implements the `/boat-handling` command, which allows users to make a WFRP Boat Handling skill test for a character. This command integrates character skills, weather modifiers, and WFRP's success level mechanics.

**Dependencies:**
- **External:** `discord`, `discord.ext.commands`.
- **Internal:**
  - `db.character_data`: To get character information and skills.
  - `utils.modifier_calculator`: To get weather modifiers.
  - `commands.constants`: For default values.
  - `commands.error_handlers`: For standardized error handling.
  - `commands.services.boat_handling_service`: For the core logic of the boat handling test.
  - `commands.services.command_logger`: To log command usage.

**Functions:**
- `setup(bot)`: Registers the `boat-handling` slash and prefix commands with the bot.
- `_perform_boat_handling(...)`: The core logic for the command. It fetches character and weather data, uses the `BoatHandlingService` to perform the test, and then builds and sends the result as a Discord embed.
- `_build_boat_handling_embed(...)`: A helper function to construct the detailed Discord embed for the command's output.

**Architectural Role:**
This file defines a primary user interaction command. It follows the bot's command architecture by separating the Discord-facing command logic from the core business logic (which is in the `BoatHandlingService`).

### `commands/constants.py`

**Purpose:**
A centralized place for constants used across the command modules. This includes channel names, role names, difficulty modifiers, and other "magic strings" to avoid hardcoding them in multiple places.

**Dependencies:**
- **External:** None.
- **Internal:** None.

**Architectural Role:**
This is a configuration and constants file that promotes code maintainability and consistency.

### `commands/error_handlers.py`

**Purpose:**
Provides standardized functions for handling and displaying errors to the user. This ensures that error messages are consistent across all commands.

**Dependencies:**
- **External:** `discord`, `discord.ext.commands`.
- **Internal:** None.

**Functions:**
- `send_error_embed(...)`: Sends a standardized red-colored error embed.
- `send_info_embed(...)`: Sends a standardized blue-colored informational embed.
- `handle_value_error(...)`: A specific handler for `ValueError` exceptions, which are common for invalid user input.
- `handle_discord_error(...)`: A handler for Discord API-related errors.
- `handle_permission_error(...)`: A handler for when a user lacks the required permissions for a command.

**Architectural Role:**
This is a utility module for the `commands` package, providing reusable error handling logic to keep the command files cleaner and more focused on their primary logic.

### `commands/help.py`

**Purpose:**
Implements a custom `/help` command that provides detailed information about all the bot's commands, including examples and explanations of the game mechanics.

**Dependencies:**
- **External:** `discord`, `discord.ext.commands`.
- **Internal:** None.

**Functions:**
- `setup(bot)`: Registers the `help` slash and prefix commands.
- `_create_general_help_embed()`: Creates the embed for the general help command.
- `_create_detailed_help_embed(command)`: Creates embeds for specific commands (e.g., `/help roll`).
- Several private helper functions (`_create_roll_help`, `_create_boat_handling_help`, etc.) to generate the content for each command's detailed help message.

**Architectural Role:**
This file provides user documentation and guidance directly within the bot, improving usability.

### `commands/permissions.py`

**Purpose:**
Provides utility functions for checking user permissions, specifically for gating access to GM-only commands and features.

**Dependencies:**
- **External:** `discord`, `discord.ext.commands`.
- **Internal:** None.

**Functions:**
- `is_gm(user)`: Checks if a user has GM permissions (either by being the server owner or having a "GM" role).
- `require_gm()`: A decorator that can be used to restrict a command to GMs only (noted as a future enhancement).

**Architectural Role:**
This is a security and permissions utility module for the `commands` package.

### `commands/river_encounter.py`

**Purpose:**
Implements the `/river-encounter` command, which generates random river encounters. It features a dual-message system: a cryptic, atmospheric message for players and a detailed mechanical breakdown for the GM in a separate channel.

**Dependencies:**
- **External:** `discord`, `discord.ext.commands`.
- **Internal:**
  - `utils.encounter_mechanics`: For encounter generation logic and formatting.
  - `commands.permissions`: To check for GM permissions for override commands.
  - `commands.constants`: For channel names.
  - `commands.error_handlers`: For error handling.
  - `commands.services.command_logger`: For logging.
  - `commands.services.encounter_service`: For the core logic of generating encounters.

**Functions:**
- `setup_river_encounter(bot)`: Registers the `river-encounter` command.
- `format_player_flavor_embed(...)`: Formats the player-facing embed.
- `format_gm_simple_embed(...)`: Formats the GM-facing embed for simple encounters.
- `format_gm_accident_embed(...)`: Formats the GM-facing embed for complex "accident" encounters.
- `send_gm_notification(...)`: Sends the detailed encounter information to the GM notification channel.

**Architectural Role:**
This file defines a major feature of the bot, providing dynamic content and engaging gameplay scenarios. It demonstrates a sophisticated command structure with different outputs for different user roles.

### `commands/roll.py`

**Purpose:**
Implements the `/roll` command for dice rolling. It supports both simple dice notation (e.g., `2d6+3`) and complex WFRP skill tests with success levels and critical/fumble detection.

**Dependencies:**
- **External:** `discord`, `discord.ext.commands`.
- **Internal:**
  - `commands.services.roll_service`: For the business logic of dice rolling.
  - `commands.services.command_logger`: For logging command usage.
  - `commands.constants`: For constants like default difficulty.
  - `commands.error_handlers`: For handling invalid dice notation.

**Functions:**
- `setup(bot)`: Registers the `roll` command.
- `_perform_roll(...)`: The core logic that parses the roll, uses the `RollService` to get the result, and builds the response embed.
- `_build_roll_embed(...)`: Constructs the Discord embed to display the roll result.

**Architectural Role:**
This is a fundamental command for any TTRPG bot. It showcases the separation of concerns between the command interface and the underlying game mechanics logic.

### `commands/weather.py`

**Purpose:**
Provides the user interface for the weather system through the `/weather` and `/weather-stage-config` commands. It allows users to start journeys, advance time (day by day or in stages), and view weather history. GM-only commands allow for configuration and overrides.

**Dependencies:**
- **External:** `discord`, `discord.ext.commands`.
- **Internal:**
  - `commands.weather_modules.handler.WeatherCommandHandler`: The core handler for all weather-related logic.
  - `commands.permissions`: To check for GM permissions.
  - `commands.error_handlers`: For standardized error messages.

**Functions:**
- `setup(bot)`: Registers the `weather` and `weather-stage-config` commands.
- `weather_slash(...)` and `weather_prefix(...)`: The command handlers that delegate all logic to the `WeatherCommandHandler`.
- `weather_stage_config_slash(...)` and `weather_stage_config_prefix(...)`: The command handlers for stage configuration, also delegating to the `WeatherCommandHandler`.

**Architectural Role:**
This file is the command-line interface for the complex weather simulation system. It acts as a thin layer that passes user input to the `WeatherCommandHandler`.

---

## `commands/services/`

This sub-package contains service classes that encapsulate the core business logic for the commands, separating it from the Discord-specific interaction code.

### `commands/services/boat_handling_service.py`

**Purpose:**
Contains the business logic for performing a boat handling test. This includes selecting the correct skill (Sail vs. Row), calculating bonuses, performing the dice roll, and generating a narrative outcome based on the success level.

**Dependencies:**
- **Internal:** `utils.wfrp_mechanics`.

**Classes:**
- `BoatHandlingResult`: A dataclass to hold the detailed result of a boat handling test.
- `BoatHandlingService`: The service class that contains the logic.
  - `determine_skill(...)`: Chooses between Sail and Row skills.
  - `calculate_lore_bonus(...)`: Calculates the bonus from the Lore (Riverways) skill.
  - `perform_boat_test(...)`: The main method that executes the test and returns a `BoatHandlingResult`.
  - `_generate_outcome(...)`: A private method to generate narrative text based on the test's success level.

**Architectural Role:**
This service encapsulates the core mechanics of the boat handling feature, making the `commands/boat_handling.py` file cleaner and allowing the logic to be tested independently of Discord.

### `commands/services/command_logger.py`

**Purpose:**
Provides a centralized service for logging command usage to a specific Discord channel (`#boat-travelling-log`).

**Dependencies:**
- **External:** `discord`.

**Classes:**
- `CommandLogEntry`: A dataclass to hold the information for a log entry.
- `CommandLogger`: The service class.
  - `log_command(...)`: Logs a command execution to the log channel.
  - `log_command_from_context(...)`: A convenience method to log directly from a Discord `Interaction` or `Context` object.

**Architectural Role:**
This is a utility service that provides a consistent logging mechanism for all commands, helping with debugging and monitoring bot activity.

### `commands/services/encounter_service.py`

**Purpose:**
Wraps the encounter generation logic from `utils.encounter_mechanics` to provide a clean and validated interface for the `/river-encounter` command.

**Dependencies:**
- **Internal:** `utils.encounter_mechanics`.

**Classes:**
- `EncounterService`: The service class.
  - `generate_encounter(...)`: Generates a random or specific encounter.
  - `_validate_encounter_data(...)`: Ensures the generated encounter data is valid.
  - `is_valid_encounter_type(...)`: Checks if a given encounter type is valid.
  - `get_valid_types()`: Returns a list of all valid encounter types.

**Architectural Role:**
This service acts as a bridge between the command layer and the low-level encounter generation mechanics, adding a layer of validation and abstraction.

### `commands/services/roll_service.py`

**Purpose:**
Contains the business logic for dice rolling and WFRP skill tests. It parses dice notation, performs the rolls, and calculates success levels and critical/fumble outcomes.

**Dependencies:**
- **Internal:** `utils.wfrp_mechanics`, `commands.constants`.

**Classes:**
- `RollResult`: A dataclass to hold the detailed result of a dice roll.
- `RollService`: The service class.
  - `roll_simple_dice(...)`: Handles simple dice rolls (e.g., `2d6+3`).
  - `roll_wfrp_test(...)`: Handles WFRP skill tests, including success level and doubles calculation.

**Architectural Role:**
This service encapsulates all the dice rolling logic, making it reusable and testable. It separates the complex game mechanics from the Discord command interface.

---

## `commands/weather_modules/`

This sub-package contains modules that break down the complex weather command's logic into more manageable parts.

### `commands/weather_modules/display.py`

**Purpose:**
Manages the creation and sending of all user-facing weather-related Discord embeds. This includes daily weather reports, historical weather views, and error/info messages.

**Dependencies:**
- **External:** `discord`, `datetime`.
- **Internal:** `commands.weather_modules.formatters`, `utils.weather_mechanics`, `db.weather_data`.

**Classes:**
- `WeatherDisplayManager`: A class with static methods for creating and sending embeds.
  - `show_daily_weather(...)`: Displays the weather for a single day.
  - `_create_daily_weather_embed(...)`: Constructs the daily weather embed.
  - `_format_wind_conditions(...)`, `_format_weather_condition(...)`, `_format_weather_effects(...)`, `_format_temperature(...)`: Helper methods for formatting different parts of the embed.
  - `send_error(...)`, `send_info(...)`: Methods for sending standardized error and info messages.

**Architectural Role:**
This module is the "view" part of the weather system's MVC-like architecture. It's responsible for all user-facing presentation.

### `commands/weather_modules/formatters.py`

**Purpose:**
Provides pure utility functions for formatting weather-related data, such as converting weather types to emojis, formatting names, and creating display strings for modifiers.

**Dependencies:**
- **External:** None.
- **Internal:** None.

**Classes:**
- `WeatherFormatters`: A utility class with static methods.
  - `get_weather_emoji(...)`: Returns an emoji for a given weather type.
  - `get_temperature_emoji(...)`: Returns an emoji for a given temperature.
  - `format_modifier_for_display(...)`: Formats a wind modifier string for display.
  - `format_province_name(...)`, `format_season_name(...)`: Format names for display.

**Architectural Role:**
This is a formatting utility module, ensuring consistent presentation of weather data across the application.

### `commands/weather_modules/handler.py`

**Purpose:**
The main business logic handler for all weather commands. It orchestrates the interactions between weather data generation, storage, and display.

**Dependencies:**
- **External:** `discord`.
- **Internal:** `db.weather_storage`, `utils.weather_mechanics`, `commands.weather_modules.display`, `commands.weather_modules.stages`, `commands.weather_modules.notifications`.

**Classes:**
- `WeatherCommandHandler`: The main class that handles all weather command logic.
  - `handle_command(...)`: The main entry point that routes actions to other handler methods.
  - `_handle_next(...)`, `_handle_next_stage(...)`, `_handle_journey(...)`, `_handle_view(...)`, `_handle_end(...)`, `_handle_override(...)`: Private methods to handle each specific weather action.
  - `configure_stage(...)`: Handles the logic for the `/weather-stage-config` command.
  - `_generate_daily_weather(...)`: The core logic for generating a single day's weather.
  - `_reconstruct_weather_data(...)`: Rebuilds display data from the database for historical views.
  - `_update_cooldown_trackers(...)`: Manages the cooldowns for special weather events.
  - `_send_command_log(...)`: Logs the weather command usage.

**Architectural Role:**
This is the "controller" in the weather system's MVC-like architecture. It contains all the business logic and orchestrates the other weather modules.

### `commands/weather_modules/notifications.py`

**Purpose:**
Manages sending mechanics-focused notifications to the GM channel for weather events. This includes detailed breakdowns of modifiers, penalties, and special events.

**Dependencies:**
- **External:** `discord`.
- **Internal:** `commands.weather_modules.formatters`, `db.weather_data`.

**Classes:**
- `NotificationManager`: A class with static methods for sending notifications.
  - `send_weather_notification(...)`: Sends a detailed weather mechanics embed to the GM channel.
  - `_create_notification_embed(...)`: Constructs the GM notification embed.
  - `_format_boat_handling_modifiers(...)`: Formats the boat handling modifiers for the GM view.
  - `send_stage_notification(...)`: Sends a notification when a stage is completed.
  - `send_journey_notification(...)`: Sends notifications for journey start/end events.

**Architectural Role:**
This module provides a specialized notification service for GMs, separating their view of the data from the players'.

### `commands/weather_modules/stages.py`

**Purpose:**
Handles the display of multi-day weather "stages". It provides a consolidated view of weather across several days for efficient planning and review.

**Dependencies:**
- **External:** `discord`, `datetime`.
- **Internal:** `commands.weather_modules.formatters`.

**Classes:**
- `StageDisplayManager`: A class with static methods for creating stage-based embeds.
  - `show_stage_summary(...)`: Displays a summary of a single stage.
  - `_create_stage_embed(...)`: Constructs the embed for a single stage.
  - `_format_day_summary(...)`: Formats a single day's weather into a condensed summary.
  - `_format_condensed_wind(...)`: Creates a very compact summary of wind conditions for a day.
  - `show_all_stages(...)`: Displays an overview of all stages in a journey.
  - `_create_all_stages_embed(...)`: Constructs the embed for the all-stages overview.

**Architectural Role:**
This module is part of the "view" layer for the weather system, specializing in the presentation of multi-day data.

---

## `db/`

This directory contains modules for data storage and retrieval.

### `db/character_data.py`

**Purpose:**
Stores the data for all player characters, including their statistics, skills, and other attributes. It provides functions to look up character data.

**Dependencies:**
- **External:** None.
- **Internal:** None.

**Data:**
- `characters_data`: A dictionary containing the data for each character.

**Functions:**
- `get_character(character_key)`: Retrieves the data for a specific character.
- `get_available_characters()`: Returns a list of all available character keys.
- `get_boat_handling_skill(character)`: Determines which boat handling skill a character should use.
- `get_lore_riverways_bonus(character)`: Calculates the bonus from the Lore (Riverways) skill.

**Architectural Role:**
This file acts as a simple, in-memory database for character information. It's a core data provider for commands that involve character skills.

### `db/encounter_data.py`

**Purpose:**
Contains all the static data for the river encounter system. This includes the d100 tables for different encounter types, the player-facing flavor texts, and the detailed mechanical data for GMs.

**Dependencies:**
- **External:** `random`.

**Data:**
- `POSITIVE_FLAVOR_TEXTS`, `COINCIDENTAL_FLAVOR_TEXTS`, etc.: Lists of flavor text strings.
- `POSITIVE_ENCOUNTERS`, `COINCIDENTAL_ENCOUNTERS`, etc.: Dictionaries mapping d100 roll ranges to encounter details.

**Functions:**
- `get_encounter_type_from_roll(roll)`: Determines the encounter type based on a d100 roll.
- `get_random_flavor_text(encounter_type)`: Gets a random flavor text for a given encounter type.
- `get_positive_encounter_from_roll(roll)`, `get_coincidental_encounter_from_roll(roll)`, etc.: Functions to get the specific encounter details from the data tables based on a d100 roll.

**Architectural Role:**
This is a data module that provides all the content for the river encounter system. It separates the encounter data from the logic that uses it.

### `db/weather_data.py`

**Purpose:**
Contains all the static data for the weather generation system. This includes tables for wind strength and direction, weather conditions by season, temperature ranges, and province-specific base temperatures.

**Dependencies:**
- **External:** None.
- **Internal:** None.

**Data:**
- `WIND_STRENGTH`, `WIND_DIRECTION`, `WIND_MODIFIERS`: Data for the wind system.
- `WEATHER_RANGES`, `WEATHER_EFFECTS`: Data for weather conditions.
- `PROVINCE_TEMPERATURES`, `TEMPERATURE_RANGES`, `TEMPERATURE_DESCRIPTIONS`: Data for the temperature system.

**Functions:**
- `get_wind_strength_from_roll(roll)`, `get_wind_direction_from_roll(roll)`: Convert d10 rolls to wind conditions.
- `get_weather_from_roll(season, roll)`: Get a weather type based on season and a d100 roll.
- `get_temperature_category_from_roll(roll)`: Get a temperature category from a d100 roll.
- `get_province_base_temperature(province, season)`: Get the base temperature for a given province and season.
- `get_available_provinces()`: Returns a list of all available provinces.

**Architectural Role:**
This is a data module that provides all the static data and lookup tables for the weather generation system.

### `db/weather_storage.py`

**Purpose:**
Provides a persistent storage system for weather data using SQLite. It manages the state of multi-day journeys for each Discord guild, including the current day, season, province, and historical weather data.

**Dependencies:**
- **External:** `sqlite3`, `json`, `datetime`, `pathlib`.
- **Internal:** None.

**Classes:**
- `WeatherStorage`: The main class for interacting with the weather database.
  - `__init__(db_path)`: Initializes the database connection and creates tables if they don't exist.
  - `_get_connection()`: A context manager for safe database connections.
  - `init_database()`: Creates the database schema and handles migrations.
  - `start_journey(...)`: Starts a new journey for a guild.
  - `save_daily_weather(...)`: Saves the weather data for a specific day.
  - `get_daily_weather(...)`: Retrieves the weather data for a specific day.
  - `get_current_day(...)`: Gets the current day of the journey.
  - `advance_day()`: Increments the journey's day counter.
  - `advance_stage()`: Advances the journey to the next stage.
  - `update_stage_duration(...)`, `update_stage_display_mode(...)`: Update stage configuration.
  - `get_journey_state(...)`: Retrieves the current state of a guild's journey.
  - `end_journey(...)`: Deletes all data for a guild's journey.
  - `get_cooldown_status(...)`, `increment_cooldown(...)`, `reset_cooldown(...)`: Methods for managing special event cooldowns.

**Architectural Role:**
This is the persistence layer for the weather system. It's responsible for storing and retrieving all journey-related data, allowing the bot to maintain state across restarts and manage long-running journeys.

---

## `utils/`

This directory contains utility modules with core game mechanics and helper functions.

### `utils/encounter_mechanics.py`

**Purpose:**
Handles the logic for generating river encounters. This includes rolling for the encounter type, generating the specific details, and providing formatting functions for displaying the encounter data.

**Dependencies:**
- **External:** `discord`.
- **Internal:** `utils.wfrp_mechanics`, `db.encounter_data`.

**Functions:**
- `roll_encounter_type()`: Rolls a d100 to determine the encounter type.
- `generate_encounter(...)`: The main function that generates a complete encounter, including player flavor text and GM mechanics.
- `calculate_cargo_loss()`: Calculates the amount of cargo lost during a "Cargo Shift" accident.
- A variety of formatting functions (`format_test_requirement`, `format_damage_result`, etc.) and display utility functions (`get_encounter_emoji`, `get_severity_color`, etc.).

**Architectural Role:**
This module contains the core logic for the encounter generation system. It's used by the `EncounterService` to provide encounter data to the `/river-encounter` command.

### `utils/modifier_calculator.py`

**Purpose:**
This module is responsible for calculating and extracting weather-based modifiers for boat handling tests. It acts as a bridge between the weather system and the boat handling command.

**Dependencies:**
- **Internal:** `db.weather_storage`, `db.weather_data`, `utils.weather_mechanics`.

**Functions:**
- `get_active_weather_modifiers(...)`: The main function that retrieves the current weather and calculates the relevant modifiers for a given time of day.
- `_get_wind_for_time(...)`: A helper to extract the wind data for a specific time from the daily timeline.
- `_parse_speed_modifier(...)`: Parses the speed modifier percentage from a text string.
- `_extract_boat_handling_penalty(...)`: Extracts any penalty to boat handling tests from the weather data.
- `format_weather_impact_for_embed(...)`: Formats the weather modifiers into a string suitable for a Discord embed.

**Architectural Role:**
This is a utility module that provides a specific calculation service. It decouples the `boat_handling` command from the complexities of the weather data structure.

### `utils/weather_mechanics.py`

**Purpose:**
Contains the core logic for generating weather conditions. This includes generating daily wind patterns, rolling for weather types based on the season, and calculating temperature with special events like cold fronts and heat waves.

**Dependencies:**
- **External:** `random`.
- **Internal:** `db.weather_data`.

**Functions:**
- `generate_daily_wind()`: Generates a full day's wind timeline.
- `generate_daily_wind_with_previous(...)`: Generates a day's wind with continuity from the previous day.
- `roll_weather_condition(season)`: Rolls for a weather type based on the season.
- `roll_temperature_with_special_events(...)`: The main function for temperature generation, which includes logic for handling cold fronts and heat waves.
- `handle_cold_front(...)`, `handle_heat_wave(...)`: Logic for managing the duration and cooldown of special weather events.
- `apply_wind_chill(...)`: Calculates the perceived temperature based on wind strength.

**Architectural Role:**
This module is the heart of the weather simulation. It contains all the procedural generation logic for creating dynamic and varied weather conditions.

### `utils/wfrp_mechanics.py`

**Purpose:**
Implements the core game mechanics for Warhammer Fantasy Roleplay (WFRP) 4th Edition. This includes dice parsing, success level calculation, and the doubles system for criticals and fumbles.

**Dependencies:**
- **External:** `re`, `random`.
- **Internal:** None.

**Functions:**
- `parse_dice_notation(notation)`: Parses a dice string (e.g., "2d6+3") into its components.
- `roll_dice(num_dice, die_size)`: Rolls a specified number of dice.
- `check_wfrp_doubles(roll_result, target)`: Determines if a d100 roll is a critical success or a fumble based on the doubles rule.
- `calculate_success_level(roll, target)`: Calculates the Success Level (SL) of a WFRP test.
- `get_success_level_name(sl, success)`: Gets the descriptive name for a given SL (e.g., "Astounding Success").
- `get_difficulty_name(modifier)`: Gets the name for a given difficulty modifier (e.g., "Hard" for -20).

**Architectural Role:**
This is a fundamental utility module that provides the core game rules as pure functions. It's used by any part of the application that needs to perform dice rolls or skill tests according to WFRP rules.
