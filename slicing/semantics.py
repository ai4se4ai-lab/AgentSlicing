"""Exact run semantics (Def. 2-3) and the hybrid slice semantics H_sigma (Def. 5).

`findings(team, sigma)` returns the symptom keys of H_sigma with one witness run each.
With sigma = all nodes it is the exact semantics, Sym(T); with sigma = 0 it is the
face-value world H_empty.

Keys: ('assume', node, prop), ('goal', 'OUT', prop), ('robust', 'OUT', prop).
Runs enumerate only minimal contributor sets and maximal failure sets (Lemma M):
every other run has a superset of content at every node and so no extra symptom.
"""
from __future__ import annotations

import heapq
import sys
import time
from functools import lru_cache
from itertools import combinations

from .model import ALL, INPUT, OUTPUT, Team


sys.setrecursionlimit(max(sys.getrecursionlimit(), 20000))


class RunLimit(Exception):
    """Raised when a slice has more internal runs than the caller allows."""


def face_value(team: Team):
    """Static face-value outputs and contents (H_empty): cone semantics."""
    cache = team.__dict__.get('_fv')
    if cache is not None:
        return cache
    out, content = {}, {}
    for n in team.order:
        c = 0
        for p in team.pred[n]:
            c |= out[p]
        req, gua, decl = team.mask[n]
        content[n] = c
        out[n] = c | gua
    team.__dict__['_fv'] = (out, content)
    return out, content


def _keys_at(team: Team, n: str, content: int, kinds=('assume', 'goal')):
    req, gua, decl = team.mask[n]
    missing = req & ~(content | decl)
    if not missing or n == INPUT:
        return []
    kind = 'goal' if n == OUTPUT else 'assume'
    return [(kind, n, p) for p in team.names(missing)]


def static_findings(team: Team) -> dict:
    """F(empty): requirements and goals not claimed upstream (no witness needed)."""
    cache = team.__dict__.get('_static')
    if cache is not None:
        return cache
    _, content = face_value(team)
    res = {}
    for n in team.order:
        for k in _keys_at(team, n, content[n]):
            res[k] = {'slice': [], 'faults': [], 'choices': []}
    team.__dict__['_static'] = res
    return res


def _fault_sets(team: Team, members: list[str]):
    """Fault-free run plus all maximal failure sets over member oracles (if relevant)."""
    sets = [frozenset()]
    if team.f > 0 and team.crit_mask:
        orcs = sorted({team.nodes[n].oracle for n in members if team.nodes[n].kind == 'agent'})
        size = min(team.f, len(orcs))
        if size:
            sets += [frozenset(c) for c in combinations(orcs, size)]
    return sets


def _minimal(masks):
    """Inclusion-minimal distinct masks (larger contents can only hide symptoms)."""
    masks = sorted(set(masks), key=lambda m: bin(m).count('1'))
    keep = []
    for m in masks:
        if not any((k & m) == k for k in keep):
            keep.append(m)
    return keep


