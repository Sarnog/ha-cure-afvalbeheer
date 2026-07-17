from pathlib import Path
from unittest.mock import AsyncMock, patch

from homeassistant.config_entries import SOURCE_USER
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.cure_afvalbeheer.const import (
    CONF_LOOKAHEAD_DAYS,
    CONF_MUNICIPALITY,
    CONF_UPDATE_INTERVAL_MINUTES,
    DEFAULT_UPDATE_INTERVAL_MINUTES,
    DOMAIN,
)


async def test_user_flow_creates_entry_per_municipality(
    hass, enable_custom_integrations
) -> None:
    """Test that picking a municipality creates a correctly titled entry."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_MUNICIPALITY: "valkenswaard"},
    )

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Valkenswaard"
    assert result2["data"] == {CONF_MUNICIPALITY: "valkenswaard"}


async def test_user_flow_aborts_for_already_configured_municipality(
    hass, enable_custom_integrations
) -> None:
    """Test that the same municipality cannot be added twice."""

    existing = MockConfigEntry(
        domain=DOMAIN,
        unique_id="eindhoven",
        data={CONF_MUNICIPALITY: "eindhoven"},
    )
    existing.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_MUNICIPALITY: "eindhoven"},
    )

    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "already_configured"


async def test_user_flow_allows_different_municipality(
    hass, enable_custom_integrations
) -> None:
    """Test that a second entry for a different municipality is allowed."""

    existing = MockConfigEntry(
        domain=DOMAIN,
        unique_id="eindhoven",
        data={CONF_MUNICIPALITY: "eindhoven"},
    )
    existing.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_MUNICIPALITY: "valkenswaard"},
    )

    assert result2["type"] is FlowResultType.CREATE_ENTRY


async def test_options_flow_updates_lookahead_days(
    hass, enable_custom_integrations
) -> None:
    """Test that the options flow updates and persists lookahead_days."""

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

        result = await hass.config_entries.options.async_init(entry.entry_id)

        assert result["type"] is FlowResultType.FORM

        default_update_interval = result["data_schema"]({})[
            CONF_UPDATE_INTERVAL_MINUTES
        ]
        assert default_update_interval == DEFAULT_UPDATE_INTERVAL_MINUTES

        result2 = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {CONF_LOOKAHEAD_DAYS: 7, CONF_UPDATE_INTERVAL_MINUTES: 30},
        )

        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY

    # NumberSelector always coerces to float during schema validation
    # (regardless of step/mode), so the flow must coerce back to int
    # before storing - otherwise range(lookahead_days + 1) crashes later.
    assert entry.options[CONF_LOOKAHEAD_DAYS] == 7
    assert isinstance(entry.options[CONF_LOOKAHEAD_DAYS], int)
    assert entry.options[CONF_UPDATE_INTERVAL_MINUTES] == 30
    assert isinstance(entry.options[CONF_UPDATE_INTERVAL_MINUTES], int)
