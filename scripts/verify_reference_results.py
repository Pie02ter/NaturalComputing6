#!/usr/bin/env python3
import csv
import hashlib
import json
import math
import re
import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "reference_results"
DOC_EXTS = {".md", ".py", ".json", ".toml", ".txt", ".csv"}
NORMALIZED_HASH_EXTS = {".md", ".json", ".toml", ".txt", ".csv"}
EXPECTED_DIRS = [
    "experiment1_baseline_stability_hospital",
    "experiment2_weight_sensitivity_hospital",
    "experiment3_ga_ablation_hospital",
    "experiment4_population_stress_hospital",
]


def fail(message):
    raise AssertionError(message)


def approx(actual, expected, tol, label):
    if not math.isclose(float(actual), float(expected), abs_tol=tol):
        fail(f"{label}: expected {expected} +/- {tol}, got {actual}")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def manifest_bytes(path):
    data = path.read_bytes()
    if path.suffix in NORMALIZED_HASH_EXTS:
        data = data.replace(b"\r\n", b"\n")
    return data


def sha256_file(path):
    digest = hashlib.sha256()
    digest.update(manifest_bytes(path))
    return digest.hexdigest()


def check_manifest():
    manifest_path = REF / "manifest.json"
    if not manifest_path.exists():
        fail("Missing reference_results/manifest.json")
    manifest = read_json(manifest_path)
    if manifest.get("experiment_directories") != EXPECTED_DIRS:
        fail("Manifest experiment_directories mismatch")

    entries = {entry["path"]: entry for entry in manifest.get("files", [])}
    actual_files = sorted(
        path.relative_to(REF).as_posix()
        for path in REF.rglob("*")
        if path.is_file() and path.name != "manifest.json"
    )
    if sorted(entries) != actual_files:
        missing = sorted(set(actual_files) - set(entries))
        extra = sorted(set(entries) - set(actual_files))
        fail(f"Manifest file list mismatch; missing={missing[:5]} extra={extra[:5]}")
    for rel_path, entry in entries.items():
        path = REF / rel_path
        if len(manifest_bytes(path)) != int(entry["size_bytes"]):
            fail(f"Manifest size mismatch: {rel_path}")
        if sha256_file(path) != entry["sha256"]:
            fail(f"Manifest hash mismatch: {rel_path}")


def check_hygiene():
    bad_names = []
    bad_text = []
    absolute_terms = ["/Use" + "rs/", "/ho" + "me/", r"[A-Za-z]:" + r"\\"]
    absolute_pattern = re.compile("|".join(absolute_terms))
    forbidden_terms = [
        "bro" + "wser",
        "front" + "end",
        "Fla" + "sk",
        "web" + " UI",
        "UI has" + " been removed",
        "127" + ".0.0.1",
        "local" + "host",
        "Figure " + "??",
    ]
    forbidden_doc_pattern = re.compile("|".join(re.escape(term) for term in forbidden_terms), re.I)

    for path in ROOT.rglob("*"):
        rel = path.relative_to(ROOT).as_posix()
        if any(part in {".git", ".venv", "__pycache__"} for part in path.parts):
            continue
        if rel.startswith("results/") and rel != "results/README.md":
            continue
        if path.name == ".DS_Store" or path.name == "__MACOSX" or path.name.startswith("._"):
            bad_names.append(rel)
        if path.is_file() and path.suffix in DOC_EXTS:
            text = path.read_text(encoding="utf-8", errors="ignore")
            if absolute_pattern.search(text):
                bad_text.append(f"absolute path: {rel}")
            if rel != "docs/PAPER_CODE_CONSISTENCY.md" and forbidden_doc_pattern.search(text):
                bad_text.append(f"forbidden wording: {rel}")

    if bad_names:
        fail(f"OS metadata found: {bad_names[:10]}")
    if bad_text:
        fail(f"Text hygiene failures: {bad_text[:10]}")


def check_experiment1():
    exp = REF / EXPECTED_DIRS[0]
    stats = read_json(exp / "aggregate_stats.json")
    rows = list(csv.DictReader((exp / "summary_per_run.csv").open(newline="", encoding="utf-8")))
    if len(rows) != 10 or int(stats["n_runs"]) != 10:
        fail("Experiment 1 run count mismatch")
    sign = stats["sign_test_improvement"]
    if sign["runs_with_improvement"] != 10 or sign["total_runs"] != 10:
        fail("Experiment 1 sign-test count mismatch")
    approx(sign["p_value_two_sided"], 0.001953125, 1e-12, "Experiment 1 sign-test p")
    mk = stats["mann_kendall_mean_convergence"]
    if mk["S"] != -298:
        fail("Experiment 1 Mann-Kendall S mismatch")
    approx(mk["Z"], -6.94, 0.01, "Experiment 1 Mann-Kendall Z")
    approx(stats["best_fitness"]["mean"], 56.96, 0.02, "Experiment 1 mean best fitness")
    approx(stats["best_fitness"]["std"], 12.01, 0.02, "Experiment 1 std best fitness")
    run9 = rows[8]
    approx(run9["agent_radius"], 2.10, 0.01, "Experiment 1 run 9 agent radius")
    approx(run9["agent_rep_weight"], 0.89, 0.01, "Experiment 1 run 9 repulsion")
    approx(run9["mean_collisions"], 891.7, 0.1, "Experiment 1 run 9 near-collisions")


