"""
Application Configuration Module

Centralized configuration loading from environment variables with validation
and sensible defaults. Provides clean separation between configuration and
application logic.

Usage:
    from config import AppConfig

    # Load from environment
    config = AppConfig.from_env()

    # Use in bot creation
    bot = create_bot(config)

Environment Variables:
    DISCORD_TOKEN (required): Discord bot authentication token
    DB_PATH (optional): Path to SQLite database file
        Default: "data/weather_state.db"
    LOG_LEVEL (optional): Logging verbosity level
        Default: "DEBUG"
        Valid: DEBUG, INFO, WARNING, ERROR, CRITICAL

Design Principles:
    - Fail fast: Missing required config raises ValueError immediately
    - Explicit: All config values are typed and documented
    - Testable: Configuration can be created directly for testing
    - Immutable: Configuration is frozen after creation (use dataclass frozen=True)
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


@dataclass(frozen=True)
class AppConfig:
    """
    Application configuration with validated settings.

    Attributes:
        discord_token: Discord bot authentication token (required)
        db_path: Path to SQLite database file
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        command_prefix: Discord bot command prefix for prefix commands (e.g., "!")
        log_filename: File to write Discord logs to

    The frozen=True makes this immutable after creation, preventing
    accidental configuration changes during runtime.
    """

    discord_token: str
    db_path: str
    log_level: str = "DEBUG"
    command_prefix: str = "!"
    log_filename: str = "discord.log"

    def __post_init__(self):
        """
        Validate configuration after creation.

        Raises:
            ValueError: If discord_token is empty or log_level is invalid
        """
        if not self.discord_token:
            raise ValueError("discord_token cannot be empty")

        valid_log_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.log_level.upper() not in valid_log_levels:
            raise ValueError(
                f"Invalid log_level: {self.log_level}. "
                f"Must be one of: {', '.join(valid_log_levels)}"
            )

    @classmethod
    def from_env(cls, env: Optional[dict] = None) -> "AppConfig":
        """
        Load configuration from environment variables.

        Args:
            env: Optional dict of environment variables (defaults to os.environ)
                 Useful for testing with custom environments

        Returns:
            AppConfig instance with loaded configuration

        Raises:
            ValueError: If DISCORD_TOKEN is missing from environment

        Examples:
            >>> # Load from system environment
            >>> config = AppConfig.from_env()

            >>> # Load from custom environment (testing)
            >>> test_env = {"DISCORD_TOKEN": "test_token"}
            >>> config = AppConfig.from_env(test_env)
        """
        # Load .env file if using system environment (not for tests)
        if env is None:
            load_dotenv()
            env = os.environ

        # Required: Discord token
        discord_token = env.get("DISCORD_TOKEN")
        if not discord_token:
            raise ValueError(
                "DISCORD_TOKEN environment variable is required. "
                "Please set it in your .env file or environment."
            )

        # Optional: Database path with sensible default
        db_path = env.get("DB_PATH")
        if not db_path:
            # Default to data/ directory, create if doesn't exist
            data_dir = Path("data")
            data_dir.mkdir(exist_ok=True)
            db_path = str(data_dir / "weather_state.db")

        # Optional: Logging level
        log_level = env.get("LOG_LEVEL", "DEBUG").upper()

        # Optional: Command prefix
        command_prefix = env.get("COMMAND_PREFIX", "!")

        # Optional: Log filename
        log_filename = env.get("LOG_FILENAME", "discord.log")

        return cls(
            discord_token=discord_token,
            db_path=db_path,
            log_level=log_level,
            command_prefix=command_prefix,
            log_filename=log_filename,
        )

    def to_dict(self) -> dict:
        """
        Convert configuration to dictionary.

        Useful for logging or serialization (exclude sensitive tokens).

        Returns:
            Dict with configuration (token is redacted)
        """
        return {
            "discord_token": "***REDACTED***",
            "db_path": self.db_path,
            "log_level": self.log_level,
            "command_prefix": self.command_prefix,
            "log_filename": self.log_filename,
        }

    def __repr__(self) -> str:
        """String representation with token redacted for security."""
        return (
            f"AppConfig(discord_token='***REDACTED***', "
            f"db_path='{self.db_path}', log_level='{self.log_level}', "
            f"command_prefix='{self.command_prefix}', "
            f"log_filename='{self.log_filename}')"
        )


# Convenience function for loading config with validation
def load_config() -> AppConfig:
    """
    Load and validate application configuration.

    Convenience wrapper around AppConfig.from_env() with better error messages.

    Returns:
        Validated AppConfig instance

    Raises:
        ValueError: If required configuration is missing

    Example:
        >>> from config import load_config
        >>> config = load_config()
        >>> print(f"Using database: {config.db_path}")
    """
    try:
        return AppConfig.from_env()
    except ValueError as e:
        # Re-raise with additional context
        raise ValueError(
            f"Configuration error: {e}\n\n"
            "Please ensure you have a .env file with DISCORD_TOKEN set, or "
            "set DISCORD_TOKEN as an environment variable."
        ) from e
