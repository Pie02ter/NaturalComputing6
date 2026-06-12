# Reproducibility

This repository separates generated outputs from submitted reference outputs. New runs write to `results/` by default. The cleaned submitted outputs are tracked in `reference_results/` and can be checked with `python scripts/verify_reference_results.py`.

## Simulator Configuration

The paper experiments use the `hospital_corridor` layout in `src/crowd_evac/config.py`.

| Quantity | Value |
| --- | --- |
| Default agents | 28 high-mobility, 12 low-mobility |
| Experiment 4 mixtures | 20/20, 32/8, 8/32 high/low agents |
| High-mobility speed | 1.5 m/s |
| Low-mobility speed | 0.7 m/s |
| Simulation step | 0.1 s |
| Maximum ticks | 1000 |
| Maximum simulated duration | 100 s |
| Evacuation capture distance | 0.2 m |
| Agent body radius | 0.35 m |
| Near-collision threshold | 0.75 m |
| Congestion radius | 1.5 m |

The optimized local movement parameters are `accel_factor`, `agent_rep_weight`, and `agent_radius`. The fixed wall parameters are `wall_rep_weight=0.5` and `wall_radius=1.0`.

## Fitness and GA Settings

Default fitness weights are time `1.0`, collisions `0.05`, congestion `1.0`, fairness `2.0`, incomplete base penalty `1000.0`, and incomplete per-agent penalty `10.0`.

The default GA uses population `24`, generations `25`, elites `2`, tournament size `3`, crossover probability `0.9`, mutation probability `0.2`, and mutation sigma equal to `10%` of each parameter range. This gives `600` candidate evaluations per GA run before accounting for repeated simulation seeds.

Evaluation seeds are `11, 29, 47, 53, 61, 73, 89, 97, 101, 109`. Experiment 1 and Experiment 3 use GA seeds `101, 202, 303, 404, 505, 606, 707, 808, 909, 1001`. Experiment 2 uses GA seeds `101, 202, 303, 404, 505` for each weight pair. Experiment 4 uses fixed Experiment 1 GA seed `606` and 30 simulation seeds per population mixture.

## Motion Mechanics

Agents follow fixed navigation routing through a waypoint graph. Each agent is assigned the shortest route-aware exit target at initialization, advances waypoint cursors when within `0.5 m`, and uses a stall-recovery rule after 15 stalled ticks to skip to the nearest remaining route waypoint when useful.

The simulator applies hard agent-separation correction for the configured body radius after movement and before wall-boundary correction. This prevents persistent body overlap without changing the GA or simulation random seeds.

Low-mobility agents have additional mechanics implemented in `simulator.py`: route-target acceleration is multiplied by `1.35`, crowd-repulsion force is multiplied by `0.7`, and agents farther than `0.75 m` from their target are given a minimum forward pace of `0.12 m/s` when stalled. These mechanics are part of the submitted result-producing simulator and are scientifically relevant.

## Plot Regeneration

Experiment 2 supports cheap plot/statistics regeneration from existing CSV files with `python scripts/run_experiment2_hospital.py --recover`. Experiments 1, 3, and 4 currently regenerate plots as part of the experiment runner. Plot-only jitter uses fixed local RNG seeds and does not affect simulation or GA randomness.
