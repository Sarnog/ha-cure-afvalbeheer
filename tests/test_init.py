from pathlib import Path
from unittest.mock import AsyncMock, patch

from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.cure_afvalbeheer.const import (
    CONF_LOOKAHEAD_DAYS,
    CONF_MUNICIPALITY,
    CONF_UPDATE_INTERVAL_MINUTES,
    DOMAIN,
)
from custom_components.cure_afvalbeheer.models import CureData, Location


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

    # 2 locations in the fixture x (1 status sensor + 2 reason sensors)
    assert len(entries) == 6

    status_entries = [e for e in entries if "_reden_" not in e.unique_id]
    reason_entries = [e for e in entries if "_reden_" in e.unique_id]

    assert len(status_entries) == 2
    assert len(reason_entries) == 4

    for registry_entry in status_entries:
        state = hass.states.get(registry_entry.entity_id)

        assert state is not None
        assert state.state in ("open", "closed")
        assert "today" in state.attributes
        assert "upcoming" in state.attributes
        assert len(state.attributes["upcoming"]) == 5

    # The fixture has an active, indefinite "verbouwing" closure notice for
    # Lodewijkstraat (no end date), so its reason sensors report that reason
    # for both today and tomorrow; Acht has no active notice, so its reason
    # sensors stay empty - not "unknown".
    for registry_entry in reason_entries:
        state = hass.states.get(registry_entry.entity_id)

        assert state is not None

        if "lodewijkstraat" in registry_entry.unique_id:
            assert state.state == "verbouwing"
        else:
            assert state.state == ""


async def test_new_location_gets_entities_without_restart(
    hass, enable_custom_integrations
) -> None:
    """A location added later (no restart) should still get its entities."""

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

    registry = er.async_get(hass)

    before = er.async_entries_for_config_entry(registry, entry.entry_id)
    assert len(before) == 6

    coordinator = entry.runtime_data

    new_location = Location(
        name="Milieustraat Nieuw",
        address="Nieuwstraat 1 5600 AA Eindhoven",
        hours=coordinator.data.locations[0].hours,
    )

    coordinator.async_set_updated_data(
        CureData(
            locations=[*coordinator.data.locations, new_location],
            notices=coordinator.data.notices,
        )
    )
    await hass.async_block_till_done()

    after = er.async_entries_for_config_entry(registry, entry.entry_id)

    # 3 locations now x 3 entities each, without a restart.
    assert len(after) == 9


async def test_setup_survives_float_options_from_before_the_fix(
    hass, enable_custom_integrations
) -> None:
    """Regression test: NumberSelector always stores floats.

    Home Assistant's NumberSelector coerces to float regardless of
    step/mode, so an entry saved before the int() fix has
    lookahead_days/update_interval_minutes stored as float. Setup must not
    crash on that (range() rejects a float), and it must self-heal without
    the user having to resubmit the options form.
    """

    html = Path("tests/fixtures/milieustraat_eindhoven.html").read_text(
        encoding="utf-8"
    )

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_MUNICIPALITY: "eindhoven"},
        options={CONF_LOOKAHEAD_DAYS: 10.0, CONF_UPDATE_INTERVAL_MINUTES: 30.0},
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.cure_afvalbeheer.api.CureApiClient.fetch_html",
        AsyncMock(return_value=html),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state.value == "loaded"

    coordinator = entry.runtime_data
    assert coordinator.update_interval.total_seconds() == 30 * 60

    registry = er.async_get(hass)
    status_entry = next(
        e
        for e in er.async_entries_for_config_entry(registry, entry.entry_id)
        if "_reden_" not in e.unique_id
    )
    state = hass.states.get(status_entry.entity_id)

    assert state is not None
    assert len(state.attributes["upcoming"]) == 10
