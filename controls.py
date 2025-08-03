"""
Controls module for LoFi Pi (Raspberry Pi Zero)
Handles mechanical switches and rotary encoder input using RPi.GPIO
"""

import time
import threading
import RPi.GPIO as GPIO


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

        # Add event detection for buttons (interrupt-based)
        GPIO.add_event_detect(
            self.PLAY_PAUSE_PIN,
            GPIO.FALLING,
            callback=lambda channel: self._button_interrupt("play_pause"),
            bouncetime=200,
        )
        GPIO.add_event_detect(
            self.NEXT_PIN,
            GPIO.FALLING,
            callback=lambda channel: self._button_interrupt("next"),
            bouncetime=200,
        )
        GPIO.add_event_detect(
            self.PREV_PIN,
            GPIO.FALLING,
            callback=lambda channel: self._button_interrupt("prev"),
            bouncetime=200,
        )
        GPIO.add_event_detect(
            self.MENU_PIN,
            GPIO.FALLING,
            callback=lambda channel: self._button_interrupt("menu"),
            bouncetime=200,
        )
        GPIO.add_event_detect(
            self.ROTARY_SW_PIN,
            GPIO.FALLING,
            callback=lambda channel: self._button_interrupt("rotary_sw"),
            bouncetime=200,
        )

        # Add interrupt for rotary encoder
        GPIO.add_event_detect(
            self.ROTARY_CLK_PIN,
            GPIO.BOTH,
            callback=self._rotary_interrupt,
            bouncetime=5,
        )

        print("Controls initialized with interrupt-based detection")

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
                threading.Thread(
                    target=self.button_callback, args=(button_name,), daemon=True
                ).start()

    def _rotary_interrupt(self, channel):
        """Handle rotary encoder interrupts"""
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
                threading.Thread(
                    target=self.rotary_callback, args=(direction,), daemon=True
                ).start()

        self.last_clk_state = current_clk_state

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
