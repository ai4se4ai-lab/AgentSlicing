"""Checkers: slice-level (any family), agent-level (B1), whole-team (B2), lint (B4);
localization (minimal manifesting slices) and mechanism diagnosis (classes S1-S6, A1-A4)."""
from __future__ import annotations

import time
from itertools import combinations

from . import semantics as sem
from . import slices as sl
from .model import ALL, INPUT, OUTPUT, Team


# ------------------------------------------------------------------ slice families
def run_family(team: Team, family: list[int], max_runs=200_000, time_budget=None) -> dict:
    """key -> list of (slice, witness) for every slice of the family that manifests it.
    Keys of F(empty) are recorded once with slice None (they manifest everywhere)."""
    static = sem.static_findings(team)
    manifest: dict = {k: [(None, w)] for k, w in static.items()}
    stats = {'slices': 0, 'runs': 0, 'limited': 0, 'timeout': False}
    t0 = time.perf_counter()
    for s in dict.fromkeys(family):
        if time_budget is not None and time.perf_counter() - t0 > time_budget:
            stats['timeout'] = True
            break
        stats['slices'] += 1
        try:
            found = sem.findings(team, s, max_runs, stats)
        except sem.RunLimit:
            stats['limited'] += 1
            continue
        for k, w in found.items():
            if k in static:
                continue
            manifest.setdefault(k, []).append((s, w))
    stats['seconds'] = time.perf_counter() - t0
    return {'manifest': manifest, 'stats': stats}


def _rank(team: Team, s: int):
    return (sl.size(s), sl.choice_points(team, s), sorted(team.index[n] for n in team.nodes_of(s)))


def localize(team: Team, manifest: dict) -> dict:
    """key -> {'minimal': [slices], 'top': slice, 'witness': w}. Static keys localize to their node."""
    out = {}
    for k, lst in manifest.items():
        if lst and lst[0][0] is None:
            out[k] = {'minimal': [team.nbit[k[1]]], 'top': team.nbit[k[1]], 'witness': lst[0][1], 'static': True}
            continue
        ss = [s for s, _ in lst]
        minimal = [s for s in set(ss) if not any(t != s and (t & s) == t for t in ss)]
        minimal.sort(key=lambda s: _rank(team, s))
        top = minimal[0]
        w = next(w for s, w in lst if s == top)
        out[k] = {'minimal': minimal, 'top': top, 'witness': w, 'static': False}
    return out


def check(team: Team, family: list[int], max_runs=200_000, time_budget=None) -> dict:
    res = run_family(team, family, max_runs, time_budget)
    loc = localize(team, res['manifest'])
    for k, v in loc.items():
        v['class'] = diagnose(team, k, v['top'] if not v['static'] else 0, v['witness'])
    return {'findings': loc, 'stats': res['stats']}


def agent_level(team: Team, **kw) -> dict:
    """B1: the singleton slicing (Def. 6)."""
    return check(team, sl.singleton(team), **kw)


def whole_team(team: Team, max_runs=2_000_000) -> dict:
    """B2: exact verdict, one witness per key; localization = hull of the witness lineage."""
    t0 = time.perf_counter()
    stats = {}
    sym = sem.symptoms(team, max_runs, stats)
    loc = {}
    full = (1 << len(team.order)) - 1
    for k, w in sym.items():
        h = lineage_hull(team, k, w) if w.get('choices') is not None and w.get('slice') else team.nbit[k[1]]
        loc[k] = {'minimal': [h], 'top': h, 'witness': w, 'static': not w.get('slice'),
                  'class': diagnose(team, k, full if w.get('slice') else 0, w)}
    return {'findings': loc, 'stats': {'seconds': time.perf_counter() - t0, 'runs': stats.get('runs', 0)}}


