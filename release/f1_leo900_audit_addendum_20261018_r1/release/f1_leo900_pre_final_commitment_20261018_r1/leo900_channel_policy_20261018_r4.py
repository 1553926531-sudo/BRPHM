"""Apply the frozen channel policy to an already normalized final payload.

Zero in normalized space is the frozen training mean. No statistic is fitted
to a final unit; finite inputs and every label/identity object are preserved.
"""
from __future__ import annotations


def validate_policy(config):
    policy = config.get("channels_policy", "strict")
    if policy not in ("strict", "impute_mean"):
        raise RuntimeError(f"unsupported channels policy: {policy!r}")
    return policy


def apply_channel_policy(payload, config):
    import numpy as np

    policy = validate_policy(config)
    x = payload["x"]
    channels = list(config["channels"])
    if (not isinstance(x, np.ndarray) or x.dtype != np.dtype("float32") or x.ndim != 3
            or x.shape[2] != len(channels) or payload["channels"] != channels
            or len(payload["rows"]) != len(x) or len(payload["y"]) != len(x)):
        raise RuntimeError("normalized final payload shape/dtype/channel/row contract mismatch")
    bad = ~np.isfinite(x)
    count = int(bad.sum())
    if policy == "strict" and count:
        raise RuntimeError(f"strict channels policy rejects {count} nonfinite normalized cells")
    corrected = x
    if count:
        corrected = x.copy()
        corrected[bad] = np.float32(0.)
    per_window = bad.sum(axis=(1, 2))
    per_unit = {}
    for row, number in zip(payload["rows"], per_window):
        uid = str(row["unit_id"])
        per_unit[uid] = per_unit.get(uid, 0) + int(number)
    return {**payload, "x": corrected,
            "channel_policy_audit": {
                "schema": "brphm-f1-normalized-channel-policy-v1", "policy": policy,
                "shape": list(x.shape), "imputed_cells": count,
                "per_channel": {name: int(n) for name, n in zip(channels, bad.sum(axis=(0, 1)))},
                "per_unit": per_unit, "replacement_normalized_value": 0.,
                "replacement_mean_source": "unchanged frozen norm_stats; no final statistic fitted",
                "finite_cells_action": "copied without arithmetic",
                "label_and_row_action": "original objects retained"}}
