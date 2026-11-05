import random

import pytest
from hypothesis import given, settings, strategies as st, HealthCheck

from slicing import analysis as an, conformance as cf, contracts as ct, generator as gen, injector as inj
from slicing import oracle, semantics as sem, slices as sl
from slicing.model import ALL, Team, build


def chain_example():
    return build([('RA', 'agent', [], ['req_spec'], 'g'), ('AR', 'agent', ['req_spec'], ['design'], 'g'),
                  ('DV', 'agent', ['design'], ['code', 'tests'], 'g'), ('SR', 'agent', ['code'], ['sec_reviewed'], 'g'),
                  ('TS', 'gate', ['tests'], ['tests_pass'])],
                 [('IN', 'RA'), ('RA', 'AR'), ('AR', 'DV'), ('DV', 'SR'), ('SR', 'TS'), ('TS', 'OUT')],
                 goals=['tests_pass', 'sec_reviewed'], critical=['tests_pass'], f=1)


def forkjoin_example(policy='any'):
    return build([('RA', 'agent', [], ['spec']), ('AR', 'agent', ['spec'], ['design']), ('DV', 'agent', ['design'], ['code']),
                  ('CR', 'agent', ['code'], ['reviewed']), ('ST', 'agent', ['code'], ['sec_tested']),
                  ('RG', 'gate', [], [], None, 'fork', policy)],
                 [('IN', 'RA'), ('RA', 'AR'), ('AR', 'DV'), ('DV', 'CR'), ('DV', 'ST'), ('CR', 'RG'), ('ST', 'RG'), ('RG', 'OUT')],
                 goals=['reviewed', 'sec_tested'])


def test_chain_running_example():
    t = chain_example()
    assert set(sem.symptoms(t)) == {('robust', 'OUT', 'tests_pass')}
    assert an.agent_level(t)['findings'] == {}
    rep = an.check(t, sl.exhaustive(t, 4))
    f = rep['findings'][('robust', 'OUT', 'tests_pass')]
    assert [t.nodes_of(s) for s in f['minimal']] == [['DV', 'SR', 'TS']]
    assert f['class'] == 'S6a'


def test_forkjoin_running_example():
    t = forkjoin_example()
    assert set(sem.symptoms(t)) == {('goal', 'OUT', 'reviewed'), ('goal', 'OUT', 'sec_tested')}
    assert an.agent_level(t)['findings'] == {}
    rep = an.check_confirmed(t, sl.exhaustive(t, 3))
    for k in sem.symptoms(t):
        assert sorted(sorted(t.nodes_of(s)) for s in rep['findings'][k]['minimal']) == [['CR', 'RG'], ['RG', 'ST']]
        assert rep['findings'][k]['class'] == 'S2'
    assert sem.symptoms(forkjoin_example('all')) == {}


def test_convexity_and_quotient():
    t = build([('a', 'agent', [], []), ('b', 'agent', [], []), ('c', 'agent', [], []), ('d', 'agent', [], [])],
              [('IN', 'a'), ('a', 'b'), ('IN', 'c'), ('c', 'd'), ('a', 'd'), ('c', 'b'), ('b', 'OUT'), ('d', 'OUT')])
    ad, bc = t.nmask(['a', 'd']), t.nmask(['b', 'c'])
    assert sl.is_convex(t, ad) and sl.is_convex(t, bc)
    rest = t.nmask(['IN', 'OUT'])
    assert not sl.quotient_is_acyclic(t, [ad, bc, t.nbit['IN'], t.nbit['OUT']])
    chain = build([('a', 'agent', [], []), ('b', 'agent', [], []), ('c', 'agent', [], [])],
                  [('IN', 'a'), ('a', 'b'), ('b', 'c'), ('c', 'OUT')])
    assert not sl.is_convex(chain, chain.nmask(['a', 'c']))
    assert sl.hull(chain, chain.nmask(['a', 'c'])) == chain.nmask(['a', 'b', 'c'])


