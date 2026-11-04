"""Convex slices (Def. 4), enumeration and slicing strategies (Section 3)."""
from __future__ import annotations

import random
from itertools import combinations

from .model import INPUT, OUTPUT, Team


def hull(team: Team, s: int) -> int:
    """Smallest convex superset: anc*(S) & desc*(S)."""
    a = d = 0
    for n in team.nodes_of(s):
        b = team.nbit[n]
        a |= team.anc[n] | b
        d |= team.desc[n] | b
    return a & d


def is_convex(team: Team, s: int) -> bool:
    return s != 0 and hull(team, s) == s


def size(s: int) -> int:
    return bin(s).count('1')


def choice_points(team: Team, s: int) -> int:
    c = 0
    for n in team.nodes_of(s):
        node = team.nodes[n]
        if node.route == 'switch' and len(team.succ[n]) > 1:
            c += 1
        if node.join != 'all' and len(team.pred[n]) > 1:
            c += 1
    return c


def components(team: Team) -> list[str]:
    """Nodes that slices range over: all nodes (IN and OUT included)."""
    return list(team.order)


def exhaustive(team: Team, k: int, within: int | None = None) -> list[int]:
    """All convex slices of size <= k (optionally inside a node mask). O(|N|^k) hull tests."""
    ids = [n for n in team.order if within is None or within & team.nbit[n]]
    out = []
    for r in range(1, k + 1):
        for comb in combinations(ids, r):
            s = team.nmask(comb)
            if hull(team, s) == s:
                out.append(s)
    return out


def all_convex(team: Team, limit: int = 1 << 16) -> list[int]:
    """Every convex slice (exponential); grows hulls from singletons, breadth first."""
    seen = set()
    frontier = [team.nbit[n] for n in team.order]
    seen.update(frontier)
    i = 0
    while i < len(frontier):
        s = frontier[i]
        i += 1
        for n in team.order:
            b = team.nbit[n]
            if s & b:
                continue
            h = hull(team, s | b)
            if h not in seen:
                seen.add(h)
                frontier.append(h)
                if len(seen) > limit:
                    raise OverflowError('too many convex slices')
    return frontier


# ---------------------------------------------------------------- strategies
def singleton(team: Team) -> list[int]:
    return [team.nbit[n] for n in team.order]


def whole(team: Team) -> list[int]:
    return [(1 << len(team.order)) - 1]


def window(team: Team, k: int) -> list[int]:
    """hull of v and its descendants within k-1 hops; on a chain, the intervals of length k."""
    out = set()
    for v in team.order:
        s = team.nbit[v]
        layer = [v]
        for _ in range(k - 1):
            nxt = []
            for x in layer:
                for y in team.succ[x]:
                    if not s & team.nbit[y]:
                        s |= team.nbit[y]
                        nxt.append(y)
            layer = nxt
        out.add(hull(team, s))
    return sorted(out)


def levels(team: Team) -> dict:
    lv = {}
    for n in team.order:
        lv[n] = 0 if not team.pred[n] else 1 + max(lv[p] for p in team.pred[n])
    return lv


def band(team: Team, w: int = 1) -> list[int]:
    """Cross-sections: hull of consecutive longest-path levels [i, i+w)."""
    lv = levels(team)
    top = max(lv.values())
    out = set()
    for i in range(top + 1):
        s = team.nmask(n for n in team.order if i <= lv[n] < i + w)
        if s:
            out.add(hull(team, s))
    return sorted(out)


def _dominators(team: Team, reverse: bool = False) -> dict:
    """(Post-)dominator sets as node masks; iterative, in (reverse) topological order."""
    order = list(reversed(team.order)) if reverse else list(team.order)
    preds = team.succ if reverse else team.pred
    full = (1 << len(team.order)) - 1
    dom = {}
    for n in order:
        ps = preds[n]
        if not ps:
            dom[n] = team.nbit[n]
        else:
            m = full
            for p in ps:
                m &= dom[p]
            dom[n] = m | team.nbit[n]
    return dom


