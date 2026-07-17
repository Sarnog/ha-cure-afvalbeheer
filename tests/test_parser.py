from datetime import date
from pathlib import Path

from custom_components.cure_afvalbeheer.parser import CureParser


def test_page_title():
    html = Path("tests/fixtures/milieustraat_eindhoven.html").read_text(
        encoding="utf-8"
    )

    parser = CureParser(html)

    assert parser.page_title() == "Milieustraat Eindhoven"


def test_headings():
    html = Path("tests/fixtures/milieustraat_eindhoven.html").read_text(
        encoding="utf-8"
    )

    parser = CureParser(html)

    headings = parser.headings()

    assert len(headings) > 5


def test_opening_hours_lines():
    html = Path("tests/fixtures/milieustraat_eindhoven.html").read_text(
        encoding="utf-8"
    )

    parser = CureParser(html)

    lines = parser.opening_hours_lines()

    assert len(lines) == 7
    assert lines[0].startswith("Maandag")
    assert lines[-1].startswith("Zon")


def test_location_name():
    html = Path("tests/fixtures/milieustraat_eindhoven.html").read_text(
        encoding="utf-8"
    )

    parser = CureParser(html)

    assert parser.location_name() == "Milieustraat Eindhoven"


def test_parse_locations():
    html = Path("tests/fixtures/milieustraat_eindhoven.html").read_text(
        encoding="utf-8"
    )

    parser = CureParser(html)

    locations = parser.parse_locations()

    assert len(locations) == 2

    assert locations[0].name == "Milieustraat Acht"
    assert locations[0].address == "Achtseweg Noord 41 5651 GG Eindhoven"

    assert locations[1].name == "Milieustraat Lodewijkstraat"
    assert locations[1].address == "Lodewijkstraat 9 5652 AC Eindhoven"

    assert len(locations[0].hours) == 7
    assert len(locations[1].hours) == 7


def test_location_addresses():
    html = Path("tests/fixtures/milieustraat_eindhoven.html").read_text(
        encoding="utf-8"
    )

    parser = CureParser(html)

    addresses = parser.location_addresses()

    assert addresses == [
        (
            "Milieustraat Acht",
            "Achtseweg Noord 41 5651 GG Eindhoven",
        ),
        (
            "Milieustraat Lodewijkstraat",
            "Lodewijkstraat 9 5652 AC Eindhoven",
        ),
    ]


def test_location_addresses_falls_back_to_page_title_without_h3():
    """Some single-location municipalities (e.g. Geldrop-Mierlo) have no
    h3 location name in the address section, only the heading and one
    address paragraph."""

    html = """
    <html>
    <body>
    <h1>Milieustraat Geldrop-Mierlo</h1>
    <section>
        <h2>Adres Milieustraat Geldrop-Mierlo</h2>
        <p>Industriepark 8 5663 PG Geldrop</p>
    </section>
    </body>
    </html>
    """

    parser = CureParser(html)

    assert parser.location_addresses() == [
        (
            "Milieustraat Geldrop-Mierlo",
            "Industriepark 8 5663 PG Geldrop",
        ),
    ]


def test_notices_finds_heat_protocol_and_scoped_closure():
    """The Eindhoven fixture contains both a site-wide heat protocol
    banner and a closure notice naming Lodewijkstraat specifically."""

    html = Path("tests/fixtures/milieustraat_eindhoven.html").read_text(
        encoding="utf-8"
    )

    parser = CureParser(html)
    locations = parser.parse_locations()

    notices = parser.notices(locations, today=date(2026, 7, 10))

    assert len(notices) == 2

    heat_protocol = next(n for n in notices if n.reason == "hitteprotocol")
    assert heat_protocol.opens == "08:00"
    assert heat_protocol.closes == "14:00"
    assert heat_protocol.ends == date(2026, 7, 16)
    assert heat_protocol.location_hint is None

    closure = next(n for n in notices if n.reason == "verbouwing")
    assert closure.closed is True
    assert closure.location_hint == "Milieustraat Lodewijkstraat"
