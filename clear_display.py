#!/usr/bin/env python3
"""
Clear E-ink Display Script
Simple utility to clear the LoFi Pi e-ink display
"""

import sys
import RPi.GPIO as GPIO
from eink_display import EInkDisplayplay import EInkDisplay


def clear_display():
    """Clear the e-ink display to blank/white"""
    print("Clearing e-ink display...")

    display = None
    try:
        # Initialize GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        gpio_initialized = True
        print("GPIO initialized")

        # Initialize display
        display = EInkDisplay(gpio_initialized=gpio_initialized)
        print("E-ink display initialized")

        # Clear the display
        display.clear()
        print("Display cleared successfully!")

    except Exception as e:
        print(f"Error clearing display: {e}")
        return False

    finally:
        # Clean up GPIO
        try:
            if display:
                display.cleanup()
            GPIO.cleanup()
            print("GPIO cleaned up")
        except:
            pass

    return True


if __name__ == "__main__":
    print("LoFi Pi Display Cleaner")
    print("=" * 30)

    if clear_display():
        print("Display cleared successfully!")
        sys.exit(0)
    else:
        print("Failed to clear display!")
        sys.exit(1)
