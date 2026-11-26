"""Tests for parsing/regular_hours.py: the weekly schedule and later sets.

Most of these were written after a mutation test run (mutmut) showed which
parts of the opening hours section no test actually pinned down.
"""

from datetime import date

from bs4 import BeautifulSoup

from custom_components.cure_afvalbeheer.parsing.regular_hours import (
    read_regular_hours,
)
from custom_components.cure_afvalbeheer.weekday import Weekday

_TODAY = date(2026, 11, 25)


def _read(html: str, today: date = _TODAY):
    """Read the regular hours of a snippet of page."""

    return read_regular_hours(BeautifulSoup(html, "html.parser"), today)


def _monday(hours) -> tuple[str | None, str | None]:
    """Return Monday's hours from a list of OpeningHours."""

    for entry in hours:
        if entry.day is Weekday.MONDAY:
            return entry.opens, entry.closes

    return None, None


def test_no_opening_hours_section_at_all():
    result = _read("<h2>Adres</h2><p>Straat 1</p>")

    assert (result.current, result.scheduled, result.warnings) == ([], [], [])


def test_a_heading_without_lines():
    result = _read("<h2>Openingstijden</h2><h2>Adres</h2>")

    assert result.current == []
    assert result.warnings == []


def test_a_single_block_logs_no_season_warning(caplog):
    _read("<h2>Openingstijden</h2><p>Maandag: 08:30 tot 17:00</p>")

    assert "opening hours blocks" not in caplog.text


def test_two_season_blocks_that_cannot_be_told_apart_are_logged(caplog):
    result = _read(
        "<h2>Openingstijden zomer</h2><p>Maandag: 08:30 tot 17:00</p>"
        "<h2>Openingstijden winter</h2><p>Maandag: 10:00 tot 16:00</p>"
    )

    assert _monday(result.current) == ("08:30", "17:00")
    assert "Found 2 opening hours blocks" in caplog.text
    assert "Openingstijden winter" in caplog.text


def test_a_dated_heading_without_a_year_starts_a_later_set():
    result = _read(
        "<h2>Openingstijden</h2><p>Maandag: 08:30 tot 17:00</p>"
        "<h2>Openingstijden vanaf 1 december</h2><p>Maandag: 10:00 tot 17:00</p>"
    )

    assert _monday(result.current) == ("08:30", "17:00")
    assert [later.starts for later in result.scheduled] == [date(2026, 12, 1)]
    assert _monday(result.scheduled[0].hours) == ("10:00", "17:00")


def test_the_undated_block_is_current_whatever_its_place_on_the_page():
    result = _read(
        "<h2>Openingstijden per 1 december 2026</h2><p>Maandag: 10:00 tot 17:00</p>"
        "<h2>Openingstijden tot en met 30 november 2026</h2>"
        "<p>Maandag: 08:30 tot 17:00</p>"
    )

    assert _monday(result.current) == ("08:30", "17:00")
    assert [later.starts for later in result.scheduled] == [date(2026, 12, 1)]


def test_a_dated_line_without_a_year_starts_a_later_set():
    result = _read(
        "<h2>Openingstijden</h2><p>Maandag: 08:30 tot 17:00</p>"
        "<p>Vanaf 1 december:</p><p>Maandag: 10:00 tot 17:00</p>"
    )

    assert [later.starts for later in result.scheduled] == [date(2026, 12, 1)]


def test_a_heading_date_puts_its_own_lines_in_date_order():
    """The heading's set starts later than a set announced below it."""

    result = _read(
        "<h2>Openingstijden vanaf 1 december 2026</h2>"
        "<p>Maandag: 10:00 tot 17:00</p>"
        "<p>Vanaf 1 november 2026:</p><p>Maandag: 08:30 tot 17:00</p>"
    )

    assert _monday(result.current) == ("08:30", "17:00")
    assert [later.starts for later in result.scheduled] == [date(2026, 12, 1)]


def test_later_sets_come_out_in_date_order():
    result = _read(
        "<h2>Openingstijden</h2><p>Maandag: 08:30 tot 17:00</p>"
        "<p>Vanaf 1 januari 2027:</p><p>Maandag: 11:00 tot 17:00</p>"
        "<p>Vanaf 1 december 2026:</p><p>Maandag: 10:00 tot 17:00</p>"
    )

    assert [later.starts for later in result.scheduled] == [
        date(2026, 12, 1),
        date(2027, 1, 1),
    ]


def test_an_empty_dated_set_is_reported_and_the_next_one_still_read():
    result = _read(
        "<h2>Openingstijden</h2><p>Maandag: 08:30 tot 17:00</p>"
        "<p>Vanaf 1 december 2026: nieuwe tijden volgen</p>"
        "<p>Vanaf 1 januari 2027:</p><p>Maandag: 11:00 tot 17:00</p>"
    )

    assert "Geen openingstijden gevonden bij ingangsdatum 01-12-2026" in (
        result.warnings
    )
    assert [later.starts for later in result.scheduled] == [date(2027, 1, 1)]


