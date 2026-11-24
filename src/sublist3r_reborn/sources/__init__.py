"""Passive source registry."""

from __future__ import annotations

from .anubisdb import AnubisDbSource
from .base import PassiveSource
from .crtsh import CrtShSource
from .hackertarget import HackerTargetSource

SOURCE_TYPES: dict[str, type[PassiveSource]] = {
    CrtShSource.name: CrtShSource,
    HackerTargetSource.name: HackerTargetSource,
    AnubisDbSource.name: AnubisDbSource,
}

DEFAULT_SOURCE_NAMES: tuple[str, ...] = ("crtsh", "hackertarget", "anubisdb")


def build_sources(names: list[str] | None = None, timeout: float = 30.0) -> list[PassiveSource]:
    """Instantiate sources by registry name (defaults to all of them).

    Raises ``ValueError`` listing the valid names for an unknown source.
    """
    selected = names if names else list(DEFAULT_SOURCE_NAMES)
    sources: list[PassiveSource] = []
    for name in selected:
        key = name.strip().lower()
        if key not in SOURCE_TYPES:
            valid = ", ".join(sorted(SOURCE_TYPES))
            raise ValueError(f"unknown source {name!r}; valid sources: {valid}")
        sources.append(SOURCE_TYPES[key](timeout=timeout))
    return sources


__all__ = [
    "PassiveSource",
    "CrtShSource",
    "HackerTargetSource",
    "AnubisDbSource",
    "SOURCE_TYPES",
    "DEFAULT_SOURCE_NAMES",
    "build_sources",
]
