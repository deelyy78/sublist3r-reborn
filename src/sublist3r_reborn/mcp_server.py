"""MCP server (stdio) exposing the Sublist3r Reborn engine to AI agents.

Tools:
- ``enumerate_subdomains`` — passive enumeration + resolution + takeover
  assessment for a target domain.
- ``check_takeover`` — takeover assessment for a single hostname.
- ``resolve_records`` — A/AAAA/CNAME lookup for a single hostname.

Ethics (mirrored in every tool description): only use these tools on
domains the operator owns or is explicitly authorised to test.
"""

from __future__ import annotations

import sys

from .engine import EnumerationEngine
from .models import DnsRecords
from .output import record_to_dict, result_to_dict

ETHICS_NOTE = (
    "Only use on domains you own or are explicitly authorised to test "
    "(bug-bounty scope, pentest engagement, own assets). Enumeration is "
    "passive: it queries public data sources."
)


def _dns_to_dict(records: DnsRecords) -> dict:
    return {"a": list(records.a), "aaaa": list(records.aaaa), "cname": records.cname}


def main() -> None:
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        try:  # mcp 2.x renamed FastMCP to MCPServer
            from mcp.server.mcpserver import MCPServer as FastMCP
        except ImportError:
            print(
                "The 'mcp' package is required for the MCP server. "
                "Install it with: pip install 'sublist3r-reborn[mcp]'",
                file=sys.stderr,
            )
            raise SystemExit(1)

    server = FastMCP("sublist3r-reborn")
    engine = EnumerationEngine()

    @server.tool()
    async def enumerate_subdomains(
        domain: str, resolve: bool = True, check_takeover: bool = True
    ) -> dict:
        """Enumerate subdomains of a domain from passive sources (crt.sh,
        HackerTarget, AnubisDB), optionally resolve DNS records and assess
        subdomain-takeover risk. """ + ETHICS_NOTE
        result = await engine.enumerate(
            domain, resolve=resolve, check_takeover=check_takeover
        )
        return result_to_dict(result)

    @server.tool()
    async def check_takeover(subdomain: str) -> dict:
        """Assess subdomain-takeover risk for a single hostname: resolves
        its CNAME and checks whether it dangles into a takeover-prone
        third-party provider. """ + ETHICS_NOTE
        record = await engine.assess_host(subdomain)
        return record_to_dict(record)

    @server.tool()
    async def resolve_records(hostname: str) -> dict:
        """Resolve A, AAAA, and CNAME records for a single hostname."""
        records = await engine.resolver.resolve_all(hostname)
        return {"hostname": hostname, "dns": _dns_to_dict(records)}

    server.run()


if __name__ == "__main__":
    main()
