"""API client for Cure Afvalbeheer."""

from __future__ import annotations

from aiohttp import ClientResponseError, ClientSession

from .const import BASE_URL
from .exceptions import CureApiError
from .models import CureData
from .parser import CureParser


class CureApiClient:
    """Client for retrieving Cure recycling centre information."""

    def __init__(self, session: ClientSession) -> None:
        """Initialise the API client."""

        self._session = session

    async def fetch_html(self, path: str) -> str:
        """Fetch HTML from the Cure website."""

        try:
            async with self._session.get(f"{BASE_URL}{path}") as response:
                response.raise_for_status()

                return await response.text()

        except ClientResponseError as err:
            raise CureApiError("Failed to fetch HTML from Cure website") from err

    async def fetch_milieustraat(self, municipality: str) -> CureData:
        """Fetch and parse the milieustraat page for a municipality."""

        html = await self.fetch_html(f"/milieustraat/milieustraat-{municipality}/")

        return self.parse_html(html)

    def parse_html(self, html: str) -> CureData:
        """Parse HTML into CureData."""

        parser = CureParser(html)

        return parser.parse()
