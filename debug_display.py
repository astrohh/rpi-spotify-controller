#!/usr/bin/env python3
"""
Debug script for Waveshare 2.13" e-ink display
Run this to diagnose display issues
"""

import sys
import time
import traceback


def check_system():
    """Check basic system requirements"""
    print("=== System Check ===")

    # Check imports
    try:
        import spidev

        print("✓ spidev import OK")
    except ImportError as e:
        print(f"✗ spidev import failed: {e}")
        return False

    try:
        import gpiozero

        print("✓ gpiozero import OK")
    except ImportError as e:
        print(f"✗ gpiozero import failed: {e}")
        return False

    try:
        import RPi.GPIO as GPIO

        print("✓ RPi.GPIO import OK")
    except ImportError as e:
        print(f"✗ RPi.GPIO import failed: {e}")
        return False

    # Check SPI devices
    try:
        import os

        spi_devices = os.listdir("/dev/")
        spi_devices = [d for d in spi_devices if d.startswith("spi")]
        if spi_devices:
            print(f"✓ SPI devices found: {spi_devices}")
        else:
            print("✗ No SPI devices found - enable SPI in raspi-config")
            return False
    except Exception as e:
        print(f"✗ Error checking SPI devices: {e}")
        return False

    return True


def test_gpio_pins():
    """Test GPIO pin configuration"""
    print("\n=== GPIO Pin Test ===")

    import RPi.GPIO as GPIO

    # Pin definitions (BCM numbering)
    pins = {"RST": 17, "DC": 25, "CS": 8, "BUSY": 24}

    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        for name, pin in pins.items():
            try:
                if name == "BUSY":
                    GPIO.setup(pin, GPIO.IN)
                    state = GPIO.input(pin)
                    print(f"✓ {name} (GPIO {pin}): INPUT = {state}")
                else:
                    GPIO.setup(pin, GPIO.OUT)
                    GPIO.output(pin, 1)
                    state = GPIO.input(pin)
                    print(f"✓ {name} (GPIO {pin}): OUTPUT = {state}")
                    GPIO.output(pin, 0)
            except Exception as e:
                print(f"✗ {name} (GPIO {pin}): Error = {e}")

        GPIO.cleanup()
        return True

    except Exception as e:
        print(f"✗ GPIO test failed: {e}")
        GPIO.cleanup()
        return False


def test_spi():
    """Test SPI communication"""
    print("\n=== SPI Test ===")

    try:
        import spidev

        spi = spidev.SpiDev()

        # Try to open SPI
        spi.open(0, 0)
        spi.max_speed_hz = 4000000
        spi.mode = 0b00

        print("✓ SPI device opened successfully")
        print(f"✓ SPI speed: {spi.max_speed_hz} Hz")
        print(f"✓ SPI mode: {spi.mode}")

        # Test a simple write
        test_data = [0x00, 0xFF, 0xAA, 0x55]
        spi.writebytes(test_data)
        print(f"✓ SPI write test successful: {test_data}")

        spi.close()
        return True

    except Exception as e:
        print(f"✗ SPI test failed: {e}")
        return False


def test_display_init():
    """Test display initialization"""
    print("\n=== Display Initialization Test ===")

    try:
        # Import our config
        import eink_config as epdconfig

        print("✓ eink_config imported")

        # Try to initialize
        result = epdconfig.module_init()
        if result == 0:
            print("✓ Display module initialized")
        else:
            print(f"✗ Display module init failed: {result}")
            return False

        # Test basic pin operations
        print("Testing pin operations...")

        # Reset sequence
        epdconfig.digital_write(epdconfig.RST_PIN, 1)
        time.sleep(0.2)
        epdconfig.digital_write(epdconfig.RST_PIN, 0)
        time.sleep(0.005)
        epdconfig.digital_write(epdconfig.RST_PIN, 1)
        time.sleep(0.2)
        print("✓ Reset sequence completed")

        # Check busy pin
        busy_state = epdconfig.digital_read(epdconfig.BUSY_PIN)
        print(f"✓ BUSY pin state: {busy_state}")

        # Test DC pin
        epdconfig.digital_write(epdconfig.DC_PIN, 1)
        dc_state = epdconfig.digital_read(epdconfig.DC_PIN)
        print(f"✓ DC pin test: {dc_state}")

        epdconfig.module_exit()
        print("✓ Display module cleanup completed")

        return True

    except Exception as e:
        print(f"✗ Display test failed: {e}")
        traceback.print_exc()
        return False


def test_full_display():
    """Test full display functionality"""
    print("\n=== Full Display Test ===")

    try:
        from eink_display import EPD
        from PIL import Image, ImageDraw, ImageFont

        print("✓ Display modules imported")

        epd = EPD()
        print("✓ EPD object created")

        # Initialize display
        epd.init(epd.FULL_UPDATE)
        print("✓ Display initialized")

        # Clear display
        epd.Clear(0xFF)
        print("✓ Display cleared")

        # Create test image
        image = Image.new("1", (epd.width, epd.height), 255)
        draw = ImageDraw.Draw(image)

        # Draw test pattern
        draw.text((10, 10), "Display Test", fill=0)
        draw.text((10, 30), "Working!", fill=0)
        draw.rectangle([10, 50, 100, 80], outline=0)

        # Display image
        buffer = epd.getbuffer(image)
        epd.display(buffer)
        print("✓ Test image displayed")

        time.sleep(3)

        # Put display to sleep
        epd.sleep()
        print("✓ Display put to sleep")

        return True

    except Exception as e:
        print(f"✗ Full display test failed: {e}")
        traceback.print_exc()
        return False


def main():
    print('Waveshare 2.13" E-ink Display Debug Tool')
    print("=" * 50)

    tests = [
        ("System Check", check_system),
        ("GPIO Pin Test", test_gpio_pins),
        ("SPI Test", test_spi),
        ("Display Init Test", test_display_init),
        ("Full Display Test", test_full_display),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))

            if not result:
                print(f"\n❌ {test_name} FAILED - stopping here")
                break

        except Exception as e:
            print(f"\n❌ {test_name} CRASHED: {e}")
            results.append((test_name, False))
            break

    print("\n" + "=" * 50)
    print("SUMMARY:")
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} {test_name}")

    print("\nIf tests fail, check:")
    print("1. SPI is enabled: sudo raspi-config -> Interface Options -> SPI")
    print("2. Wiring connections match the pin definitions")
    print("3. Display is powered (if using HAT, it gets power from Pi)")
    print("4. Required Python packages are installed")


if __name__ == "__main__":
    main()
