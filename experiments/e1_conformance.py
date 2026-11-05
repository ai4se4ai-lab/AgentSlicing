"""E1 (RQ1): theorem validation by exhaustive/randomized conformance against oracles.

* wild teams: arbitrary contracts, policies, switches and faults (3-7 nodes);
* benchmark teams: generated clean teams with injected defects (small);
* Lemma W/M: model oracle (all evidence models) vs run semantics on tiny teams;
* T7(a): the CNF reduction (symptom iff satisfiable) on random 3-CNFs;
* T4(b): fooling sets for S2, S4, S6a (singleton views of the unsafe team occur in safe teams).
"""
from __future__ import annotations

import collections
import itertools
import random
import time

from common import environment, pmap, save
from slicing import conformance as cf, generator as gen, injector as inj, oracle, semantics as sem
from slicing.model import ALL, INPUT, OUTPUT, Node, Team


def wild(seed):
    t = cf.wild_team(seed, n=3 + seed % 5)
    r = cf.check_team(t, kmax=3)
    if len(t.order) <= 6:
        r['model_oracle'] = int(oracle.model_symptoms(t, 3_000_000) != set(sem.symptoms(t)))
    return r


def bench(args):
    topo, seed, cls = args
    t, _ = inj.inject(gen.generate(topo, 4 + seed % 4, seed), cls, seed, depth=seed % 2)
    if len(t.order) > 16:
        return {}
    return cf.check_team(t, kmax=2)


def cnf_team(clauses, nvars):
    nodes, edges = [Node(INPUT, 'gate')], []
    prev = INPUT
    for i in range(nvars):
        w = Node(f'w{i}', 'gate', route='switch')
        tn = Node(f't{i}', 'gate', gua=frozenset({f't{i}'}))
        fn = Node(f'f{i}', 'gate', gua=frozenset({f'f{i}'}))
        m = Node(f'm{i}', 'gate', join=1)
        nodes += [w, tn, fn, m]
        edges += [(prev, w.id), (w.id, tn.id), (w.id, fn.id), (tn.id, m.id), (fn.id, m.id)]
        prev = m.id
    for j, cl in enumerate(clauses):
        req = frozenset(f'f{v}' if pos else f't{v}' for v, pos in cl)     # facts that falsify the clause
        k = Node(f'k{j}', 'gate', req=req, gua=frozenset({'bad'}))
        nodes.append(k)
        edges.append((prev, k.id))
        prev = k.id
    nodes.append(Node(OUTPUT, 'gate', req=frozenset({'bad'})))
    edges.append((prev, OUTPUT))
    return Team(nodes, edges, ['bad'])


def cnf_team_robust(clauses, nvars):
    """Robust-key variant (coNP-hardness): an agent A (oracle o) provides tok after the variable
    gadgets; every clause gate requires tok and guarantees the critical goal c; f = 1.
    Failing o always loses c; fault-free, c is missing iff the formula is satisfiable.
    Hence (robust, OUT, c) is a symptom iff the formula is unsatisfiable."""
    nodes, edges = [Node(INPUT, 'gate')], []
    prev = INPUT
    for i in range(nvars):
        w = Node(f'w{i}', 'gate', route='switch')
        tn = Node(f't{i}', 'gate', gua=frozenset({f't{i}'}))
        fn = Node(f'f{i}', 'gate', gua=frozenset({f'f{i}'}))
        m = Node(f'm{i}', 'gate', join=1)
        nodes += [w, tn, fn, m]
        edges += [(prev, w.id), (w.id, tn.id), (w.id, fn.id), (tn.id, m.id), (fn.id, m.id)]
        prev = m.id
    nodes.append(Node('A', 'agent', gua=frozenset({'tok'}), oracle='o'))
    edges.append((prev, 'A'))
    prev = 'A'
    for j, cl in enumerate(clauses):
        req = frozenset(f'f{v}' if pos else f't{v}' for v, pos in cl) | {'tok'}
        nodes.append(Node(f'k{j}', 'gate', req=req, gua=frozenset({'c'})))
        edges.append((prev, f'k{j}'))
        prev = f'k{j}'
    nodes.append(Node(OUTPUT, 'gate', req=frozenset({'c'})))
    edges.append((prev, OUTPUT))
    return Team(nodes, edges, ['c'], ['c'], 1)


