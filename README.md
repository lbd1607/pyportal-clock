# PyPortal Clock

A small wall clock built for an Adafruit PyPortal. It displays the current time and date, adjusts its display theme based on ambient lighting, and synchronizes the device clock using a network time source.

## Overview

This project is a compact, low-glare wall clock intended for a small room. It is designed to be readable at a glance and to remain usable across daylight and evening conditions.

The program does the following:

- shows the current time in a large 12-hour format
- shows the current date in a compact two-line layout
- changes screen brightness and color palette based on the ambient light sensor
- attempts to sync the RTC from `worldtimeapi.org`
- displays a warning banner if the time sync fails

The visual design uses a dark gray/black background and green numerals to create a clean analog-digital look.

## Requirements

For full PyPortal setup instructions, read the [Adafruit PyPortal docs](https://learn.adafruit.com/adafruit-pyportal/overview).

- Adafruit PyPortal
- CircuitPython
- Micro USB cable + power block OR a 5V 2.5A power supply with micro USB
- Wi-Fi network access
- Internet access for time sync
- Files on the CIRCUITPY drive:
  - `code.py`
  - required CircuitPython libraries from the Adafruit bundle (in `lib` folder)
  - a user-created `settings.toml` file with your Wi-Fi credentials

## Required libraries

This project relies on the standard PyPortal CircuitPython environment and imports the following modules:

- `adafruit_requests`
- `analogio`
- `board`
- `displayio`
- `rtc`
- `terminalio`
- `adafruit_display_text.label`

The exact library bundle may vary by CircuitPython release, but the board should have the standard PyPortal-compatible libraries installed in the lib directory. In practice, this includes the typical PyPortal networking and display support files from the Adafruit bundle.

## Configuration

Create your own `settings.toml` file in the root of the CIRCUITPY drive with your Wi-Fi credentials and timezone. This file is not included in the repo and should be created locally for your own board.

Example:

```toml
CIRCUITPY_WIFI_SSID = "Your_Home_WiFi"
CIRCUITPY_WIFI_PASSWORD = "Your_WiFi_Password"
TIMEZONE = "America/Chicago"
```

Replace the sample values with your actual Wi-Fi SSID, password, and timezone.

The program reads `CIRCUITPY_WIFI_SSID` and `CIRCUITPY_WIFI_PASSWORD` from the environment and uses them to connect before requesting time data. If those values are missing or invalid, the app will continue to run but the sync logic will fail and the warning banner will be displayed.

## How to run it on your own PyPortal

1. Install CircuitPython on the PyPortal.
2. Copy `code.py` to the CIRCUITPY drive.
3. Install the required libraries into the lib directory.
4. Create settings.toml at the root of the CIRCUITPY drive with your Wi-Fi credentials and timezone.
5. Reboot the PyPortal. The clock starts up and begins syncing the current time.
