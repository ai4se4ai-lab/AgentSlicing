"""Incremental recertification (Theorem T8).

A slice's result is stored as its dynamic findings dF(sigma) = F(sigma) minus the keys of
F(empty), plus the region nodes that no run reaches. After a change, F(empty) is
recomputed (cheap) and only slices that intersect the dependency set are re-evaluated.
"""
from __future__ import annotations

import time

from . import semantics as sem
from . import slices as sl
from .model import OUTPUT, Team

ATTRIBUTE_ONLY = ('oracle', 'kind', 'route', 'join')


def slice_result(team: Team, s: int, max_runs=200_000) -> frozenset:
    static = sem.static_findings(team)
    return frozenset(k for k in sem.findings(team, s, max_runs) if k not in static)


def full(team: Team, family: list[int]) -> dict:
    return {s: slice_result(team, s) for s in family}


def dependency(old: Team, new: Team, change: dict) -> tuple[int, str]:
    """Node mask D such that slices disjoint from D keep their dynamic findings (T8).

    change: {'node': a, 'field': f} or {'edge': (u, v)}.
    Returns (mask, mode): mode 'members' means only slices containing a node of D are
    affected; mode 'ancestors' means slices intersecting anc*(D) are affected."""
    if 'edge' in change:
        u, v = change['edge']
        fv_old, _ = sem.face_value(old)
        fv_new, _ = sem.face_value(new)
        delta = fv_old.get(u, 0) | fv_new.get(u, 0)
        Y = new.nbit[u] | new.nbit[v]
        for t in (old, new):
            for y in t.order:
                if (t.desc[v] | t.nbit[v]) & t.nbit[y] and t.mask[y][0] & delta:
                    Y |= new.nbit[y]
        return Y, 'ancestors_both'
    a, field = change['node'], change['field']
    if field in ATTRIBUTE_ONLY:
        return new.nbit[a], 'members'
    if field in ('req', 'decl'):
        return new.nbit[a], 'ancestors'
    if field == 'gua':
        delta = old.mask[a][1] ^ new.mask[a][1]
        Y = new.nbit[a]
        for y in new.order:
            if (new.desc[a] & new.nbit[y]) and (new.mask[y][0] & delta):
                Y |= new.nbit[y]
        return Y, 'ancestors'
    raise ValueError(field)


def affected(team: Team, s: int, D: int, mode: str, old: Team | None = None) -> bool:
    if mode == 'members':
        return bool(s & D)
    closure = D
    for y in team.nodes_of(D):
        closure |= team.anc[y]
    if mode == 'ancestors_both' and old is not None:
        for y in old.nodes_of(D):
            closure |= old.anc[y]
    return bool(s & closure)


def recertify(old: Team, new: Team, change: dict, old_results: dict, new_family: list[int]) -> dict:
    """Re-evaluate only affected slices; others reuse their stored dynamic findings."""
    t0 = time.perf_counter()
    D, mode = dependency(old, new, change)
    res, redone = {}, 0
    for s in new_family:
        if s in old_results and sl.is_convex(old, s) and not affected(new, s, D, mode, old):
            res[s] = old_results[s]
        else:
            res[s] = slice_result(new, s)
            redone += 1
    return {'results': res, 'redone': redone, 'total': len(new_family), 'seconds': time.perf_counter() - t0}
