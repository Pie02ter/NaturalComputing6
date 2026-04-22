# NaturalComputing6

Simple heterogeneous crowd evacuation prototype with a local browser UI.

## Run the browser simulation

1. Start the local server:
   `python app.py`
2. Open:
   `http://127.0.0.1:5000`

The browser UI now supports both:

- manual simulation runs with sliders
- GA runs with in-browser convergence visualization
- replay of the best evolved simulation
- replay of any selected generation champion
- method comparison charts for default, heuristics, random search, and GA
- side-by-side replay of default versus GA best
- per-generation GA champion table

## Run the terminal smoke test

`python test_run.py`

## Current scope

- Python simulation backend
- Flask local server
- Plain HTML/JS browser controls
- Canvas-based replay of a simulation run
- Basic metrics for evacuation time, near-collisions, congestion, and group fairness

## Run optimization experiments

Standard comparison:

`python experiments.py standard`

Generalization suite:

`python experiments.py generalization`

Useful overrides for quick runs:

`python experiments.py standard --population-size 8 --generations 4 --random-candidates 32 --seeds 11 29 47`

Outputs are written to `results/` by default.
