"""Project 6: tiny transformer flight school — learn from an actual forward pass."""
from __future__ import annotations

import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import torch
from transformers import GPT2Config, GPT2LMHeadModel

from neuronlab.common import OUTPUTS, device_name, seed_everything, tensor_summary


def run(text: str | None = None, real_model: bool = False, model_id: str | None = None):
    seed_everything(19)
    device = device_name()
    text = text or "Neurons learn patterns"
    # Character tokenizer and tiny random weights ensure this lesson runs without a model download.
    vocab = {c: i + 1 for i, c in enumerate(sorted(set(text + " <pad>")))}
    ids = torch.tensor([[vocab[c] for c in text]], dtype=torch.long, device=device)
    config = GPT2Config(vocab_size=max(vocab.values()) + 1, n_positions=max(64, len(text) + 8),
                        n_ctx=max(64, len(text) + 8), n_embd=32, n_layer=2, n_head=2)
    model = GPT2LMHeadModel(config).to(device).eval()
    with torch.no_grad():
        out = model(input_ids=ids, output_hidden_states=True, output_attentions=True, return_dict=True)
    act = out.hidden_states[-1][0].detach().float().cpu()
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.imshow(act.numpy().T, aspect="auto", interpolation="nearest")
    ax.set(title="Tiny transformer: final block activation per character", xlabel="character position", ylabel="hidden feature")
    fig.tight_layout()
    plot = OUTPUTS / "flight_school.png"
    fig.savefig(plot, dpi=130)
    plt.close(fig)
    report = {"model": "tiny-random-gpt2-flight-school", "device": device, "text": text, "characters": list(text),
              "hidden_states": [tensor_summary(x[0]) for x in out.hidden_states],
              "attention_shapes": [list(x.shape) for x in out.attentions], "plot": str(plot),
              "caveat": "Random weights illustrate data flow only; they do not encode trained language knowledge."}
    (OUTPUTS / "flight_school.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
