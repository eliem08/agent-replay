"""Project 5: controlled residual-stream steering prototype for GPT-2-style decoder blocks."""
from __future__ import annotations

import json
from neuronlab.common import OUTPUTS, load_model


def _generate(bundle, prompt, intervention=None, max_new_tokens=32):
    import torch
    model = bundle.model
    inputs = bundle.tokenizer(prompt, return_tensors="pt")
    inputs = {k: v.to(bundle.device) for k, v in inputs.items() if isinstance(v, torch.Tensor)}
    handle = None
    if intervention:
        layer_index, scale = intervention
        # GPT-2 transformer blocks expose a residual output. Other architectures require adapter-specific hooks.
        blocks = getattr(getattr(model, "transformer", None), "h", None)
        if blocks is None or layer_index >= len(blocks):
            raise ValueError("This first steering adapter supports GPT-2-style model.transformer.h blocks only.")
        def hook(_module, _inputs, output):
            if isinstance(output, tuple):
                hidden = output[0]
                delta = torch.zeros_like(hidden)
                delta[..., 0] = scale
                return (hidden + delta, *output[1:])
            delta = torch.zeros_like(output)
            delta[..., 0] = scale
            return output + delta
        handle = blocks[layer_index].register_forward_hook(hook)
    try:
        with torch.no_grad():
            tokens = model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False,
                                    pad_token_id=getattr(bundle.tokenizer, "pad_token_id", None))
        return bundle.tokenizer.decode(tokens[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True)
    finally:
        if handle is not None:
            handle.remove()


def run(text: str | None = None, real_model: bool = False, model_id: str | None = None):
    bundle = load_model(model_id, force_real=real_model)
    prompt = text or "The sky is"
    baseline = _generate(bundle, prompt)
    controls = []
    layer_count = len(getattr(getattr(bundle.model, "transformer", None), "h", []))
    if layer_count:
        layer = max(0, layer_count // 2)
        for scale in (-0.5, 0.5, 1.0):
            controls.append({"scale": scale, "output": _generate(bundle, prompt, (layer, scale))})
        controls.append({"scale": 0.5, "control": "random-dimension", "output": _generate_random_control(bundle, prompt, layer)})
    report = {"model": bundle.model_id, "device": bundle.device, "prompt": prompt, "baseline": baseline,
              "interventions": controls,
              "note": "This is a residual-dimension demo, not neuron-specific steering. Magnitudes are uncalibrated; compare held-out prompts and task metrics."}
    path = OUTPUTS / "steering_studio.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return {**report, "path": str(path)}


def _generate_random_control(bundle, prompt, layer):
    import torch
    # The control modifies a different residual dimension than the main intervention.
    model = bundle.model
    inputs = bundle.tokenizer(prompt, return_tensors="pt")
    inputs = {k: v.to(bundle.device) for k, v in inputs.items() if isinstance(v, torch.Tensor)}
    blocks = model.transformer.h
    def hook(_module, _inputs, output):
        dim = min(1, output[0].shape[-1] - 1) if isinstance(output, tuple) else min(1, output.shape[-1] - 1)
        if isinstance(output, tuple):
            h = output[0].clone()
            h[..., dim] += 0.5
            return (h, *output[1:])
        h = output.clone()
        h[..., dim] += 0.5
        return h
    handle = blocks[layer].register_forward_hook(hook)
    try:
        with torch.no_grad():
            tokens = model.generate(**inputs, max_new_tokens=32, do_sample=False,
                                    pad_token_id=getattr(bundle.tokenizer, "pad_token_id", None))
        return bundle.tokenizer.decode(tokens[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True)
    finally:
        handle.remove()
