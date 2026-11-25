"""API client for Cure Afvalbeheer."""

from __future__ import annotations

import asyncio
from datetime import date

from aiohttp import ClientError, ClientSession, ClientTimeout

from .const import BASE_URL
from .exceptions import CureApiError
from .models import CureData
from .parser import CureParser

# Cure's pages are static HTML of well under a megabyte. A request taking
# longer than this is hanging rather than working, and holding the
# coordinator's update open any longer serves nobody.
_TIMEOUT = ClientTimeout(total=30)


class CureApiClient:
    """Client for retrieving Cure recycling centre information."""

    def __init__(self, session: ClientSession) -> None:
        """Initialise the API client."""

        self._session = session

    async def fetch_html(self, path: str) -> str:
        """Fetch HTML from the Cure website.

        Raises:
            CureApiError: for any failure to retrieve the page - a bad
                status, a refused connection, a timeout. The caller turns
                that into Home Assistant's "update failed", which is a
                plain line in the log rather than a traceback.
        """

        try:
            async with self._session.get(
                f"{BASE_URL}{path}", timeout=_TIMEOUT
            ) as response:
                response.raise_for_status()

                return await response.text()

        except (ClientError, TimeoutError) as err:
            raise CureApiError(
                f"Failed to fetch {path} from the Cure website: {err}"
            ) from err

    async def fetch_milieustraat(
        self, municipality: str, today: date | None = None
    ) -> CureData:
        """Fetch and parse the milieustraat page for a municipality.

        Parsing runs in a worker thread: BeautifulSoup walks the whole page
        synchronously, and doing that on the event loop would stall every
        other integration for as long as it takes.
        """

        html = await self.fetch_html(f"/milieustraat/milieustraat-{municipality}/")

        return await asyncio.to_thread(self.parse_html, html, today)

    def parse_html(self, html: str, today: date | None = None) -> CureData:
        """Parse HTML into CureData.

        Args:
            html: the page source.
            today: the date to read relative dates against. Home Assistant
                has a time zone of its own, which the machine it runs on
                need not share, so the caller passes the date rather than
                letting the parser take the system's.
        """

        parser = CureParser(html)

        return parser.parse(today)
