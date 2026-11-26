"""A closure whose notice no longer opens with "Let op".

In November 2026 Cure rewrote the heading of the Lodewijkstraat renovation
notice into an announcement of the new hours ("Vanaf 01 december 2026
openingstijden Eindhovense milieustraten: ..."), and added to its body that
the Lodewijkstraat is "weer toegankelijk voor publiek" from 1 December. The
"Datum sluiting" label stayed. The parser lost the closure without a word,
so the Lodewijkstraat showed as open while the website said it was shut.
"""

from datetime import date

import pytest

from custom_components.cure_afvalbeheer.parsing.attention import (
    parse_closure_notice,
)
from custom_components.cure_afvalbeheer.parsing.page import CureParser
from custom_components.cure_afvalbeheer.schedule import resolve_day
from tests.hulp import read_fixture

_TODAY = date(2026, 11, 26)

_HEADING = (
    "Vanaf 01 december 2026 openingstijden Eindhovense milieustraten: "
    "Ma t/m vr 10:00-17:00, za 09:00-17:00, zo gesloten."
)

_BODY = (
    "De verbouwing van de milieustraat Lodewijkstraat zit er bijna op. "
    "Vanaf 01 december 2026 is de Lodewijkstraat weer toegankelijk voor "
    "publiek. Kom naar onze milieustraat in Acht. Achtseweg Noord 41, 5651 GG "
    "Eindhoven Datum sluiting: 30-11-2025"
)


def _day(data, name, day):
    """Return how one location's day resolves after all notices."""

    location = next(loc for loc in data.locations if loc.name == name)

    return resolve_day(location, day, data.notices)


@pytest.fixture
def page():
    return CureParser(read_fixture("milieustraat_eindhoven_heropening.html"))


def test_the_lodewijkstraat_stays_closed_until_it_reopens(page):
    data = page.parse(_TODAY)

    assert data.warnings == []

    # Shut through Monday 30 November, the last day before it reopens.
    for day in (date(2026, 11, 27), date(2026, 11, 28), date(2026, 11, 30)):
        assert _day(data, "Milieustraat Lodewijkstraat", day).closed is True

    reopened = _day(data, "Milieustraat Lodewijkstraat", date(2026, 12, 1))
    assert (reopened.closed, reopened.opens, reopened.closes) == (
        False,
        "10:00",
        "17:00",
    )


def test_acht_stays_open_meanwhile(page):
    data = page.parse(_TODAY)

    friday = _day(data, "Milieustraat Acht", date(2026, 11, 27))

    assert (friday.closed, friday.opens, friday.closes) == (False, "08:30", "17:00")


def test_the_closure_is_gone_once_it_has_reopened(page):
    data = page.parse(date(2026, 12, 2))

    assert data.warnings == []
    assert _day(data, "Milieustraat Lodewijkstraat", date(2026, 12, 2)).closed is (
        False
    )


def test_the_reopening_date_ends_the_closure():
    notice = parse_closure_notice(_HEADING, _BODY, _TODAY)

    assert notice is not None
    assert notice.closed is True
    assert notice.reason == "verbouwing"
    assert notice.ends == date(2026, 11, 30)
    # The heading is about new hours; the title says what is going on.
    assert notice.title == (
        "Vanaf 01 december 2026 is de Lodewijkstraat weer toegankelijk voor publiek."
    )


@pytest.mark.parametrize(
    "sentence",
    [
        "Vanaf 1 december 2026 is de Lodewijkstraat weer open.",
        "Per 01-12-2026 is de Lodewijkstraat weer geopend.",
        "De Lodewijkstraat is vanaf dinsdag 1 december weer toegankelijk.",
    ],
)
def test_other_wordings_of_the_reopening(sentence):
    body = f"Kom naar onze milieustraat in Acht. {sentence} Datum sluiting: 30-11-2025"

    notice = parse_closure_notice(_HEADING, body, _TODAY)

    assert notice is not None
    assert notice.ends == date(2026, 11, 30)


def test_an_unreadable_reopening_date_is_not_read_as_closed_for_good():
    body = "De Lodewijkstraat gaat binnenkort weer open. Datum sluiting: 30-11-2025"

    assert parse_closure_notice(_HEADING, body, _TODAY) is None


def test_a_block_without_let_op_or_a_closure_label_is_no_closure():
    assert parse_closure_notice(_HEADING, "Kom gerust langs.", _TODAY) is None