def findings(team: Team, sigma: int, max_runs: int | None = 200_000, stats: dict | None = None, deadline: float | None = None,
             all_witnesses: dict | None = None, cap: int = 64, robust_always: bool = False) -> dict:
    """Symptom keys of H_sigma -> one witness. `sigma` is a node bitmask (Team.nbit).

    With `all_witnesses` (a dict), every distinct witness of each dynamic key is also
    collected there (at most `cap` per key); confirmation by lifting needs them.
    With `robust_always`, a robust key is reported whenever some run with failures misses a
    critical goal, even if the slice also shows the goal key (used for confirmed findings)."""
    static = static_findings(team)
    if sigma == 0:
        return dict(static)
    fv_out, fv_content = face_value(team)
    nbit = team.nbit
    members = team.nodes_of(sigma)
    region_mask = sigma
    for n in members:
        region_mask |= team.desc[n]
    nodes = team.nodes
    result: dict = {}
    # static keys at nodes outside the region hold in every run
    for k, w in static.items():
        if not region_mask & nbit[k[1]]:
            result[k] = w
    always_unreached = [None]       # nodes unreached in every run so far (None = no run yet)

    def record(target, k, witness):
        if all_witnesses is None:
            target.setdefault(k, witness())
            return
        w = witness()
        target.setdefault(k, w)
        lst = all_witnesses.setdefault(k, [])
        if len(lst) < cap and w not in lst:
            lst.append(w)
    runs = 0
    robust_candidates: dict = {}

    def phase_b(state_out, state_reached, choice_switch, fault_free, witness):
        """Propagate member results to outside descendants (face value)."""
        changed_out, changed_reached = {}, {}
        heap = []
        pushed = set()
        for n in members:
            for s in team.succ[n]:
                if not sigma & nbit[s] and s not in pushed:
                    pushed.add(s)
                    heapq.heappush(heap, (team.index[s], s))
        found = []
        while heap:
            _, n = heapq.heappop(heap)
            content, reached = 0, False
            for p in team.pred[n]:
                if sigma & nbit[p]:
                    if state_reached[p] and (nodes[p].route != 'switch' or choice_switch.get(p) == n):
                        reached = True
                        content |= state_out[p]
                elif p in changed_out:
                    if changed_reached[p]:
                        reached = True
                        content |= changed_out[p]
                else:
                    reached = True
                    content |= fv_out[p]
            out = content | team.mask[n][1] if reached else 0
            if reached and content == fv_content[n]:
                continue            # unchanged: static keys at n apply, nothing propagates
            changed_out[n], changed_reached[n] = out, reached
            for s in team.succ[n]:
                if s not in pushed:
                    pushed.add(s)
                    heapq.heappush(heap, (team.index[s], s))
            if reached:
                found.append((n, content))
        if robust_always and not fault_free and not sigma & nbit[OUTPUT] and OUTPUT not in changed_out:
            # the output keeps its face-value content in this run: a critical goal missing there is lost
            for p in team.names(team.crit_mask & ~fv_content[OUTPUT]):
                record(robust_candidates, ('robust', OUTPUT, p), witness)
        unreached = {n for n, r in changed_reached.items() if not r}
        always_unreached[0] = unreached if always_unreached[0] is None else always_unreached[0] & unreached
        for n, content in found:
            if fault_free:
                for k in _keys_at(team, n, content):
                    record(result, k, witness)
            elif n == OUTPUT:
                miss = team.crit_mask & ~content
                for p in team.names(miss):
                    record(robust_candidates, ('robust', OUTPUT, p), witness)

    for fail in _fault_sets(team, members):
        fault_free = not fail
        state_out, state_reached = {}, {}
        choice_switch, choice_contrib = {}, {}

        def witness():
            return {'slice': members, 'faults': sorted(fail),
                    'choices': [('switch', k, v) for k, v in choice_switch.items()] +
                               [('contrib', k, list(v)) for k, v in choice_contrib.items()]}

        def leaf():
            nonlocal runs
            runs += 1
            if max_runs is not None and runs > max_runs:
                raise RunLimit(f'more than {max_runs} runs')
            if deadline is not None and runs % 64 == 0 and time.perf_counter() > deadline:
                raise RunLimit('deadline')
            phase_b(state_out, state_reached, choice_switch, fault_free, witness)

        def settle(n, node, content, req, gua, decl):
            applies = (req & ~(content | decl)) == 0 and (node.kind == 'gate' or node.oracle not in fail)
            state_reached[n] = True
            state_out[n] = content | gua if applies else content
            if fault_free:
                for k in _keys_at(team, n, content):
                    record(result, k, witness)
            elif n == OUTPUT:
                for p in team.names(team.crit_mask & ~content):
                    record(robust_candidates, ('robust', OUTPUT, p), witness)

        def dfs(i):
            """Deterministic members are processed in a loop; recursion happens only at choices."""
            while i < len(members):
                n = members[i]
                node = nodes[n]
                req, gua, decl = team.mask[n]
                preds = team.pred[n]
                if n == INPUT:
                    state_reached[n], state_out[n] = True, gua
                    i += 1
                    continue
                ext = [p for p in preds if not sigma & nbit[p]]
                env = 0
                for p in ext:
                    env |= fv_out[p]
                delivered = list(ext)
                for p in preds:
                    if sigma & nbit[p] and state_reached[p] and (nodes[p].route != 'switch' or choice_switch.get(p) == n):
                        delivered.append(p)
                q = node.join
                if len(preds) <= 1:
                    q = ALL
                if q == ALL:
                    reached = len(delivered) == len(preds)
                    options = [(tuple(preds), _content(delivered, ext, env))] if reached else []
                else:
                    reached = len(delivered) >= q
                    options = []
                    if reached:
                        by_mask = {}
                        for c in combinations(delivered, q):
                            m = _content(c, ext, env)
                            by_mask.setdefault(m, c)
                        options = [(by_mask[m], m) for m in _minimal(by_mask)]
                if not reached:
                    state_reached[n], state_out[n] = False, 0
                    i += 1
                    continue
                is_switch = node.route == 'switch' and len(team.succ[n]) > 1
                if len(options) == 1 and not is_switch:
                    if q != ALL:
                        choice_contrib[n] = options[0][0]
                    settle(n, node, options[0][1], req, gua, decl)
                    i += 1
                    continue
                for contrib, content in options:
                    if q != ALL:
                        choice_contrib[n] = contrib
                    settle(n, node, content, req, gua, decl)
                    if is_switch:
                        for s in team.succ[n]:
                            choice_switch[n] = s
                            dfs(i + 1)
                        choice_switch.pop(n, None)
                    else:
                        dfs(i + 1)
                choice_contrib.pop(n, None)
                return
            leaf()

        def _content(c, ext_list, env):
            m = 0
            has_ext = False
            for p in c:
                if p in ext_list:
                    has_ext = True
                else:
                    m |= state_out[p]
            return m | env if has_ext else m

        dfs(0)

    for k, w in static.items():
        if region_mask & nbit[k[1]] and not sigma & nbit[k[1]] and always_unreached[0] is not None and k[1] not in always_unreached[0]:
            result.setdefault(k, w)
    for k, w in robust_candidates.items():
        if robust_always or ('goal', OUTPUT, k[2]) not in result:
            result.setdefault(k, w)
    if stats is not None:
        stats['runs'] = stats.get('runs', 0) + runs
    return result


