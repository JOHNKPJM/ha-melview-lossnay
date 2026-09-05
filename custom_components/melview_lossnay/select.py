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
    """Lossnay / Auto Lossnay / Bypass mode selector."""

    _attr_name = "Ventilation mode"
    _attr_options = list(MODE_TO_COMMAND)

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

    @property
    def icon(self) -> str:
        """Use an icon that reflects the current airflow mode."""
        return {
            "Lossnay": "mdi:heat-wave",
            "Auto Lossnay": "mdi:autorenew",
            "Bypass": "mdi:swap-horizontal",
        }.get(self.current_option, "mdi:air-filter")

    async def async_select_option(self, option: str) -> None:
        command = MODE_TO_COMMAND.get(option)
        if command is None:
            raise ValueError(f"Unsupported ventilation mode: {option}")
        await self.coordinator.async_send_command(self.unit_id, command)


class LossnayFanSpeed(LossnayEntity, SelectEntity):
    """Discrete Lossnay fan speed selector retained for backwards compatibility."""

    _attr_name = "Fan speed"
    _attr_options = list(FAN_PRESET_TO_VALUE)
    _attr_icon = "mdi:fan"
    # The main fan entity now provides Home Assistant's richer 4-stage speed
    # control. Existing installs keep this entity; new installs can enable it if
    # they prefer a named Speed 1-4 dropdown.
    _attr_entity_registry_enabled_default = False

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

        try:
            is_on = bool(int(self.state_data.get("power", 0)))
        except (TypeError, ValueError):
            is_on = False

        if not is_on:
            await self.coordinator.async_send_command(self.unit_id, "PW1")
        await self.coordinator.async_send_command(self.unit_id, f"FS{value}")
