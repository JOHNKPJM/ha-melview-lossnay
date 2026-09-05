# Melview API notes for Mitsubishi Lossnay / ERV

This document summarises the Melview API endpoints, payloads, state fields, and command mappings that have been observed while testing a Mitsubishi Electric Lossnay ERV through the Australia/New Zealand Melview Wi-Fi Control service.

This is unofficial, reverse-engineered documentation. Values may vary by model, firmware, adapter, account, or region.

## Base URL

```text
https://api.melview.net/api
```

Authentication uses the same account as the Mitsubishi Electric Wi-Fi Control app.

## Authentication

### `POST login.aspx`

Request:

```json
{
  "user": "user@example.com",
  "pass": "password",
  "appversion": "3.3.838"
}
```

A successful login establishes the authenticated session/cookie used by later calls.

## Discovery

### `POST rooms.aspx`

Returns buildings and their units.

Observed ERV fields include:

```json
{
  "buildingid": "120152",
  "building": "Building",
  "bschedule": "0",
  "units": [
    {
      "room": "Lossnay",
      "unitid": "322430",
      "power": "on",
      "wifi": "3",
      "mode": "3",
      "temp": "17",
      "settemp": "0",
      "status": "",
      "type": "ERV",
      "outdoortemp": 15,
      "schedule1": 226405
    }
  ]
}
```

Important fields:

- `unitid`: Melview unit ID
- `type`: `ERV` for Lossnay
- `schedule1`: native Melview schedule ID for the unit

### `POST unitcapabilities.aspx`

Request:

```json
{
  "unitid": "322430",
  "v": 2
}
```

Observed ERV response fields:

- `modelid`
- `modelname`
- `unitname`
- `unittype`
- `modeltype`
- `adaptortype`
- `localip`
- `fanstage`
- `hasautofan`
- `hasoutdoortemp`
- `hasairauto`
- `fault`
- `time`
- `error`

Example:

```json
{
  "id": "322430",
  "modelid": "1373",
  "modelname": "LGH-35RVX3-E",
  "unitname": "Lossnay",
  "unittype": "ERV",
  "adaptortype": "mac578",
  "localip": "192.168.1.11",
  "fanstage": 4,
  "hasautofan": 1,
  "hasoutdoortemp": 1,
  "hasairauto": 1,
  "error": "ok"
}
```

## Unit state

### `POST unitcommand.aspx`

Read current state:

```json
{
  "unitid": "322430",
  "v": 2
}
```

Observed ERV fields:

- `power`
- `standby`
- `setmode`
- `automode`
- `setfan`
- `settemp`
- `roomtemp`
- `outdoortemp`
- `supplyfan`
- `supplytemp`
- `exhausttemp`
- `coreefficiency`
- `fault`
- `error`

Example:

```json
{
  "id": "322430",
  "power": 1,
  "standby": 0,
  "setmode": 3,
  "automode": 0,
  "setfan": 5,
  "settemp": "0",
  "roomtemp": "17",
  "outdoortemp": "14",
  "supplyfan": 5,
  "supplytemp": 16.3,
  "exhausttemp": 14.7,
  "coreefficiency": 0.77,
  "fault": "",
  "error": "ok"
}
```

## Unit control commands

Commands are sent to `unitcommand.aspx` in a compact string:

```json
{
  "unitid": "322430",
  "v": 2,
  "commands": "FS2"
}
```

### Power

```text
PW1 = Power On
PW0 = Power Off
```

### Ventilation mode

Confirmed live-control mappings:

```text
MD1 = Lossnay / Heat Recovery
MD3 = Auto
MD7 = Bypass
```

### Fan speed

Confirmed live-control mappings:

```text
FS0 = Auto
FS2 = Speed 1
FS3 = Speed 2
FS5 = Speed 3
FS6 = Speed 4
```

Note that native schedule fan values use a different encoding.

## Native schedules

### `POST schedules.aspx`

Returns schedule summaries.

Observed response:

```json
{
  "disablerules": "false",
  "edit": 1,
  "schedules": [
    {
      "id": "226405",
      "edit": "1",
      "name": "Lossnay Rules",
      "items": 8,
      "units": 1
    }
  ]
}
```

Potentially useful fields:

- `disablerules`
- `id`
- `name`
- `items`
- `units`

### `POST schedule.aspx`

Request:

```json
{
  "id": "226405",
  "v": 2
}
```

Returns native schedule events and associated units.

Observed event structure:

