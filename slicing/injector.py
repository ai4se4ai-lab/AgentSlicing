"""Blind-spot injector: adds one known defect (or a decoy) to a clean team and records
ground truth: class, root-cause nodes, and the symptom keys the defect must produce.

Goal-related gadgets are placed in a *release stage* inserted before OUT (a bridge, so
every route passes it); fact-related gadgets are placed on a random edge with a fresh
consumer right after the gadget, so no other path can supply the fact.
"""
from __future__ import annotations

import random
from dataclasses import replace

from .model import ALL, INPUT, OUTPUT, Node, Team

CLASSES = ('A1', 'A2', 'A3', 'S1v', 'A4', 'S2', 'S3', 'S4', 'S5', 'S6a', 'S6b')
DECOYS = ('D2', 'D4', 'D5', 'D6')
HIDDEN = ('S2', 'S3', 'S4', 'S5', 'S6a', 'S6b')


class Builder:
    def __init__(self, team: Team, tag: str):
        self.nodes = dict(team.nodes)
        self.edges = list(team.edges)
        self.goals, self.critical = set(team.goals), set(team.critical)
        self.f = team.f
        self.name = team.name
        self.tag = tag
        self.k = 0

    def add(self, kind='agent', req=(), gua=(), oracle=None, route='fork', join=ALL, decl=()):
        self.k += 1
        n = f'{self.tag}{self.k}'
        if kind == 'agent' and oracle is None:
            oracle = f'q_{n}'
        self.nodes[n] = Node(n, kind, frozenset(req), frozenset(gua), frozenset(decl),
                             oracle if kind == 'agent' else None, route, join)
        return n

    def set(self, n, **kw):
        self.nodes[n] = replace(self.nodes[n], **kw)

    def release_stage(self):
        """Insert P between OUT's predecessors and OUT; return P (OUT then has in-edge P->...)."""
        out = self.nodes[OUTPUT]
        p = self.add('gate', join=out.join)
        self.edges = [(u, p) if v == OUTPUT else (u, v) for u, v in self.edges]
        self.set(OUTPUT, join=ALL)
        return p

    def chain(self, start, k, **kw):
        prev, made = start, []
        for _ in range(k):
            x = self.add('agent', **kw)
            self.edges.append((prev, x))
            made.append(x)
            prev = x
        return made

    def split_edge(self, rng: random.Random):
        cands = [(u, v) for u, v in self.edges if v != OUTPUT]
        u, v = rng.choice(cands or self.edges)
        self.edges.remove((u, v))
        return u, v

    def team(self) -> Team:
        nodes = dict(self.nodes)
        nodes[OUTPUT] = replace(nodes[OUTPUT], req=frozenset(self.goals))
        return Team(nodes.values(), self.edges, self.goals, self.critical, self.f, f'{self.name}+{self.tag}')


