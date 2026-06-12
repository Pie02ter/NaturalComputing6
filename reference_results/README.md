# Reference Results

These are the cleaned outputs used for the submitted report. They were imported from `results (1).zip`, restricted to the four final paper experiment folders, and cleaned of OS metadata and machine-specific absolute paths.

New experiment outputs should be written to `results/`, not here. Full reproduction can be computationally expensive; use `python scripts/run_quick_pipeline.py` for a lightweight execution check.

| Folder | Producing command |
| --- | --- |
| `experiment1_baseline_stability_hospital/` | `python scripts/run_experiment1_hospital.py` |
| `experiment2_weight_sensitivity_hospital/` | `python scripts/run_experiment2_hospital.py` |
| `experiment3_ga_ablation_hospital/` | `python scripts/run_experiment3_hospital.py` |
| `experiment4_population_stress_hospital/` | `python scripts/run_experiment4_hospital.py` |

Run `python scripts/verify_reference_results.py` for a lightweight consistency check of the stored values, file hashes, and hygiene constraints.
