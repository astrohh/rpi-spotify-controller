#!/usr/bin/env python3
"""
Simple test script for Waveshare 2.13" e-ink display
This will help debug display issues
"""

import sys
import time
import RPi.GPIO as GPIO
from eink_display import EInkDisplay


def main():
    print('Testing Waveshare 2.13" e-ink display...')

    try:
        # Initialize display
        display = EInkDisplay()

        print("Display initialized, testing basic functionality...")

        # Test 1: Show a simple message
        print("Test 1: Showing test message...")
        display.show_message("Test Display", 'Waveshare 2.13" Working!')
        time.sleep(3)

        # Test 2: Show track info simulation
        print("Test 2: Showing simulated track info...")
        test_track = {
            "name": "Test Song",
            "artist": "Test Artist",
            "album": "Test Album",
            "duration": 180000,  # 3 minutes
            "progress": 60000,  # 1 minute
            "image_url": None,
        }
        display.show_track(test_track)
        time.sleep(3)

        # Test 3: Show volume
        print("Test 3: Showing volume display...")
        display.show_volume(75)
        time.sleep(3)

        print("All tests completed successfully!")

    except Exception as e:
        print(f"Display test failed: {e}")
        import traceback

        traceback.print_exc()

    finally:
        try:
            display.cleanup()
        except:
            pass
        GPIO.cleanup()


if __name__ == "__main__":
    main()
