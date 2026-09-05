# Mitsubishi Lossnay (Melview) for Home Assistant

A Home Assistant custom integration for Mitsubishi Electric **Lossnay ERV** systems connected through the Australia/New Zealand **Melview / Mitsubishi Electric Wi-Fi Control** service.

The integration is designed for HACS and uses the same Melview account as the Mitsubishi Electric Wi-Fi Control app. It brings Lossnay power, fan control, ventilation modes, airflow temperatures, heat-recovery information, diagnostics, and scheduling into Home Assistant.

> **Status:** Experimental/community integration. The Melview API is unofficial and reverse-engineered, so behaviour may vary by Lossnay model, Wi-Fi adapter, firmware, account, or region.

## What you get

### Main Lossnay control

The primary Home Assistant **fan entity** provides:

- Power on/off
- Four stepped fan speeds through Home Assistant's native fan-speed control
  - 25% = Speed 1
  - 50% = Speed 2
  - 75% = Speed 3
  - 100% = Speed 4
- **Auto** fan-speed preset
- A state-aware icon that follows the current ventilation mode

This makes the entity work well with Home Assistant Tile cards and other fan-aware dashboard cards, including slider/dial style speed controls where the selected frontend supports them.

A separate **Fan speed** dropdown remains available for backwards compatibility. It is disabled by default on new installs because the main fan entity now provides the richer native control.

### Ventilation mode

The **Ventilation mode** selector follows the Mitsubishi app terminology:

- **Lossnay** - heat recovery
- **Auto Lossnay** - automatic Lossnay/bypass operation
- **Bypass** - bypass the heat exchanger

The entity icon changes with the selected mode:

- Lossnay: heat-recovery style icon
- Auto Lossnay: automatic/circulating icon
- Bypass: straight-through airflow icon

### Lossnay Core temperatures

Temperature names now match the Mitsubishi app:

| Home Assistant | Melview/API value | Meaning |
| --- | --- | --- |
| **Fresh Air In** | `outdoortemp` | Outside air entering the unit |
| **Stale Air Out** | `roomtemp` | Indoor/return air entering the unit |
| **Exhaust Air** | calculated, with `exhausttemp` fallback | Air being exhausted outdoors |
| **Pre-warmed** | calculated, with `supplytemp` fallback | Conditioned fresh air supplied indoors |

Existing entity unique IDs are retained for upgrades, so renaming these display names does not intentionally create duplicate temperature entities.

### Heat recovery

The integration exposes **Heat recovery efficiency** using the fixed fan-stage values used by the Mitsubishi app:

| Fan speed | Heat recovery |
| --- | ---: |
| Speed 1 | 82% |
| Speed 2 | 79% |
| Speed 3 | 77% |
| Speed 4 | 75% |

For **Auto** fan speed, the integration falls back to the `coreefficiency` value reported by Melview when available.

When the unit is explicitly in **Bypass**, heat recovery is reported as `0%`. When the unit is off, the heat-recovery sensor has no active value.

The integration uses the active fan-stage efficiency to reproduce the app's two Lossnay Core temperatures from **Fresh Air In** and **Stale Air Out**. If the required inputs are unavailable, it falls back to Melview's `supplytemp` and `exhausttemp` fields.

The integration also exposes **Incoming air temperature change**, calculated as:

```text
Pre-warmed - Fresh Air In
```

For example, Fresh Air In at `14.0 C` and Pre-warmed at `15.6 C` gives an incoming-air increase of `1.6 C`, matching the style of information shown by the Mitsubishi app.

### Diagnostics

- Fault/status
- Model and adapter information discovered from Melview
- Raw state continues to be polled from the Lossnay through Melview

## Scheduling

The integration provides two schedule calendars.

### Home Assistant schedule

The **Home Assistant schedule** is writable. Events created in Home Assistant can directly control the Lossnay using the same Melview commands as the normal entities.

Example event titles:

```text
Power Off
Auto Lossnay
Auto Lossnay | Speed 1
Auto Lossnay | Speed 2
Auto Lossnay | Speed 3
Auto Lossnay | Speed 4
Auto Lossnay | Auto
Bypass | Speed 1
Lossnay | Speed 1
Lossnay | Speed 4
```

For backwards compatibility, schedule parsing also accepts:

```text
Auto
Heat Recovery
```

These are interpreted as **Auto Lossnay** and **Lossnay** respectively.

If the title contains only a ventilation mode, the current fan speed is left unchanged:

```text
Auto Lossnay
Bypass
Lossnay
```

You can alternatively put commands in the event description:

```text
mode=Auto Lossnay
fan=Speed 2
```

or:

```text
power=off
```

Weekly recurring events are supported when Home Assistant supplies a weekly RFC5545 recurrence rule, for example:

```text
FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR
```

### Native Melview schedule

The integration also discovers the Lossnay's existing **native Melview schedule** and exposes it as a read-only Home Assistant calendar.

Native schedule actions currently understood include:

- Power Off
- Power On + Lossnay
- Power On + Auto
- Power On + Bypass
- Fan speeds 1-4
- Keep current fan speed

Native Melview schedule creation/editing remains read-only until the write API has been fully verified.

> Avoid overlapping native Melview and Home Assistant schedules unless you intentionally want both systems controlling the Lossnay.

## Home Assistant entities

A typical Lossnay device provides:

