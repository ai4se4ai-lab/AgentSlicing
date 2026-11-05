"""Slice contracts (Def. 8) and compositional evaluation over a partition (Theorem T2).

A member's content is tracked symbolically as (flow, added): the set of entry edges whose
content reaches it and the mask of properties added inside the slice. This makes the
boundary behaviour of a part independent of the rest of the team, so a part can be
summarized in isolation and the summaries composed along an acyclic quotient.
"""
from __future__ import annotations

from itertools import combinations

from . import semantics as sem
from .model import ALL, INPUT, OUTPUT, Team


def _entries(team: Team, sigma: int):
    return [(u, v) for u, v in team.edges if not sigma & team.nbit[u] and sigma & team.nbit[v]]


def _exits(team: Team, sigma: int):
    return [(u, v) for u, v in team.edges if sigma & team.nbit[u] and not sigma & team.nbit[v]]


def member_runs(team: Team, sigma: int, entry_val: dict, fail=frozenset()):
    """Enumerate internal runs of the slice. entry_val: entry edge -> (delivered, mask).
    Yields dict member -> (reached, flow, added, applied, content) plus switch choices.
    Contents here are concrete masks (entry masks are given)."""
    members = [n for n in team.order if sigma & team.nbit[n]]
    nodes = team.nodes
    state = {}
    switch = {}

    def rec(i):
        if i == len(members):
            yield dict(state), dict(switch)
            return
        n = members[i]
        node = nodes[n]
        req, gua, decl = team.mask[n]
        if n == INPUT:
            state[n] = (True, frozenset(), gua, True, 0)
            yield from rec(i + 1)
            return
        preds = team.pred[n]
        dlv = []
        for p in preds:
            if sigma & team.nbit[p]:
                r = state[p][0]
                if r and (nodes[p].route != 'switch' or switch.get(p) == n):
                    dlv.append(p)
            elif entry_val[(p, n)][0]:
                dlv.append(p)
        q = ALL if len(preds) <= 1 else node.join
        if q == ALL:
            opts = [tuple(preds)] if len(dlv) == len(preds) else []
        else:
            opts = list(combinations(dlv, q)) if len(dlv) >= q else []
        if not opts:
            state[n] = (False, frozenset(), 0, False, 0)
            yield from rec(i + 1)
            return
        pairs = {}
        for C in opts:
            flow, added = set(), 0
            for p in C:
                if sigma & team.nbit[p]:
                    _, f2, a2, _, _ = state[p]
                    flow |= f2
                    added |= a2
                else:
                    flow.add((p, n))
            pairs.setdefault((frozenset(flow), added), C)
        keep = [k for k in pairs if not any(o != k and o[0] <= k[0] and (o[1] & k[1]) == o[1] for o in pairs)]
        for flow, added in keep:
            content = added
            for e in flow:
                content |= entry_val[e][1]
            applies = (req & ~(content | decl)) == 0 and (node.kind == 'gate' or node.oracle not in fail)
            state[n] = (True, flow, added | gua if applies else added, applies, content)
            if node.route == 'switch' and len(team.succ[n]) > 1:
                for s in team.succ[n]:
                    switch[n] = s
                    yield from rec(i + 1)
                switch.pop(n, None)
            else:
                yield from rec(i + 1)

    yield from rec(0)


def derived_contract(team: Team, sigma: int, env: int, faults: bool = False) -> dict:
    """A_sigma (with empty environment) and G_sigma(env) (and the robust version)."""
    entries, exits = _entries(team, sigma), _exits(team, sigma)
    members = [n for n in team.order if sigma & team.nbit[n]]
    assume = set()
    for st, _ in member_runs(team, sigma, {e: (True, 0) for e in entries}):
        for n in members:
            r, _, _, _, c = st[n]
            if r and n != INPUT:
                req, _, decl = team.mask[n]
                assume |= {(n, p) for p in team.names(req & ~(c | decl))}

    def guarantee(fail, per_exit=None):
        g = None
        for st, sw in member_runs(team, sigma, {e: (True, env) for e in entries}, fail):
            for u, v in exits:
                r, flow, added, _, _ = st[u]
                if r and (team.nodes[u].route != 'switch' or sw.get(u) == v):
                    o = added | (env if flow else 0)
                    g = o if g is None else g & o
                    if per_exit is not None:
                        per_exit[(u, v)] = o if (u, v) not in per_exit else per_exit[(u, v)] & o
        return 0 if g is None else g
    per = {}
    G = guarantee(frozenset(), per)
    out = {'assume': assume, 'guarantee': G, 'per_exit': per}
    if faults and team.f > 0:
        orcs = sorted({team.nodes[n].oracle for n in members if team.nodes[n].kind == 'agent'})
        k = min(team.f, len(orcs))
        Gf = G
        for F in combinations(orcs, k):
            Gf &= guarantee(frozenset(F))
        out['robust'] = Gf
    return out


