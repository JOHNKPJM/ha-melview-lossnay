"""Local maintenance tracking for Lossnay filters and heat-exchange core."""

from __future__ import annotations

import calendar
from datetime import date, timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import DOMAIN

STORAGE_VERSION = 1


def _add_months(value: date, months: int) -> date:
    """Add calendar months while keeping the day valid."""
    target_month = value.month - 1 + months
    year = value.year + target_month // 12
    month = target_month % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


class LossnayMaintenanceManager:
    """Persist and calculate user-managed Lossnay maintenance schedules."""

    def __init__(self, hass: HomeAssistant, unit_id: str) -> None:
        self.hass = hass
        self.unit_id = unit_id
        self.store = Store(hass, STORAGE_VERSION, f"{DOMAIN}_maintenance_{unit_id}")
        self.data: dict[str, Any] = {
            "enabled": False,
            "wash_interval_months": 6,
            "replace_interval_months": 24,
            "core_interval_months": 12,
            "last_washed": None,
            "last_replaced": None,
            "last_core_cleaned": None,
            "washes_since_replacement": 0,
        }
        self._unsub_midnight = None

    @property
    def signal(self) -> str:
        return f"{DOMAIN}_maintenance_update_{self.unit_id}"

    async def async_load(self) -> None:
        stored = await self.store.async_load()
        if isinstance(stored, dict):
            self.data.update(stored)
        self._unsub_midnight = async_track_time_change(
            self.hass, self._async_midnight_refresh, hour=0, minute=0, second=5
        )

    async def async_shutdown(self) -> None:
        if self._unsub_midnight is not None:
            self._unsub_midnight()
            self._unsub_midnight = None

    async def _async_midnight_refresh(self, now) -> None:
        async_dispatcher_send(self.hass, self.signal)

    async def _async_save(self) -> None:
        await self.store.async_save(self.data)
        async_dispatcher_send(self.hass, self.signal)

    def _ensure_dates(self) -> None:
        today = dt_util.now().date().isoformat()
        if not self.data.get("last_washed"):
            self.data["last_washed"] = today
        if not self.data.get("last_replaced"):
            self.data["last_replaced"] = today
        if not self.data.get("last_core_cleaned"):
            self.data["last_core_cleaned"] = today

    async def async_set_enabled(self, enabled: bool) -> None:
        self.data["enabled"] = bool(enabled)
        if enabled:
            self._ensure_dates()
        await self._async_save()

    async def async_set_interval(self, item: str, months: int) -> None:
        ranges = {
            "wash": (6, 12),
            "replace": (12, 36),
            "core": (12, 24),
        }
        if item not in ranges:
            raise ValueError(f"Unsupported maintenance item: {item}")
        low, high = ranges[item]
        months = max(low, min(high, int(months)))
        self.data[f"{item}_interval_months"] = months
        await self._async_save()

    async def async_mark_done(self, item: str) -> None:
        today = dt_util.now().date().isoformat()
        if item == "wash":
            self.data["last_washed"] = today
            self.data["washes_since_replacement"] = int(
                self.data.get("washes_since_replacement", 0)
            ) + 1
        elif item == "replace":
            self.data["last_replaced"] = today
            self.data["last_washed"] = today
            self.data["washes_since_replacement"] = 0
        elif item == "core":
            self.data["last_core_cleaned"] = today
        else:
            raise ValueError(f"Unsupported maintenance item: {item}")
        await self._async_save()

    def _date(self, key: str) -> date | None:
        value = self.data.get(key)
        if not value:
            return None
        try:
            return date.fromisoformat(str(value))
        except ValueError:
            return None

    def due_date(self, item: str) -> date | None:
        last_key = {
            "wash": "last_washed",
            "replace": "last_replaced",
            "core": "last_core_cleaned",
        }[item]
        last = self._date(last_key)
        if last is None:
            return None
        months = int(self.data[f"{item}_interval_months"])
        return _add_months(last, months)

    def days_remaining(self, item: str) -> int | None:
        due = self.due_date(item)
        if due is None:
            return None
        return (due - dt_util.now().date()).days

    def status(self, item: str) -> str:
        if not self.data.get("enabled"):
            return "Disabled"
        days = self.days_remaining(item)
        if days is None:
            return "Unknown"
        if days < 0:
            return "Overdue"
        if days == 0:
            return "Due"
        if days <= 30:
            return "Due soon"
        return "OK"

    def due(self, item: str) -> bool:
        days = self.days_remaining(item)
        return bool(self.data.get("enabled") and days is not None and days <= 0)

    def summary(self) -> dict[str, Any]:
        """Return card-friendly maintenance state."""
        result: dict[str, Any] = {
            "enabled": bool(self.data.get("enabled")),
            "wash_interval_months": int(self.data["wash_interval_months"]),
            "replace_interval_months": int(self.data["replace_interval_months"]),
            "core_interval_months": int(self.data["core_interval_months"]),
            "washes_since_replacement": int(self.data.get("washes_since_replacement", 0)),
        }
        for item in ("wash", "replace", "core"):
            due = self.due_date(item)
            result[f"{item}_due"] = due.isoformat() if due else None
            result[f"{item}_days"] = self.days_remaining(item)
            result[f"{item}_status"] = self.status(item)
        return result
