"""Enumeration engine: fan out to passive sources, normalise, resolve,
assess takeover risk.

Failure isolation is a design invariant (see design.md): a failing source,
DNS query, or HTTP probe degrades to data and never aborts the run.
"""

from __future__ import annotations

import asyncio
import os

import httpx

from . import __version__
from .models import EnumerationResult, SubdomainRecord
from .normalize import normalize_domain, normalize_hostname
from .resolver import DnsResolver, ResolverLike
from .sources import PassiveSource, build_sources
from .takeover import assess_takeover, match_provider, probe_http_signature

USER_AGENT = f"sublist3r-reborn/{__version__} (+https://kiroween.devpost.com)"


def _new_client(timeout: float) -> httpx.AsyncClient:
    """Build the shared HTTP client.

    Proxy environment variables are honoured by default. Some environments
    export ``NO_PROXY`` entries (e.g. bracketed IPv6 literals) that httpx
    cannot parse while building proxy mounts, which makes plain client
    construction raise ``InvalidURL``; in that case fall back to an
    explicitly configured proxy taken from the environment with
    ``trust_env`` disabled.
    """
    kwargs: dict = {
        "headers": {"User-Agent": USER_AGENT},
        "timeout": httpx.Timeout(timeout),
    }
    try:
        return httpx.AsyncClient(**kwargs)
    except httpx.InvalidURL:
        proxy = (
            os.environ.get("HTTPS_PROXY")
            or os.environ.get("https_proxy")
            or os.environ.get("ALL_PROXY")
            or os.environ.get("all_proxy")
        )
        return httpx.AsyncClient(trust_env=False, proxy=proxy, **kwargs)


class EnumerationEngine:
    def __init__(
        self,
        sources: list[PassiveSource] | None = None,
        resolver: ResolverLike | None = None,
        concurrency: int = 50,
        http_checks: bool = True,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.sources = sources if sources is not None else build_sources()
        self.resolver: ResolverLike = resolver or DnsResolver(concurrency=concurrency)
        self.http_checks = http_checks
        self._client = client

    # -- internals -----------------------------------------------------

    async def _fetch_source(
        self, source: PassiveSource, domain: str, client: httpx.AsyncClient
    ) -> set[str]:
        return await source.fetch(domain, client)

    async def _resolve_record(self, record: SubdomainRecord) -> None:
        record.dns = await self.resolver.resolve_all(record.name)

    async def _assess_record(
        self, record: SubdomainRecord, client: httpx.AsyncClient
    ) -> None:
        cname = record.dns.cname
        if not cname:
            record.takeover = assess_takeover(None, target_resolves=False)
            return
        target_records = await self.resolver.resolve_all(cname)
        target_resolves = bool(target_records.a or target_records.aaaa)
        signature_hit = False
        fingerprint = match_provider(cname)
        if fingerprint is not None and self.http_checks:
            signature_hit = await probe_http_signature(
                client, record.name, fingerprint
            )
        record.takeover = assess_takeover(
            cname,
            target_resolves=target_resolves,
            http_signature_hit=signature_hit,
        )

    # -- public API ----------------------------------------------------

    async def enumerate(
        self,
        domain: str,
        resolve: bool = True,
        check_takeover: bool = True,
    ) -> EnumerationResult:
        """Enumerate subdomains of ``domain`` from all configured sources."""
        domain = normalize_domain(domain)
        errors: dict[str, str] = {}
        merged: dict[str, set[str]] = {}

        owns_client = self._client is None
        client = self._client or _new_client(35.0)
        try:
            results = await asyncio.gather(
                *(self._fetch_source(s, domain, client) for s in self.sources),
                return_exceptions=True,
            )
            for source, result in zip(self.sources, results):
                if isinstance(result, Exception):
                    errors[source.name] = f"{type(result).__name__}: {result}"
                    continue
                for raw in result:
                    name = normalize_hostname(raw, domain)
                    if name:
                        merged.setdefault(name, set()).add(source.name)

            records = [
                SubdomainRecord(name=name, sources=sources)
                for name, sources in sorted(merged.items())
            ]

            if resolve:
                await asyncio.gather(
                    *(self._resolve_record(r) for r in records)
                )
                if check_takeover:
                    await asyncio.gather(
                        *(self._assess_record(r, client) for r in records)
                    )
            return EnumerationResult(domain=domain, records=records, errors=errors)
        finally:
            if owns_client:
                await client.aclose()

    async def assess_host(self, hostname: str) -> SubdomainRecord:
        """Resolve one hostname and assess its takeover risk (MCP helper)."""
        record = SubdomainRecord(name=normalize_domain(hostname))
        await self._resolve_record(record)
        owns_client = self._client is None
        client = self._client or _new_client(15.0)
        try:
            await self._assess_record(record, client)
        finally:
            if owns_client:
                await client.aclose()
        return record
