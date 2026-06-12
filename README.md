# Heterogeneous Crowd Evacuation GA

Code and stored results for the paper `Optimizing Local Movement Rules for Heterogeneous Crowd Evacuation with a Genetic Algorithm`.

## Install

```bash
python -m pip install -r requirements.txt
python -m pip install -e .
```

## Stored Results

The full results used for the paper are included in:

```text
reference_results/
  experiment1_baseline_stability_hospital/
  experiment2_weight_sensitivity_hospital/
  experiment3_ga_ablation_hospital/
  experiment4_population_stress_hospital/
```

These folders contain the CSV, JSON, figure, and per-run files needed to inspect the reported results without rerunning the full experiments.

## Reproduce Outputs

New runs write to `results/` by default.

```bash
python scripts/run_experiment1_hospital.py
python scripts/run_experiment2_hospital.py
python scripts/run_experiment3_hospital.py
python scripts/run_experiment4_hospital.py
```

The generated `results/experiment*_hospital/` folders contain the same types of tables, metadata, and figures as `reference_results/`.

For a fast code check:

```bash
python scripts/run_quick_pipeline.py
```