def inject(team: Team, cls: str, seed: int, depth: int | None = None) -> tuple[Team, dict]:
    rng = random.Random(f'{team.name}/{cls}/{seed}')
    b = Builder(team, 'g')
    d = depth if depth is not None else rng.randint(0, 2)       # intermediate nodes in chains
    inner = [n for n in team.order if n not in (INPUT, OUTPUT)]
    gt = {'class': cls, 'root': [], 'keys': [], 'decoy': cls in DECOYS or cls == 'clean'}
    if cls == 'clean':
        if rng.random() < 0.5:
            p = b.release_stage()
            g = b.add('gate', gua={'crit_ok'})
            b.edges += [(p, g), (g, OUTPUT)]
            b.goals.add('crit_ok'); b.critical.add('crit_ok')
        return b.team(), gt
    if cls == 'A1':
        b.goals.add('unowned')
        gt.update(root=[OUTPUT], keys=[('goal', OUTPUT, 'unowned')])
    elif cls == 'A2':
        v = rng.choice(inner)
        b.set(v, req=b.nodes[v].req | {'never_provided'})
        gt.update(root=[v], keys=[('assume', v, 'never_provided')])
    elif cls == 'A3':
        pairs = [(v, w) for v in inner for w in inner if w != v and not team.anc[v] & team.nbit[w]]
        v, w = rng.choice(pairs)
        b.set(v, req=b.nodes[v].req | {'late_fact'})
        b.set(w, gua=b.nodes[w].gua | {'late_fact'})
        gt.update(root=[v, w], keys=[('assume', v, 'late_fact')])
    elif cls == 'S1v':
        pairs = [(v, a) for v in inner for a in team.nodes_of(team.anc[v]) if a != INPUT]
        if not pairs:
            return inject(team, 'A2', seed)
        v, a = rng.choice(pairs)
        b.set(a, gua=b.nodes[a].gua | {'spec@raw'})
        b.set(v, req=b.nodes[v].req | {'spec@summary'})
        gt.update(root=[v, a], keys=[('assume', v, 'spec@summary')])
    elif cls == 'A4':
        p = b.release_stage()
        r = b.add('agent', gua={'crit'})
        b.edges += [(p, r), (r, OUTPUT)]
        b.goals.add('crit'); b.critical.add('crit')
        gt.update(root=[r], keys=[('robust', OUTPUT, 'crit')])
    elif cls in ('S2', 'D2'):
        p = b.release_stage()
        k = rng.choice((2, 3))
        q = 1 if k == 2 else 2
        j = b.add('gate', join=q)
        goals = [f'rev{i}' for i in range(k)]
        branch_nodes = []
        for i in range(k):
            br = b.chain(p, 1 + rng.randint(0, d))
            claim = set(goals) if cls == 'D2' else {goals[i]}
            b.set(br[0], gua=b.nodes[br[0]].gua | claim)
            b.edges.append((br[-1], j))
            branch_nodes += br
        b.edges.append((j, OUTPUT))
        b.goals |= set(goals)
        if cls == 'S2':
            gt.update(root=[j] + branch_nodes, keys=[('goal', OUTPUT, g) for g in goals])
    elif cls in ('S3',):
        u, v = b.split_edge(rng)
        fork = b.add('agent')
        b.edges.append((u, fork))
        br1 = b.chain(fork, 1 + rng.randint(0, d))
        br2 = b.chain(fork, 1 + rng.randint(0, d))
        b.set(br1[0], gua=b.nodes[br1[0]].gua | {'merged_fact'})
        m = b.add('gate', join=1)
        b.edges += [(br1[-1], m), (br2[-1], m)]
        c = b.add('agent', req={'merged_fact'})
        b.edges += [(m, c), (c, v)]
        gt.update(root=[m] + br1 + br2, keys=[('assume', c, 'merged_fact')])
    elif cls in ('S4', 'D4'):
        p = b.release_stage()
        r1 = b.add('agent', gua={'crit'}, oracle='shared_llm')
        b.edges.append((p, r1))
        mid = b.chain(r1, d)
        r2 = b.add('agent', gua={'crit'}, oracle='shared_llm')
        b.edges.append(((mid[-1] if mid else r1), r2))
        last = r2
        if cls == 'D4':
            gb = b.add('gate', gua={'crit'})
            b.edges.append((r2, gb))
            last = gb
        b.edges.append((last, OUTPUT))
        b.goals.add('crit'); b.critical.add('crit')
        if cls == 'S4':
            gt.update(root=[r1, r2] + mid, keys=[('robust', OUTPUT, 'crit')])
    elif cls in ('S5', 'D5'):
        u, v = b.split_edge(rng)
        w = b.add('agent', route='switch')
        b.edges.append((u, w))
        rv = b.chain(w, 1 + rng.randint(0, d))
        b.set(rv[0], gua=b.nodes[rv[0]].gua | {'reviewed'})
        m = b.add('gate', join=1)
        b.edges.append((rv[-1], m))
        if cls == 'S5':
            b.edges.append((w, m))
        else:
            alt = b.add('agent', gua={'reviewed'})
            b.edges += [(w, alt), (alt, m)]
        c = b.add('agent', req={'reviewed'})
        b.edges += [(m, c), (c, v)]
        if cls == 'S5':
            gt.update(root=[w, m] + rv, keys=[('assume', c, 'reviewed')])
    elif cls in ('S6a', 'D6'):
        p = b.release_stage()
        start = p
        if cls == 'D6':
            backup = b.add('gate', gua={'test_suite'})
            b.edges.append((p, backup))
            start = backup
        a = b.add('agent', gua={'test_suite'})
        b.edges.append((start, a))
        mid = b.chain(a, d)
        g = b.add('gate', req={'test_suite'}, gua={'tests_pass'})
        b.edges += [((mid[-1] if mid else a), g), (g, OUTPUT)]
        b.goals.add('tests_pass'); b.critical.add('tests_pass')
        if cls == 'S6a':
            gt.update(root=[a, g] + mid, keys=[('robust', OUTPUT, 'tests_pass')])
    elif cls == 'S6b':
        p = b.release_stage()
        y = b.add('gate')                 # would provide 'approval'; the provision is missing
        a = b.add('agent', req={'approval'}, gua={'design_ok'})
        b.edges += [(p, y), (y, a)]
        mid = b.chain(a, d)
        g = b.add('gate', req={'design_ok'}, gua={'released_ok'})
        b.edges += [((mid[-1] if mid else a), g), (g, OUTPUT)]
        b.goals.add('released_ok')
        gt.update(root=[y, a, g] + mid, keys=[('goal', OUTPUT, 'released_ok'), ('assume', a, 'approval')],
                  primary=('goal', OUTPUT, 'released_ok'))
    else:
        raise ValueError(cls)
    t = b.team()
    gt.setdefault('primary', gt['keys'][0] if gt['keys'] else None)
    return t, gt
