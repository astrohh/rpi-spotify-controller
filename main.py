"""
LoFi Pi - Main application
Raspberry Pi Zero Spotify Controller
"""

import sys
import time
import json
import signal
import requests
import threading
import RPi.GPIO as GPIO
from pathlib import Path

from config import Config
from controls import Controls

# Import custom modules
from spotify_api import SpotifyAPI
from eink_display import EInkDisplay


class LoFiPi:
    def __init__(self):
        print("Initializing LoFi Pi...")

        # Load configuration
        self.config = Config()

        # Initialize GPIO once for the entire application
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            gpio_initialized = True
            print("GPIO initialized")
        except Exception as e:
            print(f"GPIO initialization failed: {e}")
            gpio_initialized = False

        # Initialize hardware components with shared GPIO
        self.display = EInkDisplay(gpio_initialized=gpio_initialized)
        print("E-ink display initialized")

        try:
            self.controls = Controls(
                self.on_button_press,
                self.on_rotary_change,
                gpio_initialized=gpio_initialized,
            )
            print("Controls initialized successfully")
        except Exception as e:
            print(f"Warning: Controls initialization failed: {e}")
            print("LoFi Pi will continue without physical controls")
            self.controls = None

        # Initialize Spotify API
        self.spotify = SpotifyAPI(
            client_id=self.config.SPOTIFY_CLIENT_ID,
            client_secret=self.config.SPOTIFY_CLIENT_SECRET,
            redirect_uri=self.config.SPOTIFY_REDIRECT_URI,
        )

        # Current state
        self.current_track = None
        self.is_playing = False
        self.volume = 50
        self.running = True

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        # Start background update thread
        self.update_thread = threading.Thread(target=self.update_loop, daemon=True)

        print("LoFi Pi initialized successfully!")

    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print("\nShutting down LoFi Pi...")
        self.running = False
        self.display.cleanup()
        GPIO.cleanup()
        sys.exit(0)

    def update_loop(self):
        """Main update loop - runs in background thread"""
        token_check_counter = 0
        token_check_interval = 120  # Check tokens every 2 minutes (120 * 5s = 600s)

        while self.running:
            try:
                # Periodic token health check
                if token_check_counter >= token_check_interval:
                    self._check_token_health()
                    token_check_counter = 0
                else:
                    token_check_counter += 1

                # Get current track info from Spotify
                current_playback = self.spotify.get_current_playback()

                if current_playback and current_playback.get("item"):
                    track = current_playback["item"]
                    new_track_id = track["id"]

                    # Check if track has changed
                    if (
                        not self.current_track
                        or self.current_track.get("id") != new_track_id
                    ):
                        self.current_track = {
                            "id": new_track_id,
                            "name": track["name"],
                            "artist": track["artists"][0]["name"],
                            "album": track["album"]["name"],
                            "image_url": (
                                track["album"]["images"][0]["url"]
                                if track["album"]["images"]
                                else None
                            ),
                            "duration": track["duration_ms"],
                            "progress": current_playback.get("progress_ms", 0),
                        }

                        print(
                            f"Now playing: {self.current_track['name']} by {self.current_track['artist']}"
                        )

                        # Update display with new track
                        self.display.show_track(self.current_track)

                    # Update playback state
                    self.is_playing = current_playback.get("is_playing", False)
                    device_volume = current_playback.get("device", {}).get(
                        "volume_percent"
                    )
                    if device_volume is not None:
                        self.volume = device_volume

                elif current_playback is None:
                    # No active playback
                    if self.current_track is not None:
                        self.current_track = None
                        self.display.show_message(
                            "No Music", "Start playing on Spotify"
                        )

            except Exception as e:
                print(f"Error in update loop: {e}")

                # Check if it's an authentication error
                if "401" in str(e) or "authentication" in str(e).lower():
                    print("Authentication error detected, attempting token refresh...")
                    if self.spotify.refresh_access_token():
                        print("Token refresh successful, continuing...")
                        self.display.show_message("Reconnected", "")
                    else:
                        print("Token refresh failed")
                        self.display.show_message("Auth Error", "Retrying...")
                else:
                    self.display.show_message("Error", "Check connection")

            # Wait before next update
            time.sleep(self.config.SPOTIFY_UPDATE_INTERVAL / 1000)

    def _check_token_health(self):
        """Periodically check token health and refresh if needed"""
        try:
            # Check if tokens are expiring soon
            token_file = Path("spotify_tokens.json")
            if token_file.exists():
                with open(token_file, "r") as f:
                    tokens = json.load(f)
                    expires_at = tokens.get("expires_at", 0)
                    current_time = time.time()
                    time_until_expiry = expires_at - current_time

                    # Refresh if expiring in next 10 minutes
                    if time_until_expiry <= 600 and time_until_expiry > 0:
                        print("Token expiring soon, refreshing proactively...")
                        self.spotify.refresh_access_token()

        except Exception as e:
            print(f"Error during token health check: {e}")

    def on_button_press(self, button_id):
        """Handle button press events"""
        print(f"Button pressed: {button_id}")

        try:
            if button_id == "play_pause":
                if self.is_playing:
                    self.spotify.pause_playback()
                    self.display.show_message("Paused", "")
                    self.is_playing = False
                else:
                    self.spotify.start_playback()
                    self.display.show_message("Playing", "")
                    self.is_playing = True

            elif button_id == "next":
                self.spotify.next_track()
                self.display.show_message("Next Track", "Loading...")

            elif button_id == "previous":
                self.spotify.previous_track()
                self.display.show_message("Previous Track", "Loading...")

            elif button_id == "menu":
                # Toggle between different display modes
                self.display.toggle_mode()

        except Exception as e:
            print(f"Error handling button press: {e}")
            self.display.show_message("Error", str(e)[:20])

    def on_rotary_change(self, direction):
        """Handle rotary encoder changes for volume control"""
        print(f"Volume adjustment: {direction}")

        try:
            # Adjust volume
            if direction == 1:  # Clockwise
                self.volume = min(100, self.volume + 5)
            else:  # Counter-clockwise
                self.volume = max(0, self.volume - 5)

            # Set volume on Spotify
            self.spotify.set_volume(self.volume)
            self.display.show_volume(self.volume)

        except Exception as e:
            print(f"Error adjusting volume: {e}")

    def run(self):
        """Main run method"""
        print("Starting LoFi Pi...")

        # Initial display
        self.display.show_message("LoFi Pi", "Connecting...")

        # Authenticate with Spotify
        if not self.spotify.authenticate():
            self.display.show_message("Auth Failed", "Check tokens")
            print("\n" + "=" * 50)
            print("SPOTIFY AUTHENTICATION FAILED")
            print("=" * 50)
            print("Your Spotify tokens have expired or are invalid.")
            print("To fix this issue:")
            print("1. Run: python headless_spotify_auth.py")
            print("2. Follow the instructions to re-authenticate")
            print("3. Restart LoFi Pi")
            print("\nLoFi Pi will continue to retry authentication...")
            print("=" * 50)

            # Continue running but with limited functionality
            return self.run_without_spotify()

        print("Spotify authentication successful!")
        self.display.show_message("Connected", "Ready to rock!")
        time.sleep(2)

        # Start normal operation mode
        return self.run_normal_mode()

    def run_without_spotify(self):
        """Run in limited mode when Spotify authentication fails"""
        print("Running in limited mode - authentication will be retried periodically")

        # Show authentication required message
        self.display.show_message("Auth Required", "Run: headless_auth")

        retry_count = 0
        max_retries = 10

        try:
            while self.running and retry_count < max_retries:
                # Process control inputs (if controls are available)
                if self.controls:
                    self.controls.update()

                # Try to re-authenticate every 2 minutes
                if retry_count % 2400 == 0:  # 2400 * 0.05s = 2 minutes
                    print(
                        f"Retry {retry_count // 2400 + 1}/{max_retries // 2400}: Attempting Spotify re-authentication..."
                    )
                    if self.spotify.authenticate():
                        print(
                            "Re-authentication successful! Switching to normal mode..."
                        )
                        self.display.show_message("Connected", "Ready to rock!")
                        time.sleep(2)
                        return self.run_normal_mode()
                    else:
                        self.display.show_message(
                            "Auth Failed", f"Retry {retry_count // 2400 + 1}"
                        )

                retry_count += 1
                time.sleep(0.05)  # 50ms polling rate

        except KeyboardInterrupt:
            print("\nShutdown requested...")
        finally:
            self.running = False
            self.display.cleanup()
            GPIO.cleanup()
            if self.controls:
                self.controls.cleanup()

        print(
            "Max retries reached. Please run 'python headless_spotify_auth.py' to fix authentication."
        )
        return False

    def run_normal_mode(self):
        """Run in normal mode with Spotify authentication"""
        # Start background update thread
        self.update_thread.start()

        # Main control loop
        try:
            while self.running:
                # Process control inputs (if controls are available)
                if self.controls:
                    self.controls.update()
                time.sleep(0.05)  # 50ms polling rate

        except KeyboardInterrupt:
            print("\nShutdown requested...")
        finally:
            self.running = False
            self.display.cleanup()
            GPIO.cleanup()
            if self.controls:
                self.controls.cleanup()

        return True


# Entry point
if __name__ == "__main__":
    try:
        lofi_pi = LoFiPi()
        lofi_pi.run()
    except Exception as e:
        print(f"Failed to start LoFi Pi: {e}")
        sys.exit(1)