def _immediate(team: Team, dom: dict, n: str, reverse: bool) -> str | None:
    """Closest (post-)dominator: highest (lowest) topological index among strict ones."""
    m = dom[n] & ~team.nbit[n]
    if not m:
        return None
    if reverse:
        return team.order[(m & -m).bit_length() - 1]
    return team.order[m.bit_length() - 1]


def region(team: Team) -> list[int]:
    """Single-entry single-exit regions: fork/switch -> immediate post-dominator,
    and immediate dominator -> join, each as a hull."""
    dom = _dominators(team)
    pdom = _dominators(team, reverse=True)
    out = set()
    for n in team.order:
        if len(team.succ[n]) > 1:
            p = _immediate(team, pdom, n, True)
            if p is not None:
                out.add(hull(team, team.nbit[n] | team.nbit[p]))
        if len(team.pred[n]) > 1:
            d = _immediate(team, dom, n, False)
            if d is not None:
                out.add(hull(team, team.nbit[n] | team.nbit[d]))
            # the join with its direct predecessors (the merge neighbourhood)
            out.add(hull(team, team.nbit[n] | team.nmask(team.pred[n])))
    return sorted(out)


def claimers(team: Team) -> dict:
    """property -> node mask of its claimers (IN excluded)."""
    c = team.__dict__.get('_claimers')
    if c is None:
        c = {}
        for n in team.order:
            if n == INPUT:
                continue
            for p in team.names(team.mask[n][1]):
                c[p] = c.get(p, 0) | team.nbit[n]
        team.__dict__['_claimers'] = c
    return c


def goal_directed(team: Team) -> list[int]:
    """Backward-slice analogue: for each requirement (v, p), the hull of v, the ancestors
    of v that claim p, and (one level up) the ancestors of those that claim their requirements."""
    C = claimers(team)
    out = set()
    for v in team.order:
        for p in team.names(team.mask[v][0]):
            claim = team.anc[v] & C.get(p, 0)
            s = team.nbit[v] | claim
            for u in team.nodes_of(claim):
                for q in team.names(team.mask[u][0]):
                    s |= team.anc[u] & C.get(q, 0)
            out.add(hull(team, s))
    return sorted(out)


def random_convex(team: Team, sizes: list[int], rng: random.Random) -> list[int]:
    """Random convex slices with matched sizes (baseline B3)."""
    out = []
    n = len(team.order)
    for k in sizes:
        best = None
        for _ in range(20):
            s = team.nbit[team.order[rng.randrange(n)]]
            while size(s) < k:
                cand = [x for x in team.order if not s & team.nbit[x] and
                        (team.anc[x] & s or team.desc[x] & s)]
                if not cand:
                    break
                s = hull(team, s | team.nbit[rng.choice(cand)])
            if best is None or abs(size(s) - k) < abs(size(best) - k):
                best = s
            if size(s) == k:
                break
        out.append(best)
    return out


STRATEGIES = {
    'singleton': lambda t: singleton(t),
    'whole': lambda t: whole(t),
    'window2': lambda t: window(t, 2), 'window3': lambda t: window(t, 3), 'window4': lambda t: window(t, 4),
    'band1': lambda t: band(t, 1), 'band2': lambda t: band(t, 2),
    'region': lambda t: region(t),
    'goal': lambda t: goal_directed(t),
}


def quotient_is_acyclic(team: Team, parts: list[int]) -> bool:
    """Contract each part to a node; is the resulting graph a DAG?"""
    owner = {}
    for i, p in enumerate(parts):
        for n in team.nodes_of(p):
            owner[n] = i
    adj = {i: set() for i in range(len(parts))}
    for u, v in team.edges:
        if owner[u] != owner[v]:
            adj[owner[u]].add(owner[v])
    state = {}

    def visit(i):
        state[i] = 1
        for j in adj[i]:
            if state.get(j) == 1 or (j not in state and not visit(j)):
                return False
        state[i] = 2
        return True
    return all(visit(i) for i in adj if i not in state)
