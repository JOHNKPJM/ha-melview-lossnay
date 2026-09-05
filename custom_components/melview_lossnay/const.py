"""Constants for the Mitsubishi Lossnay (Melview) integration."""

DOMAIN = "melview_lossnay"

CONF_APP_VERSION = "app_version"
DEFAULT_APP_VERSION = "3.3.838"
DEFAULT_SCAN_INTERVAL = 30

BASE_URL = "https://api.melview.net/api"

PLATFORMS = ["fan", "select", "sensor"]

MODE_TO_COMMAND = {
    "Heat Recovery": "MD1",
    "Auto": "MD3",
    "Bypass": "MD7",
}
MODE_VALUE_TO_NAME = {
    1: "Heat Recovery",
    3: "Auto",
    7: "Bypass",
}

# Confirmed against LGH-35RVX3-E via Melview.
FAN_VALUE_TO_PERCENTAGE = {
    2: 25,
    3: 50,
    5: 75,
    6: 100,
}
PERCENTAGE_TO_FAN_VALUE = {
    25: 2,
    50: 3,
    75: 5,
    100: 6,
}
FAN_AUTO_VALUE = 0
FAN_AUTO_PRESET = "Auto"

# Confirmed Lossnay fan values (LGH-35RVX3-E).
FAN_PRESET_TO_VALUE = {
    "Auto": 0,
    "Speed 1": 2,
    "Speed 2": 3,
    "Speed 3": 5,
    "Speed 4": 6,
}
FAN_VALUE_TO_PRESET = {value: name for name, value in FAN_PRESET_TO_VALUE.items()}
