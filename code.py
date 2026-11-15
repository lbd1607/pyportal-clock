import time

import adafruit_requests as requests
import analogio
import board
import displayio
import rtc
import terminalio
from adafruit_display_text.label import Label

DAY_LIGHT_THRESHOLD = 20000
NIGHT_LIGHT_THRESHOLD = 12000
TIME_SYNC_INTERVAL_SECONDS = 3600

light_sensor = analogio.AnalogIn(board.LIGHT)
last_sync_attempt = 0


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

warning_banner = Label(
    terminalio.FONT,
    text="",
    color=0xF5A623,  # Warm amber that reads without clashing
    scale=1,
    x=0,
    y=8,
)
warning_banner.anchor_point = (0.5, 0.0)
warning_banner.anchored_position = (board.DISPLAY.width // 2, 8)
warning_banner.hidden = True
main_group.append(warning_banner)

VIEW_TIME_SECONDS = 10
VIEW_DATE_SECONDS = 5
current_view = "time"
last_view_change = time.monotonic()


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
        warning_banner.color = 0xF5A623  # Warm amber that reads without clashing
    elif mode == "dim":
        board.DISPLAY.brightness = 0.7
        bg_palette[0] = 0x1F4E79  # Muted blue-gray for dim/indoor lighting
        text_label.color = 0xEAF5FF  # Gentle blue-white text
        warning_banner.color = 0xF0A64A  # Slightly softer orange for dim mode
    else:
        board.DISPLAY.brightness = 1.0
        bg_palette[0] = 0x0D5D9C  # Strong blue for daytime contrast
        text_label.color = 0xF5F9FF  # Bright white text
        warning_banner.color = 0xF5A623  # Warm amber remains readable on blue


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
    """Return the current date in a friendly, full-text format."""
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
    return "{0}, {1} {2}, {3}".format(
        weekdays[current[6]], months[current[1] - 1], current[2], current[0]
    )


def animate_view_transition(new_view):
    """Slide the main label while swapping between clock and date."""
    global current_view

    current_view = new_view
    for offset in range(0, 28, 4):
        text_label.x = offset
        time.sleep(0.02)
    for offset in range(28, -28, -4):
        text_label.x = offset
        time.sleep(0.02)
    text_label.x = 0


def update_main_view():
    """Render either the time or date view and switch on a timed interval."""
    global current_view, last_view_change

    now = time.monotonic()
    duration = VIEW_TIME_SECONDS if current_view == "time" else VIEW_DATE_SECONDS

    if (now - last_view_change) >= duration:
        next_view = "date" if current_view == "time" else "time"
        animate_view_transition(next_view)
        last_view_change = now

    if current_view == "time":
        text_label.text = format_time_string()
        text_label.scale = 4
    else:
        text_label.text = format_date_string()
        text_label.scale = 2


def sync_time_from_network():
    """Fetch time from a public API and update the RTC without crashing."""
    global last_sync_attempt

    last_sync_attempt = time.monotonic()

    try:
        response = requests.get("https://worldtimeapi.org/api/ip")
        payload = response.json()
        response.close()

        time_tuple = time.localtime(int(payload["unixtime"]))
        rtc.RTC().datetime = time_tuple
        set_warning_banner("")
        return True
    except Exception:
        set_warning_banner("Warning: Sync Failed")
        return False


sync_time_from_network()
update_main_view()

while True:
    current_light = get_ambient_lighting()
    apply_light_theme(current_light)
    update_main_view()

    if (time.monotonic() - last_sync_attempt) >= TIME_SYNC_INTERVAL_SECONDS:
        sync_time_from_network()

    time.sleep(0.25)