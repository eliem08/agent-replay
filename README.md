<!-- sell-kit:start -->
# Agent Replay

[![CI](https://github.com/eliem08/agent-replay/actions/workflows/ci.yml/badge.svg)](https://github.com/eliem08/agent-replay/actions/workflows/ci.yml)

> **A shareable walkthrough of everything your agent did.**

**Who it's for:** Teams who need to show stakeholders or customers what an agent did and why.

**The problem:** Agent traces are unreadable JSON, so nobody outside engineering can review an agent's work.

**What you get:** Turn a trace into a narrated Markdown report and a single-file HTML player you can send to anyone.

## Quickstart

Customers receive a release archive with the wheel and the examples. Python 3.10+ and no other dependencies.

```bash
pip install agent_replay-0.1.0-py3-none-any.whl
agent-replay md examples/trace.jsonl
agent-replay html examples/trace.jsonl -o replay.html
```

## Web app and API

Every command is also a JSON API endpoint and a browser form, served by the built-in web app.

```bash
agent-replay-web --port 8000          # then open http://127.0.0.1:8000
docker build -t agent-replay . && docker run -p 8000:8000 -v agent-replay-data:/data agent-replay
```

Endpoints: `POST /api/md`, `POST /api/html`, plus `GET /healthz` and `GET /api/spec` (machine-readable field list).
Files are sent as `{"name": ..., "content": ...}`, folders as `{"files": [...]}` or a base64 zip.

## Pricing

Every plan starts with a 14-day free trial. Prices in USD, billed monthly unless noted.

| Plan | Price | Includes |
|---|---|---|
| **Solo** | $12 per month | Unlimited replays; Markdown and HTML player |
| **Team** | $59 per month | 10 seats; Branded players; Redaction controls |
| **Business** | $249 per month | Unlimited seats; Customer-facing replays; Priority support |

To start a trial or buy a plan, email **sales@YOUR-DOMAIN.com**.

## Licence

Proprietary. Copyright (c) 2026 eliem08. All rights reserved. Use requires a paid plan or an active trial; see [LICENSE](LICENSE).
<!-- sell-kit:end -->

## What it does

- Reads **agent-tracer JSONL** spans (or a simple `steps.json` list)
- Builds chapters from top-level steps, nests sub-steps, computes time offsets
- Narrates each step in plain English from its kind and attributes
  ("Called tool `web_search` with query …", "Asked claude-sonnet (1.2k tokens in) …")
- **Highlights**: errors, slowest step, most expensive step, retries
- **TL;DR** summary at the top: steps, duration, cost, outcome
- Outputs **Markdown** or a **single-file HTML player** (prev/next, keyboard arrows,
  progress bar; no external assets)

## Quickstart

```bash
pip install -e .
agent-replay md examples/trace.jsonl > walkthrough.md
agent-replay html examples/trace.jsonl -o replay.html
```

## Roadmap

- Screenshot / DOM snapshots for browser agents embedded per step
- Voice-over narration (TTS) exported as video
- Share links with redaction of secrets and PII

## Development

Zero runtime dependencies; Python 3.10+.

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
python -m unittest discover -s tests -t .           # unit + CLI smoke tests
ruff check . && ruff format --check .               # lint + format
```

```
agent_replay/core.py       domain logic (pure, importable, fully tested)
agent_replay/__main__.py   CLI (`agent-replay ...` / `python -m agent_replay ...`)
tests/                unit tests + generated CLI smoke tests
examples/             sample inputs used by the docs and smoke tests
```

CI runs lint and tests on Ubuntu and Windows across Python 3.10, 3.12 and 3.13.
Design, data model, trade-offs and production path: **[ARCHITECTURE.md](ARCHITECTURE.md)**.

Part of the [agent-economy](https://github.com/eliem08/agent-economy) portfolio (idea #31).
