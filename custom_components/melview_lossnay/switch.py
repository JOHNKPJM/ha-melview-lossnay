"""Configuration switch for Lossnay maintenance tracking."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import LossnayCoordinator
from .entity import LossnayEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: LossnayCoordinator = entry.runtime_data
    async_add_entities(LossnayMaintenanceTracking(coordinator, unit_id) for unit_id in coordinator.units)


class LossnayMaintenanceTracking(LossnayEntity, SwitchEntity):
    _attr_name = "Maintenance tracking"
    _attr_icon = "mdi:calendar-wrench"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator, unit_id: str) -> None:
        super().__init__(coordinator, unit_id)
        self._attr_unique_id = f"{unit_id}_maintenance_tracking"
        self._unsub = None

    @property
    def manager(self):
        return self.coordinator.maintenance_managers[self.unit_id]

    @property
    def is_on(self) -> bool:
        return bool(self.manager.data.get("enabled"))

    async def async_turn_on(self, **kwargs) -> None:
        await self.manager.async_set_enabled(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self.manager.async_set_enabled(False)

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
