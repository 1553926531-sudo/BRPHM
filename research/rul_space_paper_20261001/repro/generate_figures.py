from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
PAPER = Path(__file__).resolve().parent
EVIDENCE = json.loads((PAPER / "evidence" / "evidence_summary.json").read_text(encoding="utf-8"))
FIG = PAPER / "figures"
FIG.mkdir(parents=True, exist_ok=True)

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 8,
        "axes.titlesize": 9,
        "axes.labelsize": 8,
        "legend.fontsize": 7,
        "figure.dpi": 160,
        "savefig.bbox": "tight",
    }
)


def save(fig, name: str) -> None:
    fig.savefig(FIG / f"{name}.pdf")
    fig.savefig(FIG / f"{name}.png", dpi=300)
    plt.close(fig)


folds = EVIDENCE["final_formal_folds"]
labels = [f"{row['component'].upper()}-{row['test_orbit'].replace('LEO', '')}" for row in folds]
rmse_delta = np.array([row["rmse_delta"] for row in folds], dtype=float)
mae_delta = np.array([row["mae_delta"] for row in folds], dtype=float)
x = np.arange(len(labels))
fig, ax = plt.subplots(figsize=(6.7, 2.6))
width = 0.36
ax.bar(x - width / 2, rmse_delta, width, label="RMSE delta", color="#0072B2")
ax.bar(x + width / 2, mae_delta, width, label="MAE delta", color="#D55E00")
ax.axhline(0, color="#222222", lw=0.8)
ax.set_xticks(x, labels)
ax.set_ylabel("Candidate - frozen reference")
ax.set_title("Formal outer-fold deltas of the promoted candidate")
ax.ticklabel_format(axis="y", style="sci", scilimits=(-2, 2))
ax.legend(ncol=2, frameon=False, loc="lower left")
ax.grid(axis="y", alpha=0.22)
save(fig, "formal_deltas")


methods = EVIDENCE["methods"]
names = [
    "Unit-first TCN",
    "Residual-centered",
    "L1 residual",
    "L1 worst-direction",
    "RWA LEO550 floor",
    "Uniform alpha floor",
    "GRU",
]
counts = [int(item["promotion_failure_count"]) for item in methods]
colors = ["#BDBDBD"] * (len(counts) - 1) + ["#009E73"]
fig, ax = plt.subplots(figsize=(6.7, 2.7))
y = np.arange(len(names))
ax.barh(y, counts, color=colors)
ax.set_yticks(y, names)
ax.invert_yaxis()
ax.set_xlabel("Formal promotion failures (fold count)")
ax.set_title("Candidate progression under the fixed six-fold promotion gate")
ax.set_xlim(0, max(counts) + 0.8)
for yi, value in zip(y, counts):
    ax.text(value + 0.08, yi, str(value), va="center")
ax.grid(axis="x", alpha=0.22)
save(fig, "method_progression")


reference = {(item["component"], item["test_orbit"]): item["metrics"] for item in EVIDENCE["reference_results"]}
candidate = {(item["component"], item["test_orbit"]): item for item in folds}
ratios = np.array(
    [candidate[key]["rmse"] / reference[key]["rmse"] for key in candidate], dtype=float
)
labels = [f"{c.upper()}-{o.replace('LEO', '')}" for c, o in candidate]
fig, ax = plt.subplots(figsize=(6.7, 2.6))
colors = ["#009E73" if value <= 1.0 else "#D55E00" for value in ratios]
ax.bar(np.arange(len(labels)), ratios, color=colors)
ax.axhline(1.0, color="#222222", lw=0.8, ls="--")
ax.set_xticks(np.arange(len(labels)), labels)
ax.set_ylabel("RMSE / reference RMSE")
ax.set_title("Promoted candidate relative RMSE on each formal fold")
ax.set_ylim(min(0.99, ratios.min() - 0.001), 1.002)
ax.grid(axis="y", alpha=0.22)
save(fig, "relative_rmse")


fig, ax = plt.subplots(figsize=(6.7, 2.7))
boxes = [
    (0.05, 0.70, 0.20, 0.16, "Registered\nsource tensors"),
    (0.30, 0.70, 0.20, 0.16, "Unit-first\nrelative TCN"),
    (0.55, 0.70, 0.20, 0.16, "Source-only\nalpha route"),
    (0.80, 0.70, 0.15, 0.16, "Formal\nouter"),
    (0.30, 0.26, 0.20, 0.16, "Source gate:\n6 directions + KS"),
    (0.55, 0.26, 0.20, 0.16, "Promotion:\n6 folds vs reference"),
]
for x0, y0, w, h, label in boxes:
    face = "#E6F2F8" if y0 > 0.5 else "#FCE8E6"
    rect = plt.Rectangle((x0, y0), w, h, facecolor=face, edgecolor="#444444", lw=0.8)
    ax.add_patch(rect)
    ax.text(x0 + w / 2, y0 + h / 2, label, ha="center", va="center")
for x0, y0, x1, y1 in [(0.25, 0.78, 0.30, 0.78), (0.50, 0.78, 0.55, 0.78), (0.75, 0.78, 0.80, 0.78), (0.40, 0.70, 0.40, 0.42), (0.65, 0.70, 0.65, 0.42), (0.75, 0.34, 0.80, 0.78)]:
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops={"arrowstyle": "->", "lw": 0.8, "color": "#555555"})
ax.text(0.5, 0.08, "All selection uses source labels only; outer labels are evaluated once after handoff.", ha="center", fontsize=8)
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")
save(fig, "evaluation_protocol")

