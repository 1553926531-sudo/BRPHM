from __future__ import annotations

"""Source-only GRU candidate with the registered transfer/formal gates.

This runner changes the temporal learner family while keeping the data,
normalization, unit weighting, control binding, and outer protocol fixed.
"""

import json
from pathlib import Path

import numpy as np

import temporal_tcn_source_gate as base


GRU_CONFIG = {
    "bat": {
        "hidden": 32,
        "layers": 2,
        "dropout": 0.10,
        "lr": 1e-3,
        "weight_decay": 1e-4,
        "epochs": 70,
        "postprocess": "isotonic_nonincreasing",
    },
    "rwa": {
        "hidden": 32,
        "layers": 2,
        "dropout": 0.10,
        "lr": 1e-3,
        "weight_decay": 1e-4,
        "epochs": 70,
        "postprocess": "causal_running_min",
    },
}


def _build_gru(input_channels: int, cfg: dict):
    import torch
    from torch import nn

    class Net(nn.Module):
        def __init__(self):
            super().__init__()
            self.input = nn.Sequential(
                nn.Linear(input_channels, int(cfg["hidden"])),
                nn.LayerNorm(int(cfg["hidden"])),
                nn.SiLU(),
            )
            self.gru = nn.GRU(
                input_size=int(cfg["hidden"]),
                hidden_size=int(cfg["hidden"]),
                num_layers=int(cfg["layers"]),
                dropout=float(cfg["dropout"]) if int(cfg["layers"]) > 1 else 0.0,
                batch_first=True,
            )
            self.head = nn.Sequential(
                nn.Linear(int(cfg["hidden"]) * 2 + 3, int(cfg["hidden"])),
                nn.SiLU(),
                nn.Linear(int(cfg["hidden"]), 1),
            )

        def forward(self, values, age):
            values = torch.nan_to_num(values, nan=0.0, posinf=0.0, neginf=0.0)
            hidden, _ = self.gru(self.input(values))
            pooled = torch.cat((hidden[:, -1, :], hidden.mean(dim=1)), dim=1)
            age = age.reshape(-1, 1).to(values.dtype)
            age_features = torch.cat((age, age * age, torch.sqrt(torch.clamp(age, min=0.0))), dim=1)
            return torch.sigmoid(self.head(torch.cat((pooled, age_features), dim=1))).reshape(-1)

    return Net()


def fit_model_gru(sequences, targets, rows, cfg, seed, device_name):
    import torch

    base.seed_all(seed)
    device = torch.device(device_name)
    tmax = max(float(row.get("t_end", 0.0)) for row in rows)
    values = torch.from_numpy(np.asarray(sequences, dtype=np.float32))
    ages = torch.from_numpy(base._age(rows, tmax))
    target = torch.from_numpy(np.asarray(targets, dtype=np.float32).reshape(-1))
    weights = torch.from_numpy(base.unit_weights(rows))
    model = _build_gru(int(sequences.shape[2]), cfg).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=float(cfg["lr"]), weight_decay=float(cfg["weight_decay"]))
    generator = torch.Generator().manual_seed(seed)
    dataset = torch.utils.data.TensorDataset(values, ages, target, weights)
    loader = torch.utils.data.DataLoader(dataset, batch_size=min(256, len(dataset)), shuffle=True, generator=generator)
    model.train()
    for _ in range(max(1, int(cfg["epochs"]))):
        for xb, ab, yb, wb in loader:
            optimizer.zero_grad(set_to_none=True)
            prediction = model(xb.to(device), ab.to(device))
            loss = torch.nn.functional.smooth_l1_loss(prediction, yb.to(device), reduction="none")
            loss = (loss * wb.to(device)).mean()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
    model.eval()
    return model, tmax


def predict_models_gru(models, sequences, rows, center, scale, device_name):
    import torch

    normalized = ((np.asarray(sequences, dtype=np.float32) - center[None, None, :]) / scale[None, None, :]).astype(np.float32)
    values = torch.from_numpy(normalized)
    outputs = []
    device = torch.device(device_name)
    for model, tmax in models:
        with torch.no_grad():
            outputs.append(model(values.to(device), torch.from_numpy(base._age(rows, tmax)).to(device)).cpu().numpy())
    return np.median(np.stack(outputs, axis=0), axis=0).astype(np.float32)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()
    original_config = base.CONFIG
    original_fit, original_predict = base.fit_model, base.predict_models
    base.CONFIG = GRU_CONFIG
    base.fit_model, base.predict_models = fit_model_gru, predict_models_gru
    try:
        receipt = base.run(args)
    finally:
        base.CONFIG = original_config
        base.fit_model, base.predict_models = original_fit, original_predict
    receipt["schema"] = "brphm-temporal-gru-source-gate-20261001"
    receipt["method_id"] = "source_only_temporal_gru_unit_weighted"
    receipt["source_protocol"]["input_representation"] = "source-standardized telemetry"
    receipt["source_protocol"]["learner"] = "two-layer unidirectional GRU with last-state and mean-state pooling"
    receipt["source_protocol"]["configuration"] = GRU_CONFIG
    receipt["outer_selection_independent"] = True
    for component in receipt["components"].values():
        if component.get("selected_candidate_id") is not None:
            component["selected_candidate_id"] = receipt["method_id"]
    args.output.joinpath("receipt.json").write_text(json.dumps(receipt, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "complete", "output": str((args.output / "receipt.json").resolve()), "formal_eligible": receipt["formal_eligible"]}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
