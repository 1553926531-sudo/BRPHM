from __future__ import annotations

"""Unit-first relative TCN with source-fit centering and unit-balanced L1 loss.

This candidate changes only the training loss from the audited SmoothL1
runner. All source-gate, formal, postprocessing, and provenance rules remain
bound to the existing isolated implementation.
"""

import argparse
import json
from pathlib import Path

import numpy as np

import temporal_tcn_unit_first_residual_centered_source_gate_20261001 as centered


def fit_model_unit_first_l1(sequences, targets, rows, cfg, seed, device_name):
    """Fit the same unit-first TCN with weighted absolute error."""
    import torch

    sequences = centered.unit_first.append_unit_first(sequences, rows)
    centered.b.seed_all(seed)
    device = torch.device(device_name)
    tmax = max(float(row.get("t_end", 0.0)) for row in rows)
    x = torch.from_numpy(np.transpose(sequences, (0, 2, 1)))
    y = torch.from_numpy(np.asarray(targets, dtype=np.float32).reshape(-1))
    ages = torch.from_numpy(centered.b._age(rows, tmax))
    weights = torch.from_numpy(centered.b.unit_weights(rows))
    model = centered.b._build_torch_model(int(sequences.shape[2]), cfg).to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=float(cfg["lr"]), weight_decay=float(cfg["weight_decay"])
    )
    generator = torch.Generator().manual_seed(seed)
    dataset = torch.utils.data.TensorDataset(x, ages, y, weights)
    loader = torch.utils.data.DataLoader(
        dataset, batch_size=min(256, len(dataset)), shuffle=True, generator=generator
    )
    model.train()
    for _ in range(max(1, int(cfg["epochs"]))):
        for xb, ab, yb, wb in loader:
            optimizer.zero_grad(set_to_none=True)
            prediction = model(xb.to(device), ab.to(device))
            loss = torch.nn.functional.l1_loss(
                prediction, yb.to(device), reduction="none"
            )
            loss = (loss * wb.to(device)).mean()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
    model.eval()
    return model, tmax


def run(args: argparse.Namespace) -> dict:
    centered.r.fit_model_relative = fit_model_unit_first_l1
    centered.b.CONFIG_CURRENT = centered.b.CONFIG
    centered.b.fit_source_predictions = centered.fit_source_predictions_centered
    original_formal = centered.g._fit_relative_formal
    centered.g._fit_relative_formal = centered.fit_relative_formal_centered
    try:
        receipt = centered.fine.run(args)
    finally:
        centered.g._fit_relative_formal = original_formal
    receipt["schema"] = "brphm-temporal-tcn-unit-first-residual-centered-l1-source-gate-20261001"
    receipt["method_id"] = "source_only_temporal_tcn_unit_first_relative_residual_centered_l1"
    receipt["source_protocol"]["loss"] = "unit-balanced L1 on normalized RUL"
    receipt["source_protocol"]["training_loss"] = "absolute error"
    receipt["outer_selection_independent"] = True
    for component in receipt["components"].values():
        if component.get("selected_candidate_id") is not None:
            component["selected_candidate_id"] = receipt["method_id"]
    args.output.joinpath("receipt.json").write_text(
        json.dumps(receipt, ensure_ascii=True, indent=2) + "\n", encoding="utf-8"
    )
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()
    receipt = run(args)
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
