"""Binary sensors for Lossnay maintenance reminders."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import LossnayCoordinator
from .entity import LossnayEntity

ITEMS = {
    "wash": ("Filter wash due", "mdi:air-filter"),
    "replace": ("Filter replacement due", "mdi:air-filter"),
    "core": ("Core inspection / cleaning due", "mdi:hexagon-multiple-outline"),
}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: LossnayCoordinator = entry.runtime_data
    async_add_entities(
        LossnayMaintenanceDue(coordinator, unit_id, item, name, icon)
        for unit_id in coordinator.units
        for item, (name, icon) in ITEMS.items()
    )


class LossnayMaintenanceDue(LossnayEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, unit_id: str, item: str, name: str, icon: str) -> None:
        super().__init__(coordinator, unit_id)
        self.item = item
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"{unit_id}_maintenance_{item}_due"
        self._unsub = None

    @property
    def manager(self):
        return self.coordinator.maintenance_managers[self.unit_id]

    @property
    def is_on(self) -> bool:
        return self.manager.due(self.item)

    @property
    def available(self) -> bool:
        return bool(self.manager.data.get("enabled"))

    @property
    def extra_state_attributes(self):
        due = self.manager.due_date(self.item)
        return {
            "status": self.manager.status(self.item),
            "days_remaining": self.manager.days_remaining(self.item),
            "due_date": due.isoformat() if due else None,
        }

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
