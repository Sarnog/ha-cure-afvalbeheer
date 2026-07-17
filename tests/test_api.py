from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest
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


@pytest.mark.anyio
async def test_fetch_html() -> None:
    """Test fetching HTML."""

    response = Mock()
    response.text = AsyncMock(return_value="<html></html>")
    response.raise_for_status.return_value = None

    session = AsyncMock(spec=ClientSession)
    session.get.return_value.__aenter__.return_value = response

    client = CureApiClient(session)

    html = await client.fetch_html("/")

    assert html == "<html></html>"
