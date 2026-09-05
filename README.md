# Mitsubishi Lossnay (Melview) for Home Assistant

A HACS-compatible custom Home Assistant integration for Mitsubishi Electric Lossnay ERVs connected to the Australia/New Zealand **Melview / Wi-Fi Control** service.

This integration was built and tested around:

- **Lossnay:** LGH-35RVX3-E
- **Wi-Fi interface:** MAC-588IF-E - **Melview device type:** `ERV`

## Features

- Power on/off
- Fan Auto and fan speeds 1-4
- Heat Recovery / Lossnay mode
- Auto ventilation mode
- Bypass mode
- Indoor temperature
- Outdoor temperature
- Supply-air temperature
- Exhaust-air temperature
- Core-efficiency diagnostic
- Fault diagnostic
- UI-based configuration; no `configuration.yaml` setup required

## Confirmed command mapping

| Function | Melview command |
|---|---|
| Power on | `PW1` |
| Power off | `PW0` |
| Heat Recovery / Lossnay | `MD1` |
| Auto ventilation | `MD3` |
| Bypass | `MD7` |
| Fan Auto | `FS0` |
| Fan 1 | `FS2` |
| Fan 2 | `FS3` |
| Fan 3 | `FS5` |
| Fan 4 | `FS6` |

## Install with HACS

HACS custom repositories must be hosted at a Git repository URL, normally GitHub. This ZIP is laid out as a complete repository ready to upload.

1. Create a new GitHub repository, for example `home-assistant-melview-lossnay`.
2. Upload the **contents of this package to the repository root**. The repository root must contain `hacs.json`, `README.md`, and the `custom_components` folder.
3. In Home Assistant open **HACS > Integrations**.
4. Open the HACS menu and choose **Custom repositories**.
5. Paste the GitHub repository URL.
6. Select category **Integration** and add it.
7. Search HACS for **Mitsubishi Lossnay (Melview)** and install it.
8. Restart Home Assistant.
9. Open **Settings > Devices & services > Add Integration** and search for **Mitsubishi Lossnay (Melview)**.
10. Sign in with the same credentials used by the Mitsubishi Electric AU/NZ Wi-Fi Control app.

## Repository layout

```text
home-assistant-melview-lossnay/
├── hacs.json
├── README.md
└── custom_components/
    └── melview_lossnay/
        ├── __init__.py
        ├── api.py
        ├── config_flow.py
        ├── const.py
        ├── coordinator.py
        ├── entity.py
        ├── fan.py
        ├── manifest.json
        ├── select.py
        ├── sensor.py
        ├── strings.json
        └── translations/
            └── en.json
```

## Notes

- This uses the Melview cloud API at `api.melview.net`; it is not an ECHONET Lite integration.
- It polls Melview every 30 seconds.
- Your Wi-Fi Control credentials are stored in the Home Assistant config entry.
- `coreefficiency` is exposed as diagnostic data because Mitsubishi's exact semantic for this API property has not been confirmed.
- Command mappings are confirmed for the LGH-35RVX3-E. Other Lossnay models may work but are not currently verified.

## Troubleshooting

Temporarily enable debug logging:

```yaml
logger:
  logs:
    custom_components.melview_lossnay: debug
```

Restart Home Assistant, reproduce the problem, and inspect **Settings > System > Logs**.

Do not share your password or authentication cookie when posting logs.

## v0.1.1

- Added a visible **Fan speed** selector with Auto and Speed 1-4.
- Fan entity now exposes all five fan settings as preset modes.
- Retains Home Assistant percentage control for the four fixed fan stages.

## Native Melview schedules

Version 0.2.0 adds read-only Home Assistant calendar support for native Melview schedules. Existing weekly Lossnay schedule events from `schedule.aspx` are expanded into Home Assistant calendar events and can be shown on a Calendar card or used as calendar automation triggers.

Confirmed native schedule encoding:

- Power Off: `mode=0`
- Power On + Lossnay: `mode=11`
- Power On + Auto: `mode=13`
- Power On + Bypass: `mode=17`
- Fan 1-4: `fanspeed=1..4`
- Keep current fan speed: `fanspeed=-1`

Schedule creation/edit/delete is intentionally not enabled yet because the Melview write payload has not been confirmed.


## Melview API notes

Reverse-engineered endpoint and command documentation is available in [MELVIEW_API.md](MELVIEW_API.md).
