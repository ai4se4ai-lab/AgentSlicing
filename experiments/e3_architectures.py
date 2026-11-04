"""E3 (RQ2): slice-level blind spots in encoded published multi-agent designs, with a
sensitivity analysis over the contract and oracle assignment."""
from __future__ import annotations

import inspect
import time

from common import environment, save  # noqa: E402 (sets sys.path)
from architectures import DESIGNS
from slicing import analysis as an, semantics as sem, slices as sl
from slicing.model import Team

ALT_JOIN = {'AgentCoder': 1, 'Debate': 1, 'MoA': 1, 'Agentless': 'all'}
VARIANTS = {
    'documented': lambda n, d='backbone': d,
    'distinct': lambda n, d=None: n,
    'shared': lambda n, d=None: 'backbone',
}


def analyse(t: Team):
    sym = sem.symptoms(t)
    rep = an.check(t, sl.exhaustive(t, 5))
    al = set(an.agent_level(t)['findings'])
    out = []
    for k in sorted(sym):
        f = rep['findings'].get(k)
        depth = None if f is None else (1 if f['static'] else min(sl.size(s) for s in f['minimal']))
        out.append({'key': list(k), 'depth': depth, 'class': f and f['class'],
                    'minimal': [t.nodes_of(s) for s in f['minimal']] if f else None, 'agent_level': k in al,
                    'lint': k in an.lint(t)['findings'], 'smell': k in an.smells(t)['findings']})
    return {'safe': sem.is_safe(sym), 'clean': not sym, 'symptoms': out, 'nodes': len(t.order)}


def main():
    env = environment()
    t0 = time.time()
    rows = []
    for name, d in DESIGNS.items():
        fn = d['build']
        has_join = 'join' in inspect.signature(fn).parameters
        variants = [(v, fn(o)) for v, o in VARIANTS.items()]
        doc = fn(VARIANTS['documented'])
        variants.append(('f0', Team(doc.nodes.values(), doc.edges, doc.goals, doc.critical, 0, doc.name)))
        if has_join:
            variants.append(('alt_join', fn(VARIANTS['documented'], join=ALT_JOIN[name])))
        for v, t in variants:
            assert not t.validate(), (name, v, t.validate())
            rows.append({'design': name, 'source': d['source'], 'note': d['note'], 'variant': v, **analyse(t),
                         'spec': t.to_json()})
    save('e3_architectures', {'env': env, 'seconds': time.time() - t0, 'rows': rows})
    for r in rows:
        print(r['design'], r['variant'], 'safe' if r['safe'] else 'UNSAFE',
              [(tuple(s['key']), s['depth'], s['class'], s['agent_level']) for s in r['symptoms']])


if __name__ == '__main__':
    main()
