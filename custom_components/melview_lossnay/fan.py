"""Fan platform for Mitsubishi Lossnay via Melview."""

from __future__ import annotations

from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    FAN_AUTO_PRESET,
    FAN_AUTO_VALUE,
    FAN_VALUE_TO_PERCENTAGE,
    PERCENTAGE_TO_FAN_VALUE,
)
from .coordinator import LossnayCoordinator
from .entity import LossnayEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Lossnay fan entities."""
    coordinator: LossnayCoordinator = entry.runtime_data
    async_add_entities(LossnayFan(coordinator, unit_id) for unit_id in coordinator.units)


class LossnayFan(LossnayEntity, FanEntity):
    """Power and fan-speed control for a Lossnay ERV."""

    _attr_name = None
    _attr_supported_features = (
        FanEntityFeature.SET_SPEED
        | FanEntityFeature.PRESET_MODE
        | FanEntityFeature.TURN_ON
        | FanEntityFeature.TURN_OFF
    )
    _attr_speed_count = 4
    _attr_preset_modes = [FAN_AUTO_PRESET]

    def __init__(self, coordinator: LossnayCoordinator, unit_id: str) -> None:
        super().__init__(coordinator, unit_id)
        self._attr_unique_id = f"{unit_id}_fan"

    @property
    def is_on(self) -> bool | None:
        value = self.state_data.get("power")
        return bool(int(value)) if value is not None else None

    @property
    def percentage(self) -> int | None:
        if not self.is_on:
            return 0
        try:
            fan_value = int(self.state_data.get("setfan"))
        except (TypeError, ValueError):
            return None
        if fan_value == FAN_AUTO_VALUE:
            return None
        return FAN_VALUE_TO_PERCENTAGE.get(fan_value)

    @property
    def preset_mode(self) -> str | None:
        try:
            fan_value = int(self.state_data.get("setfan"))
        except (TypeError, ValueError):
            return None
        return FAN_AUTO_PRESET if fan_value == FAN_AUTO_VALUE else None

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        await self.coordinator.async_send_command(self.unit_id, "PW1")
        if preset_mode is not None:
            await self.async_set_preset_mode(preset_mode)
        elif percentage is not None:
            await self.async_set_percentage(percentage)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_send_command(self.unit_id, "PW0")

    async def async_set_percentage(self, percentage: int) -> None:
        if percentage <= 0:
            await self.async_turn_off()
            return

        # Snap arbitrary HA percentages to the nearest of the four supported stages.
        nearest = min(PERCENTAGE_TO_FAN_VALUE, key=lambda p: abs(p - percentage))
        value = PERCENTAGE_TO_FAN_VALUE[nearest]
        if not self.is_on:
            await self.coordinator.async_send_command(self.unit_id, "PW1")
        await self.coordinator.async_send_command(self.unit_id, f"FS{value}")

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        if preset_mode != FAN_AUTO_PRESET:
            raise ValueError(f"Unsupported preset mode: {preset_mode}")
        if not self.is_on:
            await self.coordinator.async_send_command(self.unit_id, "PW1")
        await self.coordinator.async_send_command(self.unit_id, "FS0")
