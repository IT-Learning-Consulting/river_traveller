"""Test full weather generation flow to reproduce the unpacking error."""

import sys

sys.path.insert(0, ".")

print("1. Importing modules...")
from db.weather_storage import WeatherStorage
from commands.weather_modules.services.daily_weather_service import DailyWeatherService
from db.repositories.journey_repository import JourneyRepository

print("2. Creating storage and service...")
storage = WeatherStorage("data/weather_state.db")
service = DailyWeatherService(storage)

print("3. Creating mock journey...")
journey_repo = JourneyRepository("data/weather_state.db")
guild_id = "test_guild_full"

# Create journey
from db.models.weather_models import JourneyState

journey = JourneyState(guild_id=guild_id, current_day=0, season="summer", province="reikland")
try:
    journey_repo.save_journey(journey)
except Exception:
    # Journey might already exist
    pass

print("4. Generating first day weather...")
try:
    weather_data = service.generate_daily_weather(guild_id)
    print(f"✅ Weather generated successfully!")
    print(f"   Day: {weather_data.get('day')}")
    print(f"   Temperature: {weather_data.get('actual_temp')}°C")
    print(f"   Base temp present: {'base_temp' in weather_data}")
    if "base_temp" in weather_data:
        print(f"   Base temp value: {weather_data['base_temp']}")
    print(f"   Weather type: {weather_data.get('weather_type')}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

print("\n5. Testing notification embed...")
try:
    from commands.weather_modules.services.notification_service import NotificationService

    embed = NotificationService._create_notification_embed(weather_data)
    print(f"✅ Notification embed created successfully!")
    print(f"   Title: {embed.title}")
    print(f"   Fields: {len(embed.fields)}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

print("\n6. Testing display embed...")
try:
    from commands.weather_modules.services.display_service import DisplayService

    # DisplayService methods are static and don't need instantiation
    # But we need to check if the formatting works
    temp_text = DisplayService._format_temperature(
        weather_data["actual_temp"],
        weather_data.get("perceived_temp", weather_data["actual_temp"]),
        weather_data.get("temp_category", ""),
    )
    print(f"✅ Display formatting successful!")
    print(f"   Temperature text: {temp_text[:50]}...")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

print("\n✅ All tests passed!")
