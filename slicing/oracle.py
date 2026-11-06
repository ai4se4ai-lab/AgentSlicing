"""Brute-force oracle over all contract-respecting models (Lemma W, Lemma M).

Shares no code with the checker's run enumeration: it enumerates every switch choice,
every admissible contributor set (not only minimal ones), every failure set |F| <= f
(not only maximal ones) and every evidence assignment E(v) between the realized minimum
c(v) U decl(v) and that minimum plus any of the bits that matter (req(v), goals at OUT).
"""
from __future__ import annotations

from itertools import combinations

from .model import ALL, INPUT, OUTPUT, Team


def _subsets(items):
    items = list(items)
    for r in range(len(items) + 1):
        yield from combinations(items, r)


def _bits(mask):
    out, i = [], 0
    while mask:
        if mask & 1:
            out.append(1 << i)
        mask >>= 1
        i += 1
    return out


def model_symptoms(team: Team, limit: int = 3_000_000) -> set:
    orcs = team.oracles
    fault_sets = [frozenset(F) for r in range(min(team.f, len(orcs)) + 1) for F in combinations(orcs, r)]
    found = set()
    budget = [limit]

    for F in fault_sets:
        def rec(i, reached, content, out, switch):
            budget[0] -= 1
            if budget[0] < 0:
                raise RuntimeError('oracle budget exceeded')
            if i == len(team.order):
                return
            n = team.order[i]
            node = team.nodes[n]
            req, gua, decl = team.mask[n]
            if n == INPUT:
                rec(i + 1, {**reached, n: True}, {**content, n: 0}, {**out, n: gua}, switch)
                return
            preds = team.pred[n]
            dlv = [p for p in preds if reached[p] and (team.nodes[p].route != 'switch' or switch.get(p) == n)]
            q = ALL if len(preds) <= 1 else node.join
            if q == ALL:
                opts = [preds] if len(dlv) == len(preds) else []
            else:
                opts = [C for C in _subsets(dlv) if len(C) >= q]
            if not opts:
                rec(i + 1, {**reached, n: False}, {**content, n: 0}, {**out, n: 0}, switch)
                return
            for C in opts:
                c = 0
                for p in C:
                    c |= out[p]
                base = c | decl
                matter = (req | (team.goal_mask if n == OUTPUT else 0)) & ~base
                for extra in _subsets(_bits(matter)):
                    E = base
                    for b in extra:
                        E |= b
                    applies = (req & ~E) == 0 and (node.kind == 'gate' or node.oracle not in F)
                    o = c | gua if applies else c
                    if not F:
                        miss = req & ~E
                        kind = 'goal' if n == OUTPUT else 'assume'
                        found.update((kind, n, p) for p in team.names(miss))
                    elif n == OUTPUT:
                        found.update(('robust', n, p) for p in team.names(team.crit_mask & ~E))
                    nxt = team.succ[n] if node.route == 'switch' and len(team.succ[n]) > 1 else [None]
                    for s in nxt:
                        sw = switch if s is None else {**switch, n: s}
                        rec(i + 1, {**reached, n: True}, {**content, n: c}, {**out, n: o}, sw)
        rec(0, {}, {}, {}, {})
    goal = {k[2] for k in found if k[0] == 'goal'}
    return {k for k in found if not (k[0] == 'robust' and k[2] in goal)}
