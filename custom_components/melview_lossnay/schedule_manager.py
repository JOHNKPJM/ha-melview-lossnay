"Home Assistant-managed schedules for Mitsubishi Lossnay."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
import logging
import re
from typing import Any
from uuid import uuid4

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import MODE_TO_COMMAND
from .coordinator import LossnayCoordinator

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
STORAGE_KEY = "melview_lossnay.ha_schedules"

DAY_MAP = {
    "MO": 0,
    "TU": 1,
    "WE": 2,
    "TH": 3,
    "FR": 4,
    "SA": 5,
    "SU": 6,
}

FAN_NAME_TO_COMMAND = {
    "Auto": "FS0",
    "Speed 1": "FS2",
    "Speed 2": "FS3",
    "Speed 3": "FS5",
    "Speed 4": "FS6",
}


class LossnayScheduleManager:
    """Persist and execute Home Assistant-managed Lossnay calendar events."""

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: LossnayCoordinator,
        unit_id: str,
    ) -> None:
        self.hass = hass
        self.coordinator = coordinator
        self.unit_id = unit_id
        self.store: Store[dict[str, Any]] = Store(
            hass, STORAGE_VERSION, f"{STORAGE_KEY}.{unit_id}"
        )
        self.events: dict[str, dict[str, Any]] = {}
        self._cancel_timer = None
        self._last_fired: str | None = None

    async def async_load(self) -> None:
        data = await self.store.async_load() or {}
        raw = data.get("events", {})
        if isinstance(raw, dict):
            self.events = raw
        self._schedule_next()

    async def async_shutdown(self) -> None:
        if self._cancel_timer is not None:
            self._cancel_timer()
            self._cancel_timer = None

    async def async_create_event(self, event: dict[str, Any]) -> None:
        uid = str(uuid4())
        stored = self._normalize_event(event)
        stored["uid"] = uid
        self.events[uid] = stored
        await self._save_and_reschedule()

    async def async_update_event(self, uid: str, event: dict[str, Any]) -> None:
        if uid not in self.events:
            raise ValueError(f"Unknown schedule event: {uid}")
        stored = self._normalize_event(event)
        stored["uid"] = uid
        self.events[uid] = stored
        await self._save_and_reschedule()

    async def async_delete_event(self, uid: str) -> None:
        if uid not in self.events:
            return
        del self.events[uid]
        await self._save_and_reschedule()

    def _normalize_event(self, event: dict[str, Any]) -> dict[str, Any]:
        start = event.get("start")
        end = event.get("end")
        if not isinstance(start, datetime) or not isinstance(end, datetime):
            raise ValueError("Lossnay schedules require a timed calendar event")
        if start.tzinfo is None or end.tzinfo is None:
            raise ValueError("Schedule times must include a timezone")

        summary = str(event.get("summary") or "").strip()
        if not summary:
            raise ValueError(
                "Use a title such as 'Auto | Speed 2', 'Bypass | Speed 1', "
                "'Lossnay | Speed 4', or 'Power Off'"
            )

        # Validate the command syntax while saving so invalid events cannot fire later.
        _parse_action(summary, event.get("description"))

        result = {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "summary": summary,
            "description": event.get("description"),
            "location": event.get("location"),
            "rrule": event.get("rrule"),
        }
        return result

    async def _save_and_reschedule(self) -> None:
        await self.store.async_save({"events": self.events})
        self._schedule_next()

    def _schedule_next(self) -> None:
        if self._cancel_timer is not None:
            self._cancel_timer()
            self._cancel_timer = None

        now = dt_util.now()
        next_item = self.next_occurrence(now)
        if next_item is None:
            return

        uid, occurrence = next_item
        when_utc = occurrence.astimezone(dt_util.UTC)

        @callback
        def _fire(_now: datetime) -> None:
            self.hass.async_create_task(self._async_fire(uid, occurrence))

        self._cancel_timer = async_track_point_in_utc_time(self.hass, _fire, when_utc)

    async def _async_fire(self, uid: str, occurrence: datetime) -> None:
        token = f"{uid}:{occurrence.isoformat()}"
        if token == self._last_fired:
            self._schedule_next()
            return

        item = self.events.get(uid)
        if item is None:
            self._schedule_next()
            return

        try:
            action = _parse_action(item["summary"], item.get("description"))
            await self._execute_action(action)
            self._last_fired = token
            _LOGGER.info(
                "Executed Lossnay schedule %s at %s: %s",
                uid,
                occurrence,
                item["summary"],
            )
        except Exception:
            _LOGGER.exception("Failed to execute Lossnay schedule %s", uid)
        finally:
            # Give one-shot events a chance to disappear from the "next" view.
            self._schedule_next()

    async def _execute_action(self, action: dict[str, str | None]) -> None:
        if action["power"] == "off":
            await self.coordinator.async_send_command(self.unit_id, "PW0")
            return

        await self.coordinator.async_send_command(self.unit_id, "PW1")

        mode = action.get("mode")
        if mode:
            command = MODE_TO_COMMAND.get(mode)
            if command is None:
                raise ValueError(f"Unsupported Lossnay mode: {mode}")
            await self.coordinator.async_send_command(self.unit_id, command)

        fan = action.get("fan")
        if fan:
            command = FAN_NAME_TO_COMMAND.get(fan)
            if command is None:
                raise ValueError(f"Unsupported Lossnay fan setting: {fan}")
            await self.coordinator.async_send_command(self.unit_id, command)

    def next_occurrence(self, after: datetime) -> tuple[str, datetime] | None:
        candidates: list[tuple[str, datetime]] = []
        for uid, item in self.events.items():
            occurrence = _next_occurrence(item, after)
            if occurrence is not None:
                candidates.append((uid, occurrence))
        if not candidates:
            return None
        return min(candidates, key=lambda x: x[1])

    def occurrences_between(
        self, start: datetime, end: datetime
    ) -> list[tuple[dict[str, Any], datetime, datetime]]:
        output: list[tuple[dict[str, Any], datetime, datetime]] = []
        for item in self.events.values():
            base_start = datetime.fromisoformat(item["start"])
            base_end = datetime.fromisoformat(item["end"])
            duration = base_end - base_start

            rrule = item.get("rrule")
            if not rrule:
                if base_end > start and base_start < end:
                    output.append((item, base_start, base_end))
                continue

            parsed = _parse_rrule(rrule)
            if parsed.get("FREQ") != "WEEKLY":
                # Currently only weekly recurrence is expanded/executed.
                continue

            bydays = _rrule_weekdays(parsed, base_start.weekday())
            current = start.date() - timedelta(days=7)
            final = end.date()
            while current <= final:
                if current.weekday() in bydays:
                    occurrence_start = datetime.combine(
                        current,
                        base_start.timetz().replace(tzinfo=None),
                        tzinfo=base_start.tzinfo,
                    )
                    if occurrence_start < base_start:
                        current += timedelta(days=1)
                        continue
                    occurrence_end = occurrence_start + duration
                    until = _parse_until(parsed.get("UNTIL"), base_start.tzinfo)
                    if until is not None and occurrence_start > until:
                        current += timedelta(days=1)
                        continue
                    if occurrence_end > start and occurrence_start < end:
                        output.append((item, occurrence_start, occurrence_end))
                current += timedelta(days=1)

        output.sort(key=lambda x: x[1])
        return output