```json
{
  "id": 464029,
  "stype": "ERV",
  "weekdays": 64,
  "time": "06:30pm",
  "duration": 0,
  "mode": 13,
  "fanspeed": 1,
  "settemp": 0,
  "zonedata": ""
}
```

### Weekday bitmask

Observed/derived mapping:

```text
Sunday    = 1
Monday    = 2
Tuesday   = 4
Wednesday = 8
Thursday  = 16
Friday    = 32
Saturday  = 64
```

Combinations are additive. For example, Monday-Friday is expected to be:

```text
2 + 4 + 8 + 16 + 32 = 62
```

### Schedule mode mapping

Confirmed native schedule mappings:

```text
0  = Power Off
11 = Power On + Lossnay
13 = Power On + Auto
17 = Power On + Bypass
```

### Schedule fan mapping

Confirmed native schedule mappings:

```text
-1 = Do not change fan speed
1  = Speed 1
2  = Speed 2
3  = Speed 3
4  = Speed 4
```

There is no Auto fan option exposed in the schedule UI for the tested ERV.

## Other candidate endpoints tested

The following candidate endpoints returned HTTP 403 during probing and should not currently be treated as confirmed API routes:

```text
unitschedule.aspx
unitschedules.aspx
schedulecommand.aspx
scheduledata.aspx
scheduledetail.aspx
scheduleinfo.aspx
freecooling.aspx
autofreecooling.aspx
bypass.aspx
ervconfig.aspx
ervstatus.aspx
ventilation.aspx
```

A 403 here may mean the endpoint does not exist behind the application gateway, requires a different request shape, or is not available to the current client/account.

## Local adapter information

`unitcapabilities.aspx` exposes `localip`, for example:

```text
192.168.1.11
```

Earlier Melview reverse-engineering suggests some adapters may support local `/smart` control after cloud-assisted authentication/token generation, but this has not yet been implemented in this integration.

## Home Assistant entity mapping

Current integration direction:

- `fan`: power + fan speed
- `select`: ventilation mode
- `select`: explicit fan speed
- `sensor`: indoor temperature
- `sensor`: outdoor temperature
- `sensor`: supply temperature
- `sensor`: exhaust temperature
- `sensor`: core efficiency diagnostic
- `sensor`: fault/status
- `calendar`: native Melview schedule

## Safety / development notes

- Avoid aggressive polling; Melview may rate-limit or temporarily block clients.
- Treat this API as unofficial and subject to change.
- Keep live-control mappings separate from native schedule mappings.
- Do not assume values from air-conditioner integrations apply to ERV/Lossnay devices.
- Prefer observing the official app/controller behaviour and diffing API responses before adding new write commands.


## Home Assistant-managed scheduling

The integration also provides a writable Home Assistant calendar. These events are not written to `schedule.aspx`; they are stored locally in Home Assistant and execute the confirmed `PW`, `MD`, and `FS` commands at event time.

Native Melview schedule creation/update/delete is intentionally not implemented until the schedule write request format is confirmed.

## Lossnay app presentation values

The Mitsubishi Lossnay app uses fixed heat-recovery efficiency values for the four manual fan stages. These values are useful for reproducing the app's Lossnay Core display in Home Assistant.

| Live fan command | Fan stage | App heat recovery |
| --- | --- | ---: |
| `FS2` | Speed 1 | 82% |
| `FS3` | Speed 2 | 79% |
| `FS5` | Speed 3 | 77% |
| `FS6` | Speed 4 | 75% |

`FS0` is Auto fan speed and therefore does not have one fixed stage efficiency. When available, the integration uses the `coreefficiency` value returned by Melview for Auto.

The app-facing airflow labels map to the API state as follows:

| App label | API field |
| --- | --- |
| Fresh Air In | `outdoortemp` |
| Stale Air Out | `roomtemp` |
| Exhaust Air | `exhausttemp` |
| Pre-warmed | `supplytemp` |

The displayed incoming-air temperature change can be reproduced as:

```text
supplytemp - outdoortemp
```

For example, `15.6 - 14.0 = 1.6 C`.

## Local maintenance tracking (not a Melview API feature)

As of v0.5.0, no verified Melview state field has been identified for filter life, filter condition, or filter replacement status. The integration therefore does **not** present maintenance timers as cloud/device telemetry.

The optional filter wash, filter replacement, and Lossnay core inspection/cleaning schedules are stored locally by Home Assistant and reset manually by the user. They do not send maintenance commands to Melview.
