"""Hostname normalisation and scope validation (pure functions)."""

from __future__ import annotations

import re

# A single DNS label: 1-63 chars, alphanumerics and interior hyphens.
_LABEL = r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
_HOSTNAME_RE = re.compile(rf"^(?=.{{1,253}}$){_LABEL}(?:\.{_LABEL})*$")


def normalize_domain(raw: str) -> str:
    """Normalise a target domain (lowercase, no trailing dot)."""
    return raw.strip().lower().rstrip(".")


def normalize_hostname(raw: str, domain: str) -> str | None:
    """Return the canonical form of ``raw`` if it is a valid subdomain of
    ``domain``; otherwise return ``None``.

    Rules (Requirement 2): lowercase; strip trailing dot and one leading
    ``*.`` wildcard prefix; reject names containing ``*`` or empty labels;
    reject the apex itself and anything not ending with ``.<domain>`` on a
    label boundary; reject invalid hostname syntax.
    """
    if raw is None:
        return None
    name = raw.strip().lower().rstrip(".")
    if name.startswith("*."):
        name = name[2:]
    domain = normalize_domain(domain)
    if not name or not domain:
        return None
    if "*" in name or ".." in name:
        return None
    if name == domain:
        return None  # the apex is not a subdomain
    if not name.endswith("." + domain):
        return None
    if not _HOSTNAME_RE.match(name):
        return None
    return name
