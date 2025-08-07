"""
E-ink Display Module for LoFi Pi
Wraps the Waveshare 2.13" B/W/Red display driver for easier use
"""

import os
import sys
import time
import logging

# Add lib directory to path
lib_dir = os.path.join(os.path.dirname(__file__), "lib")
if lib_dir not in sys.path:
    sys.path.insert(0, lib_dir)

from lib import epdconfig
from lib import epd_2in13b as epd_module
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


class EInkDisplay:
    """Simplified interface for the Waveshare 2.13" e-ink display"""

    def __init__(self, gpio_initialized=False):
        self.epd = None
        self.width = 122
        self.height = 250
        self.gpio_initialized = gpio_initialized

        # Display modes
        self.current_mode = "track"  # track, volume, message

    def initialize(self):
        """Initialize the e-ink display"""
        try:
            if not self.gpio_initialized:
                result = epdconfig.module_init()
                if result != 0:
                    raise Exception(f"Failed to initialize display module: {result}")

            self.epd = epd_module.EPD()
            logger.info("E-ink display initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize e-ink display: {e}")
            return False

    def clear(self):
        """Clear the display to white"""
        if not self.epd:
            logger.warning("Display not initialized")
            return

        try:
            self.epd.init()
            self.epd.Clear()
            logger.info("Display cleared")
        except Exception as e:
            logger.error(f"Failed to clear display: {e}")

    def show_track(self, track_info):
        """Display track information"""
        if not self.epd:
            if not self.initialize():
                return

        try:
            # Create black image (main content)
            black_image = Image.new("1", (self.height, self.width), 255)  # 250x122
            draw = ImageDraw.Draw(black_image)

            # Try to load fonts, fall back to default
            try:
                font_large = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16
                )
                font_medium = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14
                )
                font_small = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12
                )
            except:
                font_large = ImageFont.load_default()
                font_medium = ImageFont.load_default()
                font_small = ImageFont.load_default()

            # Draw track info
            y_pos = 5

            # Song title (truncate if too long)
            title = track_info.get("name", "Unknown Track")
            if len(title) > 20:
                title = title[:17] + "..."
            draw.text((5, y_pos), title, font=font_large, fill=0)
            y_pos += 20

            # Artist
            artist = track_info.get("artist", "Unknown Artist")
            if len(artist) > 25:
                artist = artist[:22] + "..."
            draw.text((5, y_pos), f"by {artist}", font=font_medium, fill=0)
            y_pos += 18

            # Album
            album = track_info.get("album", "Unknown Album")
            if len(album) > 25:
                album = album[:22] + "..."
            draw.text((5, y_pos), album, font=font_small, fill=0)
            y_pos += 20

            # Progress bar
            duration = track_info.get("duration", 0)
            progress = track_info.get("progress", 0)

            if duration > 0:
                bar_width = self.height - 20
                bar_height = 6
                progress_width = int((progress / duration) * bar_width)

                # Progress bar background
                draw.rectangle(
                    [10, y_pos, 10 + bar_width, y_pos + bar_height], outline=0
                )
                # Progress bar fill
                if progress_width > 0:
                    draw.rectangle(
                        [10, y_pos, 10 + progress_width, y_pos + bar_height], fill=0
                    )

                y_pos += 15

                # Time display
                progress_min = progress // 60000
                progress_sec = (progress % 60000) // 1000
                duration_min = duration // 60000
                duration_sec = (duration % 60000) // 1000

                time_text = f"{progress_min}:{progress_sec:02d} / {duration_min}:{duration_sec:02d}"
                draw.text((10, y_pos), time_text, font=font_small, fill=0)

            # Create red/yellow image (for highlights - empty for now)
            red_image = Image.new("1", (self.height, self.width), 255)

            # Display the images
            self.epd.init()
            self.epd.display(
                self.epd.getbuffer(black_image), self.epd.getbuffer(red_image)
            )

            self.current_mode = "track"
            logger.info(f"Displayed track: {title}")

        except Exception as e:
            logger.error(f"Failed to show track: {e}")

    def show_volume(self, volume_level):
        """Display volume level"""
        if not self.epd:
            if not self.initialize():
                return

        try:
            black_image = Image.new("1", (self.height, self.width), 255)
            draw = ImageDraw.Draw(black_image)

            try:
                font_large = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24
                )
                font_medium = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16
                )
            except:
                font_large = ImageFont.load_default()
                font_medium = ImageFont.load_default()

            # Volume text
            draw.text((50, 20), "Volume", font=font_large, fill=0)

            # Volume bar
            bar_width = self.height - 40
            bar_height = 20
            filled_width = int(bar_width * (volume_level / 100))

            y_pos = 60

            # Volume bar background
            draw.rectangle([20, y_pos, 20 + bar_width, y_pos + bar_height], outline=0)
            # Volume bar fill
            if filled_width > 0:
                draw.rectangle(
                    [20, y_pos, 20 + filled_width, y_pos + bar_height], fill=0
                )

            # Volume percentage
            draw.text((90, y_pos + 30), f"{volume_level}%", font=font_medium, fill=0)

            red_image = Image.new("1", (self.height, self.width), 255)

            self.epd.init()
            self.epd.display(
                self.epd.getbuffer(black_image), self.epd.getbuffer(red_image)
            )

            self.current_mode = "volume"
            logger.info(f"Displayed volume: {volume_level}%")

        except Exception as e:
            logger.error(f"Failed to show volume: {e}")

    def show_message(self, title, message):
        """Display a simple message"""
        if not self.epd:
            if not self.initialize():
                return

        try:
            black_image = Image.new("1", (self.height, self.width), 255)
            draw = ImageDraw.Draw(black_image)

            try:
                font_large = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18
                )
                font_medium = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14
                )
            except:
                font_large = ImageFont.load_default()
                font_medium = ImageFont.load_default()

            # Title
            draw.text((10, 30), title, font=font_large, fill=0)

            # Message (wrap if needed)
            lines = []
            words = message.split(" ")
            current_line = ""

            for word in words:
                test_line = current_line + (" " if current_line else "") + word
                if len(test_line) <= 25:  # Approximate character limit
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word

            if current_line:
                lines.append(current_line)

            y_pos = 55
            for line in lines[:3]:  # Max 3 lines
                draw.text((10, y_pos), line, font=font_medium, fill=0)
                y_pos += 18

            red_image = Image.new("1", (self.height, self.width), 255)

            self.epd.init()
            self.epd.display(
                self.epd.getbuffer(black_image), self.epd.getbuffer(red_image)
            )

            self.current_mode = "message"
            logger.info(f"Displayed message: {title}")

        except Exception as e:
            logger.error(f"Failed to show message: {e}")

    def toggle_mode(self):
        """Toggle between display modes (for menu button)"""
        # This can be expanded based on your needs
        logger.info(f"Display mode toggle (current: {self.current_mode})")

    def sleep(self):
        """Put display to sleep"""
        if self.epd:
            try:
                self.epd.sleep()
                logger.info("Display put to sleep")
            except Exception as e:
                logger.error(f"Failed to put display to sleep: {e}")

    def cleanup(self):
        """Clean up display resources"""
        try:
            if self.epd:
                self.epd.sleep()
            if not self.gpio_initialized:
                epdconfig.module_exit()
            logger.info("Display cleanup completed")
        except Exception as e:
            logger.error(f"Error during display cleanup: {e}")
