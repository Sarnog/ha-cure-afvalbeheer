"""Announced changes of the regular opening hours.

Cure announced new hours for Eindhoven from 1 December 2026 inside the
"Openingstijden" block, under a "Vanaf dinsdag 1 december 2026:" line. The
integration used to drop those lines without a word and kept showing the
old hours past that date. These tests pin down that announced hours are
read with their start date, and that anything in the hours section that
cannot be read ends up as a warning rather than being ignored.
"""

from datetime import date
from pathlib import Path

import pytest

from custom_components.cure_afvalbeheer.parsing.hours_lines import (
    is_opening_hours_line,
    parse_opening_hours_line,
)
from custom_components.cure_afvalbeheer.parsing.page import CureParser
from custom_components.cure_afvalbeheer.schedule import resolve_day, resolve_upcoming
from custom_components.cure_afvalbeheer.weekday import Weekday

_FIXTURE = Path("tests/fixtures/milieustraat_eindhoven_nieuwe_tijden.html")

_BEFORE = date(2026, 11, 25)  # woensdag, oude tijden
_AFTER = date(2026, 12, 3)  # donderdag, nieuwe tijden


def _page(hours_html: str, extra_html: str = "") -> str:
    """Return a minimal page with one address and the given hours block."""

    return (
        "<html><body><main>"
        f"{extra_html}"
        "<div><h2>Adres Milieustraten Eindhoven</h2>"
        "<h3>Milieustraat Acht</h3><p>Achtseweg Noord 41</p></div>"
        f"<div>{hours_html}<h2>Sluitingsdagen 2026</h2></div>"
        "</main></body></html>"
    )


_OLD_HOURS = (
    "<p>Maandag: 08:30 tot 17:00</p><p>Dinsdag: 08:30 tot 17:00</p>"
    "<p>Woensdag: 08:30 tot 17:00</p><p>Donderdag: 08:30 tot 17:00</p>"
    "<p>Vrijdag: 08:30 tot 17:00</p><p>Zaterdag: 08:30 tot 17:00</p>"
    "<p>Zon &amp; Feestdagen: Gesloten</p>"
)


def _times(hours) -> dict[Weekday, tuple[str | None, str | None, bool]]:
    """Return hours keyed by day, for easy comparison."""

    return {entry.day: (entry.opens, entry.closes, entry.closed) for entry in hours}


def test_fixture_keeps_current_hours_until_the_start_date():
    data = CureParser(_FIXTURE.read_text(encoding="utf-8")).parse(_BEFORE)

    location = data.locations[0]

    assert _times(location.hours)[Weekday.MONDAY] == ("08:30", "17:00", False)
    assert [scheduled.starts for scheduled in location.scheduled] == [date(2026, 12, 1)]
    assert data.warnings == []


def test_fixture_shows_new_hours_from_the_start_date():
    """The exact situation from the bug report: 1 December must say 10:00."""

    data = CureParser(_FIXTURE.read_text(encoding="utf-8")).parse(_BEFORE)

    location = data.locations[0]

    days = {
        day.date: day
        for day in resolve_upcoming(location, _BEFORE, data.notices, days=12)
    }

    assert (days[date(2026, 11, 30)].opens, days[date(2026, 11, 30)].closes) == (
        "08:30",
        "17:00",
    )
    assert (days[date(2026, 12, 1)].opens, days[date(2026, 12, 1)].closes) == (
        "10:00",
        "17:00",
    )
    assert days[date(2026, 12, 5)].opens == "09:00"
    assert days[date(2026, 12, 6)].closed is True


def test_fixture_after_the_start_date_uses_the_new_hours_as_current():
    data = CureParser(_FIXTURE.read_text(encoding="utf-8")).parse(_AFTER)

    location = data.locations[0]

    assert _times(location.hours)[Weekday.MONDAY] == ("10:00", "17:00", False)
    assert _times(location.hours)[Weekday.SATURDAY] == ("09:00", "17:00", False)
    assert location.scheduled == []
    assert data.warnings == []


def test_new_hours_written_with_line_breaks_in_one_paragraph():
    html = _page(
        "<h2>Openingstijden</h2>"
        + _OLD_HOURS
        + "<p><strong>Vanaf dinsdag 1 december 2026:<br>Ma t/m vr: 10.00 - 17.00 uur"
        "<br>Za: 09.00 - 17.00 uur<br>Zo: gesloten</strong></p>"
    )

    data = CureParser(html).parse(_BEFORE)

    scheduled = data.locations[0].scheduled[0]

    assert scheduled.starts == date(2026, 12, 1)
    assert _times(scheduled.hours)[Weekday.FRIDAY] == ("10:00", "17:00", False)
    assert _times(scheduled.hours)[Weekday.SUNDAY] == (None, None, True)
    assert data.warnings == []