def lint(team: Team) -> dict:
    """B4: coverage by set difference (no ancestry, no paths, no routing); counts claimers
    of critical goals (gates count as robust)."""
    claimed = 0
    for n in team.order:
        claimed |= team.mask[n][1]
    found = {}
    for n in team.order:
        if n == INPUT:
            continue
        req, gua, decl = team.mask[n]
        miss = req & ~(claimed | decl)
        kind = 'goal' if n == OUTPUT else 'assume'
        for p in team.names(miss):
            found[(kind, n, p)] = {'top': team.nbit[n], 'class': 'lint'}
    for p in team.names(team.crit_mask):
        b = team.bit[p]
        gates = sum(1 for n in team.order if team.nodes[n].kind == 'gate' and team.mask[n][1] & b and n != INPUT)
        agents = sum(1 for n in team.order if team.nodes[n].kind == 'agent' and team.mask[n][1] & b)
        if gates == 0 and agents < team.f + 1 and ('goal', OUTPUT, p) not in found:
            found[('robust', OUTPUT, p)] = {'top': team.nbit[OUTPUT], 'class': 'lint'}
    return {'findings': found, 'stats': {}}


# ------------------------------------------------------------------ replay and diagnosis
def hybrid_run(team: Team, sigma: int, witness: dict):
    """Replay one run of H_sigma given a witness. Returns reached, content, out, applied."""
    fv_out, fv_content = sem.face_value(team)
    sw = {k: v for t, k, v in witness.get('choices', []) if t == 'switch'}
    co = {k: tuple(v) for t, k, v in witness.get('choices', []) if t == 'contrib'}
    fail = set(witness.get('faults', []))
    reached, content, out, applied = {}, {}, {}, {}
    region = sigma
    for n in team.nodes_of(sigma):
        region |= team.desc[n]
    for n in team.order:
        b = team.nbit[n]
        node = team.nodes[n]
        req, gua, decl = team.mask[n]
        if not region & b:
            reached[n], content[n], out[n], applied[n] = True, fv_content[n], fv_out[n], True
            continue
        preds = team.pred[n]
        if n == INPUT:
            reached[n], content[n], out[n], applied[n] = True, 0, gua, True
            continue
        if not sigma & b:      # outside, face value
            c, r = 0, False
            for p in preds:
                if reached[p] and (not sigma & team.nbit[p] or team.nodes[p].route != 'switch' or sw.get(p) == n):
                    r = True
                    c |= out[p]
            reached[n], content[n], applied[n] = r, c, r
            out[n] = c | gua if r else 0
            continue
        ext = [p for p in preds if not sigma & team.nbit[p]]
        env = 0
        for p in ext:
            env |= fv_out[p]
        delivered = list(ext) + [p for p in preds if sigma & team.nbit[p] and reached[p] and
                                 (team.nodes[p].route != 'switch' or sw.get(p) == n)]
        q = ALL if len(preds) <= 1 else node.join
        if q == ALL:
            ok, C = len(delivered) == len(preds), preds
        else:
            ok = len(delivered) >= q
            C = co.get(n, tuple(delivered))
        if not ok:
            reached[n], content[n], out[n], applied[n] = False, 0, 0, False
            continue
        c = 0
        has_ext = False
        for p in C:
            if p in ext:
                has_ext = True
            else:
                c |= out[p]
        if has_ext:
            c |= env
        a = (req & ~(c | decl)) == 0 and (node.kind == 'gate' or node.oracle not in fail)
        reached[n], content[n], applied[n] = True, c, a
        out[n] = c | gua if a else c
    return reached, content, out, applied


def lineage_hull(team: Team, key, witness) -> int:
    """Hull of the contributing lineage of the symptom node in an exact witness run."""
    full = (1 << len(team.order)) - 1
    reached, content, out, applied = hybrid_run(team, full, witness)
    co = {k: tuple(v) for t, k, v in witness.get('choices', []) if t == 'contrib'}
    sw = {k: v for t, k, v in witness.get('choices', []) if t == 'switch'}
    seen, stack = set(), [key[1]]
    while stack:
        n = stack.pop()
        if n in seen:
            continue
        seen.add(n)
        preds = team.pred[n]
        q = ALL if len(preds) <= 1 else team.nodes[n].join
        C = preds if q == ALL else co.get(n, preds)
        for p in C:
            if reached.get(p) and (team.nodes[p].route != 'switch' or sw.get(p) == n):
                stack.append(p)
    return sl.hull(team, team.nmask(seen))


