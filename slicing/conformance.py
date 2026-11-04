"""Independent oracles and theorem checks used by E1 and the test suite.

`hybrid_oracle` enumerates *all* runs of H_sigma (every switch choice, every admissible
contributor set, every failure set |F| <= f) and replays each with `analysis.hybrid_run`,
a separate evaluator from the enumerator in `semantics.findings`.
"""
from __future__ import annotations

import random
from itertools import combinations

from . import analysis as an
from . import contracts as ct
from . import incremental as inc
from . import semantics as sem
from . import slices as sl
from .model import ALL, INPUT, OUTPUT, Node, Team


def _subsets(items, q):
    items = list(items)
    for r in range(q, len(items) + 1):
        yield from combinations(items, r)


def hybrid_oracle(team: Team, sigma: int) -> set:
    members = [n for n in team.order if sigma & team.nbit[n]]
    orcs = sorted({team.nodes[n].oracle for n in members if team.nodes[n].kind == 'agent'})
    fsets = [frozenset(c) for r in range(min(team.f, len(orcs)) + 1) for c in combinations(orcs, r)] \
        if team.f and team.crit_mask else [frozenset()]
    found = set()
    region = sigma
    for n in members:
        region |= team.desc[n]
    for F in fsets:
        def rec(i, choices):
            if i == len(members):
                w = {'choices': choices, 'faults': sorted(F)}
                reached, content, out, _ = an.hybrid_run(team, sigma, w)
                for n in team.order:
                    if not reached[n] or n == INPUT:
                        continue
                    req, _, decl = team.mask[n]
                    if not F:
                        miss = req & ~(content[n] | decl)
                        kind = 'goal' if n == OUTPUT else 'assume'
                        found.update((kind, n, p) for p in team.names(miss))
                    elif n == OUTPUT:
                        found.update(('robust', n, p) for p in team.names(team.crit_mask & ~content[n]))
                return
            n = members[i]
            node = team.nodes[n]
            # replay up to n to know what is delivered: evaluate prefix with current choices
            reached, _, _, _ = an.hybrid_run(team, sigma, {'choices': choices, 'faults': sorted(F)})
            preds = team.pred[n]
            opts = [None]
            if len(preds) > 1 and node.join != ALL and reached.get(n):
                dl = [p for p in preds if not sigma & team.nbit[p] or
                      (reached[p] and (team.nodes[p].route != 'switch' or
                                       dict((k, v) for t, k, v in choices if t == 'switch').get(p) == n))]
                opts = [('contrib', n, list(C)) for C in _subsets(dl, node.join)]
            sw = [None]
            if node.route == 'switch' and len(team.succ[n]) > 1:
                sw = [('switch', n, s) for s in team.succ[n]]
            for o in opts:
                for s in sw:
                    rec(i + 1, choices + [x for x in (o, s) if x is not None])
        rec(0, [])
    goal = {k[2] for k in found if k[0] == 'goal'}
    return {k for k in found if not (k[0] == 'robust' and k[2] in goal)}


def wild_team(seed: int, n: int = 5, props: int = 4) -> Team:
    """Random team with arbitrary contracts, policies, switches and faults (not clean)."""
    rng = random.Random(seed)
    ids = [f'n{i}' for i in range(n)]
    P = [f'p{i}' for i in range(props)]
    edges = []
    for j, v in enumerate(ids):
        cands = [INPUT] + ids[:j]
        k = 1 if rng.random() < 0.6 else 2
        for u in rng.sample(cands, min(k, len(cands))):
            edges.append((u, v))
    for u in ids:
        if not any(a == u for a, _ in edges) or rng.random() < 0.2:
            edges.append((u, OUTPUT))
    nodes = [Node(INPUT, 'gate', gua=frozenset(rng.sample(P, 1)))]
    goals = frozenset(rng.sample(P, 2))
    crit = frozenset(rng.sample(sorted(goals), 1)) if rng.random() < 0.5 else frozenset()
    indeg = {}
    for u, v in edges:
        indeg[v] = indeg.get(v, 0) + 1
    for v in ids:
        kind = 'gate' if rng.random() < 0.3 else 'agent'
        join = ALL if indeg.get(v, 0) < 2 or rng.random() < 0.4 else rng.randint(1, indeg[v])
        nodes.append(Node(v, kind, frozenset(rng.sample(P, rng.randint(0, 2))), frozenset(rng.sample(P, rng.randint(0, 2))),
                          frozenset(rng.sample(P, 1)) if rng.random() < 0.1 else frozenset(),
                          rng.choice(['a', 'b']) if kind == 'agent' else None,
                          'switch' if rng.random() < 0.25 else 'fork', join))
    oj = ALL if indeg.get(OUTPUT, 0) < 2 or rng.random() < 0.5 else 1
    nodes.append(Node(OUTPUT, 'gate', req=goals, join=oj))
    return Team(nodes, edges, goals, crit, rng.choice([0, 1, 1]), f'wild{seed}')


