# Product Steering — Sublist3r Reborn

## What this is

Sublist3r Reborn resurrects the classic Sublist3r subdomain enumerator
(2015) as a modern, async, agent-ready recon tool. It is a **Kiroween 2026
hackathon project, category: Resurrection**.

The original tool is famous but broken in practice: it targets Python 2.7 /
3.4-era environments and scrapes search engines that no longer exist.
Reborn keeps the *idea* — fast, simple subdomain enumeration for security
researchers — and rebuilds everything around passive sources that are alive
today, DNS resolution, subdomain-takeover detection, and an MCP server so
AI agents can drive it.

## Users

- Bug-bounty hunters and pentesters doing authorised reconnaissance.
- AI agents (via MCP) assisting those humans under the ethics policy in
  `ethics-and-safety.md` — that file always wins over convenience.

## Non-negotiables

- **Clean-room implementation.** The original Sublist3r is GPL-2.0. It is a
  behavioural reference only. Never copy, port line-by-line, or paraphrase
  its source code. This project is MIT-licensed and must stay that way.
- **New project.** All code is written during the Kiroween 2026 build
  period (30 Oct – 4 Dec 2026) in this repository.
- **Passive-first.** Enumeration queries public data sources. Active
  techniques are opt-in extras, never the default path.

## Success criteria for the hackathon

- Working CLI + MCP server, installable from the repo.
- A complete, honest `/.kiro` trail: specs that match the code, steering
  that an agent actually followed, an MCP config that actually connects.
- A demo under 3 minutes showing: the original failing, the reborn tool
  enumerating a domain live via an agent, and a takeover candidate flagged.