def test_a_set_starting_today_is_current():
    result = _read(
        "<h2>Openingstijden</h2><p>Maandag: 08:30 tot 17:00</p>"
        "<p>Vanaf 1 december 2026:</p><p>Maandag: 10:00 tot 17:00</p>",
        today=date(2026, 12, 1),
    )

    assert _monday(result.current) == ("10:00", "17:00")
    assert result.scheduled == []


def test_hours_ending_today_are_still_valid():
    result = _read(
        "<h2>Openingstijden tot en met 25 november 2026</h2>"
        "<p>Maandag: 08:30 tot 17:00</p>"
    )

    assert result.warnings == []


def test_expired_hours_are_reported_in_so_many_words():
    result = _read(
        "<h2>Openingstijden tot en met 24 november 2026</h2>"
        "<p>Maandag: 08:30 tot 17:00</p>"
    )

    assert result.warnings == [
        "Openingstijden waren volgens de website geldig tot en met 24-11-2026; "
        "voor vandaag zijn geen geldige openingstijden gevonden"
    ]


def test_a_dated_line_can_end_its_set_too():
    result = _read(
        "<h2>Openingstijden</h2><p>Maandag: 08:30 tot 17:00</p>"
        "<p>Vanaf 1 oktober 2026 t/m 31 oktober 2026:</p>"
        "<p>Maandag: 10:00 tot 17:00</p>"
    )

    assert any("geldig tot en met 31-10-2026" in w for w in result.warnings)


_HOURS = "<h2>Openingstijden</h2><p>Maandag: 08:30 tot 17:00</p><p>Zondag: Gesloten</p>"


def test_announcement_mismatches_name_both_sides():
    result = _read(
        _HOURS + "<h2>Vanaf 20 november openingstijden: zondag 10:00 - 12:00, "
        "dinsdag gesloten</h2>"
    )

    assert result.warnings == [
        "Aankondiging vanaf 20-11-2026 noemt zondag 10:00-12:00, maar de "
        "openingstijden zeggen gesloten",
        "Aankondiging vanaf 20-11-2026 noemt dinsdag gesloten, maar de "
        "openingstijden zeggen niets",
    ]


def test_an_announcement_exactly_31_days_old_is_still_checked():
    result = _read(
        _HOURS + "<h2>Vanaf 25 oktober 2026 openingstijden: maandag 10:00 - 12:00</h2>"
    )

    assert len(result.warnings) == 1


def test_an_old_announcement_does_not_stop_the_check():
    result = _read(
        _HOURS
        + "<h2>Vanaf 1 januari 2026 openingstijden: maandag 09:00 - 12:00</h2>"
        + "<h2>Vanaf 20 november 2026 geopend: maandag 10:00 - 12:00</h2>"
    )

    assert len(result.warnings) == 1
    assert "20-11-2026" in result.warnings[0]


def test_an_unreadable_announcement_is_reported_and_the_next_checked():
    result = _read(
        _HOURS
        + "<h2>Vanaf 20 november 2026 andere openingstijden</h2><p>Zie elders</p>"
        + "<h2>Vanaf 21 november 2026 geopend: maandag 10:00 - 12:00</h2>"
    )

    assert result.warnings[0] == (
        "Aankondiging niet leesbaar: Vanaf 20 november 2026 andere openingstijden"
    )
    assert len(result.warnings) == 2


def test_the_first_heading_dates_the_first_set():
    result = _read(
        "<h2>Openingstijden tot en met 24 november 2026</h2>"
        "<p>Maandag: 08:30 tot 17:00</p>"
        "<h2>Openingstijden vanaf 1 december 2026</h2><p>Maandag: 10:00 tot 17:00</p>"
    )

    assert any("geldig tot en met 24-11-2026" in w for w in result.warnings)


def test_a_single_dated_heading_without_a_year():
    result = _read(
        "<h2>Openingstijden vanaf 1 december</h2><p>Maandag: 10:00 tot 17:00</p>"
    )

    assert _monday(result.current) == ("10:00", "17:00")


def test_a_dated_line_with_an_end_date_without_a_year():
    result = _read(
        "<h2>Openingstijden</h2><p>Maandag: 08:30 tot 17:00</p>"
        "<p>Vanaf 20 november t/m 30 november:</p><p>Maandag: 10:00 tot 17:00</p>"
    )

    assert _monday(result.current) == ("10:00", "17:00")
    assert result.warnings == []


def test_warnings_are_logged(caplog):
    _read(
        "<h2>Openingstijden</h2><p>Maandag: 08:30 tot 17:00</p>"
        "<p>Vanaf 1 december 2026: nieuwe tijden volgen</p>"
    )

    assert (
        "Opening hours: Geen openingstijden gevonden bij ingangsdatum 01-12-2026"
        in caplog.text
    )
