from __future__ import annotations

import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PAPER = ROOT / "work" / "paper"
RELEASE = PAPER / "github_upload" / "paper_release_20261003"

if not RELEASE.is_dir() or not str(RELEASE.resolve()).startswith(str(ROOT.resolve())):
    raise RuntimeError(f"refusing unexpected release path: {RELEASE}")

def remove_tree(path: Path) -> None:
    """Remove generated tree even when a nested checkout left read-only files."""
    if not path.exists():
        return

    def onerror(func, failed_path, exc_info):
        try:
            os.chmod(failed_path, 0o700)
            func(failed_path)
        except OSError:
            raise

    shutil.rmtree(path, onerror=onerror)


for name in ("review", "repro", "figures", "evidence"):
    target = RELEASE / name
    if target.exists():
        remove_tree(target)
    shutil.copytree(PAPER / name, target)

for path in sorted(RELEASE.rglob("*"), reverse=True):
    if path.is_dir() and path.name in {".git", "__pycache__"}:
        remove_tree(path)

for name in ("main.tex", "main.pdf", "main.log", "main_extracted.txt"):
    shutil.copy2(PAPER / "en" / name, RELEASE / "en" / name)

# The frozen reference is a small, hash-bound input required by the F5/F6
# replay tests.  It contains no raw dataset bytes and is safe to publish with
# the isolated evidence package.
reference = ROOT / "reference_summary_remote.json"
if reference.exists():
    shutil.copy2(reference, RELEASE / reference.name)

# Keep the editable companion document when it exists.
docx = PAPER / "en" / "paper_en.docx"
if docx.exists():
    shutil.copy2(docx, RELEASE / "en" / docx.name)

files = [p for p in RELEASE.rglob("*") if p.is_file()]
bad_dirs = [p for p in RELEASE.rglob("*") if p.is_dir() and p.name in {".git", "__pycache__"}]
print({"release": str(RELEASE), "files": len(files), "nested_git_dirs": len(bad_dirs)})
if bad_dirs:
    raise RuntimeError(f"forbidden directories remain: {bad_dirs}")
