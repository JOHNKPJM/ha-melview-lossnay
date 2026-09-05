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

from .const import FAN_VALUE_TO_HEAT_RECOVERY
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


def _heat_recovery_efficiency(data: dict[str, Any]) -> float | None:
    """Return the Mitsubishi app heat-recovery figure for the active fan stage."""
    try:
        if not bool(int(data.get("power", 0))):
            return None
    except (TypeError, ValueError):
        return None

    try:
        mode_value = int(data.get("setmode"))
    except (TypeError, ValueError):
        mode_value = None
    if mode_value == 7:  # Explicit bypass has no heat-recovery figure.
        return None

    try:
        fan_value = int(data.get("setfan"))
    except (TypeError, ValueError):
        fan_value = None

    if fan_value in FAN_VALUE_TO_HEAT_RECOVERY:
        return FAN_VALUE_TO_HEAT_RECOVERY[fan_value]

    # Auto fan does not map to one fixed stage. Melview currently reports the
    # core figure as a decimal (for example 0.79), so use it when available.
    api_value = _number(data, "coreefficiency")
    if api_value is None:
        return None
    return round(api_value * 100, 1) if api_value <= 1 else round(api_value, 1)



def _active_efficiency_fraction(data: dict[str, Any]) -> float | None:
    """Return the active heat-transfer efficiency as a 0-1 fraction."""
    try:
        mode_value = int(data.get("setmode"))
    except (TypeError, ValueError):
        mode_value = None
    if mode_value == 7:
        return None

    try:
        fan_value = int(data.get("setfan"))
    except (TypeError, ValueError):
        fan_value = None
    if fan_value in FAN_VALUE_TO_HEAT_RECOVERY:
        return FAN_VALUE_TO_HEAT_RECOVERY[fan_value] / 100

    api_value = _number(data, "coreefficiency")
    if api_value is None:
        return None
    return api_value if api_value <= 1 else api_value / 100


def _pre_warmed_air(data: dict[str, Any]) -> float | None:
    """Reproduce the app's supply-side Lossnay Core temperature."""
    try:
        if int(data.get("setmode")) == 7:
            return None
    except (TypeError, ValueError):
        pass
    fresh = _number(data, "outdoortemp")
    stale = _number(data, "roomtemp")
    efficiency = _active_efficiency_fraction(data)
    if fresh is not None and stale is not None and efficiency is not None:
        return round(fresh + efficiency * (stale - fresh), 1)
    return _number(data, "supplytemp")


def _exhaust_air(data: dict[str, Any]) -> float | None:
    """Reproduce the app's exhaust-side Lossnay Core temperature."""
    try:
        if int(data.get("setmode")) == 7:
            return None
    except (TypeError, ValueError):
        pass
    fresh = _number(data, "outdoortemp")
    stale = _number(data, "roomtemp")
    efficiency = _active_efficiency_fraction(data)
    if fresh is not None and stale is not None and efficiency is not None:
        return round(stale - efficiency * (stale - fresh), 1)
    return _number(data, "exhausttemp")


def _temperature_change(data: dict[str, Any]) -> float | None:
    fresh = _number(data, "outdoortemp")
    supply = _pre_warmed_air(data)
    if fresh is None or supply is None:
        return None
    return round(supply - fresh, 1)


SENSORS: tuple[LossnaySensorDescription, ...] = (
    LossnaySensorDescription(
        key="outdoor_temperature",
        name="Fresh Air In",
        icon="mdi:thermometer-chevron-down",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=1,
        value_fn=lambda d: _number(d, "outdoortemp"),
    ),
    LossnaySensorDescription(
        key="room_temperature",
        name="Stale Air Out",
        icon="mdi:thermometer-chevron-up",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=1,
        value_fn=lambda d: _number(d, "roomtemp"),
    ),
    LossnaySensorDescription(
        key="exhaust_temperature",
        name="Exhaust Air",
        icon="mdi:home-export-outline",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=1,
        value_fn=_exhaust_air,
    ),
    LossnaySensorDescription(
        key="supply_temperature",
        name="Pre-warmed",
        icon="mdi:home-import-outline",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=1,
        value_fn=_pre_warmed_air,
    ),
    LossnaySensorDescription(
        key="core_efficiency",
        name="Heat recovery efficiency",
        icon="mdi:heat-wave",
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=0,
        value_fn=_heat_recovery_efficiency,
    ),
    LossnaySensorDescription(
        key="air_temperature_change",
        name="Incoming air temperature change",
        icon="mdi:thermometer-lines",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=1,
        value_fn=_temperature_change,
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
