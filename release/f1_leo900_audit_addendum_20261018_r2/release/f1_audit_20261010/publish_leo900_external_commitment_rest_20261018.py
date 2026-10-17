"""Publish the fixed pre-final package using GitHub's Git Data API.

Only a new branch in the explicitly authorized BRPHM repository can be created.
The package, working index, dirty files, and default branch are preserved. The
local Git object implementation independently checks the exact server tree and
commit objects. An exclusive transaction record supports read-first recovery
after an interrupted request; no branch is replaced or force updated.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from publish_leo900_external_commitment_20261018 import (
    API, BRANCH, HERE, NoRedirect, OWNER_REPO, PACKAGE, REPO, git, identity, sha,
)

BASE = "ed051819e5e97a205fb0b076bc79b3cd84988662"
TRANSACTION = HERE / "leo900_external_commitment_rest_transaction_20261018_r1.json"
MESSAGE = ("Record LEO900 candidate and analysis commitment before final access\n\n"
           "Publish the fixed pre-final evidence package without changing manuscript, "
           "models, data, or the default branch. F1 remains open pending final evidence.\n")


def now():
    return datetime.now(timezone.utc).isoformat()


def new_json(path, document):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(document, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def read_package():
    manifest_path = PACKAGE / "SHA256_MANIFEST.json"
    manifest = json.loads(manifest_path.read_bytes())
    files = {**manifest["files"], "SHA256_MANIFEST.json": sha(manifest_path.read_bytes())}
    actual = {p.relative_to(PACKAGE).as_posix() for p in PACKAGE.rglob("*") if p.is_file()}
    if actual != set(files):
        raise RuntimeError("package membership differs from its fixed manifest")
    payload = {}
    for name, expected in files.items():
        path = PACKAGE / name
        data = path.read_bytes()
        if path.is_symlink() or sha(data) != expected:
            raise RuntimeError("package hash mismatch: " + name)
        if re.search(rb"-----BEGIN (?:OPENSSH |RSA |EC |DSA )?PRIVATE KEY-----|github_pat_[A-Za-z0-9_]+|gh[pousr]_[A-Za-z0-9]{20,}", data):
            raise RuntimeError("credential-like content rejected: " + name)
        content = data.decode("utf-8")
        if content.encode("utf-8") != data:
            raise RuntimeError("UTF-8 content does not round trip exactly: " + name)
        payload[name] = data
    return files, payload


def credential():
    environment = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "never"}
    result = git("credential", "fill", data=("url=https://github.com/" + OWNER_REPO + ".git\n\n").encode(),
                 env=environment, allowed=(0, 128))
    fields = dict(line.split("=", 1) for line in result.stdout.decode().splitlines() if "=" in line)
    if result.returncode == 0 and fields.get("password"):
        return fields["password"]
    attachment = Path(r"C:\Users\Administrator\Downloads\新建 文本文档 (6) - 副本.txt")
    content = attachment.read_text(encoding="utf-8-sig")
    tokens = set(re.findall(r"(?:github_pat_[A-Za-z0-9_]+|gh[pousr]_[A-Za-z0-9]{20,})", content))
    if len(tokens) != 1 or not re.search(r"1553926531-sudo/BRPHM(?:\.git)?(?:\s|$|[\)\]<>])", content):
        raise RuntimeError("human-supplied credential attachment does not identify the exact repository")
    return tokens.pop()


def make_tree(rows):
    names = [row["path"] for row in rows]
    if len(names) != len(set(names)) or any("/" in name or "\0" in name or not name for name in names):
        raise RuntimeError("unsafe or duplicate Git tree entry")
    records = [f'{row["mode"]} {row["type"]} {row["sha"]}\t{row["path"]}'.encode() + b"\0" for row in rows]
    return git("mktree", "--missing", "-z", data=b"".join(records)).stdout.decode().strip()


def local_tree(payload, root_rows, release_rows):
    """Use only two remote directory listings; no repository or data download."""
    def package_tree(items):
        entries, folders = [], {}
        for name, data in items.items():
            first, separator, rest = name.partition("/")
            if separator:
                folders.setdefault(first, {})[rest] = data
            else:
                oid = git("hash-object", "-w", "--stdin", data=data).stdout.decode().strip()
                entries.append({"path": first, "type": "blob", "mode": "100644", "sha": oid})
        for name, children in folders.items():
            entries.append({"path": name, "type": "tree", "mode": "040000", "sha": package_tree(children)})
        return make_tree(entries)
    if any(row["path"] == PACKAGE.name for row in release_rows):
        raise RuntimeError("publication package already exists in the remote base; preserve it")
    package_oid = package_tree(payload)
    release_oid = make_tree([*release_rows, {"path": PACKAGE.name, "type": "tree", "mode": "040000", "sha": package_oid}])
    entries = [row for row in root_rows if row["path"] != "release"]
    entries.append({"path": "release", "type": "tree", "mode": "040000", "sha": release_oid})
    return make_tree(entries)


def main():
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    receipt = HERE / f"leo900_external_commitment_rest_publication_{stamp}.json"
    state = {"schema": "brphm-f1-rest-external-commitment-publication-v1", "started_utc": now(),
             "repository": "https://github.com/" + OWNER_REPO, "branch": BRANCH,
             "f1_closed": False, "scientific_success_claimed": False,
             "record_limits": "Server readback confirms availability by the observed response time. Neither Git dates nor this record prove historical absence of access or immutable notarization.",
             "script_sha256": sha(Path(__file__).read_bytes()),
             "helper_script_sha256": sha((HERE / "publish_leo900_external_commitment_20261018.py").read_bytes()),
             "transport": "GitHub REST Git Data API; smart Git connection reset recorded separately"}
    try:
        files, payload = read_package()
        for args in [("remote", "get-url", "origin"), ("remote", "get-url", "--push", "origin")]:
            if not identity(git(*args).stdout.decode()):
                raise RuntimeError("origin identity differs from the sole authorized repository")
        if git("rev-parse", "HEAD").stdout.decode().strip() != BASE:
            raise RuntimeError("local HEAD differs from the registered publication base")
        index_before = git("ls-files", "--stage", "-z").stdout
        dirty_before = git("diff", "--binary", "HEAD").stdout
        manuscript = [REPO / "research/rul_space_paper_20261001/en" / name for name in ("main.tex", "main.pdf")]
        source_before = {p.relative_to(REPO).as_posix(): sha(p.read_bytes()) for p in manuscript}
        state.update(local_working_head=BASE, package_manifest_sha256=files["SHA256_MANIFEST.json"],
                     files=files, bytes_published=sum(map(len, payload.values())), origin_identity_verified=True)
        token = credential()
        opener = urllib.request.build_opener(NoRedirect())
        calls = []
        state["api_requests"] = calls

        def api(suffix, *, body=None, missing_ok=False):
            method = "GET" if body is None else "POST"
            request = urllib.request.Request(API + suffix, data=None if body is None else json.dumps(body).encode(),
                method=method, headers={"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28", "Content-Type": "application/json",
                    "User-Agent": "BRPHM-F1-evidence-publisher"})
            row = {"method": method, "path": suffix, "started_utc": now()}
            calls.append(row)
            try:
                with opener.open(request, timeout=60) as response:
                    data = response.read()
                    row.update(status=response.status, ended_utc=now(), response_sha256=sha(data),
                               headers={key: response.headers.get(key) for key in ("Date", "ETag", "X-GitHub-Request-Id")})
                    return json.loads(data), row["headers"]
            except urllib.error.HTTPError as exc:
                row.update(status=exc.code, ended_utc=now(), headers={key: exc.headers.get(key) for key in ("Date", "X-GitHub-Request-Id")})
                if missing_ok and exc.code == 404:
                    return None, row["headers"]
                raise RuntimeError(f"authorized GitHub API {method} request failed with HTTP {exc.code}") from None
            except Exception as exc:
                row.update(ended_utc=now(), error_type=type(exc).__name__)
                raise RuntimeError(f"authorized GitHub API {method} transport failed ({type(exc).__name__}); preserve transaction and read before retry") from None

        repository, identity_headers = api("")
        if repository.get("full_name") != OWNER_REPO:
            raise RuntimeError("GitHub returned a different repository identity")
        state["server_repository_identity"] = {"full_name": repository["full_name"], "id": repository["id"], "headers": identity_headers}
        default_branch = repository["default_branch"]
        default_before, _ = api("/git/ref/heads/" + default_branch)
        existing, _ = api("/git/ref/heads/" + BRANCH, missing_ok=True)
        if TRANSACTION.exists():
            transaction = json.loads(TRANSACTION.read_bytes())
            if (transaction.get("files") != files or transaction.get("repository") != OWNER_REPO
                    or transaction.get("branch") != BRANCH):
                raise RuntimeError("existing publication transaction differs; preserve it")
            state["resuming_fixed_transaction"] = True
            base = transaction["base"]
        else:
            if existing is not None:
                raise RuntimeError("remote branch already exists without this publication transaction; preserve it")
            base = default_before["object"]["sha"]
        base_commit, _ = api("/git/commits/" + base)
        root_tree, _ = api("/git/trees/" + base_commit["tree"]["sha"])
        if root_tree.get("truncated"):
            raise RuntimeError("remote base root tree is truncated")
        release_entries = [row for row in root_tree["tree"] if row["path"] == "release"]
        if release_entries:
            if len(release_entries) != 1 or release_entries[0]["type"] != "tree":
                raise RuntimeError("remote release path is not a unique directory")
            release_tree, _ = api("/git/trees/" + release_entries[0]["sha"])
            if release_tree.get("truncated"):
                raise RuntimeError("remote base release tree is truncated")
            release_rows = release_tree["tree"]
        else:
            release_rows = []
        tree = local_tree(payload, root_tree["tree"], release_rows)
        state.update(base_commit=base, expected_tree=tree,
                     base_selection="Existing remote default-branch commit, recorded before all writes; local working HEAD has not been published and is preserved")
        if TRANSACTION.exists():
            if transaction.get("tree") != tree:
                raise RuntimeError("local tree differs from the fixed transaction")
        else:
            name = git("config", "user.name").stdout.decode().strip()
            email = git("config", "user.email").stdout.decode().strip()
            if not name or not email or any(c in name + email for c in "\n\r<>"):
                raise RuntimeError("invalid configured Git author metadata")
            epoch = int(datetime.now(timezone.utc).timestamp())
            person = {"name": name, "email": email, "date": datetime.fromtimestamp(epoch, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
            raw_commit = (f"tree {tree}\nparent {base}\nauthor {name} <{email}> {epoch} +0000\n"
                          f"committer {name} <{email}> {epoch} +0000\n\n" + MESSAGE).encode()
            commit = git("hash-object", "-w", "-t", "commit", "--stdin", data=raw_commit).stdout.decode().strip()
            transaction = {"schema": "brphm-f1-api-fixed-transaction-v1", "created_utc": now(),
                           "repository": OWNER_REPO, "branch": BRANCH, "base": base, "tree": tree,
                           "commit": commit, "person": person, "message": MESSAGE, "files": files}
            new_json(TRANSACTION, transaction)
        commit = transaction["commit"]
        state.update(commit=commit, commit_url="https://github.com/" + OWNER_REPO + "/commit/" + commit,
                     transaction_sha256=sha(TRANSACTION.read_bytes()))
        if existing is not None and existing["object"]["sha"] != commit:
            raise RuntimeError("remote branch points to a different commit; replacement prohibited")
        remote_tree, _ = api("/git/trees/" + tree, missing_ok=True)
        if remote_tree is None:
            remote_tree, _ = api("/git/trees", body={"base_tree": base_commit["tree"]["sha"], "tree": [
                {"path": (PACKAGE / name).relative_to(REPO).as_posix(), "mode": "100644", "type": "blob", "content": data.decode("utf-8")}
                for name, data in sorted(payload.items())]})
        if remote_tree.get("sha") != tree:
            raise RuntimeError("GitHub tree differs from independently computed local Git tree")
        remote_commit, _ = api("/git/commits/" + commit, missing_ok=True)
        if remote_commit is None:
            remote_commit, _ = api("/git/commits", body={"tree": tree, "parents": [base], "message": transaction["message"],
                "author": transaction["person"], "committer": transaction["person"]})
        if remote_commit.get("sha") != commit or remote_commit["tree"]["sha"] != tree or [r["sha"] for r in remote_commit["parents"]] != [base]:
            raise RuntimeError("GitHub commit differs from independently computed local Git commit")
        if existing is None:
            api("/git/refs", body={"ref": "refs/heads/" + BRANCH, "sha": commit})
        branch, branch_headers = api("/git/ref/heads/" + BRANCH)
        if branch.get("ref") != "refs/heads/" + BRANCH or branch["object"]["sha"] != commit:
            raise RuntimeError("remote publication ref readback differs")
        # Read exact repository contents through another API representation. The
        # local tree/commit hash already binds all other repository members.
        package_path = PACKAGE.relative_to(REPO).as_posix()
        listing, _ = api("/contents/" + package_path + "?ref=" + commit)
        api_files = {}
        def collect(rows, prefix=""):
            for row in rows:
                name = prefix + row["name"]
                if row["type"] == "dir":
                    children, _ = api("/contents/" + row["path"] + "?ref=" + commit)
                    collect(children, name + "/")
                elif row["type"] == "file":
                    api_files[name] = row
                else:
                    raise RuntimeError("unexpected repository content type")
        collect(listing)
        if set(api_files) != set(files):
            raise RuntimeError("remote package membership differs")
        for name, data in payload.items():
            expected = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
            if api_files[name]["sha"] != expected or api_files[name]["size"] != len(data):
                raise RuntimeError("remote package blob hash or length differs: " + name)
        # Download the published manifest and a protocol, independently of the
        # directory listing, to verify returned bytes and nested SHA-256 links.
        downloaded = []
        for name in ("SHA256_MANIFEST.json", "F1_LEO900_FINAL_CONTINUATION_PROTOCOL_20261018R1.json"):
            if name not in files:
                # The protocol is stored inside the package's support subdir.
                matches = [n for n in files if Path(n).name == name]
                if len(matches) != 1:
                    raise RuntimeError("published protocol path is ambiguous")
                name = matches[0]
            blob, _ = api("/git/blobs/" + api_files[name]["sha"])
            if blob.get("encoding") != "base64" or base64.b64decode(blob["content"]) != payload[name]:
                raise RuntimeError("remote blob byte readback differs: " + name)
            downloaded.append({"path": name, "sha256": files[name], "size": len(payload[name])})
        default_after, _ = api("/git/ref/heads/" + default_branch)
        if default_after["object"]["sha"] != default_before["object"]["sha"]:
            raise RuntimeError("default branch changed during publication; audit concurrent changes")
        if git("ls-files", "--stage", "-z").stdout != index_before or git("diff", "--binary", "HEAD").stdout != dirty_before:
            raise RuntimeError("tracked dirty files or working index changed during publication")
        if {p.relative_to(REPO).as_posix(): sha(p.read_bytes()) for p in manuscript} != source_before:
            raise RuntimeError("manuscript bytes changed during publication")
        state.update(status="PUBLISHED_AND_READBACK_VERIFIED", independent_local_tree_and_commit_match=True,
                     api_blob_files_verified=len(files), byte_readbacks=downloaded,
                     api_ref_response_headers=branch_headers, default_branch=default_branch,
                     default_branch_commit_preserved=default_before["object"]["sha"],
                     working_index_and_tracked_dirty_files_preserved=True, manuscript_sha256=source_before,
                     package_manifest_unchanged=sha((PACKAGE / "SHA256_MANIFEST.json").read_bytes()) == files["SHA256_MANIFEST.json"])
    except BaseException as exc:
        state.update(status="ERROR_PRESERVE_AND_DIAGNOSE", error_type=type(exc).__name__, error=str(exc))
        raise
    finally:
        state["ended_utc"] = now()
        new_json(receipt, state)
        print(json.dumps({"receipt": str(receipt), "receipt_sha256": sha(receipt.read_bytes()),
                          "status": state["status"], "commit": state.get("commit"), "branch": BRANCH}))


if __name__ == "__main__":
    main()
