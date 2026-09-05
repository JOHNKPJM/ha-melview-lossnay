"""Mitsubishi Lossnay integration using the AU/NZ Melview service."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import MelviewApi, MelviewError
from .const import CONF_APP_VERSION, DEFAULT_APP_VERSION, DOMAIN, PLATFORMS
from .coordinator import LossnayCoordinator


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
        capabilities = {
            unit_id: await api.async_get_capabilities(unit_id) for unit_id in units
        }
    except MelviewError:
        return False

    if not units:
        return False

    coordinator = LossnayCoordinator(hass, api, units, capabilities)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
