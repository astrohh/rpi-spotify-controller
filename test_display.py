#!/usr/bin/env python3
"""
Simple test script for Waveshare 2.13" e-ink display
This will help debug display issues
"""

import sys
import time
from eink_display import EPD
from PIL import Image, ImageDraw, ImageFont


def main():
    print('Testing Waveshare 2.13" e-ink display...')

    epd = EPD()

    try:
        print("Initializing display...")
        epd.init(epd.FULL_UPDATE)

        # Clear the display first
        print("Clearing display...")
        epd.Clear(0xFF)  # Clear to white
        time.sleep(2)

        # Test 1: Show a simple message
        print("Test 1: Showing test message...")
        image = Image.new("1", (epd.width, epd.height), 255)  # 255: clear the frame
        draw = ImageDraw.Draw(image)

        # Try to load a font, fall back to default if not available
        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16
            )
            font_small = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12
            )
        except:
            font = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # Draw text
        draw.text((10, 10), "Test Display", font=font, fill=0)
        draw.text((10, 30), 'Waveshare 2.13"', font=font_small, fill=0)
        draw.text((10, 50), "Working!", font=font_small, fill=0)

        # Convert and display
        buffer = epd.getbuffer(image)
        epd.display(buffer)
        time.sleep(3)

        # Test 2: Show track info simulation
        print("Test 2: Showing simulated track info...")
        image = Image.new("1", (epd.width, epd.height), 255)
        draw = ImageDraw.Draw(image)

        # Simulate track display
        draw.text((5, 5), "Now Playing:", font=font_small, fill=0)
        draw.text((5, 25), "Test Song", font=font, fill=0)
        draw.text((5, 45), "by Test Artist", font=font_small, fill=0)
        draw.text((5, 65), "Test Album", font=font_small, fill=0)

        # Draw a simple progress bar
        progress_width = int((epd.width - 20) * (60000 / 180000))  # 1/3 progress
        draw.rectangle([10, 90, 10 + progress_width, 95], fill=0)
        draw.rectangle([10 + progress_width, 90, epd.width - 10, 95], outline=0)

        # Time display
        draw.text((10, 100), "1:00 / 3:00", font=font_small, fill=0)

        buffer = epd.getbuffer(image)
        epd.display(buffer)
        time.sleep(3)

        # Test 3: Show volume
        print("Test 3: Showing volume display...")
        image = Image.new("1", (epd.width, epd.height), 255)
        draw = ImageDraw.Draw(image)

        # Volume display
        draw.text((10, 20), "Volume", font=font, fill=0)

        # Draw volume bar
        volume_level = 75
        bar_width = epd.width - 40
        filled_width = int(bar_width * (volume_level / 100))

        # Volume bar background
        draw.rectangle([20, 50, 20 + bar_width, 70], outline=0)
        # Volume bar fill
        draw.rectangle([20, 50, 20 + filled_width, 70], fill=0)

        # Volume percentage
        draw.text((10, 80), f"{volume_level}%", font=font, fill=0)

        buffer = epd.getbuffer(image)
        epd.display(buffer)
        time.sleep(3)

        print("All tests completed successfully!")

    except Exception as e:
        print(f"Display test failed: {e}")
        import traceback

        traceback.print_exc()

    finally:
        try:
            print("Putting display to sleep...")
            epd.sleep()
        except Exception as e:
            print(f"Error during cleanup: {e}")


if __name__ == "__main__":
    main()
