"""SMT proof obligations for the per-node steps of the slicing calculus.

Property sets are arrays from an uninterpreted sort `Prop` to Bool, so each obligation
quantifies over *all* finite or infinite property universes and all contracts. Each
obligation is valid iff its negation is UNSAT. Theorems over whole teams (Lemma A, W, M,
T4c, T5c, T5d) follow by induction over a topological order whose step cases are these
obligations; that induction is done on paper (Appendix A), not by the solver.
Obligations marked `expect='sat'` are countermodels (e.g. non-distributivity).

Run: python formal/prove.py [--mutant NAME] ; writes results/proofs.json
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

from z3 import (And, ArraySort, Bool, BoolSort, BoolVal, Const, Consts, DeclareSort, ForAll, If, Implies,
                Not, Or, Select, Solver, sat, unsat, get_version_string, BitVec, BitVecVal, ULE, ULT)

ROOT = Path(__file__).resolve().parents[1]
MUTANT = os.environ.get('SLICING_MUTANT')
Prop = DeclareSort('Prop')
Set = ArraySort(Prop, BoolSort())
x = Const('x', Prop)


def sub(a, b):
    return ForAll(x, Implies(Select(a, x), Select(b, x)))


def eq(a, b):
    return ForAll(x, Select(a, x) == Select(b, x))


def union_is(u, a, b):
    return ForAll(x, Select(u, x) == Or(Select(a, x), Select(b, x)))


def inter_is(u, a, b):
    return ForAll(x, Select(u, x) == And(Select(a, x), Select(b, x)))


def applies(req, c, decl, ok):
    """req subset of c U decl and the oracle is sound (ok)."""
    if MUTANT == 'applies-ignores-oracle':
        return ForAll(x, Implies(Select(req, x), Or(Select(c, x), Select(decl, x))))
    if MUTANT == 'applies-ignores-decl':
        return And(sub(req, c), ok)
    return And(ForAll(x, Implies(Select(req, x), Or(Select(c, x), Select(decl, x)))), ok)


def out_is(o, c, req, gua, decl, ok):
    """o = c U gua if the contract applies, else c (Definition 2)."""
    a = applies(req, c, decl, ok)
    if MUTANT == 'decl-inherited':
        return ForAll(x, Select(o, x) == Or(Select(c, x), Select(decl, x), And(a, Select(gua, x))))
    return ForAll(x, Select(o, x) == Or(Select(c, x), And(a, Select(gua, x))))


def fv_out_is(o, c, gua):
    """Face value: an outside node always applies (Definition 5)."""
    if MUTANT == 'face-value-conditional':
        return ForAll(x, Select(o, x) == Select(c, x))
    return ForAll(x, Select(o, x) == Or(Select(c, x), Select(gua, x)))


def missing_is(m, req, c, decl):
    return ForAll(x, Select(m, x) == And(Select(req, x), Not(Or(Select(c, x), Select(decl, x)))))


OBLIGATIONS = []


def ob(name, formula, expect='unsat', theorem=''):
    OBLIGATIONS.append((name, theorem, formula, expect))


req, gua, decl, c1, c2, o1, o2, m1, m2, E1, E2 = Consts('req gua decl c1 c2 o1 o2 m1 m2 E1 E2', Set)
ok1, ok2 = Bool('ok1'), Bool('ok2')

# L1: transfer is monotone in content and antitone in failures (Lemma M, Lemma A)
ob('L1-transfer-monotone', Implies(And(sub(c1, c2), Implies(ok1, ok2), out_is(o1, c1, req, gua, decl, ok1),
                                       out_is(o2, c2, req, gua, decl, ok2)), sub(o1, o2)), theorem='Lemma A, M')
# L2: face value dominates the exact transfer (Lemma A step)
ob('L2-face-value-dominates', Implies(And(sub(c1, c2), out_is(o1, c1, req, gua, decl, ok1), fv_out_is(o2, c2, gua)),
                                      sub(o1, o2)), theorem='Lemma A')
# L3: join step: contents of a contributor subset are below the union of all delivered outputs
a1, a2, a3, b1, b2, b3, u, w = Consts('a1 a2 a3 b1 b2 b3 u w', Set)
s1, s2, s3 = Bool('s1'), Bool('s2'), Bool('s3')


def chosen_union(r, xs, sel):
    return ForAll(x, Select(r, x) == Or(*[And(s, Select(z, x)) for z, s in zip(xs, sel)]))


join_ok = (lambda: chosen_union(w, [b1, b2, b3], [BoolVal(True)] * 3)) if MUTANT != 'join-intersection' else \
    (lambda: ForAll(x, Select(w, x) == And(Select(b1, x), Select(b2, x), Select(b3, x))))
ob('L3-join-subset', Implies(And(sub(a1, b1), sub(a2, b2), sub(a3, b3), chosen_union(u, [a1, a2, a3], [s1, s2, s3]),
                                 join_ok()), sub(u, w)), theorem='Lemma A, M')
# L4: missing requirements are antitone in content (symptom persistence: T4c, T5d)
ob('L4-missing-antitone', Implies(And(sub(c1, c2), missing_is(m1, req, c1, decl), missing_is(m2, req, c2, decl)),
                                  sub(m2, m1)), theorem='T4c, T5d, Lemma M')
# L5: Lemma W: larger evidence gives larger output; the realized minimum is the worst case
ob('L5-evidence-monotone', Implies(And(sub(E1, E2), Implies(ok1, ok2),
                                       ForAll(x, Select(o1, x) == Or(Select(c1, x), And(sub(req, E1), ok1, Select(gua, x)))),
                                       ForAll(x, Select(o2, x) == Or(Select(c1, x), And(sub(req, E2), ok2, Select(gua, x))))),
                                   sub(o1, o2)), theorem='Lemma W')
# L7: entry edges of a member carry the same environment, so any nonempty choice among them gives env
env = Const('env', Set)
ob('L7-env-uniform', Implies(And(Or(s1, s2), chosen_union(u, [env, env], [s1, s2])), eq(u, env)), theorem='T1')
# L8: the must-analysis transfer is sound: a lower bound stays below the exact output
L, Lo = Consts('L Lo', Set)
ob('L8-must-sound', Implies(And(sub(L, c1), out_is(Lo, L, req, gua, decl, BoolVal(True)),
                                out_is(o1, c1, req, gua, decl, BoolVal(True))), sub(Lo, o1)), theorem='Generator')
# L9: an any-join lower bound (intersection) is below every single contributor
ob('L9-meet-below-choice', Implies(inter_is(u, a1, a2), And(sub(u, a1), sub(u, a2))), theorem='Generator')
# L10: robust implies fault-free: content under failures is below the fault-free content (same choices)
ob('L10-fault-antitone', Implies(And(out_is(o1, c1, req, gua, decl, BoolVal(False)), out_is(o2, c1, req, gua, decl, BoolVal(True))),
                                 sub(o1, o2)), theorem='Def. 3')

# L11: a failed agent provides nothing (its output is its content)
ob('L11-failed-provides-nothing', Implies(out_is(o1, c1, req, gua, decl, BoolVal(False)), eq(o1, c1)), theorem='Def. 2')
# L12: declared evidence counts for applicability
ob('L12-decl-enables', Implies(And(sub(req, decl), out_is(o1, c1, req, gua, decl, BoolVal(True))), sub(gua, o1)), theorem='Def. 2')
# L13: declared evidence is local: it never flows to the output
ob('L13-decl-local', Implies(out_is(o1, c1, req, gua, decl, ok1),
                             ForAll(x, Implies(Select(o1, x), Or(Select(c1, x), Select(gua, x))))), theorem='Def. 2')

# C1: the conditional transfer does not distribute over intersection (must-analysis is incomplete)
A_, B_, AB, oA, oB, oAB = Consts('A_ B_ AB oA oB oAB', Set)
ob('C1-non-distributive', And(inter_is(AB, A_, B_), out_is(oA, A_, req, gua, decl, BoolVal(True)),
                              out_is(oB, B_, req, gua, decl, BoolVal(True)), out_is(oAB, AB, req, gua, decl, BoolVal(True)),
                              Not(ForAll(x, Select(oAB, x) == And(Select(oA, x), Select(oB, x))))),
   expect='sat', theorem='B6 incompleteness')

# C2 (T2c): an exit whose guarantee g appears iff r1 or r2 enters (two members r1->g, r2->g
# feeding one exit node) has no exact single pair (A, G): exactness on the three environments
# {}, {r1}, {r2} is already contradictory. Holds for any distinct r1, r2, g in any universe.
from z3 import Distinct, K, Store
r1, r2, gq = Consts('r1 r2 gq', Prop)
Ac, Gc = Consts('Ac Gc', Set)
X0 = K(Prop, BoolVal(False))
envs = [X0, Store(X0, r1, BoolVal(True)), Store(X0, r2, BoolVal(True))]


def derived_exit(X):
    if MUTANT == 'single-pair-ok':                      # a non-disjunctive exit: g iff r1 enters
        return lambda y: Or(Select(X, y), And(y == gq, Select(X, r1)))
    return lambda y: Or(Select(X, y), And(y == gq, Or(Select(X, r1), Select(X, r2))))


exact = And(*[ForAll(x, derived_exit(X)(x) == Or(Select(X, x), And(sub(Ac, X), Select(Gc, x)))) for X in envs])
ob('C2-no-exact-single-pair', Not(And(Distinct(r1, r2, gq), exact)), theorem='T2(c)')


def check_one(formula, expect, timeout_ms=60_000):
    s = Solver()
    s.set('timeout', timeout_ms)
    s.add(Not(formula) if expect == 'unsat' else formula)
    t0 = time.perf_counter()
    r = s.check()
    return str(r), time.perf_counter() - t0


def main():
    rows = []
    for name, theorem, f, expect in OBLIGATIONS:
        res, secs = check_one(f, expect)
        good = (res == 'unsat') if expect == 'unsat' else (res == 'sat')
        rows.append({'obligation': name, 'theorem': theorem, 'expect': expect, 'z3': res, 'ok': good, 'seconds': round(secs, 4)})
    payload = {'solver': 'z3 ' + get_version_string(), 'mutant': MUTANT, 'obligations': rows}
    if MUTANT is None:
        (ROOT / 'results').mkdir(exist_ok=True)
        (ROOT / 'results/proofs.json').write_text(json.dumps(payload, indent=1) + '\n', encoding='utf-8')
    print(json.dumps({'failed': [r['obligation'] for r in rows if not r['ok']]}))
    return rows


if __name__ == '__main__':
    main()