def cnf_team_robust_np(clauses, nvars):
    """Robust-key NP-hardness: a gate P guarantees the critical goal phi iff some clause is
    falsified (bad present); an agent A (oracle o) also guarantees phi. Fault-free, phi always
    arrives; failing o misses phi iff the formula is satisfiable."""
    base = cnf_team(clauses, nvars)
    nodes = [n for n in base.nodes.values() if n.id != OUTPUT]
    last = base.pred[OUTPUT][0]
    edges = [e for e in base.edges if e[1] != OUTPUT]
    nodes += [Node('P', 'gate', req=frozenset({'bad'}), gua=frozenset({'phi'})), Node('A', 'agent', gua=frozenset({'phi'}), oracle='o'),
              Node(OUTPUT, 'gate', req=frozenset({'phi'}))]
    edges += [(last, 'P'), ('P', 'A'), ('A', OUTPUT)]
    return Team(nodes, edges, ['phi'], ['phi'], 1)


def reach_team(clauses, nvars):
    """Reachability NP-hardness: switches pick literals, any-joins form clauses, an all-join R of
    all clauses is reached iff the formula is satisfiable (R requires an unclaimed property)."""
    nodes, edges = [Node(INPUT, 'gate'), Node(OUTPUT, 'gate', join=1)], []
    for i in range(nvars):
        nodes += [Node(f'w{i}', 'gate', route='switch'), Node(f't{i}', 'gate'), Node(f'f{i}', 'gate')]
        edges += [(INPUT, f'w{i}'), (f'w{i}', f't{i}'), (f'w{i}', f'f{i}'), (f't{i}', OUTPUT), (f'f{i}', OUTPUT)]
    for j, cl in enumerate(clauses):
        nodes.append(Node(f'c{j}', 'gate', join=1))
        edges += [(f't{v}' if pos else f'f{v}', f'c{j}') for v, pos in cl] + [(f'c{j}', 'R')]
    nodes.append(Node('R', 'gate', req=frozenset({'never'})))
    edges.append(('R', OUTPUT))
    return Team(nodes, edges, [], [], 0)


def reduction(seed):
    rng = random.Random(seed)
    n = rng.randint(2, 6)
    m = rng.randint(n, 7 * n)
    clauses = [[(v, rng.random() < 0.5) for v in rng.sample(range(n), min(3, n))] for _ in range(m)]
    sat = any(all(any(a[v] == pos for v, pos in cl) for cl in clauses) for a in itertools.product([False, True], repeat=n))
    unsafe = ('goal', OUTPUT, 'bad') in sem.symptoms(cnf_team(clauses, n))
    robust = ('robust', OUTPUT, 'c') in sem.symptoms(cnf_team_robust(clauses, n))
    robust_np = ('robust', OUTPUT, 'phi') in sem.symptoms(cnf_team_robust_np(clauses, n))
    reach = ('assume', 'R', 'never') in sem.symptoms(reach_team(clauses, n))
    return {'sat': sat, 'unsafe': unsafe, 'robust': robust, 'robust_np': robust_np, 'reach': reach}


