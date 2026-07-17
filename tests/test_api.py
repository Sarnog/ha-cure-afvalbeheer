from pathlib import Path

from custom_components.cure_afvalbeheer.api import CureApiClient
from custom_components.cure_afvalbeheer.models import CureData


def test_parse_html():
    html = Path("tests/fixtures/milieustraat_eindhoven.html").read_text(
        encoding="utf-8"
    )

    client = CureApiClient()

    result = client.parse_html(html)

    assert isinstance(result, CureData)
    assert len(result.locations) == 2
