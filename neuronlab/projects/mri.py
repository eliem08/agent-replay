"""Project 1: a compact model-internals explorer with activation summaries and plots."""
from __future__ import annotations

import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import torch

from neuronlab.common import OUTPUTS, load_model, model_forward, tensor_summary


def run(text: str | None = None, real_model: bool = False, model_id: str | None = None):
    text = text or "A short example sentence for activation inspection."
    bundle = load_model(model_id, force_real=real_model)
    batch, out = model_forward(bundle, text)
    hidden = out.hidden_states
    records = []
    matrix = []
    for i, state in enumerate(hidden):
        last = state[0, -1].detach().float().cpu()
        records.append({"layer": i, **tensor_summary(last)})
        matrix.append(last.numpy())
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.imshow(matrix, aspect="auto", interpolation="nearest")
    ax.set(title="Hidden-state activations (last input token)", xlabel="hidden dimension", ylabel="embedding / layer")
    fig.tight_layout()
    plot = OUTPUTS / "mri_activation_heatmap.png"
    fig.savefig(plot, dpi=130)
    plt.close(fig)
    report = {"model": bundle.model_id, "device": bundle.device, "text": text, "sequence_length": int(batch["input_ids"].shape[-1]),
              "layers": records, "plot": str(plot)}
    (OUTPUTS / "mri_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
