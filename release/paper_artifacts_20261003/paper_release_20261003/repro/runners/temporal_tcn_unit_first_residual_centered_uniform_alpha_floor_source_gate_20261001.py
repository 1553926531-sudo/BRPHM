from __future__ import annotations

"""Unit-first residual-centered TCN with a uniform source-only alpha floor."""

import argparse
import json
from pathlib import Path

import temporal_tcn_unit_first_residual_centered_source_gate_20261001 as centered


ALPHA_FLOOR = 1e-5


def select_route_uniform_floor(scores: list[dict]) -> dict | None:
    eligible = [item for item in scores if item["gate"]["passes"]]
    constrained = [
        item
        for item in eligible
        if all(
            float(value) >= ALPHA_FLOOR
            for value in item["route"]["alpha_by_target"].values()
        )
    ]
    if not constrained:
        return None
    return min(
        constrained,
        key=lambda item: (
            sum(float(value) for value in item["route"]["alpha_by_target"].values()),
            max(float(value) for value in item["route"]["alpha_by_target"].values()),
            float(item["gate"]["worst_residual_ks"]),
            float(item["gate"]["mean_rmse"]),
            float(item["gate"]["mean_mae"]),
            str(item["route"]["route_id"]),
        ),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()

    implementation = centered.fine.implementation
    original_selector = implementation.select_route
    implementation.select_route = select_route_uniform_floor
    original_formal = centered.g._fit_relative_formal
    centered.b.CONFIG_CURRENT = centered.b.CONFIG
    centered.b.fit_source_predictions = centered.fit_source_predictions_centered
    centered.g._fit_relative_formal = centered.fit_relative_formal_centered
    try:
        receipt = centered.fine.run(args)
    finally:
        implementation.select_route = original_selector
        centered.g._fit_relative_formal = original_formal
    receipt["schema"] = "brphm-temporal-tcn-unit-first-residual-centered-uniform-alpha-floor-source-gate-20261001"
    receipt["method_id"] = "source_only_temporal_tcn_unit_first_relative_residual_centered_uniform_alpha_floor"
    receipt["source_protocol"]["selection"] = (
        "source-gate-only uniform target-orbit alpha floor >= 1e-5 for BAT and RWA; "
        "then minimum total alpha and existing source-only tie-breaks"
    )
    receipt["source_protocol"]["uniform_alpha_floor"] = ALPHA_FLOOR
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
