# Experiment 4: Population Heterogeneity Stress Test

## Setup
- Layout: `hospital_corridor`
- Total agents per scenario: **40**
- Simulation seeds per scenario: **30**
- Mode: fixed-parameter evaluation only (no GA)

## Fixed parameters (from Experiment 1 best GA run)
- Source: `reference_results/experiment1_baseline_stability_hospital/summary_per_run.csv`
- Selected Exp 1 run: 6 (seed=606, fitness=52.279248)
- accel_factor: `3.743072`
- agent_rep_weight: `4.366114`
- agent_radius: `0.924495`

## Population scenarios
- Default: 20 high / 20 low (50% / 50%)
- High-mobility dominant: 32 high / 8 low (80% / 20%)
- Low-mobility dominant (ICU-like): 8 high / 32 low (20% / 80%)

## Summary statistics

| Scenario | median time (s) | IQR time | median fairness gap (s) | IQR gap | all evacuated |
|----------|-----------------|----------|-------------------------|---------|---------------|
| Default (50% high / 50% low) | 39.3500 | 7.3750 | 12.0150 | 4.8212 | 100.00% |
| High-mobility dominant (80% / 20%) | 30.9000 | 4.5500 | 10.6188 | 2.6422 | 96.67% |
| Low-mobility dominant / ICU-like (20% / 80%) | 46.6500 | 5.0250 | 11.7281 | 6.5133 | 100.00% |

## Statistical tests (across scenarios)
- Kruskal-Wallis on total_time: H=50.4769, p=1.09413e-11
- Kruskal-Wallis on fairness_gap: H=2.8373, p=0.242039

## Interpretation (for report)
- Parameters optimized under Exp 1 conditions are stress-tested on unseen population mixes.
- Wider fairness-gap boxes under low-mobility dominance indicate reduced equity robustness.
- Compare evacuation-time spread to judge whether the policy generalizes beyond training demographics.

## Figures
- `evacuation_time_by_scenario.pdf`
- `fairness_gap_by_scenario.pdf`

