# Experiment 3: GA Hyperparameter Ablation (Hospital Corridor)

## Setup
- Layout: `hospital_corridor` (28 high / 12 low agents, max_ticks=1000)
- Fixed evaluation budget per run: **600** candidate evaluations
- GA seeds per configuration: `[101, 202, 303, 404, 505, 606, 707, 808, 909, 1001]` (10 seeds)
- Simulation seeds per fitness evaluation: `[11, 29, 47, 53, 61, 73, 89, 97, 101, 109]`
- Fitness weights: standard defaults (time=1, collisions=0.05, congestion=1, fairness=2)

### Configurations
- **A (Default):** pop=24, gens=25, mutation=0.2
- **B (Exploration):** pop=60, gens=10, mutation=0.3
- **C (Exploitation):** pop=10, gens=60, mutation=0.1

> Convergence is plotted vs cumulative evaluations (generation x population), not generation index.
> Total runtime: 3 configs x N seeds x 600 evaluations on hospital layout.

## Final fitness by configuration

| Config | n | median | IQR | mean | std | min | max |
|--------|---|--------|-----|------|-----|-----|-----|
| A (Default) | 10 | 52.8992 | 1.3695 | 56.9594 | 12.0064 | 52.2792 | 91.0657 |
| B (Exploration) | 10 | 54.3274 | 1.5582 | 54.8814 | 1.5438 | 53.3817 | 58.5789 |
| C (Exploitation) | 10 | 55.7363 | 4.1098 | 65.8056 | 24.0377 | 53.6232 | 127.5292 |

## Statistical tests (final best fitness)
- Kruskal-Wallis: H=7.8039, df=2, p=0.0202028
- Mann-Whitney A_default_vs_B_exploration: U=22.00, p_raw=0.0342937, p_Bonferroni=0.102881
- Mann-Whitney A_default_vs_C_exploitation: U=18.00, p_raw=0.0155644, p_Bonferroni=0.0466932
- Mann-Whitney B_exploration_vs_C_exploitation: U=34.00, p_raw=0.226476, p_Bonferroni=0.679428

## Interpretation (for report)
- Compare convergence curves on a shared evaluation budget axis to judge search efficiency.
- Exploration (B) tests whether wider initial sampling avoids catastrophic local minima.
- Exploitation (C) tests whether deep refinement improves final fitness at the risk of early stagnation.
- Use the boxplot to separate median performance from outlier seeds.

## Figures
- Convergence vs evaluations: `convergence_vs_evaluations.pdf`
- Final fitness boxplot: `best_fitness_boxplot_by_config.pdf`

## Per-run results

- A (Default) seed=101: fitness=54.4436, time=32.3000, fairness_gap=9.3561, collisions=34.0000
- A (Default) seed=202: fitness=52.8648, time=30.6200, fairness_gap=8.9793, collisions=48.5000
- A (Default) seed=303: fitness=52.9091, time=31.4600, fairness_gap=8.5339, collisions=51.6000
- A (Default) seed=404: fitness=52.4417, time=30.9300, fairness_gap=8.6835, collisions=47.0000
- A (Default) seed=505: fitness=52.8892, time=30.4900, fairness_gap=8.6771, collisions=63.9000
- A (Default) seed=606: fitness=52.2792, time=30.9100, fairness_gap=8.7982, collisions=38.0000
- A (Default) seed=707: fitness=53.8060, time=31.2800, fairness_gap=8.8981, collisions=57.6000
- A (Default) seed=808: fitness=52.6910, time=30.5800, fairness_gap=8.6956, collisions=57.5000
- A (Default) seed=909: fitness=91.0657, time=28.6500, fairness_gap=8.0849, collisions=891.7000
- A (Default) seed=1001: fitness=54.2032, time=31.7900, fairness_gap=9.0430, collisions=50.4000
- B (Exploration) seed=101: fitness=54.3343, time=31.8700, fairness_gap=9.0476, collisions=51.5000
- B (Exploration) seed=202: fitness=53.3817, time=31.2200, fairness_gap=8.8199, collisions=54.2000
- B (Exploration) seed=303: fitness=54.1953, time=31.4300, fairness_gap=8.8725, collisions=66.0000
- B (Exploration) seed=404: fitness=55.7124, time=32.5500, fairness_gap=9.2849, collisions=55.7000
- B (Exploration) seed=505: fitness=54.9026, time=31.8600, fairness_gap=9.1213, collisions=59.7000
- B (Exploration) seed=606: fitness=53.5964, time=31.9200, fairness_gap=8.7662, collisions=47.1000
- B (Exploration) seed=707: fitness=55.9213, time=33.0500, fairness_gap=9.3450, collisions=47.8000
- B (Exploration) seed=808: fitness=54.3205, time=31.5400, fairness_gap=9.0779, collisions=54.0000
- B (Exploration) seed=909: fitness=58.5789, time=30.4300, fairness_gap=8.8818, collisions=171.8000
- B (Exploration) seed=1001: fitness=53.8706, time=32.3500, fairness_gap=9.0727, collisions=31.5000
- C (Exploitation) seed=101: fitness=87.9324, time=28.9300, fairness_gap=8.3540, collisions=813.3000
- C (Exploitation) seed=202: fitness=54.5597, time=29.5100, fairness_gap=9.0015, collisions=102.6000
- C (Exploitation) seed=303: fitness=53.7007, time=31.5800, fairness_gap=9.2356, collisions=37.0000
- C (Exploitation) seed=404: fitness=56.9510, time=33.3500, fairness_gap=9.3000, collisions=67.4000
- C (Exploitation) seed=505: fitness=53.8025, time=30.0000, fairness_gap=8.9694, collisions=79.7000
- C (Exploitation) seed=606: fitness=55.1639, time=33.3200, fairness_gap=9.3838, collisions=27.0000
- C (Exploitation) seed=707: fitness=127.5292, time=29.7000, fairness_gap=8.4687, collisions=1583.1000
- C (Exploitation) seed=808: fitness=58.4851, time=31.3900, fairness_gap=9.0580, collisions=144.8000
- C (Exploitation) seed=909: fitness=56.3087, time=31.7500, fairness_gap=9.0919, collisions=91.7000
- C (Exploitation) seed=1001: fitness=53.6232, time=32.4400, fairness_gap=8.6327, collisions=40.6000
