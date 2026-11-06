"""Topology generator and clean contract assignment.

Contracts are assigned in topological order with req(v) drawn from a sound lower bound
on the content of v (the must-analysis), and goals drawn from the bound at OUT, so the
generated team is clean by construction (no symptom); tests confirm it with the exact
semantics on small teams.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

from .model import ALL, INPUT, OUTPUT, Node, Team

TOPOLOGIES = ('chain', 'tree', 'forkjoin', 'layered', 'sp', 'random', 'mixed')


@dataclass
class Params:
    p_gate: float = 0.25          # share of deterministic gates
    oracle_pool: int = 3          # number of distinct oracles (smaller = more sharing)
    req_density: int = 2          # max requirements per node
    shared_facts: int = 3         # size of a pool of facts that several nodes may provide
    n_goals: int = 2
    fault_budget: int = 1
    p_switch: float = 0.3         # in 'mixed': probability that a block is a choice block
    n_critical: int = 0           # number of goals marked critical (E8 uses 1; E2 hosts have none)


# ------------------------------------------------------------------ topologies
class G:
    def __init__(self):
        self.nodes: list[str] = []
        self.edges: list[tuple[str, str]] = []
        self.switch: set[str] = set()
        self.join: dict[str, object] = {}
        self.k = 0

    def new(self) -> str:
        self.k += 1
        n = f'v{self.k}'
        self.nodes.append(n)
        return n


def _chain(g: G, n: int):
    first = prev = g.new()
    for _ in range(n - 1):
        x = g.new()
        g.edges.append((prev, x))
        prev = x
    return first, prev


def _sp(g: G, n: int, rng: random.Random, choice: float):
    """Two-terminal series-parallel block with n nodes; returns (entry, exit)."""
    if n <= 2:
        return _chain(g, n)
    r = rng.random()
    if n >= 4 and r < 0.5:
        k = rng.randint(2, min(3, (n - 2)))
        fork = g.new()
        branches_budget = n - 2
        sizes = [1] * k
        for _ in range(branches_budget - k):
            sizes[rng.randrange(k)] += 1
        ends = []
        alt = rng.random() < choice
        for s in sizes:
            a, b = _sp(g, s, rng, choice)
            g.edges.append((fork, a))
            ends.append(b)
        join = g.new()
        for b in ends:
            g.edges.append((b, join))
        if alt:
            g.switch.add(fork)
            g.join[join] = 1
        return fork, join
    a = rng.randint(1, n - 1)
    e1, x1 = _sp(g, a, rng, choice)
    e2, x2 = _sp(g, n - a, rng, choice)
    g.edges.append((x1, e2))
    return e1, x2


def topology(kind: str, n: int, rng: random.Random, params: Params) -> G:
    g = G()
    if kind == 'chain':
        a, b = _chain(g, n)
        g.edges += [(INPUT, a), (b, OUTPUT)]
    elif kind == 'tree':
        root = g.new()
        g.edges.append((INPUT, root))
        for _ in range(n - 1):
            parent = rng.choice(g.nodes)
            x = g.new()
            g.edges.append((parent, x))
        for v in g.nodes:
            if not any(u == v for u, _ in g.edges):
                g.edges.append((v, OUTPUT))
    elif kind == 'forkjoin':
        prev = INPUT
        left = n
        while left > 0:
            if left >= 4 and rng.random() < 0.6:
                k = rng.randint(2, min(3, left - 2))
                fork = g.new()
                g.edges.append((prev, fork))
                ends = []
                budget = min(left - 2, k * 2)
                sizes = [1] * k
                for _ in range(budget - k):
                    sizes[rng.randrange(k)] += 1
                for s in sizes:
                    a, b = _chain(g, s)
                    g.edges.append((fork, a))
                    ends.append(b)
                join = g.new()
                for b in ends:
                    g.edges.append((b, join))
                prev = join
                left -= 2 + sum(sizes)
            else:
                x = g.new()
                g.edges.append((prev, x))
                prev = x
                left -= 1
        g.edges.append((prev, OUTPUT))
    elif kind == 'layered':
        width = max(2, round(n ** 0.5))
        layers = []
        left = n
        while left > 0:
            w = min(left, rng.randint(1, width))
            layers.append([g.new() for _ in range(w)])
            left -= w
        for v in layers[0]:
            g.edges.append((INPUT, v))
        for L1, L2 in zip(layers, layers[1:]):
            for v in L2:
                g.edges.append((rng.choice(L1), v))
            for u in L1:
                if not any(a == u for a, _ in g.edges):
                    g.edges.append((u, rng.choice(L2)))
            for u in L1:
                if rng.random() < 0.3:
                    g.edges.append((u, rng.choice(L2)))
        for v in layers[-1]:
            g.edges.append((v, OUTPUT))
    elif kind in ('sp', 'mixed'):
        a, b = _sp(g, n, rng, params.p_switch if kind == 'mixed' else 0.0)
        g.edges += [(INPUT, a), (b, OUTPUT)]
    elif kind == 'random':
        nodes = [g.new() for _ in range(n)]
        p = min(0.5, 2.5 / max(1, n))
        for j, v in enumerate(nodes):
            preds = [u for u in nodes[:j] if rng.random() < p]
            if not preds:
                preds = [rng.choice(nodes[:j])] if j and rng.random() < 0.8 else [INPUT]
            for u in preds:
                g.edges.append((u, v))
        for u in nodes:
            if not any(a == u for a, _ in g.edges):
                g.edges.append((u, OUTPUT))
    else:
        raise ValueError(kind)
    g.edges = list(dict.fromkeys(g.edges))
    return g


# ------------------------------------------------------------------ contracts
def lower_out(nodes: dict, preds: dict, order: list[str], props: list[str]) -> dict:
    """Must-analysis (property sets as Python sets) used during assignment."""
    lo_c, lo_o = {}, {}
    for n in order:
        node = nodes[n]
        ps = preds.get(n, [])
        if n == INPUT:
            lo_c[n], lo_o[n] = set(), set(node.gua)
            continue
        q = ALL if len(ps) <= 1 else node.join
        if q == ALL:
            c = set().union(*(lo_o[p] for p in ps)) if ps else set()
        else:
            allp = set().union(*(lo_o[p] for p in ps))
            c = {x for x in allp if sum(1 for p in ps if x not in lo_o[p]) < q}
        lo_c[n] = c
        lo_o[n] = c | set(node.gua) if set(node.req) <= c | set(node.decl) else c
    return lo_c


def assign(g: G, rng: random.Random, params: Params, name: str) -> Team:
    preds: dict = {}
    for u, v in g.edges:
        preds.setdefault(v, []).append(u)
    t0 = Team([Node(INPUT, 'gate'), Node(OUTPUT, 'gate')] + [Node(n, 'gate') for n in g.nodes], g.edges)
    order = list(t0.order)
    oracles = [f'o{i}' for i in range(params.oracle_pool)]
    shared = [f's{i}' for i in range(params.shared_facts)]
    nodes = {INPUT: Node(INPUT, 'gate', gua=frozenset({'input'}))}
    lo_c, lo_o = {INPUT: set()}, {INPUT: {'input'}}
    for n in order:
        if n == INPUT:
            continue
        ps = preds.get(n, [])
        join = g.join.get(n, ALL)
        q = ALL if len(ps) <= 1 else join
        if q == ALL:
            c = set().union(*(lo_o[p] for p in ps))
        else:
            allp = set().union(*(lo_o[p] for p in ps))
            c = {x for x in allp if sum(1 for p in ps if x not in lo_o[p]) < q}
        lo_c[n] = c
        if n == OUTPUT:
            continue
        kind = 'gate' if rng.random() < params.p_gate else 'agent'
        gua = {f'w_{n}'}
        if rng.random() < 0.3:
            gua.add(rng.choice(shared))
        cand = sorted(c - {'input'}) or sorted(c)
        k = min(len(cand), rng.randint(0, params.req_density))
        req = set(rng.sample(cand, k)) if k else set()
        route = 'switch' if n in g.switch else 'fork'
        nodes[n] = Node(n, kind, frozenset(req), frozenset(gua), frozenset(),
                        rng.choice(oracles) if kind == 'agent' else None, route, join)
        lo_o[n] = c | gua
    cand = sorted(x for x in lo_c[OUTPUT] if x.startswith('w_'))
    goals = rng.sample(cand, min(params.n_goals, len(cand))) if cand else []
    nodes[OUTPUT] = Node(OUTPUT, 'gate', req=frozenset(goals), join=g.join.get(OUTPUT, ALL))
    critical = rng.sample(sorted(goals), min(params.n_critical, len(goals))) if params.n_critical else ()
    return Team(nodes.values(), g.edges, goals, critical, params.fault_budget, name)


def generate(kind: str, n: int, seed: int, params: Params | None = None) -> Team:
    params = params or Params()
    rng = random.Random(f'{kind}/{n}/{seed}')
    g = topology(kind, n, rng, params)
    return assign(g, rng, params, f'{kind}-{n}-{seed}')