def _base(p: str) -> str:
    return p.split('@')[0]


def diagnose(team: Team, key, sigma: int, witness: dict) -> str:
    """Mechanism class of a finding (Section 4)."""
    kind, x, p = key
    b = team.bit[p]
    if sigma == 0:
        if kind == 'goal' and not any(team.mask[n][1] & b for n in team.order):
            return 'A1'
        if any(team.mask[n][1] & b for n in team.order):
            return 'A3'                                  # provided, but not upstream
        if any(_base(q) == _base(p) and q != p and team.mask[u][1] & team.bit[q]
               for u in team.nodes_of(team.anc[x]) for q in team.props):
            return 'S1v'                                 # provided upstream in another view
        return 'A2'
    reached, content, out, applied = hybrid_run(team, sigma, witness)
    fail = set(witness.get('faults', []))
    claimers = [u for u in team.nodes_of(team.anc[x]) if team.mask[u][1] & b and u != INPUT]
    reasons = {}
    for u in claimers:
        inside = bool(sigma & team.nbit[u])
        if not reached[u]:
            reasons[u] = 'route'
        elif inside and not applied[u]:
            node = team.nodes[u]
            reasons[u] = 'fault' if node.kind == 'agent' and node.oracle in fail and \
                (team.mask[u][0] & ~(content[u] | team.mask[u][2])) == 0 else 'cond'
        else:
            reasons[u] = 'drop'
    vals = set(reasons.values())
    if kind == 'robust':
        faulted = [u for u, r in reasons.items() if r == 'fault']
        orcs = [team.nodes[u].oracle for u in faulted]
        if len(orcs) >= 2 and len(set(orcs)) < len(orcs):
            return 'S4'
        if 'cond' in vals:
            return 'S6a'
        if len(faulted) == 1 and 'drop' in vals:
            return 'S2'                                  # the join discards the redundant claimers
        if len(faulted) == 1 and len(claimers) == 1:
            return 'A4'
        return 'S4' if len(faulted) >= 2 else ('S6a' if faulted else 'A4')
    if 'route' in vals:
        return 'S5'
    if 'drop' in vals:
        return 'S5' if _merges_alternatives(team, sigma, x, reasons) else ('S2' if kind == 'goal' else 'S3')
    if 'cond' in vals:
        return 'S6b'
    return 'other'


def _merges_alternatives(team: Team, sigma: int, x: str, reasons) -> bool:
    """Is some member merge fed by exclusive alternatives, i.e. by different successors of one switch?"""
    def uses(w, a, m):
        out = {s for s in team.succ[w] if a == s or team.anc[a] & team.nbit[s]}
        if a == w:
            out.add(m)
        return out
    dropped = [u for u, r in reasons.items() if r == 'drop']
    for m in team.nodes_of(sigma):
        if not (m == x or team.anc[x] & team.nbit[m]) or not any(team.anc[m] & team.nbit[u] for u in dropped):
            continue
        srcs = team.pred[m]
        if len(srcs) < 2 or team.nodes[m].join == ALL:
            continue
        for w in team.order:
            if team.nodes[w].route != 'switch':
                continue
            for i, a in enumerate(srcs):
                for b in srcs[i + 1:]:
                    sa, sb = uses(w, a, m), uses(w, b, m)
                    if sa and sb and not (sa & sb):
                        return True
    return False


# ------------------------------------------------------------------ helpers for experiments
def detected(report: dict, keys) -> bool:
    return any(k in report['findings'] for k in keys)


def summary_keys(report: dict) -> set:
    return set(report['findings'])


