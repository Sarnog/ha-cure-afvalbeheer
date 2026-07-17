from datetime import date

from custom_components.cure_afvalbeheer.models import Location, OpeningHours
from custom_components.cure_afvalbeheer.schedule import (
    hours_for_date,
    upcoming_hours,
)
from custom_components.cure_afvalbeheer.weekday import Weekday

_MONDAY = OpeningHours(day=Weekday.MONDAY, opens="08:30", closes="17:00", closed=False)
_HOLIDAY = OpeningHours(day=Weekday.HOLIDAY, opens=None, closes=None, closed=True)

_LOCATION = Location(
    name="Milieustraat Acht",
    address="Achtseweg Noord 41 5651 GG Eindhoven",
    hours=[_MONDAY, _HOLIDAY],
)


def test_hours_for_date_matches_weekday():
    monday = date(2026, 7, 20)

    result = hours_for_date(_LOCATION, monday)

    assert result is _MONDAY


def test_hours_for_date_falls_back_to_holiday_on_sunday():
    sunday = date(2026, 7, 19)

    result = hours_for_date(_LOCATION, sunday)

    assert result is _HOLIDAY


def test_hours_for_date_returns_none_when_no_match():
    tuesday = date(2026, 7, 21)

    result = hours_for_date(_LOCATION, tuesday)

    assert result is None


def test_upcoming_hours_returns_requested_number_of_days():
    monday = date(2026, 7, 20)

    result = upcoming_hours(_LOCATION, monday, days=6)

    assert len(result) == 6
    assert result[0] == (monday, _MONDAY)
    assert result[-1][0] == date(2026, 7, 25)
