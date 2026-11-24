# Design Document — Sublist3r Reborn

## Overview

A small async Python package (`sublist3r_reborn`, src layout) with three
front doors — CLI, Python API, MCP server — over one shared engine. The
engine fans out to passive sources, normalises and deduplicates the union,
resolves DNS with bounded concurrency, and assesses takeover risk per
record. Everything network-facing is injectable so the whole pipeline is
testable offline.

```
            ┌────────────┐   ┌──────────────┐   ┌─────────────────┐
            │    CLI     │   │  MCP server  │   │  Python callers │
            └─────┬──────┘   └──────┬───────┘   └────────┬────────┘
                  └────────────┬────┴────────────────────┘
                               ▼
                    ┌─────────────────────┐
                    │  EnumerationEngine  │
                    └──────────┬──────────┘
        ┌──────────────────┬───┴───────────────┬──────────────────┐
        ▼                  ▼                   ▼                  ▼
 ┌─────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
 │   Sources   │   │  Normaliser  │   │   Resolver   │   │  Takeover    │
 │ crt.sh      │   │  (pure fns)  │   │ dnspython    │   │ fingerprints │
 │ HackerTarget│   │              │   │ async, sema- │   │ + HTTP probe │
 │ AnubisDB    │   │              │   │ phore-bound  │   │              │
 └─────────────┘   └──────────────┘   └──────────────┘   └──────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Output renderers   │  table / JSON / CSV
                    └─────────────────────┘
```

## Components

### Sources (`sublist3r_reborn/sources/`)
Each source is a small class with a `name` and an async
`fetch(domain, client) -> set[str]` returning *raw* candidate hostnames.
Response parsing lives in a separate pure function per source
(`parse_crtsh`, `parse_hackertarget`, `parse_anubisdb`) so fixtures can be
tested without any network. Sources raise on transport/parse failure; the
engine converts exceptions into per-source error entries (Requirement 1.3).

| Source | Endpoint | Notes |
| --- | --- | --- |
| crtsh | `https://crt.sh/?q=%.<domain>&output=json` | `name_value` may hold several newline-separated names, wildcards included |
| hackertarget | `https://api.hackertarget.com/hostsearch/?q=<domain>` | CSV lines `host,ip`; error strings must be ignored |
| anubisdb | `https://anubisdb.com/anubis/subdomains/<domain>` | JSON array of hostnames |

### Normaliser (`normalize.py`)
Pure function `normalize_hostname(raw, domain) -> str | None`. Implements
Requirement 2: lowercasing, wildcard/trailing-dot stripping, strict
label-boundary suffix check against the target domain, hostname syntax
validation (label regex + `..` rejection). The apex itself is excluded —
the tool enumerates *sub*domains.

### Resolver (`resolver.py`)
`DnsResolver` wraps `dns.asyncresolver` with a semaphore limiting
in-flight queries. `resolve_all(name) -> DnsRecords` queries A, AAAA and
CNAME independently; NXDOMAIN / NoAnswer / Timeout / NoNameservers all map
to empty results (Requirement 3.3). CNAME targets are lowercased and
de-dotted. The engine depends on a structural `resolve_all` protocol, so
tests inject a fake resolver.

### Takeover (`takeover.py`)
A curated table of `ProviderFingerprint(suffix, provider,
http_signatures)` entries, written from public knowledge of
takeover-prone services. `match_provider(hostname)` performs
longest-suffix matching on label boundaries only (Requirement 4.5). The
pure function `assess_takeover(cname_target, target_resolves,
http_signature_hit)` maps evidence to `none` / `possible` / `likely`
(Requirements 4.2–4.4, 4.6). `probe_http_signature()` fetches the
candidate over HTTPS/HTTP and searches the body for the provider's
unclaimed-resource error string; it runs only for provider-matching
candidates.

### Engine (`engine.py`)
`EnumerationEngine(sources, resolver, concurrency, http_checks)`:
1. gather all sources concurrently over one shared `httpx.AsyncClient`
   with an identifying User-Agent (Requirements 1.1, 7.3);
2. normalise + merge into `SubdomainRecord`s sorted by name;
3. resolve all records concurrently;
4. for records with a CNAME: resolve the target, optionally probe HTTP
   signatures, and attach the assessment.
`assess_host(name)` exposes steps 3–4 for a single host (used by the
MCP `check_takeover` tool).

### Output (`output.py`)
`record_to_dict` / `result_to_dict` define the canonical serialisation;
`to_json`, `to_csv`, `render_table` are thin renderers over it. The CLI
infers format from the output filename extension when `--format` is not
given (Requirement 5.2/5.3) and prints run summaries to stderr (5.4).

### CLI (`cli.py`)
`argparse` front end keeping the classic flag *feel* (`-d`, `-e`, `-o`,
`-t`, `-v`) plus explicit long flags. Validation errors exit with code 2
via argparse; a completed run exits 0 even when some sources failed, as
long as their errors are reported.

### MCP server (`mcp_server.py`)
Built on the official `mcp` Python SDK (`FastMCP`, stdio transport). The
three tools are thin async wrappers over the engine, returning the same
dict structures as the JSON renderer. Registered for Kiro in
`.kiro/settings/mcp.json`.

## Data models

```python
TakeoverStatus = Enum("none" | "possible" | "likely")

@dataclass TakeoverAssessment: status, provider, cname_target, reason
@dataclass DnsRecords:         a: list[str], aaaa: list[str], cname: str | None
@dataclass SubdomainRecord:    name, sources: set[str], dns, takeover
@dataclass EnumerationResult:  domain, records: list[SubdomainRecord], errors: dict[str, str]
```

## Error handling

- Source failures never abort a run; they accumulate in
  `EnumerationResult.errors` keyed by source name.
- DNS failures are indistinguishable from "no such record" by design —
  recon tooling must be robust against flaky resolvers.
- HTTP probes swallow all transport errors and report "no signature".
- The MCP entry point degrades to a clear message if the optional `mcp`
  dependency is missing (Requirement 6.5).

## Correctness properties

1. **Dedup invariant:** for any multiset of raw candidates, the output
   contains each valid normalised hostname exactly once.
2. **Scope invariant:** every emitted hostname ends with `"." + domain`
   and none equals the apex.
3. **Boundary invariant:** provider matching never fires on a substring
   that is not aligned to a DNS label boundary.
4. **Failure isolation:** an exception in any single source, DNS query,
   or HTTP probe never propagates out of `enumerate()`.

## Testing strategy

Offline `pytest` suite: parser fixtures per source, normaliser edge
cases, fingerprint boundary cases, pure assessment logic, output
renderers, and a full engine run against fake sources/resolvers. Live
network checks are manual smoke tests only, never part of the suite.
