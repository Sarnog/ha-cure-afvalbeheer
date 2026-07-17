from pathlib import Path
from unittest.mock import AsyncMock, patch

from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.cure_afvalbeheer.const import CONF_MUNICIPALITY, DOMAIN


async def test_setup_entry_creates_sensors(hass, enable_custom_integrations) -> None:
    """Test that setting up the config entry wires up working sensors."""

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

    assert entry.state.value == "loaded"

    registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(registry, entry.entry_id)

    assert len(entries) == 2

    for registry_entry in entries:
        state = hass.states.get(registry_entry.entity_id)

        assert state is not None
        assert state.state in ("open", "closed")
        assert "today" in state.attributes
        assert "upcoming" in state.attributes
        assert len(state.attributes["upcoming"]) == 5
