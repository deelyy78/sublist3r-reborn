# Requirements Document — Sublist3r Reborn

## Introduction

Sublist3r Reborn is a clean-room reimplementation of the classic Sublist3r
subdomain enumerator (2015), rebuilt as a modern async Python package. It
enumerates subdomains from passive public sources, resolves them via DNS,
detects subdomain-takeover risk from dangling CNAME records, and exposes the
same capabilities to AI agents through an MCP (Model Context Protocol)
server. The original GPL-2.0 project is a behavioural reference only; no
original code is reused.

Target category: **Kiroween 2026 — Resurrection**.

## Glossary

- **Target Domain**: the apex domain supplied by the user (e.g. `example.com`).
- **Candidate**: a raw hostname string returned by a passive source, before
  normalisation.
- **Subdomain Record**: a normalised, deduplicated subdomain together with
  its sources, DNS records, and takeover assessment.
- **Passive Source**: a third-party public data service (crt.sh,
  HackerTarget, AnubisDB) that lists subdomains without probing the target.
- **Dangling CNAME**: a CNAME record whose target no longer resolves or
  whose hosted resource no longer exists.
- **Takeover Assessment**: a verdict of `none`, `possible`, or `likely`
  with a human-readable reason.
- **Engine**: the orchestrator that queries sources, normalises results,
  resolves DNS, and assesses takeover risk.

## Requirements

### Requirement 1: Passive enumeration from multiple sources

**User story:** As a security researcher, I want subdomains of my target
domain collected from several passive sources at once, so that coverage
does not depend on any single service being alive.

#### Acceptance Criteria

1. WHEN the user starts an enumeration, THE SYSTEM SHALL query every
   enabled passive source concurrently for the target domain.
2. WHEN a passive source returns candidate hostnames, THE SYSTEM SHALL
   attribute each resulting subdomain to the source(s) that produced it.
3. WHEN a passive source times out, returns an HTTP error, or returns
   malformed data, THE SYSTEM SHALL record the failure against that source
   and continue enumeration with the remaining sources.
4. IF all passive sources fail, THEN THE SYSTEM SHALL return an empty
   result together with the per-source errors instead of crashing.
5. THE SYSTEM SHALL NOT require API keys for any built-in passive source.

### Requirement 2: Normalisation and deduplication

**User story:** As a user, I want one clean entry per real subdomain, so
that reports are not polluted by wildcards, duplicates, or other people's
domains.

#### Acceptance Criteria

1. WHEN a candidate is processed, THE SYSTEM SHALL lowercase it and strip
   any trailing dot and any leading `*.` wildcard prefix.
2. WHEN a candidate appears in several sources or several times in one
   source, THE SYSTEM SHALL emit exactly one subdomain record for it,
   merging the source attributions.
3. WHEN a candidate does not end with the target domain on a label
   boundary, or equals the target domain itself, THE SYSTEM SHALL discard
   it.
4. WHEN a candidate contains characters that are invalid in a hostname,
   empty labels, or a remaining `*` character, THE SYSTEM SHALL discard it.

### Requirement 3: Asynchronous DNS resolution

**User story:** As a user, I want discovered subdomains resolved quickly,
so that a several-hundred-host result set finishes in seconds.

#### Acceptance Criteria

1. WHEN resolution is enabled, THE SYSTEM SHALL resolve A, AAAA, and CNAME
   records for every subdomain record.
2. THE SYSTEM SHALL bound the number of concurrent DNS queries to a
   configurable limit (default 50).
3. WHEN a name does not exist (NXDOMAIN) or has no record of a requested
   type, THE SYSTEM SHALL record an empty result for that record type
   instead of failing the run.
4. WHEN resolution is disabled via CLI flag or tool argument, THE SYSTEM
   SHALL skip all DNS queries and mark takeover assessment as skipped.

### Requirement 4: Subdomain-takeover detection

**User story:** As a bug-bounty hunter, I want dangling CNAMEs flagged, so
that I can prioritise subdomains that may be claimable on third-party
providers.

#### Acceptance Criteria

1. WHEN a subdomain has a CNAME whose target ends, on a label boundary,
   with a known takeover-prone provider suffix (e.g. `github.io`,
   `herokuapp.com`, `s3.amazonaws.com`, `azurewebsites.net`,
   `netlify.app`), THE SYSTEM SHALL mark the record as a takeover
   candidate for that provider.
2. WHEN a candidate's CNAME target does not resolve to any A or AAAA
   record, THE SYSTEM SHALL assess the takeover status as `likely`.
3. WHEN a candidate's HTTP response body contains the provider's known
   unclaimed-resource error signature, THE SYSTEM SHALL assess the
   takeover status as `likely`.
4. WHEN a candidate points at a known provider but the target resolves and
   no error signature is observed, THE SYSTEM SHALL assess the status as
   `possible`.
5. WHEN a hostname merely contains a provider suffix as a substring
   without a label boundary (e.g. `evilgithub.io`), THE SYSTEM SHALL NOT
   treat it as that provider.
6. WHEN a subdomain has no CNAME, THE SYSTEM SHALL assess the takeover
   status as `none`.

### Requirement 5: Output formats

**User story:** As a user, I want results as a terminal table, JSON, or
CSV, so that I can read them directly or feed them into other tooling.

#### Acceptance Criteria

1. THE SYSTEM SHALL render results as a human-readable table by default.
2. WHEN JSON output is requested or the output filename ends in `.json`,
   THE SYSTEM SHALL emit a document containing the target domain, the
   record count, the per-source errors, and one object per subdomain with
   name, sources, DNS records, and takeover assessment.
3. WHEN CSV output is requested or the output filename ends in `.csv`,
   THE SYSTEM SHALL emit a header row plus one row per subdomain.
4. THE SYSTEM SHALL print a run summary (records found, sources queried,
   per-source errors) to stderr so stdout stays machine-consumable.

### Requirement 6: MCP server for AI agents

**User story:** As an agent user, I want the enumerator exposed as MCP
tools, so that an AI agent can run recon on my own domains from chat.

#### Acceptance Criteria

1. THE SYSTEM SHALL provide an MCP server speaking the stdio transport.
2. THE MCP server SHALL expose a tool `enumerate_subdomains` accepting a
   domain plus optional `resolve` and `check_takeover` booleans and
   returning the JSON result structure of Requirement 5.
3. THE MCP server SHALL expose a tool `check_takeover` accepting a single
   hostname and returning its takeover assessment.
4. THE MCP server SHALL expose a tool `resolve_records` accepting a single
   hostname and returning its A, AAAA, and CNAME records.
5. WHEN the `mcp` package is not installed, THE MCP server entry point
   SHALL exit with a clear installation hint instead of a traceback.

### Requirement 7: Safety, ethics, and politeness

**User story:** As a responsible researcher, I want the tool to be safe by
default, so that using it cannot accidentally become an attack.

#### Acceptance Criteria

1. THE SYSTEM SHALL perform passive enumeration only; it SHALL NOT
   include aggressive DNS brute-forcing in its default behaviour.
2. THE SYSTEM SHALL apply a bounded per-request timeout (default 30 s) to
   every passive-source query.
3. THE SYSTEM SHALL send an identifying `User-Agent` header naming the
   tool and its version.
4. THE CLI help and the MCP tool descriptions SHALL state that the tool
   must only be used on domains the user owns or is authorised to test.
5. THE repository SHALL carry an always-loaded steering document stating
   the authorised-use and rate-limit policy for any agent working on or
   with this codebase.
