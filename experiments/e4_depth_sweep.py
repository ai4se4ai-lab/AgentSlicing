"""E4b (RQ3): slice size vs. hand-off distance. The injector's hand-off length l is set to
0..5 (the main benchmark draws it from 0..2), so the depth needed to see a defect is a
measured outcome rather than a benchmark parameter. Confirmed exhaustive slices up to k=8."""
from __future__ import annotations

import time

from common import environment, pmap, save
from slicing import analysis as an, generator as gen, injector as inj, slices as sl

CLS = ['S2', 'S3', 'S4', 'S6a', 'S6b']
KMAX = 8


def run(args):
    topo, cls, ell, seed, host = args
    t, gt = inj.inject(gen.generate(topo, host, seed), cls, seed, depth=ell)
    prim = gt['primary']
    kmax = KMAX if host <= 5 else ell + 2          # larger hosts: enough to decide depth <= l+2
    ex = sl.exhaustive(t, kmax)
    r = an.check_confirmed(t, ex)
    f = r['findings'].get(prim)
    depth = None if f is None else (1 if f['static'] else min(sl.size(s) for s in f['minimal']))
    return {'topo': topo, 'cls': cls, 'ell': ell, 'seed': seed, 'host': host, 'kmax': kmax, 'nodes': len(t.order),
            'depth': depth,
            'detected_by_k': {k: depth is not None and depth <= k for k in range(1, kmax + 1)},
            'slices_by_k': {k: sum(1 for s in ex if sl.size(s) <= k) for k in range(1, kmax + 1)}}


def main():
    env = environment()
    t0 = time.time()
    jobs = [(topo, c, ell, s, host) for host in (5, 12) for topo in ('chain', 'forkjoin') for c in CLS for ell in range(6)
            for s in range(10)]
    rows = pmap(run, jobs, chunksize=2)
    save('e4_depth_sweep', {'env': env, 'kmax': KMAX, 'seconds': time.time() - t0, 'rows': rows})
    print('done', len(rows), round(time.time() - t0), 's')


if __name__ == '__main__':
    main()