def naive_contract(team: Team, sigma: int, env: int) -> int:
    """What face-value composition of member contracts promises on every exit."""
    g = None
    for u, _ in _exits(team, sigma):
        o = env
        for m in team.nodes_of((team.anc[u] | team.nbit[u]) & sigma):
            o |= team.mask[m][1]
        g = o if g is None else g & o
    return 0 if g is None else g


def gap(team: Team, sigma: int, env: int) -> int:
    return naive_contract(team, sigma, env) & ~derived_contract(team, sigma, env)['guarantee']


def declared_valid(team: Team, sigma: int, assume: int, guarantee: int) -> bool:
    """Valid iff, with entries carrying `assume`, every member requirement holds in every
    internal run and every delivered exit carries `guarantee`."""
    entries = _entries(team, sigma)
    members = [n for n in team.order if sigma & team.nbit[n]]
    for st, _ in member_runs(team, sigma, {e: (True, assume) for e in entries}):
        for n in members:
            r, _, _, _, c = st[n]
            if r and n != INPUT:
                req, _, decl = team.mask[n]
                if req & ~(c | decl):
                    return False
    return (guarantee & ~derived_contract(team, sigma, assume)['guarantee']) == 0


# ------------------------------------------------------------------ T2(d): partition summaries
class PartSummary:
    """Boundary behaviour of one part, computed lazily from the part alone."""

    def __init__(self, team: Team, part: int):
        self.team, self.part = team, part
        self.entries, self.exits = _entries(team, part), _exits(team, part)
        self.members = [n for n in team.order if part & team.nbit[n]]
        rel = 0
        for n in self.members:
            rel |= team.mask[n][0]
        self.relevant = rel
        self.orcs = frozenset(team.nodes[n].oracle for n in self.members if team.nodes[n].kind == 'agent')
        self.cache = {}

    def outcomes(self, entry_val: dict, fail: frozenset):
        """entry_val: entry edge -> (delivered, mask). Only relevant bits are used as key."""
        team = self.team
        key = (tuple((entry_val[e][0], entry_val[e][1] & self.relevant) for e in self.entries), fail & self.orcs, not fail)
        if key in self.cache:
            return self.cache[key]
        val = {e: (d, m) for e, (d, m) in zip(self.entries, key[0])}
        res = set()
        for st, sw in member_runs(team, self.part, val, key[1]):
            exits = []
            for u, v in self.exits:
                r, flow, added, _, _ = st[u]
                d = r and (team.nodes[u].route != 'switch' or sw.get(u) == v)
                exits.append((d, flow if d else frozenset(), added if d else 0))
            keys = []
            for n in self.members:
                r, _, _, _, c = st[n]
                if not r or n == INPUT:
                    continue
                req, _, decl = team.mask[n]
                miss = req & ~(c | decl)
                if key[2]:
                    kind = 'goal' if n == OUTPUT else 'assume'
                    keys += [(kind, n, p) for p in team.names(miss)]
                elif n == OUTPUT:
                    keys += [('robust', n, p) for p in team.names(miss & team.crit_mask)]
            res.add((tuple(exits), frozenset(keys)))
        self.cache[key] = res
        return res


def quotient_symptoms(team: Team, parts: list[int]) -> dict:
    """Sym(T) computed from part summaries composed in quotient topological order."""
    owner = {n: i for i, p in enumerate(parts) for n in team.nodes_of(p)}
    succ = {i: set() for i in range(len(parts))}
    for u, v in team.edges:
        if owner[u] != owner[v]:
            succ[owner[u]].add(owner[v])
    indeg = {i: 0 for i in succ}
    for i in succ:
        for j in succ[i]:
            indeg[j] += 1
    order, ready = [], [i for i in succ if indeg[i] == 0]
    while ready:
        i = ready.pop()
        order.append(i)
        for j in succ[i]:
            indeg[j] -= 1
            if indeg[j] == 0:
                ready.append(j)
    if len(order) != len(parts):
        raise ValueError('quotient is cyclic')
    summ = [PartSummary(team, p) for p in parts]
    fault_sets = [frozenset()]
    if team.f and team.crit_mask and team.oracles:
        k = min(team.f, len(team.oracles))
        fault_sets += [frozenset(c) for c in combinations(team.oracles, k)]
    found = set()
    for fail in fault_sets:
        def rec(idx, edge_val, acc):
            if idx == len(order):
                found.update(acc)
                return
            s = summ[order[idx]]
            val = {e: edge_val.get(e, (False, 0)) for e in s.entries}
            for exits, keys in s.outcomes(val, fail):
                new = dict(edge_val)
                for (u, v), (d, flow, added) in zip(s.exits, exits):
                    m = added
                    for e in flow:
                        m |= val[e][1]
                    new[(u, v)] = (d, m if d else 0)
                rec(idx + 1, new, acc | keys)
        rec(0, {}, frozenset())
    goal = {k[2] for k in found if k[0] == 'goal'}
    return {k: None for k in found if not (k[0] == 'robust' and k[2] in goal)}
