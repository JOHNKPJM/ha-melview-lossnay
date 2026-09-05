"""Sensor platform for Mitsubishi Lossnay via Melview."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import LossnayCoordinator
from .entity import LossnayEntity


@dataclass(frozen=True, kw_only=True)
class LossnaySensorDescription(SensorEntityDescription):
    """Description for a Lossnay sensor."""

    value_fn: Callable[[dict[str, Any]], Any]


def _number(data: dict[str, Any], key: str) -> float | None:
    value = data.get(key)
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


SENSORS: tuple[LossnaySensorDescription, ...] = (
    LossnaySensorDescription(
        key="room_temperature",
        name="Indoor temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=1,
        value_fn=lambda d: _number(d, "roomtemp"),
    ),
    LossnaySensorDescription(
        key="outdoor_temperature",
        name="Outdoor temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=1,
        value_fn=lambda d: _number(d, "outdoortemp"),
    ),
    LossnaySensorDescription(
        key="supply_temperature",
        name="Supply temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=1,
        value_fn=lambda d: _number(d, "supplytemp"),
    ),
    LossnaySensorDescription(
        key="exhaust_temperature",
        name="Exhaust temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=1,
        value_fn=lambda d: _number(d, "exhausttemp"),
    ),
    LossnaySensorDescription(
        key="core_efficiency",
        name="Core efficiency",
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=0,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: (
            round(v * 100, 1) if (v := _number(d, "coreefficiency")) is not None else None
        ),
    ),
    LossnaySensorDescription(
        key="fault",
        name="Fault",
        icon="mdi:alert-circle-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("fault") or "OK",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: LossnayCoordinator = entry.runtime_data
    async_add_entities(
        LossnaySensor(coordinator, unit_id, description)
        for unit_id in coordinator.units
        for description in SENSORS
    )


class LossnaySensor(LossnayEntity, SensorEntity):
    """A sensor read from the Lossnay unit state."""

    entity_description: LossnaySensorDescription

    def __init__(
        self,
        coordinator: LossnayCoordinator,
        unit_id: str,
        description: LossnaySensorDescription,
    ) -> None:
        super().__init__(coordinator, unit_id)
        self.entity_description = description
        self._attr_unique_id = f"{unit_id}_{description.key}"

    @property
    def native_value(self):
        return self.entity_description.value_fn(self.state_data)
