# Experiment 2: Multi-Objective Weight Sensitivity (Hospital Corridor)

| w_time | w_fair | GA seed | mean_time (s) | mean_fairness_gap (s) | mean_collisions | best_fitness |
|--------|--------|---------|---------------|------------------------|-----------------|--------------|
| 1 | 0 | 202 | 30.8900 | 9.3827 | 45.9000 | 35.0692 |
| 1 | 0.5 | 202 | 31.9500 | 9.1058 | 27.5000 | 39.6339 |
| 1 | 1 | 505 | 31.0600 | 8.9002 | 41.9000 | 44.0110 |
| 1 | 2 | 404 | 30.9300 | 8.6835 | 47.0000 | 52.4417 |
| 0 | 1 | 202 | 32.3400 | 8.7188 | 25.5000 | 11.7252 |

## Statistical notes
- Spearman(w_fair, fairness_gap): -0.9746794344808963
- Spearman(w_fair, time): 0.20519567041703085
- Spearman(w_fair, collisions): 0.20519567041703085