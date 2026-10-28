"""Project 4: a bounded experiment planner and runner with transparent hypotheses."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from neuronlab.common import OUTPUTS, load_model
from neuronlab.projects.behavior_bench import generate


def run(text: str | None = None, real_model: bool = False, model_id: str | None = None):
    bundle = load_model(model_id, force_real=real_model)
    question = text or "Does asking for concise answers reduce response length without changing the answer?"
    # The initial scientist is deliberately deterministic and bounded; no hidden autonomous shell or network access.
    prompt = "Answer the question below in a short, testable hypothesis with a measurable outcome. Do not claim it is proven.\nQuestion: " + question
    hypothesis = generate(bundle, prompt, max_new_tokens=60)
    experiments = [
        {"condition": "baseline", "instruction": "Answer the question directly: " + question},
        {"condition": "concise", "instruction": "Answer in at most two sentences: " + question},
        {"condition": "random-control", "instruction": "Please consider this unrelated phrase, then answer: violet bicycle copper. " + question},
    ]
    results = []
    for item in experiments:
        output = generate(bundle, item["instruction"], max_new_tokens=48)
        results.append({**item, "output": output, "output_chars": len(output)})
    report = {"created_at": datetime.now(timezone.utc).isoformat(), "model": bundle.model_id, "device": bundle.device,
              "question": question, "candidate_hypothesis": hypothesis, "experiments": results,
              "interpretation": "Exploratory only. Review outputs and predefine metrics before drawing conclusions; a small demo model may be random."}
    path = OUTPUTS / "scientist_experiment.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return {**report, "path": str(path)}
