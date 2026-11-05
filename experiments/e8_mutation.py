"""E8 (RQ2): naturally arising defects. Clean generated teams (one critical goal, f = 1) receive
one to three random engineering changes (mutations); whatever symptoms result are the ground
truth (exact semantics, cross-checked with the independent replay oracle on small teams).
Neither the class nor the depth of a defect is chosen by the experimenter."""
from __future__ import annotations

import random
import time
from dataclasses import replace

from common import environment, pmap, save
from slicing import analysis as an, conformance as cf, generator as gen, semantics as sem, slices as sl
from slicing.generator import Params
from slicing.model import ALL, INPUT, OUTPUT, Team

OPS = ['relax_join', 'share_oracle', 'drop_guarantee', 'gate_to_agent', 'add_requirement', 'fork_to_switch',
       'remove_edge']


def mutate(t: Team, rng: random.Random):
    """One random engineering change; returns (team, op) or (None, op) if not applicable."""
    op = rng.choice(OPS)
    inner = [n for n in t.order if n not in (INPUT, OUTPUT)]
    nodes = dict(t.nodes)
    edges = list(t.edges)
    if op == 'relax_join':
        c = [n for n in t.order if len(t.pred[n]) > 1 and t.nodes[n].join == ALL]
        if not c:
            return None, op
        n = rng.choice(c)
        nodes[n] = replace(nodes[n], join=rng.randint(1, len(t.pred[n]) - 1))
    elif op == 'share_oracle':
        ag = [n for n in inner if t.nodes[n].kind == 'agent']
        pairs = [(a, b) for a in ag for b in ag if t.nodes[a].oracle != t.nodes[b].oracle]
        if not pairs:
            return None, op
        a, b = rng.choice(pairs)
        nodes[b] = replace(nodes[b], oracle=t.nodes[a].oracle)
    elif op == 'drop_guarantee':
        c = [(n, p) for n in inner for p in sorted(t.nodes[n].gua)]
        if not c:
            return None, op
        n, p = rng.choice(c)
        nodes[n] = replace(nodes[n], gua=t.nodes[n].gua - {p})
    elif op == 'gate_to_agent':
        c = [n for n in inner if t.nodes[n].kind == 'gate']
        if not c or not t.oracles:
            return None, op
        n = rng.choice(c)
        nodes[n] = replace(nodes[n], kind='agent', oracle=rng.choice(t.oracles))
    elif op == 'add_requirement':
        claimed = sorted({p for n in t.order if n != INPUT for p in t.nodes[n].gua})
        if not claimed:
            return None, op
        n = rng.choice(inner)
        nodes[n] = replace(nodes[n], req=t.nodes[n].req | {rng.choice(claimed)})
    elif op == 'fork_to_switch':
        c = [n for n in inner if len(t.succ[n]) > 1 and t.nodes[n].route == 'fork']
        if not c:
            return None, op
        n = rng.choice(c)
        nodes[n] = replace(nodes[n], route='switch')
    elif op == 'remove_edge':
        c = [(u, v) for u, v in t.edges if len(t.succ[u]) > 1 and len(t.pred[v]) > 1]
        if not c:
            return None, op
        e = rng.choice(c)
        edges.remove(e)
        v = e[1]
        if nodes[v].join != ALL and nodes[v].join > len(t.pred[v]) - 1:
            nodes[v] = replace(nodes[v], join=max(1, len(t.pred[v]) - 1))
    return Team(nodes.values(), edges, t.goals, t.critical, t.f, t.name), op


def run(args):
    topo, n, seed, m = args
    rng = random.Random(f'e8/{topo}/{n}/{seed}/{m}')
    t = gen.generate(topo, n, seed, Params(n_critical=1))
    ops = []
    tries = 0
    while len(ops) < m and tries < 50:            # retry until m changes were actually applied
        tries += 1
        new, op = mutate(t, rng)
        if new is not None and not new.validate():
            t = new
            ops.append(op)
    rec = {'topo': topo, 'n': n, 'seed': seed, 'm': m, 'ops': ops, 'nodes': len(t.order)}
    try:
        sym = sem.symptoms(t, 500_000)
    except sem.RunLimit:
        rec['skipped'] = True
        return rec
    full = (1 << len(t.order)) - 1
    if len(t.order) <= 12:
        rec['oracle_agrees'] = set(sym) == cf.hybrid_oracle(t, full)
    rec['symptoms'] = [list(k) for k in sym]
    rec['unsafe'] = not sem.is_safe(sym)
    if not sym:
        return rec
    K = 6 if len(t.order) <= 16 else 5
    rec['K'] = K
    gt = an.check_confirmed(t, sl.exhaustive(t, K))['findings']
    depth = {k: (1 if gt[k]['static'] else min(sl.size(s) for s in gt[k]['minimal'])) if k in gt else None for k in sym}
    rec['depth'] = {str(k): d for k, d in depth.items()}
    slf = list(dict.fromkeys(sl.singleton(t) + sl.window(t, 2) + sl.region(t) + sl.goal_directed(t)))
    runners = {
        'B1': lambda: an.check_confirmed(t, sl.singleton(t))['findings'],
        'B1raw': lambda: an.check(t, sl.singleton(t))['findings'],
        'SL': lambda: an.check_confirmed(t, slf)['findings'],
        'SLraw': lambda: an.check(t, slf)['findings'],
        'B4': lambda: an.lint(t)['findings'], 'B5': lambda: an.smells(t)['findings'],
        'B6': lambda: an.must_analysis(t)['findings'],
    }
    checkers, times = {}, {}
    for name, fn in runners.items():
        t0 = time.perf_counter()
        checkers[name] = fn()
        times[name] = time.perf_counter() - t0
    t0 = time.perf_counter()
    sem.symptoms(t, 500_000)
    times['B2'] = time.perf_counter() - t0
    rec['times'] = times
    rec['checkers'] = {}
    for name, f in checkers.items():
        keys = set(f)
        per = {}
        for k in sym:
            d = {'found': k in keys}
            if k in keys and gt.get(k) and not f[k].get('static') and depth[k]:
                top = f[k]['top']
                d.update(exact=top in set(gt[k]['minimal']), minimum=sl.size(top) == depth[k], size=sl.size(top))
            per[str(k)] = d
        rec['checkers'][name] = {'per_key': per, 'reported': len(keys),
                                 'false_keys': sum(1 for k in keys if not an.correct(sym, k))}
    # whole-team witness + shrinking for hidden keys
    shr = {}
    for k, w in sym.items():
        if depth[k] and depth[k] >= 2 and w.get('slice'):
            t0 = time.perf_counter()
            s, c = an.shrink(t, k)
            rec.setdefault('shrink_seconds', []).append(time.perf_counter() - t0)
            dev = an.deviation_hull(t, k, w)
            shr[str(k)] = {'shrink_exact': s in set(gt[k]['minimal']), 'shrink_minimum': sl.size(s) == depth[k],
                           'shrink_checks': c, 'dev_exact': dev in set(gt[k]['minimal']), 'dev_size': sl.size(dev),
                           'dev_precise_size_ratio': sl.size(dev) / len(t.order)}
    rec['shrink'] = shr
    return rec


def main():
    env = environment()
    t0 = time.time()
    jobs = [(topo, n, s, m) for topo in gen.TOPOLOGIES for n in (6, 10, 20, 30) for s in range(20) for m in (1, 2, 3)]
    rows = pmap(run, jobs, chunksize=2)
    save('e8_mutation', {'env': env, 'seconds': time.time() - t0, 'rows': rows})
    print('done', len(rows), round(time.time() - t0), 's')


if __name__ == '__main__':
    main()