def smells(team: Team) -> dict:
    """B5 (added baseline): pattern-based smell detector. Flags structures that *look*
    like the slice-level classes, without semantics: an any/quorum join or a switch between
    a claimer and a consumer, a critical goal whose claimers share an oracle, and a gate that
    claims a critical goal while requiring a property that only agents provide."""
    found = {}
    merges = [n for n in team.order if len(team.pred[n]) > 1 and team.nodes[n].join != ALL]
    routers = [n for n in team.order if team.nodes[n].route == 'switch']

    def between(u, v, cands):
        return any((team.anc[m] & team.nbit[u] or m == u) and (team.anc[v] & team.nbit[m] or m == v) for m in cands)
    for v in team.order:
        req = team.mask[v][0]
        for p in team.names(req):
            claim = [u for u in team.nodes_of(team.anc[v]) if team.mask[u][1] & team.bit[p]]
            if claim and all(between(u, v, merges + routers) for u in claim):
                kind = 'goal' if v == OUTPUT else 'assume'
                found[(kind, v, p)] = {'top': team.nbit[v], 'class': 'smell'}
    for p in team.names(team.crit_mask):
        b = team.bit[p]
        claim = [u for u in team.order if team.mask[u][1] & b and u != INPUT]
        orcs = [team.nodes[u].oracle for u in claim if team.nodes[u].kind == 'agent']
        gate_dep = any(team.nodes[u].kind == 'gate' and any(
            all(team.nodes[w].kind == 'agent' for w in team.nodes_of(team.anc[u]) if team.mask[w][1] & team.bit[q] and w != INPUT)
            and any(team.mask[w][1] & team.bit[q] for w in team.nodes_of(team.anc[u]))
            for q in team.names(team.mask[u][0])) for u in claim)
        if len(orcs) != len(set(orcs)) or gate_dep:
            found[('robust', OUTPUT, p)] = {'top': team.nbit[OUTPUT], 'class': 'smell'}
    return {'findings': found, 'stats': {}}


# ------------------------------------------------------------------ lifting and confirmed findings (T3b)
def lift(team: Team, sigma: int, key, witness: dict, max_runs: int = 200_000) -> dict:
    """Search a run of T that exhibits `key` and whose own member choices (restricted to
    `sigma`, with failures F & orc(sigma)), replayed in H_sigma, exhibit `key` as well.
    The witness fixes the member switch choices; contributor sets and outside choices are
    free; failures extend the witness's failed oracles to a maximal set (Lemma M).

    Returns {'lifted': bool, 'choices': lifted run or None, 'exhausted': bool}."""
    kind, x, prop = key
    b = team.bit[prop]
    fixed_sw = {k: v for t, k, v in witness.get('choices', []) if t == 'switch' and sigma & team.nbit[k]}
    wf = frozenset(witness.get('faults', []))
    orc_s = {team.nodes[n].oracle for n in team.nodes_of(sigma) if team.nodes[n].kind == 'agent'}
    if kind == 'robust':
        others = [o for o in team.oracles if o not in wf]
        extra = max(0, min(team.f, len(team.oracles)) - len(wf))
        attempts = [wf | frozenset(c) for c in combinations(others, min(extra, len(others)))]
    else:
        attempts = [frozenset()]
    budget = [max_runs]
    order = team.order
    for fail in attempts:
        reached, out = {}, {}
        sw, co = {}, {}
        found = [None]

        def missing(n, content):
            req, gua, decl = team.mask[n]
            if kind == 'assume':
                return n == x and bool(b & req & ~(content | decl))
            return n == OUTPUT and not content & b

        def verify(choices):
            mine = [c for c in choices if sigma & team.nbit[c[1]]]
            hr, hc, _, _ = hybrid_run(team, sigma, {'choices': mine, 'faults': sorted(fail & orc_s)})
            return hr.get(x, False) and missing(x, hc[x])

        def rec(i):
            if found[0] is not None:
                return
            budget[0] -= 1
            if budget[0] < 0:
                raise sem.RunLimit('lift budget')
            if i == len(order):
                return
            n = order[i]
            node = team.nodes[n]
            req, gua, decl = team.mask[n]
            if n == INPUT:
                reached[n], out[n] = True, gua
                rec(i + 1)
                return
            preds = team.pred[n]
            dlv = [p for p in preds if reached[p] and (team.nodes[p].route != 'switch' or sw.get(p) == n)]
            q = ALL if len(preds) <= 1 else node.join
            ok = len(dlv) == len(preds) if q == ALL else len(dlv) >= q
            if not ok:
                reached[n], out[n] = False, 0
                rec(i + 1)
                return
            if q == ALL:
                opts = [tuple(preds)]
            else:
                opts = [C for r in range(q, len(dlv) + 1) for C in combinations(dlv, r)]
            is_sw = node.route == 'switch' and len(team.succ[n]) > 1
            succs = [fixed_sw[n]] if is_sw and n in fixed_sw else (list(team.succ[n]) if is_sw else [None])
            for C in opts:
                c = 0
                for p in C:
                    c |= out[p]
                applies = (req & ~(c | decl)) == 0 and (node.kind == 'gate' or node.oracle not in fail)
                reached[n], out[n] = True, (c | gua if applies else c)
                if q != ALL:
                    co[n] = C
                if n == x and missing(n, c):
                    choices = [('switch', k, v) for k, v in sw.items()] + [('contrib', k, list(v)) for k, v in co.items()]
                    if verify(choices):
                        found[0] = {'choices': choices, 'faults': sorted(fail)}
                        return
                    continue
                for s in succs:
                    if s is not None:
                        sw[n] = s
                    rec(i + 1)
                    if found[0] is not None:
                        return
                sw.pop(n, None)
            co.pop(n, None)

        try:
            rec(0)
        except sem.RunLimit:
            return {'lifted': False, 'choices': None, 'exhausted': True}
        if found[0] is not None:
            return {'lifted': True, 'choices': found[0], 'exhausted': False}
    return {'lifted': False, 'choices': None, 'exhausted': False}


