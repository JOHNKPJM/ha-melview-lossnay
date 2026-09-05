"""Serve the optional Lossnay Lovelace cards."""

from __future__ import annotations

from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

CARD_URL = "/melview_lossnay/lossnay-card.js"


async def async_register_frontend(hass: HomeAssistant) -> None:
    path = Path(__file__).parent / "www" / "lossnay-card.js"
    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_URL, str(path), False)]
    )
