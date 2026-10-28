"""Project 2: reproducible behavior regression suite (works with demo or user-selected model)."""
from __future__ import annotations

import json
from neuronlab.common import OUTPUTS, load_model


PROMPTS = [
    {"id": "direct-answer", "prompt": "Answer in one sentence: what is photosynthesis?"},
    {"id": "uncertainty", "prompt": "What happened in an event that you have no information about? State uncertainty clearly."},
    {"id": "format", "prompt": "Return exactly three bullet points about keeping a software project maintainable."},
]


def generate(bundle, prompt: str, max_new_tokens: int = 48):
    import torch
    inputs = bundle.tokenizer(prompt, return_tensors="pt")
    inputs = {k: v.to(bundle.device) for k, v in inputs.items() if isinstance(v, torch.Tensor)}
    with torch.no_grad():
        tokens = bundle.model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False,
                                       pad_token_id=getattr(bundle.tokenizer, "pad_token_id", None))
    return bundle.tokenizer.decode(tokens[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True)


def run(text: str | None = None, real_model: bool = False, model_id: str | None = None):
    bundle = load_model(model_id, force_real=real_model)
    rows = []
    for item in PROMPTS:
        output = generate(bundle, item["prompt"])
        rows.append({**item, "output": output, "characters": len(output)})
    report = {"model": bundle.model_id, "device": bundle.device, "baseline": rows,
              "note": "This starter benchmark stores outputs for later diffing; scores are diagnostic, not a validated quality measure."}
    path = OUTPUTS / "behavior_bench.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return {**report, "path": str(path)}
