"""Ventilation-mode select for Mitsubishi Lossnay via Melview."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import MODE_TO_COMMAND, MODE_VALUE_TO_NAME
from .coordinator import LossnayCoordinator
from .entity import LossnayEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: LossnayCoordinator = entry.runtime_data
    async_add_entities(
        LossnayVentilationMode(coordinator, unit_id) for unit_id in coordinator.units
    )


class LossnayVentilationMode(LossnayEntity, SelectEntity):
    """Heat Recovery / Auto / Bypass mode selector."""

    _attr_name = "Ventilation mode"
    _attr_options = list(MODE_TO_COMMAND)
    _attr_icon = "mdi:air-filter"

    def __init__(self, coordinator: LossnayCoordinator, unit_id: str) -> None:
        super().__init__(coordinator, unit_id)
        self._attr_unique_id = f"{unit_id}_ventilation_mode"

    @property
    def current_option(self) -> str | None:
        try:
            value = int(self.state_data.get("setmode"))
        except (TypeError, ValueError):
            return None
        return MODE_VALUE_TO_NAME.get(value)

    async def async_select_option(self, option: str) -> None:
        command = MODE_TO_COMMAND.get(option)
        if command is None:
            raise ValueError(f"Unsupported ventilation mode: {option}")
        await self.coordinator.async_send_command(self.unit_id, command)
