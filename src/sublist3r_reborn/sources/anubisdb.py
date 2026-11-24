"""AnubisDB source (https://anubisdb.com).

AnubisDB is a public subdomain database; its open endpoint returns a JSON
array of hostname strings for a domain, no API key required.
"""

from __future__ import annotations

import json

import httpx

from .base import PassiveSource


def parse_anubisdb(text: str) -> set[str]:
    """Extract raw candidate hostnames from an AnubisDB response body."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"AnubisDB returned invalid JSON: {exc}") from exc
    names: set[str] = set()
    if isinstance(data, list):
        for item in data:
            if isinstance(item, str) and item.strip():
                names.add(item.strip())
    return names


class AnubisDbSource(PassiveSource):
    name = "anubisdb"
    url_template = "https://anubisdb.com/anubis/subdomains/{domain}"

    async def fetch(self, domain: str, client: httpx.AsyncClient) -> set[str]:
        response = await client.get(
            self.url_template.format(domain=domain), timeout=self.timeout
        )
        response.raise_for_status()
        return parse_anubisdb(response.text)
