from datetime import date, datetime

from custom_components.cure_afvalbeheer.models import Location, Notice, OpeningHours
from custom_components.cure_afvalbeheer.schedule import (
    hours_for_date,
    next_open_close,
    resolve_day,
    resolve_upcoming,
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

_MON_TUE_LOCATION = Location(
    name="Milieustraat Acht",
    address="Achtseweg Noord 41 5651 GG Eindhoven",
    hours=[
        _MONDAY,
        OpeningHours(day=Weekday.TUESDAY, opens="08:30", closes="17:00", closed=False),
    ],
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


def test_resolve_day_falls_back_to_regular_schedule_without_notices():
    monday = date(2026, 7, 20)

    result = resolve_day(_LOCATION, monday, notices=[])

    assert result.opens == "08:30"
    assert result.closes == "17:00"
    assert result.closed is False
    assert result.reason is None


def test_resolve_day_applies_heat_protocol_within_range():
    monday = date(2026, 7, 20)

    heat_protocol = Notice(
        reason="hitteprotocol",
        title="Hitteprotocol",
        closed=False,
        opens="08:00",
        closes="14:00",
        ends=date(2026, 7, 20),
    )

    result = resolve_day(_LOCATION, monday, notices=[heat_protocol])

    assert result.opens == "08:00"
    assert result.closes == "14:00"
    assert result.reason == "hitteprotocol"


def test_resolve_day_ignores_heat_protocol_outside_range():
    tuesday_after_end = date(2026, 7, 21)

    heat_protocol = Notice(
        reason="hitteprotocol",
        title="Hitteprotocol",
        closed=False,
        opens="08:00",
        closes="14:00",
        ends=date(2026, 7, 20),
    )

    result = resolve_day(_LOCATION, tuesday_after_end, notices=[heat_protocol])

    assert result.reason is None


def test_resolve_day_applies_dated_closure_only_on_listed_dates():
    closure = Notice(
        reason="werkzaamheden",
        title="Let op!",
        closed=True,
        dates=[date(2026, 7, 20)],
    )

    on_date = resolve_day(_LOCATION, date(2026, 7, 20), notices=[closure])
    off_date = resolve_day(_LOCATION, date(2026, 7, 21), notices=[closure])

    assert on_date.closed is True
    assert on_date.reason == "werkzaamheden"
    assert off_date.reason is None


def test_resolve_day_ignores_closure_for_a_different_location():
    closure = Notice(
        reason="verbouwing",
        title="Let op!",
        closed=True,
        location_hint="Milieustraat Lodewijkstraat",
    )

    result = resolve_day(_LOCATION, date(2026, 7, 20), notices=[closure])

    assert result.reason is None
    assert result.closed is False


def test_resolve_day_prefers_closure_over_hours_adjustment():
    monday = date(2026, 7, 20)

    heat_protocol = Notice(
        reason="hitteprotocol",
        title="Hitteprotocol",
        closed=False,
        opens="08:00",
        closes="14:00",
        ends=monday,
    )
    closure = Notice(
        reason="verbouwing",
        title="Let op!",
        closed=True,
        dates=[monday],
    )

    result = resolve_day(_LOCATION, monday, notices=[heat_protocol, closure])

    assert result.closed is True
    assert result.reason == "verbouwing"


def test_resolve_upcoming_returns_resolved_days():
    monday = date(2026, 7, 20)

    result = resolve_upcoming(_LOCATION, monday, notices=[], days=3)

    assert [day.date for day in result] == [
        date(2026, 7, 20),
        date(2026, 7, 21),
        date(2026, 7, 22),
    ]


def test_next_open_close_when_currently_open():
    now = datetime(2026, 7, 20, 10, 0)  # Monday, within opening hours

    upcoming = resolve_upcoming(_MON_TUE_LOCATION, now.date(), notices=[], days=2)

    next_open, next_close = next_open_close(upcoming, now)

    assert next_close == datetime(2026, 7, 20, 17, 0)
    assert next_open == datetime(2026, 7, 21, 8, 30)


def test_next_open_close_when_currently_closed():
    now = datetime(2026, 7, 20, 18, 0)  # Monday, after closing time

    upcoming = resolve_upcoming(_MON_TUE_LOCATION, now.date(), notices=[], days=2)

    next_open, next_close = next_open_close(upcoming, now)

    assert next_open == datetime(2026, 7, 21, 8, 30)
    assert next_close == datetime(2026, 7, 21, 17, 0)


def test_next_open_close_returns_none_outside_window():
    now = datetime(2026, 7, 22, 10, 0)  # Wednesday, no hours defined at all

    upcoming = resolve_upcoming(_LOCATION, now.date(), notices=[], days=1)

    next_open, next_close = next_open_close(upcoming, now)

    assert next_open is None
    assert next_close is None
