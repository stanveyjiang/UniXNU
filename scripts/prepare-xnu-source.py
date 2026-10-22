#!/usr/bin/env python3
"""Restore omitted DriverKit headers from earlier pinned XNU Git tags.

The public GitHub Contents API has a 60 request/hour limit per source IP. Hosted
macOS runners share egress addresses, so directory listing through that API is
not reliable. Read the headers directly from the same Apple Git remote instead:
fetch each pinned tag shallowly, enumerate its Git tree, and verify every blob.
"""

import hashlib
import json
import os
from pathlib import Path
import subprocess

TAG = os.environ.get('UNIXNU_DRIVERKIT_TAG', 'xnu-10063.121.3')
TRUST_TAG = os.environ.get('UNIXNU_TRUSTCACHE_TAG', 'xnu-8796.101.5')
WORK = Path('.cache/xnu-work')
DESTINATION = WORK / 'iokit/DriverKit'
TRUST_DESTINATION = WORK / 'EXTERNAL_HEADERS/TrustCache'
REPORT = Path('.cache/sources/xnu-restored-headers.json')


def git(*args, check=True, text=False):
    result = subprocess.run(
        ['git', '-C', str(WORK), *args],
        capture_output=True,
        text=text,
    )
    if check and result.returncode:
        error = result.stderr if text else result.stderr.decode(errors='replace')
        raise RuntimeError(f'git {" ".join(args)} failed: {error.strip()}')
    return result


def ensure_tag(tag):
    found = git('rev-parse', '--verify', '--quiet',
                f'refs/tags/{tag}^{{commit}}', check=False)
    if found.returncode == 0:
        return
    git('fetch', '--depth', '1',
        'https://github.com/apple-oss-distributions/xnu.git',
        f'refs/tags/{tag}:refs/tags/{tag}')


def header_paths(tag, directory):
    output = git('ls-tree', '-r', tag, '--', directory, text=True).stdout
    paths = []
    for line in output.splitlines():
        metadata, path = line.split('\t', 1)
        mode, kind, blob = metadata.split()
        if kind == 'blob' and path.endswith('.h'):
            paths.append((path, blob))
    return paths


def restore(tag, directory, destination):
    records = []
    for path, expected_blob in header_paths(tag, directory):
        relative = Path(path).relative_to(directory)
        data = git('show', f'{tag}:{path}').stdout
        blob = hashlib.sha1(
            b'blob ' + str(len(data)).encode() + b'\0' + data
        ).hexdigest()
        if blob != expected_blob:
            raise ValueError(f'Git blob hash mismatch: {path}')
        target = destination / relative
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        records.append({
            'name': str(relative),
            'source_tag': tag,
            'git_blob': blob,
            'sha256': hashlib.sha256(data).hexdigest(),
        })
    return records


if __name__ == '__main__':
    if not WORK.is_dir():
        raise SystemExit('Create the local XNU work source before preparing headers')

    ensure_tag(TAG)
    ensure_tag(TRUST_TAG)
    records = restore(TAG, 'iokit/DriverKit', DESTINATION)
    records += restore(TRUST_TAG, 'EXTERNAL_HEADERS/TrustCache',
                       TRUST_DESTINATION)

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(records, indent=2) + '\n')
    print(f'Restored {len(records)} omitted public headers from Apple tags; '
          'Git blobs verified')