def test_new_hours_under_a_heading_of_their_own():
    html = _page(
        "<h2>Openingstijden</h2>"
        + _OLD_HOURS
        + "<h2>Openingstijden vanaf 1 december 2026</h2>"
        "<p>Maandag t/m vrijdag: 10:00 - 17:00</p>"
        "<p>Zaterdag: 09:00 - 17:00</p><p>Zondag: gesloten</p>"
    )

    data = CureParser(html).parse(_BEFORE)

    location = data.locations[0]

    assert _times(location.hours)[Weekday.MONDAY] == ("08:30", "17:00", False)
    assert location.scheduled[0].starts == date(2026, 12, 1)
    assert _times(location.scheduled[0].hours)[Weekday.MONDAY] == (
        "10:00",
        "17:00",
        False,
    )


def test_start_date_and_hours_on_one_line():
    html = _page(
        "<h2>Openingstijden</h2>"
        + _OLD_HOURS
        + "<p>Per 1 december 2026: zaterdag 09:00 - 15:00</p>"
    )

    data = CureParser(html).parse(_BEFORE)

    scheduled = data.locations[0].scheduled[0]

    assert _times(scheduled.hours)[Weekday.SATURDAY] == ("09:00", "15:00", False)


def test_a_partial_change_keeps_the_other_days():
    """ "Vanaf ...: zaterdag ..." changes Saturday and nothing else."""

    html = _page(
        "<h2>Openingstijden</h2>"
        + _OLD_HOURS
        + "<p>Vanaf 1 december 2026:</p><p>Zaterdag: 09:00 - 15:00</p>"
    )

    location = CureParser(html).parse(_BEFORE).locations[0]

    day = resolve_day(location, date(2026, 12, 2), [])

    assert (day.opens, day.closes) == ("08:30", "17:00")
    assert resolve_day(location, date(2026, 12, 5), []).closes == "15:00"


def test_an_unreadable_hours_line_is_reported():
    html = _page(
        "<h2>Openingstijden</h2>" + _OLD_HOURS + "<p>Weekend: 09:00 - 15:00</p>"
    )

    warnings = CureParser(html).hours_warnings(_BEFORE)

    assert warnings == ["Regel niet leesbaar: Weekend: 09:00 - 15:00"]


def test_an_unreadable_start_date_is_reported():
    html = _page(
        "<h2>Openingstijden</h2>"
        + _OLD_HOURS
        + "<p>Vanaf volgend jaar:</p><p>Zaterdag: 09:00 - 15:00</p>"
    )

    data = CureParser(html).parse(_BEFORE)

    assert "Ingangsdatum niet leesbaar: Vanaf volgend jaar:" in data.warnings


def test_a_start_date_without_hours_is_reported():
    html = _page(
        "<h2>Openingstijden</h2>"
        + _OLD_HOURS
        + "<p>Vanaf 1 december 2026 gelden nieuwe openingstijden.</p>"
    )

    data = CureParser(html).parse(_BEFORE)

    assert data.warnings == ["Geen openingstijden gevonden bij ingangsdatum 01-12-2026"]


def test_hours_the_page_says_have_expired_are_reported():
    html = _page("<h2>Openingstijden tot en met 30 november 2026</h2>" + _OLD_HOURS)

    assert CureParser(html).hours_warnings(_BEFORE) == []

    warnings = CureParser(html).hours_warnings(_AFTER)

    assert len(warnings) == 1
    assert "tot en met 30-11-2026" in warnings[0]


_ANNOUNCEMENT = (
    "<div><h2>Vanaf 01 december 2026 openingstijden Eindhovense milieustraten: "
    "Ma t/m vr 10:00-17:00, za 09:00-17:00, zo gesloten.</h2>"
    "<p><strong>Milieustraat Lodewijkstraat</strong><br>Lodewijkstraat 7<br>"
    "Maandag tot en met vrijdag geopend van 10:00 tot 17:00 uur<br>"
    "Zaterdag geopend van 09:00 tot 17:00 uur<br>Zondag gesloten.</p></div>"
)

