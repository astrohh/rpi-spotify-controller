#!/usr/bin/env python3
"""
Spotify Authentication Setup Script
Run this on your computer to generate tokens for the Pico
"""

import json
import base64
import requests
import threading
import webbrowser
import http.server
import urllib.parse
import socketserver
from urllib.parse import urlparse, parse_qs urlparse, parse_qs


class SpotifyAuth:
    def __init__(self, client_id, client_secret, redirect_uri):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.auth_code = None

    def get_auth_url(self):
        """Generate Spotify authorization URL"""
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
        return auth_url

    def start_callback_server(self):
        """Start a local server to catch the authorization callback"""

        class CallbackHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(handler_self):
                if handler_self.path.startswith("/callback"):
                    parsed_url = urlparse(handler_self.path)
                    query_params = parse_qs(parsed_url.query)

                    if "code" in query_params:
                        self.auth_code = query_params["code"][0]
                        handler_self.send_response(200)
                        handler_self.send_header("Content-type", "text/html")
                        handler_self.end_headers()
                        handler_self.wfile.write(
                            b"""
                        <html>
                        <body>
                        <h1>Authorization Successful!</h1>
                        <p>You can close this window and return to the terminal.</p>
                        </body>
                        </html>
                        """
                        )
                    else:
                        handler_self.send_response(400)
                        handler_self.end_headers()
                        handler_self.wfile.write(b"Authorization failed")

                def log_message(self, format, *args):
                    pass  # Suppress log messages

        # Start server on port 8888
        with socketserver.TCPServer(("", 8888), CallbackHandler) as httpd:
            print("Callback server started on http://localhost:8888")

            # Wait for the callback
            while self.auth_code is None:
                httpd.handle_request()

            print("Authorization code received!")

    def exchange_code_for_tokens(self):
        """Exchange authorization code for access and refresh tokens"""
        if not self.auth_code:
            raise Exception("No authorization code available")

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
            "code": self.auth_code,
            "redirect_uri": self.redirect_uri,
        }

        response = requests.post(
            "https://accounts.spotify.com/api/token", headers=headers, data=data
        )

        if response.status_code == 200:
            token_data = response.json()
            return {
                "access_token": token_data["access_token"],
                "refresh_token": token_data["refresh_token"],
                "expires_at": token_data.get("expires_in", 3600)
                + int(requests.utils.default_headers()["User-Agent"].split()[-1]),
            }
        else:
            raise Exception(
                f"Token exchange failed: {response.status_code} - {response.text}"
            )


def main():
    print("LoFi Pi Spotify Authentication Setup")
    print("=" * 40)

    # Get credentials from user
    client_id = input("Enter your Spotify Client ID: ").strip()
    client_secret = input("Enter your Spotify Client Secret: ").strip()
    redirect_uri = "http://localhost:8888/callback"

    if not client_id or not client_secret:
        print("Error: Client ID and Client Secret are required!")
        return

    # Initialize Spotify auth
    auth = SpotifyAuth(client_id, client_secret, redirect_uri)

    # Generate auth URL
    auth_url = auth.get_auth_url()

    print(f"\nOpening browser for Spotify authorization...")
    print(f"If the browser doesn't open automatically, visit this URL:")
    print(f"{auth_url}")

    # Open browser
    webbrowser.open(auth_url)

    # Start callback server in a separate thread
    server_thread = threading.Thread(target=auth.start_callback_server)
    server_thread.daemon = True
    server_thread.start()

    print("\nWaiting for authorization...")
    print("Please authorize the application in your browser.")

    # Wait for authorization
    server_thread.join()

    try:
        # Exchange code for tokens
        print("Exchanging authorization code for tokens...")
        tokens = auth.exchange_code_for_tokens()

        # Save tokens to file
        with open("spotify_tokens.json", "w") as f:
            json.dump(tokens, f, indent=2)

        print("\nSuccess! Tokens saved to 'spotify_tokens.json'")
        print("Copy this file to your Raspberry Pi Pico.")
        print("\nYour LoFi Pi is now ready to use!")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
