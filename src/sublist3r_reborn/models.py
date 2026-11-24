"""Core data models shared by the engine, CLI, output renderers, and MCP server."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class TakeoverStatus(str, Enum):
    """Verdict of a subdomain-takeover assessment."""

    NONE = "none"
    POSSIBLE = "possible"
    LIKELY = "likely"


@dataclass
class TakeoverAssessment:
    status: TakeoverStatus = TakeoverStatus.NONE
    provider: str | None = None
    cname_target: str | None = None
    reason: str = ""


@dataclass
class DnsRecords:
    a: list[str] = field(default_factory=list)
    aaaa: list[str] = field(default_factory=list)
    cname: str | None = None


@dataclass
class SubdomainRecord:
    name: str
    sources: set[str] = field(default_factory=set)
    dns: DnsRecords = field(default_factory=DnsRecords)
    takeover: TakeoverAssessment = field(default_factory=TakeoverAssessment)


@dataclass
class EnumerationResult:
    domain: str
    records: list[SubdomainRecord] = field(default_factory=list)
    errors: dict[str, str] = field(default_factory=dict)

    @property
    def count(self) -> int:
        return len(self.records)
