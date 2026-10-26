"""Reproducible chronological count-model experiment; never a prospective validation."""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path

import numpy as np
import pandas as pd

from measleswatch.describe import read_validated_tables
from measleswatch.ingest import load_config, sha256, verify_study_contract, write_json
from measleswatch.models import fit_count

MODELS = ("seasonal_naive", "seasonal_reference", "negative_binomial")


def finite_json(value):
    if isinstance(value, dict):
        return {str(k): finite_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, np.ndarray)):
        return [finite_json(v) for v in value]
    if isinstance(value, (np.integer, np.bool_)):
        return value.item()
    if isinstance(value, (float, np.floating)):
        return float(value) if np.isfinite(value) else None
    return value


def metrics(rows):
    scored = [r for r in rows if r["status"] == "ok" and r["expected"] is not None]
    errors = [r["observed"] - r["expected"] for r in scored]
    intervals = [r for r in scored if r["lower_95"] is not None]
    scales = [abs(r["observed"] - r["expected"]) / r["mase_scale"]
              for r in scored if r["mase_scale"] is not None]
    zero_probabilities = sum(r["zero_predictive_probability"] for r in intervals)
    log_scores = [r["negative_log_probability"] for r in intervals
                  if r["negative_log_probability"] is not None]
    return {
        "eligible_months": len(rows), "scored_months": len(scored),
        "failed_months": len(rows) - len(scored),
        "MAE": float(np.mean(np.abs(errors))) if errors else None,
        "RMSE": float(np.sqrt(np.mean(np.square(errors)))) if errors else None,
        "MASE": float(np.mean(scales)) if scales else None,
        "MASE_scored_months": len(scales),
        "interval_scored_months": len(intervals),
        "interval_coverage": sum(r["lower_95"] <= r["observed"] <= r["upper_95"]
                                 for r in intervals) / len(intervals) if intervals else None,
        "interval_width": float(np.mean([r["upper_95"] - r["lower_95"] for r in intervals]))
                          if intervals else None,
        "negative_log_predictive_probability": float(np.mean(log_scores))
                          if log_scores and not zero_probabilities else None,
        "log_score_status": "infinite_zero_probability" if zero_probabilities
                            else "defined" if log_scores else "not_available",
        "zero_predictive_probability_months": zero_probabilities,
        "alert_months": sum(r["anomaly"] is True for r in intervals),
        "alert_proportion": sum(r["anomaly"] is True for r in intervals) / len(intervals)
                            if intervals else None,
        "reference": "Statistical exceedance frequency; real outbreak labels unavailable",
    }


def chronological_predictions(dates, y, measure, start, end, window=60, fixed_cutoff=None,
                              model_names=MODELS, split="test"):
    dates = pd.DatetimeIndex(dates)
    y = np.asarray(y, dtype=float)
    result, diagnostics = [], []
    targets = dates[(dates >= pd.Timestamp(start)) & (dates <= pd.Timestamp(end))]
    cache = {}
    for target in targets:
        cutoff = pd.Timestamp(fixed_cutoff) if fixed_cutoff else target - pd.offsets.MonthBegin(1)
        eligible = dates <= cutoff
        train_dates, train_y = dates[eligible][-window:], y[eligible][-window:]
        if len(train_dates) < window:
            continue  # shared-eligibility counts are recorded by the caller
        observed = int(y[np.flatnonzero(dates == target)[0]])
        for name in model_names:
            key = (name, cutoff)
            if key not in cache:
                cache[key] = fit_count(name, train_dates, train_y)
                diagnostics.append({"measure": measure, "model": name, "split": split,
                                    "training_window": window, "training_end": cutoff.strftime("%Y-%m"),
                                    "status": cache[key].status, **cache[key].diagnostics,
                                    "warnings": cache[key].warnings})
            row = cache[key].predict(target, observed)
            row.update({"measure": measure, "split": split, "geography": "Bangladesh",
                        "population": "all_ages", "unit": "reported_cases",
                        "training_window": window, "fixed_origin": fixed_cutoff is not None})
            result.append(row)
    return result, diagnostics


