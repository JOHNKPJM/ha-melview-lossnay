"""Manual maintenance reset buttons for Lossnay."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import LossnayCoordinator
from .entity import LossnayEntity

BUTTONS = {
    "wash": ("Mark filters washed", "mdi:air-filter"),
    "replace": ("Mark filters replaced", "mdi:air-filter"),
    "core": ("Mark core inspected / cleaned", "mdi:hexagon-multiple-outline"),
}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: LossnayCoordinator = entry.runtime_data
    async_add_entities(
        LossnayMaintenanceButton(coordinator, unit_id, item, name, icon)
        for unit_id in coordinator.units
        for item, (name, icon) in BUTTONS.items()
    )


class LossnayMaintenanceButton(LossnayEntity, ButtonEntity):
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator, unit_id: str, item: str, name: str, icon: str) -> None:
        super().__init__(coordinator, unit_id)
        self.item = item
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"{unit_id}_maintenance_{item}_reset"

    @property
    def manager(self):
        return self.coordinator.maintenance_managers[self.unit_id]

    async def async_press(self) -> None:
        await self.manager.async_mark_done(self.item)
