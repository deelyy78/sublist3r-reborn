"""Certificate Transparency source: crt.sh (https://crt.sh).

crt.sh indexes TLS certificates; every certificate's subject/SAN names are
candidate subdomains. The JSON output carries a ``name_value`` field that
may contain several newline-separated names (including wildcards) plus a
``common_name`` field.
"""

from __future__ import annotations

import json

import httpx

from .base import PassiveSource


def parse_crtsh(text: str) -> set[str]:
    """Extract raw candidate hostnames from a crt.sh JSON response body."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"crt.sh returned invalid JSON: {exc}") from exc
    names: set[str] = set()
    if not isinstance(data, list):
        return names
    for entry in data:
        if not isinstance(entry, dict):
            continue
        for key in ("name_value", "common_name"):
            value = entry.get(key)
            if isinstance(value, str):
                for line in value.splitlines():
                    line = line.strip()
                    if line:
                        names.add(line)
    return names


class CrtShSource(PassiveSource):
    name = "crtsh"
    url = "https://crt.sh/"

    async def fetch(self, domain: str, client: httpx.AsyncClient) -> set[str]:
        response = await client.get(
            self.url,
            params={"q": f"%.{domain}", "output": "json"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return parse_crtsh(response.text)
