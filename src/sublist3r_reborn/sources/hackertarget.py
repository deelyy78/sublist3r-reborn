"""HackerTarget hostsearch source (https://hackertarget.com).

The free API returns one ``hostname,ip`` pair per line. On bad input or
quota exhaustion it returns plain-text error strings instead; those lines
are ignored by the parser (they contain no comma-separated hostname that
is in scope, and explicit error prefixes are filtered).
"""

from __future__ import annotations

import httpx

from .base import PassiveSource


def parse_hackertarget(text: str) -> set[str]:
    """Extract raw candidate hostnames from a HackerTarget response body."""
    names: set[str] = set()
    for line in text.splitlines():
        line = line.strip()
        if not line or "," not in line:
            continue
        host = line.split(",", 1)[0].strip()
        lowered = host.lower()
        if not host or lowered.startswith(("error", "no dns", "api count")):
            continue
        names.add(host)
    return names


class HackerTargetSource(PassiveSource):
    name = "hackertarget"
    url = "https://api.hackertarget.com/hostsearch/"

    async def fetch(self, domain: str, client: httpx.AsyncClient) -> set[str]:
        response = await client.get(
            self.url, params={"q": domain}, timeout=self.timeout
        )
        response.raise_for_status()
        return parse_hackertarget(response.text)
