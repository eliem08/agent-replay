"""Shared utilities for loading a causal LM and running small reproducible experiments."""
from __future__ import annotations

import json
import os
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch

ROOT = Path(__file__).resolve().parent
OUTPUTS = ROOT / "outputs"
OUTPUTS.mkdir(exist_ok=True)


def seed_everything(seed: int = 7) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def device_name() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


@dataclass
class ModelBundle:
    model: Any
    tokenizer: Any
    model_id: str
    device: str


def load_model(model_id: str | None = None, *, force_real: bool = False) -> ModelBundle:
    """Load the selected causal LM. Real model load is opt-in so smoke tests never download GBs."""
    from transformers import AutoModelForCausalLM, AutoTokenizer, GPT2Config, GPT2LMHeadModel

    device = device_name()
    model_id = model_id or os.getenv("NEURONLAB_MODEL", "demo-random-gpt2")
    if model_id == "demo-random-gpt2" and not force_real:
        # A small random model is deliberately used as an offline-safe software demo.
        from transformers import GPT2TokenizerFast
        try:
            tok = GPT2TokenizerFast.from_pretrained("gpt2")
        except Exception:
            # tokenizer assets are downloaded only if available. Fall back to byte-level toy tokenizer.
            tok = ByteTokenizer()
        config = GPT2Config(
            vocab_size=getattr(tok, "vocab_size", 256) or 256,
            n_positions=128,
            n_ctx=128,
            n_embd=64,
            n_layer=2,
            n_head=2,
        )
        model = GPT2LMHeadModel(config)
        model_id = "demo-random-gpt2"
    else:
        tok = AutoTokenizer.from_pretrained(model_id, use_fast=True)
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            low_cpu_mem_usage=True,
        )
    model.to(device)
    model.eval()
    if getattr(tok, "pad_token_id", None) is None and getattr(tok, "eos_token", None):
        tok.pad_token = tok.eos_token
    return ModelBundle(model, tok, model_id, device)


class ByteTokenizer:
    """Tiny deterministic fallback tokenizer requiring no network access."""
    vocab_size = 256
    eos_token = None
    pad_token_id = 0

    def __call__(self, text: str, return_tensors: str = "pt", **kwargs):
        ids = [ord(ch) % self.vocab_size for ch in text[:120]] or [0]
        if return_tensors == "pt":
            return {"input_ids": torch.tensor([ids], dtype=torch.long)}
        return {"input_ids": ids}

    def decode(self, ids, skip_special_tokens: bool = True):
        if isinstance(ids, torch.Tensor):
            ids = ids.tolist()
        return "".join(chr(int(i) % 256) for i in ids if int(i) != 0)


def model_forward(bundle: ModelBundle, text: str, *, output_hidden_states: bool = True):
    batch = bundle.tokenizer(text, return_tensors="pt")
    batch = {k: v.to(bundle.device) for k, v in batch.items() if isinstance(v, torch.Tensor)}
    with torch.no_grad():
        out = bundle.model(**batch, output_hidden_states=output_hidden_states, return_dict=True)
    return batch, out


def json_dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def tensor_summary(t: torch.Tensor) -> dict[str, Any]:
    x = t.detach().float().cpu()
    return {
        "shape": list(x.shape),
        "min": float(x.min()) if x.numel() else 0.0,
        "max": float(x.max()) if x.numel() else 0.0,
        "mean": float(x.mean()) if x.numel() else 0.0,
        "std": float(x.std()) if x.numel() > 1 else 0.0,
    }
