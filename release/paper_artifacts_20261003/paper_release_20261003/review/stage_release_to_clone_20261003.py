from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
UPLOAD = ROOT / "work" / "paper" / "github_upload"
RELEASE = UPLOAD / "paper_release_20261003"
CLONE = ROOT / "work" / "paper_upload_target"
TARGET = CLONE / "release" / "paper_artifacts_20261003"

if not (CLONE / ".git").is_dir():
    raise RuntimeError(f"refusing non-git target: {CLONE}")
if not RELEASE.is_dir() or not str(TARGET.resolve()).startswith(str(CLONE.resolve())):
    raise RuntimeError(f"unexpected target: {TARGET}")

if TARGET.exists():
    shutil.rmtree(TARGET)
TARGET.mkdir(parents=True)
shutil.copytree(RELEASE, TARGET / RELEASE.name)
for name in (
    "paper_manuscript_20261003.tar.gz",
    "paper_review_evidence_20261003.tar.gz",
    "paper_reproduction_20261003.tar.gz",
    "upload_manifest.json",
    "secret_scan.json",
):
    shutil.copy2(UPLOAD / name, TARGET / name)

files = [p for p in TARGET.rglob("*") if p.is_file()]
bad = [p for p in TARGET.rglob("*") if p.is_dir() and p.name in {".git", "__pycache__"}]
print({"target": str(TARGET), "files": len(files), "bad_dirs": len(bad)})
if bad:
    raise RuntimeError(f"forbidden generated directories: {bad}")
