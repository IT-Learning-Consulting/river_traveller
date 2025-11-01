"""
Weather command module - refactored for maintainability.

This module provides a clean separation of concerns for weather commands:
- handler: Business logic orchestration (delegates to service layer)
- services/: Service layer (JourneyService, DailyWeatherService, NotificationService, DisplayService)
- stages: Multi-day stage display (legacy, still in use)
- formatters: Pure utility functions for formatting

Legacy modules removed in Phase 2:
- display.py: Replaced by services/display_service.py
- notifications.py: Replaced by services/notification_service.py
"""

# Import available modules
try:
    from commands.weather_modules.formatters import WeatherFormatters
except ImportError:
    WeatherFormatters = None

try:
    from commands.weather_modules.handler import WeatherCommandHandler
except ImportError:
    WeatherCommandHandler = None

try:
    from commands.weather_modules.stages import StageDisplayManager
except ImportError:
    StageDisplayManager = None

__all__ = [
    "WeatherCommandHandler",
    "StageDisplayManager",
    "WeatherFormatters",
]
