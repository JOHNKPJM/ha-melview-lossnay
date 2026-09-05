# Mitsubishi Lossnay (Melview) for Home Assistant

A Home Assistant custom integration for Mitsubishi Electric **Lossnay ERV** systems connected through the Australia/New Zealand **Melview / Mitsubishi Electric Wi-Fi Control** service.

The integration brings Lossnay control, environmental telemetry, diagnostics, and scheduling into Home Assistant. It is designed for installation through HACS and uses the same Melview account as the Mitsubishi Electric Wi-Fi Control app.

> **Status:** Experimental/community integration. The Melview API is unofficial and reverse-engineered, so behaviour may vary by Lossnay model, Wi-Fi adapter, firmware, account, or region.

## Features

### Lossnay control

Control the ERV directly from Home Assistant:

- Power on/off
- Ventilation mode
  - Lossnay / Heat Recovery
  - Auto
  - Bypass
- Fan control
  - Auto
  - Speed 1
  - Speed 2
  - Speed 3
  - Speed 4
- Fan speed is available both through the Home Assistant fan entity and as a dedicated **Fan speed** selector.

### Sensors and status

The integration exposes the telemetry returned by Melview, including:

- Indoor temperature
- Outdoor temperature
- Supply air temperature
- Exhaust air temperature
- Core efficiency
- Fault/status information

Additional device and capability information is obtained from Melview during discovery.

## Scheduling

The integration provides two different schedule calendars.

### Home Assistant schedule

The **Home Assistant schedule** is writable and lets you create, edit, and delete Lossnay schedules from Home Assistant.

These schedules are stored in Home Assistant and execute the normal Melview control commands at the scheduled time.

Create an event in the Home Assistant calendar using a title such as:

```text
Power Off
Auto
Auto | Speed 1
Auto | Speed 2
Auto | Speed 3
Auto | Speed 4
Auto | Auto
Bypass | Speed 1
Lossnay | Speed 1
Heat Recovery | Speed 4
```

`Lossnay` and `Heat Recovery` refer to the same ventilation mode.

If the title contains only a mode, the current fan speed is left unchanged:

```text
Auto
Bypass
Lossnay
```

You can alternatively specify the action in the event description:

```text
mode=Auto
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

This allows schedules configured in the Mitsubishi app to be viewed from Home Assistant without modifying them.

Native schedule actions currently understood by the integration include:

- Power Off
- Power On + Lossnay
- Power On + Auto
- Power On + Bypass
- Fan speeds 1-4
- Keep current fan speed

Native Melview schedule creation/editing is intentionally read-only until the schedule-write API has been fully verified.

> Avoid creating overlapping native Melview and Home Assistant schedules unless you intentionally want both systems controlling the Lossnay.

## Home Assistant entities

A typical Lossnay device provides:

| Entity | Purpose |
| --- | --- |
| Fan | Power and fan control |
| Fan speed | Auto / Speed 1-4 selector |
| Ventilation mode | Lossnay / Auto / Bypass |
| Indoor temperature | Return/room temperature reported by Melview |
| Outdoor temperature | Outdoor air temperature |
| Supply temperature | Supply air temperature |
| Exhaust temperature | Exhaust air temperature |
| Core efficiency | Reported heat-exchanger efficiency |
| Fault | Current fault/status |
| Native Melview schedule | Read-only Mitsubishi schedule calendar |
| Home Assistant schedule | Writable Home Assistant schedule calendar |

The exact entities available can depend on the capabilities reported by the unit.

## Installation with HACS

This repository can be installed as a HACS custom repository.

1. Open **HACS** in Home Assistant.
2. Open **Integrations**.
3. Select the menu and choose **Custom repositories**.
4. Add this GitHub repository.
5. Select **Integration** as the repository type.
6. Install **Mitsubishi Lossnay (Melview)**.
7. Restart Home Assistant.

Then go to:

**Settings → Devices & services → Add Integration**

Search for:

**Mitsubishi Lossnay (Melview)**

Enter the credentials used by your Mitsubishi Electric Wi-Fi Control / Melview account.

The integration will discover Lossnay units associated with the account.

## Dashboard use

After setup, open the Lossnay device under:

**Settings → Devices & services → Mitsubishi Lossnay (Melview)**

The entities can be added to any Home Assistant dashboard.

Useful dashboard controls include:

- Fan card/tile for power
- Fan speed selector
- Ventilation mode selector
- Temperature sensors
- Core efficiency
- Fault status
- Calendar card for schedules

## How it works

The integration communicates with the cloud Melview service rather than directly controlling the Lossnay over the local network.

It:

1. Authenticates using the configured Melview account.
2. Discovers ERV/Lossnay units.
3. Queries model capabilities.
4. Polls current Lossnay state.
5. Sends confirmed Melview commands for power, ventilation mode, and fan speed.
6. Reads native Melview schedules.
7. Runs optional Home Assistant-managed schedules using those same control commands.

The integration is currently classified as **cloud polling**.

## Confirmed control mappings

The following live Melview commands have been confirmed:

### Power

```text
PW1 = On
PW0 = Off
```

### Ventilation mode

```text
MD1 = Lossnay / Heat Recovery
MD3 = Auto
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

Native Melview schedules use a different encoding from live control commands. Those mappings and the discovered API endpoints are documented separately.

## Melview API documentation

This project includes [MELVIEW_API.md](MELVIEW_API.md), which records the reverse-engineered Melview API information discovered during development.

It includes:

- Authentication
- Unit discovery
- Capability discovery
- State queries
- Power/mode/fan commands
- Native schedule endpoints
- Native schedule event format
- Weekday bitmasks
- Schedule mode and fan mappings
- Candidate endpoints investigated during development

This is intended both as project documentation and as a starting point for anyone who wants to investigate additional Lossnay/Melview functionality.

## Known limitations

- Melview is an unofficial/reverse-engineered API and may change without notice.
- Control currently depends on the Melview cloud service.
- Native Mitsubishi schedules can be read but not created or edited by this integration.
- Home Assistant-managed schedules require Home Assistant to be running and able to reach Melview when an event fires.
- Weekly recurrence is the currently supported recurring pattern for Home Assistant-managed schedules.
- Not every Lossnay model, adapter, or regional Melview implementation has been tested.
- Features available in Mitsubishi controllers or apps are not necessarily exposed through Melview.

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
