# LoFi Pi Setup Guide (Raspberry Pi Zero)

## Prerequisites

### Hardware Requirements

- Raspberry Pi Zero W (or Zero 2 W)
- 2.13" E-ink display (SPI interface, e.g., Waveshare 2.13" e-Paper HAT)
- 3-4 mechanical keyboard switches
- Rotary encoder with push button
- MicroSD card (16GB+)
- Breadboard or custom PCB
- Jumper wires
- 5V power supply (micro USB)

### Software Requirements

- Raspberry Pi OS Lite (recommended)
- Python 3.7+ (included with Pi OS)
- Spotify Premium account
- Spotify Developer Account

## Step 1: Prepare Raspberry Pi Zero

1. Flash Raspberry Pi OS Lite to your SD card using Raspberry Pi Imager
2. Enable SSH and configure WiFi before first boot (add `ssh` file and `wpa_supplicant.conf`)
3. Boot the Pi and connect via SSH or directly with keyboard/monitor
4. Update the system:

   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

5. Enable SPI interface:

   ```bash
   sudo raspi-config
   # Navigate to: Interface Options > SPI > Enable
   ```

6. Install system dependencies:
   ```bash
   sudo apt install python3-pip python3-venv git libopenjp2-7 libtiff5 -y
   ```

## Step 2: Create Spotify App

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Log in with your Spotify account
3. Click "Create an App"
4. Fill in the details:
   - App Name: "LoFi Pi Controller"
   - App Description: "Raspberry Pi Zero Spotify Controller"
5. Accept the terms and create the app
6. Note down your **Client ID** and **Client Secret**
7. Click "Edit Settings" and add redirect URI: `http://localhost:8888/callback`

## Step 3: Install LoFi Pi Software

1. Clone or copy the project files to your Pi:

   ```bash
   mkdir ~/lofi-pi
   cd ~/lofi-pi
   # Copy all project files here
   ```

2. Create and activate a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Step 4: Set Up Authentication

1. Edit `config.py` with your credentials:

   ```bash
   nano config.py
   ```

   Update:

   - WiFi SSID and password
   - Spotify Client ID and Client Secret

2. Run the authentication setup script on your computer (not the Pi):

   ```bash
   python setup_spotify_auth.py
   ```

3. Copy the generated `spotify_tokens.json` to your Pi:
   ```bash
   scp spotify_tokens.json pi@your-pi-ip:~/lofi-pi/
   ```

## Step 5: Wire the Hardware

### E-ink Display (SPI)

```
Display Pin → Pi Zero Pin (GPIO)
VCC   → 3.3V (Pin 1)
GND   → GND (Pin 6)
DIN   → GPIO 10 (Pin 19) - MOSI
CLK   → GPIO 11 (Pin 23) - SCLK
CS    → GPIO 8 (Pin 24) - CE0
DC    → GPIO 25 (Pin 22)
RST   → GPIO 17 (Pin 11)
BUSY  → GPIO 24 (Pin 18)
```

### Control Buttons

```
Button        → Pi Zero Pin (GPIO) + GND
Play/Pause    → GPIO 2 (Pin 3)
Next Track    → GPIO 3 (Pin 5)
Previous      → GPIO 4 (Pin 7)
Menu/Mode     → GPIO 14 (Pin 8)
```

### Rotary Encoder

```
Encoder Pin → Pi Zero Pin (GPIO)
CLK   → GPIO 5 (Pin 29)
DT    → GPIO 6 (Pin 31)
SW    → GPIO 13 (Pin 33)
VCC   → 3.3V (Pin 1)
GND   → GND (Pin 9)
```

## Step 6: Test the Setup

1. Test the application manually:

   ```bash
   cd ~/lofi-pi
   source venv/bin/activate
   python main.py
   ```

2. Check for any errors and verify:
   - Display initializes correctly
   - Buttons respond
   - Spotify API connects
   - Track information displays

## Step 7: Set Up Auto-Start Service

1. Create a systemd service file:

   ```bash
   sudo nano /etc/systemd/system/lofi-pi.service
   ```

2. Enable and start the service:

   ```bash
   sudo systemctl enable lofi-pi.service
   sudo systemctl start lofi-pi.service
   ```

3. Check service status:

   ```bash
   sudo systemctl status lofi-pi.service
   ```

4. View logs:
   ```bash
   sudo journalctl -u lofi-pi.service -f
   ```

## Troubleshooting

### Display Issues

- Verify SPI is enabled: `ls /dev/spi*` should show devices
- Check wiring connections, especially power and ground
- Ensure your display model matches the initialization sequence
- Try different SPI speed settings if display is garbled

### GPIO/Button Issues

- Test GPIO access: `sudo python3 -c "import RPi.GPIO as GPIO; print('GPIO OK')"`
- Check button wiring and pull-up resistors
- Verify BCM pin numbering matches your connections
- Use `gpio readall` to check pin states

### Spotify API Issues

- Ensure you have Spotify Premium (required for API control)
- Check internet connectivity
- Verify tokens are valid and not expired
- Re-run authentication setup if needed

### WiFi Connection

- Check `/etc/wpa_supplicant/wpa_supplicant.conf` configuration
- Ensure 2.4GHz network (Pi Zero W doesn't support 5GHz)
- Check signal strength with `iwconfig`

### Performance Issues

- Pi Zero is single-core; consider Pi Zero 2 W for better performance
- Reduce image processing if display updates are slow
- Adjust update intervals in `config.py`

## Power Management

### Battery Operation

- Use a quality USB power bank
- Consider adding a power management HAT
- Implement sleep modes for extended battery life

### Power Consumption Tips

- E-ink displays consume power only when refreshing
- Reduce Spotify API polling frequency
- Disable unnecessary services

## Customization Ideas

### Enhanced Display

- Add weather information
- Show time/date
- Display lyrics (if available via API)
- Custom visualizations

### Additional Controls

- Volume buttons instead of rotary encoder
- Playlist switching buttons
- Shuffle/repeat toggle
- Device switching

### Integration

- MQTT integration for home automation
- Web interface for remote control
- Voice control with speech recognition
- Integration with other music services
