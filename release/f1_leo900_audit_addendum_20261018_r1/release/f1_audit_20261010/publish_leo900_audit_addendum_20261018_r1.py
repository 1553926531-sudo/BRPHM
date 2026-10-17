"""Append only the exact F1 audit package on a new authorized BRPHM branch."""
from __future__ import annotations

import base64
import hashlib
import json
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from publish_leo900_external_commitment_20261018 import API, HERE, NoRedirect, OWNER_REPO, REPO, git, identity, sha
from publish_leo900_external_commitment_rest_20261018 import credential, make_tree, new_json

PACKAGE = REPO / 'release/f1_leo900_audit_addendum_20261018_r1'
BRANCH = 'f1-leo900-audit-addendum-20261018-r1'
BASE = '846cdaac03beab2bacb9834bde1ed8fff1c77141'
LOCAL_HEAD = 'ed051819e5e97a205fb0b076bc79b3cd84988662'
ORIGINAL_BRANCH = 'f1-leo900-prefinal-20261018-r1'
TRANSACTION = HERE / 'leo900_audit_addendum_transaction_20261018_r1.json'
MESSAGE = ('Append independent LEO900 numerical audit and retained evidence\n\n'
           'Preserve the original candidate/analysis commitment. This additive audit '
           'package does not change the candidate, analysis or manuscript. F1 remains open.\n')


def now():
    return datetime.now(timezone.utc).isoformat()


def read_package():
    manifest = json.loads((PACKAGE / 'SHA256_MANIFEST.json').read_bytes())
    files = {**manifest['files'], 'SHA256_MANIFEST.json': sha((PACKAGE / 'SHA256_MANIFEST.json').read_bytes())}
    actual = {p.relative_to(PACKAGE).as_posix() for p in PACKAGE.rglob('*') if p.is_file()}
    if actual != set(files):
        raise RuntimeError('package membership differs')
    payload = {}
    for name, expected in files.items():
        p = PACKAGE / name
        if p.is_symlink() or not p.resolve().is_relative_to(PACKAGE.resolve()):
            raise RuntimeError('unsafe package member')
        data = p.read_bytes()
        if sha(data) != expected or re.search(rb'-----BEGIN (?:OPENSSH |RSA |EC |DSA )?PRIVATE KEY-----|github_pat_[A-Za-z0-9_]+|gh[pousr]_[A-Za-z0-9]{20,}', data):
            raise RuntimeError('hash/credential check failed: ' + name)
        if data.decode('utf-8').encode('utf-8') != data:
            raise RuntimeError('non-UTF8 content')
        payload[name] = data
    if sum(map(len, payload.values())) > 3_000_000:
        raise RuntimeError('small-text traffic budget exceeded')
    return files, payload


def local_tree(payload, root_rows, release_rows):
    def descend(items):
        entries, directories = [], {}
        for name, data in items.items():
            first, separator, rest = name.partition('/')
            if separator:
                directories.setdefault(first, {})[rest] = data
            else:
                oid = git('hash-object', '-w', '--stdin', data=data).stdout.decode().strip()
                entries.append({'path': first, 'mode': '100644', 'type': 'blob', 'sha': oid})
        for name, children in directories.items():
            entries.append({'path': name, 'mode': '040000', 'type': 'tree', 'sha': descend(children)})
        return make_tree(entries)
    if any(row['path'] == PACKAGE.name for row in release_rows):
        raise RuntimeError('addendum package already exists in base; preserve it')
    package_tree = descend(payload)
    release_tree = make_tree([*release_rows, {'path': PACKAGE.name, 'mode': '040000', 'type': 'tree', 'sha': package_tree}])
    return make_tree([*(row for row in root_rows if row['path'] != 'release'),
                      {'path': 'release', 'mode': '040000', 'type': 'tree', 'sha': release_tree}])


