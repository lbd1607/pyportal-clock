import os
import time

import adafruit_requests as requests
import analogio
import board
import displayio
import rtc
import terminalio
from adafruit_display_text.label import Label

try:
    import wifi
except ImportError:
    wifi = None

DAY_LIGHT_THRESHOLD = 20000
NIGHT_LIGHT_THRESHOLD = 12000
TIME_SYNC_INTERVAL_SECONDS = 3600
VIEW_TIME_SECONDS = 18
VIEW_DATE_SECONDS = 10
light_sensor = analogio.AnalogIn(board.LIGHT)
last_sync_attempt = 0
current_view = "time"
last_view_change = time.monotonic()


def load_wifi_credentials():
    """Read Wi-Fi settings from settings.toml."""
    ssid = os.getenv("CIRCUITPY_WIFI_SSID")
    password = os.getenv("CIRCUITPY_WIFI_PASSWORD")
    return ssid or "", password or ""


WIFI_SSID, WIFI_PASSWORD = load_wifi_credentials()


# Create a display group to hold our visual elements
main_group = displayio.Group()
board.DISPLAY.root_group = main_group

# Create the base background color palette and tilegrid.
bg_palette = displayio.Palette(1)
bg_palette[0] = 0x0A0A0A  # Near-black: consistent startup and runtime background
bg_bitmap = displayio.Bitmap(board.DISPLAY.width, board.DISPLAY.height, 1)
bg_tilegrid = displayio.TileGrid(bg_bitmap, pixel_shader=bg_palette)
main_group.append(bg_tilegrid)

# Create the main label that reflects the active lighting mode.
text_label = Label(
    terminalio.FONT,
    text="",
    color=0x7CFF9C,  # Soft green digits for the analog-digital look
    scale=5,
    x=0,
    y=0,
)
text_label.anchor_point = (0.5, 0.5)
text_label.anchored_position = (board.DISPLAY.width // 2, board.DISPLAY.height // 2)
main_group.append(text_label)

warning_banner = Label(
    terminalio.FONT,
    text="",
    color=0xE7A84D,  # Warm amber warning accent
    scale=1,
    x=0,
    y=8,
)
warning_banner.anchor_point = (0.5, 0.0)
warning_banner.anchored_position = (board.DISPLAY.width // 2, 8)
warning_banner.hidden = True
main_group.append(warning_banner)

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
    base_brightness = 0.35 if mode == "night" else 0.7 if mode == "dim" else 1.0

    if mode == "night":
        board.DISPLAY.brightness = base_brightness
        bg_palette[0] = 0x0A0A0A  # Near-black background for low-glare night view
        text_label.color = 0x7CFF9C  # Green numerals for a classic clock glow
        warning_banner.color = 0xE7A84D  # Warm amber warning accent
    elif mode == "dim":
        board.DISPLAY.brightness = base_brightness
        bg_palette[0] = 0x1B1B1B  # Dark gray for dim indoor lighting
        text_label.color = 0x8DFFAC  # Slightly brighter green in dim mode
        warning_banner.color = 0xE7A84D  # Warm amber warning accent
    else:
        board.DISPLAY.brightness = base_brightness
        bg_palette[0] = 0x2A2A2A  # Medium gray for daytime contrast
        text_label.color = 0x7CFF9C  # Green numerals remain the main focal point
        warning_banner.color = 0xE7A84D  # Warm amber remains readable against gray


def set_warning_banner(message):
    """Show or hide the sync warning banner without breaking the UI loop."""
    if message:
        warning_banner.text = message
        warning_banner.hidden = False
    else:
        warning_banner.text = ""
        warning_banner.hidden = True


def format_time_string():
    """Return the current local time in a large, readable 12-hour format."""
    current = time.localtime()
    hour = current[3] % 12 or 12
    minute = current[4]
    meridiem = "AM" if current[3] < 12 else "PM"
    return "{0}:{1:02d} {2}".format(hour, minute, meridiem)


def format_date_string():
    """Return the current date on two lines without the year."""
    current = time.localtime()
    weekdays = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    months = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]
    return "{0}\n{1} {2}".format(
        weekdays[current[6]], months[current[1] - 1], current[2]
    )


def update_main_view():
    """Render either the time or date view and switch on a timed interval."""
    global current_view, last_view_change

    now = time.monotonic()
    duration = VIEW_TIME_SECONDS if current_view == "time" else VIEW_DATE_SECONDS

    if (now - last_view_change) >= duration:
        current_view = "date" if current_view == "time" else "time"
        last_view_change = now

    if current_view == "time":
        text_label.text = format_time_string()
        text_label.scale = 5
        text_label.anchored_position = (
            board.DISPLAY.width // 2,
            board.DISPLAY.height // 2,
        )
    else:
        text_label.text = format_date_string()
        text_label.scale = 3
        text_label.anchored_position = (
            board.DISPLAY.width // 2,
            board.DISPLAY.height // 2,
        )


def sync_time_from_network():
    """Fetch time from a public API and update the RTC without crashing."""
    global last_sync_attempt, WIFI_SSID, WIFI_PASSWORD

    last_sync_attempt = time.monotonic()
    response = None

    try:
        WIFI_SSID, WIFI_PASSWORD = load_wifi_credentials()
        if not WIFI_SSID or not WIFI_PASSWORD or WIFI_SSID.startswith("Your_"):
            raise RuntimeError("Wi-Fi not configured")

        if wifi is not None and not wifi.radio.connected:
            wifi.radio.connect(WIFI_SSID, WIFI_PASSWORD)

        response = requests.get("https://worldtimeapi.org/api/ip", timeout=10)
        payload = response.json()
        if "unixtime" not in payload:
            raise ValueError("Missing unixtime field")
        time_tuple = time.localtime(int(payload["unixtime"]))
        rtc.RTC().datetime = time_tuple
        set_warning_banner("")
        return True
    except Exception:
        set_warning_banner("Warning: Sync Failed")
        return False
    finally:
        if response is not None:
            try:
                response.close()
            except Exception:
                pass


sync_time_from_network()
update_main_view()

while True:
    current_light = get_ambient_lighting()
    apply_light_theme(current_light)
    update_main_view()

    if (time.monotonic() - last_sync_attempt) >= TIME_SYNC_INTERVAL_SECONDS:
        sync_time_from_network()

    time.sleep(0.25)
