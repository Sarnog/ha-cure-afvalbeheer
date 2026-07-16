from pathlib import Path

from custom_components.cure_afvalbeheer.parser import CureParser


def test_page_title():
    html = Path(
        "tests/fixtures/milieustraat_eindhoven.html"
    ).read_text(encoding="utf-8")

    parser = CureParser(html)

    assert parser.page_title() == "Milieustraat Eindhoven"