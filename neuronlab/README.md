# NeuronLab Suite

Six practical experiments for understanding, testing, and controlling open-weight language models. Built around PyTorch + Hugging Face Transformers, with GPU auto-detection, modest-model defaults, and Google Colab notebooks.

> Scientific caveat: activation interventions are experiments, not proof that a neuron has a stable human-readable meaning. Results must be compared with baselines, random controls, held-out prompts, and regressions.

## Six projects

1. **MRI — Model Internals Explorer**: capture activations, inspect selected layers, and plot token × neuron responses.
2. **Behavior Bench**: versioned regression tests for response behavior with baseline/variant comparisons.
3. **Safety Probe Lab**: run controlled prompt suites and compare behaviors; does not claim to detect intent or reliably identify deception.
4. **Experiment Scientist**: bounded agent loop that proposes and runs experiments using an explicit hypothesis template and reports evidence.
5. **Steering Studio**: experiment with activation interventions in compatible decoder-only transformer MLPs, with null/random controls.
6. **Neural Flight School**: small educational transformer with interactive-like layer/activation visualizations that works on CPU as a quickstart.

## Quickstart (local)

Python 3.10+ recommended. Use a virtual environment.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r neuronlab/requirements.txt
python -m neuronlab.cli smoke
python -m neuronlab.cli demo --project all
```

For local GPU installs, install the correct PyTorch build for your CUDA/ROCm setup using the official PyTorch selector first. The suite detects CUDA/MPS/CPU and does not require a GPU for its tiny model and smoke tests.

## Google Colab

Open `neuronlab/notebooks/NeuronLab_Quickstart.ipynb` in Colab, select **Runtime → Change runtime type → T4 GPU** if available, then run cells top to bottom. The notebook clones this branch and executes small reproducible experiments. Free Colab GPU availability and session length vary.

## Run a project

```bash
python -m neuronlab.cli run --project mri --text "A short example sentence"
python -m neuronlab.cli run --project behavior-bench
python -m neuronlab.cli run --project safety-probe
python -m neuronlab.cli run --project scientist
python -m neuronlab.cli run --project steering --text "The sky is"
python -m neuronlab.cli run --project flight-school
```

The defaults use a tiny randomly initialized GPT-2-style model for smoke/demo operation, preventing large model downloads. To use a real open-weight model, set `NEURONLAB_MODEL` to a model ID you have permission to access (for example a small openly available causal LM) and pass `--real-model`. Model downloads may require substantial disk/RAM/VRAM.

## Safety and reproducibility

- The default demo model is randomly initialized and demonstrates the workflow, not meaningful model capabilities.
- Use prompts and datasets you are allowed to process. Do not upload private data to hosted notebooks.
- Do not expose experiment endpoints to the public internet without authentication and sandboxing.
- Steering may reduce quality or change unrelated behavior. Keep baseline, intervention, random-control, and held-out results.
- This suite is a starter research toolkit, not a validated safety or interpretability benchmark.

## Project layout

```
neuronlab/
  README.md
  requirements.txt
  cli.py
  common.py
  projects/
    mri.py
    behavior_bench.py
    safety_probe.py
    scientist.py
    steering.py
    flight_school.py
  tests/
  notebooks/NeuronLab_Quickstart.ipynb
```
