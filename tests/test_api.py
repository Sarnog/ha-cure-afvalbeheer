from pathlib import Path
from unittest.mock import Mock

from aiohttp import ClientSession

from custom_components.cure_afvalbeheer.api import CureApiClient
from custom_components.cure_afvalbeheer.models import CureData


def test_parse_html() -> None:
    """Test parsing HTML into CureData."""

    html = Path("tests/fixtures/milieustraat_eindhoven.html").read_text(
        encoding="utf-8"
    )

    session = Mock(spec=ClientSession)
    client = CureApiClient(session)

    result = client.parse_html(html)

    assert isinstance(result, CureData)
    assert len(result.locations) == 2
