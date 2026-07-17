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
    html = Path(
        "tests/fixtures/milieustraat_eindhoven.html"
    ).read_text(encoding="utf-8")

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
