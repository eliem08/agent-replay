"""Turn agent traces into narrated walkthroughs (Markdown / HTML player)."""
from __future__ import annotations

import html
import json

__all__ = ["load_spans", "build_steps", "narrate", "summary", "to_markdown", "to_html"]


def load_spans(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        text = fh.read().strip()
    if text.startswith("["):
        steps = json.loads(text)
        t = 0.0
        spans = []
        for i, s in enumerate(steps):
            dur = s.get("duration_ms", 0)
            spans.append({"span_id": str(i), "parent_id": None, "name": s["name"], "kind": s.get("kind", "step"),
                          "start": t, "duration_ms": dur, "attrs": s.get("attrs", {}), "status": s.get("status", "ok"),
                          "error": s.get("error")})
            t += dur / 1000
        return spans
    return [json.loads(l) for l in text.splitlines() if l.strip()]


def build_steps(spans: list[dict]) -> tuple[dict | None, list[dict]]:
    """Return (root agent span or None, ordered list of steps with depth)."""
    by_parent: dict = {}
    for s in spans:
        by_parent.setdefault(s.get("parent_id"), []).append(s)
    for v in by_parent.values():
        v.sort(key=lambda s: s["start"])
    roots = by_parent.get(None, [])
    root = roots[0] if len(roots) == 1 and roots[0]["kind"] == "agent" else None
    t0 = min(s["start"] for s in spans) if spans else 0
    steps = []

    def walk(parent_id, depth):
        for s in by_parent.get(parent_id, []):
            steps.append({**s, "depth": depth, "offset_s": round(s["start"] - t0, 2)})
            walk(s["span_id"], depth + 1)

    walk(root["span_id"] if root else None, 0)
    names = [s["name"] for s in steps]
    for i, s in enumerate(steps):
        s["retry"] = i > 0 and names[i - 1] == s["name"] and steps[i - 1]["status"] == "error"
    return root, steps


def narrate(s: dict) -> str:
    a = s.get("attrs", {})
    k = s["kind"]
    if k == "llm":
        tokens = ""
        if a.get("input_tokens"):
            tokens = f" ({a['input_tokens']:,} tokens in, {a.get('output_tokens', 0):,} out)"
        text = f"Asked {a.get('model', 'the model')} to **{s['name']}**{tokens}."
    elif k == "tool":
        args = ", ".join(f"{key}=`{v}`" for key, v in a.items() if key not in {"cost_usd"})
        text = f"Called tool `{s['name']}`" + (f" with {args}" if args else "") + "."
    elif k == "retrieval":
        text = f"Looked up context: {s['name']}."
    else:
        text = f"Step: {s['name']}."
    if s.get("retry"):
        text = "Retried. " + text
    if s.get("status") == "error":
        text += f" **Failed** - {s.get('error', 'unknown error')}."
    return text


def summary(root: dict | None, steps: list[dict]) -> dict:
    total_ms = root["duration_ms"] if root else sum(s.get("duration_ms", 0) for s in steps if s["depth"] == 0)
    cost = sum(s.get("attrs", {}).get("cost_usd", 0) or 0 for s in steps)
    errors = [s for s in steps if s.get("status") == "error"]
    slowest = max(steps, key=lambda s: s.get("duration_ms", 0)) if steps else None
    priciest = max(steps, key=lambda s: s.get("attrs", {}).get("cost_usd", 0) or 0) if steps else None
    final_failed = bool(steps) and steps[-1].get("status") == "error"
    return {"goal": (root or {}).get("attrs", {}).get("input", ""), "steps": len(steps), "seconds": round(total_ms / 1000, 1),
            "cost_usd": round(cost, 4), "errors": len(errors), "recovered": bool(errors) and not final_failed,
            "slowest": slowest and (slowest["name"], slowest.get("duration_ms", 0)),
            "priciest": priciest and (priciest["name"], priciest.get("attrs", {}).get("cost_usd", 0))}


def to_markdown(spans: list[dict]) -> str:
    root, steps = build_steps(spans)
    sm = summary(root, steps)
    out = [f"# Agent walkthrough: {root['name'] if root else 'run'}", ""]
    if sm["goal"]:
        out.append(f"> **Goal:** {sm['goal']}")
        out.append("")
    outcome = "completed" + (" after recovering from errors" if sm["recovered"] else "") if not (sm["errors"] and not sm["recovered"]) else "failed"
    out.append(f"**TL;DR** - {sm['steps']} steps in {sm['seconds']}s, ${sm['cost_usd']:.4f}, {outcome}.")
    if sm["slowest"]:
        out.append(f"Slowest step: `{sm['slowest'][0]}` ({sm['slowest'][1] / 1000:.1f}s). "
                   f"Most expensive: `{sm['priciest'][0]}` (${sm['priciest'][1]:.4f}).")
    out.append("")
    for i, s in enumerate(steps, 1):
        indent = "  " * s["depth"]
        badge = " (error)" if s.get("status") == "error" else ""
        out.append(f"{indent}{i}. **[{s['offset_s']:>6.2f}s]** {narrate(s)} _{s.get('duration_ms', 0) / 1000:.1f}s_{badge}")
    return "\n".join(out) + "\n"


def to_html(spans: list[dict]) -> str:
    root, steps = build_steps(spans)
    sm = summary(root, steps)
    cards = []
    for i, s in enumerate(steps, 1):
        err = s.get("status") == "error"
        body = html.escape(narrate(s)).replace("**", "")
        cards.append(f'<section class="step{" err" if err else ""}" data-i="{i - 1}"><div class="meta">Step {i} of {len(steps)} &middot; '
                     f'+{s["offset_s"]:.2f}s &middot; {s.get("duration_ms", 0) / 1000:.1f}s &middot; {html.escape(s["kind"])}</div>'
                     f'<h2>{html.escape(s["name"])}</h2><p>{body}</p></section>')
    title = html.escape(root["name"] if root else "Agent run")
    goal = html.escape(sm["goal"])
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} replay</title><style>
:root{{--bg:#fafaf9;--fg:#1c1917;--muted:#78716c;--card:#fff;--err:#b91c1c;--accent:#4f46e5}}
@media (prefers-color-scheme:dark){{:root{{--bg:#1c1917;--fg:#f5f5f4;--muted:#a8a29e;--card:#292524;--err:#f87171;--accent:#a5b4fc}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:16px/1.5 system-ui,sans-serif}}main{{max-width:720px;margin:0 auto;padding:24px 16px}}
.step{{display:none;background:var(--card);border-radius:12px;padding:20px;border-left:4px solid var(--accent)}}.step.on{{display:block}}
.step.err{{border-left-color:var(--err)}}.meta{{color:var(--muted);font-size:13px}}nav{{display:flex;gap:8px;margin:16px 0}}
button{{padding:8px 16px;border-radius:8px;border:1px solid var(--muted);background:var(--card);color:var(--fg);cursor:pointer}}
.bar{{height:4px;background:var(--muted);border-radius:2px;overflow:hidden}}.bar i{{display:block;height:100%;background:var(--accent);width:0}}
</style></head><body><main><h1>{title}</h1><p class="meta">{goal}</p>
<p>{sm['steps']} steps &middot; {sm['seconds']}s &middot; ${sm['cost_usd']:.4f} &middot; {sm['errors']} error(s)</p>
<div class="bar"><i id="bar"></i></div><nav><button id="prev">&larr; Prev</button><button id="next">Next &rarr;</button></nav>
{''.join(cards)}</main><script>
const s=[...document.querySelectorAll('.step')];let i=0;const bar=document.getElementById('bar');
function show(n){{i=Math.max(0,Math.min(s.length-1,n));s.forEach((e,k)=>e.classList.toggle('on',k===i));bar.style.width=((i+1)/s.length*100)+'%';}}
document.getElementById('prev').onclick=()=>show(i-1);document.getElementById('next').onclick=()=>show(i+1);
document.addEventListener('keydown',e=>{{if(e.key==='ArrowRight')show(i+1);if(e.key==='ArrowLeft')show(i-1);}});show(0);
</script></body></html>"""
