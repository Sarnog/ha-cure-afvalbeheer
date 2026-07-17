from unittest.mock import AsyncMock

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.cure_afvalbeheer.coordinator import (
    CureDataUpdateCoordinator,
)
from custom_components.cure_afvalbeheer.exceptions import CureApiError
from custom_components.cure_afvalbeheer.models import CureData


async def test_async_update_data(hass) -> None:
    """Test coordinator updates data."""

    api = AsyncMock()
    api.fetch_milieustraat.return_value = CureData(locations=[])

    coordinator = CureDataUpdateCoordinator(
        hass=hass,
        api=api,
        config_entry=MockConfigEntry(),
        municipality="eindhoven",
    )

    result = await coordinator._async_update_data()

    api.fetch_milieustraat.assert_awaited_once_with("eindhoven")
    assert result == CureData(locations=[])


async def test_async_update_data_raises_update_failed(hass) -> None:
    """Test that API errors are converted to UpdateFailed."""

    api = AsyncMock()
    api.fetch_milieustraat.side_effect = CureApiError("boom")

    coordinator = CureDataUpdateCoordinator(
        hass=hass,
        api=api,
        config_entry=MockConfigEntry(),
        municipality="eindhoven",
    )

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()