_NEW_HOURS = (
    "<p><strong>Vanaf dinsdag 1 december 2026:</strong></p>"
    "<p><strong>Maandag tot en met vrijdag geopend van 10:00 tot 17:00 uur"
    "</strong></p><p><strong>Zaterdag geopend van 09:00 tot 17:00 uur</strong></p>"
    "<p><strong>Zondag gesloten</strong></p>"
)


def test_an_announcement_matching_the_hours_gives_no_warning():
    html = _page("<h2>Openingstijden</h2>" + _OLD_HOURS + _NEW_HOURS, _ANNOUNCEMENT)

    assert CureParser(html).hours_warnings(_BEFORE) == []


def test_an_announcement_missing_from_the_hours_block_is_reported():
    """The announcement alone is not trusted, but it is never ignored."""

    html = _page("<h2>Openingstijden</h2>" + _OLD_HOURS, _ANNOUNCEMENT)

    warnings = CureParser(html).hours_warnings(_BEFORE)

    assert any("noemt maandag 10:00-17:00" in warning for warning in warnings)


def test_an_announcement_contradicting_the_hours_is_reported():
    html = _page(
        "<h2>Openingstijden</h2>" + _OLD_HOURS + _NEW_HOURS,
        _ANNOUNCEMENT.replace("za 09:00-17:00", "za 08:00-17:00"),
    )

    warnings = CureParser(html).hours_warnings(_BEFORE)

    assert warnings == [
        "Aankondiging vanaf 01-12-2026 noemt zaterdag 08:00-17:00, maar de "
        "openingstijden zeggen 09:00-17:00"
    ]


def test_an_old_announcement_is_not_checked_anymore():
    html = _page("<h2>Openingstijden</h2>" + _OLD_HOURS, _ANNOUNCEMENT)

    assert CureParser(html).hours_warnings(date(2027, 3, 1)) == []


@pytest.mark.parametrize(
    ("line", "days", "expected"),
    [
        (
            "Maandag tot en met vrijdag geopend van 10:00 tot 17:00 uur",
            5,
            ("10:00", "17:00", False),
        ),
        ("Zaterdag geopend van 09:00 tot 17:00 uur", 1, ("09:00", "17:00", False)),
        ("Zaterdag zijn we open van 9.00 - 17.00 uur", 1, ("09:00", "17:00", False)),
        ("Zondag gesloten.", 1, (None, None, True)),
        ("Zondag is de milieustraat gesloten", 1, (None, None, True)),
        ("Ma t/m vr 10:00-17:00", 5, ("10:00", "17:00", False)),
        ("ma-vr: 10:00 – 17:00", 5, ("10:00", "17:00", False)),
        (
            "Maandag t/m vrijdag: geopend van 10:00 tot 17:00",
            5,
            ("10:00", "17:00", False),
        ),
    ],
)
def test_other_ways_of_writing_an_hours_line(line, days, expected):
    assert is_opening_hours_line(line)

    hours = parse_opening_hours_line(line)

    assert len(hours) == days
    assert all((h.opens, h.closes, h.closed) == expected for h in hours)


def test_a_start_date_line_is_not_read_as_hours():
    assert not is_opening_hours_line("Vanaf dinsdag 1 december 2026:")


def test_a_dated_heading_before_the_undated_one_keeps_both_sets():
    html = _page(
        "<h2>Openingstijden vanaf 1 december 2026</h2>"
        "<p>Maandag t/m vrijdag: 10:00 - 17:00</p>"
        "<h2>Openingstijden tot en met 30 november 2026</h2>" + _OLD_HOURS
    )

    location = CureParser(html).parse(_BEFORE).locations[0]

    assert _times(location.hours)[Weekday.MONDAY] == ("08:30", "17:00", False)
    assert location.scheduled[0].starts == date(2026, 12, 1)
    assert _times(location.scheduled[0].hours)[Weekday.MONDAY] == (
        "10:00",
        "17:00",
        False,
    )


def test_expired_hours_before_a_later_set_are_reported():
    """A gap between the end of one set and the start of the next."""

    html = _page(
        "<h2>Openingstijden tot en met 30 november 2026</h2>"
        + _OLD_HOURS
        + "<p>Vanaf 7 december 2026:</p><p>Maandag t/m vrijdag: 10:00 - 17:00</p>"
    )

    warnings = CureParser(html).hours_warnings(_AFTER)

    assert len(warnings) == 1
    assert "tot en met 30-11-2026" in warnings[0]
