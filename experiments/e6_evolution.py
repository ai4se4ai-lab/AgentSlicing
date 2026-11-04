"""E6 (RQ3): incremental recertification after random changes (contract, kind, policy, route, edge)."""
from __future__ import annotations

import random
import time

from common import environment, pmap, save
from slicing import conformance as cf, generator as gen, incremental as inc, injector as inj, slices as sl
from slicing.model import Team

TOPOS = ['chain', 'tree', 'forkjoin', 'layered', 'sp', 'random', 'mixed']


def family(t):
    return list(dict.fromkeys(sl.singleton(t) + sl.window(t, 2) + sl.region(t) + sl.goal_directed(t)))


def edge_change(t: Team, rng):
    if rng.random() < 0.5:   # add an edge forward in topological order
        for _ in range(50):
            i, j = sorted(rng.sample(range(1, len(t.order) - 1), 2))
            u, v = t.order[i], t.order[j]
            if (u, v) not in t.edges:
                return Team(t.nodes.values(), list(t.edges) + [(u, v)], t.goals, t.critical, t.f, t.name), {'edge': (u, v)}
    cands = [(u, v) for u, v in t.edges if len(t.succ[u]) > 1 and len(t.pred[v]) > 1]
    if not cands:
        return None
    u, v = rng.choice(cands)
    return Team(t.nodes.values(), [e for e in t.edges if e != (u, v)], t.goals, t.critical, t.f, t.name), {'edge': (u, v)}


def run(args):
    topo, n, seed = args
    rng = random.Random(f'e6/{topo}/{n}/{seed}')
    t, _ = inj.inject(gen.generate(topo, n, seed), rng.choice(['S2', 'S3', 'S4', 'S6a', 'clean']), seed)
    fam = family(t)
    t0 = time.perf_counter()
    base = inc.full(t, fam)
    full_s = time.perf_counter() - t0
    rows = []
    for _ in range(10):
        if rng.random() < 0.2:
            r = edge_change(t, rng)
            if r is None:
                continue
            new, change = r
            kind = 'edge'
        else:
            new, change = cf.mutate(t, rng)
            kind = change['field']
        new_fam = family(new)
        old_ok = {s: v for s, v in base.items() if sl.is_convex(new, s)}
        res = inc.recertify(t, new, change, old_ok, new_fam)
        f0 = time.perf_counter()
        truth = inc.full(new, new_fam)
        rows.append({'change': kind, 'redone': res['redone'], 'total': res['total'], 'inc_seconds': res['seconds'],
                     'full_seconds': time.perf_counter() - f0,
                     'agree': all(res['results'][s] == truth[s] for s in new_fam)})
    return {'topo': topo, 'n': n, 'seed': seed, 'nodes': len(t.order), 'slices': len(fam), 'base_seconds': full_s, 'changes': rows}


def main():
    env = environment()
    t0 = time.time()
    rows = pmap(run, [(topo, n, s) for topo in TOPOS for n in (20, 40) for s in range(10)])
    save('e6_evolution', {'env': env, 'seconds': time.time() - t0, 'rows': rows})
    print('done', len(rows), round(time.time() - t0), 's')


if __name__ == '__main__':
    main()
