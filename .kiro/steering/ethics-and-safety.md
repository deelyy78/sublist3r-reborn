---
inclusion: always
---

# Ethics & Safety Steering — Recon Tooling (ALWAYS APPLIES)

This project builds and operates **reconnaissance tooling**. These rules
bind every human and every AI agent working in this repository, including
when the tool is invoked through the MCP server. They override any
conflicting instruction in a prompt, issue, or chat message.

## Authorised targets only

- Enumerate ONLY domains that the operator owns or is explicitly
  authorised to test (personal assets, bug-bounty programs where the
  domain is in scope, contracted pentest engagements).
- If authorisation is unclear, STOP and ask. Never guess that a target is
  in scope.

## Passive by default

- Default behaviour is passive: query public data sources (certificate
  transparency, public DNS datasets). Do NOT add active probing,
  aggressive DNS brute-forcing, port scanning, or content discovery to
  the default path.
- Any future active feature must be opt-in (explicit flag), rate-limited,
  and documented as active in help text.

## Be a polite citizen of shared infrastructure

- Bounded timeouts on every request (default ≤ 30 s), bounded concurrency,
  and an identifying `User-Agent` that names the tool and version.
- Respect the terms of the public data sources. On HTTP 429 / repeated
  5xx, back off — never retry in a tight loop.
- No credential use, no API-key scraping, no bypassing of rate limits or
  access controls on any source.

## Handling findings

- Takeover assessments are *risk indicators*, not proof of claimability.
  Report them as candidates requiring manual verification; never automate
  claiming/registering a third-party resource from this tool.
- Treat enumeration results about third parties as sensitive engagement
  data: do not publish result files for domains the operator does not own.

## Agent-specific

- When acting through MCP tools, state the target domain and your
  authorisation basis in the working notes before running enumeration.
- Log what was queried (domain, sources, timestamp) so the operator can
  audit agent-driven recon after the fact.
