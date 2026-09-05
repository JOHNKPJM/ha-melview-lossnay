"""Base entities for Mitsubishi Lossnay via Melview."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import LossnayCoordinator


class LossnayEntity(CoordinatorEntity[LossnayCoordinator]):
    """Base class shared by all Lossnay entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: LossnayCoordinator, unit_id: str) -> None:
        super().__init__(coordinator)
        self.unit_id = unit_id
        unit = coordinator.units[unit_id]
        caps = coordinator.capabilities.get(unit_id, {})

        model = caps.get("modelname") or "Lossnay ERV"
        name = caps.get("unitname") or unit.get("room") or "Lossnay"
        adapter = caps.get("adaptortype")

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, unit_id)},
            name=str(name),
            manufacturer="Mitsubishi Electric",
            model=str(model),
            serial_number=None,
            hw_version=str(adapter) if adapter else None,
            configuration_url="https://app.melview.net",
        )

    @property
    def state_data(self) -> dict[str, Any]:
        """Return current state for this unit."""
        return (self.coordinator.data or {}).get(self.unit_id, {})
