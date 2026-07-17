from datetime import date, datetime
from unittest.mock import MagicMock

from freezegun import freeze_time

from custom_components.cure_afvalbeheer.models import (
    CureData,
    Location,
    Notice,
    OpeningHours,
)
from custom_components.cure_afvalbeheer.sensor import (
    CureLocationSensor,
    CureNextTransitionSensor,
    CureReasonSensor,
)
from custom_components.cure_afvalbeheer.weekday import Weekday

_LOCATION = Location(
    name="Milieustraat Acht",
    address="Achtseweg Noord 41 5651 GG Eindhoven",
    hours=[
        OpeningHours(day=Weekday.MONDAY, opens="08:30", closes="17:00", closed=False),
        OpeningHours(day=Weekday.TUESDAY, opens="08:30", closes="17:00", closed=False),
        OpeningHours(day=Weekday.HOLIDAY, opens=None, closes=None, closed=True),
    ],
)

_LOCATION_LIST = [_LOCATION]


def _build_coordinator(
    notices: list[Notice] | None = None, locations: list[Location] | None = None
) -> MagicMock:
    coordinator = MagicMock()
    coordinator.data = CureData(
        locations=_LOCATION_LIST if locations is None else locations,
        notices=notices or [],
    )
    coordinator.municipality = "eindhoven"
    coordinator.last_update_success = True

    return coordinator


def _build_sensor(
    lookahead_days: int = 5,
    notices: list[Notice] | None = None,
    locations: list[Location] | None = None,
) -> CureLocationSensor:
    coordinator = _build_coordinator(notices, locations)

    entry = MagicMock()
    entry.entry_id = "test_entry"

    sensor = CureLocationSensor(coordinator, entry, _LOCATION.name, lookahead_days)
    sensor.hass = MagicMock()

    return sensor


def _build_reason_sensor(
    day_offset: int,
    label: str,
    notices: list[Notice] | None = None,
    locations: list[Location] | None = None,
) -> CureReasonSensor:
    coordinator = _build_coordinator(notices, locations)

    entry = MagicMock()
    entry.entry_id = "test_entry"

    sensor = CureReasonSensor(coordinator, entry, _LOCATION.name, day_offset, label)
    sensor.hass = MagicMock()

    return sensor


def _build_next_transition_sensor(
    transition: str,
    label: str,
    lookahead_days: int = 5,
    notices: list[Notice] | None = None,
    locations: list[Location] | None = None,
) -> CureNextTransitionSensor:
    coordinator = _build_coordinator(notices, locations)

    entry = MagicMock()
    entry.entry_id = "test_entry"

    sensor = CureNextTransitionSensor(
        coordinator, entry, _LOCATION.name, lookahead_days, transition, label
    )
    sensor.hass = MagicMock()

    return sensor


@freeze_time("2026-07-20 10:00:00")
def test_native_value_open_during_opening_hours():
    sensor = _build_sensor()

    assert sensor.native_value == "open"


@freeze_time("2026-07-20 18:00:00")
def test_native_value_closed_outside_opening_hours():
    sensor = _build_sensor()

    assert sensor.native_value == "closed"


@freeze_time("2026-07-19 10:00:00")
def test_native_value_closed_on_holiday_sunday():
    sensor = _build_sensor()

    assert sensor.native_value == "closed"


@freeze_time("2026-07-20 10:00:00")
def test_native_value_reflects_active_closure_notice():
    closure = Notice(
        reason="verbouwing",
        title="Let op!",
        closed=True,
        dates=[date(2026, 7, 20)],
    )

    sensor = _build_sensor(notices=[closure])

    assert sensor.native_value == "closed"


@freeze_time("2026-07-20 18:00:00")
def test_native_value_reflects_active_heat_protocol_extension():
    # Normally closed at 18:00, but a heat protocol notice extends hours.
    heat_protocol = Notice(
        reason="hitteprotocol",
        title="Hitteprotocol",
        closed=False,
        opens="08:00",
        closes="20:00",
        ends=date(2026, 7, 20),
    )

    sensor = _build_sensor(notices=[heat_protocol])

    assert sensor.native_value == "open"


@freeze_time("2026-07-20 10:00:00")
def test_extra_state_attributes_contains_today_and_upcoming():
    sensor = _build_sensor()

    attributes = sensor.extra_state_attributes

    assert attributes["today"] == {
        "date": "2026-07-20",
        "closed": False,
        "opens": "08:30",
        "closes": "17:00",
    }

    assert len(attributes["upcoming"]) == 5
    assert attributes["upcoming"][0]["date"] == "2026-07-21"
    assert attributes["upcoming"][0]["reason"] is None


@freeze_time("2026-07-20 10:00:00")
def test_extra_state_attributes_contains_address():
    sensor = _build_sensor()

    attributes = sensor.extra_state_attributes

    assert attributes["address"] == "Achtseweg Noord 41 5651 GG Eindhoven"


