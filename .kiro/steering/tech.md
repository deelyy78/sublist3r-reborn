# Tech Steering — Sublist3r Reborn

## Stack

- Python ≥ 3.11, `src/` layout, packaged with hatchling (`pyproject.toml`).
- Async everywhere on the network path: `asyncio` + `httpx` for HTTP,
  `dnspython` (`dns.asyncresolver`) for DNS.
- MCP server on the official `mcp` Python SDK (`FastMCP`, stdio), kept as
  an optional dependency extra so the core CLI stays light.
- Tests: `pytest`, fully offline. Network behaviour is verified by manual
  smoke tests, never by the test suite.

## Code standards

- Type hints on all public functions; dataclasses for data crossing
  module boundaries.
- Pure functions wherever parsing or decision logic is involved
  (`parse_*`, `normalize_hostname`, `assess_takeover`) — side effects live
  at the edges (sources, resolver, engine, CLI, MCP server).
- Every network operation has an explicit timeout and a failure mode that
  degrades to data (an error entry or an empty result), never to an
  unhandled exception escaping the engine.
- Concurrency is always bounded by a semaphore or an explicit limit.
- No new runtime dependency without a strong reason; the standard library
  wins ties.
- Commits: small, imperative, conventional prefixes (`feat:`, `fix:`,
  `chore:`, `docs:`, `test:`).

## Clean-room rule (binding)

The original Sublist3r is GPL-2.0. When behaviour is unclear, infer the
*requirement* from public documentation of what the tool does, then design
and write original code. Do not fetch, open, or reproduce the original
source files in this repository's workflow.
