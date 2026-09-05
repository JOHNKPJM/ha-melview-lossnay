# Changelog

## 0.4.0

- Match Mitsubishi app airflow labels: Fresh Air In, Stale Air Out, Exhaust Air, and Pre-warmed Air.
- Add fixed manual fan-stage heat-recovery values: 82%, 79%, 77%, 75%.
- Add Incoming air temperature change sensor.
- Rename displayed modes to Lossnay, Auto Lossnay, and Bypass.
- Add mode-aware icons to the main fan and ventilation-mode entities.
- Prefer the native Home Assistant four-stage fan speed control.
- Keep Auto as the fan preset.
- Keep the legacy Fan speed select for existing users; disable it by default on new installs.
- Preserve existing temperature/core-efficiency unique IDs across the rename.
- Preserve old Home Assistant schedule aliases such as Auto and Heat Recovery.

## 0.3.0

- Added Home Assistant-managed writable schedules.
- Added read-only native Melview schedules.
- Expanded reverse-engineered API documentation.
