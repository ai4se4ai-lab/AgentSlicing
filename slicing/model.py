"""Teams: typed DAGs of agents and deterministic gates with contracts (Definition 1).

Properties are interned to bit positions so that property sets are Python ints.
A team is immutable after construction; edits return new teams (see `Team.replace`).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, replace as dc_replace
from typing import Iterable

INPUT, OUTPUT = 'IN', 'OUT'
ALL = 'all'


@dataclass(frozen=True)
class Node:
    id: str
    kind: str = 'agent'                 # 'agent' | 'gate' (IN and OUT are gates)
    req: frozenset = frozenset()        # requirements (assumptions)
    gua: frozenset = frozenset()        # guarantees (provided properties and goals)
    decl: frozenset = frozenset()       # declared evidence (local, never inherited)
    oracle: str | None = None           # reasoning engine of an agent
    route: str = 'fork'                 # 'fork' (deliver to all successors) | 'switch' (one)
    join: object = ALL                  # 'all' or an int q >= 1 ('any' == 1)

    @property
    def fallible(self) -> bool:
        return self.kind == 'agent'


def _join(value):
    if value in (None, ALL):
        return ALL
    if value == 'any':
        return 1
    if isinstance(value, str) and value.startswith('quorum:'):
        return int(value.split(':')[1])
    return int(value)


class Team:
    """A well-formed team. Node order is a fixed topological order."""

    def __init__(self, nodes: Iterable[Node], edges: Iterable[tuple[str, str]], goals=(), critical=(),
                 fault_budget: int = 0, name: str = 'team'):
        self.name = name
        self.nodes = {n.id: n for n in nodes}
        self.edges = tuple(dict.fromkeys((u, v) for u, v in edges))
        self.goals = frozenset(goals)
        self.critical = frozenset(critical)
        self.f = int(fault_budget)
        succ = {n: [] for n in self.nodes}
        pred = {n: [] for n in self.nodes}
        for u, v in self.edges:
            if u not in self.nodes or v not in self.nodes:
                raise ValueError(f'edge {u}->{v} names an unknown node')
            succ[u].append(v)
            pred[v].append(u)
        self.succ = {k: tuple(v) for k, v in succ.items()}
        self.pred = {k: tuple(v) for k, v in pred.items()}
        # a switch with fewer than two successors has nothing to choose: it is a fork
        for k, node in list(self.nodes.items()):
            if node.route == 'switch' and len(self.succ[k]) < 2:
                self.nodes[k] = dc_replace(node, route='fork')
        self.order = self._topo()
        self.index = {n: i for i, n in enumerate(self.order)}
        props = set(self.goals)
        for n in self.nodes.values():
            props |= n.req | n.gua | n.decl
        self.props = tuple(sorted(props))
        self.bit = {p: 1 << i for i, p in enumerate(self.props)}
        self.mask = {n: self._masks(self.nodes[n]) for n in self.nodes}
        self.goal_mask = self.m(self.goals)
        self.crit_mask = self.m(self.critical)
        nbit = {n: 1 << i for i, n in enumerate(self.order)}
        self.nbit = nbit
        anc = {}
        for n in self.order:
            a = 0
            for p in self.pred[n]:
                a |= anc[p] | nbit[p]
            anc[n] = a
        desc = {}
        for n in reversed(self.order):
            d = 0
            for s in self.succ[n]:
                d |= desc[s] | nbit[s]
            desc[n] = d
        self.anc, self.desc = anc, desc

    # ---- helpers
    def m(self, props) -> int:
        out = 0
        for p in props:
            out |= self.bit[p]
        return out

    def names(self, mask: int) -> list[str]:
        return [p for p in self.props if mask & self.bit[p]]

    def nodes_of(self, nmask: int) -> list[str]:
        out, order = [], self.order
        while nmask:
            low = nmask & -nmask
            out.append(order[low.bit_length() - 1])
            nmask ^= low
        return out

    def nmask(self, ids) -> int:
        out = 0
        for n in ids:
            out |= self.nbit[n]
        return out

    def _masks(self, node: Node):
        return (self.m(node.req), self.m(node.gua), self.m(node.decl))

    def _topo(self):
        indeg = {n: len(self.pred[n]) for n in self.nodes}
        ready = sorted(n for n, d in indeg.items() if d == 0)
        order = []
        while ready:
            n = ready.pop(0)
            order.append(n)
            for s in self.succ[n]:
                indeg[s] -= 1
                if indeg[s] == 0:
                    ready.append(s)
            ready.sort()
        if len(order) != len(self.nodes):
            raise ValueError('team graph has a cycle')
        return tuple(order)

    def validate(self) -> list[str]:
        """Structural well-formedness (liveness is checked in semantics.live_nodes)."""
        errs = []
        if INPUT not in self.nodes or OUTPUT not in self.nodes:
            errs.append('missing IN or OUT')
            return errs
        if self.pred[INPUT]:
            errs.append('IN has predecessors')
        if self.succ[OUTPUT]:
            errs.append('OUT has successors')
        for n in self.order:
            if n != INPUT and not self.pred[n]:
                errs.append(f'{n} has no predecessor')
            if n != OUTPUT and not self.succ[n]:
                errs.append(f'{n} has no successor')
            node = self.nodes[n]
            if node.join != ALL and len(self.pred[n]) < 2:
                pass
            if node.join != ALL and node.join > max(1, len(self.pred[n])):
                errs.append(f'{n} quorum exceeds in-degree')
            if node.kind == 'agent' and node.oracle is None:
                errs.append(f'agent {n} has no oracle')
        if self.nodes[OUTPUT].req != self.goals:
            errs.append('OUT.req must equal the goals')
        if not self.critical <= self.goals:
            errs.append('critical goals must be goals')
        return errs

    @property
    def oracles(self) -> tuple:
        return tuple(sorted({n.oracle for n in self.nodes.values() if n.kind == 'agent'}))

    def replace(self, node_id: str | None = None, edges=None, goals=None, critical=None, fault_budget=None, **changes) -> 'Team':
        nodes = dict(self.nodes)
        if node_id is not None:
            nodes[node_id] = dc_replace(nodes[node_id], **changes)
        return Team(nodes.values(), self.edges if edges is None else edges,
                    self.goals if goals is None else goals, self.critical if critical is None else critical,
                    self.f if fault_budget is None else fault_budget, self.name)

    # ---- (de)serialization: the team specification language (TSL), JSON
    def to_json(self) -> dict:
        def node(n: Node):
            d = {'id': n.id, 'kind': n.kind, 'req': sorted(n.req), 'gua': sorted(n.gua)}
            if n.decl:
                d['decl'] = sorted(n.decl)
            if n.oracle is not None:
                d['oracle'] = n.oracle
            if n.route != 'fork':
                d['route'] = n.route
            if n.join != ALL:
                d['join'] = 'any' if n.join == 1 else f'quorum:{n.join}'
            return d
        return {'name': self.name, 'goals': sorted(self.goals), 'critical': sorted(self.critical),
                'fault_budget': self.f, 'nodes': [node(self.nodes[n]) for n in self.order],
                'edges': [list(e) for e in self.edges]}

    @staticmethod
    def from_json(d: dict) -> 'Team':
        goals = d.get('goals', [])
        nodes = []
        for x in d['nodes']:
            nodes.append(Node(x['id'], x.get('kind', 'agent'), frozenset(x.get('req', [])), frozenset(x.get('gua', [])),
                              frozenset(x.get('decl', [])), x.get('oracle'), x.get('route', 'fork'), _join(x.get('join'))))
        ids = {n.id for n in nodes}
        if INPUT not in ids:
            nodes.append(Node(INPUT, 'gate', gua=frozenset(d.get('input', []))))
        if OUTPUT not in ids:
            nodes.append(Node(OUTPUT, 'gate', req=frozenset(goals), join=_join(d.get('output_join'))))
        return Team(nodes, [tuple(e) for e in d['edges']], goals, d.get('critical', []), d.get('fault_budget', 0), d.get('name', 'team'))

    def dumps(self) -> str:
        return json.dumps(self.to_json(), sort_keys=True)


def build(spec_nodes: list[tuple], edges, goals=(), critical=(), f=0, inputs=(), out_join=ALL, name='team') -> Team:
    """Compact constructor used in tests and examples.

    spec_nodes: (id, kind, req, gua[, oracle[, route[, join[, decl]]]])
    """
    nodes = [Node(INPUT, 'gate', gua=frozenset(inputs)), Node(OUTPUT, 'gate', req=frozenset(goals), join=_join(out_join))]
    for t in spec_nodes:
        i, kind, req, gua = t[:4]
        oracle = t[4] if len(t) > 4 else (i if kind == 'agent' else None)
        route = t[5] if len(t) > 5 else 'fork'
        join = _join(t[6]) if len(t) > 6 else ALL
        decl = frozenset(t[7]) if len(t) > 7 else frozenset()
        if kind == 'agent' and oracle is None:
            oracle = i
        nodes.append(Node(i, kind, frozenset(req), frozenset(gua), decl, oracle if kind == 'agent' else None, route, join))
    return Team(nodes, edges, goals, critical, f, name)
