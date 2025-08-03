"""
Configuration settings for LoFi Pi
Copy this to config.py and fill in your actual credentials
"""


class Config:
    # WiFi Settings
    WIFI_SSID = "YOUR_WIFI_NETWORK_NAME"
    WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"

    # Spotify API Credentials
    # Get these from https://developer.spotify.com/dashboard
    SPOTIFY_CLIENT_ID = "your_spotify_client_id_here"
    SPOTIFY_CLIENT_SECRET = "your_spotify_client_secret_here"
    SPOTIFY_REDIRECT_URI = "http://localhost:8888/callback"

    # Hardware Pin Configuration
    # E-ink Display (SPI)
    EINK_MOSI_PIN = 11
    EINK_SCK_PIN = 10
    EINK_CS_PIN = 9
    EINK_DC_PIN = 8
    EINK_RST_PIN = 12
    EINK_BUSY_PIN = 13

    # Control Buttons
    PLAY_PAUSE_PIN = 2
    NEXT_PIN = 3
    PREV_PIN = 4
    MENU_PIN = 5

    # Rotary Encoder
    ROTARY_CLK_PIN = 6
    ROTARY_DT_PIN = 7
    ROTARY_SW_PIN = 14

    # Display Settings
    DISPLAY_WIDTH = 250
    DISPLAY_HEIGHT = 122

    # Update intervals (milliseconds)
    SPOTIFY_UPDATE_INTERVAL = 5000
    DISPLAY_REFRESH_INTERVAL = 1000
