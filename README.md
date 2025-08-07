# LoFi Pi - Raspberry Pi Zero Spotify Controller

A minimalist Spotify controller using a Raspberry Pi Zero with e-ink display, mechanical switches, and rotary encoder.

## Hardware Requirements

- Raspberry Pi Zero W (or Zero 2 W)
- 2" E-ink display (SPI interface, e.g., Waveshare 2.13" e-Paper HAT)
- 3-4 mechanical keyboard switches (Cherry MX or similar)
- Rotary encoder with push button
- MicroSD card (16GB+)
- Breadboard or HAT
- Jumper wires
- 5V power supply (micro USB)

## Wiring Diagram

### E-ink Display (SPI)

- VCC → 3.3V (Pin 1)
- GND → GND (Pin 6)
- DIN → GPIO 10 (Pin 19) - MOSI
- CLK → GPIO 11 (Pin 23) - SCLK
- CS → GPIO 8 (Pin 24) - CE0
- DC → GPIO 25 (Pin 22) - Data/Command
- RST → GPIO 17 (Pin 11) - Reset
- BUSY → GPIO 24 (Pin 18) - Busy

### Mechanical Switches

- Play/Pause → GPIO 2 (Pin 3)
- Next Track → GPIO 3 (Pin 5)
- Previous Track → GPIO 4 (Pin 7)
- Menu/Mode → GPIO 14 (Pin 8)

### Rotary Encoder (Volume Control)

- CLK → GPIO 5 (Pin 29)
- DT → GPIO 6 (Pin 31)
- SW → GPIO 13 (Pin 33) - Push button
- VCC → 3.3V (Pin 1)
- GND → GND (Pin 9)

## 🚀 Quick Start with Automated Token Management

**New!** This project now includes a fully automated token management system that eliminates manual token refresh operations.

### 1. Install and Setup

```bash
# Install dependencies and setup automation
./setup_auto_tokens.sh

# One-time authentication (use any device with a browser)
python3 headless_spotify_auth.py
```

### 2. Start Automatic Management

```bash
sudo systemctl enable lofi-pi-token-manager
sudo systemctl start lofi-pi-token-manager
```

**That's it!** Your LoFi Pi will now maintain Spotify connectivity automatically, refreshing tokens before they expire and recovering from authentication failures without manual intervention.

## Software Setup

1. Install Raspberry Pi OS Lite on your Pi Zero
2. Enable SPI interface in raspi-config
3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure your Spotify API credentials in `config.py`
5. Connect to WiFi
6. **Run the automated setup**:
   ```bash
   ./setup_auto_tokens.sh
   ```

## 🔄 Automated Token Management

This project includes a sophisticated automated token management system:

- **🔄 Automatic refresh**: Tokens are refreshed 10 minutes before expiry
- **🛡️ Multiple fallback strategies**: Client credentials, backup tokens, device discovery
- **📊 Continuous monitoring**: Background service + cron job redundancy
- **🔧 Self-healing**: Automatic recovery from network and API errors
- **📱 Headless friendly**: Re-authenticate using any device with a browser
- **📋 Comprehensive logging**: Full audit trail of all token operations

### Quick Status Check

```bash
python3 auto_token_manager.py --status
```

### Emergency Re-authentication

If you ever see "Auth Failed":

```bash
python3 headless_spotify_auth.py
```

See `docs/automated_token_system.md` for comprehensive documentation.

## Features

- Display current song title, artist, and album
- Show album artwork on e-ink display
- Control playback (play/pause, next/previous)
- Volume control with rotary encoder
- Low power consumption with e-ink display
- Spotify Web API integration
- Album art caching and display

## Setup Instructions

See `docs/setup.md` for detailed setup instructions.