def confirmed_findings(team: Team, sigma: int, max_runs=200_000, lift_runs=200_000, include_static=True) -> dict:
    """Keys of F(sigma) with a witness that lifts to a run of T (Def. 'confirmed finding').
    key -> {'witness': hybrid witness, 'run': lifted run of T}."""
    allw: dict = {}
    raw = sem.findings(team, sigma, max_runs, all_witnesses=allw)
    static = sem.static_findings(team)
    out = {}
    for k, w in raw.items():
        if k in static:
            if not include_static:
                continue
            ws = [w]
            s = 0
        else:
            ws = allw.get(k) or [w]
            s = sigma
        for cand in ws:
            r = lift(team, s, k, cand, lift_runs)
            if r['lifted']:
                out[k] = {'witness': cand, 'run': r['choices']}
                break
    return out


def correct(sym: dict, key) -> bool:
    """A reported key is correct if it is a symptom of T; a robust key is also correct when T
    loses the same property without faults (Sym(T) then records the stronger goal key)."""
    return key in sym or (key[0] == 'robust' and ('goal', key[1], key[2]) in sym)


def manifests(team: Team, sigma: int, key, max_runs=200_000, lift_runs=200_000) -> bool:
    """Does sigma confirm `key` (some witness of key in H_sigma lifts to T)?"""
    allw: dict = {}
    raw = sem.findings(team, sigma, max_runs, all_witnesses=allw)
    if key not in raw:
        return False
    if key in sem.static_findings(team):
        return lift(team, 0, key, raw[key], lift_runs)['lifted']
    return any(lift(team, sigma, key, w, lift_runs)['lifted'] for w in allw.get(key) or [raw[key]])


def check_confirmed(team: Team, family: list[int], max_runs=200_000, lift_runs=200_000) -> dict:
    """Slice-level checking with confirmation: like `check`, but a slice manifests a key only
    if one of its witnesses lifts to a run of T. Static keys are confirmed once."""
    static = sem.static_findings(team)
    manifest: dict = {}
    stats = {'slices': 0, 'lifts': 0, 'unconfirmed': 0, 'limited': 0}
    t0 = time.perf_counter()
    for k, w in static.items():
        stats['lifts'] += 1
        if lift(team, 0, k, w, lift_runs)['lifted']:
            manifest[k] = [(None, w)]
        else:
            stats['unconfirmed'] += 1
    for s in dict.fromkeys(family):
        stats['slices'] += 1
        allw: dict = {}
        try:
            raw = sem.findings(team, s, max_runs, all_witnesses=allw)
        except sem.RunLimit:
            stats['limited'] += 1
            continue
        for k, w in raw.items():
            if k in static:
                continue
            ok = False
            for cand in allw.get(k) or [w]:
                stats['lifts'] += 1
                if lift(team, s, k, cand, lift_runs)['lifted']:
                    manifest.setdefault(k, []).append((s, cand))
                    ok = True
                    break
            if not ok:
                stats['unconfirmed'] += 1
    loc = localize(team, manifest)
    for k, v in loc.items():
        v['class'] = diagnose(team, k, 0 if v['static'] else v['top'], v['witness'])
    stats['seconds'] = time.perf_counter() - t0
    return {'findings': loc, 'stats': stats}