def fooling():
    """T4(b): views = (own contract, kind, oracle, policy, set of properties claimed by ancestors)."""
    from slicing.model import build

    def views(t):
        from slicing.semantics import face_value
        _, fvc = face_value(t)
        return {(n, t.nodes[n].kind, t.nodes[n].oracle, t.nodes[n].join, t.nodes[n].route,
                 t.nodes[n].req, t.nodes[n].gua, frozenset(t.names(fvc[n]))) for n in t.order}
    out = {}
    # S4: reviewers on oracles (o1,o2) and (o2,o1) are safe; (o1,o1) is unsafe
    mk = lambda a, b: build([('R1', 'agent', [], ['crit'], a), ('R2', 'agent', [], ['crit'], b)],
                            [('IN', 'R1'), ('R1', 'R2'), ('R2', 'OUT')], goals=['crit'], critical=['crit'], f=1)
    safe, unsafe = [mk('o1', 'o2'), mk('o2', 'o1')], mk('o1', 'o1')
    out['S4'] = _fooled(safe, unsafe, views)
    # S2: join any with both branches claiming both goals is safe; with split claims unsafe
    fj = lambda c1, c2, pol: build([('B1', 'agent', [], c1), ('B2', 'agent', [], c2), ('J', 'gate', [], [], None, 'fork', pol)],
                                   [('IN', 'B1'), ('IN', 'B2'), ('B1', 'J'), ('B2', 'J'), ('J', 'OUT')], goals=['g1', 'g2'])
    safe = [fj(['g1'], ['g2'], 'all'), fj(['g1', 'g2'], ['g1', 'g2'], 'any'), fj(['g1'], ['g2'], 'any')]
    # views of B1/B2 come from the 'all' team, the view of J (any, cone {g1,g2}) from the doubly-claimed team
    out['S2'] = _fooled(safe[:2], safe[2], views)
    # S6a: provider gate -> consumer gate is safe; fallible provider + extra backup gate H is safe
    s6 = lambda kind, extra: build([('A', kind, [], ['x'], 'o1' if kind == 'agent' else None), ('G', 'gate', ['x'], ['crit'])] +
                                   ([('H', 'gate', [], ['crit'])] if extra else []),
                                   [('IN', 'A'), ('A', 'G')] + ([('G', 'H'), ('H', 'OUT')] if extra else [('G', 'OUT')]),
                                   goals=['crit'], critical=['crit'], f=1)
    out['S6a'] = _fooled([s6('gate', False), s6('agent', True)], s6('agent', False), views)
    return out


def _fooled(safe_teams, unsafe, views):
    ok_safe = all(sem.is_safe(sem.symptoms(t)) for t in safe_teams)
    bad = not sem.is_safe(sem.symptoms(unsafe))
    covered = views(unsafe) <= set().union(*(views(t) for t in safe_teams))
    slice_finds = any(k[0] in ('goal', 'robust') for k in sem.symptoms(unsafe))
    return {'safe_teams_safe': ok_safe, 'unsafe_is_unsafe': bad, 'views_covered': covered, 'whole_slice_detects': slice_finds}


def main():
    env = environment()
    t0 = time.time()
    N_WILD = 20_000
    wild_rows = pmap(wild, range(N_WILD), chunksize=50)
    agg = collections.Counter()
    tried = collections.Counter()
    for r in wild_rows:
        for k, v in r.items():
            tried[k] += 1
            agg[k] += int(v > 0)
    jobs = [(topo, s, c) for topo in gen.TOPOLOGIES for s in range(10) for c in inj.CLASSES + inj.DECOYS + ('clean',)]
    bench_rows = pmap(bench, jobs, chunksize=10)
    bagg, btried = collections.Counter(), collections.Counter()
    for r in bench_rows:
        for k, v in r.items():
            btried[k] += 1
            bagg[k] += int(v > 0)
    red = pmap(reduction, range(500), chunksize=20)
    payload = {'env': env, 'seconds': time.time() - t0,
               'wild': {'teams': N_WILD, 'checked': dict(tried), 'mismatching_teams': dict(agg)},
               'bench': {'teams': sum(1 for r in bench_rows if r), 'checked': dict(btried), 'mismatching_teams': dict(bagg)},
               'reduction': {'formulas': len(red), 'satisfiable': sum(r['sat'] for r in red),
                             'disagreements': sum(r['sat'] != r['unsafe'] for r in red),
                             'robust_disagreements': sum(r['sat'] == r['robust'] for r in red),
                             'robust_np_disagreements': sum(r['sat'] != r['robust_np'] for r in red),
                             'reach_disagreements': sum(r['sat'] != r['reach'] for r in red)},
               'fooling': fooling()}
    save('e1_conformance', payload)
    print(payload['wild'], payload['bench'], payload['reduction'], payload['fooling'], round(payload['seconds']), 's')


if __name__ == '__main__':
    main()
