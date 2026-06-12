# Paper-Code Consistency

This audit compares the current command-line code, the cleaned reference outputs in `reference_results/`, and the submitted report text.

## Confirmed Matches

The repository implements the four final hospital-corridor experiments and preserves their submitted result-producing settings. The reference outputs contain the final folders `experiment1_baseline_stability_hospital/`, `experiment2_weight_sensitivity_hospital/`, `experiment3_ga_ablation_hospital/`, and `experiment4_population_stress_hospital/`.

The GA minimizes fitness. Experiment 2 metadata records the selection rule as `lowest_best_fitness_across_seeds`, and the selected candidates in `summary_by_weights.csv` match the minimum best-fitness candidates in `all_ga_seed_attempts.csv`.

Experiment 4 uses Experiment 1 GA seed `606` as its fixed parameter source. The cleaned metadata uses a repository-relative source path instead of the exported private absolute path.

## Documentation Omissions

The submitted report does not fully describe all simulator mechanics that affect interpretation: low-mobility route-target acceleration scaling, reduced low-mobility crowd-repulsion scaling, minimum forward pace when stalled, waypoint stall recovery, hard body-separation correction, exact collision/congestion thresholds, and the fixed waypoint routing graph.

These mechanics are now documented in `REPRODUCIBILITY.md` without changing experiment semantics.

## Paper Corrections Still Required

Experiment 3 is not a strict isolated population-size-versus-generation-count ablation. The code and exported metadata use:

```text
A_default:      population 24, generations 25, mutation probability 0.2
B_exploration:  population 60, generations 10, mutation probability 0.3
C_exploitation: population 10, generations 60, mutation probability 0.1
```

The paper should describe Experiment 3 as a comparison of broader search dynamics under a fixed 600-evaluation budget, not as an isolated ablation where only population size and generation count vary.

Experiment 2 wording should say the `lowest fitness candidate` was selected. The current phrase `highest fitness candidate` is incorrect because the GA minimizes fitness.

The Experiment 3 results discussion contains an unresolved figure placeholder in the submitted report text. Repository documentation avoids reproducing that stale placeholder, but the paper PDF itself must be revised separately.

The simulator-methods section should explicitly mention the undocumented mechanics listed above.

Experiment 4 documentation should avoid calling the 20/20 population `Default`, because the main Experiment 1 default is 28 high-mobility and 12 low-mobility agents. Repository documentation and newly generated plots use `Balanced (20 high / 20 low)`.

## Code-Cleanup Changes Made Without Changing Experiment Semantics

Generated outputs under `results/` are ignored; submitted outputs are tracked under `reference_results/`.

Apple metadata and legacy/debug result folders from the exported ZIP were excluded from `reference_results/`.

Unseeded plotting jitter was replaced with local fixed plot RNGs. This only affects point placement in regenerated figures and does not affect simulation RNG, GA RNG, metrics, or reference values.

Experiment 4 metadata no longer embeds private absolute source paths in newly generated outputs.

## Unresolved Issues

`pdftotext` was unavailable in the validation environment, so PDF text extraction could not be automated during this cleanup. The known paper-text issues above are documented from the provided task requirements and checked against repository documentation where possible.

Full end-to-end recomputation of the paper experiments was not performed because the full sweeps are computationally expensive. The repository verifies the submitted values from stored reference outputs and provides quick executable checks for the code path.
