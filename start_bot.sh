#!/bin/bash

# Stop any running bot instances
echo "🛑 Stopping any running bot instances..."
pkill -9 -f "python.*main.py" 2>/dev/null || true
sleep 1

# Clear ALL Python cache aggressively
echo "🧹 Clearing Python cache..."
find . -type f -name "*.pyc" -delete 2>/dev/null
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null

# Verify the critical line is correct
echo "✅ Verifying fix..."
if grep -q '"temp_modifier": actual_temp - base_temp' commands/weather_modules/services/daily_weather_service.py; then
    echo "✅ Line 266 is correct (on one line)"
else
    echo "❌ ERROR: Line 266 is still split!"
    exit 1
fi

# Start the bot with bytecode disabled
echo "🚀 Starting bot (bytecode disabled)..."
export PYTHONDONTWRITEBYTECODE=1
export PYTHONIOENCODING=utf-8
python -B main.py
