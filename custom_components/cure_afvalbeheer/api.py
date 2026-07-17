"""API client for Cure Afvalbeheer."""

from __future__ import annotations

from .models import CureData
from .parser import CureParser


class CureApiClient:
    """Client for retrieving Cure recycling centre information."""

    def parse_html(self, html: str) -> CureData:
        """Parse HTML into CureData."""

        parser = CureParser(html)

        return parser.parse()
