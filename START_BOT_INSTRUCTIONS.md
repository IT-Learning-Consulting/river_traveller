# 🚨 CRITICAL: How to Start the Bot Correctly

## THE PROBLEM

Your bot is loading **OLD CACHED BYTECODE** (`.pyc` files) that contains the BROKEN version of the code. Even though the source code is fixed, Python is executing the cached version.

## THE SOLUTION

**Use the special startup script that clears cache first:**

```bash
cd /e/foundry_development/bots/travelling-bot
./start_bot.sh
```

**OR manually run these commands:**

```bash
# 1. Kill any running bot
pkill -9 -f "python.*main.py"

# 2. Clear ALL cache
find . -type f -name "*.pyc" -delete
find . -type d -name "__pycache__" -exec rm -rf {} +

# 3. Start bot with bytecode DISABLED
export PYTHONDONTWRITEBYTECODE=1
python -B main.py
```

## WHY THIS IS NECESSARY

1. ✅ The source code IS correct (line 266 is on ONE line)
2. ✅ The code compiles successfully  
3. ✅ The debug script works perfectly
4. ❌ But `main.py` loads cached `.pyc` files from BEFORE the fix

The `-B` flag tells Python to **NOT use bytecode cache** and **NOT create new cache files**, forcing it to read the source code directly.

## VERIFY THE FIX

Before starting, verify line 266 is correct:
```bash
sed -n '266p' commands/weather_modules/services/daily_weather_service.py
```

Should show:
```python
            "temp_modifier": actual_temp - base_temp,  # Total deviation from seasonal base
```

## IMPORTANT

- **DO NOT** run `python main.py` directly anymore
- **ALWAYS** use `./start_bot.sh` or the manual commands above
- **DO NOT** save `daily_weather_service.py` while the formatter is active (it will break it again)

The `# fmt: off` comments protect the code from the formatter, but you need to start fresh with cleared cache!
