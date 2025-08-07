#!/usr/bin/env python3
"""
Spotify Token Monitor and Recovery Service
Monitors token health and attempts automatic recovery
"""

import json
import time
import requests
import schedule
from pathlib import Path
from config import Config
from spotify_api import SpotifyAPI
from datetime import datetime, timedelta


class TokenMonitor:
    def __init__(self):
        self.config = Config()
        self.token_file = Path("spotify_tokens.json")
        self.log_file = Path("token_monitor.log")

    def log(self, message):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)

        try:
            with open(self.log_file, "a") as f:
                f.write(log_entry + "\n")
        except:
            pass  # Don't fail if logging fails

    def check_token_health(self):
        """Check if tokens are healthy and refresh if needed"""
        try:
            if not self.token_file.exists():
                self.log("ERROR: No token file found")
                return False

            with open(self.token_file, "r") as f:
                tokens = json.load(f)

            expires_at = tokens.get("expires_at", 0)
            current_time = time.time()

            # Check if token expires in the next 10 minutes
            if current_time > (expires_at - 600):
                self.log("Token expires soon, attempting refresh...")
                return self.refresh_token()
            else:
                # Test token validity
                if self.test_token(tokens["access_token"]):
                    time_until_expiry = expires_at - current_time
                    self.log(
                        f"Token healthy, expires in {int(time_until_expiry/60)} minutes"
                    )
                    return True
                else:
                    self.log("Token test failed, attempting refresh...")
                    return self.refresh_token()

        except Exception as e:
            self.log(f"ERROR checking token health: {e}")
            return False

    def test_token(self, access_token):
        """Test if access token is valid"""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = requests.get(
                "https://api.spotify.com/v1/me", headers=headers, timeout=5
            )
            return response.status_code == 200
        except:
            return False

    def refresh_token(self):
        """Attempt to refresh the token"""
        try:
            spotify = SpotifyAPI(
                self.config.SPOTIFY_CLIENT_ID,
                self.config.SPOTIFY_CLIENT_SECRET,
                self.config.SPOTIFY_REDIRECT_URI,
            )

            # Load current tokens
            if self.token_file.exists():
                with open(self.token_file, "r") as f:
                    tokens = json.load(f)
                    spotify.refresh_token = tokens.get("refresh_token")

            if spotify.refresh_access_token():
                self.log("Token refresh successful")
                return True
            else:
                self.log("Token refresh failed - manual re-authentication required")
                self.send_notification()
                return False

        except Exception as e:
            self.log(f"ERROR during token refresh: {e}")
            return False

    def send_notification(self):
        """Send notification about authentication failure"""
        notification_file = Path("auth_failure_notice.txt")

        message = f"""
SPOTIFY AUTHENTICATION FAILURE
==============================
Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Your LoFi Pi has lost connection to Spotify and automatic token refresh failed.
Manual re-authentication is required.

To fix this:
1. Run: python headless_spotify_auth.py
2. Follow the instructions to re-authenticate
3. Your LoFi Pi will automatically resume working

This file will be automatically deleted once authentication is restored.
"""

        try:
            with open(notification_file, "w") as f:
                f.write(message)
            self.log("Authentication failure notice created")
        except Exception as e:
            self.log(f"Failed to create notice file: {e}")

    def cleanup_notifications(self):
        """Remove notification files if authentication is working"""
        notification_file = Path("auth_failure_notice.txt")
        if notification_file.exists():
            try:
                notification_file.unlink()
                self.log("Authentication restored - removed failure notice")
            except:
                pass

    def run_check(self):
        """Run a single token health check"""
        self.log("Running token health check...")

        if self.check_token_health():
            self.cleanup_notifications()
        else:
            self.log("Token health check failed")

    def start_monitoring(self):
        """Start continuous token monitoring"""
        self.log("Starting Spotify token monitoring service...")

        # Schedule checks every 30 minutes
        schedule.every(30).minutes.do(self.run_check)

        # Run initial check
        self.run_check()

        # Keep running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute for scheduled tasks


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Spotify Token Monitor")
    parser.add_argument(
        "--check", action="store_true", help="Run single check and exit"
    )
    parser.add_argument(
        "--monitor", action="store_true", help="Start continuous monitoring"
    )

    args = parser.parse_args()

    monitor = TokenMonitor()

    if args.check:
        monitor.run_check()
    elif args.monitor:
        try:
            monitor.start_monitoring()
        except KeyboardInterrupt:
            monitor.log("Token monitoring stopped")
    else:
        print("Usage:")
        print("  python token_monitor.py --check      # Run single check")
        print("  python token_monitor.py --monitor    # Start continuous monitoring")


if __name__ == "__main__":
    main()
