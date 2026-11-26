"""Tests for parsing/closing_days.py: The list of closing days."""

from datetime import date

import pytest

from custom_components.cure_afvalbeheer.parsing.closing_days import (
    _closing_day_date,
    _closing_day_dates,
    _expand_days,
    _span,
    parse_closing_days,
)

# Real text captured live from cure-afvalbeheer.nl on 2026-08-05.
_CLOSING_DAYS_HEADING = "Sluitingsdagen 2026"
_CLOSING_DAYS_LINES = [
    "De milieustraat is gesloten op onderstaande data:",
    "Maandag 6 april 2026 (Pasen)",
    "Maandag 27 april 2026 (Koningsdag)",
    "Donderdag 14 mei 2026 (Hemelvaartsdag)",
    "Maandag 25 mei 2026 (Tweede Pinksterdag)",
    "Vrijdag 25 en zaterdag 26 december 2026 (Kerstmis)",
    "Vrijdag 1 januari 2027 (nieuwjaarsdag)",
    "Afwijkende openingstijden: op donderdag 24 december (Kerstavond) en "
    "donderdag 31 december (Oudejaarsavond) is de milieustraat geopend tot "
    "16:00 uur.",
    "Ben op tijd. Heb je te veel afval bij waardoor je de openingstijd "
    "overschrijdt, kan toegang worden geweigerd. De poortmedewerker oordeelt "
    "hierover.",
    "Zorg ervoor dat je de Cure milieupas bij hebt. Zonder Cure milieupas is "
    "toegang tot de milieustraat niet mogelijk.",
]

# The same block as Cure worded it before the 2025 website rebuild: the
# holiday name comes first, the weekday is missing and so is the year.
_OLD_CLOSING_DAYS_HEADING = "Sluitingsdagen 2024"
_OLD_CLOSING_DAYS_LINES = [
    "De milieustraat is gesloten op onderstaande data:",
    "2e Paasdag, 1 april",
    "Koningsdag, 27 april",
    "1e Kerstdag, 25 december",
    "1 januari 2025",
    "Op Kerstavond, dinsdag 24 december, én Oudjaarsavond, dinsdag 31 "
    "december, sluiten de milieustraten om 16 uur.",
]


def test_parse_closing_days_reads_every_listed_day():
    notices = parse_closing_days(
        _CLOSING_DAYS_HEADING, _CLOSING_DAYS_LINES, date(2026, 8, 5)
    )

    closures = [notice for notice in notices if notice.closed]

    assert [notice.dates for notice in closures] == [
        [date(2026, 4, 6)],
        [date(2026, 4, 27)],
        [date(2026, 5, 14)],
        [date(2026, 5, 25)],
        [date(2026, 12, 25), date(2026, 12, 26)],  # "25 en zaterdag 26 december"
        [date(2027, 1, 1)],
    ]

    assert {notice.reason for notice in closures} == {"sluitingsdag"}


def test_parse_closing_days_reads_the_adjusted_closing_time():
    notices = parse_closing_days(
        _CLOSING_DAYS_HEADING, _CLOSING_DAYS_LINES, date(2026, 8, 5)
    )

    adjusted = [notice for notice in notices if not notice.closed]

    assert len(adjusted) == 1
    assert adjusted[0].reason == "aangepaste openingstijden"
    assert adjusted[0].closes == "16:00"
    assert adjusted[0].opens is None  # keeps the regular opening time
    # The year is missing from the sentence and taken from the heading.
    assert adjusted[0].dates == [date(2026, 12, 24), date(2026, 12, 31)]


def test_parse_closing_days_ignores_lines_without_a_date():
    notices = parse_closing_days(
        _CLOSING_DAYS_HEADING, _CLOSING_DAYS_LINES, date(2026, 8, 5)
    )

    assert len(notices) == 7  # six closing days plus one adjusted closing time


def test_parse_closing_days_handles_the_pre_2025_wording():
    """Weekday-less entries, the holiday name first and no year at all."""

    notices = parse_closing_days(
        _OLD_CLOSING_DAYS_HEADING, _OLD_CLOSING_DAYS_LINES, date(2025, 6, 1)
    )

    assert [notice.dates for notice in notices] == [
        [date(2024, 4, 1)],
        [date(2024, 4, 27)],
        [date(2024, 12, 25)],
        [date(2025, 1, 1)],  # the only entry that spells out its own year
        [date(2024, 12, 24), date(2024, 12, 31)],
    ]

    assert notices[-1].closes == "16:00"


