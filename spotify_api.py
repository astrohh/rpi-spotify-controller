"""
Spotify Web API integration for LoFi Pi
Handles authentication and playback control
"""

import json
import time
import base64
import requests
from pathlib import Path


class SpotifyAPI:
    def __init__(self, client_id, client_secret, redirect_uri):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = 0

        # Spotify API endpoints
        self.auth_url = "https://accounts.spotify.com/authorize"
        self.token_url = "https://accounts.spotify.com/api/token"
        self.api_base = "https://api.spotify.com/v1"

        # Token file path
        self.token_file = Path("spotify_tokens.json")

    def authenticate(self):
        """
        Authenticate with Spotify using stored tokens
        """
        try:
            if self.token_file.exists():
                with open(self.token_file, "r") as f:
                    tokens = json.load(f)
                    self.access_token = tokens["access_token"]
                    self.refresh_token = tokens["refresh_token"]
                    self.token_expires_at = tokens["expires_at"]

                # Check if token needs refresh
                if time.time() > self.token_expires_at:
                    return self.refresh_access_token()

                return True
            else:
                print("No stored tokens found. Please run setup_spotify_auth.py first.")
                return False

        except Exception as e:
            print(f"Error loading tokens: {e}")
            return False

    def refresh_access_token(self):
        """Refresh the access token using refresh token"""
        if not self.refresh_token:
            print("No refresh token available")
            return False

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        # Create basic auth header
        auth_str = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_str.encode("ascii")
        auth_b64 = base64.b64encode(auth_bytes).decode("ascii")
        headers["Authorization"] = f"Basic {auth_b64}"

        data = {"grant_type": "refresh_token", "refresh_token": self.refresh_token}

        try:
            response = requests.post(
                self.token_url, headers=headers, data=data, timeout=10
            )

            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data["access_token"]

                # Update expiry time
                expires_in = token_data.get("expires_in", 3600)
                self.token_expires_at = time.time() + expires_in

                # Save updated tokens
                tokens = {
                    "access_token": self.access_token,
                    "refresh_token": self.refresh_token,
                    "expires_at": self.token_expires_at,
                }

                with open(self.token_file, "w") as f:
                    json.dump(tokens, f, indent=2)

                print("Access token refreshed successfully")
                return True
            else:
                print(f"Token refresh failed: {response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"Network error refreshing token: {e}")
            return False
        except Exception as e:
            print(f"Error refreshing token: {e}")
            return False

    def _make_request(self, method, endpoint, data=None, params=None):
        """Make authenticated request to Spotify API"""
        if not self.access_token:
            raise Exception("Not authenticated")

        url = f"{self.api_base}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        try:
            if method == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=10)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=10)
            elif method == "PUT":
                if data:
                    response = requests.put(url, headers=headers, json=data, timeout=10)
                else:
                    response = requests.put(url, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            if response.status_code == 401:
                # Token expired, try to refresh
                print("Token expired, attempting refresh...")
                if self.refresh_access_token():
                    headers["Authorization"] = f"Bearer {self.access_token}"
                    # Retry the request
                    if method == "GET":
                        response = requests.get(
                            url, headers=headers, params=params, timeout=10
                        )
                    elif method == "POST":
                        response = requests.post(
                            url, headers=headers, json=data, timeout=10
                        )
                    elif method == "PUT":
                        if data:
                            response = requests.put(
                                url, headers=headers, json=data, timeout=10
                            )
                        else:
                            response = requests.put(url, headers=headers, timeout=10)

            if response.status_code >= 400:
                print(f"API Error {response.status_code}: {response.text}")
                return None

            # Handle empty responses (like for pause/play)
            if response.status_code == 204 or not response.text:
                return {}

            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"Network error: {e}")
            return None
        except Exception as e:
            print(f"Request error: {e}")
            return None

    def get_current_playback(self):
        """Get information about current playback"""
        return self._make_request("GET", "/me/player")

    def start_playback(self, device_id=None):
        """Start or resume playback"""
        endpoint = "/me/player/play"
        params = {"device_id": device_id} if device_id else None
        return self._make_request("PUT", endpoint)

    def pause_playback(self, device_id=None):
        """Pause playback"""
        endpoint = "/me/player/pause"
        params = {"device_id": device_id} if device_id else None
        return self._make_request("PUT", endpoint)

    def next_track(self, device_id=None):
        """Skip to next track"""
        endpoint = "/me/player/next"
        params = {"device_id": device_id} if device_id else None
        return self._make_request("POST", endpoint)

    def previous_track(self, device_id=None):
        """Skip to previous track"""
        endpoint = "/me/player/previous"
        params = {"device_id": device_id} if device_id else None
        return self._make_request("POST", endpoint)

    def set_volume(self, volume_percent, device_id=None):
        """Set playback volume (0-100)"""
        params = {"volume_percent": volume_percent}
        if device_id:
            params["device_id"] = device_id
        return self._make_request("PUT", "/me/player/volume", params=params)

    def get_devices(self):
        """Get available playback devices"""
        return self._make_request("GET", "/me/player/devices")

    def get_user_profile(self):
        """Get current user's profile"""
        return self._make_request("GET", "/me")
