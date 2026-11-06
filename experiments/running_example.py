"""Running example of the paper (Section 2.6): the chain and fork-join software teams.

Records what the agent-level checker, the lint, and slice-level analysis report, the
derived and naive contracts of the slices discussed in the text, and the repairs.
"""
from __future__ import annotations

import time

from common import environment, save  # noqa: F401 (sets sys.path)
from slicing import analysis as an, contracts as ct, semantics as sem, slices as sl
from slicing.model import build


def chain(repair=None):
    nodes = [('RA', 'agent', [], ['req_spec'], 'g'), ('AR', 'agent', ['req_spec'], ['design'], 'g'),
             ('DV', 'agent', ['design'], ['code', 'tests'], 'g'), ('SR', 'agent', ['code'], ['sec_reviewed'], 'g'),
             ('TS', 'gate', ['tests'], ['tests_pass'])]
    edges = [('IN', 'RA'), ('RA', 'AR'), ('AR', 'DV'), ('DV', 'SR'), ('SR', 'TS'), ('TS', 'OUT')]
    if repair == 'downstream':
        # a deterministic test generator that needs DV's code: still rests on the shared oracle
        nodes.append(('TG', 'gate', ['code'], ['tests']))
        edges = [('IN', 'RA'), ('RA', 'AR'), ('AR', 'DV'), ('DV', 'TG'), ('TG', 'SR'), ('SR', 'TS'), ('TS', 'OUT')]
    elif repair == 'independent':
        # an independent test designer on another model, fed by the input, joined at the test gate
        nodes.append(('TD', 'agent', [], ['tests'], 'h'))
        edges += [('IN', 'TD'), ('TD', 'TS')]
    return build(nodes, edges, goals=['tests_pass', 'sec_reviewed'], critical=['tests_pass'], f=1, name='chain')


def forkjoin(policy='any'):
    """The developer's code forks to a code reviewer (CR) and a security tester (ST); both feed a
    release gate (RG) that releases on the first approval."""
    return build([('RA', 'agent', [], ['spec']), ('AR', 'agent', ['spec'], ['design']), ('DV', 'agent', ['design'], ['code']),
                  ('CR', 'agent', ['code'], ['reviewed']), ('ST', 'agent', ['code'], ['sec_tested']),
                  ('RG', 'gate', [], [], None, 'fork', policy)],
                 [('IN', 'RA'), ('RA', 'AR'), ('AR', 'DV'), ('DV', 'CR'), ('DV', 'ST'), ('CR', 'RG'), ('ST', 'RG'), ('RG', 'OUT')],
                 goals=['reviewed', 'sec_tested'], name=f'forkjoin-{policy}')


def report(t, kmax):
    sym = sem.symptoms(t)
    al = an.check_confirmed(t, sl.singleton(t))['findings']
    rep = an.check_confirmed(t, sl.exhaustive(t, kmax))
    keys = []
    for k in sorted(sym):
        f = rep['findings'].get(k)
        keys.append({'key': list(k), 'class': f and f['class'],
                     'depth': None if f is None else (1 if f['static'] else min(sl.size(s) for s in f['minimal'])),
                     'minimal': [t.nodes_of(s) for s in f['minimal']] if f else None,
                     'witness': sym[k]})
    return {'nodes': len(t.order), 'convex_slices': len(sl.all_convex(t)), 'slices_checked': len(sl.exhaustive(t, kmax)),
            'safe': sem.is_safe(sym), 'symptoms': keys, 'agent_level': [list(k) for k in al],
            'lint': [list(k) for k in an.lint(t)['findings']], 'smells': [list(k) for k in an.smells(t)['findings']],
            'must': [list(k) for k in an.must_analysis(t)['findings']],
            'shrink': {str(k): t.nodes_of(an.shrink(t, k)[0]) for k, w in sym.items() if w.get('slice')}}


def contract(t, members, env_props, faults=False):
    s = t.nmask(members)
    env = t.m(env_props)
    d = ct.derived_contract(t, s, env, faults)
    out = {'slice': members, 'env': env_props, 'assume': sorted([list(a) for a in d['assume']]),
           'guarantee': t.names(d['guarantee']), 'naive': t.names(ct.naive_contract(t, s, env))}
    if 'robust' in d:
        out['robust'] = t.names(d['robust'])
    return out


def main():
    env = environment()
    t0 = time.time()
    c, f = chain(), forkjoin()
    payload = {
        'env': env,
        'chain': report(c, len(c.order)),
        'chain_repair_downstream': report(chain('downstream'), 7),
        'chain_repair_independent': report(chain('independent'), 7),
        'forkjoin': report(f, len(f.order)),
        'forkjoin_all': report(forkjoin('all'), 4),
        'contracts': {
            'chain_DV_SR_TS': contract(c, ['DV', 'SR', 'TS'], ['req_spec', 'design'], faults=True),
            'chain_SR_TS': contract(c, ['SR', 'TS'], ['req_spec', 'design', 'code', 'tests'], faults=True),
            'fj_CR_RG': contract(f, ['CR', 'RG'], ['spec', 'design', 'code']),
            'fj_ST_RG': contract(f, ['ST', 'RG'], ['spec', 'design', 'code']),
            'fj_CR_ST': contract(f, ['CR', 'ST'], ['spec', 'design', 'code']),
        },
        'strategies': {name: [f.nodes_of(s) for s in fn(f)] for name, fn in
                       [('band1', lambda t: sl.band(t, 1)), ('region', sl.region), ('goal', sl.goal_directed),
                        ('window2', lambda t: sl.window(t, 2))]},
    }
    payload['seconds'] = time.time() - t0
    save('running_example', payload)
    for k in ('chain', 'chain_repair_downstream', 'chain_repair_independent', 'forkjoin', 'forkjoin_all'):
        print(k, payload[k]['safe'], [(s['key'], s['class'], s['depth'], s['minimal']) for s in payload[k]['symptoms']],
              'AL', payload[k]['agent_level'])


if __name__ == '__main__':
    main()
