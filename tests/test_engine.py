"""Full engine runs against fake sources/resolvers — offline.

Covers: concurrent fan-out, dedup + source merging, scope filtering,
per-source failure isolation, resolution, and takeover assessment
(Requirements 1.3, 1.4, 2, 3, 4).
"""

import asyncio

import httpx

from sublist3r_reborn.engine import EnumerationEngine
from sublist3r_reborn.models import DnsRecords, TakeoverStatus


class FakeSource:
    def __init__(self, name, names=None, error=None):
        self.name = name
        self._names = names or set()
        self._error = error

    async def fetch(self, domain, client: httpx.AsyncClient):
        if self._error is not None:
            raise self._error
        return set(self._names)


class FakeResolver:
    def __init__(self, mapping):
        self._mapping = mapping

    async def resolve_all(self, name: str) -> DnsRecords:
        return self._mapping.get(name, DnsRecords())


def _engine(sources, mapping):
    return EnumerationEngine(
        sources=sources,
        resolver=FakeResolver(mapping),
        http_checks=False,  # never touch the network in tests
    )


def test_merges_dedups_and_filters_scope():
    sources = [
        FakeSource("a", {"www.example.com", "API.example.com", "other.org"}),
        FakeSource("b", {"www.example.com", "*.mail.example.com", "example.com"}),
    ]
    result = asyncio.run(_engine(sources, {}).enumerate("example.com", resolve=False))
    names = [r.name for r in result.records]
    assert names == ["api.example.com", "mail.example.com", "www.example.com"]
    by_name = {r.name: r for r in result.records}
    assert by_name["www.example.com"].sources == {"a", "b"}
    assert result.errors == {}


def test_source_failure_is_isolated():
    sources = [
        FakeSource("good", {"www.example.com"}),
        FakeSource("bad", error=RuntimeError("kaput")),
    ]
    result = asyncio.run(_engine(sources, {}).enumerate("example.com", resolve=False))
    assert [r.name for r in result.records] == ["www.example.com"]
    assert "bad" in result.errors and "kaput" in result.errors["bad"]


def test_all_sources_failing_returns_empty_with_errors():
    sources = [FakeSource("bad", error=ValueError("nope"))]
    result = asyncio.run(_engine(sources, {}).enumerate("example.com", resolve=False))
    assert result.records == []
    assert set(result.errors) == {"bad"}


def test_resolution_and_takeover_assessment():
    mapping = {
        # blog -> CNAME to GitHub Pages, whose target resolves: POSSIBLE
        "blog.example.com": DnsRecords(cname="user.github.io"),
        "user.github.io": DnsRecords(a=["185.199.108.153"]),
        # old -> CNAME to a Heroku app that no longer resolves: LIKELY
        "old.example.com": DnsRecords(cname="gone.herokuapp.com"),
        "gone.herokuapp.com": DnsRecords(),
        # www -> plain A record: NONE
        "www.example.com": DnsRecords(a=["192.0.2.1"]),
    }
    sources = [FakeSource("a", {"blog.example.com", "old.example.com", "www.example.com"})]
    result = asyncio.run(_engine(sources, mapping).enumerate("example.com"))
    by_name = {r.name: r for r in result.records}
    assert by_name["blog.example.com"].takeover.status is TakeoverStatus.POSSIBLE
    assert by_name["blog.example.com"].takeover.provider == "GitHub Pages"
    assert by_name["old.example.com"].takeover.status is TakeoverStatus.LIKELY
    assert by_name["www.example.com"].takeover.status is TakeoverStatus.NONE
    assert by_name["www.example.com"].dns.a == ["192.0.2.1"]


def test_no_resolve_skips_dns_and_takeover():
    sources = [FakeSource("a", {"www.example.com"})]
    result = asyncio.run(
        _engine(sources, {}).enumerate("example.com", resolve=False)
    )
    record = result.records[0]
    assert record.dns.a == [] and record.dns.cname is None
    assert record.takeover.status is TakeoverStatus.NONE
