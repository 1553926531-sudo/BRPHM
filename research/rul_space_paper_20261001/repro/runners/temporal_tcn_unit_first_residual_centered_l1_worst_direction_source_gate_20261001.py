from __future__ import annotations

"""L1 unit-first TCN with source-only worst-direction route selection."""

import argparse
import json
from pathlib import Path

import temporal_tcn_unit_first_residual_centered_l1_source_gate_20261001 as l1


def select_route_worst_direction(scores: list[dict]) -> dict | None:
    """Choose a source-gate route by its worst transfer direction."""
    eligible = [item for item in scores if item["gate"]["passes"]]
    if not eligible:
        return None

    def key(item: dict):
        direction_records = [
            record for record in item["records"] if "direction" in record
        ]
        worst_rmse = max(float(record["metrics"]["rmse"]) for record in direction_records)
        worst_mae = max(float(record["metrics"]["mae"]) for record in direction_records)
        return (
            worst_rmse,
            worst_mae,
            float(item["gate"]["worst_residual_ks"]),
            sum(float(value) for value in item["route"]["alpha_by_target"].values()),
            max(float(value) for value in item["route"]["alpha_by_target"].values()),
            str(item["route"]["route_id"]),
        )

    return min(eligible, key=key)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()
    implementation = l1.centered.fine.implementation
    original_selector = implementation.select_route
    implementation.select_route = select_route_worst_direction
    try:
        receipt = l1.run(args)
    finally:
        implementation.select_route = original_selector
    receipt["schema"] = "brphm-temporal-tcn-unit-first-residual-centered-l1-worst-direction-source-gate-20261001"
    receipt["method_id"] = "source_only_temporal_tcn_unit_first_relative_residual_centered_l1_worst_direction"
    receipt["source_protocol"]["selection"] = (
        "source-gate-only route selection by worst source-direction RMSE, worst source-direction MAE, "
        "worst residual-KS, then total alpha; outer-independent"
    )
    receipt["outer_selection_independent"] = True
    for component in receipt["components"].values():
        if component.get("selected_candidate_id") is not None:
            component["selected_candidate_id"] = receipt["method_id"]
    args.output.joinpath("receipt.json").write_text(
        json.dumps(receipt, ensure_ascii=True, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": "complete",
                "output": str((args.output / "receipt.json").resolve()),
                "formal_eligible": receipt["formal_eligible"],
            },
            ensure_ascii=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
