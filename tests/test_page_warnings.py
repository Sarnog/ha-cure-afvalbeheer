"""Everything on the page that cannot be read is reported, not skipped.

The sensors have to match the website at all times. Where the parser
meets a message, closing day or location it cannot read, the only honest
answer is to say so: a warning in CureData.warnings, which the coordinator
turns into a repair notification. These tests pin down that each kind of
content is covered, and that a normal page raises nothing.
"""

from datetime import date

import pytest

from custom_components.cure_afvalbeheer.parsing.page import CureParser
from tests.hulp import read_fixture

_TODAY = date(2026, 11, 25)

_HOURS = (
    "<div><h2>Openingstijden</h2>"
    "<p>Maandag t/m zaterdag: 08:30 tot 17:00</p>"
    "<p>Zon &amp; Feestdagen: Gesloten</p></div>"
)

_ADDRESSES = (
    "<div><h2>Adres Milieustraten Eindhoven</h2>"
    "<h3>Milieustraat Acht</h3><p>Achtseweg Noord 41</p>"
    "<h3>Milieustraat Lodewijkstraat</h3><p>Lodewijkstraat 9</p></div>"
)


def _page(*blocks: str, addresses: str = _ADDRESSES) -> str:
    """Return a minimal page with addresses, hours and the given blocks."""

    return (
        "<html><body><main><h1>Milieustraat Eindhoven</h1>"
        f"{''.join(blocks)}{addresses}{_HOURS}"
        "</main></body></html>"
    )


@pytest.mark.parametrize(
    "fixture",
    ["milieustraat_eindhoven", "milieustraat_eindhoven_nieuwe_tijden"],
)
@pytest.mark.parametrize(
    "today",
    [date(2026, 7, 14), date(2026, 11, 25), date(2026, 12, 20)],
)
def test_the_real_page_raises_no_warnings(fixture, today):
    """A warning that is always there gets ignored; a normal page has none."""

    html = read_fixture(f"{fixture}.html")

    assert CureParser(html).parse(today).warnings == []


def test_a_minimal_page_raises_no_warnings():
    assert CureParser(_page()).parse(_TODAY).warnings == []


def test_an_unreadable_let_op_notice_is_reported():
    html = _page(
        '<div data-block="textAndMedia"><h2>Let op! Werkzaamheden</h2>'
        "<p>Binnenkort gaan we de milieustraat aanpassen.</p></div>"
    )

    assert CureParser(html).parse(_TODAY).warnings == [
        "Mededeling niet leesbaar: Let op! Werkzaamheden"
    ]


def test_an_unreadable_heat_protocol_is_reported():
    html = _page(
        '<div data-block="newsBlock"><h2>Let op! Hitteprotocol! Gewijzigde '
        "openingstijden op onze milieustraten</h2></div>"
    )

    warnings = CureParser(html).parse(_TODAY).warnings

    assert len(warnings) == 1
    assert warnings[0].startswith("Hitteprotocol niet leesbaar:")


def test_a_news_message_about_closing_is_reported():
    html = _page(
        '<div data-block="newsBlock"><h2>Alle milieustraten gesloten op '
        "5 december wegens storm</h2></div>"
    )

    assert CureParser(html).parse(_TODAY).warnings == [
        "Bericht niet verwerkt: Alle milieustraten gesloten op 5 december wegens storm"
    ]


def test_an_unreadable_closing_day_is_reported():
    html = _page(
        "<div><h2>Sluitingsdagen 2026</h2><ul>"
        "<li><p>Vrijdag 25 december 2026 (Kerstmis)</p></li>"
        "<li><p>Zaterdag 26 december 2026: geopend, tijden volgen</p></li>"
        "</ul></div>"
    )

    data = CureParser(html).parse(_TODAY)

    assert data.warnings == [
        "Sluitingsdag niet leesbaar: Zaterdag 26 december 2026: geopend, tijden volgen"
    ]
    # The readable line still counts.
    assert [notice.dates for notice in data.notices] == [[date(2026, 12, 25)]]


def test_a_notice_in_a_block_of_a_new_kind_is_reported():
    """The safety net for a layout change: no "Let op", still a message."""

    html = _page(
        "<div><h2>Storing: milieustraat Acht dicht</h2>"
        "<p>Op donderdag 3 december is de milieustraat Acht gesloten.</p></div>"
    )

    assert CureParser(html).parse(_TODAY).warnings == [
        "Bericht niet verwerkt: Storing: milieustraat Acht dicht"
    ]


def test_a_location_without_an_address_is_kept_and_reported():
    """Such a location used to vanish from the sensors without a word."""

    html = _page(
        addresses=(
            "<div><h2>Adres Milieustraten Eindhoven</h2>"
            "<h3>Milieustraat Acht</h3>"
            "<h3>Milieustraat Lodewijkstraat</h3><p>Lodewijkstraat 9</p></div>"
        )
    )

    data = CureParser(html).parse(_TODAY)

    assert [(loc.name, loc.address) for loc in data.locations] == [
        ("Milieustraat Acht", None),
        ("Milieustraat Lodewijkstraat", "Lodewijkstraat 9"),
    ]
    assert data.warnings == ["Geen adres gevonden voor Milieustraat Acht"]


def test_a_location_on_a_site_map_but_not_in_the_addresses_is_reported():
    html = _page(
        '<div data-block="linkCards"><h3>Plattegrond Milieustraat Acht</h3>'
        "<h3>Plattegrond Milieustraat Woenselse Poort</h3></div>"
    )

    assert CureParser(html).parse(_TODAY).warnings == [
        "Milieustraat Woenselse Poort staat op de pagina, maar niet bij de adressen"
    ]