def paired_bootstrap(rows):
    by = {(r["model"], r["month"]): r for r in rows if r["status"] == "ok"}
    months = sorted({r["month"] for r in rows})
    differences = []
    for month in months:
        a, b = by.get(("negative_binomial", month)), by.get(("seasonal_naive", month))
        if a and b:
            differences.append(abs(a["observed"] - a["expected"]) - abs(b["observed"] - b["expected"]))
    if len(differences) != 48:
        return {"status": "unavailable_requires_48_paired_months", "paired_months": len(differences)}
    rng = np.random.default_rng(2026)
    draws = []
    for _ in range(1000):
        indices = np.concatenate([(s + np.arange(12)) % 48 for s in rng.integers(0, 48, 4)])
        draws.append(float(np.asarray(differences)[indices].mean()))
    return {"status": "defined", "NB_minus_naive_MAE": float(np.mean(differences)),
            "block_bootstrap_95": [float(v) for v in np.quantile(draws, [.025, .975])],
            "resamples": 1000, "block_months": 12, "paired_months": 48,
            "limitation": "Only 48 test months; limited precision, not evidence of prospective skill"}


def synthetic_experiment():
    dates = pd.date_range("2000-01", periods=72, freq="MS")
    t = np.arange(72)
    mean = 20 * np.exp(.35 * np.sin(2 * np.pi * t / 12) + .20 * np.cos(2 * np.pi * t / 12) + .005 * t)
    records = []
    for process_index, process in enumerate(("poisson", "negative_binomial_nb2")):
        for strength_index, multiplier in enumerate((2.0, 4.0)):
            for replicate in range(10):
                streams = np.random.SeedSequence([2026, process_index, strength_index, replicate]).spawn(3)
                clean_rng, onset_rng, injection_rng = [np.random.default_rng(s) for s in streams]
                clean = (clean_rng.poisson(mean) if process == "poisson" else
                         clean_rng.negative_binomial(1 / .3, 1 / (1 + .3 * mean)))
                onset = int(onset_rng.integers(0, 10))
                injected = clean.copy()
                indices = np.arange(60 + onset, 63 + onset)
                injected[indices] += injection_rng.poisson((multiplier - 1) * mean[indices])
                for model in ("seasonal_reference", "negative_binomial"):
                    fit = fit_count(model, dates[:60], clean[:60])
                    for kind, values in (("clean", clean), ("injected", injected)):
                        for i in range(12):
                            record = fit.predict(dates[60 + i], values[60 + i])
                            record.update({"process": process, "multiplier": multiplier,
                                           "replicate": replicate, "path": kind,
                                           "pulse_label": bool(onset <= i < onset + 3),
                                           "onset": onset, "evaluation_index": i,
                                           "synthetic": True})
                            records.append(record)
    summaries = []
    grouped = defaultdict(list)
    for row in records:
        grouped[(row["process"], row["multiplier"], row["model"])].append(row)
    for (process, multiplier, model), rows in grouped.items():
        clean = [r for r in rows if r["path"] == "clean" and r["anomaly"] is not None]
        injected = [r for r in rows if r["path"] == "injected" and r["anomaly"] is not None]
        tp = sum(r["anomaly"] and r["pulse_label"] for r in injected)
        alerts = sum(r["anomaly"] for r in injected)
        labels = sum(r["pulse_label"] for r in injected)
        precision, recall = tp / alerts if alerts else None, tp / labels if labels else None
        delays = []
        for replicate in range(10):
            found = [r["evaluation_index"] - r["onset"] for r in injected
                     if r["replicate"] == replicate and r["anomaly"] and r["pulse_label"]]
            delays.append(min(found) if found else None)
        summaries.append({"process": process, "multiplier": multiplier, "model": model,
                          "clean_months_scored": len(clean), "injected_months_scored": len(injected),
                          "false_alert_proportion": sum(r["anomaly"] for r in clean) / len(clean) if clean else None,
                          "precision": precision, "monthly_recall": recall,
                          "F1": 2 * precision * recall / (precision + recall)
                                if precision is not None and recall is not None and precision + recall else None,
                          "event_recall": sum(v is not None for v in delays) / 10,
                          "missed_events": sum(v is None for v in delays),
                          "delays_months": delays,
                          "interpretation": "Synthetic stress test only; not Bangladesh surveillance validation"})
    return records, summaries


