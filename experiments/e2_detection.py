"""E2 (RQ2) detection and localization, and E4 (RQ3) slice-size sweep.

Small benchmark: exhaustive convex slices up to K give ground-truth minimal manifesting
slices; every checker is scored against the injected keys and root causes.
Medium benchmark: no exhaustive ground truth; strategies and baselines only.
"""
from __future__ import annotations

import random
import sys
import time

from common import environment, pmap, save
from slicing import analysis as an, generator as gen, injector as inj, semantics as sem, slices as sl

K = 5
STRATS = ['singleton', 'window2', 'window3', 'band1', 'band2', 'region', 'goal']
CLASSES = inj.CLASSES + inj.DECOYS + ('clean',)


def family(t, name):
    if name == 'SL':
        return list(dict.fromkeys(sl.singleton(t) + sl.window(t, 2) + sl.region(t) + sl.goal_directed(t)))
    return sl.STRATEGIES[name](t)


def score(t, sym, gt, findings, gt_mms, root_hull, root, n_slices, seconds):
    keys = set(findings)
    gk = set(gt['keys'])
    prim = gt.get('primary')
    row = {'reported': len(keys), 'false_keys': len(keys - set(sym)), 'true_keys': len(keys & set(sym)),
           'detected': bool(keys & gk) if gk else None, 'primary_detected': (prim in keys) if prim else None,
           'alarm': bool(keys) if gt['decoy'] else None, 'slices': n_slices, 'seconds': seconds}
    if prim and prim in findings:
        f = findings[prim]
        top = f['top']
        row.update(top_size=sl.size(top), size_ratio=sl.size(top) / len(t.order),
                   exact=(top in gt_mms) if gt_mms else None, precise=(top & ~root_hull) == 0,
                   hit=bool(top & root), cls=f.get('class'),
                   n_minimal=len(f.get('minimal', [])))
    return row


def run_team(args):
    topo, n, seed, cls, medium = args
    t0 = time.perf_counter()
    base = gen.generate(topo, n, seed)
    t, gt = inj.inject(base, cls, seed)
    stats = {}
    try:
        sym = sem.symptoms(t, max_runs=500_000, stats=stats)
        exact_ok = True
    except sem.RunLimit:
        sym, exact_ok = {k: None for k in gt['keys']}, False
    root = t.nmask(gt['root']) if gt['root'] else 0
    root_hull = sl.hull(t, root) if root else 0
    rec = {'topo': topo, 'n': n, 'seed': seed, 'cls': cls, 'nodes': len(t.order), 'medium': medium,
           'gt_ok': set(gt['keys']) <= set(sym), 'exact_ok': exact_ok, 'sym': len(sym), 'checkers': {}}
    prim = gt.get('primary')
    cache = {}

    def fam_findings(slices, budget=None):
        manifest = {k: [(None, w)] for k, w in sem.static_findings(t).items()}
        t1 = time.perf_counter()
        for s in dict.fromkeys(slices):
            if s not in cache:
                try:
                    cache[s] = sem.findings(t, s, 200_000)
                except sem.RunLimit:
                    cache[s] = {}
            for k, w in cache[s].items():
                if not (manifest.get(k) and manifest[k][0][0] is None):
                    manifest.setdefault(k, []).append((s, w))
        loc = an.localize(t, manifest)
        for k, v in loc.items():
            v['class'] = an.diagnose(t, k, 0 if v['static'] else v['top'], v['witness'])
        return loc, time.perf_counter() - t1

    gt_mms, depth = None, None
    if not medium:
        ex = sl.exhaustive(t, K)
        loc_all, secs_all = fam_findings(ex)
        if prim in loc_all:
            gt_mms = set(loc_all[prim]['minimal'])
            depth = 1 if loc_all[prim]['static'] else min(sl.size(s) for s in gt_mms)
        rec['depth'] = depth
        rec['depths'] = {str(k): (1 if loc_all[k]['static'] else min(sl.size(s) for s in loc_all[k]['minimal']))
                         for k in gt['keys'] if k in loc_all}
        for k in range(1, K + 1):
            sub = [s for s in ex if sl.size(s) <= k]
            loc, secs = fam_findings(sub)
            rec['checkers'][f'k{k}'] = score(t, sym, gt, loc, gt_mms, root_hull, root, len(sub), secs)
    for name in STRATS + ['SL']:
        slices = family(t, name)
        loc, secs = fam_findings(slices)
        rec['checkers'][name] = score(t, sym, gt, loc, gt_mms, root_hull, root, len(set(slices)), secs)
        if name == 'SL':
            sizes = [sl.size(s) for s in dict.fromkeys(slices)]
    rng = random.Random(f'B3/{topo}/{n}/{seed}/{cls}')
    rnd = sl.random_convex(t, sizes, rng)
    loc, secs = fam_findings(rnd)
    rec['checkers']['B3'] = score(t, sym, gt, loc, gt_mms, root_hull, root, len(rnd), secs)
    if exact_ok:
        t1 = time.perf_counter()
        w = an.whole_team(t, 500_000)
        rec['checkers']['B2'] = score(t, sym, gt, w['findings'], gt_mms, root_hull, root, 1, time.perf_counter() - t1)
    lint = an.lint(t)
    rec['checkers']['B4'] = score(t, sym, gt, lint['findings'], gt_mms, root_hull, root, 0, 0.0)
    rec['checkers']['B5'] = score(t, sym, gt, an.smells(t)['findings'], gt_mms, root_hull, root, 0, 0.0)
    rec['seconds'] = time.perf_counter() - t0
    return rec


def jobs(medium: bool):
    out = []
    sizes = (20, 30) if medium else (5, 8)
    for topo in gen.TOPOLOGIES:
        for n in sizes:
            for seed in range(10):
                for cls in CLASSES:
                    out.append((topo, n, seed, cls, medium))
    return out


def main():
    env = environment()
    t0 = time.time()
    small = pmap(run_team, jobs(False), chunksize=4)
    medium = pmap(run_team, jobs(True), chunksize=4)
    save('e2_detection', {'env': env, 'K': K, 'seconds': time.time() - t0, 'rows': small + medium})
    print('done', len(small), len(medium), round(time.time() - t0), 's')


if __name__ == '__main__':
    main()
