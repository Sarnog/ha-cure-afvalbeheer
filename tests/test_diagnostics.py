from pathlib import Path
from unittest.mock import AsyncMock, patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.cure_afvalbeheer.const import CONF_MUNICIPALITY, DOMAIN
from custom_components.cure_afvalbeheer.diagnostics import (
    async_get_config_entry_diagnostics,
)


async def test_diagnostics_serialises_locations_and_notices(
    hass, enable_custom_integrations
) -> None:
    """Test that diagnostics return a plain, serialisable data dump."""

    html = Path("tests/fixtures/milieustraat_eindhoven.html").read_text(
        encoding="utf-8"
    )

    entry = MockConfigEntry(domain=DOMAIN, data={CONF_MUNICIPALITY: "eindhoven"})
    entry.add_to_hass(hass)

    with patch(
        "custom_components.cure_afvalbeheer.api.CureApiClient.fetch_html",
        AsyncMock(return_value=html),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert diagnostics["entry"]["data"] == {CONF_MUNICIPALITY: "eindhoven"}
    assert diagnostics["coordinator"]["last_update_success"] is True
    assert diagnostics["coordinator"]["update_interval_seconds"] == 3600

    locations = diagnostics["coordinator"]["data"]["locations"]
    assert len(locations) == 2

    acht = next(loc for loc in locations if loc["name"] == "Milieustraat Acht")
    assert acht["address"] == "Achtseweg Noord 41 5651 GG Eindhoven"
    assert len(acht["hours"]) == 7
    assert acht["hours"][0] == {
        "day": "monday",
        "opens": "08:30",
        "closes": "17:00",
        "closed": False,
    }

    notices = diagnostics["coordinator"]["data"]["notices"]
    closure = next(n for n in notices if n["reason"] == "verbouwing")
    assert closure["location_hint"] == "Milieustraat Lodewijkstraat"
    assert closure["starts"] is None
    assert closure["ends"] is None