def test_single_successor_switch_is_fork():
    t = build([('a', 'agent', [], ['p'], None, 'switch')], [('IN', 'a'), ('a', 'OUT')], goals=['p'])
    assert t.nodes['a'].route == 'fork'
    assert sem.symptoms(t) == {}


def test_declared_evidence_is_local():
    t = build([('a', 'agent', ['x'], ['y'], None, 'fork', 'all', ['x']), ('b', 'agent', ['x'], [])],
              [('IN', 'a'), ('a', 'b'), ('b', 'OUT')], goals=['y'])
    assert set(sem.symptoms(t)) == {('assume', 'b', 'x')}


def test_derived_contract_is_conditional():
    t = build([('m1', 'agent', ['r1'], ['g1']), ('m2', 'agent', ['r2'], ['g2'])],
              [('IN', 'm1'), ('IN', 'm2'), ('m1', 'OUT'), ('m2', 'OUT')])
    s = t.nmask(['m1', 'm2'])
    g_r1 = ct.derived_contract(t, s, t.m(['r1']))['guarantee']
    assert g_r1 & t.bit['g1'] == 0          # m2's exit lacks g1: guarantee is per exit, intersected
    assert ct.declared_valid(t, s, t.m(['r1', 'r2']), 0)


def test_lint_misses_ordering_but_al_finds_it():
    t = build([('a', 'agent', ['late'], []), ('b', 'agent', [], ['late'])], [('IN', 'a'), ('a', 'b'), ('b', 'OUT')])
    assert an.lint(t)['findings'] == {}
    assert ('assume', 'a', 'late') in an.agent_level(t)['findings']


@pytest.mark.parametrize('topo', gen.TOPOLOGIES)
def test_generated_teams_are_clean(topo):
    for seed in range(8):
        t = gen.generate(topo, 5 + seed, seed)
        assert not t.validate()
        assert sem.symptoms(t) == {}


@pytest.mark.parametrize('cls', inj.CLASSES + inj.DECOYS + ('clean',))
def test_injection_ground_truth(cls):
    for seed in range(6):
        t, gt = inj.inject(gen.generate(gen.TOPOLOGIES[seed % 7], 6, seed), cls, seed)
        sym = sem.symptoms(t)
        assert set(gt['keys']) <= set(sym)
        if gt['decoy']:
            assert sym == {}


def test_hidden_classes_are_silent_at_agent_level():
    for cls in ('S2', 'S3', 'S4', 'S6a'):
        for seed in range(5):
            t, gt = inj.inject(gen.generate('chain', 5, seed), cls, seed)
            al = an.agent_level(t)['findings']
            assert not set(gt['keys']) & set(al), (cls, seed)
    t, gt = inj.inject(gen.generate('chain', 5, 1), 'S6b', 1)
    al = an.agent_level(t)['findings']
    assert ('assume',) + gt['keys'][1][1:] in al and gt['primary'] not in al


@settings(max_examples=150, deadline=None, derandomize=True, suppress_health_check=list(HealthCheck))
@given(st.integers(0, 10_000))
def test_conformance_property(seed):
    t = cf.wild_team(seed, n=3 + seed % 3)
    r = cf.check_team(t, kmax=2)
    assert all(v == 0 for v in r.values()), r


@settings(max_examples=60, deadline=None, derandomize=True, suppress_health_check=list(HealthCheck))
@given(st.integers(0, 10_000))
def test_model_oracle_property(seed):
    t = cf.wild_team(seed, n=3 + seed % 2)
    assert oracle.model_symptoms(t, 3_000_000) == set(sem.symptoms(t))


def test_false_alarm_and_nonmonotonicity():
    """T3(c), T5(e): an outside all-join at face value admits a run the team does not have."""
    t = build([('s', 'gate', [], [], None, 'switch'), ('y', 'gate', [], ['g']),
               ('x', 'gate', [], [], None, 'fork', 'any')],
              [('IN', 's'), ('IN', 'y'), ('s', 'x'), ('y', 'x'), ('s', 'OUT'), ('x', 'OUT')], goals=['g'])
    assert sem.symptoms(t) == {}
    small, large = t.nmask(['s', 'x', 'y']), t.nmask(['s', 'x', 'y', 'OUT'])
    assert ('goal', 'OUT', 'g') in sem.findings(t, small)
    assert ('goal', 'OUT', 'g') not in sem.findings(t, large)


