"""Constants for the Mitsubishi Lossnay (Melview) integration."""

DOMAIN = "melview_lossnay"

CONF_APP_VERSION = "app_version"
DEFAULT_APP_VERSION = "3.3.838"
DEFAULT_SCAN_INTERVAL = 30

BASE_URL = "https://api.melview.net/api"

PLATFORMS = ["fan", "select", "sensor", "calendar", "binary_sensor", "switch", "number", "button"]

MODE_TO_COMMAND = {
    "Lossnay": "MD1",
    "Auto Lossnay": "MD3",
    "Bypass": "MD7",
}
MODE_VALUE_TO_NAME = {
    1: "Lossnay",
    3: "Auto Lossnay",
    7: "Bypass",
}

# Confirmed against LGH-35RVX3-E via Melview live control.
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
FAN_PRESET_TO_VALUE = {
    "Auto": 0,
    "Speed 1": 2,
    "Speed 2": 3,
    "Speed 3": 5,
    "Speed 4": 6,
}
FAN_VALUE_TO_PRESET = {value: name for name, value in FAN_PRESET_TO_VALUE.items()}

# Lossnay heat-recovery efficiency figures used by the Mitsubishi app for each
# fixed fan stage. The Melview API encodes Speed 1-4 as 2, 3, 5 and 6.
# Auto fan has no single fixed efficiency, so the API-provided coreefficiency
# value is used as a fallback when available.
FAN_VALUE_TO_HEAT_RECOVERY = {
    2: 82,
    3: 79,
    5: 77,
    6: 75,
}

# Native Melview ERV schedule encoding discovered from schedule.aspx.
SCHEDULE_MODE_VALUE_TO_NAME = {
    0: "Power Off",
    11: "Lossnay",
    13: "Auto",
    17: "Bypass",
}
SCHEDULE_FAN_VALUE_TO_NAME = {
    -1: "Keep fan speed",
    1: "Speed 1",
    2: "Speed 2",
    3: "Speed 3",
    4: "Speed 4",
}

# Melview weekday bitmask: Sunday=1 through Saturday=64.
SCHEDULE_WEEKDAY_BITS = {
    6: 1,   # Sunday in Python weekday numbering is 6
    0: 2,   # Monday
    1: 4,   # Tuesday
    2: 8,   # Wednesday
    3: 16,  # Thursday
    4: 32,  # Friday
    5: 64,  # Saturday
}
