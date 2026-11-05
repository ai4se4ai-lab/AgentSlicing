"""E7: sensitivity (gate share, oracle sharing, contract density) and ablations
(joins treated as all, non-convex slices, no fault reasoning); false alarms on random wild teams."""
from __future__ import annotations

import random
import time
from dataclasses import replace

from common import environment, pmap, save
from slicing import conformance as cf, generator as gen, injector as inj, semantics as sem, slices as sl
from slicing.generator import Params
from slicing.model import ALL, Team

HID = ['S2', 'S3', 'S4', 'S6a', 'S6b']
TOPOS = ['tree', 'forkjoin', 'layered', 'sp', 'random', 'mixed']


def sl_family(t):
    return list(dict.fromkeys(sl.singleton(t) + sl.window(t, 2) + sl.region(t) + sl.goal_directed(t)))


def keys_of(t, fam):
    found = set(sem.static_findings(t))
    for s in fam:
        try:
            found |= set(sem.findings(t, s, 50_000))
        except sem.RunLimit:
            pass
    return found


def sensitivity(args):
    param, value, topo, seed, cls = args
    p = replace(Params(), **{param: value})
    t, gt = inj.inject(gen.generate(topo, 15, seed, p), cls, seed)
    sym = set(sem.symptoms(t, 500_000))
    sl_keys = keys_of(t, sl_family(t))
    al_keys = keys_of(t, sl.singleton(t))
    prim = gt.get('primary')
    return {'param': param, 'value': value, 'topo': topo, 'seed': seed, 'cls': cls,
            'sl': (prim in sl_keys) if prim else bool(sl_keys), 'al': (prim in al_keys) if prim else bool(al_keys),
            'sl_false': len(sl_keys - sym)}


def ablation(args):
    topo, seed, cls = args
    t, gt = inj.inject(gen.generate(topo, 12, seed), cls, seed)
    prim = gt['primary']
    sym = set(sem.symptoms(t))
    full = prim in keys_of(t, sl_family(t))
    ta = Team([replace(n, join=ALL) for n in t.nodes.values()], t.edges, t.goals, t.critical, t.f, t.name)
    a = prim in keys_of(ta, sl_family(ta))           # (a) analysis ignores join policies
    tc = Team(t.nodes.values(), t.edges, t.goals, t.critical, 0, t.name)
    c = prim in keys_of(tc, sl_family(tc))           # (c) no fault reasoning
    rng = random.Random(seed)                        # (b) non-convex: drop one interior node
    nc_keys, nc_false, tried = set(sem.static_findings(t)), 0, 0
    for s in sl_family(t) + sl.exhaustive(t, 4):
        nodes = t.nodes_of(s)
        inner = [x for x in nodes if t.anc[x] & s and t.desc[x] & s]
        if not inner:
            continue
        s2 = s & ~t.nbit[rng.choice(inner)]
        tried += 1
        try:
            f = set(sem.findings(t, s2, 50_000))
        except sem.RunLimit:
            continue
        nc_keys |= f
        nc_false += len(f - sym)
    return {'topo': topo, 'seed': seed, 'cls': cls, 'full': full, 'joins_as_all': a, 'no_faults': c,
            'nonconvex_tried': tried, 'nonconvex_false_keys': nc_false}


def wild_false(seed):
    """Raw vs. confirmed findings of all convex slices (size <= 3) on unstructured teams, and
    non-convex slices (a convex slice minus one interior node)."""
    from slicing import analysis as an
    t = cf.wild_team(seed, n=5 + seed % 3)
    symd = sem.symptoms(t)
    out = {'teams': 1, 'findings': 0, 'false': 0, 'slices': 0, 'slices_false': 0, 'confirmed': 0,
           'confirmed_false': 0, 'true_lost': 0, 'lift_seconds': 0.0, 'nc_slices': 0, 'nc_findings': 0, 'nc_false': 0}
    rng = random.Random(seed)
    for s in sl.exhaustive(t, 3):
        f = set(sem.findings(t, s))
        out['slices'] += 1
        out['findings'] += len(f)
        bad = sum(1 for k in f if not an.correct(symd, k))
        out['false'] += bad
        out['slices_false'] += int(bad > 0)
        t0 = time.perf_counter()
        c = set(an.confirmed_findings(t, s))
        out['lift_seconds'] += time.perf_counter() - t0
        out['confirmed'] += len(c)
        out['confirmed_false'] += sum(1 for k in c if not an.correct(symd, k))
        out['true_lost'] += sum(1 for k in f if an.correct(symd, k) and k not in c)
        inner = [x for x in t.nodes_of(s) if t.anc[x] & s and t.desc[x] & s]
        if inner:
            s2 = s & ~t.nbit[rng.choice(inner)]
            f2 = set(sem.findings(t, s2))
            out['nc_slices'] += 1
            out['nc_findings'] += len(f2)
            out['nc_false'] += sum(1 for k in f2 if not an.correct(symd, k))
    return out


def main():
    env = environment()
    t0 = time.time()
    grid = {'p_gate': [0.0, 0.25, 0.5], 'oracle_pool': [1, 3, 6], 'req_density': [1, 2, 3]}
    jobs = [(p, v, topo, s, c) for p, vs in grid.items() for v in vs for topo in TOPOS for s in range(10) for c in HID + ['clean']]
    sens = pmap(sensitivity, jobs, chunksize=8)
    abl = pmap(ablation, [(topo, s, c) for topo in TOPOS for s in range(10) for c in HID], chunksize=4)
    wild = pmap(wild_false, range(3000), chunksize=50)
    tot = {k: sum(w[k] for w in wild) for k in wild[0]}
    save('e7_ablation', {'env': env, 'seconds': time.time() - t0, 'sensitivity': sens, 'ablation': abl, 'wild_false_alarms': tot})
    print('done', round(time.time() - t0), 's', tot)


if __name__ == '__main__':
    main()