def test_cyclic_quotient_circular_contracts():
    """T2(d): convex parts {a,d}, {b,c} with a cyclic quotient; flat contracts discharge each other
    although neither requirement is ever established."""
    t = build([('a', 'agent', ['y'], ['x']), ('b', 'agent', ['x'], ['y']), ('c', 'agent', ['x'], ['y']), ('d', 'agent', ['y'], ['x'])],
              [('IN', 'a'), ('IN', 'c'), ('a', 'b'), ('c', 'd'), ('b', 'OUT'), ('d', 'OUT')], goals=['x', 'y'])
    ad, bc = t.nmask(['a', 'd']), t.nmask(['b', 'c'])
    assert sl.is_convex(t, ad) and sl.is_convex(t, bc)
    assert not sl.quotient_is_acyclic(t, [ad, bc, t.nbit['IN'], t.nbit['OUT']])
    # each flat contract is valid when its entries are assumed to carry its assumption
    assert ct.declared_valid(t, ad, t.m(['y']), t.m(['x']))
    assert ct.declared_valid(t, bc, t.m(['x']), t.m(['y']))
    assert {('assume', 'a', 'y'), ('assume', 'c', 'x')} <= set(sem.symptoms(t))
    assert not sem.is_safe(sem.symptoms(t))


def test_confirmation_removes_agent_level_false_alarm():
    """Reviewer counterexample: an outside all-join at face value; the raw singleton finding is
    not a symptom, and confirmation (lifting) removes it."""
    t = build([('s', 'gate', [], [], None, 'switch'), ('a', 'gate', [], ['x']), ('J', 'gate', ['x'], [])],
              [('IN', 's'), ('s', 'a'), ('s', 'OUT'), ('IN', 'J'), ('a', 'J'), ('J', 'OUT')], goals=['g'], inputs=['g'],
              out_join='any')
    assert sem.symptoms(t) == {}
    assert ('assume', 'J', 'x') in sem.findings(t, t.nbit['s'])
    assert an.confirmed_findings(t, t.nbit['s']) == {}
    assert an.check_confirmed(t, sl.singleton(t))['findings'] == {}


@settings(max_examples=120, deadline=None, derandomize=True, suppress_health_check=list(HealthCheck))
@given(st.integers(0, 10_000))
def test_confirmed_findings_match_oracle(seed):
    t = cf.wild_team(seed, n=3 + seed % 3)
    sym = sem.symptoms(t)
    for s in sl.exhaustive(t, 2):
        conf = set(an.confirmed_findings(t, s))
        assert conf == cf.confirmed_oracle(t, s)
        assert all(an.correct(sym, k) for k in conf)


def test_running_example_baselines():
    t = build([('RA', 'agent', [], ['req_spec'], 'g'), ('AR', 'agent', ['req_spec'], ['design'], 'g'),
               ('DV', 'agent', ['design'], ['code', 'tests'], 'g'), ('SR', 'agent', ['code'], ['sec_reviewed'], 'g'),
               ('TS', 'gate', ['tests'], ['tests_pass'])],
              [('IN', 'RA'), ('RA', 'AR'), ('AR', 'DV'), ('DV', 'SR'), ('SR', 'TS'), ('TS', 'OUT')],
              goals=['tests_pass', 'sec_reviewed'], critical=['tests_pass'], f=1)
    k = ('robust', 'OUT', 'tests_pass')
    assert k in an.must_analysis(t)['findings']           # a global must-analysis detects it ...
    s, _ = an.shrink(t, k)
    assert t.nodes_of(s) == ['DV', 'SR', 'TS']            # ... slices localize it
