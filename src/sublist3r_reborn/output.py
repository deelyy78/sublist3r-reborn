"""Output renderers: canonical dict serialisation, JSON, CSV, table."""

from __future__ import annotations

import csv
import io
import json

from .models import EnumerationResult, SubdomainRecord


def record_to_dict(record: SubdomainRecord) -> dict:
    return {
        "name": record.name,
        "sources": sorted(record.sources),
        "dns": {
            "a": list(record.dns.a),
            "aaaa": list(record.dns.aaaa),
            "cname": record.dns.cname,
        },
        "takeover": {
            "status": record.takeover.status.value,
            "provider": record.takeover.provider,
            "cname_target": record.takeover.cname_target,
            "reason": record.takeover.reason,
        },
    }


def result_to_dict(result: EnumerationResult) -> dict:
    return {
        "domain": result.domain,
        "count": result.count,
        "subdomains": [record_to_dict(r) for r in result.records],
        "errors": dict(result.errors),
    }


def to_json(result: EnumerationResult) -> str:
    return json.dumps(result_to_dict(result), indent=2)


def to_csv(result: EnumerationResult) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        ["name", "sources", "a", "aaaa", "cname", "takeover_status", "takeover_provider"]
    )
    for record in result.records:
        writer.writerow(
            [
                record.name,
                ";".join(sorted(record.sources)),
                ";".join(record.dns.a),
                ";".join(record.dns.aaaa),
                record.dns.cname or "",
                record.takeover.status.value,
                record.takeover.provider or "",
            ]
        )
    return buffer.getvalue()


def render_table(result: EnumerationResult) -> str:
    header = f"{'SUBDOMAIN':<50} {'A':<16} {'CNAME':<34} TAKEOVER"
    lines = [header, "-" * len(header)]
    for record in result.records:
        a = record.dns.a[0] if record.dns.a else "-"
        cname = record.dns.cname or "-"
        takeover = (
            record.takeover.status.value.upper()
            if record.takeover.status.value != "none"
            else "-"
        )
        lines.append(f"{record.name:<50} {a:<16} {cname:<34} {takeover}")
    return "\n".join(lines)
