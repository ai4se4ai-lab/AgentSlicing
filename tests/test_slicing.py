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
    return build([('RA', 'agent', [], ['spec']), ('AR', 'agent', ['spec'], ['design']), ('TM', 'agent', ['spec'], ['threat_model']),
                  ('DV', 'agent', ['design'], ['implemented']), ('ST', 'agent', ['threat_model'], ['sec_tested']),
                  ('RG', 'gate', [], [], None, 'fork', policy)],
                 [('IN', 'RA'), ('RA', 'AR'), ('RA', 'TM'), ('AR', 'DV'), ('TM', 'ST'), ('DV', 'RG'), ('ST', 'RG'), ('RG', 'OUT')],
                 goals=['implemented', 'sec_tested'])


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
    assert set(sem.symptoms(t)) == {('goal', 'OUT', 'implemented'), ('goal', 'OUT', 'sec_tested')}
    assert an.agent_level(t)['findings'] == {}
    rep = an.check(t, sl.exhaustive(t, 3))
    for k in sem.symptoms(t):
        assert sorted(sorted(t.nodes_of(s)) for s in rep['findings'][k]['minimal']) == [['DV', 'RG'], ['RG', 'ST']]
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
