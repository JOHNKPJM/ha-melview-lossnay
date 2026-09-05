"""Native Melview schedule calendar for Mitsubishi Lossnay."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    SCHEDULE_FAN_VALUE_TO_NAME,
    SCHEDULE_MODE_VALUE_TO_NAME,
    SCHEDULE_WEEKDAY_BITS,
)
from .coordinator import LossnayCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up native Melview schedule calendars."""
    coordinator: LossnayCoordinator = entry.runtime_data
    async_add_entities(
        LossnayScheduleCalendar(coordinator, schedule_id)
        for schedule_id in coordinator.schedules
    )


class LossnayScheduleCalendar(CoordinatorEntity[LossnayCoordinator], CalendarEntity):
    """Read-only Home Assistant calendar backed by a Melview native schedule."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: LossnayCoordinator, schedule_id: str) -> None:
        super().__init__(coordinator)
        self.schedule_id = schedule_id
        self._attr_unique_id = f"schedule_{schedule_id}"
        self._attr_name = self.schedule_data.get("name") or "Native schedule"
        self._attr_icon = "mdi:calendar-clock"

        unit_ids = {
            str(unit.get("id"))
            for unit in self.schedule_data.get("units", [])
            if isinstance(unit, dict) and unit.get("id") is not None
        }
        matching_unit = next((uid for uid in unit_ids if uid in coordinator.units), None)
        if matching_unit is not None:
            unit = coordinator.units[matching_unit]
            caps = coordinator.capabilities.get(matching_unit, {})
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, matching_unit)},
                name=str(caps.get("unitname") or unit.get("room") or "Lossnay"),
                manufacturer="Mitsubishi Electric",
                model=str(caps.get("modelname") or "Lossnay ERV"),
            )

    @property
    def schedule_data(self) -> dict[str, Any]:
        """Return the current schedule payload from memory."""
        return self.coordinator.schedules.get(self.schedule_id, {})

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose useful native schedule metadata."""
        events = self.schedule_data.get("events", [])
        return {
            "schedule_id": self.schedule_id,
            "native_rules_enabled": not self.coordinator.schedule_rules_disabled,
            "event_count": len(events) if isinstance(events, list) else 0,
        }

    @property
    def event(self) -> CalendarEvent | None:
        """Return the current or next scheduled action."""
        now = dt_util.now()
        events = self._expanded_events(now - timedelta(minutes=1), now + timedelta(days=8))
        for item in events:
            if item.end > now:
                return item
        return None

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return expanded weekly schedule events for the requested range."""
        return self._expanded_events(start_date, end_date)

    def _expanded_events(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        raw_events = self.schedule_data.get("events", [])
        if not isinstance(raw_events, list):
            return []

        expanded: list[CalendarEvent] = []
        current_date = start_date.date()
        final_date = end_date.date()

        while current_date <= final_date:
            weekday_bit = SCHEDULE_WEEKDAY_BITS.get(current_date.weekday())
            if weekday_bit is None:
                current_date += timedelta(days=1)
                continue

            for raw in raw_events:
                if not isinstance(raw, dict):
                    continue
                try:
                    weekdays = int(raw.get("weekdays", 0))
                except (TypeError, ValueError):
                    continue
                if not weekdays & weekday_bit:
                    continue

                event_time = _parse_time(raw.get("time"))
                if event_time is None:
                    continue

                start = datetime.combine(current_date, event_time, tzinfo=start_date.tzinfo)
                # Melview events are point-in-time actions. Represent them as
                # one-minute calendar events so Home Assistant can display and
                # trigger on them while preserving the original action time.
                end = start + timedelta(minutes=1)
                if end <= start_date or start >= end_date:
                    continue

                summary, description = _event_text(raw)
                event_id = raw.get("id")
                expanded.append(
                    CalendarEvent(
                        start=start,
                        end=end,
                        summary=summary,
                        description=description,
                        uid=str(event_id) if event_id is not None else None,
                    )
                )

            current_date += timedelta(days=1)

        expanded.sort(key=lambda item: item.start)
        return expanded


def _parse_time(value: Any):
    if not isinstance(value, str):
        return None
    for fmt in ("%I:%M%p", "%I:%M %p"):
        try:
            return datetime.strptime(value.strip(), fmt).time()
        except ValueError:
            pass
    return None


def _event_text(raw: dict[str, Any]) -> tuple[str, str]:
    """Translate a native schedule record to Home Assistant text."""
    try:
        mode_value = int(raw.get("mode"))
    except (TypeError, ValueError):
        mode_value = None
    try:
        fan_value = int(raw.get("fanspeed"))
    except (TypeError, ValueError):
        fan_value = None

    mode = SCHEDULE_MODE_VALUE_TO_NAME.get(mode_value, f"Mode {mode_value}")
    fan = SCHEDULE_FAN_VALUE_TO_NAME.get(fan_value, f"Fan {fan_value}")

    if mode_value == 0:
        summary = "Lossnay: Power Off"
    else:
        summary = f"Lossnay: {mode} · {fan}"

    description = (
        f"Native Melview schedule action. mode={mode_value}, "
        f"fanspeed={fan_value}, event_id={raw.get('id')}"
    )
    return summary, description
