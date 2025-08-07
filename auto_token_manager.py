#!/usr/bin/env python3
"""
Automatic Spotify Token Management Service
Runs continuously to maintain valid tokens without user intervention
"""

import time
import json
import signal
import threading
from pathlib import Path
from config import Config
from datetime import datetime
from spotify_api import SpotifyAPIfrom config import Config


class AutoTokenManager:
    def __init__(self):
        self.config = Config()
        self.running = True
        self.spotify = None

        # Timing configuration
        self.check_interval = 300  # Check every 5 minutes
        self.refresh_early_seconds = 600  # Refresh 10 minutes before expiry
        self.max_retry_attempts = 5
        self.retry_delay = 60  # 1 minute between retries

        # State tracking
        self.last_successful_refresh = 0
        self.consecutive_failures = 0

        # Files
        self.status_file = Path("auto_token_status.json")
        self.log_file = Path("auto_token.log")

        # Initialize Spotify API
        self._init_spotify_api()

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _init_spotify_api(self):
        """Initialize Spotify API with automatic session management"""
        try:
            self.spotify = SpotifyAPI(
                self.config.SPOTIFY_CLIENT_ID,
                self.config.SPOTIFY_CLIENT_SECRET,
                self.config.SPOTIFY_REDIRECT_URI,
            )
            self.log("Spotify API initialized")
        except Exception as e:
            self.log(f"Failed to initialize Spotify API: {e}")

    def log(self, message):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)

        try:
            with open(self.log_file, "a") as f:
                f.write(log_entry + "\n")
        except:
            pass

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.log("Shutdown signal received, stopping token manager...")
        self.running = False

    def get_token_status(self):
        """Get current token status information"""
        try:
            token_file = Path("spotify_tokens.json")
            if not token_file.exists():
                return {"status": "no_tokens", "expires_at": 0, "time_until_expiry": 0}

            with open(token_file, "r") as f:
                tokens = json.load(f)

            expires_at = tokens.get("expires_at", 0)
            current_time = time.time()
            time_until_expiry = expires_at - current_time

            if time_until_expiry <= 0:
                status = "expired"
            elif time_until_expiry <= self.refresh_early_seconds:
                status = "expiring_soon"
            else:
                status = "valid"

            return {
                "status": status,
                "expires_at": expires_at,
                "time_until_expiry": time_until_expiry,
                "expires_in_minutes": int(time_until_expiry / 60),
            }

        except Exception as e:
            self.log(f"Error getting token status: {e}")
            return {"status": "error", "error": str(e)}

    def refresh_tokens_if_needed(self):
        """Check and refresh tokens if necessary"""
        try:
            status = self.get_token_status()

            if status["status"] in ["expired", "expiring_soon", "no_tokens"]:
                self.log(f"Token refresh needed. Status: {status['status']}")

                if status["status"] == "expiring_soon":
                    self.log(f"Token expires in {status['expires_in_minutes']} minutes")

                # Attempt to refresh
                if self.spotify and self.spotify.refresh_access_token():
                    self.log("Token refresh successful")
                    self.last_successful_refresh = time.time()
                    self.consecutive_failures = 0
                    self._save_status("success", "Token refreshed successfully")
                    return True
                else:
                    self.consecutive_failures += 1
                    self.log(
                        f"Token refresh failed (attempt {self.consecutive_failures})"
                    )

                    # Try to re-initialize and authenticate
                    if self._attempt_full_reauth():
                        return True

                    self._save_status(
                        "failed",
                        f"Token refresh failed after {self.consecutive_failures} attempts",
                    )
                    return False
            else:
                # Tokens are valid
                if status["status"] == "valid":
                    self.log(
                        f"Tokens valid, expires in {status['expires_in_minutes']} minutes"
                    )
                    self._save_status(
                        "valid",
                        f"Tokens valid for {status['expires_in_minutes']} minutes",
                    )
                return True

        except Exception as e:
            self.log(f"Error during token refresh check: {e}")
            self._save_status("error", str(e))
            return False

    def _attempt_full_reauth(self):
        """Attempt full re-authentication when refresh fails"""
        try:
            self.log("Attempting full re-authentication...")

            # Re-initialize Spotify API
            self._init_spotify_api()

            if self.spotify and self.spotify.authenticate():
                self.log("Full re-authentication successful")
                self.consecutive_failures = 0
                self.last_successful_refresh = time.time()
                return True
            else:
                self.log("Full re-authentication failed")
                return False

        except Exception as e:
            self.log(f"Error during full re-authentication: {e}")
            return False

    def _save_status(self, status, message):
        """Save current status to file"""
        try:
            status_data = {
                "status": status,
                "message": message,
                "timestamp": time.time(),
                "datetime": datetime.now().isoformat(),
                "consecutive_failures": self.consecutive_failures,
                "last_successful_refresh": self.last_successful_refresh,
            }

            with open(self.status_file, "w") as f:
                json.dump(status_data, f, indent=2)

        except Exception as e:
            self.log(f"Error saving status: {e}")

    def run_continuous(self):
        """Run continuous token management"""
        self.log("Starting automatic token management service...")
        self.log(f"Check interval: {self.check_interval} seconds")
        self.log(f"Refresh early: {self.refresh_early_seconds} seconds before expiry")

        while self.running:
            try:
                self.refresh_tokens_if_needed()

                # If we have too many consecutive failures, increase check interval
                if self.consecutive_failures > 3:
                    sleep_time = self.check_interval * 2
                    self.log(
                        f"Multiple failures detected, checking again in {sleep_time} seconds"
                    )
                else:
                    sleep_time = self.check_interval

                # Sleep in small increments to respond to shutdown signals quickly
                for _ in range(sleep_time):
                    if not self.running:
                        break
                    time.sleep(1)

            except KeyboardInterrupt:
                self.log("Keyboard interrupt received")
                break
            except Exception as e:
                self.log(f"Unexpected error in main loop: {e}")
                time.sleep(30)  # Wait 30 seconds before retrying

        self.log("Token management service stopped")

    def run_single_check(self):
        """Run a single token check and refresh if needed"""
        self.log("Running single token check...")
        success = self.refresh_tokens_if_needed()

        if success:
            self.log("Single check completed successfully")
        else:
            self.log("Single check failed")

        return success


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Automatic Spotify Token Manager")
    parser.add_argument(
        "--continuous", action="store_true", help="Run continuous monitoring"
    )
    parser.add_argument(
        "--check", action="store_true", help="Run single check and exit"
    )
    parser.add_argument(
        "--status", action="store_true", help="Show current token status"
    )
    parser.add_argument(
        "--daemon", action="store_true", help="Run as daemon (background)"
    )

    args = parser.parse_args()

    manager = AutoTokenManager()

    if args.status:
        status = manager.get_token_status()
        print(f"Token Status: {status['status']}")
        if status.get("expires_in_minutes"):
            print(f"Expires in: {status['expires_in_minutes']} minutes")
        if status.get("error"):
            print(f"Error: {status['error']}")

    elif args.check:
        success = manager.run_single_check()
        exit(0 if success else 1)

    elif args.continuous or args.daemon:
        if args.daemon:
            # TODO: Implement proper daemon mode with fork()
            print("Daemon mode not yet implemented. Running in foreground...")

        try:
            manager.run_continuous()
        except KeyboardInterrupt:
            print("\nStopping token manager...")
    else:
        print("Usage:")
        print("  python auto_token_manager.py --check        # Run single check")
        print(
            "  python auto_token_manager.py --continuous   # Run continuous monitoring"
        )
        print("  python auto_token_manager.py --status       # Show token status")
        print("  python auto_token_manager.py --daemon       # Run as daemon")


if __name__ == "__main__":
    main()
