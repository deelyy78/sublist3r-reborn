"""Asynchronous DNS resolution built on dnspython.

Design rule: DNS failure is data, not an exception. NXDOMAIN, missing
record types, timeouts, and resolver errors all produce empty results so
that one bad name can never fail an enumeration run (Requirement 3.3).
"""

from __future__ import annotations

import asyncio
from typing import Protocol

import dns.asyncresolver
import dns.exception
import dns.resolver

from .models import DnsRecords


class ResolverLike(Protocol):
    """Structural type the engine depends on (tests inject fakes)."""

    async def resolve_all(self, name: str) -> DnsRecords: ...


class DnsResolver:
    """Semaphore-bounded async resolver for A / AAAA / CNAME records."""

    def __init__(
        self,
        timeout: float = 5.0,
        concurrency: int = 50,
        nameservers: list[str] | None = None,
    ) -> None:
        self._resolver = dns.asyncresolver.Resolver(configure=True)
        self._resolver.lifetime = timeout
        if nameservers:
            self._resolver.nameservers = nameservers
        self._semaphore = asyncio.Semaphore(max(1, concurrency))

    async def _query(self, name: str, rdtype: str) -> list[str]:
        async with self._semaphore:
            try:
                answer = await self._resolver.resolve(name, rdtype)
            except (
                dns.resolver.NXDOMAIN,
                dns.resolver.NoAnswer,
                dns.resolver.NoNameservers,
                dns.exception.Timeout,
                dns.exception.DNSException,
            ):
                return []
            values: list[str] = []
            for rdata in answer:
                if rdtype == "CNAME":
                    values.append(rdata.target.to_text().rstrip(".").lower())
                else:
                    values.append(rdata.to_text())
            return values

    async def resolve_all(self, name: str) -> DnsRecords:
        a, aaaa, cname = await asyncio.gather(
            self._query(name, "A"),
            self._query(name, "AAAA"),
            self._query(name, "CNAME"),
        )
        return DnsRecords(a=a, aaaa=aaaa, cname=cname[0] if cname else None)
