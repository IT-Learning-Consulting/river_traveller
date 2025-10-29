"""
Weather command module - refactored for maintainability.

This module provides a clean separation of concerns for weather commands:
- handler: Business logic and orchestration
- display: Discord embed creation and display
- stages: Multi-day stage display
- notifications: GM channel notifications
- formatters: Pure utility functions for formatting
"""

# Import available modules (some may not be implemented yet during refactoring)
try:
    from commands.weather_modules.formatters import WeatherFormatters
except ImportError:
    WeatherFormatters = None

try:
    from commands.weather_modules.handler import WeatherCommandHandler
except ImportError:
    WeatherCommandHandler = None

try:
    from commands.weather_modules.display import WeatherDisplayManager
except ImportError:
    WeatherDisplayManager = None

try:
    from commands.weather_modules.stages import StageDisplayManager
except ImportError:
    StageDisplayManager = None

try:
    from commands.weather_modules.notifications import NotificationManager
except ImportError:
    NotificationManager = None

__all__ = [
    "WeatherCommandHandler",
    "WeatherDisplayManager",
    "StageDisplayManager",
    "NotificationManager",
    "WeatherFormatters",
]
