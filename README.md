# Optimizing Local Movement Rules for Heterogeneous Crowd Evacuation

Command-line research code for the Natural Computing project paper, "Optimizing Local Movement Rules for Heterogeneous Crowd Evacuation with a Genetic Algorithm". The project studies a heterogeneous hospital-corridor evacuation model and optimizes local movement-rule parameters with a genetic algorithm (GA).

## Repository Structure

```text
src/crowd_evac/        simulator, configuration, and GA implementation
scripts/               smoke test, quick pipeline, experiment runners, verifier
results/               ignored runtime outputs from newly executed experiments
reference_results/     tracked cleaned outputs used for the submitted report
reports/               submitted report PDF and archived checkpoint reports
docs/                  consistency notes for code, stored results, and paper text
```

## Installation

Use Python 3.10 or newer.

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

## Smoke Test

```bash
python scripts/smoke_test.py
```

## One-Command Quick Check

This runs the smoke test and tiny versions of Experiments 1-4. Outputs are written under `results/quick_check/`.

```bash
python scripts/run_quick_pipeline.py
```

## Full Experiment Commands

Full runs are substantially slower than quick checks because the default GA evaluates 600 candidates per independent run and each candidate is averaged over multiple simulation seeds.

```bash
python scripts/run_experiment1_hospital.py
python scripts/run_experiment2_hospital.py
python scripts/run_experiment3_hospital.py
python scripts/run_experiment4_hospital.py
```

Experiment 4 uses the Experiment 1 GA seed `606` parameters by default. To use an explicit parameter JSON, pass `--params-json`.

## Results Semantics

`results/` is ignored and is only for newly generated runtime outputs. `reference_results/` is tracked and contains the cleaned outputs used for the submitted report. Do not overwrite `reference_results/` with quick-test outputs.

Verify the stored reference outputs with:

```bash
python scripts/verify_reference_results.py
```

## Method Configuration

| Component | Setting |
| --- | --- |
| Layout | `hospital_corridor` |
| Main population | 28 high-mobility, 12 low-mobility agents |
| Stress populations | 20/20, 32/8, 8/32 high/low agents |
| Speeds | high: 1.5 m/s, low: 0.7 m/s |
| Simulation | `dt=0.1`, `max_ticks=1000`, max duration 100 s |
| Optimized parameters | `accel_factor`, `agent_rep_weight`, `agent_radius` |
| Fixed parameters | `wall_rep_weight=0.5`, `wall_radius=1.0` |
| Default GA | population 24, generations 25, elites 2, tournament size 3 |
| Fitness weights | time 1.0, collisions 0.05, congestion 1.0, fairness 2.0 |

See `REPRODUCIBILITY.md` for full simulator mechanics, seeds, thresholds, waypoint routing, stall recovery, and low-mobility-specific rules.

## Generated Artifacts

Experiment 1 writes `summary_per_run.csv`, `ga_convergence_all_runs.csv`, `aggregate_stats.json`, convergence and parameter-variance plots, and per-run GA histories/evaluation logs.

Experiment 2 writes `summary_by_weights.csv`, `all_ga_seed_attempts.csv`, `aggregate_stats.json`, a time-fairness plot, and per-weight selected GA outputs.

Experiment 3 writes `summary_per_run.csv`, `convergence_by_eval.csv`, `aggregate_stats.json`, convergence and final-fitness plots, and per-configuration GA outputs.

Experiment 4 writes `fixed_params.json`, `per_seed_results.csv`, `aggregate_stats.json`, and scenario boxplots.

The submitted report is `reports/final_report.pdf`.

## Reproducibility Notes

Stored reference outputs are verified from files, while full recomputation requires the expensive experiment commands above. Known paper-text and interpretation limitations are documented in `docs/PAPER_CODE_CONSISTENCY.md`.