def symptoms(team: Team, max_runs: int | None = 2_000_000, stats=None, deadline=None) -> dict:
    """Sym(T): the exact semantics."""
    return findings(team, (1 << len(team.order)) - 1, max_runs, stats, deadline)


def is_safe(sym: dict) -> bool:
    return not any(k[0] in ('goal', 'robust') for k in sym)


def evaluate_run(team: Team, choices: dict, contrib: dict, fail=frozenset()):
    """One exact run (Def. 2). choices: switch -> successor; contrib: node -> tuple of preds.

    Returns (reached, content, out) dicts. Used by the brute-force oracle and tests.
    """
    reached, content, out = {}, {}, {}
    for n in team.order:
        node = team.nodes[n]
        req, gua, decl = team.mask[n]
        if n == INPUT:
            reached[n], content[n], out[n] = True, 0, gua
            continue
        preds = team.pred[n]
        delivered = [p for p in preds if reached[p] and (team.nodes[p].route != 'switch' or choices.get(p) == n)]
        q = ALL if len(preds) <= 1 else node.join
        if q == ALL:
            ok = len(delivered) == len(preds)
            C = preds
        else:
            ok = len(delivered) >= q
            C = contrib.get(n, tuple(delivered))
            if ok and not (set(C) <= set(delivered) and len(C) >= q):
                raise ValueError(f'inadmissible contributors at {n}')
        if not ok:
            reached[n], content[n], out[n] = False, 0, 0
            continue
        c = 0
        for p in C:
            c |= out[p]
        applies = (req & ~(c | decl)) == 0 and (node.kind == 'gate' or node.oracle not in fail)
        reached[n], content[n], out[n] = True, c, (c | gua if applies else c)
    return reached, content, out


def lower_bound(team: Team, gates_only: bool = False) -> dict:
    """Must-analysis: a lower bound on content over all fault-free runs reaching each node.

    Sound (never above the content of a run) but not exact (forks correlate contributions,
    and the conditional transfer is not distributive). With gates_only, agent guarantees
    are ignored, giving a bound that survives any oracle failures.
    """
    lo_out, lo_c = {}, {}
    for n in team.order:
        node = team.nodes[n]
        req, gua, decl = team.mask[n]
        preds = team.pred[n]
        if n == INPUT:
            lo_c[n], lo_out[n] = 0, gua
            continue
        q = ALL if len(preds) <= 1 else node.join
        if q == ALL:
            c = 0
            for p in preds:
                c |= lo_out[p]
        else:
            c = 0
            for i, p in enumerate(team.props):
                b = 1 << i
                lacking = sum(1 for x in preds if not lo_out[x] & b)
                if lacking < q:
                    c |= b
        lo_c[n] = c
        applies = (req & ~(c | decl)) == 0 and not (gates_only and node.kind == 'agent')
        lo_out[n] = c | gua if applies else c
    return lo_c


def live_nodes(team: Team, max_runs=200_000) -> set:
    """Nodes reached in some fault-free run (exact; exponential in choice points)."""
    live = set()
    switches = [n for n in team.order if team.nodes[n].route == 'switch' and len(team.succ[n]) > 1]

    def rec(i, choice):
        if i == len(switches):
            r, _, _ = evaluate_run(team, choice, {})
            live.update(n for n, v in r.items() if v)
            return
        for s in team.succ[switches[i]]:
            choice[switches[i]] = s
            rec(i + 1, choice)
    rec(0, {})
    return live
