"""Async client for the Mitsubishi Electric AU/NZ Melview API."""

from __future__ import annotations

import asyncio
from typing import Any

from aiohttp import ClientError, ClientResponse, ClientSession

from .const import BASE_URL, DEFAULT_APP_VERSION


class MelviewError(Exception):
    """Base Melview exception."""


class MelviewAuthError(MelviewError):
    """Authentication failed."""


class MelviewConnectionError(MelviewError):
    """Connection to Melview failed."""


class MelviewApi:
    """Small client for the Melview endpoints used by Lossnay ERVs."""

    def __init__(
        self,
        session: ClientSession,
        username: str,
        password: str,
        app_version: str = DEFAULT_APP_VERSION,
    ) -> None:
        self._session = session
        self._username = username
        self._password = password
        self._app_version = app_version
        self._authenticated = False
        self._auth_lock = asyncio.Lock()

    async def async_login(self) -> None:
        """Authenticate to Melview."""
        async with self._auth_lock:
            payload = {
                "user": self._username,
                "pass": self._password,
                "appversion": self._app_version,
            }
            response = await self._request_raw("POST", "login.aspx", json=payload)
            if response.status in (401, 403):
                await response.release()
                self._authenticated = False
                raise MelviewAuthError("Melview rejected the supplied credentials")
            if response.status >= 400:
                text = await response.text()
                raise MelviewConnectionError(
                    f"Melview login failed with HTTP {response.status}: {text[:200]}"
                )
            await response.read()
            self._authenticated = True

    async def async_get_rooms(self) -> list[dict[str, Any]]:
        """Return all buildings/rooms returned by Melview."""
        data = await self._request_json("POST", "rooms.aspx")
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return [data]
        raise MelviewError("Unexpected rooms response from Melview")

    async def async_get_units(self, erv_only: bool = True) -> list[dict[str, Any]]:
        """Flatten units from the rooms/buildings response."""
        buildings = await self.async_get_rooms()
        units: list[dict[str, Any]] = []
        for building in buildings:
            building_name = building.get("building")
            raw_units = building.get("units", [])
            if not isinstance(raw_units, list):
                continue
            for raw in raw_units:
                if not isinstance(raw, dict):
                    continue
                unit = dict(raw)
                unit["building"] = building_name
                if erv_only and str(unit.get("type", "")).upper() != "ERV":
                    continue
                units.append(unit)
        return units

    async def async_get_capabilities(self, unit_id: str) -> dict[str, Any]:
        """Read model/capability metadata for a unit."""
        return await self._request_json(
            "POST",
            "unitcapabilities.aspx",
            json={"unitid": str(unit_id), "v": 2},
        )

    async def async_get_state(self, unit_id: str) -> dict[str, Any]:
        """Read current state without changing the unit."""
        return await self._request_json(
            "POST",
            "unitcommand.aspx",
            json={"unitid": str(unit_id), "v": 2},
        )

    async def async_command(self, unit_id: str, command: str) -> dict[str, Any]:
        """Send one compact Melview command, e.g. PW1, FS2, MD3."""
        data = await self._request_json(
            "POST",
            "unitcommand.aspx",
            json={"unitid": str(unit_id), "v": 2, "commands": command},
        )
        if str(data.get("error", "ok")).lower() != "ok":
            raise MelviewError(f"Melview command failed: {data.get('error')}")
        return data

    async def _request_raw(self, method: str, endpoint: str, **kwargs: Any) -> ClientResponse:
        """Make a raw HTTP request and normalize transport errors."""
        url = f"{BASE_URL}/{endpoint}"
        headers = kwargs.pop("headers", {})
        headers.setdefault("Accept", "application/json, text/javascript, */*")
        try:
            return await self._session.request(
                method,
                url,
                headers=headers,
                timeout=15,
                **kwargs,
            )
        except (ClientError, TimeoutError) as err:
            raise MelviewConnectionError(f"Unable to reach Melview: {err}") from err

    async def _request_json(
        self,
        method: str,
        endpoint: str,
        *,
        _retry_auth: bool = True,
        **kwargs: Any,
    ) -> dict[str, Any] | list[Any]:
        """Make an authenticated request and decode JSON."""
        if not self._authenticated:
            await self.async_login()

        response = await self._request_raw(method, endpoint, **kwargs)
        if response.status in (401, 403):
            await response.release()
            self._authenticated = False
            if _retry_auth:
                await self.async_login()
                return await self._request_json(
                    method,
                    endpoint,
                    _retry_auth=False,
                    **kwargs,
                )
            raise MelviewAuthError("Melview session expired or authentication failed")

        if response.status >= 400:
            text = await response.text()
            raise MelviewConnectionError(
                f"Melview returned HTTP {response.status}: {text[:200]}"
            )

        try:
            data = await response.json(content_type=None)
        except (ValueError, ClientError) as err:
            text = await response.text()
            raise MelviewError(f"Invalid JSON from Melview: {text[:200]}") from err

        if not isinstance(data, (dict, list)):
            raise MelviewError("Unexpected response type from Melview")
        return data
