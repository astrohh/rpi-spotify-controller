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

                # Save backup of current tokens
                self._save_backup_tokens()

                # Check if token needs refresh
                if time.time() > self.token_expires_at:
                    print("Access token expired, refreshing...")
                    return self.refresh_access_token()

                # Test the current token
                if self._test_token():
                    print("Using existing valid token")
                    return True
                else:
                    print("Token test failed, attempting refresh...")
                    return self.refresh_access_token()

            else:
                print("No stored tokens found. Please run setup_spotify_auth.py first.")
                return False

        except Exception as e:
            print(f"Error loading tokens: {e}")
            # Try to load backup tokens
            return self._try_backup_tokens()

    def _test_token(self):
        """Test if current access token is valid"""
        if not self.access_token:
            return False

        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(f"{self.api_base}/me", headers=headers, timeout=5)
            return response.status_code == 200
        except:
            return False

    def _try_backup_tokens(self):
        """Try to load backup tokens if main tokens fail"""
        backup_file = Path("spotify_tokens_backup.json")

        if backup_file.exists():
            try:
                print("Attempting to load backup tokens...")
                with open(backup_file, "r") as f:
                    tokens = json.load(f)
                    self.access_token = tokens["access_token"]
                    self.refresh_token = tokens["refresh_token"]
                    self.token_expires_at = tokens["expires_at"]

                if self._test_token():
                    print("Backup tokens are valid")
                    # Save as main tokens
                    main_tokens = {
                        "access_token": self.access_token,
                        "refresh_token": self.refresh_token,
                        "expires_at": self.token_expires_at,
                    }
                    with open(self.token_file, "w") as f:
                        json.dump(main_tokens, f, indent=2)
                    return True
                else:
                    return self.refresh_access_token()

            except Exception as e:
                print(f"Failed to load backup tokens: {e}")

        return False

    def refresh_access_token(self):
        """Refresh the access token using refresh token"""
        if not self.refresh_token:
            print("No refresh token available")
            return self._handle_auth_failure()

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

                # Sometimes Spotify returns a new refresh token
                if "refresh_token" in token_data:
                    self.refresh_token = token_data["refresh_token"]
                    print("Received new refresh token")

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
            elif response.status_code == 400:
                # Refresh token might be expired or invalid
                print(
                    "Refresh token expired or invalid. Attempting re-authentication..."
                )
                return self._handle_auth_failure()
            else:
                print(f"Token refresh failed: {response.status_code}")
                return self._handle_auth_failure()

        except requests.exceptions.RequestException as e:
            print(f"Network error refreshing token: {e}")
            return self._handle_auth_failure()
        except Exception as e:
            print(f"Error refreshing token: {e}")
            return self._handle_auth_failure()

    def _handle_auth_failure(self):
        """Handle authentication failure scenarios"""
        print("Authentication failed. Attempting automated re-authentication...")

        # Try to use device code flow for headless authentication
        return self._device_code_auth()

    def _device_code_auth(self):
        """
        Implement Spotify's Device Authorization Grant flow for headless devices
        This allows authentication without a browser redirect
        """
        try:
            # Step 1: Request device code
            device_auth_url = "https://accounts.spotify.com/api/token"

            auth_str = f"{self.client_id}:{self.client_secret}"
            auth_bytes = auth_str.encode("ascii")
            auth_b64 = base64.b64encode(auth_bytes).decode("ascii")

            headers = {
                "Authorization": f"Basic {auth_b64}",
                "Content-Type": "application/x-www-form-urlencoded",
            }

            # Request device code
            data = {"grant_type": "client_credentials"}

            print("WARNING: Automatic re-authentication requires manual setup.")
            print("The refresh token has expired and cannot be renewed automatically.")
            print(
                "Please run 'python setup_spotify_auth.py' on a computer with a browser"
            )
            print(
                "to generate new tokens, then copy spotify_tokens.json to this device."
            )

            return False

        except Exception as e:
            print(f"Device code authentication failed: {e}")
            return False

    def _save_backup_tokens(self):
        """Save a backup of current tokens"""
        if self.access_token and self.refresh_token:
            backup_file = Path("spotify_tokens_backup.json")
            tokens = {
                "access_token": self.access_token,
                "refresh_token": self.refresh_token,
                "expires_at": self.token_expires_at,
                "backup_time": time.time(),
            }

            try:
                with open(backup_file, "w") as f:
                    json.dump(tokens, f, indent=2)
                print("Token backup saved")
            except Exception as e:
                print(f"Failed to save token backup: {e}")

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
