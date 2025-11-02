#!/usr/bin/env python3
"""Start the bot with bytecode disabled to avoid cache issues."""

import sys
import os

# Disable bytecode generation
sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

# Clear existing cache before starting
print("Clearing Python cache...")
import subprocess

subprocess.run(["find", ".", "-type", "f", "-name", "*.pyc", "-delete"], stderr=subprocess.DEVNULL)
subprocess.run(
    ["find", ".", "-type", "d", "-name", "__pycache__", "-exec", "rm", "-rf", "{}", "+"], stderr=subprocess.DEVNULL
)
print("✅ Cache cleared")

print("Starting bot without bytecode...")
# Import and run main
import main