def run_evaluation(root, output, input_dir=None):
    root, output = Path(root), Path(output)
    if output.exists():
        raise FileExistsError(output)
    tables, source = read_validated_tables(input_dir or root / "data/processed/phase1-r2")
    verify_study_contract(root / ".devin/study.toml", source)
    protocol = load_config(root / ".devin/analysis_protocol.toml")
    rows, diagnostics, sensitivity, diagnostic_comparisons = [], [], [], []
    for measure in (protocol["primary_target"], protocol["sensitivity_target"]):
        series = sorted([r for r in tables["surveillance_monthly"] if r["measure"] == measure],
                        key=lambda r: r["month"])
        dates = pd.DatetimeIndex([r["month"] + "-01" for r in series])
        y = np.asarray([r["count"] for r in series])
        for start, end, split, cutoff in (("2017-01", "2021-12", "development", None),
                                         ("2022-01", "2025-12", "test", None),
                                         ("2026-01", "2026-05", "case_study", "2025-12")):
            part, diag = chronological_predictions(dates, y, measure, start, end,
                                                    fixed_cutoff=cutoff, split=split)
            rows.extend(part)
            diagnostics.extend(diag)
        for window in (36, 84):
            part, diag = chronological_predictions(dates, y, measure, "2022-01", "2025-12",
                                                    window=window, model_names=("negative_binomial",),
                                                    split="test_window_sensitivity")
            rows.extend(part)
            diagnostics.extend(diag)
        eligible = dates <= pd.Timestamp("2021-12-01")
        train_dates, train_y = dates[eligible][-60:], y[eligible][-60:]
        target, observed = pd.Timestamp("2022-01-01"), y[dates == pd.Timestamp("2022-01-01")][0]
        base = fit_count("negative_binomial", train_dates, train_y)
        poisson_fit = fit_count("poisson_diagnostic", train_dates, train_y)
        diagnostic_comparisons.append({"measure": measure, "training_end": "2021-12",
                                       "NB2": base.diagnostics, "Poisson": poisson_fit.diagnostics,
                                       "note": "Development-only diagnostics; main NB2 model prespecified"})
        perturbed = train_y.copy()
        perturbed[int(np.argmax(perturbed))] *= 2
        changed = fit_count("negative_binomial", train_dates, perturbed)
        try:
            keep = np.ones(60, dtype=bool)
            keep[[7, 18, 39]] = False
            fit_count("negative_binomial", train_dates[keep], train_y[keep])
            missingness = "unexpected_acceptance"
        except ValueError:
            missingness = "rejected_incomplete_training_no_imputation"
        sensitivity.append({"measure": measure, "fit_cutoff": "2021-12",
                            "origin": "2022-01", "base": base.predict(target, observed),
                            "doubled_largest_training_count": changed.predict(target, observed),
                            "missingness_stress": missingness,
                            "note": "Isolated copies; primary inputs unchanged. Not a model-selection exercise."})
    groups = defaultdict(list)
    for row in rows:
        groups[(row["measure"], row["model"], row["split"], row["training_window"])].append(row)
    summaries = [{"measure": key[0], "model": key[1], "split": key[2], "training_window": key[3],
                  **metrics(value)} for key, value in groups.items()]
    synthetic, synthetic_summary = synthetic_experiment()
    bootstraps = {measure: paired_bootstrap([r for r in rows if r["split"] == "test" and r["measure"] == measure])
                  for measure in (protocol["primary_target"], protocol["sensitivity_target"])}
    output.mkdir(parents=True)
    artifacts = {"predictions": rows, "metrics": summaries, "diagnostics": diagnostics,
                 "development_diagnostics": diagnostic_comparisons, "sensitivity": sensitivity,
                 "paired_bootstrap": bootstraps, "synthetic_predictions": synthetic,
                 "synthetic_metrics": synthetic_summary}
    for name, value in artifacts.items():
        write_json(output / f"{name}.json", finite_json(value))
    manifest = {"status": "completed_retrospective_statistical_evaluation", "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "protocol_sha256": sha256(root / ".devin/analysis_protocol.toml"),
                "supplement_sha256": sha256(root / ".devin/completion_protocol.toml"),
                "source_table_sha256": source["table_sha256"],
                "implementation_sha256": {f: sha256(root / f"src/measleswatch/{f}.py") for f in ("models", "evaluate")},
                "artifact_sha256": {name: sha256(output / f"{name}.json") for name in artifacts},
                "limitations": ["Historical observation ordering enforced; historical release vintages unavailable",
                                "Plug-in prediction bounds exclude some parameter and reporting uncertainty",
                                "Real monthly outbreak labels unavailable; statistical anomalies are not confirmed outbreaks",
                                "Synthetic detector metrics do not validate Bangladesh public-health effectiveness"]}
    write_json(output / "run_manifest.json", manifest)
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run_evaluation(Path.cwd(), args.output), indent=2))