def check_experiment2():
    exp = REF / EXPECTED_DIRS[1]
    stats = read_json(exp / "aggregate_stats.json")
    if stats["n_weight_pairs"] != 5:
        fail("Experiment 2 weight-pair count mismatch")
    if stats["selection_rule"] != "lowest_best_fitness_across_seeds":
        fail("Experiment 2 selection rule mismatch")
    df = pd.read_csv(exp / "summary_by_weights.csv")
    attempts = pd.read_csv(exp / "all_ga_seed_attempts.csv")
    for _, row in df.iterrows():
        subset = attempts[(attempts["w_time"] == row["w_time"]) & (attempts["w_fair"] == row["w_fair"])]
        if int(row["ga_seed_selected"]) != int(subset.loc[subset["best_fitness"].idxmin(), "ga_seed"]):
            fail("Experiment 2 selected candidate is not lowest fitness")
    lookup = {(float(r.w_time), float(r.w_fair)): r for r in df.itertuples()}
    approx(lookup[(1.0, 0.0)].mean_time, 30.89, 0.02, "Experiment 2 (1,0) mean time")
    approx(lookup[(1.0, 2.0)].mean_fairness_gap, 8.68, 0.02, "Experiment 2 (1,2) fairness gap")
    approx(lookup[(0.0, 1.0)].mean_time, 32.34, 0.02, "Experiment 2 (0,1) mean time")
    approx(lookup[(0.0, 1.0)].mean_collisions, 25.5, 0.1, "Experiment 2 (0,1) near-collisions")
    approx(stats["spearman_w_fair_vs_mean_fairness_gap"], -0.975, 0.002, "Experiment 2 Spearman")


def check_experiment3():
    exp = REF / EXPECTED_DIRS[2]
    stats = read_json(exp / "aggregate_stats.json")
    if stats["eval_budget"] != 600:
        fail("Experiment 3 eval budget mismatch")
    df = pd.read_csv(exp / "summary_per_run.csv")
    expected = {
        "A_default": (24, 25, 0.2, 52.90),
        "B_exploration": (60, 10, 0.3, 54.33),
        "C_exploitation": (10, 60, 0.1, 55.74),
    }
    for name, (pop, gen, mut, median) in expected.items():
        subset = df[df["config_name"] == name]
        if set(subset["population_size"].astype(int)) != {pop}:
            fail(f"Experiment 3 {name} population mismatch")
        if set(subset["generations"].astype(int)) != {gen}:
            fail(f"Experiment 3 {name} generation mismatch")
        if set(round(x, 10) for x in subset["mutation_probability"].astype(float)) != {mut}:
            fail(f"Experiment 3 {name} mutation mismatch")
        approx(stats["configs"][name]["median"], median, 0.02, f"Experiment 3 {name} median")
    kw = stats["kruskal_wallis_final_fitness"]
    approx(kw["H"], 7.80, 0.02, "Experiment 3 Kruskal-Wallis H")
    approx(kw["p_value"], 0.020, 0.002, "Experiment 3 Kruskal-Wallis p")
    posthoc = {item["comparison"]: item for item in stats["mann_whitney_posthoc_bonferroni"]}
    approx(posthoc["A_default_vs_C_exploitation"]["p_value_bonferroni"], 0.047, 0.002, "Experiment 3 A vs C adjusted p")


def check_experiment4():
    exp = REF / EXPECTED_DIRS[3]
    stats = read_json(exp / "aggregate_stats.json")
    fixed = stats["fixed_params"]
    if fixed["selected_ga_seed"] != 606:
        fail("Experiment 4 fixed GA seed mismatch")
    if stats["n_seeds_per_scenario"] != 30:
        fail("Experiment 4 seed count mismatch")
    expected = {
        "balanced_50_50": (20, 20, 1.0, 39.35),
        "high_dominant_80_20": (32, 8, 0.967, 30.90),
        "low_dominant_20_80": (8, 32, 1.0, 46.65),
    }
    if set(stats["scenarios"]) != set(expected):
        fail("Experiment 4 scenario set mismatch")
    for name, (high, low, rate, median) in expected.items():
        scenario = stats["scenarios"][name]
        if scenario["num_high"] != high or scenario["num_low"] != low:
            fail(f"Experiment 4 {name} population mismatch")
        approx(scenario["all_evacuated_rate"], rate, 0.001, f"Experiment 4 {name} completion rate")
        approx(scenario["total_time"]["median"], median, 0.02, f"Experiment 4 {name} median time")
    approx(stats["kruskal_wallis_total_time"]["H"], 50.48, 0.02, "Experiment 4 total-time H")
    approx(stats["kruskal_wallis_fairness_gap"]["H"], 2.84, 0.02, "Experiment 4 fairness H")
    approx(stats["kruskal_wallis_fairness_gap"]["p_value"], 0.24, 0.01, "Experiment 4 fairness p")


def main():
    checks = [
        check_manifest,
        check_hygiene,
        check_experiment1,
        check_experiment2,
        check_experiment3,
        check_experiment4,
    ]
    failures = []
    for check in checks:
        try:
            check()
            print(f"PASS {check.__name__}")
        except Exception as exc:
            failures.append(f"FAIL {check.__name__}: {exc}")
            print(failures[-1])
    if failures:
        return 1
    print("Reference results verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
