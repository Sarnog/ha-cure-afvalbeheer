from datetime import timedelta
from unittest.mock import AsyncMock

import pytest
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.cure_afvalbeheer.const import DOMAIN, ISSUE_NO_LOCATIONS_FOUND
from custom_components.cure_afvalbeheer.coordinator import (
    CureDataUpdateCoordinator,
)
from custom_components.cure_afvalbeheer.exceptions import CureApiError
from custom_components.cure_afvalbeheer.models import CureData, Location, OpeningHours
from custom_components.cure_afvalbeheer.weekday import Weekday


async def test_async_update_data(hass) -> None:
    """Test coordinator updates data."""

    api = AsyncMock()
    api.fetch_milieustraat.return_value = CureData(locations=[])

    coordinator = CureDataUpdateCoordinator(
        hass=hass,
        api=api,
        config_entry=MockConfigEntry(),
        municipality="eindhoven",
        update_interval_minutes=60,
    )

    result = await coordinator._async_update_data()

    api.fetch_milieustraat.assert_awaited_once_with("eindhoven")
    assert result == CureData(locations=[])
    assert coordinator.update_interval == timedelta(minutes=60)


async def test_async_update_data_raises_update_failed(hass) -> None:
    """Test that API errors are converted to UpdateFailed."""

    api = AsyncMock()
    api.fetch_milieustraat.side_effect = CureApiError("boom")

    coordinator = CureDataUpdateCoordinator(
        hass=hass,
        api=api,
        config_entry=MockConfigEntry(),
        municipality="eindhoven",
        update_interval_minutes=60,
    )

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


async def test_creates_repair_issue_when_no_locations_found(hass) -> None:
    """A successful fetch that finds no locations creates a repair issue."""

    entry = MockConfigEntry()

    api = AsyncMock()
    api.fetch_milieustraat.return_value = CureData(locations=[])

    coordinator = CureDataUpdateCoordinator(
        hass=hass,
        api=api,
        config_entry=entry,
        municipality="eindhoven",
        update_interval_minutes=60,
    )

    await coordinator._async_update_data()

    issue_registry = ir.async_get(hass)
    issue_id = f"{ISSUE_NO_LOCATIONS_FOUND}_{entry.entry_id}"

    assert issue_registry.async_get_issue(DOMAIN, issue_id) is not None


async def test_clears_repair_issue_once_locations_reappear(hass) -> None:
    """The repair issue is removed again once locations are found."""

    entry = MockConfigEntry()

    location = Location(
        name="Milieustraat Acht",
        address="Achtseweg Noord 41",
        hours=[
            OpeningHours(
                day=Weekday.MONDAY, opens="08:30", closes="17:00", closed=False
            )
        ],
    )

    api = AsyncMock()
    api.fetch_milieustraat.return_value = CureData(locations=[])

    coordinator = CureDataUpdateCoordinator(
        hass=hass,
        api=api,
        config_entry=entry,
        municipality="eindhoven",
        update_interval_minutes=60,
    )

    await coordinator._async_update_data()

    api.fetch_milieustraat.return_value = CureData(locations=[location])

    await coordinator._async_update_data()

    issue_registry = ir.async_get(hass)
    issue_id = f"{ISSUE_NO_LOCATIONS_FOUND}_{entry.entry_id}"

    assert issue_registry.async_get_issue(DOMAIN, issue_id) is None