def main():
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    receipt = HERE / f'leo900_audit_addendum_publication_{stamp}.json'
    state = {'schema': 'brphm-f1-additive-audit-publication-v1', 'started_utc': now(),
             'repository': 'https://github.com/' + OWNER_REPO, 'branch': BRANCH,
             'kind': 'additional audit evidence; no new candidate/analysis registration',
             'f1_closed': False, 'scientific_success_claimed': False,
             'script_sha256': sha(Path(__file__).read_bytes()),
             'helper_sha256': {n: sha((HERE / n).read_bytes()) for n in
                ('publish_leo900_external_commitment_20261018.py', 'publish_leo900_external_commitment_rest_20261018.py')},
             'record_limits': 'Observed GitHub availability is not historical non-access proof or immutable notarization; local commit dates are self-recorded.'}
    try:
        files, payload = read_package()
        for args in [('remote', 'get-url', 'origin'), ('remote', 'get-url', '--push', 'origin')]:
            if not identity(git(*args).stdout.decode()):
                raise RuntimeError('origin is not the sole authorized BRPHM repository')
        if git('rev-parse', 'HEAD').stdout.decode().strip() != LOCAL_HEAD:
            raise RuntimeError('local HEAD changed; preserve and review')
        index_before = git('ls-files', '--stage', '-z').stdout
        dirty_before = git('diff', '--binary', 'HEAD').stdout
        protected_paths = [REPO / 'research/rul_space_paper_20261001/en' / n for n in ('main.tex', 'main.pdf')]
        protected_paths.append(REPO / 'release/f1_leo900_pre_final_commitment_20261018_r1/SHA256_MANIFEST.json')
        protected = {str(p): sha(p.read_bytes()) for p in protected_paths}
        state.update(files=files, raw_payload_bytes=sum(map(len, payload.values())),
                     package_manifest_sha256=files['SHA256_MANIFEST.json'], local_head=LOCAL_HEAD)
        token = credential()
        opener = urllib.request.build_opener(NoRedirect())
        calls = state['api_requests'] = []

        def api(suffix, *, body=None, missing_ok=False):
            method = 'GET' if body is None else 'POST'
            data = None if body is None else json.dumps(body).encode()
            row = {'method': method, 'path': suffix, 'started_utc': now(), 'request_body_bytes': len(data) if data else 0}
            calls.append(row)
            request = urllib.request.Request(API + suffix, data=data, method=method, headers={
                'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json',
                'X-GitHub-Api-Version': '2022-11-28', 'Content-Type': 'application/json',
                'User-Agent': 'BRPHM-F1-additive-audit-publisher'})
            try:
                with opener.open(request, timeout=30) as response:
                    result = response.read()
                    row.update(status=response.status, ended_utc=now(), response_bytes=len(result),
                               response_sha256=sha(result), headers={k: response.headers.get(k) for k in ('Date', 'ETag', 'X-GitHub-Request-Id')})
                    return json.loads(result), row['headers']
            except urllib.error.HTTPError as exc:
                row.update(status=exc.code, ended_utc=now())
                if missing_ok and exc.code == 404:
                    return None, {}
                raise RuntimeError(f'authorized GitHub {method} request returned HTTP{exc.code}') from None
            except Exception as exc:
                row.update(ended_utc=now(), error_type=type(exc).__name__)
                raise RuntimeError('authorized GitHub transport interrupted; preserve transaction and read before retry') from None

        repository, headers = api('')
        if repository.get('full_name') != OWNER_REPO:
            raise RuntimeError('server repository identity mismatch')
        state['server_repository_identity'] = {'full_name': repository['full_name'], 'id': repository['id'], 'headers': headers}
        default = repository['default_branch']
        default_before, _ = api('/git/ref/heads/' + default)
        original, _ = api('/git/ref/heads/' + ORIGINAL_BRANCH)
        if original['object']['sha'] != BASE:
            raise RuntimeError('original commitment branch changed; do not overwrite it')
        existing, _ = api('/git/ref/heads/' + BRANCH, missing_ok=True)
        base_commit, _ = api('/git/commits/' + BASE)
        root, _ = api('/git/trees/' + base_commit['tree']['sha'])
        if root.get('truncated'):
            raise RuntimeError('truncated base tree')
        releases = [r for r in root['tree'] if r['path'] == 'release' and r['type'] == 'tree']
        if len(releases) != 1:
            raise RuntimeError('missing unique release directory')
        release, _ = api('/git/trees/' + releases[0]['sha'])
        if release.get('truncated'):
            raise RuntimeError('truncated release tree')
        tree = local_tree(payload, root['tree'], release['tree'])
        if TRANSACTION.exists():
            transaction = json.loads(TRANSACTION.read_bytes())
            if any(transaction.get(k) != v for k, v in {'repository': OWNER_REPO, 'branch': BRANCH, 'base': BASE, 'tree': tree, 'files': files}.items()):
                raise RuntimeError('existing transaction differs; preserve it')
            state['resuming_fixed_transaction'] = True
        else:
            if existing is not None:
                raise RuntimeError('branch exists without this transaction; replacement prohibited')
            name = git('config', 'user.name').stdout.decode().strip()
            email = git('config', 'user.email').stdout.decode().strip()
            if not name or not email or any(c in name + email for c in '\n\r<>'):
                raise RuntimeError('invalid configured Git metadata')
            epoch = int(datetime.now(timezone.utc).timestamp())
            person = {'name': name, 'email': email, 'date': datetime.fromtimestamp(epoch, timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}
            raw = (f'tree {tree}\nparent {BASE}\nauthor {name} <{email}> {epoch} +0000\ncommitter {name} <{email}> {epoch} +0000\n\n' + MESSAGE).encode()
            commit = git('hash-object', '-w', '-t', 'commit', '--stdin', data=raw).stdout.decode().strip()
            transaction = {'schema': 'brphm-f1-additive-audit-fixed-transaction-v1', 'created_utc': now(),
                           'repository': OWNER_REPO, 'branch': BRANCH, 'base': BASE, 'tree': tree,
                           'commit': commit, 'person': person, 'message': MESSAGE, 'files': files}
            new_json(TRANSACTION, transaction)
        commit = transaction['commit']
        state.update(base_commit=BASE, expected_tree=tree, commit=commit,
                     commit_url='https://github.com/' + OWNER_REPO + '/commit/' + commit,
                     transaction_sha256=sha(TRANSACTION.read_bytes()))
        if existing is not None and existing['object']['sha'] != commit:
            raise RuntimeError('branch differs from fixed transaction; replacement prohibited')
        remote_tree, _ = api('/git/trees/' + tree, missing_ok=True)
        if remote_tree is None:
            remote_tree, _ = api('/git/trees', body={'base_tree': base_commit['tree']['sha'], 'tree': [
                {'path': (PACKAGE / n).relative_to(REPO).as_posix(), 'mode': '100644', 'type': 'blob', 'content': d.decode('utf-8')}
                for n, d in sorted(payload.items())]})
        if remote_tree.get('sha') != tree:
            raise RuntimeError('server tree differs from local Git object')
        remote_commit, _ = api('/git/commits/' + commit, missing_ok=True)
        if remote_commit is None:
            remote_commit, _ = api('/git/commits', body={'tree': tree, 'parents': [BASE], 'message': transaction['message'],
                'author': transaction['person'], 'committer': transaction['person']})
        if remote_commit.get('sha') != commit or remote_commit['tree']['sha'] != tree or [p['sha'] for p in remote_commit['parents']] != [BASE]:
            raise RuntimeError('server commit differs from local Git object')
        if existing is None:
            api('/git/refs', body={'ref': 'refs/heads/' + BRANCH, 'sha': commit})
        branch, branch_headers = api('/git/ref/heads/' + BRANCH)
        if branch.get('ref') != 'refs/heads/' + BRANCH or branch['object']['sha'] != commit:
            raise RuntimeError('branch readback differs')
        listing, _ = api('/contents/' + PACKAGE.relative_to(REPO).as_posix() + '?ref=' + commit)
        remote_files = {}

        def collect(rows, prefix=''):
            for row in rows:
                name = prefix + row['name']
                if row['type'] == 'dir':
                    children, _ = api('/contents/' + row['path'] + '?ref=' + commit)
                    collect(children, name + '/')
                elif row['type'] == 'file':
                    remote_files[name] = row
                else:
                    raise RuntimeError('unexpected remote member type')
        collect(listing)
        if set(remote_files) != set(files):
            raise RuntimeError('remote package membership differs')
        for name, data in payload.items():
            oid = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
            if remote_files[name]['sha'] != oid or remote_files[name]['size'] != len(data):
                raise RuntimeError('remote blob binding differs: ' + name)
        for name in ('SHA256_MANIFEST.json', 'INTEGRITY_GRAPH.json'):
            blob, _ = api('/git/blobs/' + remote_files[name]['sha'])
            if blob.get('encoding') != 'base64' or base64.b64decode(blob['content']) != payload[name]:
                raise RuntimeError('remote byte readback differs: ' + name)
        default_after, _ = api('/git/ref/heads/' + default)
        original_after, _ = api('/git/ref/heads/' + ORIGINAL_BRANCH)
        if default_after['object']['sha'] != default_before['object']['sha'] or original_after['object']['sha'] != BASE:
            raise RuntimeError('protected branch changed concurrently; audit required')
        if git('ls-files', '--stage', '-z').stdout != index_before or git('diff', '--binary', 'HEAD').stdout != dirty_before:
            raise RuntimeError('working index or tracked dirty files changed')
        if {str(p): sha(p.read_bytes()) for p in protected_paths} != protected:
            raise RuntimeError('frozen manuscript/original manifest changed')
        if any(sha((PACKAGE / n).read_bytes()) != h for n, h in files.items()):
            raise RuntimeError('package changed during publication')
        state.update(status='PUBLISHED_AND_READBACK_VERIFIED', api_blob_files_verified=len(files),
                     independent_local_tree_and_commit_match=True, api_ref_response_headers=branch_headers,
                     default_branch=default, default_branch_commit_preserved=default_before['object']['sha'],
                     original_commitment_branch_preserved=True, working_index_and_tracked_dirty_files_preserved=True,
                     protected_local_sha256=protected,
                     api_response_bytes=sum(row.get('response_bytes', 0) for row in calls),
                     api_request_body_bytes=sum(row.get('request_body_bytes', 0) for row in calls))
    except BaseException as exc:
        state.update(status='ERROR_PRESERVE_AND_DIAGNOSE', error_type=type(exc).__name__, error=str(exc))
        raise
    finally:
        state['ended_utc'] = now()
        new_json(receipt, state)
        print(json.dumps({'receipt': str(receipt), 'sha256': sha(receipt.read_bytes()), 'status': state['status'],
                          'commit': state.get('commit'), 'branch': BRANCH, 'f1_closed': False}))


if __name__ == '__main__':
    main()
