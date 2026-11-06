"""E2 (RQ2) detection and localization on the injected benchmark, and the E4 slice-size sweep.

Every slice-based checker reports *confirmed* findings: a slice manifests a key only if one
of its witnesses lifts to a run of the team (Theorem 3b). Ground truth: the injected keys
(verified with the exact semantics) and, on the small benchmark, the true minimal manifesting
slices from exhaustive enumeration of confirmed convex slices up to size 6 (teams with at
most 16 nodes, as pre-registered) or 5 (larger teams).
"""
from __future__ import annotations

import random
import time

from common import environment, pmap, save
from slicing import analysis as an, generator as gen, injector as inj, semantics as sem, slices as sl

STRATS = ['singleton', 'window2', 'window3', 'band1', 'band2', 'region', 'goal']
CLASSES = inj.CLASSES + inj.DECOYS + ('clean',)


def family(t, name):
    if name == 'SL':
        return list(dict.fromkeys(sl.singleton(t) + sl.window(t, 2) + sl.region(t) + sl.goal_directed(t)))
    return sl.STRATEGIES[name](t)


def score(t, sym, gt, findings, gt_mms, root_hull, root, n_slices, seconds, extra=None, depth=None):
    keys = set(findings)
    gk = set(gt['keys'])
    prim = gt.get('primary')
    row = {'reported': len(keys), 'false_keys': sum(1 for k in keys if not an.correct(sym, k)),
           'detected': bool(keys & gk) if gk else None, 'primary_detected': (prim in keys) if prim else None,
           'alarm': bool(keys) if gt['decoy'] else None, 'slices': n_slices, 'seconds': seconds}
    if prim and prim in findings:
        f = findings[prim]
        top = f['top']
        row.update(top_size=sl.size(top), size_ratio=sl.size(top) / len(t.order),
                   exact=(top in gt_mms) if gt_mms else None,
                   minimum=(sl.size(top) == depth) if depth else None, precise=(top & ~root_hull) == 0,
                   hit=bool(top & root), cls=f.get('class'), n_minimal=len(f.get('minimal', [])))
    if extra:
        row.update(extra)
    return row


def run_team(args):
    topo, n, seed, cls, medium = args
    t0 = time.perf_counter()
    base = gen.generate(topo, n, seed)
    t, gt = inj.inject(base, cls, seed)
    try:
        sym = sem.symptoms(t, max_runs=500_000)
        exact_ok = True
    except sem.RunLimit:
        sym, exact_ok = {k: None for k in gt['keys']}, False
    root = t.nmask(gt['root']) if gt['root'] else 0
    root_hull = sl.hull(t, root) if root else 0
    rec = {'topo': topo, 'n': n, 'seed': seed, 'cls': cls, 'nodes': len(t.order), 'medium': medium,
           'gt_ok': set(gt['keys']) <= set(sym), 'exact_ok': exact_ok, 'sym': len(sym), 'checkers': {}}
    prim = gt.get('primary')

    def confirmed(slices):
        t1 = time.perf_counter()
        r = an.check_confirmed(t, slices)
        return r['findings'], time.perf_counter() - t1, r['stats']

    gt_mms = None
    rec['depth'] = None
    if not medium:
        K = 6 if len(t.order) <= 16 else 5
        rec['K'] = K
        ex = sl.exhaustive(t, K)
        loc_all, _, _ = confirmed(ex)
        if prim in loc_all:
            gt_mms = set(loc_all[prim]['minimal'])
            rec['depth'] = 1 if loc_all[prim]['static'] else min(sl.size(s) for s in gt_mms)
        else:
            rec['depth'] = None                       # deeper than K
        rec['depths'] = {str(k): (1 if loc_all[k]['static'] else min(sl.size(s) for s in loc_all[k]['minimal']))
                         for k in gt['keys'] if k in loc_all}
        for k in range(1, 6):
            sub = [s for s in ex if sl.size(s) <= k]
            loc, secs, st = confirmed(sub)
            rec['checkers'][f'k{k}'] = score(t, sym, gt, loc, gt_mms, root_hull, root, len(sub), secs, depth=rec['depth'])
    _score = score

    def score2(*a, **kw):
        return _score(*a, **kw, depth=rec.get('depth'))
    sizes = None
    for name in STRATS + ['SL']:
        slices = family(t, name)
        loc, secs, st = confirmed(slices)
        rec['checkers'][name] = score2(t, sym, gt, loc, gt_mms, root_hull, root, len(set(slices)), secs,
                                      {'lifts': st['lifts'], 'unconfirmed': st['unconfirmed']})
        if name == 'SL':
            sizes = [sl.size(s) for s in dict.fromkeys(slices)]
    # raw (unconfirmed) agent level and SL, to measure what confirmation removes
    for name, slices in [('B1raw', sl.singleton(t)), ('SLraw', family(t, 'SL'))]:
        t1 = time.perf_counter()
        r = an.check(t, slices)
        rec['checkers'][name] = score2(t, sym, gt, r['findings'], gt_mms, root_hull, root, len(set(slices)),
                                      time.perf_counter() - t1)
    rng = random.Random(f'B3/{topo}/{n}/{seed}/{cls}')
    rnd = sl.random_convex(t, sizes, rng)
    loc, secs, _ = confirmed(rnd)
    rec['checkers']['B3'] = score2(t, sym, gt, loc, gt_mms, root_hull, root, len(rnd), secs)
    if exact_ok:
        t1 = time.perf_counter()
        w = an.whole_team(t, 500_000)
        tb2 = time.perf_counter() - t1
        rec['checkers']['B2'] = score2(t, sym, gt, w['findings'], gt_mms, root_hull, root, 1, tb2)
        # B2-dev: deviation set of the witness; B2+shrink: greedy confirmed minimization
        dev, shr = {}, {}
        checks, t_shr = 0, 0.0
        for k, f in w['findings'].items():
            if f['static']:
                dev[k] = dict(f)
                shr[k] = dict(f)
                continue
            h = an.deviation_hull(t, k, f['witness'])
            dev[k] = {**f, 'top': h, 'minimal': [h]}
            if k == prim:
                t2 = time.perf_counter()
                s, c = an.shrink(t, k)
                t_shr += time.perf_counter() - t2
                checks += c
                shr[k] = {**f, 'top': s, 'minimal': [s]}
        rec['checkers']['B2dev'] = score2(t, sym, gt, dev, gt_mms, root_hull, root, 1, tb2)
        rec['checkers']['B2shrink'] = score2(t, sym, gt, {k: v for k, v in shr.items() if k == prim} | {
            k: v for k, v in dev.items() if k != prim}, gt_mms, root_hull, root, checks, tb2 + t_shr, {'checks': checks})
    rec['checkers']['B4'] = score2(t, sym, gt, an.lint(t)['findings'], gt_mms, root_hull, root, 0, 0.0)
    rec['checkers']['B5'] = score2(t, sym, gt, an.smells(t)['findings'], gt_mms, root_hull, root, 0, 0.0)
    t1 = time.perf_counter()
    rec['checkers']['B6'] = score2(t, sym, gt, an.must_analysis(t)['findings'], gt_mms, root_hull, root, 0,
                                  time.perf_counter() - t1)
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
    small = pmap(run_team, jobs(False), chunksize=2)
    medium = pmap(run_team, jobs(True), chunksize=2)
    save('e2_detection', {'env': env, 'K': 5, 'seconds': time.time() - t0, 'rows': small + medium})
    print('done', len(small), len(medium), round(time.time() - t0), 's')


if __name__ == '__main__':
    main()