def test_parse_closing_days_expands_a_range():
    notices = parse_closing_days(
        "Sluitingsdagen 2026",
        ["Van 23 t/m 27 december 2026 gesloten"],
        date(2026, 8, 5),
    )

    assert notices[0].dates == [
        date(2026, 12, 23),
        date(2026, 12, 24),
        date(2026, 12, 25),
        date(2026, 12, 26),
        date(2026, 12, 27),
    ]


def test_parse_closing_days_reads_a_line_adjusting_both_sides():
    notices = parse_closing_days(
        "Sluitingsdagen 2026",
        ["Op donderdag 24 december geopend van 10:00 tot 16:00 uur"],
        date(2026, 8, 5),
    )

    assert notices[0].closed is False
    assert notices[0].opens == "10:00"
    assert notices[0].closes == "16:00"
    assert notices[0].dates == [date(2026, 12, 24)]


def test_parse_closing_days_reads_a_line_adjusting_the_opening_only():
    notices = parse_closing_days(
        "Sluitingsdagen 2026",
        ["Op donderdag 24 december zijn we pas vanaf 10:00 uur open"],
        date(2026, 8, 5),
    )

    assert notices[0].closed is False
    assert notices[0].opens == "10:00"
    assert notices[0].closes is None  # the regular closing time stands


def test_parse_closing_days_skips_an_open_day_whose_times_are_unreadable():
    """Calling such a day closed would state the opposite of the line."""

    notices = parse_closing_days(
        "Sluitingsdagen 2026",
        ["Op donderdag 24 december gaan we later open"],
        date(2026, 8, 5),
    )

    assert notices == []


def test_parse_closing_days_still_closes_a_day_that_says_it_is_closed():
    """An open-sounding word must not rescue a line that says "gesloten"."""

    notices = parse_closing_days(
        "Sluitingsdagen 2026",
        ["Vrijdag 25 december 2026 gesloten, milieustraat Acht is wel open"],
        date(2026, 8, 5),
    )

    assert notices[0].closed is True
    assert notices[0].dates == [date(2026, 12, 25)]


def test_parse_closing_days_expands_a_range_across_a_month_boundary():
    """Only the two ends are written out; the days between are implied."""

    notices = parse_closing_days(
        "Sluitingsdagen 2026",
        ["Gesloten van 30 december 2026 tot en met 2 januari 2027"],
        date(2026, 8, 5),
    )

    assert notices[0].dates == [
        date(2026, 12, 30),
        date(2026, 12, 31),
        date(2027, 1, 1),
        date(2027, 1, 2),
    ]


def test_parse_closing_days_reads_a_range_crossing_new_year_without_a_year():
    """The end of such a range is a year on from the heading's year."""

    notices = parse_closing_days(
        "Sluitingsdagen 2026",
        ["Gesloten van 30 december tot en met 2 januari"],
        date(2026, 8, 5),
    )

    assert notices[0].dates == [
        date(2026, 12, 30),
        date(2026, 12, 31),
        date(2027, 1, 1),
        date(2027, 1, 2),
    ]


def test_parse_closing_days_keeps_only_the_ends_of_an_implausible_range():
    """A closing days list is days off, never a closure of months."""

    notices = parse_closing_days(
        "Sluitingsdagen 2026",
        ["Gesloten van 1 januari tot en met 31 december 2026"],
        date(2026, 8, 5),
    )

    assert notices[0].dates == [date(2026, 1, 1), date(2026, 12, 31)]


def test_parse_closing_days_does_not_read_a_hyphenated_name_as_a_range():
    """Municipality names such as Geldrop-Mierlo carry a hyphen of their own."""

    notices = parse_closing_days(
        "Sluitingsdagen 2026",
        ["1 mei Geldrop-Mierlo en 2 juni 2026"],
        date(2026, 8, 5),
    )

    assert notices[0].dates == [date(2026, 5, 1), date(2026, 6, 2)]


def test_parse_closing_days_infers_the_year_without_one_anywhere():
    """No year in the entry and none in the heading: read it as upcoming."""

    notices = parse_closing_days("Sluitingsdagen", ["25 december"], date(2026, 8, 5))

    assert notices[0].dates == [date(2026, 12, 25)]