def _parse_action(summary: str, description: Any = None) -> dict[str, str | None]:
    """Parse a calendar title/description into a Lossnay command.

    Supported titles:
      Power Off
      Auto
      Auto | Speed 2
      Bypass | Speed 1
      Lossnay | Speed 4
      Heat Recovery | Auto

    Description may override with:
      mode=Auto
      fan=Speed 2
      power=off
    """
    text = summary.strip()
    desc = str(description or "")

    power: str | None = None
    mode: str | None = None
    fan: str | None = None

    # Optional key/value overrides in the description.
    for key, value in re.findall(
        r"(?im)^\s*(power|mode|fan)\s*=\s*(.+?)\s*$", desc
    ):
        key = key.lower()
        value = value.strip()
        if key == "power":
            power = value.lower()
        elif key == "mode":
            mode = _normalise_mode(value)
        elif key == "fan":
            fan = _normalise_fan(value)

    lower = text.lower()
    if power is None and lower in {"power off", "off", "turn off"}:
        power = "off"

    if power != "off":
        power = "on"
        parts = [part.strip() for part in re.split(r"\s*[|,/]\s*", text) if part.strip()]
        if mode is None and parts:
            mode = _normalise_mode(parts[0])
        if fan is None and len(parts) > 1:
            fan = _normalise_fan(parts[1])

    if power == "off":
        return {"power": "off", "mode": None, "fan": None}

    if mode is None:
        raise ValueError(
            "Schedule title must specify Auto, Bypass, Lossnay, or Heat Recovery"
        )
    return {"power": "on", "mode": mode, "fan": fan}


