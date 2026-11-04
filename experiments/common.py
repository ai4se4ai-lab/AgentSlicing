"""Shared experiment utilities: environment record, parallel map, JSON output."""
from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / 'results'
sys.path.insert(0, str(ROOT))


def environment() -> dict:
    try:
        commit = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True).stdout.strip()
        dirty = bool(subprocess.run(['git', 'status', '--porcelain'], cwd=ROOT, capture_output=True, text=True).stdout.strip())
    except OSError:
        commit, dirty = 'unknown', True
    import numpy, scipy, z3
    return {'commit': commit, 'dirty_worktree': dirty, 'python': sys.version.split()[0], 'platform': platform.platform(),
            'numpy': numpy.__version__, 'scipy': scipy.__version__, 'z3': z3.get_version_string(),
            'cpus': os.cpu_count(), 'started': time.strftime('%Y-%m-%dT%H:%M:%S')}


def pmap(fn, items, workers=None, chunksize=1):
    workers = workers or max(1, (os.cpu_count() or 2) - 2)
    if workers == 1:
        return [fn(x) for x in items]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(fn, items, chunksize=chunksize))


def save(name: str, payload: dict):
    RESULTS.mkdir(exist_ok=True)
    path = RESULTS / f'{name}.json'
    path.write_text(json.dumps(payload, indent=1, default=str) + '\n', encoding='utf-8')
    return path


def load(name: str) -> dict:
    return json.loads((RESULTS / f'{name}.json').read_text(encoding='utf-8'))
