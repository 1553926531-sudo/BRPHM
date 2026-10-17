"""Recompute the fixed F1 gate and paired unit uncertainty from same-pass NPZ.

This postprocessor never loads a MAT, tensor, model, or training input. It does
not select or change a candidate. Gate arithmetic follows the registered
evaluator, including its saved float32 label division and comparison order.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import scipy
from scipy.stats import rankdata, wilcoxon

COMPONENTS = ("bat", "rwa")
TOLERANCE = 1e-12
PHYSICAL_UNITS = {"bat": "cycle", "rwa": "day"}
METRIC_KEYS = ("rmse", "mae", "bias", "unit_macro_rmse", "rul_upward_fraction", "n_windows", "n_units")


def canonical_bytes(value):
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode("utf-8")


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def sibling(root, name):
    if not isinstance(name, str) or Path(name).name != name or name in ("", ".", ".."):
        raise ValueError("artifact path must be a direct sibling")
    path = root / name
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"missing or symlink artifact: {name}")
    return path


def errors_for(prediction, truth_relative, rmax, rows):
    prediction = np.asarray(prediction, dtype=np.float64)
    truth = np.asarray(truth_relative, dtype=np.float64)
    if (prediction.ndim != 1 or truth.shape != prediction.shape or not len(truth)
            or len(rows) != len(truth) or not np.isfinite(prediction).all()
            or not np.isfinite(truth).all() or not math.isfinite(rmax) or rmax <= 0):
        raise ValueError("finite aligned arrays, rows, and positive rmax are required")
    by_unit = {}
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or not isinstance(row.get("unit_id"), str) or not row["unit_id"].strip():
            raise ValueError("every row needs a unit_id")
        if not math.isfinite(float(row.get("t_end", index))):
            raise ValueError("row time must be finite")
        by_unit.setdefault(str(row["unit_id"]), []).append(index)
    predicted = np.clip(prediction, 0., 1.) * float(rmax)
    actual = truth * float(rmax)
    return predicted - actual, predicted, by_unit


def recompute_metrics(prediction, truth_relative, rmax, rows):
    error, predicted, by_unit = errors_for(prediction, truth_relative, rmax, rows)
    unit_rmse = [float(np.sqrt(np.mean(error[index] ** 2))) for index in by_unit.values()]
    pairs = upward = 0
    for indices in by_unit.values():
        order = sorted(indices, key=lambda index: float(rows[index].get("t_end", index)))
        for left, right in zip(order, order[1:]):
            pairs += 1
            upward += int(predicted[right] > predicted[left] + 1e-9)
    return {"rmse": float(np.sqrt(np.mean(error ** 2))),
            "mae": float(np.mean(np.abs(error))), "bias": float(np.mean(error)),
            "unit_macro_rmse": float(np.mean(unit_rmse)),
            "rul_upward_fraction": float(upward / pairs) if pairs else None,
            "n_windows": int(len(error)), "n_units": int(len(by_unit))}


def gate_decision(candidate, reference):
    deltas, regressions, strict_gain = {}, [], False
    for component in COMPONENTS:
        if component not in candidate or component not in reference:
            raise ValueError(f"missing component metrics: {component}")
        deltas[component] = {}
        for metric in ("rmse", "mae"):
            observed, baseline = float(candidate[component][metric]), float(reference[component][metric])
            if not math.isfinite(observed) or not math.isfinite(baseline):
                raise ValueError("non-finite gate metric")
            deltas[component][metric] = observed - baseline
            # Do not replace these comparisons by a threshold on the delta.
            if observed > baseline + TOLERANCE:
                regressions.append(f"{component}.{metric}")
            if observed < baseline - TOLERANCE:
                strict_gain = True
    return {"passes": not regressions and strict_gain, "strict_gain": strict_gain,
            "regressions": sorted(regressions), "tolerance": TOLERANCE,
            "deltas_candidate_minus_same_partition_reference": deltas}


def holm_adjust(pvalues):
    if any(not math.isfinite(float(p)) or not 0 <= p <= 1 for p in pvalues):
        raise ValueError("p-values must be in [0,1]")
    order = sorted(range(len(pvalues)), key=lambda index: (float(pvalues[index]), index))
    adjusted, previous = [0.] * len(pvalues), 0.
    for rank, index in enumerate(order):
        previous = min(1., max(previous, (len(pvalues) - rank) * float(pvalues[index])))
        adjusted[index] = previous
    return adjusted


def paired_test(delta):
    delta = np.asarray(delta, dtype=np.float64)
    nonzero = delta[delta != 0]
    standard_deviation = float(np.std(delta, ddof=1)) if len(delta) > 1 else None
    if standard_deviation is None:
        effect, effect_status = None, "undefined: fewer than two units"
    elif standard_deviation == 0:
        effect, effect_status = None, "undefined: paired unit delta variance is zero"
    else:
        effect = float(np.mean(delta)) / standard_deviation
        effect_status = "defined: mean paired unit delta / sample SD of paired unit deltas"
    result = {"mean_unit_delta": float(np.mean(delta)), "median_unit_delta": float(np.median(delta)),
              "sd_unit_delta": standard_deviation,
              "standardized_paired_effect_dz": effect, "standardized_effect_status": effect_status,
              "fraction_units_lower_error": float(np.mean(delta < 0)),
              "fraction_units_equal_error": float(np.mean(delta == 0)),
              "n_units": int(len(delta)), "n_nonzero": int(len(nonzero)),
              "effect_direction": "negative delta/rank-biserial means lower candidate error"}
    if len(delta) < 2:
        return {**result, "pvalue": None, "statistic": None, "rank_biserial": None,
                "method": "single unit: descriptive only"}
    if not len(nonzero):
        return {**result, "pvalue": 1., "statistic": 0., "rank_biserial": 0.,
                "method": "all paired differences exactly zero"}
    ranks = rankdata(np.abs(nonzero), method="average")
    positive, negative = float(ranks[nonzero > 0].sum()), float(ranks[nonzero < 0].sum())
    if len(nonzero) <= 20:
        # Exact sign enumeration via rank-sum convolution handles tied ranks.
        # Doubling converts all average ranks to integers without rounding loss.
        distribution = {0: 1}
        for rank in (ranks * 2).astype(int):
            following = dict(distribution)
            for subtotal, count in distribution.items():
                following[subtotal + int(rank)] = following.get(subtotal + int(rank), 0) + count
            distribution = following
        observed = int(round(min(positive, negative) * 2))
        total = int(round(float(ranks.sum()) * 2))
        extreme = sum(count for subtotal, count in distribution.items()
                      if min(subtotal, total - subtotal) <= observed)
        pvalue = float(extreme / (2 ** len(nonzero)))
        method = "two-sided exact signed-rank sign randomization; zeros excluded; tied average ranks retained"
    else:
        test = wilcoxon(nonzero, zero_method="wilcox", correction=False,
                        alternative="two-sided", method="approx")
        pvalue = float(test.pvalue)
        method = "two-sided Wilcoxon normal approximation with tie correction; zeros excluded; no continuity correction"
    return {**result, "pvalue": pvalue, "statistic": min(positive, negative),
            "rank_biserial": (positive - negative) / (positive + negative), "method": method}


def paired_unit_statistics(candidate, control, truth_relative, rmax, rows, *, reps=20000, seed=20261018):
    if not isinstance(reps, int) or reps < 100:
        raise ValueError("at least 100 bootstrap repetitions are required")
    error_c, _, by_unit = errors_for(candidate, truth_relative, rmax, rows)
    error_b, _, _ = errors_for(control, truth_relative, rmax, rows)
    units = []
    for unit_id, index in sorted(by_unit.items()):
        c, b = error_c[index], error_b[index]
        units.append({"unit_id": unit_id, "n_windows": len(index),
                      "candidate_sse": float(np.sum(c ** 2)), "reference_sse": float(np.sum(b ** 2)),
                      "candidate_sae": float(np.sum(np.abs(c))), "reference_sae": float(np.sum(np.abs(b))),
                      "candidate_rmse": float(np.sqrt(np.mean(c ** 2))),
                      "reference_rmse": float(np.sqrt(np.mean(b ** 2))),
                      "candidate_mae": float(np.mean(np.abs(c))), "reference_mae": float(np.mean(np.abs(b)))})
        for metric in ("rmse", "mae"):
            observed, baseline = units[-1][f"candidate_{metric}"], units[-1][f"reference_{metric}"]
            units[-1][f"delta_{metric}"] = observed - baseline
            units[-1][f"relative_change_percent_{metric}"] = (
                100. * (observed - baseline) / baseline if baseline > 0 else None)
    n_units = len(units)
    names = ("n_windows", "candidate_sse", "reference_sse", "candidate_sae", "reference_sae")
    summaries = np.array([[unit[name] for name in names] for unit in units], dtype=np.float64)
    rng = np.random.default_rng(seed)
    draws = {f"{metric}__{estimand}": np.empty(reps, np.float64)
             for metric in ("rmse", "mae") for estimand in ("window_pooled", "unit_macro")}
    # Bounded batches avoid an unbounded [repetitions, units, windows] allocation.
    macro = {metric: np.array([unit[f"candidate_{metric}"] - unit[f"reference_{metric}"]
                              for unit in units]) for metric in ("rmse", "mae")}
    for begin in range(0, reps, 256):
        end = min(reps, begin + 256)
        picked = rng.integers(0, n_units, size=(end - begin, n_units))
        totals = summaries[picked].sum(axis=1)
        draws["rmse__window_pooled"][begin:end] = (np.sqrt(totals[:, 1] / totals[:, 0])
                                                         - np.sqrt(totals[:, 2] / totals[:, 0]))
        draws["mae__window_pooled"][begin:end] = (totals[:, 3] - totals[:, 4]) / totals[:, 0]
        for metric in ("rmse", "mae"):
            draws[f"{metric}__unit_macro"][begin:end] = macro[metric][picked].mean(axis=1)
    candidate_metrics = recompute_metrics(candidate, truth_relative, rmax, rows)
    reference_metrics = recompute_metrics(control, truth_relative, rmax, rows)
    bootstrap, tests = {}, {}
    for metric in ("rmse", "mae"):
        bootstrap[metric] = {}
        tests[metric] = paired_test(macro[metric])
        for estimand in ("window_pooled", "unit_macro"):
            values = draws[f"{metric}__{estimand}"]
            reference_point = (reference_metrics[metric] if estimand == "window_pooled" else
                               float(np.mean([unit[f"reference_{metric}"] for unit in units])))
            candidate_point = (candidate_metrics[metric] if estimand == "window_pooled" else
                               float(np.mean([unit[f"candidate_{metric}"] for unit in units])))
            point = (candidate_metrics[metric] - reference_metrics[metric] if estimand == "window_pooled"
                     else float(macro[metric].mean()))
            bootstrap[metric][estimand] = {
                "candidate_point": candidate_point, "reference_point": reference_point,
                "point_delta": point,
                "relative_change_percent": 100. * point / reference_point if reference_point > 0 else None,
                "relative_change_status": ("defined: 100 * paired delta / reference error" if reference_point > 0
                                           else "undefined: reference error is zero"),
                "bootstrap_sd": float(values.std(ddof=1)),
                "ci95": [float(x) for x in np.quantile(values, [.025, .975], method="linear")],
                "ci_familywise_95_bonferroni_8": [float(x) for x in np.quantile(
                    values, [.05 / 16, 1 - .05 / 16], method="linear")]}
    return {"n_units": n_units, "n_windows": len(rows), "units": units, "bootstrap": bootstrap,
            "paired_tests": tests, "bootstrap_draws": draws,
            "bootstrap_design": {"cluster": "unit_id", "paired": True, "all_unit_windows_retained": True,
                                 "seed": int(seed), "repetitions": reps, "interval": "percentile",
                                 "one_unit_limitation": n_units < 2}}


def load_component(root, component, component_receipt):
    paired = component_receipt["paired_predictions"]
    layout_path = sibling(root, paired["layout_path"])
    arrays_path = sibling(root, paired["arrays_path"])
    if sha256(layout_path) != paired["layout_sha256"] or sha256(arrays_path) != paired["arrays_sha256"]:
        raise ValueError(f"{component} paired artifact hash mismatch")
    layout = json.loads(layout_path.read_text(encoding="utf-8"))
    if (layout.get("schema") != "brphm-f1-original-pass-paired-predictions-v1"
            or layout.get("component") != component or layout.get("arrays_path") != arrays_path.name
            or layout.get("arrays_sha256") != paired["arrays_sha256"]
            or layout.get("payload_sha256") != component_receipt["payload_sha256"]):
        raise ValueError("paired layout identity/binding mismatch")
    rows = layout["rows"]
    row_hash = hashlib.sha256(canonical_bytes(rows)).hexdigest()
    if row_hash != layout["rows_sha256"] or row_hash != paired["rows_sha256"]:
        raise ValueError("paired row hash mismatch")
    if len(rows) != paired["n_rows"] or len(rows) != component_receipt["n_windows"]:
        raise ValueError("paired row count mismatch")
    with np.load(arrays_path, allow_pickle=False) as archive:
        arrays = {name: archive[name] for name in archive.files}
    required = {"truth_rul", "truth_relative", "candidate", "control", "alpha",
                "blended_before_final_projection", "projected"}
    if set(arrays) not in (required, required | {"seed_raw_predictions"}):
        raise ValueError("paired NPZ array membership mismatch")
    if set(arrays) != set(layout["array_dtypes"]) or set(arrays) != set(layout["array_shapes"]):
        raise ValueError("paired array metadata membership mismatch")
    for name, value in arrays.items():
        shape = [len(layout.get("seeds") or []), len(rows)] if name == "seed_raw_predictions" else [len(rows)]
        if (list(value.shape) != shape or list(value.shape) != layout["array_shapes"][name]
                or str(value.dtype) != layout["array_dtypes"][name]
                or value.dtype.kind != "f" or not np.isfinite(value).all()):
            raise ValueError(f"paired array shape/dtype/finiteness mismatch: {name}")
    rmax = float(layout["rmax"])
    if not math.isfinite(rmax) or rmax <= 0:
        raise ValueError("invalid paired rmax")
    if not np.array_equal(arrays["truth_relative"], arrays["truth_rul"] / float(rmax)):
        raise ValueError("saved truth_relative does not preserve evaluator label division")
    alpha = arrays["alpha"]
    if np.any(alpha < 0) or np.any(alpha > 1):
        raise ValueError("alpha outside [0,1]")
    expected = (alpha * np.asarray(arrays["candidate"], dtype=np.float32)
                + (1. - alpha) * np.asarray(arrays["control"], dtype=np.float32))
    if not np.array_equal(expected, arrays["blended_before_final_projection"]):
        raise ValueError("same-pass candidate/control blend mismatch")
    metrics = {name: recompute_metrics(arrays[key], arrays["truth_relative"], rmax, rows)
               for name, key in (("metrics", "projected"), ("candidate_only_metrics", "candidate"),
                                 ("control_only_metrics", "control"))}
    for name, recomputed in metrics.items():
        for key in METRIC_KEYS:
            if recomputed[key] != component_receipt[name][key]:
                raise ValueError(f"unrounded metric mismatch: {component}.{name}.{key}")
    if metrics["metrics"]["n_units"] != component_receipt["n_units"]:
        raise ValueError("component unit count mismatch")
    return layout, arrays, metrics


def build_report(result, *, reps=20000, seed=20261018):
    root = Path(result).resolve(strict=True)
    receipt_path = sibling(root, "final_receipt.json")
    gate_path = sibling(root, "same_partition_performance_gate.json")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    original_gate = json.loads(gate_path.read_text(encoding="utf-8"))
    if receipt.get("schema") != "brphm-f1-clean-final-evaluation-v1":
        raise ValueError("unexpected final receipt schema")
    if original_gate["final_receipt_sha256"] != sha256(receipt_path):
        raise ValueError("final receipt hash mismatch")
    for name in ("freeze_manifest", "selection_decision"):
        if receipt[name + "_sha256"] != sha256(sibling(root, name + ".json")):
            raise ValueError(f"{name} hash mismatch")
    if original_gate["freeze_manifest_sha256"] != receipt["freeze_manifest_sha256"]:
        raise ValueError("gate freeze binding mismatch")
    candidate, reference, components, distributions = {}, {}, {}, {}
    for component_index, component in enumerate(COMPONENTS):
        entry = receipt["results"][component]
        layout, arrays, metrics = load_component(root, component, entry)
        candidate[component], reference[component] = metrics["metrics"], metrics["control_only_metrics"]
        if (original_gate["metrics"][component]["candidate_blend"] != entry["metrics"]
                or original_gate["metrics"][component]["same_partition_reference"] != entry["control_only_metrics"]):
            raise ValueError("gate metric binding mismatch")
        component_stats = paired_unit_statistics(arrays["projected"], arrays["control"],
                                                 arrays["truth_relative"], float(layout["rmax"]), layout["rows"],
                                                 reps=reps, seed=seed + component_index)
        distributions.update({f"{component}__{name}": values
                              for name, values in component_stats.pop("bootstrap_draws").items()})
        raw = arrays.get("seed_raw_predictions")
        seed_metrics = [] if raw is None else [
            {"seed": seed_id, "raw_metrics": recompute_metrics(values, arrays["truth_relative"],
                                                               float(layout["rmax"]), layout["rows"])}
            for seed_id, values in zip(layout["seeds"], raw)]
        components[component] = {**component_stats, "metrics": metrics,
                                 "physical_unit": PHYSICAL_UNITS[component], "rmax": float(layout["rmax"]),
                                 "prediction_binding": entry["paired_predictions"],
                                 "seed_description": {"constituents": seed_metrics, "independent_repeats": 0,
                                     "interpretation": "raw ensemble constituents before centering/projection; no seed-level inference"}}
    gate = gate_decision(candidate, reference)
    for key, value in gate.items():
        if value != original_gate["comparison"][key]:
            raise ValueError(f"recomputed gate disagreement: {key}")
    family = [(component, metric) for component in COMPONENTS for metric in ("rmse", "mae")]
    adjusted = holm_adjust([components[c]["paired_tests"][m]["pvalue"]
                            if components[c]["paired_tests"][m]["pvalue"] is not None else 1.
                            for c, m in family])
    for (component, metric), pvalue in zip(family, adjusted):
        test = components[component]["paired_tests"][metric]
        test["holm_pvalue_family4"] = pvalue if test["pvalue"] is not None else None
    return {"schema": "brphm-f1-lossless-gate-paired-unit-statistics-v1",
            "created_utc": datetime.now(timezone.utc).isoformat(), "gate": gate, "components": components,
            "inputs": {p.name: sha256(p) for p in (receipt_path, gate_path,
                        sibling(root, "freeze_manifest.json"), sibling(root, "selection_decision.json"))},
            "analysis_code_sha256": sha256(Path(__file__)),
            "verification": {"gate_matches_original": True, "metrics_exactly_match_original": True,
                             "models_rerun": False, "tensors_or_mat_loaded": False},
            "multiple_comparisons": {"paired_tests": "Holm over 4 component-by-metric unit paired tests",
                                     "bootstrap_intervals": "pointwise95 and Bonferroni familywise95 over 8 component-by-metric-by-estimand intervals"},
            "limitations": ["one final orbit, not an independent orbit-level replication",
                            "unit-cluster uncertainty conditional on the simulator, fixed candidate and training run",
                            "overlapping windows remain in their sampled units; no window independence assumption",
                            "signed-rank inference assumes independent units and symmetric paired differences",
                            "ensemble constituents are not independent training repetitions",
                            "deterministic gate pass alone establishes neither statistical nor practical improvement"],
            "runtime": {"python": sys.version, "platform": platform.platform(),
                        "numpy": np.__version__, "scipy": scipy.__version__}}, distributions


def write_report(result, output, *, reps=20000, seed=20261018):
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    report, distributions = build_report(result, reps=reps, seed=seed)
    output.mkdir(parents=True, exist_ok=False)
    arrays_path = output / "f1_unit_cluster_bootstrap.npz"
    with arrays_path.open("xb") as handle:
        np.savez_compressed(handle, **distributions)
    report["bootstrap_distributions"] = {"path": arrays_path.name, "sha256": sha256(arrays_path),
                                         "shapes": {k: list(v.shape) for k, v in distributions.items()}}
    text = io.StringIO(newline="")
    fields = ("component", "metric", "physical_unit", "n_units", "n_windows", "candidate", "candidate_hex",
              "reference", "reference_hex", "delta", "delta_hex", "reference_plus_tolerance",
              "reference_plus_tolerance_hex", "reference_minus_tolerance", "reference_minus_tolerance_hex",
              "regression", "strict_gain")
    writer = csv.DictWriter(text, fieldnames=fields)
    writer.writeheader()
    for component in COMPONENTS:
        item = report["components"][component]
        for metric in ("rmse", "mae"):
            observed = item["metrics"]["metrics"][metric]
            baseline = item["metrics"]["control_only_metrics"][metric]
            row = {"component": component, "metric": metric, "physical_unit": item["physical_unit"],
                   "n_units": item["n_units"], "n_windows": item["n_windows"],
                   "regression": observed > baseline + TOLERANCE, "strict_gain": observed < baseline - TOLERANCE}
            for name, value in (("candidate", observed), ("reference", baseline), ("delta", observed - baseline),
                                ("reference_plus_tolerance", baseline + TOLERANCE),
                                ("reference_minus_tolerance", baseline - TOLERANCE)):
                row[name], row[name + "_hex"] = format(value, ".17g"), value.hex()
            writer.writerow(row)
    csv_path = output / "f1_full_precision_gate.csv"
    with csv_path.open("xb") as handle:
        handle.write(text.getvalue().encode("utf-8"))
    report["full_precision_csv"] = {"path": csv_path.name, "sha256": sha256(csv_path)}
    report_path = output / "f1_gate_statistics.json"
    with report_path.open("xb") as handle:
        handle.write(canonical_bytes(report))
    receipt = {"schema": "brphm-f1-lossless-statistics-receipt-v1", "status": "PASS",
               "report_sha256": sha256(report_path), "gate_passes": report["gate"]["passes"],
               "note": "PASS verifies reconstruction and artifact integrity; see gate_passes for the experiment gate",
               "created_utc": report["created_utc"]}
    with (output / "statistics_receipt.json").open("xb") as handle:
        handle.write(canonical_bytes(receipt))
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--bootstrap-reps", type=int, default=20000)
    parser.add_argument("--bootstrap-seed", type=int, default=20261018)
    args = parser.parse_args(argv)
    print(json.dumps(write_report(args.result, args.output, reps=args.bootstrap_reps,
                                  seed=args.bootstrap_seed), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
