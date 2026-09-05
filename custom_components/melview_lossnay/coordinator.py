"""Data update coordinator for Mitsubishi Lossnay via Melview."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import MelviewApi, MelviewAuthError, MelviewError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class LossnayCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Coordinate state and native schedule polling."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: MelviewApi,
        units: dict[str, dict[str, Any]],
        capabilities: dict[str, dict[str, Any]],
    ) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.api = api
        self.units = units
        self.capabilities = capabilities
        self.schedules_summary: dict[str, dict[str, Any]] = {}
        self.schedules: dict[str, dict[str, Any]] = {}
        self.schedule_rules_disabled = False

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        try:
            states: dict[str, dict[str, Any]] = {}
            for unit_id in self.units:
                states[unit_id] = await self.api.async_get_state(unit_id)

            # Native schedules are optional. A schedule failure should not take
            # the Lossnay itself offline, so retain prior schedule data if the
            # endpoint is temporarily unavailable.
            try:
                summary = await self.api.async_get_schedules()
                self.schedule_rules_disabled = str(
                    summary.get("disablerules", "false")
                ).lower() == "true"

                raw_schedules = summary.get("schedules", [])
                if isinstance(raw_schedules, list):
                    self.schedules_summary = {
                        str(item["id"]): item
                        for item in raw_schedules
                        if isinstance(item, dict) and item.get("id") is not None
                    }

                    details: dict[str, dict[str, Any]] = {}
                    for schedule_id in self.schedules_summary:
                        details[schedule_id] = await self.api.async_get_schedule(
                            schedule_id
                        )
                    self.schedules = details
            except MelviewError as err:
                _LOGGER.warning("Unable to refresh Melview native schedules: %s", err)

            return states
        except MelviewAuthError as err:
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except MelviewError as err:
            raise UpdateFailed(str(err)) from err

    async def async_send_command(self, unit_id: str, command: str) -> None:
        """Send a command and immediately use returned state."""
        try:
            new_state = await self.api.async_command(unit_id, command)
        except MelviewError as err:
            raise UpdateFailed(str(err)) from err

        data = dict(self.data or {})
        data[unit_id] = new_state
        self.async_set_updated_data(data)
