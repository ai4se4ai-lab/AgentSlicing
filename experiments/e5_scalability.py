"""E5 (RQ3): cost vs team size, per strategy; whole-team exact and exhaustive-k with cut-offs."""
from __future__ import annotations

import time
import tracemalloc
from math import comb

from common import environment, pmap, save
from slicing import generator as gen, injector as inj, semantics as sem, slices as sl

SIZES = [10, 20, 50, 100, 200, 500, 1000, 2000, 5000]
TOPOS = ['layered', 'sp', 'random', 'mixed']
STRATS = ['singleton', 'window2', 'band1', 'region', 'goal']
BUDGET = 60.0
CLS = ['S2', 'S3', 'S4', 'S6a']


def family(t, name):
    if name == 'SL':
        return list(dict.fromkeys(sl.singleton(t) + sl.window(t, 2) + sl.region(t) + sl.goal_directed(t)))
    return sl.STRATEGIES[name](t)


def timed_family(t, slices, budget, gt_keys):
    t0 = time.perf_counter()
    deadline = t0 + budget
    runs, limited, found, done = {}, 0, set(), 0
    for s in slices:
        if time.perf_counter() > deadline:
            return {'seconds': time.perf_counter() - t0, 'slices': done, 'timeout': True, 'limited': limited,
                    'detected': bool(found & gt_keys), 'runs': runs.get('runs', 0)}
        try:
            f = sem.findings(t, s, 20_000, runs, deadline)
            found |= set(f)
        except sem.RunLimit:
            limited += 1
        done += 1
    return {'seconds': time.perf_counter() - t0, 'slices': done, 'timeout': False, 'limited': limited,
            'detected': bool(found & gt_keys), 'runs': runs.get('runs', 0)}


def run(args):
    topo, n, seed = args
    t0 = time.perf_counter()
    base = gen.generate(topo, n, seed)
    t, gt = inj.inject(base, CLS[seed % len(CLS)], seed)
    gen_s = time.perf_counter() - t0
    keys = set(gt['keys'])
    rec = {'topo': topo, 'n': n, 'nodes': len(t.order), 'edges': len(t.edges), 'seed': seed, 'gen_seconds': gen_s,
           'choice_points': sl.choice_points(t, (1 << len(t.order)) - 1), 'strategies': {}}
    mem = seed == 0
    for name in STRATS + ['SL']:
        if mem:
            tracemalloc.start()
        f0 = time.perf_counter()
        slices = family(t, name)
        fam_s = time.perf_counter() - f0
        r = timed_family(t, list(dict.fromkeys(slices)), BUDGET, keys)
        r['family_seconds'] = fam_s
        r['max_slice'] = max(sl.size(s) for s in slices)
        if mem:
            r['peak_mb'] = tracemalloc.get_traced_memory()[1] / 2**20
            tracemalloc.stop()
        rec['strategies'][name] = r
    # B6 must-analysis (global, path-insensitive, linear per failure set)
    from slicing import analysis as an
    m0 = time.perf_counter()
    mf = an.must_analysis(t)['findings']
    rec['must'] = {'seconds': time.perf_counter() - m0, 'timeout': False, 'detected': bool(set(mf) & keys)}
    # whole-team exact
    w0 = time.perf_counter()
    stats = {}
    try:
        sym = sem.symptoms(t, 10_000_000, stats, time.perf_counter() + BUDGET)
        rec['whole'] = {'seconds': time.perf_counter() - w0, 'timeout': False, 'runs': stats.get('runs', 0),
                        'detected': bool(set(sym) & keys)}
    except sem.RunLimit:
        rec['whole'] = {'seconds': time.perf_counter() - w0, 'timeout': True, 'runs': stats.get('runs', 0), 'detected': None}
    # exhaustive k=3 (combinatorial cut-off)
    combos = sum(comb(len(t.order), k) for k in range(1, 4))
    if combos <= 3_000_000:
        e0 = time.perf_counter()
        ex = sl.exhaustive(t, 3)
        r = timed_family(t, ex, BUDGET, keys)
        r['enumerate_seconds'] = time.perf_counter() - e0 - r['seconds']
        r['convex'] = len(ex)
        rec['exhaustive3'] = r
    else:
        rec['exhaustive3'] = {'skipped': True, 'subsets': combos}
    return rec


def convex_counts():
    """Number of convex slices vs size: chain (quadratic) vs wide layered (exponential)."""
    out = []
    for n in [4, 6, 8, 10, 12, 14, 16]:
        for topo in ['chain', 'layered', 'forkjoin']:
            t = gen.generate(topo, n, 0)
            try:
                c = len(sl.all_convex(t, limit=400_000))
            except OverflowError:
                c = None
            out.append({'topo': topo, 'n': n, 'nodes': len(t.order), 'convex': c})
    return out


def main():
    env = environment()
    t0 = time.time()
    jobs = [(topo, n, seed) for n in SIZES for topo in TOPOS for seed in range(10)]
    jobs.sort(key=lambda j: -j[1])
    rows = pmap(run, jobs, workers=10)
    save('e5_scalability', {'env': env, 'budget': BUDGET, 'seconds': time.time() - t0, 'rows': rows,
                            'convex_counts': convex_counts()})
    print('done', len(rows), round(time.time() - t0), 's')


if __name__ == '__main__':
    main()
