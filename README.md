# NaturalComputing6

Simple heterogeneous crowd evacuation prototype with a local browser UI, GA optimization, method comparison, and experiment presets.

## Run the browser simulation

1. Start the local server:
   `python app.py`
2. Open:
   `http://127.0.0.1:5000`

The browser UI is now split into focused pages:

- `/manual` for the evacuation simulator and the 6 movement parameters
- `/ga` for GA runs, GA hyperparameters, and editable fitness weights
- `/comparison` for baseline comparison, charts, and side-by-side replay
- `/experiments` for preset-driven standard and generalization experiments

The root page `/` acts as a navigation hub.

## Browser Features

- manual simulation with replay and evacuation metrics
- editable fitness weights for time, collisions, congestion, fairness, and incomplete evacuation penalties
- GA convergence visualization and generation replay
- baseline comparison across default, two heuristics, random search, and GA
- experiment presets that can be loaded and then modified before running

## Run the terminal smoke test

`python test_run.py`

## Current scope

- Python simulation backend
- Flask local server
- Multi-page HTML/JS browser controls
- Canvas-based replay of a simulation run
- Configurable fitness weighting
- Baseline and GA experiment runner
- Basic metrics for evacuation time, near-collisions, congestion, and group fairness

## Run optimization experiments

Standard comparison:

`python experiments.py standard`

Generalization suite:

`python experiments.py generalization`

Useful overrides for quick runs:

`python experiments.py standard --population-size 8 --generations 4 --random-candidates 32 --seeds 11 29 47`

Outputs are written to `results/` by default.
