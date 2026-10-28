"""Command-line interface for the six NeuronLab projects."""
from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path

PROJECTS = {
    "mri": "neuronlab.projects.mri",
    "behavior-bench": "neuronlab.projects.behavior_bench",
    "safety-probe": "neuronlab.projects.safety_probe",
    "scientist": "neuronlab.projects.scientist",
    "steering": "neuronlab.projects.steering",
    "flight-school": "neuronlab.projects.flight_school",
}


def main(argv=None):
    parser = argparse.ArgumentParser(prog="neuronlab")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("smoke", help="Run CPU-safe software smoke tests.")
    demo = sub.add_parser("demo", help="Run one or all project demos.")
    demo.add_argument("--project", default="all", choices=["all", *PROJECTS])
    run = sub.add_parser("run", help="Run a project experiment.")
    run.add_argument("--project", required=True, choices=list(PROJECTS))
    run.add_argument("--text", default="A small model can be studied with controlled experiments.")
    run.add_argument("--real-model", action="store_true", help="Load NEURONLAB_MODEL instead of the random demo model.")
    run.add_argument("--model-id", default=None)
    args = parser.parse_args(argv)

    if args.command == "smoke":
        import pytest
        raise SystemExit(pytest.main([str(Path(__file__).parent / "tests"), "-q"]))
    selected = list(PROJECTS) if args.project == "all" else [args.project]
    if args.command == "run":
        selected = [args.project]
    summaries = []
    for name in selected:
        module = importlib.import_module(PROJECTS[name])
        result = module.run(text=getattr(args, "text", None), real_model=getattr(args, "real_model", False),
                            model_id=getattr(args, "model_id", None))
        summaries.append({"project": name, "result": result})
        print(f"\n=== {name} ===\n{json.dumps(result, indent=2, default=str)[:5000]}")
    return summaries


if __name__ == "__main__":
    main()
