"""Passive source base type.

A passive source queries a public data service for candidate hostnames.
Parsers are kept as separate pure functions so they can be unit-tested
against fixtures without any network access.
"""

from __future__ import annotations

import abc

import httpx


class PassiveSource(abc.ABC):
    """Base class for passive subdomain sources."""

    name: str = "base"

    def __init__(self, timeout: float = 30.0) -> None:
        self.timeout = timeout

    @abc.abstractmethod
    async def fetch(self, domain: str, client: httpx.AsyncClient) -> set[str]:
        """Return raw (unnormalised) candidate hostnames for ``domain``.

        Implementations raise on transport or parse failure; the engine
        records the failure against the source and continues with the rest.
        """
        raise NotImplementedError
