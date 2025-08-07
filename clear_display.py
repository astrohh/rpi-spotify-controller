#!/usr/bin/env python3
"""
Clear E-ink Display - Prevents burn-in during storage
"""

import sys
from PIL import Image
import RPi.GPIO as GPIO
from eink_display import EInkDisplay


def clear_display():
    """Clear the e-ink display to blank/white"""
    print("Clearing display...")

    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        display = EInkDisplay(gpio_initialized=True)
        if not display.initialize() or not display.epd:
            print("Display initialization failed")
            return False

        # Create white images (255 = white for 1-bit images)
        white_black = Image.new("1", (display.height, display.width), 255)
        white_red = Image.new("1", (display.height, display.width), 255)

        display.epd.init()
        display.epd.display(
            display.epd.getbuffer(white_black), display.epd.getbuffer(white_red)
        )
        print("Display cleared!")
        return True

    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        try:
            GPIO.cleanup()
        except:
            pass

    return True


if __name__ == "__main__":
    if clear_display():
        print("Success!")
        sys.exit(0)
    else:
        print("Failed!")
        sys.exit(1)
