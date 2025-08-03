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

        # Initialize hardware components
        self.display = EInkDisplay()
        self.controls = Controls(self.on_button_press, self.on_rotary_change)

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
        sys.exit(0)

    def update_loop(self):
        """Main update loop - runs in background thread"""
        while self.running:
            try:
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
                self.display.show_message("Error", "Check connection")

            # Wait before next update
            time.sleep(self.config.SPOTIFY_UPDATE_INTERVAL / 1000)

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
            return False

        print("Spotify authentication successful!")
        self.display.show_message("Connected", "Ready to rock!")
        time.sleep(2)

        # Start background update thread
        self.update_thread.start()

        # Main control loop
        try:
            while self.running:
                # Process control inputs
                self.controls.update()
                time.sleep(0.05)  # 50ms polling rate

        except KeyboardInterrupt:
            print("\nShutdown requested...")
        finally:
            self.running = False
            self.display.cleanup()

        return True


# Entry point
if __name__ == "__main__":
    try:
        lofi_pi = LoFiPi()
        lofi_pi.run()
    except Exception as e:
        print(f"Failed to start LoFi Pi: {e}")
        sys.exit(1)
