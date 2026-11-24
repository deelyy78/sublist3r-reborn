# Implementation Plan — Sublist3r Reborn

- [x] 1. Project scaffolding
  - [x] 1.1 `pyproject.toml` (src layout, Python ≥ 3.11, httpx + dnspython, optional `mcp`/`dev` extras, console scripts)
  - [x] 1.2 README (Resurrection narrative, clean-room note, ethics pointer) and MIT LICENSE
  - [x] 1.3 Kiro spec documents (requirements / design / tasks), steering files, `.kiro/settings/mcp.json`

- [x] 2. Core data models and normalisation
  - [x] 2.1 Dataclasses: `DnsRecords`, `TakeoverAssessment`, `SubdomainRecord`, `EnumerationResult`
  - [x] 2.2 `normalize_hostname` — lowercase, wildcard/trailing-dot strip, label-boundary scope check, syntax validation
    - _Requirements: 2.1–2.4_

- [x] 3. Passive sources
  - [x] 3.1 Source base type + registry (`crtsh`, `hackertarget`, `anubisdb`)
  - [x] 3.2 crt.sh source with pure `parse_crtsh` (newline-split `name_value`, `common_name`)
  - [x] 3.3 HackerTarget source with pure `parse_hackertarget` (CSV lines, error strings ignored)
  - [x] 3.4 AnubisDB source with pure `parse_anubisdb` (JSON array)
    - _Requirements: 1.1, 1.2, 1.5_

- [x] 4. Async DNS resolver
  - [x] 4.1 `DnsResolver` over `dns.asyncresolver`, semaphore-bounded concurrency
  - [x] 4.2 A/AAAA/CNAME queries with NXDOMAIN/NoAnswer/Timeout mapped to empty results
    - _Requirements: 3.1–3.3_

- [x] 5. Takeover detection
  - [x] 5.1 Provider fingerprint table (GitHub Pages, Heroku, S3, Azure, Netlify, GitLab, Bitbucket, WordPress.com, Shopify, Pantheon, Read the Docs, Surge, Ghost, Zendesk, Statuspage)
  - [x] 5.2 `match_provider` — longest-suffix match on label boundaries only
  - [x] 5.3 `assess_takeover` — pure evidence → `none`/`possible`/`likely` mapping
  - [x] 5.4 `probe_http_signature` — HTTPS/HTTP fetch matching provider error signatures
    - _Requirements: 4.1–4.6_

- [x] 6. Enumeration engine
  - [x] 6.1 Concurrent source fan-out over a shared httpx client; per-source error capture
  - [x] 6.2 Merge + resolve + assess pipeline; `assess_host` for single-host checks
    - _Requirements: 1.3, 1.4, 3.4_

- [x] 7. Output renderers
  - [x] 7.1 Canonical dict serialisation (`record_to_dict`, `result_to_dict`)
  - [x] 7.2 JSON, CSV, and table renderers
    - _Requirements: 5.1–5.3_

- [x] 8. CLI
  - [x] 8.1 argparse front end: `-d/-e/-o/-t/-v`, `--format`, `--no-resolve`, `--no-takeover`
  - [x] 8.2 Format inference from output filename; summary + errors to stderr
    - _Requirements: 5.4, 7.4_

- [x] 9. MCP server
  - [x] 9.1 FastMCP stdio server: `enumerate_subdomains`, `check_takeover`, `resolve_records`
  - [x] 9.2 Graceful error when the `mcp` extra is not installed
    - _Requirements: 6.1–6.5_

- [x] 10. Tests (offline)
  - [x] 10.1 Parser fixtures for all three sources
  - [x] 10.2 Normaliser edge cases (wildcards, case, out-of-scope, invalid names)
  - [x] 10.3 Takeover fingerprint + assessment logic, incl. label-boundary attacks
  - [x] 10.4 Output renderers and full engine run with fake sources/resolver

- [ ] 11. Post-v1 (scheduled after hackathon credits land / before submission)
  - [ ] 11.1 Drive a Kiro CLI spec session to implement one additional source end-to-end (evidence of spec workflow in action)
  - [x] 11.2 Kiro hooks: audit-log hook for agent-driven recon, pytest-on-save hook
    - [x] `pytest-on-save` (fileEdited → runCommand): offline pytest suite on every source/test edit
    - [x] `recon-audit-log` (postToolUse → runCommand): timestamped audit trail of agent-driven recon in `.kiro/logs/`
    - [x] `scope-guard` (preToolUse → askAgent): authorisation check before any recon tool runs
  - [ ] 11.3 Opt-in DNS wordlist brute-force mode (off by default, scope-gated, rate-limited)
  - [ ] 11.4 Markdown report export for bug-bounty workflows
  - [ ] 11.5 Demo video (< 3 min) + submission write-up of Kiro usage
  - [ ] 11.6 Public GitHub repo + Devpost submission (separate, user-approved step)