def test_parse_closing_days_rolls_a_bare_date_over_into_next_year():
    notices = parse_closing_days("Sluitingsdagen", ["1 januari"], date(2026, 8, 5))

    assert notices[0].dates == [date(2027, 1, 1)]


def test_parse_closing_days_returns_nothing_for_an_unparsable_block():
    assert (
        parse_closing_days("Sluitingsdagen 2026", ["Zie de kalender"], date.today())
        == []
    )


def test_parse_closing_days_skips_an_impossible_date():
    assert (
        parse_closing_days("Sluitingsdagen 2026", ["30 februari 2026"], date.today())
        == []
    )


# --- Spellings Cure has not used yet, but readily could ---


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("Maandag 6 april 2026 (Pasen)", date(2026, 4, 6)),
        ("6 apr 2026", date(2026, 4, 6)),
        ("Maandag 6 apr. 2026", date(2026, 4, 6)),
        ("06-04-2026", date(2026, 4, 6)),
        ("6-4-2026 (Pasen)", date(2026, 4, 6)),
        ("06/04/2026", date(2026, 4, 6)),
    ],
)
def test_parse_closing_days_reads_a_date_however_it_is_written(line, expected):
    notices = parse_closing_days("Sluitingsdagen 2026", [line], date(2026, 1, 1))

    assert notices[0].dates == [expected]
    assert notices[0].closed is True


def test_parse_closing_days_does_not_read_a_number_pair_as_a_date():
    """A numeric date needs its year in full, or a house number would do."""

    assert parse_closing_days("Sluitingsdagen 2026", ["6-4-26"], date(2026, 1, 1)) == []


# --- Grenzen, gevonden met mutatietests (mutmut) ---------------------------


def test_expand_days_reads_a_list_as_separate_days():
    assert _expand_days("25 en 27") == [25, 27]


def test_closing_day_date_keeps_a_date_exactly_30_days_ago():
    assert _closing_day_date(1, 7, None, date(2026, 7, 31), None) == date(2026, 7, 1)


def test_closing_day_date_rolls_over_a_date_31_days_ago():
    assert _closing_day_date(1, 7, None, date(2026, 8, 1), None) == date(2027, 7, 1)


def test_span_leaves_a_later_end_in_its_own_year():
    assert _span(date(2026, 12, 24), [date(2026, 12, 26)], False) == [
        date(2026, 12, 25),
        date(2026, 12, 26),
    ]


def test_span_of_one_day():
    assert _span(date(2026, 12, 24), [date(2026, 12, 24)], False) == [
        date(2026, 12, 24)
    ]


def test_span_fills_in_a_range_of_exactly_the_maximum_length():
    result = _span(date(2026, 12, 1), [date(2027, 1, 1)], True)

    assert len(result) == 31
    assert result[0] == date(2026, 12, 2)
    assert result[-1] == date(2027, 1, 1)


def test_span_does_not_repeat_its_start():
    assert _span(date(2026, 12, 30), [date(2027, 1, 2)], True) == [
        date(2026, 12, 31),
        date(2027, 1, 1),
        date(2027, 1, 2),
    ]


def test_closing_day_dates_skips_an_impossible_numeric_date():
    assert _closing_day_dates("31-02-2026 en 01-03-2026", date(2026, 1, 1), None) == [
        date(2026, 3, 1)
    ]


def test_closing_day_dates_trusts_a_written_year_over_new_year():
    """With both years written out, a backwards range is not reread."""

    result = _closing_day_dates(
        "30 december 2026 t/m 2 januari 2026", date(2026, 12, 1), None
    )

    assert result == [date(2026, 12, 30), date(2026, 1, 2)]


def test_closing_days_notices_carry_their_line_as_title():
    lines = ["Vrijdag 25 december gesloten", "Zaterdag 26 december: 10:00 tot 14:00"]

    notices = parse_closing_days("Sluitingsdagen 2026", lines, date(2026, 12, 1))

    assert [notice.title for notice in notices] == lines


def test_closing_days_reads_a_bare_time_range_as_adjusted_hours():
    """Mutatietests vonden dit: zo'n regel werd als hele dag dicht gelezen."""

    notices = parse_closing_days(
        "Sluitingsdagen 2026",
        ["Zaterdag 26 december: 10:00 tot 14:00"],
        date(2026, 12, 1),
    )

    assert len(notices) == 1
    assert notices[0].closed is False
    assert (notices[0].opens, notices[0].closes) == ("10:00", "14:00")
    assert notices[0].reason == "aangepaste openingstijden"
