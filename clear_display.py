#!/usr/bin/env python3
"""
Clear E-ink Display Script
Simple utility to clear the LoFi Pi e-ink display to solid white
This prevents image burn-in during storage
"""

import sys
from PIL import Image
import RPi.GPIO as GPIO
from eink_display import EInkDisplay


def clear_display():
    """Clear the e-ink display to blank/white"""
    print("Clearing e-ink display to white...")

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

        # Initialize the display hardware
        if not display.initialize():
            print("Failed to initialize display hardware")
            return False

        # Check if EPD is properly initialized
        if not display.epd:
            print("EPD hardware not properly initialized")
            return False

        # Create completely white images for both black and red layers
        # E-ink displays use 1-bit images where 255 = white, 0 = black
        # Display dimensions: 250x122 (height x width)
        white_image_black = Image.new(
            "1", (display.height, display.width), 255
        )  # Solid white
        white_image_red = Image.new(
            "1", (display.height, display.width), 255
        )  # Solid white

        print("Created white images for display layers")

        # Display the white images to clear any burn-in
        display.epd.init()
        display.epd.display(
            display.epd.getbuffer(white_image_black),
            display.epd.getbuffer(white_image_red),
        )

        print("Display set to solid white - safe for storage!")

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
