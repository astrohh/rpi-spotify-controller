#!/usr/bin/env python3
"""
Test the new e-ink display integration
"""

import os
import sys
import time

# Add current directory to Python path so we can import our modules
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from eink_display import EInkDisplay


def test_display():
    """Test the new display wrapper"""
    print("Testing E-ink Display Integration...")

    try:
        # Initialize display
        display = EInkDisplay()

        print("1. Initializing display...")
        if not display.initialize():
            print("❌ Failed to initialize display")
            return False
        print("✅ Display initialized")

        print("2. Clearing display...")
        display.clear()
        time.sleep(2)
        print("✅ Display cleared")

        print("3. Testing message display...")
        display.show_message("LoFi Pi", "Display test successful!")
        time.sleep(3)
        print("✅ Message displayed")

        print("4. Testing track display...")
        test_track = {
            "name": "Test Song Title",
            "artist": "Test Artist Name",
            "album": "Test Album Name",
            "duration": 180000,  # 3 minutes in milliseconds
            "progress": 60000,  # 1 minute in milliseconds
        }
        display.show_track(test_track)
        time.sleep(3)
        print("✅ Track info displayed")

        print("5. Testing volume display...")
        display.show_volume(75)
        time.sleep(3)
        print("✅ Volume displayed")

        print("6. Putting display to sleep...")
        display.sleep()
        print("✅ Display sleeping")

        print("\n🎉 All display tests passed!")
        return True

    except Exception as e:
        print(f"❌ Display test failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        try:
            display.cleanup()
        except:
            pass


if __name__ == "__main__":
    test_display()