def lifts(team: Team, sigma: int, key, witness) -> bool:
    """T3(b): is there an exact run agreeing inside sigma that exhibits the key?"""
    return key in sem.symptoms(team)


def check_team(team: Team, kmax: int = 3) -> dict:
    """Run all theorem checks on one small team; return mismatch counts per check."""
    out = {}
    sym = sem.symptoms(team)
    full = (1 << len(team.order)) - 1
    # H_N = T (exact semantics vs independent replay oracle)
    out['HN_equals_T'] = int(set(sym) != hybrid_oracle(team, full))
    slices = sl.exhaustive(team, kmax)
    mism = 0
    fam = {}
    for s in slices:
        f = set(sem.findings(team, s))
        fam[s] = f
        if f != hybrid_oracle(team, s):
            mism += 1
    out['hybrid_vs_oracle'] = mism
    # Lemma A at the level of findings: F(empty) subset F({v}) when v is reached somewhere
    static = set(sem.static_findings(team))
    out['static_in_singletons'] = sum(1 for v in team.order if not static <= fam[team.nbit[v]])
    # T4(c) recovery: AL findings at v persist in every slice containing v (live teams)
    live = sem.live_nodes(team)
    rec = 0
    for v in team.order:
        if v not in live:
            continue
        al_v = {k for k in fam[team.nbit[v]] if k[1] == v}
        for s in slices:
            if s & team.nbit[v] and not al_v <= fam[s]:
                rec += 1
    out['recovery'] = rec
    # T5(c): the hull of a witness lineage manifests the key
    bad = 0
    for k, w in sym.items():
        if not w.get('slice'):
            continue
        h = an.lineage_hull(team, k, w)
        if k not in sem.findings(team, h):
            bad += 1
    out['witness_hull'] = bad
    # T5(a)/T3(a): every symptom of T is found by the whole slice; whole-slice findings are exact
    out['whole_exact'] = int(set(sem.findings(team, full)) != set(sym))
    # T2(d): partition with acyclic quotient, part summaries composed in quotient order
    parts = random_partition(team, random.Random(len(team.edges)))
    if parts is not None:
        out['quotient'] = int(set(ct.quotient_symptoms(team, parts)) != set(sym))
    # T8: incremental = full after a random change
    out['incremental'] = incremental_check(team, slices)
    return out


def random_partition(team: Team, rng: random.Random, tries: int = 20):
    for _ in range(tries):
        order = list(team.order)
        parts, cur = [], 0
        for n in order:
            cur |= team.nbit[n]
            if rng.random() < 0.45:
                parts.append(cur)
                cur = 0
        if cur:
            parts.append(cur)
        if all(sl.is_convex(team, p) for p in parts) and sl.quotient_is_acyclic(team, parts):
            if max(sl.size(p) for p in parts) <= 4:
                return parts
    return None


def mutate(team: Team, rng: random.Random):
    """A random change: (new team, change descriptor)."""
    inner = [n for n in team.order if n not in (INPUT, OUTPUT)]
    if not inner:
        return team, {'node': OUTPUT, 'field': 'join'}
    a = rng.choice(inner)
    node = team.nodes[a]
    field = rng.choice(['req', 'gua', 'oracle', 'kind', 'join', 'route', 'decl'])
    props = list(team.props) + ['fresh']
    if field in ('req', 'gua', 'decl'):
        cur = set(getattr(node, field))
        p = rng.choice(props)
        cur ^= {p}
        new = team.replace(a, **{field: frozenset(cur)})
    elif field == 'oracle':
        new = team.replace(a, kind='agent', oracle=rng.choice(['a', 'b', 'c']))
        field = 'kind'
    elif field == 'kind':
        k = 'gate' if node.kind == 'agent' else 'agent'
        new = team.replace(a, kind=k, oracle=None if k == 'gate' else 'a')
    elif field == 'join':
        d = len(team.pred[a])
        new = team.replace(a, join=ALL if node.join != ALL or d < 2 else rng.randint(1, d))
    else:
        new = team.replace(a, route='switch' if node.route == 'fork' else 'fork')
    return new, {'node': a, 'field': field}


def incremental_check(team: Team, slices: list[int]) -> int:
    rng = random.Random(len(slices) * 7 + len(team.edges))
    old_res = inc.full(team, slices)
    new, change = mutate(team, rng)
    new_family = [s for s in slices if sl.is_convex(new, s)]
    r = inc.recertify(team, new, change, old_res, new_family)
    truth = inc.full(new, new_family)
    return sum(1 for s in new_family if r['results'][s] != truth[s])
