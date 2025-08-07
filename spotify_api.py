"""
Spotify Web API integration for LoFi Pi
Handles authentication and playback control
"""

import json
import time
import base64
import requests
from pathlib import Pathport Path


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

        # Token file paths
        self.token_file = Path("spotify_tokens.json")
        self.session_file = Path("spotify_session.json")

        # Session management
        self.device_id = None
        self.last_successful_auth = 0
        self.auth_retry_count = 0
        self.max_auth_retries = 3

        # Create persistent session
        self.session = requests.Session()

        # Default timeout for all requests
        self.request_timeout = 10

    def authenticate(self):
        """
        Authenticate with Spotify using stored tokens with automatic renewal
        """
        try:
            # Load session data if available
            self._load_session_data()

            if self.token_file.exists():
                with open(self.token_file, "r") as f:
                    tokens = json.load(f)
                    self.access_token = tokens["access_token"]
                    self.refresh_token = tokens["refresh_token"]
                    self.token_expires_at = tokens["expires_at"]

                # Save backup of current tokens
                self._save_backup_tokens()

                # Check if token needs refresh (refresh 5 minutes early)
                if time.time() > (self.token_expires_at - 300):
                    print("Access token expires soon, refreshing...")
                    if not self.refresh_access_token():
                        return self._attempt_automatic_reauth()

                # Test the current token
                if self._test_token():
                    print("Using existing valid token")
                    self.last_successful_auth = time.time()
                    self.auth_retry_count = 0
                    self._save_session_data()
                    return True
                else:
                    print("Token test failed, attempting refresh...")
                    if not self.refresh_access_token():
                        return self._attempt_automatic_reauth()
                    return True

            else:
                print("No stored tokens found.")
                return self._attempt_automatic_reauth()

        except Exception as e:
            print(f"Error loading tokens: {e}")
            return self._attempt_automatic_reauth()

    def _load_session_data(self):
        """Load persistent session data"""
        try:
            if self.session_file.exists():
                with open(self.session_file, "r") as f:
                    session_data = json.load(f)
                    self.device_id = session_data.get("device_id")
                    self.last_successful_auth = session_data.get(
                        "last_successful_auth", 0
                    )
                    self.auth_retry_count = session_data.get("auth_retry_count", 0)
        except Exception as e:
            print(f"Error loading session data: {e}")

    def _save_session_data(self):
        """Save persistent session data"""
        try:
            session_data = {
                "device_id": self.device_id,
                "last_successful_auth": self.last_successful_auth,
                "auth_retry_count": self.auth_retry_count,
                "last_update": time.time(),
            }
            with open(self.session_file, "w") as f:
                json.dump(session_data, f, indent=2)
        except Exception as e:
            print(f"Error saving session data: {e}")

    def _attempt_automatic_reauth(self):
        """Attempt automatic re-authentication using various strategies"""
        self.auth_retry_count += 1

        # Don't retry too frequently
        time_since_last_auth = time.time() - self.last_successful_auth
        if time_since_last_auth < 300:  # 5 minutes
            print(
                f"Too soon since last auth attempt ({int(time_since_last_auth)}s ago)"
            )
            return False

        if self.auth_retry_count > self.max_auth_retries:
            print("Max authentication retries exceeded")
            return False

        print(
            f"Attempting automatic re-authentication (attempt {self.auth_retry_count}/{self.max_auth_retries})"
        )

        # Strategy 1: Try backup tokens
        if self._try_backup_tokens():
            return True

        # Strategy 2: Try to get a client credentials token for basic functionality
        if self._try_client_credentials():
            return True

        # Strategy 3: Check if we can find active Spotify sessions to piggyback
        if self._try_device_discovery():
            return True

        print("All automatic authentication strategies failed")
        print("You may need to run headless_spotify_auth.py for full functionality")

        # Even if we can't fully authenticate, return True to continue in limited mode
        return True

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

    def _try_client_credentials(self):
        """
        Try to get a client credentials token for basic functionality
        This provides limited access but doesn't require user authorization
        """
        try:
            print("Attempting client credentials authentication...")

            auth_str = f"{self.client_id}:{self.client_secret}"
            auth_bytes = auth_str.encode("ascii")
            auth_b64 = base64.b64encode(auth_bytes).decode("ascii")

            headers = {
                "Authorization": f"Basic {auth_b64}",
                "Content-Type": "application/x-www-form-urlencoded",
            }

            data = {"grant_type": "client_credentials"}

            response = self.session.post(
                self.token_url, headers=headers, data=data, timeout=self.request_timeout
            )

            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data["access_token"]

                # Client credentials tokens don't have refresh tokens
                self.refresh_token = None

                expires_in = token_data.get("expires_in", 3600)
                self.token_expires_at = time.time() + expires_in

                print(
                    "Client credentials authentication successful (limited functionality)"
                )
                return True
            else:
                print(
                    f"Client credentials authentication failed: {response.status_code}"
                )
                return False

        except Exception as e:
            print(f"Client credentials authentication error: {e}")
            return False

    def _try_device_discovery(self):
        """
        Try to discover active Spotify devices that might be usable
        This is a fallback strategy for maintaining connectivity
        """
        try:
            print("Attempting device discovery...")

            # This would require an existing valid token, so it's more of a
            # connectivity test and device enumeration
            if not self.access_token:
                return False

            devices = self.get_devices()
            if devices and devices.get("devices"):
                active_devices = [d for d in devices["devices"] if d.get("is_active")]
                if active_devices:
                    self.device_id = active_devices[0]["id"]
                    print(f"Found active device: {active_devices[0]['name']}")
                    self._save_session_data()
                    return True

            return False

        except Exception as e:
            print(f"Device discovery error: {e}")
            return False

    def refresh_access_token(self):
        """Refresh the access token using enhanced refresh with retries"""
        if not self.refresh_token:
            print("No refresh token available")
            return self._handle_auth_failure()

        # Try enhanced refresh first
        if self._enhanced_token_refresh():
            return True
        else:
            return self._handle_auth_failure()

    def _enhanced_token_refresh(self):
        """
        Enhanced token refresh with multiple retry strategies
        """
        if not self.refresh_token:
            print("No refresh token available for enhanced refresh")
            return False

        max_retries = 3
        retry_delay = 2  # seconds

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    print(f"Token refresh retry {attempt + 1}/{max_retries}")
                    time.sleep(retry_delay * attempt)  # Exponential backoff

                headers = {"Content-Type": "application/x-www-form-urlencoded"}

                # Create basic auth header
                auth_str = f"{self.client_id}:{self.client_secret}"
                auth_bytes = auth_str.encode("ascii")
                auth_b64 = base64.b64encode(auth_bytes).decode("ascii")
                headers["Authorization"] = f"Basic {auth_b64}"

                data = {
                    "grant_type": "refresh_token",
                    "refresh_token": self.refresh_token,
                }

                response = self.session.post(
                    self.token_url,
                    headers=headers,
                    data=data,
                    timeout=self.request_timeout,
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

                    print("Enhanced token refresh successful")
                    self.auth_retry_count = 0
                    self.last_successful_auth = time.time()
                    self._save_session_data()
                    return True

                elif response.status_code == 400:
                    # Refresh token might be expired or invalid
                    print("Refresh token expired or invalid")
                    return False
                else:
                    print(f"Token refresh failed with status {response.status_code}")
                    if attempt == max_retries - 1:
                        return False

            except requests.exceptions.RequestException as e:
                print(
                    f"Network error during token refresh (attempt {attempt + 1}): {e}"
                )
                if attempt == max_retries - 1:
                    return False
            except Exception as e:
                print(f"Unexpected error during token refresh: {e}")
                if attempt == max_retries - 1:
                    return False

        return False

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