def must_analysis(team: Team) -> dict:
    """B6: classical must-analysis (meet over paths at any/quorum joins, union at all-joins),
    run once fault-free and once per maximal failure set. Path-insensitive and linear per
    failure set; sound for content (never above a run's content), hence may raise false alarms.
    Localizes to the symptom node."""
    def bound(fail):
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
                for i in range(len(team.props)):
                    bit = 1 << i
                    if sum(1 for x in preds if not lo_out[x] & bit) < q:
                        c |= bit
            lo_c[n] = c
            applies = (req & ~(c | decl)) == 0 and (node.kind == 'gate' or node.oracle not in fail)
            lo_out[n] = c | gua if applies else c
        return lo_c
    found = {}
    lo = bound(frozenset())
    for n in team.order:
        if n == INPUT:
            continue
        req, _, decl = team.mask[n]
        kind = 'goal' if n == OUTPUT else 'assume'
        for p in team.names(req & ~(lo[n] | decl)):
            found[(kind, n, p)] = {'top': team.nbit[n], 'class': 'must', 'static': True, 'minimal': [team.nbit[n]]}
    if team.f and team.crit_mask:
        k = min(team.f, len(team.oracles))
        for F in combinations(team.oracles, k):
            lf = bound(frozenset(F))
            for p in team.names(team.crit_mask & ~lf[OUTPUT]):
                if ('goal', OUTPUT, p) not in found:
                    found.setdefault(('robust', OUTPUT, p), {'top': team.nbit[OUTPUT], 'class': 'must', 'static': True,
                                                             'minimal': [team.nbit[OUTPUT]], 'faults': list(F)})
    return {'findings': found, 'stats': {}}


def deviation_hull(team: Team, key, witness: dict) -> int:
    """B2-dev: localization from a whole-team witness without slices: the hull of the
    ancestors-or-self of the symptom node that deviate in the witness (failed oracle, did not
    apply, quorum join using fewer than its delivered inputs, switch), plus the symptom node."""
    full = (1 << len(team.order)) - 1
    reached, content, out, applied = hybrid_run(team, full, witness)
    fail = set(witness.get('faults', []))
    co = {k: tuple(v) for t, k, v in witness.get('choices', []) if t == 'contrib'}
    sw = {k for t, k, v in witness.get('choices', []) if t == 'switch'}
    x = key[1]
    D = team.nbit[x]
    for u in team.nodes_of(team.anc[x]):
        if u == INPUT or not reached[u]:
            continue
        node = team.nodes[u]
        dlv = [p for p in team.pred[u] if reached[p] and (team.nodes[p].route != 'switch' or
                                                           any(t == 'switch' and k == p and v == u for t, k, v in witness.get('choices', [])))]
        if (node.kind == 'agent' and node.oracle in fail) or not applied[u] or u in sw or \
                (u in co and len(co[u]) < len(dlv)):
            D |= team.nbit[u]
    return sl.hull(team, D)


def shrink(team: Team, key, start: int | None = None, max_runs=200_000, lift_runs=200_000) -> tuple[int, int]:
    """Whole-team detection followed by greedy slice minimization (1-minimal under removal of
    one node that keeps the slice convex), using confirmed manifestation. Returns (slice, checks)."""
    s = start if start is not None else (1 << len(team.order)) - 1
    checks = 0
    changed = True
    while changed:
        changed = False
        for n in team.nodes_of(s):
            t = s & ~team.nbit[n]
            if not t or not sl.is_convex(team, t):
                continue
            checks += 1
            try:
                ok = manifests(team, t, key, max_runs, lift_runs)
            except sem.RunLimit:
                ok = False
            if ok:
                s, changed = t, True
                break
    return s, checks
