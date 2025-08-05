#!/usr/bin/env python3
"""
Simple GPIO and SPI test for Waveshare e-ink display
This bypasses any existing GPIO locks and tests basic functionality
"""

import sys
import time


def cleanup_gpio():
    """Force cleanup any existing GPIO usage"""
    try:
        import RPi.GPIO as GPIO

        GPIO.cleanup()
        print("✓ GPIO cleanup completed")
    except:
        pass


def test_basic_gpio():
    """Test basic GPIO functionality without external dependencies"""
    print("=== Basic GPIO Test ===")

    try:
        import RPi.GPIO as GPIO

        # Force cleanup first
        cleanup_gpio()
        time.sleep(0.5)

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        # Test pins for e-ink display
        pins = {"RST": 17, "DC": 25, "CS": 8, "BUSY": 24}

        print("Testing GPIO pins...")

        for name, pin in pins.items():
            try:
                if name == "BUSY":
                    # BUSY is an input from the display
                    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                    state = GPIO.input(pin)
                    print(f"✓ {name} (GPIO {pin}): {state} (input)")
                else:
                    # Control pins are outputs
                    GPIO.setup(pin, GPIO.OUT)

                    # Test high
                    GPIO.output(pin, GPIO.HIGH)
                    time.sleep(0.1)
                    state_high = GPIO.input(pin)

                    # Test low
                    GPIO.output(pin, GPIO.LOW)
                    time.sleep(0.1)
                    state_low = GPIO.input(pin)

                    print(f"✓ {name} (GPIO {pin}): HIGH={state_high}, LOW={state_low}")

            except Exception as e:
                print(f"✗ {name} (GPIO {pin}): {e}")

        return True

    except Exception as e:
        print(f"✗ GPIO test failed: {e}")
        return False
    finally:
        cleanup_gpio()


def test_spi():
    """Test SPI communication"""
    print("\n=== SPI Test ===")

    try:
        import spidev

        spi = spidev.SpiDev()
        spi.open(0, 0)  # Bus 0, Device 0
        spi.max_speed_hz = 4000000
        spi.mode = 0b00

        print(f"✓ SPI opened: Bus 0, Device 0")
        print(f"✓ Speed: {spi.max_speed_hz} Hz")
        print(f"✓ Mode: {spi.mode}")

        # Test write
        test_data = [0x12, 0x34, 0x56, 0x78]
        spi.writebytes(test_data)
        print(f"✓ SPI write test: {test_data}")

        spi.close()
        return True

    except Exception as e:
        print(f"✗ SPI test failed: {e}")
        return False


def test_display_reset_sequence():
    """Test the display reset sequence"""
    print("\n=== Display Reset Test ===")

    try:
        import RPi.GPIO as GPIO

        cleanup_gpio()
        time.sleep(0.5)

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        RST_PIN = 17
        BUSY_PIN = 24

        # Setup pins
        GPIO.setup(RST_PIN, GPIO.OUT)
        GPIO.setup(BUSY_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        print("Performing display reset sequence...")

        # Reset sequence
        GPIO.output(RST_PIN, GPIO.HIGH)
        time.sleep(0.2)
        print("RST HIGH")

        GPIO.output(RST_PIN, GPIO.LOW)
        time.sleep(0.005)
        print("RST LOW")

        GPIO.output(RST_PIN, GPIO.HIGH)
        time.sleep(0.2)
        print("RST HIGH again")

        # Check BUSY pin
        busy_state = GPIO.input(BUSY_PIN)
        print(f"BUSY pin state: {busy_state}")

        print("✓ Reset sequence completed")
        return True

    except Exception as e:
        print(f"✗ Reset test failed: {e}")
        return False
    finally:
        cleanup_gpio()


def check_system():
    """Check system requirements"""
    print("=== System Check ===")

    # Check imports
    modules = ["spidev", "RPi.GPIO", "gpiozero"]
    all_good = True

    for module in modules:
        try:
            __import__(module)
            print(f"✓ {module} available")
        except ImportError as e:
            print(f"✗ {module} missing: {e}")
            all_good = False

    # Check SPI devices
    try:
        import os

        spi_devs = [f for f in os.listdir("/dev/") if f.startswith("spi")]
        if spi_devs:
            print(f"✓ SPI devices: {spi_devs}")
        else:
            print("✗ No SPI devices found")
            all_good = False
    except Exception as e:
        print(f"✗ Error checking SPI: {e}")
        all_good = False

    return all_good


def main():
    print("Waveshare E-ink Display GPIO/SPI Test")
    print("=" * 45)

    tests = [
        ("System Check", check_system),
        ("Basic GPIO Test", test_basic_gpio),
        ("SPI Test", test_spi),
        ("Display Reset Test", test_display_reset_sequence),
    ]

    for test_name, test_func in tests:
        print(f"\n{test_name}...")
        try:
            result = test_func()
            if result:
                print(f"✓ {test_name} PASSED")
            else:
                print(f"✗ {test_name} FAILED")
                break
        except Exception as e:
            print(f"✗ {test_name} CRASHED: {e}")
            break

    print("\n" + "=" * 45)
    print("Test completed!")
    print("\nNext steps if tests pass:")
    print("1. Check physical wiring connections")
    print("2. Verify display power (3.3V)")
    print("3. Try the full display initialization")


if __name__ == "__main__":
    main()
