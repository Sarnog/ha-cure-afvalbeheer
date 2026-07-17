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

    assert len(lines) == 6
    assert lines[0].startswith("Maandag")
    assert lines[-1].startswith("Zaterdag")


def test_location_name():
    html = Path("tests/fixtures/milieustraat_eindhoven.html").read_text(
        encoding="utf-8"
    )

    parser = CureParser(html)

    assert parser.location_name() == "Milieustraat Eindhoven"


def test_parse_location():
    html = Path("tests/fixtures/milieustraat_eindhoven.html").read_text(
        encoding="utf-8"
    )

    parser = CureParser(html)

    location = parser.parse_location()

    assert location.name == "Milieustraat Eindhoven"
    assert location.address is None
    assert len(location.hours) == 6


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

    assert len(locations[0].hours) == 6
    assert len(locations[1].hours) == 6


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