def _normalise_mode(value: str) -> str:
    value = value.strip().lower()
    aliases = {
        "auto": "Auto",
        "bypass": "Bypass",
        "lossnay": "Heat Recovery",
        "heat recovery": "Heat Recovery",
        "heat-recovery": "Heat Recovery",
    }
    if value not in aliases:
        raise ValueError(f"Unknown Lossnay mode: {value}")
    return aliases[value]


def _normalise_fan(value: str) -> str:
    value = value.strip().lower()
    aliases = {
        "auto": "Auto",
        "speed 1": "Speed 1",
        "speed1": "Speed 1",
        "1": "Speed 1",
        "speed 2": "Speed 2",
        "speed2": "Speed 2",
        "2": "Speed 2",
        "speed 3": "Speed 3",
        "speed3": "Speed 3",
        "3": "Speed 3",
        "speed 4": "Speed 4",
        "speed4": "Speed 4",
        "4": "Speed 4",
        "keep": None,
        "no change": None,
    }
    if value not in aliases:
        raise ValueError(f"Unknown Lossnay fan setting: {value}")
    return aliases[value]


def _parse_rrule(value: str) -> dict[str, str]:
    if value.upper().startswith("RRULE:"):
        value = value.split(":", 1)[1]
    result: dict[str, str] = {}
    for part in value.split(";"):
        if "=" in part:
            key, val = part.split("=", 1)
            result[key.upper()] = val
    return result


def _rrule_weekdays(parsed: dict[str, str], fallback: int) -> set[int]:
    byday = parsed.get("BYDAY")
    if not byday:
        return {fallback}
    result = set()
    for item in byday.split(","):
        item = item[-2:].upper()
        if item in DAY_MAP:
            result.add(DAY_MAP[item])
    return result or {fallback}


def _parse_until(value: str | None, tzinfo) -> datetime | None:
    if not value:
        return None
    for fmt in ("%Y%m%dT%H%M%SZ", "%Y%m%dT%H%M%S", "%Y%m%d"):
        try:
            parsed = datetime.strptime(value, fmt)
            if value.endswith("Z"):
                return parsed.replace(tzinfo=dt_util.UTC).astimezone(tzinfo)
            return parsed.replace(tzinfo=tzinfo)
        except ValueError:
            continue
    return None


def _next_occurrence(item: dict[str, Any], after: datetime) -> datetime | None:
    base_start = datetime.fromisoformat(item["start"])
    rrule = item.get("rrule")

    if not rrule:
        # Avoid repeatedly rescheduling an event exactly at 'after'.
        return base_start if base_start > after + timedelta(seconds=1) else None

    parsed = _parse_rrule(rrule)
    if parsed.get("FREQ") != "WEEKLY":
        return None

    bydays = _rrule_weekdays(parsed, base_start.weekday())
    until = _parse_until(parsed.get("UNTIL"), base_start.tzinfo)

    # Search the next eight days; a weekly rule must occur within that span.
    for offset in range(0, 8):
        candidate_date = after.date() + timedelta(days=offset)
        if candidate_date.weekday() not in bydays:
            continue
        candidate = datetime.combine(
            candidate_date,
            base_start.timetz().replace(tzinfo=None),
            tzinfo=base_start.tzinfo,
        )
        if candidate < base_start:
            continue
        if candidate <= after + timedelta(seconds=1):
            continue
        if until is not None and candidate > until:
            continue
        return candidate
    return None
