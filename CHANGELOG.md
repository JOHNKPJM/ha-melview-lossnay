# Changelog

## 0.5.0

- Added optional rich `custom:lossnay-card` dashboard UI.
- Added matching `custom:lossnay-maintenance-card` for separate maintenance display.
- Added dynamic heat-recovery vs bypass airflow visualisation.
- Bypass now leaves Exhaust Air, Pre-warmed and heat-recovery efficiency unavailable rather than calculating misleading values.
- Added Bypass Cooling/Warming/Balanced presentation based on indoor/outdoor temperature difference.
- Removed fan-stage efficiency labels from the visual speed controls; efficiency remains in the dedicated recovery panel.
- Added optional local maintenance tracking:
  - filter wash: 6-12 months
  - filter replacement: 1-3 years
  - Lossnay core inspection/cleaning: 1-2 years
- Added persistent manual reset dates and washes-since-replacement counter.
- Added maintenance interval number entities, reset buttons, tracking switch, and due binary sensors.
- Added local maintenance services used by the rich cards and automations.

## 0.4.0

- Added native Home Assistant fan entity with four stepped speeds and Auto fan preset.
- Renamed core temperature entities to match the Mitsubishi app.
- Added fixed Mitsubishi heat-recovery values for fixed fan stages.
- Added calculated Lossnay Core temperatures and incoming-air temperature change.
- Added mode-aware icons.

## 0.3.0

- Added Home Assistant-managed writable schedules.
- Added read-only native Melview schedule discovery.
- Added API reference and README refresh.
