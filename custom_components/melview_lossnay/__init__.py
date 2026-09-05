"""Mitsubishi Lossnay integration using the AU/NZ Melview service."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import MelviewApi, MelviewError
from .const import CONF_APP_VERSION, DEFAULT_APP_VERSION, DOMAIN, MODE_TO_COMMAND, PLATFORMS
from .coordinator import LossnayCoordinator
from .frontend import async_register_frontend
from .maintenance import LossnayMaintenanceManager
from .schedule_manager import LossnayScheduleManager

DATA_FRONTEND_REGISTERED = f"{DOMAIN}_frontend_registered"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Mitsubishi Lossnay from a config entry."""
    session = async_get_clientsession(hass)
    api = MelviewApi(
        session=session,
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
        app_version=entry.data.get(CONF_APP_VERSION, DEFAULT_APP_VERSION),
    )

    try:
        raw_units = await api.async_get_units(erv_only=True)
        units = {str(unit["unitid"]): unit for unit in raw_units if unit.get("unitid")}
        capabilities = {unit_id: await api.async_get_capabilities(unit_id) for unit_id in units}
    except MelviewError:
        return False

    if not units:
        return False

    coordinator = LossnayCoordinator(hass, api, units, capabilities)
    await coordinator.async_config_entry_first_refresh()

    coordinator.ha_schedule_managers = {}
    coordinator.maintenance_managers = {}
    for unit_id in units:
        schedule_manager = LossnayScheduleManager(hass, coordinator, unit_id)
        await schedule_manager.async_load()
        coordinator.ha_schedule_managers[unit_id] = schedule_manager

        maintenance_manager = LossnayMaintenanceManager(hass, unit_id)
        await maintenance_manager.async_load()
        coordinator.maintenance_managers[unit_id] = maintenance_manager

    entry.runtime_data = coordinator

    if not hass.data.get(DATA_FRONTEND_REGISTERED):
        await async_register_frontend(hass)
        hass.data[DATA_FRONTEND_REGISTERED] = True

    async def get_manager(call: ServiceCall):
        unit_id = str(call.data["unit_id"])
        manager = coordinator.maintenance_managers.get(unit_id)
        if manager is None:
            raise ValueError(f"Unknown Lossnay unit: {unit_id}")
        return manager

    async def set_maintenance_enabled(call: ServiceCall) -> None:
        manager = await get_manager(call)
        await manager.async_set_enabled(bool(call.data["enabled"]))

    async def set_maintenance_interval(call: ServiceCall) -> None:
        manager = await get_manager(call)
        await manager.async_set_interval(str(call.data["item"]), int(call.data["months"]))

    async def mark_maintenance_done(call: ServiceCall) -> None:
        manager = await get_manager(call)
        await manager.async_mark_done(str(call.data["item"]))

    async def set_ventilation_mode(call: ServiceCall) -> None:
        unit_id = str(call.data["unit_id"])
        mode = str(call.data["mode"])
        command = MODE_TO_COMMAND.get(mode)
        if unit_id not in coordinator.units or command is None:
            raise ValueError("Invalid Lossnay unit or ventilation mode")
        await coordinator.async_send_command(unit_id, command)

    hass.services.async_register(
        DOMAIN,
        "set_maintenance_enabled",
        set_maintenance_enabled,
        schema=vol.Schema({vol.Required("unit_id"): str, vol.Required("enabled"): bool}),
    )
    hass.services.async_register(
        DOMAIN,
        "set_maintenance_interval",
        set_maintenance_interval,
        schema=vol.Schema({vol.Required("unit_id"): str, vol.Required("item"): vol.In(["wash", "replace", "core"]), vol.Required("months"): vol.Coerce(int)}),
    )
    hass.services.async_register(
        DOMAIN,
        "mark_maintenance_done",
        mark_maintenance_done,
        schema=vol.Schema({vol.Required("unit_id"): str, vol.Required("item"): vol.In(["wash", "replace", "core"])}),
    )
    hass.services.async_register(
        DOMAIN,
        "set_ventilation_mode",
        set_ventilation_mode,
        schema=vol.Schema({vol.Required("unit_id"): str, vol.Required("mode"): vol.In(list(MODE_TO_COMMAND))}),
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    coordinator = entry.runtime_data
    for manager in getattr(coordinator, "ha_schedule_managers", {}).values():
        await manager.async_shutdown()
    for manager in getattr(coordinator, "maintenance_managers", {}).values():
        await manager.async_shutdown()
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        for service in (
            "set_maintenance_enabled",
            "set_maintenance_interval",
            "mark_maintenance_done",
            "set_ventilation_mode",
        ):
            hass.services.async_remove(DOMAIN, service)
    return unloaded
