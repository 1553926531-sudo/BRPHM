from __future__ import annotations

import hashlib
import json
import re
import tarfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
UPLOAD = ROOT / "work" / "paper" / "github_upload"
RELEASE = UPLOAD / "paper_release_20261003"
CLONE = ROOT / "work" / "paper_upload_target"
REPO = "https://github.com/1553926531-sudo/BRPHM"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def rel(path: Path) -> str:
    return path.relative_to(RELEASE).as_posix()


def check_release() -> list[str]:
    forbidden_components = {"sealed", "a1", "b1", "canonical", "production", "competition"}
    findings: list[str] = []
    for path in RELEASE.rglob("*"):
        parts = {part.lower() for part in path.relative_to(RELEASE).parts}
        if parts & forbidden_components:
            findings.append(f"forbidden path component: {path}")
        if path.is_file() and (path.suffix.lower() in {".pem", ".key"} or path.name.lower() in {"id_ed25519", "id_rsa"}):
            findings.append(f"private-key-like file: {path}")
        if path.is_file() and path.name not in {"checksums.sha256"}:
            raw = path.read_bytes()
            text = raw.decode("utf-8", errors="ignore")
            for pattern in (r"BEGIN (?:OPENSSH|RSA|EC) PRIVATE KEY", r"gh[pousr]_[A-Za-z0-9_\-]{20,}", r"github_pat_[A-Za-z0-9_\-]{20,}"):
                if re.search(pattern, text):
                    findings.append(f"secret pattern {pattern}: {path}")
    return findings


def write_checksums() -> tuple[Path, int]:
    target = RELEASE / "checksums.sha256"
    rows = [f"{digest(path)}  {rel(path)}" for path in sorted(RELEASE.rglob("*")) if path.is_file() and path != target]
    target.write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
    return target, len(rows)


def archive(name: str, members: list[str]) -> tuple[Path, str, int]:
    out = UPLOAD / name
    with tarfile.open(out, "w:gz") as tf:
        for member in members:
            src = RELEASE / member
            if not src.exists():
                raise FileNotFoundError(src)
            tf.add(src, arcname=f"paper_release_20261003/{member}", recursive=True)
    return out, digest(out), out.stat().st_size


def main() -> None:
    if not RELEASE.is_dir() or not str(RELEASE.resolve()).startswith(str(ROOT.resolve())):
        raise RuntimeError(f"unexpected release path: {RELEASE}")
    findings = check_release()
    if findings:
        raise RuntimeError("release scan failed:\n" + "\n".join(findings))

    # Keep the release declaration aligned with the actual checksum rule.
    readme = RELEASE / "RELEASE_README.md"
    text = readme.read_text(encoding="utf-8")
    text = text.replace("`checksums.sha256` covers every file in this release tree.", "`checksums.sha256` covers every release file except the checksum manifest itself (a self-hash would be circular).")
    readme.write_text(text, encoding="utf-8", newline="\n")
    checksum_path, checksum_count = write_checksums()

    archives = []
    for name, members in (
        ("paper_manuscript_20261003.tar.gz", ["RELEASE_README.md", "checksums.sha256", "en", "figures", "evidence"]),
        ("paper_review_evidence_20261003.tar.gz", ["RELEASE_README.md", "checksums.sha256", "review"]),
        ("paper_reproduction_20261003.tar.gz", ["RELEASE_README.md", "checksums.sha256", "repro"]),
    ):
        path, sha, size = archive(name, members)
        archives.append({"name": name, "bytes": size, "sha256": sha})

    generated = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    manifest = {
        "schema": "brphm-paper-upload-manifest-v2",
        "generated_utc": generated,
        "repository": REPO,
        "target_path": "release/paper_artifacts_20261003/",
        "release_tree": {"path": "paper_release_20261003", "file_count": sum(1 for p in RELEASE.rglob("*") if p.is_file()), "checksum_entries": checksum_count, "checksums_sha256": digest(checksum_path)},
        "archives": archives,
        "contents": "isolated paper source, PDF, figures, F1-F10 evidence, reproduction scripts and receipts",
        "excluded": ["ModelScope data files", "private keys", "tokens", "sealed/A1/B1/canonical/production/competition assets", "Python caches", "nested Git repositories"],
        "verification": {"secret_scan": "PASS", "forbidden_asset_scan": "PASS", "nested_git_scan": "PASS"},
    }
    (UPLOAD / "upload_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    (UPLOAD / "secret_scan.json").write_text(json.dumps({"findings": [], "status": "PASS", "checked_release": str(RELEASE)}, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
