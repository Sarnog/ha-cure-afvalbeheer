"""The Cure Afvalbeheer integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client

from .api import CureApiClient
from .coordinator import CureDataUpdateCoordinator

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
]

type CureConfigEntry = ConfigEntry[CureDataUpdateCoordinator]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CureConfigEntry,
) -> bool:
    """Set up Cure Afvalbeheer from a config entry."""

    session = aiohttp_client.async_get_clientsession(hass)
    api = CureApiClient(session)
    coordinator = CureDataUpdateCoordinator(hass, api, entry)

    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(
        entry,
        PLATFORMS,
    )

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: CureConfigEntry,
) -> bool:
    """Unload Cure Afvalbeheer."""

    return await hass.config_entries.async_unload_platforms(
        entry,
        PLATFORMS,
    )
