from __future__ import annotations

"""Unit-cluster uncertainty for the frozen F8 source-gate residual KS checks."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.stats import ks_2samp


ROOT = Path(__file__).resolve().parents[3]
PAIRS = ("LEO500<->LEO550", "LEO500<->LEO700", "LEO550<->LEO700")
COMPONENTS = ("bat", "rwa")
BOOTSTRAP_REPS = 5000
PERMUTATION_REPS = 5000
SEED = 20261002


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def flatten(groups: dict[str, list[float]], selected_ids: list[str] | None = None) -> np.ndarray:
    keys = selected_ids if selected_ids is not None else list(groups)
    return np.concatenate([np.asarray(groups[key], dtype=np.float64) for key in keys])


def d_statistic(left: np.ndarray, right: np.ndarray) -> float:
    return float(ks_2samp(left, right, method="asymp").statistic)


def holm_adjust(p_values: dict[str, float]) -> dict[str, float]:
    ordered = sorted(p_values.items(), key=lambda item: item[1])
    adjusted: dict[str, float] = {}
    running = 0.0
    count = len(ordered)
    for rank, (key, value) in enumerate(ordered):
        current = min(1.0, (count - rank) * value)
        running = max(running, current)
        adjusted[key] = running
    return adjusted


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--residuals", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    document = json.loads(args.residuals.read_text(encoding="utf-8"))
    if document.get("formal_evaluation_called") is not False:
        raise ValueError("source residual export did not prove formal path exclusion")

    seed_seq = np.random.SeedSequence(SEED)
    child_seeds = seed_seq.spawn(len(COMPONENTS) * len(PAIRS))
    results: list[dict] = []
    p_family: dict[str, float] = {}
    for index, (component, pair) in enumerate(
        (component, pair) for component in COMPONENTS for pair in PAIRS
    ):
        rng = np.random.default_rng(child_seeds[index])
        left_orbit, right_orbit = pair.split("<->")
        directions = document["components"][component]["directions"]
        left = directions[f"{left_orbit}->{right_orbit}"]
        right = directions[f"{right_orbit}->{left_orbit}"]
        maps = {
            side: {
                kind: {
                    str(unit): np.asarray(values, dtype=np.float64)
                    for unit, values in row[f"{kind}_residuals_by_unit"].items()
                }
                for kind in ("candidate", "control")
            }
            for side, row in (("left", left), ("right", right))
        }
        for side in ("left", "right"):
            candidate_ids = set(maps[side]["candidate"])
            control_ids = set(maps[side]["control"])
            if candidate_ids != control_ids:
                raise ValueError(f"candidate/control unit membership differs: {component} {pair} {side}")
            for unit_id in candidate_ids:
                if maps[side]["candidate"][unit_id].shape != maps[side]["control"][unit_id].shape:
                    raise ValueError(f"candidate/control window alignment differs for {unit_id}")

        left_c = flatten(maps["left"]["candidate"])
        right_c = flatten(maps["right"]["candidate"])
        left_0 = flatten(maps["left"]["control"])
        right_0 = flatten(maps["right"]["control"])
        observed_candidate_d = d_statistic(left_c, right_c)
        observed_control_d = d_statistic(left_0, right_0)
        observed_delta = observed_candidate_d - observed_control_d
        stored = document["components"][component]["metric_replay"][pair]
        receipt_candidate_d = float(stored["stored"])

        bootstrap_delta = np.empty(BOOTSTRAP_REPS, dtype=np.float64)
        left_ids = np.asarray(sorted(maps["left"]["candidate"]))
        right_ids = np.asarray(sorted(maps["right"]["candidate"]))
        for draw in range(BOOTSTRAP_REPS):
            selected_left = rng.choice(left_ids, size=len(left_ids), replace=True).tolist()
            selected_right = rng.choice(right_ids, size=len(right_ids), replace=True).tolist()
            candidate_d = d_statistic(
                flatten(maps["left"]["candidate"], selected_left),
                flatten(maps["right"]["candidate"], selected_right),
            )
            control_d = d_statistic(
                flatten(maps["left"]["control"], selected_left),
                flatten(maps["right"]["control"], selected_right),
            )
            bootstrap_delta[draw] = candidate_d - control_d

        permutation_delta = np.empty(PERMUTATION_REPS, dtype=np.float64)
        for draw in range(PERMUTATION_REPS):
            permuted: dict[str, dict[str, dict[str, np.ndarray]]] = {"left": {}, "right": {}}
            for side, ids in (("left", left_ids), ("right", right_ids)):
                swap = rng.integers(0, 2, size=len(ids), dtype=np.int8).astype(bool)
                candidate_parts = []
                control_parts = []
                for unit_id, do_swap in zip(ids.tolist(), swap):
                    candidate_values = maps[side]["candidate"][unit_id]
                    control_values = maps[side]["control"][unit_id]
                    candidate_parts.append(control_values if do_swap else candidate_values)
                    control_parts.append(candidate_values if do_swap else control_values)
                permuted[side]["candidate"] = {"all": np.concatenate(candidate_parts)}
                permuted[side]["control"] = {"all": np.concatenate(control_parts)}
            candidate_d = d_statistic(
                permuted["left"]["candidate"]["all"],
                permuted["right"]["candidate"]["all"],
            )
            control_d = d_statistic(
                permuted["left"]["control"]["all"],
                permuted["right"]["control"]["all"],
            )
            permutation_delta[draw] = candidate_d - control_d

        p_worse = float((1 + np.count_nonzero(permutation_delta >= observed_delta)) / (PERMUTATION_REPS + 1))
        key = f"{component}:{pair}"
        p_family[key] = p_worse
        candidate_iid = ks_2samp(left_c, right_c, method="exact")
        control_iid = ks_2samp(left_0, right_0, method="exact")
        results.append(
            {
                "component": component,
                "orbit_pair": pair,
                "left_direction": f"{left_orbit}->{right_orbit}",
                "right_direction": f"{right_orbit}->{left_orbit}",
                "n_candidate_windows_left": int(left_c.size),
                "n_candidate_windows_right": int(right_c.size),
                "n_units_left": int(len(left_ids)),
                "n_units_right": int(len(right_ids)),
                "receipt_candidate_ks_d": receipt_candidate_d,
                "replayed_candidate_ks_d": observed_candidate_d,
                "replayed_control_ks_d": observed_control_d,
                "delta_ks_candidate_minus_control": observed_delta,
                "delta_ks_cluster_bootstrap_ci95": [float(x) for x in np.quantile(bootstrap_delta, [0.025, 0.975])],
                "cluster_swap_permutation_p_worse_one_sided": p_worse,
                "iid_window_candidate_ks_p_noninferential": float(candidate_iid.pvalue),
                "iid_window_control_ks_p_noninferential": float(control_iid.pvalue),
                "bootstrap_replicates": BOOTSTRAP_REPS,
                "permutation_replicates": PERMUTATION_REPS,
                "seed": SEED + index,
            }
        )

    adjusted = holm_adjust(p_family)
    for row in results:
        row["cluster_swap_permutation_p_holm_family6"] = adjusted[f"{row['component']}:{row['orbit_pair']}"]

    output = {
        "schema": "brphm-f8-unit-cluster-ks-analysis-v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "residual_export_sha256": sha256(args.residuals),
        "source_receipt_sha256": document["receipt_sha256"],
        "scope": "Source-validation residuals only; no formal/outer evaluation; analysis is exploratory because route selection used the source-validation data.",
        "methods": {
            "bootstrap": "Paired unit-cluster bootstrap within each target orbit; resample units with replacement and retain all windows; recompute D_candidate-D_control; percentile 95% interval.",
            "permutation": "For each unit within each orbit, swap the candidate/control residual vectors as one cluster under the paired exchangeability null; one-sided alternative delta-KS>0; Monte Carlo plus-one p-value.",
            "multiplicity": "Holm step-down across six component-by-orbit-pair candidate-minus-control tests.",
            "iid_reference": "SciPy exact two-sample KS p-values are included as nominal window-IID references only; overlapping windows violate that independence assumption and these values are not inferential claims.",
        },
        "parameters": {"bootstrap_replicates": BOOTSTRAP_REPS, "permutation_replicates": PERMUTATION_REPS, "seed": SEED},
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "complete", "tests": len(results), "output": str(args.output)}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
