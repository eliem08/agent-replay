# agent-replay

> **Loom for agents** — a walkthrough of everything your agent did.

Traces are for engineers. Your boss, your client or your future self wants
the story: *what did the agent do, in what order, why did it take 4 minutes
and where did it go wrong?* `agent-replay` turns an agent trace into a
narrated walkthrough — Markdown for PRs and docs, and a self-contained HTML
"player" you can click through step by step.

## What the MVP does

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
