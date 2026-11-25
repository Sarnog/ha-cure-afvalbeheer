"""Tests for parsing/attention.py: The "Let op" announcements."""

from datetime import date

import pytest

from custom_components.cure_afvalbeheer.parsing.attention import parse_closure_notice
from tests.hulp import (
    EINDHOVEN_CLOSURE_BODY,
    NO_NOTICE_HEADING,
    VALKENSWAARD_CLOSURE_BODY,
)

_EINDHOVEN_CLOSURE_HEADING = "Let op! Lodewijkstraat wordt verbouwd"

_VALKENSWAARD_CLOSURE_HEADING = (
    "Let op! Milieustraat Valkenswaard dicht i.v.m. werkzaamheden."
)


def test_parse_closure_notice_eindhoven_explicit_date_in_past():
    notice = parse_closure_notice(
        _EINDHOVEN_CLOSURE_HEADING, EINDHOVEN_CLOSURE_BODY, date(2026, 7, 17)
    )

    assert notice is not None
    assert notice.reason == "verbouwing"
    assert notice.closed is True
    assert notice.starts is None  # already started, no lower bound needed
    assert notice.ends is None  # indefinite, no announced reopening
    assert notice.dates is None


def test_parse_closure_notice_explicit_date_in_future():
    notice = parse_closure_notice(
        "Let op! Milieustraat wordt verbouwd",
        "Datum sluiting: 01-01-2027",
        date(2026, 7, 17),
    )

    assert notice is not None
    assert notice.starts == date(2027, 1, 1)


def test_parse_closure_notice_valkenswaard_dated_list():
    notice = parse_closure_notice(
        _VALKENSWAARD_CLOSURE_HEADING, VALKENSWAARD_CLOSURE_BODY, date(2026, 7, 17)
    )

    assert notice is not None
    assert notice.reason == "werkzaamheden"
    assert notice.closed is True
    assert notice.dates == [
        date(2026, 6, 30),
        date(2026, 7, 1),
        date(2026, 7, 2),
    ]


def test_parse_closure_notice_ignores_unrelated_heading():
    assert (
        parse_closure_notice(NO_NOTICE_HEADING, "wat tekst", date(2026, 7, 17)) is None
    )


def test_parse_closure_notice_returns_none_without_parsable_date():
    notice = parse_closure_notice(
        "Let op! Iets is anders", "Geen datum hier te vinden.", date(2026, 7, 17)
    )

    assert notice is None


def test_parse_closure_notice_reads_a_period():
    notice = parse_closure_notice(
        "Let op! Milieustraat dicht i.v.m. werkzaamheden.",
        "De milieustraat is gesloten van 30 juni tot en met 2 juli.",
        date(2026, 6, 1),
    )

    assert notice is not None
    assert notice.closed is True
    assert notice.starts == date(2026, 6, 30)
    assert notice.ends == date(2026, 7, 2)


@pytest.mark.parametrize(
    "heading",
    [
        "Let op! Milieustraat dicht i.v.m. werkzaamheden.",
        "Let op: Milieustraat dicht i.v.m. werkzaamheden.",
        "LET OP! Milieustraat dicht i.v.m. werkzaamheden.",
        "Let op, milieustraat dicht i.v.m. werkzaamheden.",
        "Letop! Milieustraat dicht i.v.m. werkzaamheden.",
    ],
)
def test_parse_closure_notice_however_the_heading_is_punctuated(heading):
    notice = parse_closure_notice(heading, "Dinsdag 30 juni 2026", date(2026, 6, 1))

    assert notice is not None
    assert notice.dates == [date(2026, 6, 30)]


def test_parse_closure_notice_ignores_a_heading_without_the_wording():
    assert (
        parse_closure_notice(
            "Inpaktips voor vertrek", "Dinsdag 30 juni 2026", date(2026, 6, 1)
        )
        is None
    )


# --- A "Let op" notice that adjusts hours instead of cancelling the day ---


_FROST_HEADING = "Let op! Vorst op de milieustraat"
_FROST_BODY = (
    "Vanwege vorst en gladheid zijn de milieustraten op dinsdag 12 januari "
    "2027 pas geopend van 10:00 tot 15:00 uur."
)


def test_parse_closure_notice_reads_adjusted_hours_instead_of_a_closure():
    """Frost can shorten a day rather than cancel it."""

    notice = parse_closure_notice(_FROST_HEADING, _FROST_BODY, date(2027, 1, 10))

    assert notice is not None
    assert notice.closed is False
    assert notice.opens == "10:00"
    assert notice.closes == "15:00"
    assert notice.reason == "weersomstandigheden"
    assert notice.dates == [date(2027, 1, 12)]


def test_parse_closure_notice_reads_an_early_closing_time():
    notice = parse_closure_notice(
        "Let op! Storm",
        "Vanwege de storm sluiten wij op woensdag 13 januari 2027 om 15:00 uur.",
        date(2027, 1, 10),
    )

    assert notice is not None
    assert notice.closed is False
    assert notice.closes == "15:00"
    assert notice.opens is None


def test_parse_closure_notice_takes_gesloten_at_its_word():
    """ "Gesloten" describes the state; "sluiten om 15:00" a closing time."""

    notice = parse_closure_notice(
        "Let op! Gladheid",
        "Op dinsdag 12 januari 2027 zijn de milieustraten gesloten. Normaal "
        "zijn wij geopend van 08:30 tot 17:00 uur.",
        date(2027, 1, 10),
    )

    assert notice is not None
    assert notice.closed is True
    assert notice.opens is None
    assert notice.closes is None


def test_parse_closure_notice_keeps_a_permanent_closure_a_closure():
    """A "Datum sluiting" body names the alternative location's hours."""

    notice = parse_closure_notice(
        "Let op! Lodewijkstraat wordt verbouwd",
        "Kom naar onze milieustraat in Acht, geopend van 08:30 tot 17:00 uur. "
        "Datum sluiting: 30-11-2027",
        date(2027, 1, 10),
    )

    assert notice is not None
    assert notice.closed is True
    assert notice.opens is None
    assert notice.reason == "verbouwing"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Let op! Lodewijkstraat wordt verbouwd", "verbouwing"),
        ("Let op! Vorst en gladheid", "weersomstandigheden"),
        ("Let op! Door de storm", "weersomstandigheden"),
        ("Let op! Stroomstoring", "storing"),
        ("Let op! Werkzaamheden aan de weg", "werkzaamheden"),
        ("Let op! Onderhoud aan de weegbrug", "werkzaamheden"),
        ("Let op! Er wordt gestaakt", "sluiting"),
    ],
)
def test_parse_closure_notice_names_the_cause_it_can_read(text, expected):
    notice = parse_closure_notice(
        text, "Op dinsdag 12 januari 2027 gesloten.", date(2027, 1, 10)
    )

    assert notice is not None
    assert notice.reason == expected


def test_parse_closure_notice_falls_back_to_a_plain_reason():
    """An unknown cause still gets a reason that is true."""

    notice = parse_closure_notice(
        "Let op! Iets onverwachts",
        "Op dinsdag 12 januari 2027 zijn wij geopend van 10:00 tot 12:00 uur.",
        date(2027, 1, 10),
    )

    assert notice is not None
    assert notice.reason == "aangepaste openingstijden"
