"""Proof mutants: each mutated definition must break at least one obligation it should.

A vacuous or over-assumed obligation would survive the mutation of the definition it
depends on. Writes results/proof_mutants.json.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
MUTANTS = {
    'applies-ignores-oracle': 'L11-failed-provides-nothing',
    'face-value-conditional': 'L2-face-value-dominates',
    'join-intersection': 'L3-join-subset',
    'applies-ignores-decl': 'L12-decl-enables',
    'decl-inherited': 'L13-decl-local',
    'single-pair-ok': 'C2-single-pair-inexact',
}


def main():
    rows = []
    for m, expected in MUTANTS.items():
        out = subprocess.run([sys.executable, str(HERE / 'prove.py')], env={**os.environ, 'SLICING_MUTANT': m},
                             capture_output=True, text=True, check=True).stdout.strip().splitlines()[-1]
        failed = json.loads(out)['failed']
        rows.append({'mutant': m, 'expected': expected, 'failed': failed, 'killed': expected in failed})
        print(m, 'killed' if expected in failed else 'SURVIVED', failed)
    (ROOT / 'results').mkdir(exist_ok=True)
    (ROOT / 'results/proof_mutants.json').write_text(json.dumps(rows, indent=1) + '\n', encoding='utf-8')
    sys.exit(0 if all(r['killed'] for r in rows) else 1)


if __name__ == '__main__':
    main()
