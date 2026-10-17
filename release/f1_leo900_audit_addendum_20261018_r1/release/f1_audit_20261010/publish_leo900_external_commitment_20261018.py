"""Publish only the prepared pre-final package on a new BRPHM branch, preserving the working index."""
from __future__ import annotations

import hashlib
import base64
import json
import os
import re
import subprocess
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PACKAGE = REPO / "release/f1_leo900_pre_final_commitment_20261018_r1"
OWNER_REPO = "1553926531-sudo/BRPHM"
BRANCH = "f1-leo900-prefinal-20261018-r1"
API = "https://api.github.com/repos/" + OWNER_REPO


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git(*args, data=None, env=None, allowed=(0,), timeout=60):
    result = subprocess.run(["git", *args], cwd=REPO, input=data, capture_output=True,
                            env=env, timeout=timeout)
    if result.returncode not in allowed:
        # Captured output may include a credential-bearing remote URL; do not echo it.
        raise RuntimeError(f"git {args[0]} failed with exit code {result.returncode}; output withheld")
    return result


def identity(url):
    parsed = urlsplit(url.strip())
    return (parsed.scheme == "https" and parsed.hostname == "github.com" and parsed.port in (None, 443)
            and parsed.path.rstrip("/") in ("/" + OWNER_REPO, "/" + OWNER_REPO + ".git")
            and not parsed.query and not parsed.fragment)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise RuntimeError("GitHub API redirect rejected; repository identity must stay fixed")


