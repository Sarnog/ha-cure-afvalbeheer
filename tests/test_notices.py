"""Tests for parsing/notices.py: finding the messages on a page.

Written after a mutation test run (mutmut) showed which parts of the
notice reading no test actually pinned down.
"""

from datetime import date

from bs4 import BeautifulSoup

from custom_components.cure_afvalbeheer.models import Location
from custom_components.cure_afvalbeheer.parsing.notices import (
    heat_protocol_notice,
    read_notices,
)

_TODAY = date(2026, 7, 10)

_LOCATIONS = [
    Location(name="Milieustraat Acht", address=None, hours=[]),
    Location(name="Milieustraat Lodewijkstraat", address=None, hours=[]),
]


def _soup(html: str) -> BeautifulSoup:
    """Parse a snippet the way the integration parses a page."""

    return BeautifulSoup(html, "html.parser")


def _news(heading: str) -> str:
    """Return a site-wide news block with the given heading."""

    return f'<div data-block="newsBlock"><h2>{heading}</h2></div>'


def test_the_news_heading_counts_as_current():
    notice = heat_protocol_notice(
        _soup(_news("Hitteprotocol: vandaag geopend van 08:00 tot 14:00")), _TODAY
    )

    assert notice is not None
    assert (notice.starts, notice.ends) == (_TODAY, _TODAY)


def test_an_unreadable_heat_protocol_with_a_written_date_is_reported():
    _, warnings = read_notices(
        _soup(_news("Hitteprotocol t/m 16 juli")), _LOCATIONS, _TODAY
    )

    assert warnings == ["Hitteprotocol niet leesbaar: Hitteprotocol t/m 16 juli"]


def test_a_closure_notice_keeps_its_heading_and_location():
    notices, warnings = read_notices(
        _soup(
            '<section data-block="textAndMedia"><h2> Let op! <span>Acht</span> '
            "dicht </h2><p>Gesloten t/m 16 juli</p></section>"
        ),
        _LOCATIONS,
        _TODAY,
    )

    assert warnings == []
    assert len(notices) == 1
    assert notices[0].title == "Let op! Acht dicht"
    assert notices[0].location_hint == "Milieustraat Acht"


def test_a_closure_notice_body_reads_across_paragraphs():
    notices, _ = read_notices(
        _soup(
            '<section data-block="textAndMedia"><h2>Let op!</h2>'
            "<p>Gesloten op</p><p>maandag 13 juli</p></section>"
        ),
        _LOCATIONS,
        _TODAY,
    )

    assert [notice.dates for notice in notices] == [[date(2026, 7, 13)]]


def test_closing_days_without_a_year_are_read_against_today():
    notices, warnings = read_notices(
        _soup("<h2>Sluitingsdagen</h2><p>Vrijdag 25 december</p>"),
        _LOCATIONS,
        _TODAY,
    )

    assert warnings == []
    assert [notice.dates for notice in notices] == [[date(2026, 12, 25)]]


def test_the_safety_net_reads_past_a_handled_heading():
    _, warnings = read_notices(
        _soup(
            '<section data-block="textAndMedia"><h2>Let op!</h2>'
            "<p>Gesloten t/m 16 juli</p></section>"
            "<h2>Gewijzigde tijden</h2><p>Op 20 juli gesloten</p>"
        ),
        _LOCATIONS,
        _TODAY,
    )

    assert warnings == ["Bericht niet verwerkt: Gewijzigde tijden"]
