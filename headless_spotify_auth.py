#!/usr/bin/env python3
"""
Headless Spotify Authentication for Raspberry Pi
This script generates a URL for authentication that can be used on another device
"""

import json
import time
import base64
import requests
import urllib.parse
from pathlib import Path
from config import Configt Config


class HeadlessSpotifyAuth:
    def __init__(self, client_id, client_secret, redirect_uri):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def generate_auth_instructions(self):
        """Generate authentication instructions for manual completion"""
        scopes = [
            "user-read-playback-state",
            "user-modify-playback-state",
            "user-read-currently-playing",
        ]

        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(scopes),
            "show_dialog": "true",
        }

        auth_url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(
            params
        )

        print("=== HEADLESS SPOTIFY AUTHENTICATION ===")
        print()
        print(
            "Since this is a headless device, please complete authentication manually:"
        )
        print()
        print("1. Open this URL in a browser on ANY device:")
        print(f"   {auth_url}")
        print()
        print("2. Log in to Spotify and authorize the app")
        print()
        print("3. You'll be redirected to a URL that looks like:")
        print(f"   {self.redirect_uri}?code=AUTHORIZATION_CODE")
        print()
        print("4. Copy the AUTHORIZATION_CODE from the URL and enter it below:")
        print()

        # Get the authorization code from user
        auth_code = input("Enter the authorization code: ").strip()

        if not auth_code:
            print("Error: No authorization code provided!")
            return False

        return self.exchange_code_for_tokens(auth_code)

    def exchange_code_for_tokens(self, auth_code):
        """Exchange authorization code for access and refresh tokens"""
        try:
            # Prepare the token request
            auth_str = f"{self.client_id}:{self.client_secret}"
            auth_bytes = auth_str.encode("ascii")
            auth_b64 = base64.b64encode(auth_bytes).decode("ascii")

            headers = {
                "Authorization": f"Basic {auth_b64}",
                "Content-Type": "application/x-www-form-urlencoded",
            }

            data = {
                "grant_type": "authorization_code",
                "code": auth_code,
                "redirect_uri": self.redirect_uri,
            }

            response = requests.post(
                "https://accounts.spotify.com/api/token",
                headers=headers,
                data=data,
                timeout=10,
            )

            if response.status_code == 200:
                token_data = response.json()
                expires_in = token_data.get("expires_in", 3600)
                current_time = int(time.time())

                tokens = {
                    "access_token": token_data["access_token"],
                    "refresh_token": token_data["refresh_token"],
                    "expires_at": current_time + expires_in,
                }

                # Save tokens
                with open("spotify_tokens.json", "w") as f:
                    json.dump(tokens, f, indent=2)

                # Create backup
                with open("spotify_tokens_backup.json", "w") as f:
                    backup_tokens = tokens.copy()
                    backup_tokens["backup_time"] = current_time
                    json.dump(backup_tokens, f, indent=2)

                print()
                print("✅ SUCCESS! Tokens saved successfully.")
                print("Your LoFi Pi should now be able to connect to Spotify.")
                return True

            else:
                print(f"❌ Token exchange failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False

        except Exception as e:
            print(f"❌ Error during token exchange: {e}")
            return False


def main():
    print("LoFi Pi Headless Spotify Authentication")
    print("=" * 50)

    try:
        # Load config
        config = Config()

        # Initialize auth
        auth = HeadlessSpotifyAuth(
            config.SPOTIFY_CLIENT_ID,
            config.SPOTIFY_CLIENT_SECRET,
            config.SPOTIFY_REDIRECT_URI,
        )

        # Generate auth instructions
        success = auth.generate_auth_instructions()

        if success:
            print()
            print("🎵 Your LoFi Pi is now ready to rock!")
        else:
            print()
            print("❌ Authentication failed. Please try again.")

    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        print("Make sure your config.py file is properly configured with:")
        print("- SPOTIFY_CLIENT_ID")
        print("- SPOTIFY_CLIENT_SECRET")
        print("- SPOTIFY_REDIRECT_URI")


if __name__ == "__main__":
    main()
