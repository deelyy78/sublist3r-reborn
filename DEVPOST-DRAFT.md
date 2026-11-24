# Devpost Submission Draft — Sublist3r Reborn (Kiroween 2026)

> Draft prepared 25 Nov 2026. Copy each field into the Devpost project form.
> **Submission deadline: 5 Dec 2026, 05:00 WIB** (4 Dec 14:00 PT).
> Category: **Resurrection**.

---

## Project name

Sublist3r Reborn

## Tagline (elevator pitch)

The legendary Sublist3r subdomain enumerator, resurrected as an async,
agent-ready recon tool — with takeover detection and an MCP server, built
spec-first with Kiro.

## Links (fill in before submitting)

- **GitHub repo (public, MIT):** `https://github.com/deelyy78/sublist3r-reborn`
- **Demo video (< 3 min, YouTube/Vimeo):** `<VIDEO URL>` ← placeholder — record per the script at the bottom of this draft.
- **Try it out:** `pip install git+https://github.com/deelyy78/sublist3r-reborn` (or clone + `pip install .`)

## Description (paste into "Project Description")

### Inspiration

Every pentester knows Sublist3r. The 2015 original has 11k+ GitHub stars —
and is effectively dead: its README still recommends Python 2.7, and most of
the search engines it scraped no longer exist. The *idea* (fast, simple
subdomain enumeration) is timeless; the implementation is a fossil. For
Kiroween's **Resurrection** category I rebuilt it from scratch: same spirit,
2026 internals — and one thing 2015 never imagined, an interface for AI
agents.

### What it does

Sublist3r Reborn enumerates subdomains from passive sources that are alive
today and need no API keys — crt.sh (certificate transparency), HackerTarget,
and AnubisDB — then resolves every result asynchronously (A/AAAA/CNAME) and
checks each dangling CNAME against a fingerprint table of takeover-prone
providers (GitHub Pages, Heroku, S3, Azure, Netlify, …), flagging
`possible`/`likely` subdomain-takeover candidates with HTTP signature
confirmation where a reliable provider error page exists.

The same engine is exposed three ways: a CLI with the classic flag feel
(`-d`, `-e`, `-o`, `-t`, `-v`) and table/JSON/CSV output; a Python API; and
an **MCP server** (`enumerate_subdomains`, `check_takeover`,
`resolve_records`) so Kiro — or any MCP client — can run recon on your own
domains from plain-language chat.

Enumeration is passive-first by design: it queries public data, applies
bounded timeouts and concurrency, and ships with no aggressive brute-forcing.

### How I built it

Clean-room, spec-first. The original is GPL-2.0, so it served purely as a
behavioural reference — what the tool should do and which flags people
expect. Not a line of its code was copied; Reborn is an independent MIT
implementation in modern async Python (httpx + dnspython), with pure,
fixture-tested parsers per source and a 36-test offline pytest suite.

Kiro drove the whole build (see the next section): requirements in EARS
format, a design doc, and a task list executed item by item, so every
module in `src/` traces back to a checked-off spec task.

### How Kiro helped

Kiro wasn't autocomplete here — it was the workshop. The full trail ships
in the repo's `/.kiro` directory:

- **Specs** (`.kiro/specs/sublist3r-reborn/`): EARS requirements ("WHEN a
  passive source times out, THE SYSTEM SHALL record the failure and
  continue with the remaining sources"), design, and tasks. Writing the
  failure-isolation requirement *before* code is why one dead source never
  sinks a run.
- **Steering** (`.kiro/steering/`): product rules (clean-room,
  passive-first), tech standards, and an always-loaded ethics file that
  binds every agent session to authorised-targets-only recon. The ethics
  steering is a feature, not paperwork: it is the reason the tool has no
  default brute-force mode.
- **Hooks** (`.kiro/hooks/`): `pytest-on-save` runs the test suite on
  every source/test edit; `recon-audit-log` keeps a timestamped audit
  trail of agent-driven recon; `scope-guard` forces the agent to state
  the target and its authorisation basis before any recon tool runs.
- **MCP** (`.kiro/settings/mcp.json`): registers the project's own MCP
  server with Kiro — the agent that helped build the tool can operate it.

### Challenges

- **crt.sh is flaky** under load; the spec's failure-isolation requirement
  plus per-source error reporting turned that into a non-event.
- **Takeover detection precision:** naive substring matching flags
  `evilgithub.io` as GitHub Pages. The fingerprint matcher works on DNS
  label boundaries only, with dedicated tests for exactly that attack.
- **Staying clean-room** while matching beloved CLI behaviour: every
  behaviour had to be re-derived from public documentation, never from
  the GPL source.

### Accomplishments I'm proud of

- A dead classic is a working, tested, installable tool again — and it
  found a second life as an agent tool, not just a CLI.
- Safety is enforced by the development environment itself: steering +
  a pre-flight scope-guard hook, not just a README warning.
- 36 offline tests; the whole pipeline (sources → normalise → resolve →
  assess → render) is testable without touching the network.

### What I learned

Spec-driven development pays off most where behaviour must *not* happen:
failure isolation, scope invariants, label-boundary matching. Writing
those as requirements first made the agent's implementation right the
first time. I also learned that an MCP server is the difference between
"a tool an agent can describe" and "a tool an agent can use."

### What's next

- Opt-in, scope-gated DNS wordlist mode (off by default, rate-limited).
- Markdown report export tailored to bug-bounty workflows.
- More passive sources, added the same way the first three were: spec →
  tasks → implementation → tests.

## Built with

python · asyncio · httpx · dnspython · mcp (model context protocol) ·
kiro · pytest · crt.sh · hackertarget · anubisdb

---

## Demo video script (< 3 min)

1. **0:00** — The original Sublist3r: Python 2.7 README, dead engines. It doesn't run.
2. **0:30** — Kiro CLI: "Enumerate subdomains of my test domain and check takeover risk."
3. **1:00** — The agent calls the MCP tools live; results stream in with sources + DNS.
4. **1:45** — One dangling CNAME flagged `likely` takeover; show the record and reason.
5. **2:20** — Tour `/.kiro`: spec, ethics steering, the three hooks, MCP config.
6. **2:50** — Close: "Same tool. Now any agent can drive it — safely."

## Submission checklist

- [x] Working app: CLI + MCP server, 36/36 tests passing
- [x] `/.kiro` at repo root: specs, steering, hooks, MCP settings
- [x] MIT LICENSE in repo (detected by GitHub About)
- [ ] **Public GitHub repo + push** ← user step (needs user's GitHub login/approval)
- [ ] **Demo video < 3 min recorded + uploaded** ← user step
- [ ] **Didit identity verification on Devpost** ← user-only step
- [ ] Paste this draft into the Devpost project form, select **Resurrection**, submit **before 5 Dec 2026 05:00 WIB**
- [ ] Redeem the 4,000 Kiro credits by **4 Dec 2026** (credits expire 31 Dec 2026)
- [ ] Optional stretch (task 11.1): one Kiro CLI spec session adding a 4th source end-to-end, as extra "Kiro in action" evidence
