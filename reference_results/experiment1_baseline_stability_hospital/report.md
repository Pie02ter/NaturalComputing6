# Experiment 1: Baseline Stability (Hospital Corridor)

## Setup
- Layout: `hospital_corridor`
- Max ticks: `1000`
- Simulation seeds per fitness evaluation: `[11, 29, 47, 53, 61, 73, 89, 97, 101, 109]`
- Independent GA seeds: `[101, 202, 303, 404, 505, 606, 707, 808, 909, 1001]`
- Fitness weights: time=1, collisions=0.05, congestion=1, fairness=2

## Core outcomes
- Best fitness mean +- std: 56.959355 +- 12.006383
- accel_factor mean +- std: 3.664841 +- 0.578087
- agent_rep_weight mean +- std: 3.819327 +- 1.107123
- agent_radius mean +- std: 1.017910 +- 0.381151
- mean_time mean +- std: 30.901000 +- 0.978803
- mean_collisions mean +- std: 134.020000 +- 266.372020
- mean_fairness_gap mean +- std: 8.774964 +- 0.337560

## Inferential statistics
- Bootstrap 95% CI best_fitness(mean): [52.833938, 64.720358]
- Bootstrap 95% CI best_fitness(std): [0.501340, 18.436215]
- Mann-Kendall trend on mean convergence curve: S=-298, Z=-6.9402, p=3.91509e-12
- Exact sign test (generation 0 -> final improvement): 10/10 improved, p=0.00195312

## Figures
- Parameter variance boxplot: `parameter_variance_boxplot.pdf`
- GA convergence: `ga_convergence_runs.pdf`
- Best fitness histogram: `best_fitness_histogram.pdf`

## Per-run best points

- Run 01 (seed=101): fitness=54.443579, accel=3.05013, rep=4.02554, rad=0.88507, time=32.30000, collisions=34.00000, fairness_gap=9.35607
- Run 02 (seed=202): fitness=52.864822, accel=4.04637, rep=5.00000, rad=0.88353, time=30.62000, collisions=48.50000, fairness_gap=8.97929
- Run 03 (seed=303): fitness=52.909119, accel=3.20099, rep=3.81999, rad=0.88614, time=31.46000, collisions=51.60000, fairness_gap=8.53393
- Run 04 (seed=404): fitness=52.441703, accel=3.14010, rep=3.94752, rad=0.87844, time=30.93000, collisions=47.00000, fairness_gap=8.68345
- Run 05 (seed=505): fitness=52.889188, accel=4.15429, rep=4.50711, rad=0.89418, time=30.49000, collisions=63.90000, fairness_gap=8.67714
- Run 06 (seed=606): fitness=52.279248, accel=3.74307, rep=4.36611, rad=0.92450, time=30.91000, collisions=38.00000, fairness_gap=8.79821
- Run 07 (seed=707): fitness=53.805955, accel=3.35534, rep=3.65683, rad=0.92624, time=31.28000, collisions=57.60000, fairness_gap=8.89810
- Run 08 (seed=808): fitness=52.690988, accel=3.81665, rep=4.23781, rad=0.90267, time=30.58000, collisions=57.50000, fairness_gap=8.69560
- Run 09 (seed=909): fitness=91.065696, accel=4.87686, rep=0.88683, rad=2.10167, time=28.65000, collisions=891.70000, fairness_gap=8.08488
- Run 10 (seed=1001): fitness=54.203248, accel=3.26461, rep=3.74552, rad=0.89666, time=31.79000, collisions=50.40000, fairness_gap=9.04298
