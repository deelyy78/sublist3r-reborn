# Sublist3r Reborn 🧟

> *The legendary subdomain enumerator, dug up and rebuilt for the age of AI agents.*

**Sublist3r Reborn** is a clean-room, async reimplementation of the classic
[Sublist3r](https://github.com/aboul3la/Sublist3r) (2015) — a tool every
pentester knows, and one that has been effectively dead for years: its README
still recommends Python 2.7 and many of the search engines it scraped no
longer exist.

Built from scratch during **Kiroween 2026** (category: **Resurrection**) with
Kiro's spec-driven workflow — see the [`/.kiro`](.kiro/) directory for the
specs, steering rules, agent hooks, and MCP configuration that produced
this project.

> **Clean-room note:** the original Sublist3r is GPL-2.0. It was used purely
> as a *behavioural reference* (what the tool should do, which CLI flags
> people expect). No GPL code was copied; this project is an independent
> implementation released under the MIT license.

## The resurrection, at a glance

| | Sublist3r (2015) | Sublist3r Reborn (2026) |
| --- | --- | --- |
| Runtime | Python 2.7 / 3.4 era | Python ≥ 3.11, fully async |
| Sources | Scraped search engines — mostly dead today | crt.sh, HackerTarget, AnubisDB — alive, no API keys |
| Output | Plain list of names | Table / JSON / CSV with DNS records + per-source provenance |
| Takeover checks | None | Dangling-CNAME detection with provider fingerprints + HTTP confirmation |
| Agent use | None | MCP server — any AI agent can drive it |
| Tests | None | 36 offline pytest tests |

## What it does

- **Passive enumeration** from sources that are alive today and need no API
  keys: [crt.sh](https://crt.sh) (certificate transparency),
  [HackerTarget](https://hackertarget.com), and
  [AnubisDB](https://anubisdb.com).
- **Async DNS resolution** (A / AAAA / CNAME) with bounded concurrency.
- **Subdomain-takeover detection** — dangling CNAMEs pointing at
  takeover-prone providers (GitHub Pages, Heroku, S3, Azure, Netlify, …)
  are flagged `possible` / `likely`, with HTTP fingerprint confirmation
  where a reliable provider error signature exists.
- **MCP server** — the same engine is exposed to AI agents (Kiro, or any
  MCP client) as tools: `enumerate_subdomains`, `check_takeover`,
  `resolve_records`. Ask your agent to recon your own domain in plain
  language.
- **Output formats**: terminal table, JSON, CSV — ready to paste into a
  bug-bounty or pentest workflow.

## Install

```bash
pip install .            # core CLI
pip install ".[mcp]"     # + MCP server support
pip install ".[dev]"    # + test tooling
```

Requires Python ≥ 3.11.

## Usage

```bash
# Enumerate a domain you own / are authorized to test
sublist3r-reborn -d example.com

# Choose engines, save JSON output
sublist3r-reborn -d example.com -e crtsh,hackertarget -o results.json

# Skip DNS resolution / takeover checks
sublist3r-reborn -d example.com --no-resolve
```

| Flag | Meaning |
| --- | --- |
| `-d, --domain` | Target domain (required) |
| `-e, --engines` | Comma-separated passive sources: `crtsh`, `hackertarget`, `anubisdb` |
| `-o, --output` | Write results to a file (format inferred from extension) |
| `--format` | `table` \| `json` \| `csv` |
| `-t, --threads` | Max concurrent DNS queries (default 50) |
| `--no-resolve` | Skip DNS resolution (and takeover checks) |
| `--no-takeover` | Resolve DNS but skip takeover assessment |
| `-v, --verbose` | Show per-source errors |

## MCP server

```bash
sublist3r-reborn-mcp     # stdio transport
```

Or register it with Kiro using the shipped config in
[`.kiro/settings/mcp.json`](.kiro/settings/mcp.json).

## Built with Kiro

This project was built spec-first with Kiro (CLI), and the whole trail is
in [`/.kiro`](.kiro/) — nothing here is decorative; each artifact did work:

- **Specs** (`.kiro/specs/sublist3r-reborn/`) — EARS-format requirements,
  a design document, and a task list that was executed item by item.
  Behaviour such as *"when a passive source fails, record the error and
  continue"* was specified before it was coded, and the checked-off tasks
  map 1:1 to the modules in `src/`.
- **Steering** (`.kiro/steering/`) — `product.md` fixes the clean-room and
  passive-first rules, `tech.md` the code standards, and
  `ethics-and-safety.md` (always loaded) binds every agent session to
  authorised-targets-only recon. The ethics file is why the tool has no
  default brute-force mode.
- **Hooks** (`.kiro/hooks/`) — three agent hooks:
  - `pytest-on-save` runs the offline test suite whenever a source or
    test file is edited;
  - `recon-audit-log` appends a timestamped entry to
    `.kiro/logs/recon-audit.log` after every agent-driven recon tool
    call, so agent activity is auditable after the fact;
  - `scope-guard` makes the agent state the target domain and its
    authorisation basis *before* any recon tool runs — and stop if there
    isn't one.
- **MCP** (`.kiro/settings/mcp.json`) — registers this project's own MCP
  server with Kiro, so the agent that helped build the tool can also
  operate it: enumerate a domain, check a takeover candidate, resolve
  records, all from chat.

## Ethics

This is a reconnaissance tool. **Only run it against domains you own or are
explicitly authorized to test** (bug-bounty scope, pentest engagement, your
own assets). Enumeration here is deliberately *passive-first*: it queries
public data sources rather than hammering the target, applies polite
timeouts, and ships with no aggressive brute-forcing by default. The full
policy lives in [`.kiro/steering/ethics-and-safety.md`](.kiro/steering/ethics-and-safety.md)
and is loaded into every Kiro session that works on this repo.

## Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,mcp]"
pytest
```

## Roadmap

- [x] Passive engine (crt.sh, HackerTarget, AnubisDB)
- [x] Async resolution + takeover fingerprinting
- [x] CLI (table / JSON / CSV)
- [x] MCP server (stdio)
- [ ] Opt-in DNS wordlist brute-force (off by default, scope-gated)
- [x] Kiro hooks: pytest-on-save, audit log of agent-driven recon, pre-flight scope guard
- [ ] Markdown report export for bug-bounty workflows

## License

MIT — see [LICENSE](LICENSE). Inspired by the original Sublist3r by
Ahmed Aboul-Ela; no original code is included.
