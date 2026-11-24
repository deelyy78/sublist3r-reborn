"""Command-line interface.

Keeps the classic Sublist3r flag feel (-d, -e, -o, -t, -v) with explicit
long flags. Run summaries and per-source errors go to stderr so stdout
stays machine-consumable for JSON/CSV.
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from . import __version__
from .engine import EnumerationEngine
from .models import EnumerationResult
from .output import render_table, to_csv, to_json
from .sources import DEFAULT_SOURCE_NAMES, build_sources

EPILOG = (
    "Ethics: only enumerate domains you own or are explicitly authorised "
    "to test (bug-bounty scope, pentest engagement, your own assets). "
    "Enumeration is passive: it queries public data sources."
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sublist3r-reborn",
        description=(
            "Sublist3r Reborn — async subdomain enumeration from passive "
            "sources, with DNS resolution and subdomain-takeover detection."
        ),
        epilog=EPILOG,
    )
    parser.add_argument("-d", "--domain", required=True, help="target domain")
    parser.add_argument(
        "-e",
        "--engines",
        default=None,
        help="comma-separated passive sources (default: %(default)s) — "
        + ", ".join(DEFAULT_SOURCE_NAMES),
    )
    parser.add_argument("-o", "--output", default=None, help="write results to this file")
    parser.add_argument(
        "--format",
        choices=["table", "json", "csv"],
        default=None,
        help="output format (default: table, or inferred from --output extension)",
    )
    parser.add_argument(
        "-t",
        "--threads",
        type=int,
        default=50,
        help="max concurrent DNS queries (default: 50)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="per-source request timeout in seconds (default: 30)",
    )
    parser.add_argument(
        "--no-resolve", action="store_true", help="skip DNS resolution and takeover checks"
    )
    parser.add_argument(
        "--no-takeover", action="store_true", help="resolve DNS but skip takeover assessment"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose summary")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def _infer_format(args: argparse.Namespace) -> str:
    if args.format:
        return args.format
    if args.output:
        lowered = args.output.lower()
        if lowered.endswith(".json"):
            return "json"
        if lowered.endswith(".csv"):
            return "csv"
    return "table"


def _render(result: EnumerationResult, fmt: str) -> str:
    if fmt == "json":
        return to_json(result)
    if fmt == "csv":
        return to_csv(result)
    return render_table(result)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    domain = args.domain.strip().lower()
    if "." not in domain or " " in domain:
        parser.error(f"invalid domain: {args.domain!r}")

    engine_names = (
        [part for part in args.engines.split(",") if part.strip()]
        if args.engines
        else None
    )
    try:
        sources = build_sources(engine_names, timeout=args.timeout)
    except ValueError as exc:
        parser.error(str(exc))

    engine = EnumerationEngine(sources=sources, concurrency=max(1, args.threads))
    result = asyncio.run(
        engine.enumerate(
            domain,
            resolve=not args.no_resolve,
            check_takeover=not args.no_takeover,
        )
    )

    fmt = _infer_format(args)
    rendered = _render(result, fmt)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(rendered + "\n")
    else:
        print(rendered)

    source_names = ", ".join(s.name for s in sources)
    print(
        f"[*] {result.count} subdomains found for {result.domain} "
        f"(sources: {source_names})",
        file=sys.stderr,
    )
    for name, error in result.errors.items():
        print(f"[!] source {name} failed: {error}", file=sys.stderr)
    if args.verbose:
        flagged = [
            r for r in result.records if r.takeover.status.value != "none"
        ]
        for record in flagged:
            print(
                f"[!] takeover {record.takeover.status.value}: {record.name} "
                f"-> {record.takeover.cname_target} ({record.takeover.provider})",
                file=sys.stderr,
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
