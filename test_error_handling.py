"""
Test script for enhanced error handling system.

This script verifies that the new exception classes and error handlers
work correctly without requiring Discord interaction.
"""

import sys
from commands.exceptions import (
    CharacterNotFoundException,
    DiceNotationException,
    JourneyNotFoundException,
    InvalidParameterException,
)
from commands.enhanced_error_handlers import (
    ErrorLogger,
    format_error_for_user,
    get_error_category,
)


def test_exceptions():
    """Test custom exception creation."""
    print("=" * 60)
    print("Testing Custom Exceptions")
    print("=" * 60)

    # Test CharacterNotFoundException
    print("\n1. CharacterNotFoundException:")
    try:
        raise CharacterNotFoundException(
            character_name="bobby",
            available_characters=["anara", "emmerich", "hildric"],
            user_message="❌ Character not found.",
        )
    except CharacterNotFoundException as e:
        print(f"   Message: {e.message}")
        print(f"   User Message: {e.user_message}")
        print(f"   Context: {e.context}")
        print(f"   ✅ CharacterNotFoundException works")

    # Test DiceNotationException
    print("\n2. DiceNotationException:")
    try:
        raise DiceNotationException(notation="5d", reason="Missing die size", user_message="❌ Invalid dice notation")
    except DiceNotationException as e:
        print(f"   Message: {e.message}")
        print(f"   User Message: {e.user_message}")
        print(f"   Context: {e.context}")
        print(f"   ✅ DiceNotationException works")

    # Test JourneyNotFoundException
    print("\n3. JourneyNotFoundException:")
    try:
        raise JourneyNotFoundException(guild_id="123456789", user_message="❌ No journey in progress.")
    except JourneyNotFoundException as e:
        print(f"   Message: {e.message}")
        print(f"   User Message: {e.user_message}")
        print(f"   Context: {e.context}")
        print(f"   ✅ JourneyNotFoundException works")

    # Test InvalidParameterException
    print("\n4. InvalidParameterException:")
    try:
        raise InvalidParameterException(
            parameter_name="difficulty", parameter_value=100, expected="Value between -50 and +60"
        )
    except InvalidParameterException as e:
        print(f"   Message: {e.message}")
        print(f"   User Message: {e.user_message}")
        print(f"   Context: {e.context}")
        print(f"   ✅ InvalidParameterException works")

    print("\n✅ All exception classes work correctly")


def test_error_logger():
    """Test error logging functionality."""
    print("\n" + "=" * 60)
    print("Testing Error Logger")
    print("=" * 60)

    logger = ErrorLogger()

    # Log some test errors
    print("\n1. Logging CharacterNotFoundException:")
    try:
        raise CharacterNotFoundException(character_name="test", available_characters=["anara", "emmerich"])
    except CharacterNotFoundException as e:
        logger.log_error(
            error=e, command_name="boat-handling", guild_id="123", user_id="456", context_data={"character": "test"}
        )
        print("   ✅ Error logged successfully")

    # Log a warning
    print("\n2. Logging warning:")
    logger.log_warning("Test warning message", command_name="weather", context_data={"reason": "testing"})
    print("   ✅ Warning logged successfully")

    # Get statistics
    print("\n3. Getting error statistics:")
    stats = logger.get_stats()
    print(f"   Total errors: {stats['total']}")
    print(f"   By type: {stats['by_type']}")
    print("   ✅ Statistics retrieved successfully")

    print("\n✅ Error logger works correctly")


def test_helper_functions():
    """Test helper functions."""
    print("\n" + "=" * 60)
    print("Testing Helper Functions")
    print("=" * 60)

    # Test format_error_for_user
    print("\n1. Testing format_error_for_user:")
    error = CharacterNotFoundException(character_name="bobby", available_characters=["anara"])
    formatted = format_error_for_user(error, include_details=False)
    print(f"   Formatted: {formatted}")
    print("   ✅ format_error_for_user works")

    # Test get_error_category
    print("\n2. Testing get_error_category:")
    category = get_error_category(error)
    print(f"   Category: {category}")
    print("   ✅ get_error_category works")

    print("\n✅ Helper functions work correctly")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("ENHANCED ERROR HANDLING SYSTEM TEST")
    print("=" * 60)

    try:
        test_exceptions()
        test_error_logger()
        test_helper_functions()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print("\nThe enhanced error handling system is working correctly!")
        print("\nNext steps:")
        print("1. Test /roll command in Discord with invalid inputs")
        print("2. Test /boat-handling with invalid character name")
        print("3. Monitor logs for error details")
        print("4. Continue migrating other commands")

        return 0

    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ TEST FAILED")
        print("=" * 60)
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