@freeze_time("2026-07-20 10:00:00")
def test_extra_state_attributes_respects_configured_lookahead_days():
    sensor = _build_sensor(lookahead_days=3)

    attributes = sensor.extra_state_attributes

    assert len(attributes["upcoming"]) == 3
    assert attributes["upcoming"][-1]["date"] == "2026-07-23"


@freeze_time("2026-07-20 10:00:00")
def test_extra_state_attributes_today_has_no_reason_key():
    """reason moved to its own CureReasonSensor; today stays closed-only."""

    closure = Notice(
        reason="verbouwing",
        title="Let op! Wordt verbouwd",
        closed=True,
        dates=[date(2026, 7, 20)],
    )

    sensor = _build_sensor(notices=[closure])

    attributes = sensor.extra_state_attributes

    assert attributes["today"]["closed"] is True
    assert "reason" not in attributes["today"]


@freeze_time("2026-07-20 10:00:00")
def test_extra_state_attributes_upcoming_still_has_reason():
    closure = Notice(
        reason="verbouwing",
        title="Let op! Wordt verbouwd",
        closed=True,
        dates=[date(2026, 7, 21)],
    )

    sensor = _build_sensor(notices=[closure])

    attributes = sensor.extra_state_attributes

    assert attributes["upcoming"][0]["date"] == "2026-07-21"
    assert attributes["upcoming"][0]["reason"] == "verbouwing"


@freeze_time("2026-07-20 10:00:00")
def test_location_sensor_available_when_location_present():
    sensor = _build_sensor()

    assert sensor.available is True


@freeze_time("2026-07-20 10:00:00")
def test_location_sensor_unavailable_when_location_gone():
    sensor = _build_sensor(locations=[])

    assert sensor.available is False


@freeze_time("2026-07-20 10:00:00")
def test_reason_sensor_today_empty_string_without_notice():
    sensor = _build_reason_sensor(day_offset=0, label="vandaag")

    assert sensor.native_value == ""


@freeze_time("2026-07-20 10:00:00")
def test_reason_sensor_today_reports_active_reason():
    closure = Notice(
        reason="verbouwing",
        title="Let op!",
        closed=True,
        dates=[date(2026, 7, 20)],
    )

    sensor = _build_reason_sensor(day_offset=0, label="vandaag", notices=[closure])

    assert sensor.native_value == "verbouwing"


@freeze_time("2026-07-20 10:00:00")
def test_reason_sensor_tomorrow_reports_next_day_reason():
    closure = Notice(
        reason="werkzaamheden",
        title="Let op!",
        closed=True,
        dates=[date(2026, 7, 21)],
    )

    today_sensor = _build_reason_sensor(
        day_offset=0, label="vandaag", notices=[closure]
    )
    tomorrow_sensor = _build_reason_sensor(
        day_offset=1, label="morgen", notices=[closure]
    )

    assert today_sensor.native_value == ""
    assert tomorrow_sensor.native_value == "werkzaamheden"


@freeze_time("2026-07-20 10:00:00")
def test_reason_sensor_unavailable_when_location_gone():
    sensor = _build_reason_sensor(day_offset=0, label="vandaag", locations=[])

    assert sensor.available is False
    assert sensor.native_value is None


def test_reason_sensor_unique_id_and_name():
    sensor = _build_reason_sensor(day_offset=1, label="morgen")

    assert sensor.unique_id == "test_entry_milieustraat_acht_reden_morgen"
    assert sensor.name == "Milieustraat Acht reden morgen"


@freeze_time("2026-07-20 10:00:00")
def test_next_transition_sensor_close_when_currently_open():
    sensor = _build_next_transition_sensor("close", "volgende gesloten")

    assert sensor.native_value.replace(tzinfo=None) == datetime(2026, 7, 20, 17, 0)


@freeze_time("2026-07-20 10:00:00")
def test_next_transition_sensor_open_when_currently_open_returns_tomorrow():
    sensor = _build_next_transition_sensor("open", "volgende open")

    assert sensor.native_value.replace(tzinfo=None) == datetime(2026, 7, 21, 8, 30)


@freeze_time("2026-07-20 18:00:00")
def test_next_transition_sensor_open_when_currently_closed():
    sensor = _build_next_transition_sensor("open", "volgende open")

    assert sensor.native_value.replace(tzinfo=None) == datetime(2026, 7, 21, 8, 30)


@freeze_time("2026-07-20 10:00:00")
def test_next_transition_sensor_unavailable_when_location_gone():
    sensor = _build_next_transition_sensor("open", "volgende open", locations=[])

    assert sensor.available is False
    assert sensor.native_value is None


def test_next_transition_sensor_unique_id_and_name():
    sensor = _build_next_transition_sensor("close", "volgende gesloten")

    assert sensor.unique_id == "test_entry_milieustraat_acht_volgende_close"
    assert sensor.name == "Milieustraat Acht volgende gesloten"
