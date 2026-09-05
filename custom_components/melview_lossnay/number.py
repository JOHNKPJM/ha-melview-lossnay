"""Configurable maintenance intervals for Lossnay."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import LossnayCoordinator
from .entity import LossnayEntity

DESCRIPTIONS = {
    "wash": ("Filter wash interval", 6, 12, 1, "mdi:air-filter"),
    "replace": ("Filter replacement interval", 12, 36, 12, "mdi:air-filter"),
    "core": ("Core inspection / cleaning interval", 12, 24, 12, "mdi:hexagon-multiple-outline"),
}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: LossnayCoordinator = entry.runtime_data
    async_add_entities(
        LossnayMaintenanceInterval(coordinator, unit_id, item, *desc)
        for unit_id in coordinator.units
        for item, desc in DESCRIPTIONS.items()
    )


class LossnayMaintenanceInterval(LossnayEntity, NumberEntity):
    _attr_mode = NumberMode.BOX
    _attr_native_unit_of_measurement = "months"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator, unit_id: str, item: str, name: str, minimum: int, maximum: int, step: int, icon: str) -> None:
        super().__init__(coordinator, unit_id)
        self.item = item
        self._attr_name = name
        self._attr_icon = icon
        self._attr_native_min_value = minimum
        self._attr_native_max_value = maximum
        self._attr_native_step = step
        self._attr_unique_id = f"{unit_id}_maintenance_{item}_interval"
        self._unsub = None

    @property
    def manager(self):
        return self.coordinator.maintenance_managers[self.unit_id]

    @property
    def native_value(self) -> float:
        return float(self.manager.data[f"{self.item}_interval_months"])

    async def async_set_native_value(self, value: float) -> None:
        await self.manager.async_set_interval(self.item, int(value))

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._unsub = async_dispatcher_connect(self.hass, self.manager.signal, self._handle_update)

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub:
            self._unsub()
        await super().async_will_remove_from_hass()

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()
