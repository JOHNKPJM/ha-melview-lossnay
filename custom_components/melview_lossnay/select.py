"""Select platforms for Mitsubishi Lossnay via Melview."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    FAN_PRESET_TO_VALUE,
    FAN_VALUE_TO_PRESET,
    MODE_TO_COMMAND,
    MODE_VALUE_TO_NAME,
)
from .coordinator import LossnayCoordinator
from .entity import LossnayEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: LossnayCoordinator = entry.runtime_data
    entities = []
    for unit_id in coordinator.units:
        entities.append(LossnayVentilationMode(coordinator, unit_id))
        entities.append(LossnayFanSpeed(coordinator, unit_id))
    async_add_entities(entities)


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


class LossnayFanSpeed(LossnayEntity, SelectEntity):
    """Discrete Lossnay fan speed selector."""

    _attr_name = "Fan speed"
    _attr_options = list(FAN_PRESET_TO_VALUE)
    _attr_icon = "mdi:fan"

    def __init__(self, coordinator: LossnayCoordinator, unit_id: str) -> None:
        super().__init__(coordinator, unit_id)
        self._attr_unique_id = f"{unit_id}_fan_speed"

    @property
    def current_option(self) -> str | None:
        try:
            value = int(self.state_data.get("setfan"))
        except (TypeError, ValueError):
            return None
        return FAN_VALUE_TO_PRESET.get(value)

    async def async_select_option(self, option: str) -> None:
        value = FAN_PRESET_TO_VALUE.get(option)
        if value is None:
            raise ValueError(f"Unsupported fan speed: {option}")

        # Ensure the unit is on before setting a fan speed.
        try:
            is_on = bool(int(self.state_data.get("power", 0)))
        except (TypeError, ValueError):
            is_on = False

        if not is_on:
            await self.coordinator.async_send_command(self.unit_id, "PW1")
        await self.coordinator.async_send_command(self.unit_id, f"FS{value}")
