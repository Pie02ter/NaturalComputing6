# Checkpoint Experiment Notes

## Experimental Settings
- layout: `standard`
- exit_width: `0.6`
- num_high: `30`
- num_low: `10`
- max_ticks: `500`
- dt: `0.1`
- evaluation seeds: `[0, 1, 2]`
- random_search_samples: `50`
- ga_population_size: `15`
- ga_generations: `15`

## Fitness Function
`fitness = 1.0 * total_time + 0.05 * mean_congestion + 0.001 * near_collisions + fairness_weight * fairness_gap_time + 10.0 * remaining_agents`

For the common comparison summary, `fitness` is recomputed with `fairness_weight = 1.0` for every method. `GA without fairness` is optimized with `fairness_weight = 0.0`; its convergence file therefore reports the no-fairness optimization objective.

## Fairness Definition
`G = abs(mean_low_time - mean_high_time)`

## Result Summary
| Method | Fitness | Total time | Fairness gap | Mean congestion | Near collisions | Remaining |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| fixed_default | 42.185 | 30.067 | 11.808 | 4.388 | 91.333 | 0.000 |
| random_search | 22.254 | 15.133 | 6.268 | 5.925 | 556.333 | 0.000 |
| ga_no_fairness | 14.944 | 9.833 | 4.154 | 6.889 | 611.333 | 0.000 |
| ga_fairness | 15.035 | 9.867 | 4.207 | 6.890 | 617.333 | 0.000 |

Best common checkpoint fitness: `ga_no_fairness` (14.944).
Fastest mean evacuation time: `ga_no_fairness` (9.833s).
The smallest mean evacuation-time gap was produced by `ga_no_fairness` (4.154s).

## Planned Next Experiments
- More evaluation seeds.
- Fairness-weight sweep with `w_G in {0, 0.25, 0.5, 1.0, 2.0}`.
- Generalization to corridor and asymmetric layouts.
- Different high/low mobility ratios.
