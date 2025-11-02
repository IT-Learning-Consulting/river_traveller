#!/usr/bin/env python3
"""Debug script to trace the base_temp error with full traceback."""

import sys
import traceback

# Add project to path
sys.path.insert(0, "e:/foundry_development/bots/travelling-bot")

print("=" * 60)
print("DEBUGGING base_temp ERROR")
print("=" * 60)

try:
    print("\n1. Importing modules...")
    from db.weather_storage import WeatherStorage
    from commands.weather_modules.services.daily_weather_service import (
        DailyWeatherService,
    )

    print("   ✅ Imports successful")

    print("\n2. Creating storage and service...")
    storage = WeatherStorage()
    service = DailyWeatherService(storage)
    print("   ✅ Service created")

    print("\n3. Creating mock journey state...")
    # Create a simple dict-based journey for testing
    journey = {
        "guild_id": "test_guild_123",
        "current_day": 1,
        "season": "summer",
        "province": "reikland",
        "current_stage": 1,
        "stage_duration": 3,
        "stage_display_mode": "simple",
        "days_since_last_cold_front": 99,
        "days_since_last_heat_wave": 99,
        "last_weather_date": None,
    }
    print("   ✅ Journey created")

    print("\n4. Generating weather...")
    weather_data = service.generate_daily_weather("test_guild_123", journey)
    print("   ✅ Weather generated successfully!")

    print("\n5. Checking weather_data contents:")
    print(f"   - Keys in weather_data: {list(weather_data.keys())}")
    print(f"   - base_temp present: {'base_temp' in weather_data}")
    if "base_temp" in weather_data:
        print(f"   - base_temp value: {weather_data['base_temp']}")
    else:
        print("   ❌ base_temp is MISSING from weather_data!")

    print("\n6. Testing notification service...")
    from commands.weather_modules.services.notification_service import (
        NotificationService,
    )

    embed = NotificationService._create_notification_embed(weather_data)
    print("   ✅ Notification embed created successfully!")

    print("\n" + "=" * 60)
    print("✅ SUCCESS - No errors found!")
    print("=" * 60)

except NameError as e:
    print(f"\n❌ NameError caught: {e}")
    print("\nFull traceback:")
    print("-" * 60)
    traceback.print_exc()
    print("-" * 60)
    sys.exit(1)

except Exception as e:
    print(f"\n❌ Other error: {type(e).__name__}: {e}")
    print("\nFull traceback:")
    print("-" * 60)
    traceback.print_exc()
    print("-" * 60)
    sys.exit(1)
