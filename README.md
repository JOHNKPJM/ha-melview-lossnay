# Mitsubishi Lossnay (Melview) for Home Assistant

A Home Assistant custom integration for Mitsubishi Electric **Lossnay ERV** systems connected through the Australia/New Zealand **Melview / Mitsubishi Electric Wi-Fi Control** service.

The integration provides normal Home Assistant entities **and an optional rich Lossnay dashboard card** designed around the visual language of the Mitsubishi app: airflow graphics, mode-aware colours, fan controls, heat-recovery information, bypass cooling/warming information, and an optional maintenance tracker.

> **Status:** Experimental/community integration. The Melview API is unofficial and reverse-engineered, so behaviour can vary by model, adapter, firmware, account, or region.

## v0.5.0 highlights

- New optional **Lossnay rich dashboard card** with a dark app-like design.
- Dynamic **Lossnay Core** airflow graphic.
- In **Lossnay** mode the graphic shows crossed heat-exchange airflow and calculated **Exhaust Air** / **Pre-warmed** temperatures.
- In **Bypass** mode the graphic changes to straight-through airflow. **Exhaust Air** and **Pre-warmed** become unavailable rather than displaying misleading calculated values.
- Bypass status becomes **Cooling**, **Warming**, or **Balanced** based on Fresh Air In versus Stale Air Out, with airflow colours changing accordingly.
- Fan-speed controls no longer display heat-recovery percentages under each speed; recovery is shown in the dedicated heat-recovery panel.
- Optional **local maintenance tracking** for filter washing, filter replacement, and Lossnay core inspection/cleaning.
- Maintenance can be displayed **inside the main card** or as a **separate matching card**.

## Main Lossnay control

The primary Home Assistant **fan entity** provides:

- Power on/off
- Four stepped speeds
  - 25% = Speed 1
  - 50% = Speed 2
  - 75% = Speed 3
  - 100% = Speed 4
- **Auto** fan-speed preset
- State-aware icon matching the ventilation mode

A legacy **Fan speed** select remains available but is disabled by default on new installs.

## Ventilation modes

- **Lossnay** - heat recovery
- **Auto Lossnay** - automatic operation
- **Bypass** - bypass the heat exchanger

The rich card uses the active mode to change the entire core graphic, rather than showing multiple airflow diagrams at once.

## Lossnay Core temperatures

| Home Assistant | Source | Meaning |
| --- | --- | --- |
| **Fresh Air In** | `outdoortemp` | Outside air entering the unit |
| **Stale Air Out** | `roomtemp` | Indoor/return air entering the unit |
| **Exhaust Air** | calculated in heat-recovery mode | Air leaving the building after heat exchange |
| **Pre-warmed** | calculated in heat-recovery mode | Fresh supply air after heat exchange |

### Lossnay / heat-recovery mode

The fixed Mitsubishi heat-recovery figures are:

| Fan speed | Heat recovery |
| --- | ---: |
| Speed 1 | 82% |
| Speed 2 | 79% |
| Speed 3 | 77% |
| Speed 4 | 75% |

For Auto fan speed, Melview's `coreefficiency` value is used when available.

The card uses these values to reproduce the two conditioned Lossnay Core temperatures and shows the temperature change of the incoming air.

### Bypass mode

Bypass deliberately does **not** calculate heat-exchanger outlet temperatures:

- **Exhaust Air:** unavailable
- **Pre-warmed:** unavailable
- **Heat recovery efficiency:** unavailable

Instead, the rich card compares Fresh Air In and Stale Air Out:

- Outside cooler than indoors -> **Cooling**
- Outside warmer than indoors -> **Warming**
- Equal temperatures -> **Balanced**

The direct-airflow arrows also change colour. For example, cool outside air entering the house is blue while warmer indoor air being expelled is red. If the outside air is warmer, those colours reverse.

## Optional rich dashboard card

The integration serves a custom Lovelace resource at:

```text
/melview_lossnay/lossnay-card.js
```

After installing/updating the integration and restarting Home Assistant, add that URL once under:

**Settings -> Dashboards -> Resources -> Add resource**

Use resource type **JavaScript Module**.

### Main card with integrated maintenance

```yaml
type: custom:lossnay-card
entity: fan.lossnay
maintenance: integrated
```

### Main card without maintenance

```yaml
type: custom:lossnay-card
entity: fan.lossnay
maintenance: hidden
```

### Separate maintenance card

```yaml
type: custom:lossnay-maintenance-card
entity: fan.lossnay
```

Replace `fan.lossnay` with the actual Lossnay fan entity ID in your Home Assistant instance.

