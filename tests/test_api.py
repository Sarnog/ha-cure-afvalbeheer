from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest
from aiohttp import ClientResponseError, ClientSession
from yarl import URL

from custom_components.cure_afvalbeheer.api import (
    CureApiClient,
    CureApiError,
)
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


@pytest.mark.anyio
async def test_fetch_html_raises_http_error() -> None:
    """Test that HTTP errors are propagated."""

    response = Mock()
    response.raise_for_status.side_effect = ClientResponseError(
        request_info=Mock(real_url=URL("https://example.com")),
        history=(),
        status=500,
        message="Internal Server Error",
    )

    session = AsyncMock(spec=ClientSession)
    session.get.return_value.__aenter__.return_value = response

    client = CureApiClient(session)

    with pytest.raises(
        CureApiError,
        match="Failed to fetch HTML from Cure website",
    ):
        await client.fetch_html("/")


@pytest.mark.anyio
async def test_fetch_milieustraat() -> None:
    """Test fetching and parsing the milieustraat page."""

    html = Path("tests/fixtures/milieustraat_eindhoven.html").read_text(
        encoding="utf-8"
    )

    session = Mock(spec=ClientSession)

    client = CureApiClient(session)

    client.fetch_html = AsyncMock(return_value=html)

    result = await client.fetch_milieustraat()

    assert isinstance(result, CureData)
    assert len(result.locations) == 2

    client.fetch_html.assert_awaited_once_with("/milieustraat/")
