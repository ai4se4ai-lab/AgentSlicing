"""One command to regenerate every result, table, figure and macro of the paper.

    python experiments/run_all.py            # everything (about an hour on 20 cores)
    python experiments/run_all.py --quick    # proofs, tests, E1, running example, E3, post-processing

Each step is a separate process so a failure names its step; logs go to results/logs/.
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
STEPS = [
    ('proofs', [PY, 'formal/prove.py']),
    ('mutants', [PY, 'formal/mutate.py']),
    ('tests', [PY, '-m', 'pytest', '-q', 'tests']),
    ('running_example', [PY, 'experiments/running_example.py']),
    ('e1_conformance', [PY, 'experiments/e1_conformance.py']),
    ('e2_detection', [PY, 'experiments/e2_detection.py']),
    ('e3_architectures', [PY, 'experiments/e3_architectures.py']),
    ('e4_depth_sweep', [PY, 'experiments/e4_depth_sweep.py']),
    ('e8_mutation', [PY, 'experiments/e8_mutation.py']),
    ('e5_scalability', [PY, 'experiments/e5_scalability.py']),
    ('e6_evolution', [PY, 'experiments/e6_evolution.py']),
    ('e7_ablation', [PY, 'experiments/e7_ablation.py']),
    ('process', [PY, 'scripts/process_results.py']),
]
QUICK = {'proofs', 'mutants', 'tests', 'running_example', 'e1_conformance', 'e3_architectures', 'process'}


def main():
    quick = '--quick' in sys.argv
    only = [a for a in sys.argv[1:] if not a.startswith('--')]
    logs = ROOT / 'results/logs'
    logs.mkdir(parents=True, exist_ok=True)
    for name, cmd in STEPS:
        if (quick and name not in QUICK) or (only and name not in only):
            continue
        t0 = time.time()
        with open(logs / f'{name}.log', 'w', encoding='utf-8') as fh:
            r = subprocess.run(cmd, cwd=ROOT, stdout=fh, stderr=subprocess.STDOUT)
        print(f'{name:18s} {"ok" if r.returncode == 0 else "FAILED"} {time.time() - t0:8.1f} s', flush=True)
        if r.returncode != 0:
            sys.exit(f'step {name} failed; see results/logs/{name}.log')


if __name__ == '__main__':
    main()
