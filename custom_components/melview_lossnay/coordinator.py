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
    """Coordinate state polling for all discovered Lossnay units."""

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

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        try:
            states: dict[str, dict[str, Any]] = {}
            for unit_id in self.units:
                states[unit_id] = await self.api.async_get_state(unit_id)
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
