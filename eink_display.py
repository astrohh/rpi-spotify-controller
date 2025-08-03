"""
E-ink Display Driver for LoFi Pi (Raspberry Pi Zero)
Supports 2.13" e-Paper displays (250x122 resolution)
"""

import os
import time
import spidev
import requests
from io import BytesIO
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw, ImageFont


class EInkDisplay:
    def __init__(self):
        # Display dimensions
        self.width = 250
        self.height = 122

        # GPIO pin assignments (BCM numbering)
        self.RST_PIN = 17
        self.DC_PIN = 25
        self.CS_PIN = 8
        self.BUSY_PIN = 24

        # Initialize GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.RST_PIN, GPIO.OUT)
        GPIO.setup(self.DC_PIN, GPIO.OUT)
        GPIO.setup(self.CS_PIN, GPIO.OUT)
        GPIO.setup(self.BUSY_PIN, GPIO.IN)

        # Initialize SPI
        self.spi = spidev.SpiDev()
        self.spi.open(0, 0)  # Bus 0, Device 0
        self.spi.max_speed_hz = 4000000
        self.spi.mode = 0

        # Create image buffer
        self.image = Image.new(
            "1", (self.width, self.height), 255
        )  # 1-bit image, white background
        self.draw = ImageDraw.Draw(self.image)

        # Load fonts (fallback to default if not available)
        try:
            self.font_large = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16
            )
            self.font_medium = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12
            )
            self.font_small = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10
            )
        except:
            self.font_large = ImageFont.load_default()
            self.font_medium = ImageFont.load_default()
            self.font_small = ImageFont.load_default()

        # Current display mode
        self.display_mode = 0  # 0: Track info, 1: Volume, 2: Clock

        # Album art cache
        self.album_art_cache = {}

        # Initialize display
        self.init_display()
        print("E-ink display initialized")

    def init_display(self):
        """Initialize the e-ink display"""
        self.reset()
        self.wait_until_idle()

        # Software reset
        self.send_command(0x12)
        self.wait_until_idle()

        # Set display settings (adjust for your specific display model)
        self.send_command(0x01)  # Driver output control
        self.send_data([0xF9, 0x00, 0x00])

        self.send_command(0x11)  # Data entry mode
        self.send_data([0x01])

        self.send_command(0x44)  # Set RAM X address
        self.send_data([0x00, 0x0F])

        self.send_command(0x45)  # Set RAM Y address
        self.send_data([0xF9, 0x00, 0x00, 0x00])

        self.send_command(0x3C)  # Border waveform
        self.send_data([0x03])

        self.send_command(0x2C)  # VCOM value
        self.send_data([0x55])

        self.send_command(0x03)  # Gate voltage
        self.send_data([0x15])

        self.send_command(0x04)  # Source voltage
        self.send_data([0x41, 0xA8, 0x32])

        self.send_command(0x3A)  # Dummy line period
        self.send_data([0x30])

        self.send_command(0x3B)  # Gate line width
        self.send_data([0x0A])

        self.send_command(0x32)  # LUT
        self.send_data(
            [
                0x50,
                0xAA,
                0x55,
                0xAA,
                0x11,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0xFF,
                0xFF,
                0x1F,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
            ]
        )

        self.wait_until_idle()

    def reset(self):
        """Hardware reset"""
        GPIO.output(self.RST_PIN, GPIO.HIGH)
        time.sleep(0.2)
        GPIO.output(self.RST_PIN, GPIO.LOW)
        time.sleep(0.002)
        GPIO.output(self.RST_PIN, GPIO.HIGH)
        time.sleep(0.2)

    def send_command(self, command):
        """Send command to display"""
        GPIO.output(self.DC_PIN, GPIO.LOW)
        GPIO.output(self.CS_PIN, GPIO.LOW)
        self.spi.writebytes([command])
        GPIO.output(self.CS_PIN, GPIO.HIGH)

    def send_data(self, data):
        """Send data to display"""
        GPIO.output(self.DC_PIN, GPIO.HIGH)
        GPIO.output(self.CS_PIN, GPIO.LOW)
        if isinstance(data, list):
            self.spi.writebytes(data)
        else:
            self.spi.writebytes([data])
        GPIO.output(self.CS_PIN, GPIO.HIGH)

    def wait_until_idle(self):
        """Wait for display to finish current operation"""
        while GPIO.input(self.BUSY_PIN) == 1:
            time.sleep(0.01)

    def clear(self):
        """Clear the display buffer"""
        self.draw.rectangle((0, 0, self.width, self.height), fill=255)

    def show_message(self, title, message):
        """Display a simple message"""
        self.clear()

        # Draw title
        self.draw.text((10, 20), title, font=self.font_large, fill=0)

        # Draw message with word wrapping
        if message:
            words = message.split(" ")
            lines = []
            current_line = ""

            for word in words:
                test_line = current_line + word + " "
                bbox = self.draw.textbbox((0, 0), test_line, font=self.font_medium)
                if bbox[2] < 230:  # Width check
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line.strip())
                    current_line = word + " "

            if current_line:
                lines.append(current_line.strip())

            # Display lines
            y_pos = 50
            for line in lines[:3]:  # Max 3 lines
                self.draw.text((10, y_pos), line, font=self.font_medium, fill=0)
                y_pos += 20

        self.refresh()

    def show_track(self, track_info):
        """Display current track information with album art"""
        self.clear()

        # Get album art
        album_art = self.get_album_art(track_info.get("image_url"))

        if album_art:
            # Display album art on the right side (60x60 pixels)
            art_size = 60
            art_x = self.width - art_size - 10
            art_y = 10

            # Resize and paste album art
            album_art_resized = album_art.resize(
                (art_size, art_size), Image.Resampling.LANCZOS
            )
            # Convert to 1-bit and paste
            album_art_1bit = album_art_resized.convert("1")
            self.image.paste(album_art_1bit, (art_x, art_y))

            # Adjust text area to avoid overlap
            text_width = art_x - 20
        else:
            text_width = self.width - 20

        # Track title (truncate if too long)
        title = track_info.get("name", "Unknown")
        title = self.truncate_text(title, self.font_large, text_width)
        self.draw.text((10, 10), title, font=self.font_large, fill=0)

        # Artist
        artist = track_info.get("artist", "Unknown Artist")
        artist = self.truncate_text(artist, self.font_medium, text_width)
        self.draw.text((10, 30), artist, font=self.font_medium, fill=0)

        # Album
        album = track_info.get("album", "Unknown Album")
        album = self.truncate_text(album, self.font_small, text_width)
        self.draw.text((10, 50), album, font=self.font_small, fill=0)

        # Progress bar
        duration = track_info.get("duration", 0)
        progress = track_info.get("progress", 0)

        if duration > 0:
            progress_ratio = progress / duration
            bar_width = 200
            bar_height = 4
            bar_x = 10
            bar_y = 80

            # Draw progress bar background
            self.draw.rectangle(
                (bar_x, bar_y, bar_x + bar_width, bar_y + bar_height), fill=0, outline=0
            )

            # Draw progress
            progress_width = int(bar_width * progress_ratio)
            if progress_width > 2:
                self.draw.rectangle(
                    (
                        bar_x + 1,
                        bar_y + 1,
                        bar_x + progress_width - 1,
                        bar_y + bar_height - 1,
                    ),
                    fill=255,
                )

        # Time display
        progress_min = (progress // 1000) // 60
        progress_sec = (progress // 1000) % 60
        duration_min = (duration // 1000) // 60
        duration_sec = (duration // 1000) % 60

        time_str = (
            f"{progress_min}:{progress_sec:02d} / {duration_min}:{duration_sec:02d}"
        )
        self.draw.text((10, 95), time_str, font=self.font_small, fill=0)

        self.refresh()

    def get_album_art(self, image_url):
        """Download and cache album art"""
        if not image_url:
            return None

        # Check cache first
        if image_url in self.album_art_cache:
            return self.album_art_cache[image_url]

        try:
            # Download image
            response = requests.get(image_url, timeout=5)
            if response.status_code == 200:
                image = Image.open(BytesIO(response.content))

                # Cache the image (limit cache size)
                if len(self.album_art_cache) > 10:
                    # Remove oldest entry
                    oldest_key = next(iter(self.album_art_cache))
                    del self.album_art_cache[oldest_key]

                self.album_art_cache[image_url] = image
                return image

        except Exception as e:
            print(f"Error downloading album art: {e}")

        return None

    def truncate_text(self, text, font, max_width):
        """Truncate text to fit within max_width"""
        bbox = self.draw.textbbox((0, 0), text, font=font)
        if bbox[2] <= max_width:
            return text

        # Binary search for the right length
        left, right = 0, len(text)
        while left < right:
            mid = (left + right + 1) // 2
            test_text = text[:mid] + "..."
            bbox = self.draw.textbbox((0, 0), test_text, font=font)
            if bbox[2] <= max_width:
                left = mid
            else:
                right = mid - 1

        return text[:left] + "..." if left < len(text) else text

    def show_volume(self, volume):
        """Display volume level"""
        self.clear()

        # Volume text
        self.draw.text((10, 30), "Volume", font=self.font_large, fill=0)
        self.draw.text((10, 55), f"{volume}%", font=self.font_large, fill=0)

        # Volume bar
        bar_width = 180
        bar_height = 20
        bar_x = 30
        bar_y = 80

        # Draw bar background
        self.draw.rectangle(
            (bar_x, bar_y, bar_x + bar_width, bar_y + bar_height), fill=255, outline=0
        )

        # Draw volume level
        volume_width = int((volume / 100) * (bar_width - 4))
        if volume_width > 0:
            self.draw.rectangle(
                (
                    bar_x + 2,
                    bar_y + 2,
                    bar_x + 2 + volume_width,
                    bar_y + bar_height - 2,
                ),
                fill=0,
            )

        self.refresh()

    def toggle_mode(self):
        """Toggle between different display modes"""
        self.display_mode = (self.display_mode + 1) % 3

        if self.display_mode == 0:
            self.show_message("Mode", "Track Info")
        elif self.display_mode == 1:
            self.show_message("Mode", "Volume Display")
        elif self.display_mode == 2:
            self.show_message("Mode", "Clock Mode")

    def refresh(self):
        """Refresh the display with current buffer content"""
        # Convert PIL image to display buffer
        buffer = []
        for y in range(self.height):
            for x in range(0, self.width, 8):
                byte = 0
                for bit in range(8):
                    if x + bit < self.width:
                        pixel = self.image.getpixel((x + bit, y))
                        if pixel == 0:  # Black pixel
                            byte |= 1 << (7 - bit)
                buffer.append(byte)

        # Set memory area
        self.send_command(0x4E)
        self.send_data([0x00])

        self.send_command(0x4F)
        self.send_data([0xF9, 0x00])

        # Send buffer data
        self.send_command(0x24)
        for i in range(0, len(buffer), 4096):  # Send in chunks
            chunk = buffer[i : i + 4096]
            self.send_data(chunk)

        # Update display
        self.send_command(0x22)
        self.send_data([0xC7])

        self.send_command(0x20)
        self.wait_until_idle()

    def cleanup(self):
        """Clean up GPIO and SPI"""
        try:
            self.spi.close()
            GPIO.cleanup()
        except:
            pass