The main card includes:

- Power
- Lossnay / Auto Lossnay / Bypass controls
- Speed 1-4 / Auto fan controls
- Dynamic airflow graphic
- Heat recovery when applicable
- Bypass cooling/warming information when applicable
- Four core temperature tiles
- Optional maintenance section

## Maintenance tracking

Maintenance tracking is **local to Home Assistant**. It does not pretend that Melview reports filter condition or filter life.

It is disabled by default and can be enabled from the rich card or the **Maintenance tracking** entity.

### Wash filters

Configurable from **6 to 12 months** in one-month increments.

Press **Mark filters washed** after cleaning. This:

- resets the wash timer
- increments **Washes since replacement**
- does not reset filter replacement age

After three wash cycles, the wash count remains visible so you can use it as an additional replacement cue.

### Replace filters

Configurable from **1 to 3 years**.

Press **Mark filters replaced** after replacement. This:

- resets the replacement timer
- resets the wash timer
- resets **Washes since replacement** to zero

### Inspect / clean Lossnay core

Configurable from **1 to 2 years**.

Press **Mark core inspected / cleaned** to reset only the core timer.

### Reminder states

Each maintenance item can report:

- **OK**
- **Due soon** - 30 days or less remaining
- **Due**
- **Overdue**

The integration exposes problem binary sensors so normal Home Assistant automations can send notifications when maintenance is due.

### Maintenance entities

| Entity | Purpose |
| --- | --- |
| Maintenance tracking | Enable/disable the local tracker |
| Filter wash interval | 6-12 months |
| Filter replacement interval | 12/24/36 months |
| Core inspection / cleaning interval | 12/24 months |
| Filter wash due | Binary reminder sensor |
| Filter replacement due | Binary reminder sensor |
| Core inspection / cleaning due | Binary reminder sensor |
| Mark filters washed | Manual reset button |
| Mark filters replaced | Manual replacement reset |
| Mark core inspected / cleaned | Manual core reset |

The rich card and the standard Home Assistant entities operate on the same stored maintenance data, so you can switch between an integrated maintenance panel, a separate maintenance card, or standard HA entities without losing history.

## Scheduling

The integration provides two calendars.

### Home Assistant schedule

Writable HA-managed schedule events can directly control the Lossnay. Example titles:

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

For backwards compatibility, `Auto` and `Heat Recovery` are accepted as aliases for **Auto Lossnay** and **Lossnay**.

### Native Melview schedule

Existing Melview schedules are exposed as a read-only Home Assistant calendar. Native schedule write support remains disabled until the write API is fully verified.

## Home Assistant entities

A typical device provides:

| Entity | Purpose |
| --- | --- |
| Lossnay fan | Main power + speed control + Auto fan preset |
| Ventilation mode | Lossnay / Auto Lossnay / Bypass |
| Fresh Air In | Outside air entering the Lossnay |
| Stale Air Out | Indoor/return air entering the Lossnay |
| Exhaust Air | Heat-recovery exhaust temperature; unavailable in Bypass |
| Pre-warmed | Heat-recovery supply temperature; unavailable in Bypass |
| Heat recovery efficiency | Active heat-recovery efficiency; unavailable in Bypass |
| Incoming air temperature change | Heat-recovery supply change |
| Fault | Lossnay fault/status |
| Home Assistant schedule | Writable HA calendar |
| Native Melview schedule | Read-only Mitsubishi schedule |
| Maintenance entities | Optional local maintenance tracker |

## Installation with HACS

1. Add this repository to HACS as an **Integration** custom repository.
2. Install **Mitsubishi Lossnay (Melview)**.
3. Restart Home Assistant.
4. Go to **Settings -> Devices & services -> Add Integration**.
5. Search for **Mitsubishi Lossnay (Melview)**.
6. Sign in using the same credentials as the Mitsubishi Electric Wi-Fi Control / Melview app.
7. For the rich card, add `/melview_lossnay/lossnay-card.js` as a JavaScript Module dashboard resource.

## Confirmed live-control mappings

```text
PW1 = On
PW0 = Off

MD1 = Lossnay
MD3 = Auto Lossnay
MD7 = Bypass

FS0 = Auto
FS2 = Speed 1
FS3 = Speed 2
FS5 = Speed 3
FS6 = Speed 4
```

Native Melview schedules use a different encoding from live controls.

## API documentation

See [MELVIEW_API.md](MELVIEW_API.md) for the reverse-engineered API notes, including authentication, unit discovery, capabilities, current state, commands, temperature fields, and native schedules.
