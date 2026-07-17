from datetime import date
from unittest.mock import MagicMock

from freezegun import freeze_time

from custom_components.cure_afvalbeheer.models import (
    CureData,
    Location,
    Notice,
    OpeningHours,
)
from custom_components.cure_afvalbeheer.sensor import CureLocationSensor
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


def _build_sensor(
    lookahead_days: int = 5, notices: list[Notice] | None = None
) -> CureLocationSensor:
    coordinator = MagicMock()
    coordinator.data = CureData(locations=[_LOCATION], notices=notices or [])
    coordinator.municipality = "eindhoven"

    entry = MagicMock()
    entry.entry_id = "test_entry"

    sensor = CureLocationSensor(coordinator, entry, _LOCATION.name, lookahead_days)
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
        "reason": None,
    }

    assert len(attributes["upcoming"]) == 5
    assert attributes["upcoming"][0]["date"] == "2026-07-21"


@freeze_time("2026-07-20 10:00:00")
def test_extra_state_attributes_respects_configured_lookahead_days():
    sensor = _build_sensor(lookahead_days=3)

    attributes = sensor.extra_state_attributes

    assert len(attributes["upcoming"]) == 3
    assert attributes["upcoming"][-1]["date"] == "2026-07-23"


@freeze_time("2026-07-20 10:00:00")
def test_extra_state_attributes_includes_reason_for_active_notice():
    closure = Notice(
        reason="verbouwing",
        title="Let op! Wordt verbouwd",
        closed=True,
        dates=[date(2026, 7, 20)],
    )

    sensor = _build_sensor(notices=[closure])

    attributes = sensor.extra_state_attributes

    assert attributes["today"]["closed"] is True
    assert attributes["today"]["reason"] == "verbouwing"
