#!/usr/bin/env python3
"""
Simple test to verify the lib modules work correctly
"""

import os
import sys
import time

# Add lib directory to path
lib_dir = os.path.join(os.path.dirname(__file__), "lib")
sys.path.insert(0, lib_dir)


def test_lib_import():
    """Test importing lib modules directly"""
    print("Testing lib module imports...")

    try:
        import epdconfig

        print("✅ epdconfig imported successfully")

        import epd_2in13b

        print("✅ epd_2in13b imported successfully")

        from PIL import Image, ImageDraw, ImageFont

        print("✅ PIL modules imported successfully")

        return True

    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


def test_display_basic():
    """Test basic display functionality"""
    print("\nTesting basic display functionality...")

    try:
        import epdconfig
        import epd_2in13b
        from PIL import Image, ImageDraw

        # Initialize the config
        result = epdconfig.module_init()
        if result != 0:
            print(f"❌ Module init failed: {result}")
            return False
        print("✅ Module initialized")

        # Create EPD instance
        epd = epd_2in13b.EPD()
        print("✅ EPD instance created")

        # Initialize display
        epd.init()
        print("✅ Display initialized")

        # Clear display
        epd.clear()
        print("✅ Display cleared")
        time.sleep(2)

        # Create test image
        black_image = Image.new("1", (250, 122), 255)  # White background
        red_image = Image.new("1", (250, 122), 255)  # No red content

        draw = ImageDraw.Draw(black_image)
        draw.text((10, 10), "Hello LoFi Pi!", fill=0)
        draw.text((10, 30), "Display Working!", fill=0)
        draw.rectangle([10, 50, 100, 80], outline=0)

        # Display the image
        epd.display(epd.getbuffer(black_image), epd.getbuffer(red_image))
        print("✅ Test image displayed")
        time.sleep(3)

        # Put to sleep
        epd.sleep()
        print("✅ Display put to sleep")

        return True

    except Exception as e:
        print(f"❌ Display test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    print("Waveshare E-ink Display Library Test")
    print("=" * 40)

    # Test imports
    if not test_lib_import():
        print("\n❌ Import test failed - check your lib directory")
        return

    # Test display
    if not test_display_basic():
        print("\n❌ Display test failed")
        return

    print("\n🎉 All tests passed! Your display setup is working correctly.")
    print("\nYou can now proceed to test the full EInkDisplay wrapper.")


if __name__ == "__main__":
    main()
