"""
Controls module for LoFi Pi (Raspberry Pi Zero)
Handles mechanical switches and rotary encoder input using RPi.GPIO
"""

import time
import threading
import RPi.GPIO as GPIOGPIO as GPIO


class Controls:
    def __init__(self, button_callback, rotary_callback):
        self.button_callback = button_callback
        self.rotary_callback = rotary_callback

        # GPIO pin assignments (BCM numbering)
        self.PLAY_PAUSE_PIN = 2
        self.NEXT_PIN = 3
        self.PREV_PIN = 4
        self.MENU_PIN = 14

        # Rotary encoder pins
        self.ROTARY_CLK_PIN = 5
        self.ROTARY_DT_PIN = 6
        self.ROTARY_SW_PIN = 13

        # Initialize GPIO
        self._init_gpio()

        # Button debouncing
        self.button_states = {
            "play_pause": True,
            "next": True,
            "prev": True,
            "menu": True,
            "rotary_sw": True,
        }

        self.last_button_time = {
            "play_pause": 0,
            "next": 0,
            "prev": 0,
            "menu": 0,
            "rotary_sw": 0,
        }

        # Rotary encoder state
        self.last_clk_state = GPIO.input(self.ROTARY_CLK_PIN)
        self.rotary_position = 0

        # Debounce time in seconds
        self.debounce_time = 0.2

        # Setup event detection
        self._setup_event_detection()

        print("Controls initialized with interrupt-based detection")

    def _init_gpio(self):
        """Initialize GPIO with proper cleanup and error handling"""
        try:
            # Clean up any existing GPIO setup
            GPIO.cleanup()
        except:
            pass

        # Set GPIO mode and disable warnings
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        # Setup button pins with pull-up resistors
        GPIO.setup(self.PLAY_PAUSE_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.NEXT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.PREV_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.MENU_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # Setup rotary encoder pins
        GPIO.setup(self.ROTARY_CLK_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.ROTARY_DT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.ROTARY_SW_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def _setup_event_detection(self):
        """Setup GPIO event detection with error handling"""
        pins_and_callbacks = [
            (self.PLAY_PAUSE_PIN, "play_pause"),
            (self.NEXT_PIN, "next"),
            (self.PREV_PIN, "prev"),
            (self.MENU_PIN, "menu"),
            (self.ROTARY_SW_PIN, "rotary_sw"),
        ]

        # Add event detection for buttons
        for pin, button_name in pins_and_callbacks:
            try:
                GPIO.add_event_detect(
                    pin,
                    GPIO.FALLING,
                    callback=lambda channel, name=button_name: self._button_interrupt(
                        name
                    ),
                    bouncetime=200,
                )
                print(f"Event detection added for {button_name} (pin {pin})")
            except Exception as e:
                print(
                    f"Failed to add event detection for {button_name} (pin {pin}): {e}"
                )
                # Continue with other pins

        # Add interrupt for rotary encoder
        try:
            GPIO.add_event_detect(
                self.ROTARY_CLK_PIN,
                GPIO.BOTH,
                callback=self._rotary_interrupt,
                bouncetime=5,
            )
            print(
                f"Event detection added for rotary encoder (pin {self.ROTARY_CLK_PIN})"
            )
        except Exception as e:
            print(f"Failed to add event detection for rotary encoder: {e}")

    def _button_interrupt(self, button_name):
        """Handle button press interrupts"""
        current_time = time.time()

        # Additional debouncing check
        if current_time - self.last_button_time[button_name] > self.debounce_time:
            self.last_button_time[button_name] = current_time

            print(f"Button pressed: {button_name}")

            # Map rotary switch to menu button
            if button_name == "rotary_sw":
                button_name = "menu"

            # Call the callback function in a separate thread to avoid blocking
            if self.button_callback:
                try:
                    threading.Thread(
                        target=self.button_callback, args=(button_name,), daemon=True
                    ).start()
                except Exception as e:
                    print(f"Error in button callback: {e}")

    def _rotary_interrupt(self, channel):
        """Handle rotary encoder interrupts"""
        try:
            current_clk_state = GPIO.input(self.ROTARY_CLK_PIN)

            # Check if CLK pin state changed
            if current_clk_state != self.last_clk_state:
                # Determine direction based on DT pin state
                if GPIO.input(self.ROTARY_DT_PIN) != current_clk_state:
                    # Clockwise rotation
                    direction = 1
                    self.rotary_position += 1
                else:
                    # Counter-clockwise rotation
                    direction = -1
                    self.rotary_position -= 1

                print(f"Rotary encoder: {direction}, Position: {self.rotary_position}")

                # Call the callback function in a separate thread
                if self.rotary_callback:
                    try:
                        threading.Thread(
                            target=self.rotary_callback, args=(direction,), daemon=True
                        ).start()
                    except Exception as e:
                        print(f"Error in rotary callback: {e}")

            self.last_clk_state = current_clk_state
        except Exception as e:
            print(f"Error in rotary interrupt: {e}")

    def update(self):
        """Update method for compatibility - interrupts handle everything now"""
        # This method is kept for compatibility but interrupts handle all input
        pass

    def get_rotary_position(self):
        """Get current rotary encoder position"""
        return self.rotary_position

    def reset_rotary_position(self):
        """Reset rotary encoder position to 0"""
        self.rotary_position = 0

    def cleanup(self):
        """Clean up GPIO"""
        try:
            GPIO.cleanup()
        except:
            pass
