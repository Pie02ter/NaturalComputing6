#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_step(label, args):
    print(f"\n[{label}] {' '.join(args)}")
    result = subprocess.run(args, cwd=ROOT)
    return {"label": label, "args": args, "returncode": result.returncode}


def main():
    python = sys.executable
    steps = [
        ("smoke", [python, "scripts/smoke_test.py"]),
        ("experiment1", [python, "scripts/run_experiment1_hospital.py", "--quick", "--out", "results/quick_check/experiment1"]),
        ("experiment2", [python, "scripts/run_experiment2_hospital.py", "--quick", "--out", "results/quick_check/experiment2"]),
        ("experiment3", [python, "scripts/run_experiment3_hospital.py", "--quick", "--out", "results/quick_check/experiment3"]),
        (
            "experiment4",
            [
                python,
                "scripts/run_experiment4_hospital.py",
                "--quick",
                "--params-json",
                "results/quick_check/experiment1/runs/run_01/best_ga.json",
                "--out",
                "results/quick_check/experiment4",
            ],
        ),
    ]

    results = []
    for label, args in steps:
        outcome = run_step(label, args)
        results.append(outcome)
        if outcome["returncode"] != 0:
            break

    print("\nQuick pipeline summary:")
    for outcome in results:
        status = "PASS" if outcome["returncode"] == 0 else "FAIL"
        print(f"- {outcome['label']}: {status}")

    if len(results) != len(steps) or any(item["returncode"] != 0 for item in results):
        print("Quick pipeline failed.")
        return 1

    print("Quick pipeline passed. Outputs are under results/quick_check/.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