| Entity | Purpose |
| --- | --- |
| **Lossnay fan** | Main power + 4-stage speed control + Auto fan preset |
| **Ventilation mode** | Lossnay / Auto Lossnay / Bypass with dynamic icon |
| **Fresh Air In** | Outside air entering the Lossnay |
| **Stale Air Out** | Indoor/return air entering the Lossnay |
| **Exhaust Air** | Exhaust air leaving the Lossnay |
| **Pre-warmed** | Fresh supply air after the Lossnay core |
| **Heat recovery efficiency** | 82/79/77/75% by fixed fan speed; API fallback on Auto |
| **Incoming air temperature change** | Pre-warmed minus Fresh Air In |
| **Fault** | Current Lossnay fault/status |
| **Home Assistant schedule** | Writable HA-managed calendar |
| **Native Melview schedule** | Read-only Mitsubishi schedule calendar |
| **Fan speed** | Legacy Auto / Speed 1-4 dropdown; disabled by default on new installs |

The exact entities available can depend on the capabilities reported by the unit.

## Dashboard ideas

The integration deliberately uses standard Home Assistant entities rather than requiring a bundled custom dashboard card.

A useful dashboard arrangement is:

1. A large **Tile card** for the Lossnay fan, with fan-speed controls enabled.
2. The **Ventilation mode** entity directly below it so the mode icon changes between Lossnay, Auto Lossnay, and Bypass.
3. Four compact temperature tiles arranged like the Lossnay core:
   - Fresh Air In
   - Stale Air Out
   - Exhaust Air
   - Pre-warmed
4. A prominent **Heat recovery efficiency** tile.
5. **Incoming air temperature change** beside it.
6. The Home Assistant schedule calendar underneath.

This gives a dashboard similar in usefulness to the Mitsubishi app while remaining completely native to Home Assistant and responsive across desktop and mobile.

## Installation with HACS

This repository can be installed as a HACS custom repository.

1. Open **HACS** in Home Assistant.
2. Open **Integrations**.
3. Select the menu and choose **Custom repositories**.
4. Add this GitHub repository.
5. Select **Integration** as the repository type.
6. Install **Mitsubishi Lossnay (Melview)**.
7. Restart Home Assistant.
8. Go to **Settings -> Devices & services -> Add Integration**.
9. Search for **Mitsubishi Lossnay (Melview)**.
10. Enter the same credentials used by the Mitsubishi Electric Wi-Fi Control / Melview app.

The integration discovers Lossnay units associated with the account.

## Confirmed live-control mappings

### Power

```text
PW1 = On
PW0 = Off
```

### Ventilation mode

```text
MD1 = Lossnay / Heat Recovery
MD3 = Auto Lossnay
MD7 = Bypass
```

### Fan speed

```text
FS0 = Auto
FS2 = Speed 1
FS3 = Speed 2
FS5 = Speed 3
FS6 = Speed 4
```

Native Melview schedules use a different encoding from live control commands.

## Melview API documentation

This project includes [MELVIEW_API.md](MELVIEW_API.md), which records the reverse-engineered API information discovered during development, including:

- Authentication
- Unit discovery
- Capability discovery
- State queries
- Power/mode/fan commands
- Temperature fields
- Heat-recovery values
- Native schedule endpoints
- Native schedule event format
- Weekday bitmasks
- Schedule mode and fan mappings
- Candidate endpoints investigated during development

The API notes are intentionally kept in the repository so future contributors can extend the integration without having to rediscover the control surface from scratch.

## Version 0.4.0

This release focuses on presentation and usability:

- Renames airflow temperature entities to match the Mitsubishi app.
- Adds fixed fan-stage heat-recovery values: 82%, 79%, 77%, and 75%.
- Adds Incoming air temperature change.
- Changes displayed ventilation modes to Lossnay / Auto Lossnay / Bypass.
- Adds mode-aware icons.
- Makes the main fan entity the preferred four-stage speed control.
- Keeps Auto fan speed as a fan preset.
- Keeps the legacy Fan speed select for upgraded installations but disables it by default for new installs.
- Preserves existing temperature entity unique IDs to reduce upgrade churn.
- Keeps old schedule wording such as Auto and Heat Recovery as accepted aliases.

## Known limitations

- Melview is an unofficial/reverse-engineered API and may change without notice.
- Control depends on the Melview cloud service.
- Native Mitsubishi schedules can be read but not created or edited by this integration.
- Home Assistant-managed schedules require Home Assistant to be running and able to reach Melview when an event fires.
- Weekly recurrence is the currently supported recurring pattern for Home Assistant-managed schedules.
- Not every Lossnay model, adapter, or regional Melview implementation has been tested.
- Features available in Mitsubishi controllers or apps are not necessarily exposed through Melview.
- The integration exposes native Home Assistant entities; it does not install a proprietary Mitsubishi-style frontend card.

## Development and API exploration

Contributions and testing with other Lossnay models are welcome.

When investigating new functionality:

- Prefer reading state before attempting write operations.
- Change one setting at a time in the official Mitsubishi app and compare API responses.
- Keep live-control mappings separate from native schedule mappings.
- Avoid aggressive polling because Melview may rate-limit or temporarily block clients.
- Do not assume Mitsubishi air-conditioner API values also apply to ERV/Lossnay devices.

See [MELVIEW_API.md](MELVIEW_API.md) for the currently documented API surface.

## Disclaimer

This is an unofficial community project and is not affiliated with, endorsed by, or supported by Mitsubishi Electric.

Use it at your own risk.