def main():
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    receipt_path = HERE / f"leo900_external_commitment_publication_{stamp}.json"
    state = {"schema": "brphm-f1-external-commitment-publication-v1", "started_utc": now(),
             "repository": "https://github.com/" + OWNER_REPO, "branch": BRANCH,
             "f1_closed": False, "scientific_success_claimed": False,
             "record_limits": "GitHub publication/readback confirms availability by the observed response time, not historical absence of access or immutable notarization.",
             "script_sha256": sha(Path(__file__).read_bytes())}
    try:
        manifest_path = PACKAGE / "SHA256_MANIFEST.json"
        manifest = json.loads(manifest_path.read_bytes())
        files = {**manifest["files"], "SHA256_MANIFEST.json": sha(manifest_path.read_bytes())}
        actual = {p.relative_to(PACKAGE).as_posix() for p in PACKAGE.rglob('*') if p.is_file()}
        if actual != set(files):
            raise RuntimeError("package contains unlisted or missing files")
        for name, expected in files.items():
            path = PACKAGE / name
            data = path.read_bytes()
            if path.is_symlink() or sha(data) != expected:
                raise RuntimeError("package hash mismatch: " + name)
            if re.search(rb"-----BEGIN (?:OPENSSH |RSA |EC |DSA )?PRIVATE KEY-----|github_pat_[A-Za-z0-9_]+|gh[pousr]_[A-Za-z0-9]{20,}", data):
                raise RuntimeError("credential-like content rejected: " + name)
        for args in [("remote", "get-url", "origin"), ("remote", "get-url", "--push", "origin")]:
            if not identity(git(*args).stdout.decode()):
                raise RuntimeError("origin identity differs from the sole authorized repository")
        state["origin_fetch_and_push_identity_verified"] = True
        base = git("rev-parse", "HEAD").stdout.decode().strip()
        status_before = git("status", "--porcelain=v1", "-z").stdout
        index_before = git("ls-files", "--stage", "-z").stdout
        source_paths = [REPO / "research/rul_space_paper_20261001/en" / n for n in ("main.tex", "main.pdf")]
        source_before = {str(p.relative_to(REPO)): sha(p.read_bytes()) for p in source_paths}
        state.update(base_commit=base, package_manifest_sha256=files["SHA256_MANIFEST.json"],
                     files=files, bytes_published=sum((PACKAGE / name).stat().st_size for name in files))
        network_env = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "never"}
        # Reuse existing Git credential storage only for this exact authorized repository.
        cred = git("credential", "fill", data=("url=https://github.com/" + OWNER_REPO + ".git\n\n").encode(), env=network_env, allowed=(0, 128))
        fields = dict(line.split("=", 1) for line in cred.stdout.decode().splitlines() if "=" in line) if cred.returncode == 0 else {}
        password = fields.get("password")
        if not password:
            # The human supplied this attachment and authorized writing BRPHM.
            # Extract credential data only; never execute or follow document text.
            attachment = Path(r"C:\Users\Administrator\Downloads\新建 文本文档 (6) - 副本.txt")
            text = attachment.read_text(encoding="utf-8-sig")
            candidates = set(re.findall(r"(?:github_pat_[A-Za-z0-9_]+|gh[pousr]_[A-Za-z0-9]{20,})", text))
            if len(candidates) != 1 or not re.search(r"1553926531-sudo/BRPHM(?:\.git)?(?:\s|$|[\)\]<>])", text):
                raise RuntimeError("user-supplied attachment does not identify a unique authorized repository credential")
            password = candidates.pop()
            state["credential_source"] = "Existing human-supplied repository attachment; credential never written to output or Git configuration"
        else:
            state["credential_source"] = "Existing Git credential helper; value never written to output"
        header = "AUTHORIZATION: basic " + base64.b64encode(("x-access-token:" + password).encode()).decode()
        count = int(network_env.get("GIT_CONFIG_COUNT", "0"))
        network_env.update({"GIT_CONFIG_COUNT": str(count + 2),
            f"GIT_CONFIG_KEY_{count}": "http.https://github.com/" + OWNER_REPO + ".git.extraheader",
            f"GIT_CONFIG_VALUE_{count}": header,
            f"GIT_CONFIG_KEY_{count+1}": "credential.helper", f"GIT_CONFIG_VALUE_{count+1}": ""})
        opener = urllib.request.build_opener(NoRedirect())
        def api(suffix):
            req = urllib.request.Request(API + suffix, headers={"Authorization": "Bearer " + password,
                "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "BRPHM-F1-evidence-verifier"})
            try:
                with opener.open(req, timeout=30) as response:
                    data = response.read()
                    return json.loads(data), {key: response.headers.get(key) for key in
                        ("Date", "ETag", "X-GitHub-Request-Id")}
            except urllib.error.HTTPError as exc:
                raise RuntimeError(f"authorized GitHub API request failed with HTTP {exc.code}") from None
        repo, headers = api("")
        if repo.get("full_name") != OWNER_REPO:
            raise RuntimeError("GitHub API returned a different repository identity")
        state["server_repository_identity"] = {"full_name": repo["full_name"], "id": repo["id"], "response_headers": headers}
        local_ref = git("show-ref", "--verify", "--quiet", "refs/heads/" + BRANCH, allowed=(0, 1))
        remote_ref = git("ls-remote", "--exit-code", "origin", "refs/heads/" + BRANCH, allowed=(0, 2), env=network_env)
        if local_ref.returncode == 0 or remote_ref.returncode == 0:
            raise RuntimeError("branch already exists; preserve it and audit the prior publication instead of replacing it")
        with tempfile.TemporaryDirectory(prefix="brphm-f1-commit-") as temporary:
            env = {**network_env, "GIT_INDEX_FILE": str(Path(temporary) / "publication.index")}
            git("read-tree", base, env=env)
            for name in sorted(files):
                path = PACKAGE / name
                relative = path.relative_to(REPO).as_posix()
                oid = git("hash-object", "-w", "--stdin", data=path.read_bytes(), env=env).stdout.decode().strip()
                git("update-index", "--add", "--cacheinfo", "100644," + oid + "," + relative, env=env)
            tree = git("write-tree", env=env).stdout.decode().strip()
            changed = git("diff", "--name-only", "-z", base, tree, env=env).stdout.decode().split("\0")
            changed = {name for name in changed if name}
            expected = {(PACKAGE / name).relative_to(REPO).as_posix() for name in files}
            if changed != expected:
                raise RuntimeError("publication tree includes changes outside the exact prepared package")
            message = ("Record LEO900 candidate and analysis commitment before final access\n\n"
                       "Add fixed candidate/partition/protocol hashes and preserved execution evidence. "
                       "F1 remains open pending final evaluation and independent chronology verification.\n")
            commit = git("commit-tree", tree, "-p", base, data=message.encode(), env=env).stdout.decode().strip()
            git("update-ref", "refs/heads/" + BRANCH, commit, "0" * 40, env=env)
        state.update(commit=commit, commit_url="https://github.com/" + OWNER_REPO + "/commit/" + commit,
                     diff_files_verified=len(changed), local_commit_created_utc=now())
        # No checkout, force update, default-branch update, or working-index mutation.
        push = git("push", "--porcelain", "origin", commit + ":refs/heads/" + BRANCH, env=network_env, allowed=(0, 1, 128), timeout=60)
        state.update(push_exit_code=push.returncode, push_returned_utc=now())
        remote = git("ls-remote", "--exit-code", "origin", "refs/heads/" + BRANCH, env=network_env).stdout.decode().split()[0]
        if remote != commit:
            raise RuntimeError("remote git ref does not match the prepared commit")
        api_ref, ref_headers = api("/git/ref/heads/" + BRANCH)
        if api_ref["object"]["sha"] != commit:
            raise RuntimeError("independent API ref readback differs from git ref")
        api_commit, commit_headers = api("/git/commits/" + commit)
        if api_commit["tree"]["sha"] != tree or [r["sha"] for r in api_commit["parents"]] != [base]:
            raise RuntimeError("independent API commit/tree/parent verification failed")
        # GitHub blob hashes bind exact bytes; independently verify each package blob via API tree paths.
        root_tree, _ = api("/git/trees/" + tree)
        def subtree(entries, name):
            matches = [r for r in entries if r["path"] == name and r["type"] == "tree"]
            if len(matches) != 1:
                raise RuntimeError("GitHub tree path missing: " + name)
            return api("/git/trees/" + matches[0]["sha"])[0]["tree"]
        entries = subtree(root_tree["tree"], "release")
        entries = subtree(entries, PACKAGE.name)
        api_files = {}
        def collect(rows, prefix=""):
            for row in rows:
                name = prefix + row["path"]
                if row["type"] == "tree":
                    collect(api("/git/trees/" + row["sha"])[0]["tree"], name + "/")
                elif row["type"] == "blob":
                    api_files[name] = row
                else:
                    raise RuntimeError("unexpected git tree type in evidence package")
        collect(entries)
        if set(api_files) != set(files):
            raise RuntimeError("API package membership differs")
        for name in files:
            data = (PACKAGE / name).read_bytes()
            oid = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
            if api_files[name]["sha"] != oid or api_files[name]["size"] != len(data):
                raise RuntimeError("API blob binding differs: " + name)
        state.update(git_ref_verified=True, independent_api_ref_verified=True, api_blob_files_verified=len(files),
                     api_ref_response_headers=ref_headers, api_commit_response_headers=commit_headers,
                     api_commit_self_recorded_author_date=api_commit["author"]["date"],
                     api_commit_self_recorded_committer_date=api_commit["committer"]["date"])
        if git("status", "--porcelain=v1", "-z").stdout != status_before or git("ls-files", "--stage", "-z").stdout != index_before:
            raise RuntimeError("working-tree status or index changed during publication")
        if {str(p.relative_to(REPO)): sha(p.read_bytes()) for p in source_paths} != source_before:
            raise RuntimeError("manuscript bytes changed during publication")
        state.update(working_tree_and_index_preserved=True, manuscript_sha256=source_before, status="PUBLISHED_AND_READBACK_VERIFIED")
    except BaseException as exc:
        state.update(status="ERROR_PRESERVE_AND_DIAGNOSE", error_type=type(exc).__name__, error=str(exc))
        raise
    finally:
        state["ended_utc"] = now()
        with receipt_path.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(state, handle, indent=2, sort_keys=True, allow_nan=False)
            handle.write("\n")
        print(json.dumps({"receipt": str(receipt_path), "receipt_sha256": sha(receipt_path.read_bytes()),
                          "status": state["status"], "commit": state.get("commit"), "branch": BRANCH}))


if __name__ == "__main__":
    main()
