# Heterogeneous Crowd Evacuation Optimization

This project studies whether a real-coded genetic algorithm can tune local movement-rule parameters for a heterogeneous crowd evacuation model. The core code is independent from the browser interface: scripts and the WebUI both call the same `src/crowd_evac` package.

## Repository Structure

```text
configs/                 JSON experiment configurations
scripts/                 command-line entry points
src/crowd_evac/          simulator, fitness, baselines, GA, experiments, visualization
webapp/                  optional Flask UI for interactive exploration
results/                 generated experiment outputs
reports/                 optional report figures/PDFs
```

The code-only hand-in can exclude `webapp/`, `results/`, and `reports/` unless generated artifacts are requested.

## Installation

Install dependencies from the project root:

```bash
pip install -r requirements.txt
```

Optional editable install:

```bash
pip install -e .
```

## Run The Main Experiment

The first formal experiment compares the fixed default, two heuristics, 600-sample random search, and a GA with population 24 for 25 generations. It uses the standard room, 30 high-mobility agents, 10 low-mobility agents, and seeds `[11, 29, 47]`.

```bash
python scripts/run_experiment.py --config configs/standard_baseline.json --out results/standard_baseline --make-plots --make-animations
```

For a fast sanity check:

```bash
python scripts/run_experiment.py --config configs/quick_debug.json --out results/quick_debug --make-plots --quick
```

## Output Format

Each standardized run writes:

```text
results/<run_name>/
├── config.json
├── best_runs.json             original full run summary
├── evaluations.csv            all candidate evaluations
├── summary.csv                compact method comparison
├── summary.json               compact machine-readable summary
├── ga_convergence.csv
├── plots/
│   ├── fitness_comparison.png
│   ├── metric_breakdown.png
│   ├── ga_convergence.png
│   ├── efficiency_fairness_tradeoff.png
│   └── parameter_comparison.png
└── animations/
    ├── default.gif
    ├── heuristic_1.gif
    ├── heuristic_2.gif
    ├── random_search.gif
    ├── ga.gif
    └── method_comparison.gif
```

Plots and animations can be regenerated without rerunning the optimization:

```bash
python scripts/make_plots.py results/standard_baseline
python scripts/make_animations.py results/standard_baseline --seed 11
```

## Experiment Configs

Use JSON files in `configs/` to define reproducible experiments.

Available configs:

- `standard_baseline.json`: main first experiment for the report.
- `quick_debug.json`: tiny run for testing the pipeline.
- `generalization.json`: train on standard setup and evaluate best parameters on extra layouts/densities.
- `fairness_ablation.json`: standardized replacement for the old checkpoint fairness/no-fairness idea; change `fitness_weights.fairness` and rerun into separate result folders.

## WebUI

The WebUI is only for interactive exploration. It is not required for the code hand-in.

Start it with:

```bash
python webapp/app.py
```

Then open:

```text
http://127.0.0.1:5000
```

Pages:

- `/manual`: run one simulation with chosen parameters.
- `/ga`: run a GA interactively.
- `/comparison`: compare default, heuristics, random search, and GA.
- `/experiments`: run preset-style standard/generalization experiments from the browser.

The old checkpoint page was removed. Its useful role is covered by standardized configs and visualization scripts.

## Smoke Test

```bash
python scripts/smoke_test.py
```

This checks that the default GA genome expands to the default full parameter vector and that the simulator completes a default evacuation.

## Extending The Project

To add a new experiment:

1. Add a JSON file in `configs/`.
2. Run it with `scripts/run_experiment.py`.
3. Reuse `scripts/make_plots.py` and `scripts/make_animations.py` for standardized figures.
4. If a new experiment type needs custom orchestration, add it under `src/crowd_evac/experiments.py`, not in the WebUI.

The intended dependency direction is:

```text
scripts/  ─────┐
               ├──> src/crowd_evac/
webapp/   ─────┘
```

`src/crowd_evac/` should never import from `webapp/`.
