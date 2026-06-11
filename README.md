# Heterogeneous Hospital-Corridor Evacuation Optimization

This repository contains the reproducible Python code for the Natural Computing project paper, "Optimizing Local Movement Rules for Heterogeneous Crowd Evacuation with a Genetic Algorithm". The browser UI has been removed; the hand-in now consists only of the simulator, GA, paper experiment scripts, and documentation needed to reproduce the reported results.

## Structure

```text
scripts/                 command-line runners for the four paper experiments
src/crowd_evac/          hospital-corridor config, simulator, GA, package code
results/                 generated outputs when experiments are run
reports/                 report PDFs, if included in the hand-in
```

The core dependency direction is intentionally simple: scripts call `src/crowd_evac/`; the package does not depend on any UI code.

## Install

Use Python 3.10 or newer.

```bash
pip install -r requirements.txt
```

Optional editable install:

```bash
pip install -e .
```

## Smoke Test

Run this first to check that the hospital-corridor simulator and GA parameter expansion work:

```bash
python scripts/smoke_test.py
```

## Fast Pipeline Check

These commands use tiny GA budgets and seed counts. They are meant to verify that every experiment script runs and writes the expected CSV, JSON, and figure outputs without waiting for the full paper run.

```bash
python scripts/run_experiment1_hospital.py --quick --out results/quick_experiment1
python scripts/run_experiment2_hospital.py --quick --out results/quick_experiment2
python scripts/run_experiment3_hospital.py --quick --out results/quick_experiment3
python scripts/run_experiment4_hospital.py --quick --params-json results/quick_experiment1/runs/run_01/best_ga.json --out results/quick_experiment4
```

## Full Paper Experiments

Run the experiments below to reproduce the results and plots used in the latest paper draft. Defaults encode the reported hospital-corridor layout, 40 agents, GA settings, weights, and seeds.

Experiment 1, baseline stability and parameter variance:

```bash
python scripts/run_experiment1_hospital.py
```

Experiment 2, fitness-weight sensitivity and Pareto structure:

```bash
python scripts/run_experiment2_hospital.py
```

Experiment 3, GA hyperparameter ablation under a fixed 600-evaluation budget:

```bash
python scripts/run_experiment3_hospital.py
```

Experiment 4, population heterogeneity stress test using the Experiment 1 run with GA seed `606`:

```bash
python scripts/run_experiment4_hospital.py
```

Experiment 4 depends on `results/experiment1_baseline_stability_hospital/summary_per_run.csv` by default. If you want to use a specific parameter file instead, pass `--params-json` with a JSON containing `params`, `full_params`, or `active_params`.

## Output Files

Each experiment writes a self-contained result folder under `results/`.

Experiment 1 writes:

```text
results/experiment1_baseline_stability_hospital/
├── summary_per_run.csv
├── ga_convergence_all_runs.csv
├── aggregate_stats.json
├── ga_convergence_runs.png
├── parameter_variance_boxplot.png
└── runs/run_*/best_ga.json, ga_history.json, meta.json, evaluations_ga.csv
```

Experiment 2 writes:

```text
results/experiment2_weight_sensitivity_hospital/
├── summary_by_weights.csv
├── all_ga_seed_attempts.csv
├── aggregate_stats.json
├── pareto_time_vs_fairness.png
└── weights_*/best_ga.json, ga_history.json, best_selected.json, meta.json
```

Experiment 3 writes:

```text
results/experiment3_ga_ablation_hospital/
├── summary_per_run.csv
├── convergence_by_eval.csv
├── aggregate_stats.json
├── convergence_vs_evaluations.png
├── best_fitness_boxplot_by_config.png
└── configs/*/seed_*/best_ga.json, ga_history.json, meta.json, evaluations_ga.csv
```

Experiment 4 writes:

```text
results/experiment4_population_stress_hospital/
├── fixed_params.json
├── per_seed_results.csv
├── aggregate_stats.json
├── evacuation_time_by_scenario.png
└── fairness_gap_by_scenario.png
```

## Re-running Plots From Existing Data

Experiment 2 supports rebuilding statistics and plots without rerunning the GA sweep:

```bash
python scripts/run_experiment2_hospital.py --recover
```

The other paper scripts currently regenerate plots as part of their normal run because their plotting is directly tied to the experiment summary CSVs.

## What Is Optimized

The GA optimizes three continuous local movement parameters: acceleration factor, agent-agent repulsion weight, and agent-agent interaction radius. Wall repulsion weight and wall interaction radius are fixed in `src/crowd_evac/config.py`, matching the paper's focus on interpersonal movement rules in the hospital-corridor scenario.
