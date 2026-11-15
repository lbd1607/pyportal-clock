import time

import analogio
import board
import displayio
import terminalio
from adafruit_display_text.label import Label

DAY_LIGHT_THRESHOLD = 20000
NIGHT_LIGHT_THRESHOLD = 12000

light_sensor = analogio.AnalogIn(board.LIGHT)


# Create a display group to hold our visual elements
main_group = displayio.Group()
board.DISPLAY.root_group = main_group

# Create the base background color palette and tilegrid.
bg_palette = displayio.Palette(1)
bg_palette[0] = 0x0D5D9C  # Deep blue: default day mode
bg_bitmap = displayio.Bitmap(board.DISPLAY.width, board.DISPLAY.height, 1)
bg_tilegrid = displayio.TileGrid(bg_bitmap, pixel_shader=bg_palette)
main_group.append(bg_tilegrid)

# Create the main label that reflects the active lighting mode.
text_label = Label(
    terminalio.FONT,
    text="Clock",
    color=0xF5F9FF,
    scale=4,
    x=0,
    y=0,
)
text_label.anchor_point = (0.5, 0.5)
text_label.anchored_position = (
    board.DISPLAY.width // 2,
    board.DISPLAY.height // 2,
)
text_label.x = 30
text_label.y = 30
main_group.append(text_label)


def get_ambient_lighting():
    """Return the raw analog value from the PyPortal light sensor."""
    return light_sensor.value


def get_light_mode(light_level):
    """Return the current display mode based on the ambient lighting level."""
    if light_level < NIGHT_LIGHT_THRESHOLD:
        return "night"
    if light_level < DAY_LIGHT_THRESHOLD:
        return "dim"
    return "day"


def apply_light_theme(light_level):
    """Update the screen backlight and UI palette based on ambient light."""
    mode = get_light_mode(light_level)

    if mode == "night":
        board.DISPLAY.brightness = 0.35
        bg_palette[0] = 0x102A43  # Dark navy-blue for low-glare night view
        text_label.color = 0xD9ECFF  # Soft cool white text
        text_label.text = "Night Mode"
    elif mode == "dim":
        board.DISPLAY.brightness = 0.7
        bg_palette[0] = 0x1F4E79  # Muted blue-gray for dim/indoor lighting
        text_label.color = 0xEAF5FF  # Gentle blue-white text
        text_label.text = "Low Light"
    else:
        board.DISPLAY.brightness = 1.0
        bg_palette[0] = 0x0D5D9C  # Strong blue for daytime contrast
        text_label.color = 0xF5F9FF  # Bright white text
        text_label.text = "Day Mode"


while True:
    current_light = get_ambient_lighting()
    apply_light_theme(current_light)
    time.sleep(2)