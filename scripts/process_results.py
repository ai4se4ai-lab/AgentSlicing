"""Turn results/*.json into statistics, LaTeX tables, figures and result macros.

Every number in the paper comes from here: docs/TSE/results_macros.tex (\\res... macros)
and docs/TSE/tables/*.tex; figures go to docs/TSE/figures/*.pdf. Do not hand-edit outputs.
"""
from __future__ import annotations

import json
import math
import os
import re
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / 'results'
OUT = Path(os.environ.get('SLICING_OUT', ROOT / 'docs/TSE'))
(OUT / 'tables').mkdir(parents=True, exist_ok=True)
(OUT / 'figures').mkdir(parents=True, exist_ok=True)
RNG = np.random.default_rng(20261104)
MACROS: dict = {}
SUMMARY: dict = {}
COLORS = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#6250d6']
MARKERS = ['o', 's', '^', 'D', 'v', 'P', 'X']
STYLES = ['-', '--', '-.', ':', '-', '--', '-.']
HIDDEN = ['S2', 'S3', 'S4', 'S6a', 'S6b']
DIGITS = dict(zip('0123456789', ['Zero', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine']))


def load(name):
    p = RES / f'{name}.json'
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else None


def mname(s):
    s = ''.join(DIGITS.get(c, c) for c in s)
    return 'res' + re.sub(r'[^A-Za-z]', '', s)


def macro(name, value, fmt=None):
    if fmt == 'pct':
        v = f'{100 * value:.1f}\\%'
    elif fmt == 'int' or (fmt is None and isinstance(value, (int, np.integer))):
        v = f'{int(value):,}'.replace(',', '{,}')
    elif fmt == 'p':
        v = '<0.001' if value < 0.001 else f'{value:.3f}'
    elif isinstance(value, float) or fmt:
        v = f'{value:{fmt or ".2f"}}'
    else:
        v = str(value)
    MACROS[mname(name)] = v
    return v


def boot_ci(x, n=10_000):
    x = np.asarray(x, float)
    if len(x) == 0:
        return (math.nan, math.nan, math.nan)
    idx = RNG.integers(0, len(x), (n, len(x)))
    m = x[idx].mean(axis=1)
    return (float(x.mean()), float(np.quantile(m, 0.025)), float(np.quantile(m, 0.975)))


def a12(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    gt = sum((xi > y).sum() for xi in x)
    eq = sum((xi == y).sum() for xi in x)
    return float((gt + 0.5 * eq) / (len(x) * len(y)))


def wilcoxon_greater(x, y):
    d = np.asarray(x, float) - np.asarray(y, float)
    if np.all(d == 0):
        return 1.0
    return float(stats.wilcoxon(x, y, alternative='greater', zero_method='zsplit').pvalue)


def holm(ps):
    order = np.argsort(ps)
    adj = np.empty(len(ps))
    run = 0.0
    for rank, i in enumerate(order):
        run = max(run, min(1.0, (len(ps) - rank) * ps[i]))
        adj[i] = run
    return adj


def mcnemar(a, b):
    """Exact McNemar on paired booleans: returns (b01, b10, p)."""
    b10 = sum(1 for x, y in zip(a, b) if x and not y)
    b01 = sum(1 for x, y in zip(a, b) if y and not x)
    n = b10 + b01
    p = 1.0 if n == 0 else float(stats.binomtest(b10, n, 0.5).pvalue)
    return b01, b10, p


def pct(x):
    return f'{100 * x:.1f}'


TABLES: dict = {}
FIGS: dict = {}
PGF_COLORS = ['cA', 'cB', 'cC', 'cD', 'cE', 'cF', 'cG']
PGF_MARKS = ['*', 'square*', 'triangle*', 'diamond*', 'pentagon*', '+', 'x']
PGF_STYLES = ['solid', 'dashed', 'dashdotted', 'densely dotted', 'solid', 'dashed', 'dashdotted']


def write_table(name, text):
    """Table bodies go to docs/TSE/tables/ (artifact) and into the generated block of main.tex."""
    (OUT / 'tables' / f'{name}.tex').write_text(text + '\n', encoding='utf-8')
    TABLES['tab' + ''.join(w.capitalize() for w in name.split('_'))] = text


def coords(xs, ys):
    return ' '.join(f'({x:.6g},{y:.6g})' for x, y in zip(xs, ys) if not (math.isnan(x) or math.isnan(y)))


def pgf_series(i, xs, mean, lo=None, hi=None, legend=None, color=None, width='semithick'):
    """One line (and an optional confidence band) as pgfplots commands."""
    col = color or PGF_COLORS[i % 7]
    out = []
    if lo is not None:
        band = coords(list(xs) + list(xs)[::-1], list(lo) + list(hi)[::-1])
        out.append(f'\\addplot[fill={col},fill opacity=0.15,draw=none,forget plot] coordinates {{{band}}} -- cycle;')
    out.append(f'\\addplot[{col},{width},{PGF_STYLES[i % 7]},mark={PGF_MARKS[i % 7]},mark size=1.4pt,mark options={{solid}}] '
               f'coordinates {{{coords(xs, mean)}}};')
    if legend:
        out.append(f'\\addlegendentry{{{legend}}}')
    return '\n'.join(out)


def plt():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as p
    p.rcParams.update({'font.size': 8, 'axes.spines.top': False, 'axes.spines.right': False, 'axes.grid': True,
                       'grid.color': '#e6e6e3', 'grid.linewidth': 0.6, 'axes.edgecolor': '#8a8a85', 'pdf.fonttype': 42,
                       'legend.frameon': False, 'lines.linewidth': 1.6})
    return p


# ------------------------------------------------------------------ E1 / proofs
def e1():
    d, pr, mu = load('e1_conformance'), load('proofs'), load('proof_mutants')
    if pr:
        rows = pr['obligations']
        macro('ProofObligations', len(rows))
        macro('ProofValid', sum(r['ok'] for r in rows))
        macro('ProofSteps', sum(r['expect'] == 'unsat' for r in rows))
        macro('ProofCountermodels', sum(r['expect'] == 'sat' for r in rows))
        macro('ProofSeconds', sum(r['seconds'] for r in rows), '.2f')
        macro('ZThreeVersion', pr['solver'].split()[-1])
        lines = [f"{r['obligation'].split('-', 1)[0]} & {r['obligation'].split('-', 1)[1].replace('-', ' ')} & {r['theorem']} & "
                 f"{'valid' if r['expect'] == 'unsat' else 'countermodel'} & {'\\checkmark' if r['ok'] else '$\\times$'} \\\\" for r in rows]
        write_table('proofs', '\n'.join(lines))
    if mu:
        macro('Mutants', len(mu))
        macro('MutantsKilled', sum(r['killed'] for r in mu))
    if d:
        w, b = d['wild'], d['bench']
        macro('WildTeams', w['teams'])
        macro('BenchTeams', b['teams'])
        comps = sum(w['checked'].values()) + sum(b['checked'].values())
        macro('ConformanceComparisons', comps)
        macro('ConformanceMismatches', sum(w['mismatching_teams'].values()) + sum(b['mismatching_teams'].values()))
        macro('ModelOracleTeams', w['checked'].get('model_oracle', 0))
        macro('ConformanceChecks', len(w['checked']))
        r = d['reduction']
        macro('ReductionFormulas', r['formulas'])
        macro('ReductionSat', r['satisfiable'])
        macro('ReductionDisagreements', r['disagreements'])
        macro('ReductionRobustDisagreements', r.get('robust_disagreements', 0))
        macro('ReductionRobustNPDisagreements', r.get('robust_np_disagreements', 0))
        macro('ReductionReachDisagreements', r.get('reach_disagreements', 0))
        macro('FoolingAllHold', 'all' if all(all(v.values()) for v in d['fooling'].values()) else 'not all')
        macro('ManySwitchMismatches', d.get('many_switch_mismatches', 0))
        names = {'HN_equals_T': 'Exact semantics vs.\\ independent replay ($H_N=T$)',
                 'hybrid_vs_oracle': 'Hybrid semantics vs.\\ exhaustive replay (all slices $\\le 3$)',
                 'static_in_singletons': 'Lemma~\\ref{lem:face} at singletons ($F(\\emptyset)\\subseteq F(\\{v\\})$)',
                 'recovery': 'Static keys persist in every slice (Thm.~\\ref{thm:sep}c)',
                 'confirmed_vs_oracle': 'Confirmed findings vs.\\ run-enumeration oracle ($\\le 2$)',
                 'confirmed_sound': 'Confirmed findings are symptoms (Thm.~\\ref{thm:sound}b)',
                 'confirmed_monotone': 'Confirmed findings are monotone (Thm.~\\ref{thm:loc}c)',
                 'whole_exact': 'Whole slice is exact (Thm.~\\ref{thm:sound}a)',
                 'quotient': 'Partition summaries compose (Thm.~\\ref{thm:abs}d)',
                 'incremental': 'Incremental $=$ full re-verification, incl.\\ edges (Thm.~\\ref{thm:inc})',
                 'model_oracle': 'Run semantics vs.\\ all evidence models (Lemmas W, M)'}
        lines = []
        for k, label in names.items():
            lines.append(f"{label} & {w['checked'].get(k, 0):,} & {b['checked'].get(k, 0):,} & "
                         f"{w['mismatching_teams'].get(k, 0) + b['mismatching_teams'].get(k, 0)} \\\\".replace(',', '{,}'))
        write_table('conformance', '\n'.join(lines))
        macro('EOneSeconds', d['seconds'], '.0f')


# ------------------------------------------------------------------ E2 / E4
CHK = [('singleton', 'B1 agent (conf.)'), ('SL', 'SL (conf.)'), ('window2', 'window-2'), ('band1', 'band-1'),
       ('region', 'region'), ('goal', 'goal-dir.'), ('B2', 'B2 whole'), ('B3', 'B3 random'),
       ('B4', 'B4 lint'), ('B5', 'B5 smells'), ('B6', 'B6 must')]
CLS_ORDER = ['A1', 'A2', 'A3', 'S1v', 'A4', 'S5', 'S2', 'S3', 'S4', 'S6a', 'S6b']
DECOY = ['D2', 'D4', 'D5', 'D6']


def seed_rates(rows, checker, field, cond=lambda r: True, unit=lambda r: r['seed']):
    by = defaultdict(list)
    for r in rows:
        if checker in r['checkers'] and cond(r):
            v = r['checkers'][checker].get(field)
            if v is not None:
                by[unit(r)].append(bool(v))
    return {s: np.mean(v) for s, v in by.items()}


def cluster_ci(rows, value, n=4000):
    """Bootstrap CI of a mean, resampling clusters (topology, size, seed): the hosts that are
    reused across classes and checkers."""
    by = defaultdict(list)
    for r in rows:
        v = value(r)
        if v is not None:
            by[(r['topo'], r['n'], r['seed'])].append(float(v))
    keys = list(by)
    if not keys:
        return (math.nan, math.nan, math.nan)
    sums = np.array([sum(by[k]) for k in keys])
    cnts = np.array([len(by[k]) for k in keys])
    idx = RNG.integers(0, len(keys), (n, len(keys)))
    m = sums[idx].sum(axis=1) / cnts[idx].sum(axis=1)
    return (float(sums.sum() / cnts.sum()), float(np.quantile(m, 0.025)), float(np.quantile(m, 0.975)))


def cp_upper(k, n, alpha=0.05):
    """One-sided 95% Clopper-Pearson upper bound."""
    return 1.0 if k == n else float(stats.beta.ppf(1 - alpha, k + 1, n - k))


def e2():
    d = load('e2_detection')
    if not d:
        return
    rows = d['rows']
    small = [r for r in rows if not r['medium']]
    medium = [r for r in rows if r['medium']]
    macro('BenchSmall', len(small))
    macro('BenchMedium', len(medium))
    macro('BenchTotal', len(rows))
    macro('BenchGTok', sum(r['gt_ok'] for r in rows))
    macro('BenchNodesSmallMin', min(r['nodes'] for r in small))
    macro('BenchNodesSmallMax', max(r['nodes'] for r in small))
    macro('BenchNodesMediumMax', max(r['nodes'] for r in medium))
    macro('BenchNodesMediumMin', min(r['nodes'] for r in medium))
    macro('BenchKSix', sum(1 for r in small if r.get('K') == 6))
    defect = [r for r in rows if r['cls'] in CLS_ORDER]
    hidden = [r for r in rows if r['cls'] in HIDDEN]
    # recall table: primary key (and the pre-registered any-GT-key definition in macros)
    lines = []
    for cls in CLS_ORDER:
        rs = [r for r in rows if r['cls'] == cls]
        cells = []
        for c, _ in CHK:
            v = [r['checkers'][c]['primary_detected'] for r in rs if c in r['checkers']]
            cells.append(pct(np.mean(v)) if v else '--')
        dep = [r['depth'] for r in small if r['cls'] == cls and r.get('depth')]
        dd = f"{min(dep)}--{max(dep)}" if dep and min(dep) != max(dep) else (str(dep[0]) if dep else '--')
        lines.append(f"{cls} & {dd} & " + ' & '.join(cells) + ' \\\\')
    write_table('recall', '\n'.join(lines))
    for c in ['singleton', 'SL', 'B2', 'B3', 'B4', 'B5', 'B6', 'goal', 'region', 'window2', 'band1', 'B1raw', 'SLraw']:
        hid = [r['checkers'][c]['primary_detected'] for r in hidden if c in r['checkers']]
        macro(f'RecallHidden{c}', np.mean(hid), 'pct')
        macro(f'RecallHiddenN{c}', int(sum(hid)))
        allc = [r['checkers'][c]['primary_detected'] for r in defect if c in r['checkers']]
        macro(f'RecallAll{c}', np.mean(allc), 'pct')
        anyk = [r['checkers'][c]['detected'] for r in hidden if c in r['checkers']]
        macro(f'RecallPlanHidden{c}', np.mean(anyk), 'pct')
        s6b = [r['checkers'][c]['detected'] for r in rows if r['cls'] == 'S6b' and c in r['checkers']]
        macro(f'RecallPlanSSixb{c}', np.mean(s6b), 'pct')
    macro('HiddenTeams', len(hidden))
    macro('HiddenDesignShare', len([c for c in CLS_ORDER if c in HIDDEN]) / len(CLS_ORDER), 'pct')
    # localization (small benchmark, hidden classes, detected)
    loc_rows = [('SL', 'SL (combined)'), ('goal', 'goal-directed'), ('region', 'region'), ('window2', 'window-2'),
                ('B3', 'B3 random slices'), ('B2', 'B2 witness lineage hull'), ('B2dev', 'B2 witness deviation set'),
                ('B2shrink', 'B2 + slice shrinking')]
    loc_lines, exact_seed = [], {}
    for c, label in loc_rows:
        rs = [r for r in small if r['cls'] in HIDDEN and c in r['checkers'] and r['checkers'][c].get('primary_detected')]
        if not rs:
            continue
        m, lo, hi = cluster_ci(rs, lambda r: bool(r['checkers'][c].get('exact')))
        mn = np.mean([bool(r['checkers'][c].get('minimum')) for r in rs])
        pr = np.mean([bool(r['checkers'][c].get('precise')) for r in rs])
        hit = np.mean([bool(r['checkers'][c].get('hit')) for r in rs])
        ts = np.mean([r['checkers'][c]['top_size'] for r in rs])
        sr = np.mean([r['checkers'][c]['size_ratio'] for r in rs])
        cost = np.mean([r['checkers'][c]['slices'] for r in rs])
        loc_lines.append(f"{label} & {len(rs)} & {pct(m)} [{pct(lo)}, {pct(hi)}] & {pct(mn)} & {pct(pr)} & {pct(hit)} & "
                         f"{ts:.1f} & {sr:.2f} & {cost:.0f} \\\\")
        exact_seed[c] = seed_rates([r for r in small if r['cls'] in HIDDEN], c, 'exact',
                                   lambda r, c=c: r['checkers'].get(c, {}).get('primary_detected'),
                                   unit=lambda r: (r['topo'], r['seed']))
        macro(f'LocExact{c}', m, 'pct')
        macro(f'LocExactLo{c}', lo, 'pct')
        macro(f'LocExactHi{c}', hi, 'pct')
        macro(f'LocMinimum{c}', mn, 'pct')
        macro(f'LocPrecise{c}', pr, 'pct')
        macro(f'LocRatio{c}', sr, '.2f')
        macro(f'LocSize{c}', ts, '.1f')
        macro(f'LocCost{c}', cost, '.0f')
    write_table('localization', '\n'.join(loc_lines))
    # H2.2: SL vs B3, B2dev, B2 (exact localization; unit = topology x seed; Holm over the three)
    comps = [o for o in ['B3', 'B2dev', 'B2'] if o in exact_seed]
    ps, effs = [], []
    for other in comps:
        units = sorted(set(exact_seed['SL']) & set(exact_seed[other]))
        x = [exact_seed['SL'][u] for u in units]
        y = [exact_seed[other][u] for u in units]
        ps.append(wilcoxon_greater(x, y))
        effs.append(a12(x, y))
        macro(f'HTwoTwoN{other}', len(units))
    for other, pa, e in zip(comps, holm(np.array(ps)), effs):
        macro(f'HTwoTwoP{other}', pa, 'p')
        macro(f'HTwoTwoA{other}', e, '.2f')
    # shrinking vs SL (two-sided information: is shrinking better?)
    if 'B2shrink' in exact_seed:
        units = sorted(set(exact_seed['SL']) & set(exact_seed['B2shrink']))
        x = [exact_seed['B2shrink'][u] for u in units]
        y = [exact_seed['SL'][u] for u in units]
        macro('ShrinkVsSLP', wilcoxon_greater(x, y), 'p')
        macro('ShrinkVsSLA', a12(x, y), '.2f')
    # per-class localization (exact %, small benchmark)
    pc = []
    for cls in HIDDEN:
        cells = []
        for c in ['SL', 'B3', 'B2dev', 'B2shrink']:
            rs = [r for r in small if r['cls'] == cls and r['checkers'].get(c, {}).get('primary_detected')]
            cells.append(pct(np.mean([bool(r['checkers'][c].get('exact')) for r in rs])) if rs else '--')
            if c == 'SL' and rs:
                macro(f'LocExactSL{cls}', np.mean([bool(r['checkers'][c].get('exact')) for r in rs]), 'pct')
        pc.append(f"{cls} & " + ' & '.join(cells) + ' \\\\')
    write_table('loc_class', '\n'.join(pc))
    # medium localization
    for c in ['SL', 'B2', 'B2dev', 'B2shrink', 'B3', 'goal']:
        rs = [r for r in medium if r['cls'] in HIDDEN and r['checkers'].get(c, {}).get('primary_detected')]
        if rs:
            macro(f'MedPrecise{c}', np.mean([bool(r['checkers'][c].get('precise')) for r in rs]), 'pct')
            macro(f'MedRatio{c}', np.mean([r['checkers'][c]['size_ratio'] for r in rs]), '.3f')
            macro(f'MedSize{c}', np.mean([r['checkers'][c]['top_size'] for r in rs]), '.1f')
    sc = [r['checkers']['B2shrink']['checks'] for r in rows if r['checkers'].get('B2shrink', {}).get('primary_detected')
          and r['cls'] in HIDDEN]
    if sc:
        macro('ShrinkChecks', np.mean(sc), '.0f')
    # false alarms on clean + decoys: counts and Clopper-Pearson upper bounds
    fa_lines = []
    for c, label in CHK + [('B1raw', 'B1 agent (raw)'), ('SLraw', 'SL (raw)')]:
        cells = []
        for grp, cls in [('clean', ['clean']), ('decoy', DECOY)]:
            v = [bool(r['checkers'][c]['alarm']) for r in rows if r['cls'] in cls and c in r['checkers']]
            if v:
                k = int(sum(v))
                macro(f'Alarm{grp}{c}', np.mean(v), 'pct')
                macro(f'AlarmHi{grp}{c}', cp_upper(k, len(v)), 'pct')
                cells.append(f"{k}/{len(v)} ({pct(np.mean(v))})")
            else:
                cells.append('--')
        fa_lines.append(f"{label} & " + ' & '.join(cells) + ' \\\\')
    write_table('alarms', '\n'.join(fa_lines))
    macro('CleanTeams', sum(r['cls'] == 'clean' for r in rows))
    macro('DecoyTeams', sum(r['cls'] in DECOY for r in rows))
    for c in ['SL', 'SLraw', 'B6', 'B5', 'B1raw', 'singleton']:
        fk = sum(r['checkers'][c]['false_keys'] for r in rows if c in r['checkers'])
        tk = sum(r['checkers'][c]['reported'] for r in rows if c in r['checkers'])
        macro(f'FalseKeys{c}', fk)
        macro(f'ReportedKeys{c}', tk)
        macro(f'Precision{c}', 1 - fk / max(1, tk), 'pct')
    lifts = [r['checkers']['SL']['lifts'] for r in rows]
    macro('SLLifts', np.mean(lifts), '.1f')
    macro('SLUnconfirmed', sum(r['checkers']['SL']['unconfirmed'] for r in rows))
    # per-topology recall on hidden classes
    topo_lines = []
    for topo in ['chain', 'tree', 'forkjoin', 'layered', 'sp', 'random', 'mixed']:
        rs = [r for r in hidden if r['topo'] == topo]
        cells = [pct(np.mean([r['checkers'][c]['primary_detected'] for r in rs if c in r['checkers']]))
                 for c in ['singleton', 'SL', 'region', 'goal', 'B3', 'B5', 'B6']]
        sr = [r['checkers']['SL']['size_ratio'] for r in rs if r['checkers']['SL'].get('primary_detected')]
        topo_lines.append(f"{topo} & {len(rs)} & " + ' & '.join(cells) + f" & {np.mean(sr):.2f} \\\\")
    write_table('topology', '\n'.join(topo_lines))
    # E4 (within the benchmark): recall by k
    ks = list(range(1, 6))
    sweep_lines = []
    for cls in HIDDEN:
        means = [np.mean([r['checkers'][f'k{k}']['primary_detected'] for r in small if r['cls'] == cls]) for k in ks]
        sweep_lines.append(f"{cls} & " + ' & '.join(pct(m) for m in means) + ' \\\\')
    allk = [np.mean([r['checkers'][f'k{k}']['primary_detected'] for r in small if r['cls'] in CLS_ORDER]) for k in ks]
    sweep_lines.append('all classes & ' + ' & '.join(pct(a) for a in allk) + ' \\\\')
    write_table('k_sweep', '\n'.join(sweep_lines))
    for k, a in zip(ks, allk):
        macro(f'RecallK{k}', a, 'pct')
        alarms = [bool(r['checkers'][f'k{k}']['alarm']) for r in small if r['cls'] in ['clean'] + DECOY]
        macro(f'AlarmK{k}', np.mean(alarms), 'pct')
        macro(f'SlicesK{k}', np.mean([r['checkers'][f'k{k}']['slices'] for r in small]), '.0f')
    # depth histogram per class
    dep_lines = []
    for cls in CLS_ORDER:
        dep = [r['depth'] for r in small if r['cls'] == cls]
        cnt = [sum(1 for x in dep if x == k) for k in range(1, 7)] + [sum(1 for x in dep if x is None)]
        dep_lines.append(f"{cls} & " + ' & '.join(str(c) for c in cnt) + ' \\\\')
    write_table('depth', '\n'.join(dep_lines))


# ------------------------------------------------------------------ E4b: hand-off distance sweep
def e4b():
    d = load('e4_depth_sweep')
    if not d:
        return
    allrows = d['rows']
    rows = [r for r in allrows if r.get('host', 5) == 5]
    big = [r for r in allrows if r.get('host', 5) != 5]
    K = d['kmax']
    ks = list(range(1, K + 1))
    chainy = [r for r in rows if r['cls'] in ('S4', 'S6a', 'S6b')]
    if big:
        macro('DepthSweepBigTeams', len(big))
        macro('DepthSweepBigNodesMax', max(r['nodes'] for r in big))
        macro('DepthSweepBigNodesMin', min(r['nodes'] for r in big))
        macro('DepthBigIsEllPlusTwo', np.mean([r['depth'] == r['ell'] + 2 for r in big if r['cls'] in ('S4', 'S6a', 'S6b')]), 'pct')
        macro('DepthBigTwoForJoins', np.mean([r['depth'] == 2 for r in big if r['cls'] in ('S2', 'S3')]), 'pct')
    macro('DepthSweepTeams', len(allrows))
    macro('DepthSweepSmallTeams', len(rows))
    macro('DepthSweepKmax', K)
    macro('DepthIsEllPlusTwo', np.mean([r['depth'] == r['ell'] + 2 for r in chainy]), 'pct')
    macro('DepthTwoForJoins', np.mean([r['depth'] == 2 for r in rows if r['cls'] in ('S2', 'S3')]), 'pct')
    series = []
    for i, ell in enumerate(range(6)):
        rs = [r for r in chainy if r['ell'] == ell]
        ys = [np.mean([r['detected_by_k'][str(k)] for r in rs]) for k in ks]
        series.append(pgf_series(i, ks, ys, legend=f'$\\ell={ell}$'))
    rs = [r for r in rows if r['cls'] in ('S2', 'S3')]
    series.append(pgf_series(6, ks, [np.mean([r['detected_by_k'][str(k)] for r in rs]) for k in ks],
                             legend='S2, S3 (any $\\ell$)', color='black', width='very thick'))
    FIGS['figDepthSweep'] = ('\\begin{tikzpicture}\\begin{axis}[width=\\columnwidth,height=5.2cm,xlabel={maximum slice size $k$},'
                             f'ylabel={{recall (confirmed)}},xtick={{{",".join(map(str, ks))}}},ymin=-0.03,ymax=1.05,grid=major,'
                             'grid style={gray!20},legend columns=4,legend style={at={(0.5,-0.32)},anchor=north,font=\\scriptsize,draw=none,fill=none},'
                             'tick label style={font=\\footnotesize},label style={font=\\footnotesize}]\n'
                             + '\n'.join(series) + '\n\\end{axis}\\end{tikzpicture}')
    lines = []
    for cls in ['S2', 'S3', 'S4', 'S6a', 'S6b']:
        cells = []
        for ell in range(6):
            dep = [r['depth'] for r in rows if r['cls'] == cls and r['ell'] == ell]
            cells.append(f"{np.mean([x for x in dep if x]):.1f}" if any(dep) else '--')
        lines.append(f"{cls} & " + ' & '.join(cells) + ' \\\\')
    write_table('depth_sweep', '\n'.join(lines))
    slices = {k: np.mean([r['slices_by_k'][str(k)] for r in rows]) for k in ks}
    macro('DepthSweepSlicesKTwo', slices[2], '.0f')
    macro('DepthSweepSlicesKMax', slices[K], '.0f')



# ------------------------------------------------------------------ teaser figure (E8)
def teaser():
    """Two-panel opening figure from every E8 team, styled like the scalability figure: against team size,
    (a) share of defect symptoms found and (b) share of hidden symptoms localized to exactly a minimal
    confirming slice, one line per method with a 95% cluster-bootstrap band and one shared legend.
    """
    d8 = load('e8_mutation')
    if not d8:
        return
    unclean = [r for r in d8['rows'] if not r.get('skipped') and r.get('symptoms')]
    keys = [(r, k, dd) for r in unclean for k, dd in r['depth'].items()]
    sizes = sorted({r['nodes'] for r in unclean})
    hidden = lambda dd: dd is None or dd >= 2
    rng = np.random.default_rng(20261104)   # local stream: do not perturb the shared RNG used by later stages

    def ci(items, value):
        """Mean of value over items, with a 95% bootstrap CI resampling host teams (topology, size, seed)."""
        by = defaultdict(lambda: [0.0, 0])
        for r, k, dd in items:
            v = value(r, k, dd)
            if v is not None:
                c = by[(r['topo'], r['n'], r['seed'])]
                c[0] += float(v)
                c[1] += 1
        if not by:
            return (math.nan, math.nan, math.nan)
        s = np.array([v[0] for v in by.values()])
        c = np.array([v[1] for v in by.values()])
        idx = rng.integers(0, len(s), (4000, len(s)))
        m = s[idx].sum(axis=1) / c[idx].sum(axis=1)
        return tuple(100 * x for x in (s.sum() / c.sum(), np.quantile(m, 0.025), np.quantile(m, 0.975)))

    found = lambda c: (lambda r, k, dd: r['checkers'][c]['per_key'][k]['found'])
    def sl_exact(r, k, dd):
        p = r['checkers']['SL']['per_key'][k]
        return p.get('exact') if p['found'] else None
    shrink = lambda f: (lambda r, k, dd: r['shrink'][k][f] if k in r.get('shrink', {}) else None)
    # method -> (legend, style); the same style marks the same method in both panels
    M = {
        'SL':     ('Agent slicing (confirmed)', 'cA,thick,solid,mark=*'),
        'shrink': ('Agent slicing + shrinking', 'cA!50!black,thick,densely dashed,mark=diamond*'),
        'k2':     ('Slices of $\\le$2 agents only', 'cC,semithick,dashdotted,mark=triangle*'),
        'B1':     ('Agent-level check', 'cB,semithick,dashed,mark=square*'),
        'B6':     ('Global must-analysis', 'cG,thick,densely dotted,mark=x,mark size=3pt'),
        'dev':    ('Deviating agents of a witness', 'cE,semithick,solid,mark=pentagon*'),
        'B5':     ('Smell catalogue', 'cD,semithick,dotted,mark=diamond*'),
        'B4':     ('Structural lint', 'gray,semithick,dashed,mark=o'),
    }
    detect = {'SL': found('SL'), 'k2': lambda r, k, dd: dd is not None and dd <= 2, 'B1': found('B1'),
              'B5': found('B5'), 'B4': found('B4'), 'B6': found('B6')}   # B6 last: drawn on top of SL at ~100%
    localize = {'shrink': shrink('shrink_exact'), 'SL': sl_exact, 'dev': shrink('dev_exact'),
                'B6': lambda r, k, dd: 0.0 if r['checkers']['B6']['per_key'][k]['found'] else None}  # reports one node; a hidden symptom's minimal slice has >= 2

    def panel(metrics, only_hidden):
        out = []
        for key, fn in metrics.items():
            col = M[key][1].split(',')[0]
            stats_ = [ci([(r, k, dd) for r, k, dd in keys if r['nodes'] == s and (hidden(dd) or not only_hidden)], fn) for s in sizes]
            mean, lo, hi = zip(*stats_)
            out.append(f'\\addplot[fill={col},fill opacity=0.15,draw=none,forget plot] coordinates '
                       f'{{{coords(list(sizes) + sizes[::-1], list(lo) + list(hi)[::-1])}}} -- cycle;')
            out.append(f'\\addplot[mark size=1.6pt,{M[key][1]},mark options={{solid}},forget plot] coordinates {{{coords(sizes, mean)}}};')
        return out

    pooled = lambda fn, only_hidden=False: ci([(r, k, dd) for r, k, dd in keys if hidden(dd) or not only_hidden], fn)[0] / 100
    macro('TeaserKeys', len(keys))
    macro('TeaserTeams', len(unclean))
    macro('TeaserSizeMin', sizes[0])
    macro('TeaserSizeMax', sizes[-1])
    macro('TeaserAgentShare', pooled(found('B1')), 'pct')
    macro('TeaserSliceShareTwo', pooled(detect['k2']), 'pct')
    macro('TeaserSlicingShare', pooled(found('SL')), 'pct')
    macro('TeaserLintShare', pooled(found('B4')), 'pct')
    macro('TeaserSmellShare', pooled(found('B5')), 'pct')

    legend = [f'\\addlegendimage{{mark size=1.6pt,{M[k][1]},mark options={{solid}}}}\\addlegendentry{{{M[k][0]}}}' for k in M]
    ax = ('width=0.37\\textwidth,height=5.2cm,xmode=log,log basis x=2,'
          f'xtick={{{",".join(map(str, sizes))}}},xticklabels={{{",".join(map(str, sizes))}}},'
          f'xmin={sizes[0] * 0.88:.2f},xmax={sizes[-1] * 1.12:.2f},ymin=-4,ymax=104,ytick={{0,25,50,75,100}},'
          'xlabel={team size (nodes)},grid=major,grid style={gray!20},tick label style={font=\\footnotesize},'
          'label style={font=\\footnotesize},title style={font=\\footnotesize}')
    FIGS['figTeaser'] = (
        '\\begin{tikzpicture}\n'
        f'\\begin{{axis}}[{ax},title={{(a) defect symptoms found}},ylabel={{share of symptoms (\\%)}},name=left]\n'
        + '\n'.join(panel(detect, False)) + '\n\\end{axis}\n'
        f'\\begin{{axis}}[{ax},title={{(b) hidden symptoms localized exactly}},at={{(left.east)}},anchor=west,xshift=1.2cm,'
        'legend pos=outer north east,legend cell align=left,legend style={font=\\scriptsize,draw=none,fill=none}]\n'
        + '\n'.join(legend) + '\n' + '\n'.join(panel(localize, True)) + '\n\\end{axis}\n\\end{tikzpicture}')

# ------------------------------------------------------------------ E8: mutation benchmark
def e8():
    d = load('e8_mutation')
    if not d:
        return
    rows = [r for r in d['rows'] if not r.get('skipped')]
    macro('MutTeams', len(d['rows']))
    macro('MutSkipped', len(d['rows']) - len(rows))
    macro('MutMutations', sum(len(r['ops']) for r in rows))
    unsafe = [r for r in rows if r.get('unsafe')]
    unclean = [r for r in rows if r.get('symptoms')]
    macro('MutUnclean', len(unclean))
    macro('MutUnsafe', len(unsafe))
    orc = [r['oracle_agrees'] for r in rows if 'oracle_agrees' in r]
    macro('MutOracleTeams', len(orc))
    macro('MutOracleDisagree', sum(1 for x in orc if not x))
    keys = [(r, k, dd) for r in unclean for k, dd in r['depth'].items()]
    macro('MutKeys', len(keys))
    hist = defaultdict(int)
    for _, _, dd in keys:
        hist[dd if dd is not None else 'deep'] += 1
    for k in range(1, 7):
        macro(f'MutDepth{k}', hist.get(k, 0))
    macro('MutDepthDeep', hist.get('deep', 0))
    hid = [(r, k) for r, k, dd in keys if dd is None or dd >= 2]
    macro('MutHiddenKeys', len(hid))
    macro('MutHiddenShare', len(hid) / max(1, len(keys)), 'pct')
    only_hidden = [r for r in unclean if all((dd is None or dd >= 2) for dd in r['depth'].values())]
    macro('MutTeamsHiddenOnly', len(only_hidden))
    macro('MutTeamsWithHidden', sum(1 for r in unclean if any(dd is None or dd >= 2 for dd in r['depth'].values())))
    lines = []
    names = [('B1', 'B1 agent (conf.)'), ('B1raw', 'B1 agent (raw)'), ('SL', 'SL (conf.)'), ('SLraw', 'SL (raw)'),
             ('B6', 'B6 must'), ('B5', 'B5 smells'), ('B4', 'B4 lint')]
    for c, label in names:
        allk = [r['checkers'][c]['per_key'][k]['found'] for r, k, _ in keys]
        hk = [r['checkers'][c]['per_key'][k]['found'] for r, k in hid]
        fk = sum(r['checkers'][c]['false_keys'] for r in unclean)
        rep = sum(r['checkers'][c]['reported'] for r in unclean)
        ex = [r['checkers'][c]['per_key'][k].get('exact') for r, k in hid if r['checkers'][c]['per_key'][k]['found']]
        ex = [e for e in ex if e is not None]
        lines.append(f"{label} & {pct(np.mean(allk))} & {pct(np.mean(hk)) if hk else '--'} & {fk}/{rep} & "
                     f"{pct(np.mean(ex)) if ex else '--'} \\\\")
        macro(f'MutRecall{c}', np.mean(allk), 'pct')
        if hk:
            macro(f'MutRecallHidden{c}', np.mean(hk), 'pct')
        macro(f'MutFalse{c}', fk)
        macro(f'MutReported{c}', rep)
        macro(f'MutFalseRate{c}', fk / max(1, rep), 'pct')
        if ex:
            macro(f'MutExact{c}', np.mean(ex), 'pct')
    shr = [v for r in unclean for v in r.get('shrink', {}).values()]
    if shr:
        lines.append(f"B2 + slice shrinking & 100.0 & 100.0 & -- & {pct(np.mean([s['shrink_exact'] for s in shr]))} \\\\")
        lines.append(f"B2 deviation set & 100.0 & 100.0 & -- & {pct(np.mean([s['dev_exact'] for s in shr]))} \\\\")
        macro('MutShrinkExact', np.mean([s['shrink_exact'] for s in shr]), 'pct')
        macro('MutShrinkMinimum', np.mean([s['shrink_minimum'] for s in shr]), 'pct')
        macro('MutShrinkChecks', np.mean([s['shrink_checks'] for s in shr]), '.0f')
        macro('MutDevExact', np.mean([s['dev_exact'] for s in shr]), 'pct')
        macro('MutDevRatio', np.mean([s['dev_precise_size_ratio'] for s in shr]), '.2f')
    write_table('mutation', '\n'.join(lines))
    # pipeline: B6 detects, the exact semantics confirms, shrinking localizes
    pipe = [(r, k) for r, k in hid if r['checkers']['B6']['per_key'][k]['found'] and k in r.get('shrink', {})]
    if pipe:
        macro('MutPipeRecallHidden', len(pipe) / max(1, len(hid)), 'pct')
        macro('MutPipeExact', np.mean([r['shrink'][k]['shrink_exact'] for r, k in pipe]), 'pct')
    # teams that confirmed agent-level analysis would declare clean / safe
    al_clean = [r for r in unclean if not any(v['found'] for v in r['checkers']['B1']['per_key'].values())]
    macro('MutALDeclaredClean', len(al_clean))
    macro('MutALDeclaredCleanUnsafe', sum(1 for r in al_clean if r.get('unsafe')))
    macro('MutDeepKeys', sum(1 for _, _, dd in keys if dd is None))
    macro('MutTeamsFewerOps', sum(1 for r in rows if len(r['ops']) < r['m']))
    # by team size
    size_lines = []
    for n in sorted({r['n'] for r in rows}):
        rs = [r for r in unclean if r['n'] == n]
        kk = [(r, k, dd) for r in rs for k, dd in r['depth'].items()]
        hk = [(r, k) for r, k, dd in kk if dd is None or dd >= 2]
        node_rng = f"{min(r['nodes'] for r in rs)}--{max(r['nodes'] for r in rs)}" if rs else '--'
        ex_rows = [{'topo': r['topo'], 'n': r['n'], 'seed': r['seed'], 'v': r['checkers']['SL']['per_key'][k].get('exact')}
                   for r, k in hk if r['checkers']['SL']['per_key'][k]['found'] and r['checkers']['SL']['per_key'][k].get('exact') is not None]
        m_, lo_, hi_ = cluster_ci(ex_rows, lambda x: x['v'])
        sh = [r['shrink'][k]['shrink_exact'] for r, k in hk if k in r.get('shrink', {})]
        b6f = sum(r['checkers']['B6']['false_keys'] for r in rs)
        b6r = sum(r['checkers']['B6']['reported'] for r in rs)
        size_lines.append(f"{n} & {node_rng} & {len(rs)} & {len(kk)} & {pct(len(hk) / max(1, len(kk)))} & "
                          f"{pct(np.mean([r['checkers']['B1']['per_key'][k]['found'] for r, k in hk])) if hk else '--'} & "
                          f"{pct(m_) if not math.isnan(m_) else '--'} [{pct(lo_) if not math.isnan(lo_) else '--'}, {pct(hi_) if not math.isnan(hi_) else '--'}] & "
                          f"{pct(np.mean(sh)) if sh else '--'} & {pct(b6f / max(1, b6r))} \\\\")
        macro(f'MutHiddenShareN{n}', len(hk) / max(1, len(kk)), 'pct')
        macro(f'MutB6FalseRateN{n}', b6f / max(1, b6r), 'pct')
        if not math.isnan(m_):
            macro(f'MutExactSLN{n}', m_, 'pct')
        if sh:
            macro(f'MutShrinkExactN{n}', np.mean(sh), 'pct')
    write_table('mutation_size', '\n'.join(size_lines))
    # timing (seconds per team): medians
    for c in ['B1', 'SL', 'SLraw', 'B6', 'B2']:
        v = [r['times'][c] for r in unclean if 'times' in r]
        if v:
            macro(f'MutTime{c}', float(np.median(v)) * 1000, '.1f')
    sv = [x for r in unclean for x in r.get('shrink_seconds', [])]
    if sv:
        macro('MutTimeShrink', float(np.median(sv)) * 1000, '.1f')
    ops = defaultdict(int)
    for r in rows:
        for o in r['ops']:
            ops[o] += 1
    write_table('mutation_ops', ', '.join(f"{o.replace('_', ' ')} ({n})" for o, n in sorted(ops.items())))
    # which mutation operators produce hidden keys: over all teams containing the operator, and over
    # teams whose only change is that operator (cleaner attribution, since the others overlap)
    def hidden(dd):
        return dd is None or dd >= 2

    opl = []
    for o in sorted(ops):
        name = ''.join(w.capitalize() for w in o.split('_'))
        applied = [r for r in rows if o in r['ops']]
        rs = [r for r in applied if r.get('symptoms')]
        kk = [dd for r in rs for dd in r['depth'].values()]
        silent = [r for r in rs if not any(v['found'] for v in r['checkers']['B1']['per_key'].values())]
        single = [r for r in applied if len(r['ops']) == 1]
        srs = [r for r in single if r.get('symptoms')]
        skk = [dd for r in srs for dd in r['depth'].values()]
        hs = pct(np.mean([hidden(x) for x in kk])) if kk else '--'
        shs = pct(np.mean([hidden(x) for x in skk])) if skk else '--'
        opl.append(f"{o.replace('_', ' ')} & {len(applied)} & {len(rs)} ({pct(len(rs) / max(1, len(applied)))}) & {len(kk)} & "
                   f"{hs} & {len(silent)} & {len(single)} & {len(srs)} ({pct(len(srs) / max(1, len(single)))}) & {shs} \\\\")
        macro(f'MutOp{name}Teams', len(applied))
        macro(f'MutOp{name}Unclean', len(rs))
        macro(f'MutOp{name}UncleanShare', len(rs) / max(1, len(applied)), 'pct')
        macro(f'MutOp{name}Hidden', np.mean([hidden(x) for x in kk]) if kk else 0, 'pct')
        macro(f'MutOp{name}ALSilent', len(silent))
        macro(f'MutOp{name}SingleTeams', len(single))
        macro(f'MutOp{name}SingleUnclean', len(srs))
        if skk:
            macro(f'MutOp{name}SingleHidden', np.mean([hidden(x) for x in skk]), 'pct')
    macro('MutSingleChangeTeams', sum(1 for r in rows if len(r['ops']) == 1))
    write_table('mutation_by_op', '\n'.join(opl))
    depth_by_op(rows, sorted(ops))


def depth_by_op(rows, ops):
    """Figure: depth distribution of the symptom keys per change operator, (a) in teams whose only change
    is that operator and (b) in teams that combine it with one or two other changes. 100% stacked bars;
    depth 1 (visible at agent level) in neutral gray, hidden depths on a light-to-dark blue ramp."""
    bins = [('1', lambda d: d == 1), ('2', lambda d: d == 2), ('3', lambda d: d == 3),
            ('$\\ge$4', lambda d: d is None or d >= 4)]   # None: deeper than the enumeration bound
    fills = ['black!18', 'cA!35', 'cA!70', 'cA!60!black']

    def dist(rs):
        dd = [d for r in rs if r.get('symptoms') for d in r['depth'].values()]
        return len(dd), [100 * sum(map(f, dd)) / len(dd) if dd else 0 for _, f in bins]

    single = {o: dist([r for r in rows if r['ops'] == [o]]) for o in ops}
    combo = {o: dist([r for r in rows if o in r['ops'] and len(r['ops']) > 1]) for o in ops}
    hid = lambda v: sum(v[1][1:])
    # operators ordered by the hidden share of their combined teams, most dangerous on top
    order = sorted(ops, key=lambda o: hid(combo[o]))
    for o in ops:
        name = ''.join(w.capitalize() for w in o.split('_'))
        macro(f'MutOp{name}ComboHidden', hid(combo[o]) / 100, 'pct')
        macro(f'MutOp{name}ComboKeys', combo[o][0])
    macro('MutComboTeams', sum(1 for r in rows if len(r['ops']) > 1))
    ys = ','.join(map(str, range(len(order))))
    labels = ','.join(o.replace('_', ' ') for o in order)

    def panel(data, title, extra, legend=False):
        out = [f'\\begin{{axis}}[xbar stacked,bar width=7pt,width=0.40\\textwidth,height=5.4cm,xmin=0,xmax=100,'
               f'ytick={{{ys}}},ymin=-0.6,ymax={len(order) - 0.4},xtick={{0,25,50,75,100}},'
               'xlabel={share of symptom keys (\\%)},axis y line*=left,axis x line*=bottom,'
               'xmajorgrids,grid style={gray!20},y axis line style={draw=none},ytick style={draw=none},'
               'tick label style={font=\\footnotesize},label style={font=\\footnotesize},'
               f'title style={{font=\\footnotesize}},title={{{title}}},clip=false,{extra}]']
        for j, (lab, _) in enumerate(bins):
            pts = ' '.join(f'({data[o][1][j]:.4g},{i})' for i, o in enumerate(order))
            out.append(f'\\addplot[fill={fills[j]},draw=white,line width=0.5pt] coordinates {{{pts}}};')
            if legend:
                out.append(f'\\addlegendentry{{depth {lab}}}')
        for i, o in enumerate(order):
            n = data[o][0]
            txt = f'$n={n:,}$'.replace(',', '{,}') if n else 'no symptom'
            out.append(f'\\node[font=\\scriptsize,text=black!60,anchor=west] at (axis cs:{100 if n else 0},{i}) {{\\,{txt}}};')
        out.append('\\end{axis}')
        return out

    legend = ('area legend,legend columns=4,legend style={at={(-0.3,-0.25)},anchor=north,font=\\scriptsize,'
              'draw=none,fill=none,/tikz/every even column/.append style={column sep=6pt}},legend cell align=left')
    left = panel(single, '(a) the only change', f'yticklabels={{{labels}}},name=left')
    right = panel(combo, '(b) combined with other changes',
                  'yticklabels={},at={(left.east)},anchor=west,xshift=1.6cm,' + legend, legend=True)
    FIGS['figDepthByOp'] = '\\begin{tikzpicture}\n' + '\n'.join(left + right) + '\n\\end{tikzpicture}'


# ------------------------------------------------------------------ E3
def e3():
    d = load('e3_architectures')
    if not d:
        return
    rows = d['rows']
    lines = []
    designs = list(dict.fromkeys(r['design'] for r in rows))
    macro('ArchDesigns', len(designs))
    macro('ArchVariants', len(rows))
    doc = [r for r in rows if r['variant'] == 'documented']
    macro('ArchUnsafeDocumented', sum(not r['safe'] for r in doc))
    macro('ArchHiddenDocumented', sum(any(not s['agent_level'] for s in r['symptoms']) for r in doc))
    macro('ArchHiddenSmell', sum(any(not s['agent_level'] and s.get('smell') for s in r['symptoms']) for r in doc))
    macro('ArchHiddenMust', sum(any(not s['agent_level'] and s.get('must') for s in r['symptoms']) for r in doc))
    macro('ArchSafeFZero', sum(1 for r in rows if r['variant'] == 'f0' and r['safe']))
    for r in doc:
        if r['symptoms']:
            s = min(r['symptoms'], key=lambda s: (s['agent_level'], s['depth'] or 99))
            sl_ = ', '.join(s['minimal'][0]) if s['minimal'] else '--'
            key = f"{s['key'][0]}: \\textsf{{{s['key'][2].replace('_', '\\_')}}}"
            lines.append(f"\\cite{{{r['source']}}} {r['design']} & {r['nodes']} & {key} & {s['class']} & {s['depth']} & "
                         f"{{\\footnotesize {sl_}}} & {'yes' if s['agent_level'] else 'no'} & {'yes' if s.get('smell') else 'no'} & "
                         f"{'yes' if s.get('must') else 'no'} \\\\")
        else:
            lines.append(f"\\cite{{{r['source']}}} {r['design']} & {r['nodes']} & none & -- & -- & -- & -- & -- & -- \\\\")
    write_table('architectures', '\n'.join(lines))
    sens = []
    for dsg in designs:
        cells = []
        for v in ['documented', 'shared', 'distinct', 'f0', 'alt_join']:
            rr = [r for r in rows if r['design'] == dsg and r['variant'] == v]
            if not rr:
                cells.append('--')
                continue
            r = rr[0]
            if r['safe'] and r['clean']:
                cells.append('safe')
            else:
                cl = sorted({s['class'] for s in r['symptoms']})
                cells.append('/'.join(cl))
        sens.append(f"{dsg} & " + ' & '.join(cells) + ' \\\\')
    write_table('arch_sensitivity', '\n'.join(sens))


# ------------------------------------------------------------------ E5
def e5():
    d = load('e5_scalability')
    if not d:
        return
    rows = d['rows']
    B = d['budget']
    strats = ['singleton', 'window2', 'band1', 'region', 'goal', 'SL', 'must', 'whole']
    labels = {'singleton': 'singleton (B1)', 'window2': 'window-2', 'band1': 'band-1', 'region': 'region',
              'goal': 'goal-directed', 'SL': 'SL (combined)', 'must': 'B6 must', 'whole': 'B2 whole team'}
    sizes = sorted({r['n'] for r in rows})
    macro('ScaleMaxNodes', max(r['nodes'] for r in rows))
    macro('ScaleTeams', len(rows))
    macro('ScaleBudget', B, '.0f')

    def res(r, s):
        return r[s] if s in ('whole', 'must') else r['strategies'][s]

    def secs(x):
        return B if x['timeout'] else x['seconds']             # censored at the budget
    pgf_panels, slope_lines = [], []
    for ai, topo_set in enumerate([['layered', 'sp', 'random'], ['mixed']]):
        pgf_lines = []
        for i, s in enumerate(strats):
            xs, med, lo, hi = [], [], [], []
            for n in sizes:
                rs = [r for r in rows if r['n'] == n and r['topo'] in topo_set]
                v = [secs(res(r, s)) for r in rs]
                xs.append(np.mean([r['nodes'] for r in rs]))
                med.append(max(np.median(v), 1e-5)); lo.append(max(np.quantile(v, 0.25), 1e-5)); hi.append(max(np.quantile(v, 0.75), 1e-5))
            pgf_lines.append(pgf_series(i, xs, med, lo, hi, labels[s] if ai == 1 else None,
                                        color='black' if s == 'whole' else None))
        title = 'switch-free topologies' if ai == 0 else 'mixed (switches and any-joins)'
        opts = (f'width=0.37\\textwidth,height=5.2cm,xmode=log,ymode=log,xlabel={{team size (nodes)}},title={{{title}}},'
                'grid=major,grid style={gray!20},tick label style={font=\\footnotesize},label style={font=\\footnotesize},'
                'title style={font=\\footnotesize}')
        opts += ',ylabel={wall time per team (s)}' if ai == 0 else ',legend pos=outer north east,legend style={font=\\scriptsize,draw=none,fill=none}'
        pgf_panels.append(f'\\begin{{axis}}[{opts}' + (',name=left]' if ai == 0 else ',at={(left.east)},anchor=west,xshift=1.2cm]')
                          + '\n' + '\n'.join(pgf_lines) + '\n\\end{axis}')
    FIGS['figScalability'] = '\\begin{tikzpicture}\n' + '\n'.join(pgf_panels) + '\n\\end{tikzpicture}'
    for s in strats:
        for grp, topo_set in [('free', ['layered', 'sp', 'random']), ('mixed', ['mixed'])]:
            tos = [r for r in rows if r['topo'] in topo_set]
            pts_c = [(math.log(r['nodes']), math.log(max(secs(res(r, s)), 1e-6))) for r in tos if r['n'] >= 50]
            pts_s = [(math.log(r['nodes']), math.log(max(res(r, s)['seconds'], 1e-6))) for r in tos if r['n'] >= 50 and not res(r, s)['timeout']]

            def fit(P):
                if len(P) < 5:
                    return (math.nan, math.nan, math.nan)
                P = np.array(P)
                sl_ = np.polyfit(P[:, 0], P[:, 1], 1)[0]
                bs = [np.polyfit(P[i, 0], P[i, 1], 1)[0] for i in (RNG.integers(0, len(P), len(P)) for _ in range(2000))]
                return (sl_, np.quantile(bs, 0.025), np.quantile(bs, 0.975))
            sc, ss = fit(pts_c), fit(pts_s)
            tout = sum(res(r, s)['timeout'] for r in tos)
            big = [secs(res(r, s)) for r in tos if r['n'] == max(sizes)]
            det = sum(1 for r in tos if res(r, s).get('detected') and not res(r, s)['timeout'])
            fmt = lambda t: '--' if math.isnan(t[0]) else f'{t[0]:.2f} [{t[1]:.2f}, {t[2]:.2f}]'
            slope_lines.append(f"{labels[s]} & {grp} & {fmt(ss)} & {fmt(sc)} & {np.median(big):.2f} & {tout}/{len(tos)} & {det}/{len(tos)} \\\\")
            if not math.isnan(sc[0]):
                macro(f'Slope{s}{grp}', sc[0], '.2f')
                macro(f'SlopeHi{s}{grp}', sc[2], '.2f')
            if not math.isnan(ss[0]):
                macro(f'SlopeSurv{s}{grp}', ss[0], '.2f')
            macro(f'Timeouts{s}{grp}', tout)
            macro(f'Detect{s}{grp}', det)
            macro(f'DetectRate{s}{grp}', det / len(tos), 'pct')
            macro(f'TimeBig{s}{grp}', float(np.median(big)), '.2f')
            macro(f'Teams{grp}', len(tos))
    write_table('scalability', '\n'.join(slope_lines))
    ex = [r['exhaustive3'] for r in rows]
    macro('ExhSkipped', sum(1 for x in ex if x.get('skipped')))
    macro('ExhTimeout', sum(1 for x in ex if x.get('timeout')))
    macro('ExhRun', sum(1 for x in ex if not x.get('skipped')))
    mem = [r['strategies']['SL'].get('peak_mb') for r in rows if r['strategies']['SL'].get('peak_mb') is not None]
    if mem:
        macro('PeakMemSL', max(mem), '.0f')
    lim = sum(r['strategies']['SL']['limited'] for r in rows)
    macro('LimitedSL', lim)
    conf = [r for r in rows if 'SLconf' in r]
    if conf:
        for grp, topo_set in [('free', ['layered', 'sp', 'random']), ('mixed', ['mixed'])]:
            cs = [r for r in conf if r['topo'] in topo_set]
            macro(f'ConfTimeouts{grp}', sum(r['SLconf']['timeout'] for r in cs))
            macro(f'ConfTeams{grp}', len(cs))
            macro(f'ConfDetect{grp}', sum(1 for r in cs if r['SLconf']['detected']))
            big = [r for r in cs if r['n'] == 200]
            if big:
                macro(f'ConfTimeTwoHundred{grp}', float(np.median([B if r['SLconf']['timeout'] else r['SLconf']['seconds'] for r in big])), '.2f')
                macro(f'RawTimeTwoHundred{grp}', float(np.median([B if r['strategies']['SL']['timeout'] else r['strategies']['SL']['seconds'] for r in big])), '.2f')
        macro('ConfExhausted', sum(r['SLconf']['exhausted'] for r in conf))
    cc = d['convex_counts']
    lines = []
    for n in sorted({c['n'] for c in cc}):
        cells = [str(next((c['convex'] for c in cc if c['n'] == n and c['topo'] == t), '--') or '$>$4e5') for t in ['chain', 'forkjoin', 'layered']]
        lines.append(f"{n} & " + ' & '.join(cells) + ' \\\\')
    write_table('convex_counts', '\n'.join(lines))


# ------------------------------------------------------------------ E6
def e6():
    d = load('e6_evolution')
    if not d:
        return
    ch = [(r['topo'], c) for r in d['rows'] for c in r['changes']]
    macro('EvoChanges', len(ch))
    macro('EvoTeams', len(d['rows']))
    macro('EvoSkipped', sum(1 for r in d['rows'] if r.get('skipped')))
    macro('EvoAgree', np.mean([c['agree'] for _, c in ch]), 'pct')
    frac = [c['redone'] / c['total'] for _, c in ch]
    macro('EvoRedone', np.mean(frac), 'pct')
    nonchain = [c['redone'] / c['total'] for t, c in ch if t != 'chain']
    m, lo, hi = boot_ci(nonchain)
    macro('EvoRedoneNonChain', m, 'pct')
    macro('EvoRedoneNonChainHi', hi, 'pct')
    macro('EvoRedoneChain', np.mean([c['redone'] / c['total'] for t, c in ch if t == 'chain']), 'pct')
    speed = [c['full_seconds'] / max(c['inc_seconds'], 1e-6) for _, c in ch]
    macro('EvoSpeedup', float(np.median(speed)), '.1f')
    macro('EvoSlower', np.mean([x < 1 for x in speed]), 'pct')
    for n in sorted({r['n'] for r in d['rows']}):
        sp = [c['full_seconds'] / max(c['inc_seconds'], 1e-6) for r in d['rows'] if r['n'] == n for c in r['changes']]
        rd = [c['redone'] / c['total'] for r in d['rows'] if r['n'] == n for c in r['changes']]
        macro(f'EvoSpeedupN{n}', float(np.median(sp)), '.1f')
        macro(f'EvoRedoneN{n}', np.mean(rd), 'pct')
        macro(f'EvoSlowerN{n}', np.mean([x < 1 for x in sp]), 'pct')
    kinds = ['oracle', 'kind', 'route', 'join', 'req', 'decl', 'gua', 'edge']
    lines = []
    topos = ['chain', 'tree', 'forkjoin', 'layered', 'sp', 'random', 'mixed']
    for k in kinds:
        v = [c['redone'] / c['total'] for _, c in ch if c['change'] == k]
        if v:
            macro(f'EvoRedone{k}', np.mean(v), 'pct')
            cells = []
            for t in topos:
                w = [c['redone'] / c['total'] for tt, c in ch if c['change'] == k and tt == t]
                cells.append(pct(np.mean(w)) if w else '--')
            lines.append(f"{k} & {len(v)} & " + ' & '.join(cells) + f" & {pct(np.mean(v))} \\\\")
    write_table('evolution', '\n'.join(lines))
    p = plt()
    fig, ax = p.subplots(figsize=(3.45, 2.2))
    present = [k for k in kinds if any(c['change'] == k for _, c in ch)]
    pgf_lines = []
    for i, grp in enumerate([['chain'], ['tree', 'forkjoin', 'layered', 'sp', 'random', 'mixed']]):
        ys = [np.mean([c['redone'] / c['total'] for t, c in ch if c['change'] == k and t in grp] or [np.nan]) for k in present]
        cis = [boot_ci([c['redone'] / c['total'] for t, c in ch if c['change'] == k and t in grp]) for k in present]
        pgf_lines.append(pgf_series(i, list(range(len(present))), ys, [c[1] for c in cis], [c[2] for c in cis],
                                    'chain' if i == 0 else 'other topologies'))
        ax.plot(range(len(present)), ys, STYLES[i], color=COLORS[i], marker=MARKERS[i], markersize=4,
                label='chain' if i == 0 else 'other topologies')
    ax.set_xticks(range(len(present)))
    ax.set_xticklabels(present, rotation=30)
    ax.set_ylabel('slices re-verified (fraction)')
    ax.set_xlabel('changed attribute')
    ax.set_ylim(0, 1.05)
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(OUT / 'figures/evolution.pdf')
    p.close(fig)
    names = {'kind': 'kind or oracle', 'route': 'routing', 'join': 'join policy', 'req': 'requirement',
             'decl': 'declared evidence', 'gua': 'guarantee', 'edge': 'edge'}   # as in the recertification table
    FIGS['figEvolution'] = ('\\begin{tikzpicture}\\begin{axis}[width=\\columnwidth,height=5cm,ymin=0,ymax=1.05,'
                            f'xtick={{{",".join(str(i) for i in range(len(present)))}}},'
                            f'xticklabels={{{",".join(names.get(k, k) for k in present)}}},'
                            'x tick label style={rotate=30,anchor=north east,font=\\footnotesize},xlabel={changed attribute},'
                            'ylabel={fraction of slices re-verified},grid=major,grid style={gray!20},'
                            'legend pos=north west,legend style={font=\\scriptsize,draw=none,fill=none},'
                            'tick label style={font=\\footnotesize},label style={font=\\footnotesize}]\n'
                            + '\n'.join(pgf_lines) + '\n\\end{axis}\\end{tikzpicture}')
    evolution_detail(d['rows'], topos)


def evolution_detail(teams, topos):
    """Detailed recertification table: (a) per change type, the dependency rule of the incremental
    theorem, the share of slices re-verified (mean with a 95% bootstrap CI over changes, median, share of
    changes that re-verify every slice), the mean share by team size, and wall time; (b) the mean share
    by change type and topology. The cross-check against full re-verification is reported in the text."""
    rng = np.random.default_rng(20261104)   # local stream: do not perturb the shared RNG used by later stages
    ch = [(r, c) for r in teams for c in r['changes']]
    sizes = sorted({r['n'] for r in teams})
    groups = [('Node policy', [('kind', 'kind or oracle', '$\\{a\\}$'), ('route', 'routing', '$\\{a\\}$'),
                               ('join', 'join policy', '$\\{a\\}$')]),
              ('Node contract', [('req', 'requirement', '$\\anc^*(a)$'), ('decl', 'declared evidence', '$\\anc^*(a)$'),
                                 ('gua', 'guarantee', '$\\anc^*(Y)$')]),
              ('Structure', [('edge', 'edge added or removed', '$\\anc^*(Y)$, both')])]

    def ci(v):
        v = np.asarray(v, float)
        m = v[rng.integers(0, len(v), (10_000, len(v)))].mean(axis=1)
        return v.mean(), np.quantile(m, 0.025), np.quantile(m, 0.975)

    frac = lambda c: c['redone'] / c['total']
    speed = lambda c: c['full_seconds'] / max(c['inc_seconds'], 1e-6)

    def row(label, dep, cs):
        f = [frac(c) for _, c in cs]
        m, lo, hi = ci(f)
        by = [pct(np.mean([frac(c) for r, c in cs if r['n'] == n])) for n in sizes]
        sp = [speed(c) for _, c in cs]
        full = 1000 * np.median([c['full_seconds'] for _, c in cs])
        n_ = f'{len(cs):,}'.replace(',', '{,}')
        return (f"{label} & {dep} & {n_} & {pct(m)} & {{\\footnotesize[{pct(lo)}, {pct(hi)}]}} & {pct(np.median(f))} & "
                f"{pct(np.mean([x == 1 for x in f]))} & " + ' & '.join(by) +
                f" & {full:.1f} & {np.median(sp):.1f} & {pct(np.mean([x < 1 for x in sp]))} \\\\")

    a, b = [], []
    for gi, (gname, items) in enumerate(groups):
        if gi:
            a.append('\\addlinespace')
            b.append('\\addlinespace')
        a.append(f'\\multicolumn{{13}}{{@{{}}l}}{{\\textit{{{gname}}}}}\\\\')
        b.append(f'\\multicolumn{{9}}{{@{{}}l}}{{\\textit{{{gname}}}}}\\\\')
        for k, label, dep in items:
            cs = [(r, c) for r, c in ch if c['change'] == k]
            if not cs:
                continue
            a.append(row(f'\\quad {label}', dep, cs))
            cells = [pct(np.mean([frac(c) for r, c in cs if r['topo'] == t])) for t in topos]
            b.append(f"\\quad {label} & {len(cs)} & " + ' & '.join(cells) + f" & {pct(np.mean([frac(c) for _, c in cs]))} \\\\")
            sp = [speed(c) for _, c in cs]
            macro(f'EvoMedian{k}', np.median([frac(c) for _, c in cs]), 'pct')
            macro(f'EvoAllSlices{k}', np.mean([frac(c) == 1 for _, c in cs]), 'pct')
            macro(f'EvoSpeedup{k}', float(np.median(sp)), '.1f')
            macro(f'EvoSlower{k}', np.mean([x < 1 for x in sp]), 'pct')
    a += ['\\midrule', row('All changes', '', ch)]
    b += ['\\midrule', 'All changes & ' + f'{len(ch):,} & '.replace(',', '{,}') +
          ' & '.join(pct(np.mean([frac(c) for r, c in ch if r['topo'] == t])) for t in topos) +
          f" & {pct(np.mean([frac(c) for _, c in ch]))} \\\\"]
    macro('EvoMedianAll', np.median([frac(c) for _, c in ch]), 'pct')
    for t in topos:
        macro(f'EvoRedoneTopo{t}', np.mean([frac(c) for r, c in ch if r['topo'] == t]), 'pct')
    macro('EvoFullMs', 1000 * float(np.median([c['full_seconds'] for _, c in ch])), '.1f')
    macro('EvoIncMs', 1000 * float(np.median([c['inc_seconds'] for _, c in ch])), '.1f')
    for n in sizes:
        macro(f'EvoSlicesN{n}', float(np.mean([r['slices'] for r in teams if r['n'] == n and not r.get('skipped')])), '.0f')
    write_table('evolution_detail', '\n'.join(a))
    write_table('evolution_topology', '\n'.join(b))


# ------------------------------------------------------------------ E7
def e7():
    d = load('e7_ablation')
    if not d:
        return
    sens = d['sensitivity']
    lines = []
    for param, label in [('p_gate', 'share of gates'), ('oracle_pool', 'distinct oracles'), ('req_density', 'max.\\ requirements')]:
        for v in sorted({s['value'] for s in sens if s['param'] == param}):
            rs = [s for s in sens if s['param'] == param and s['value'] == v and s['cls'] != 'clean']
            cl = [s for s in sens if s['param'] == param and s['value'] == v and s['cls'] == 'clean']
            lines.append(f"{label} & {v} & {pct(np.mean([s['sl'] for s in rs]))} & {pct(np.mean([s['al'] for s in rs]))} & "
                         f"{pct(np.mean([s['sl'] for s in cl]))} & {sum(s['sl_false'] for s in rs + cl)} \\\\")
    write_table('sensitivity', '\n'.join(lines))
    macro('SensTeams', len(sens))
    macro('SensMinRecall', min(np.mean([s['sl'] for s in sens if s['param'] == p and s['value'] == v and s['cls'] != 'clean'])
                               for p in {s['param'] for s in sens} for v in {s['value'] for s in sens if s['param'] == p}), 'pct')
    macro('SensFalseKeys', sum(s['sl_false'] for s in sens))
    abl = d['ablation']
    macro('AblTeams', len(abl))
    lines = []
    for cls in HIDDEN:
        rs = [a for a in abl if a['cls'] == cls]
        lines.append(f"{cls} & {pct(np.mean([a['full'] for a in rs]))} & {pct(np.mean([a['joins_as_all'] for a in rs]))} & "
                     f"{pct(np.mean([a['no_faults'] for a in rs]))} & {sum(a['nonconvex_false_keys'] for a in rs)} \\\\")
    write_table('ablation', '\n'.join(lines))
    macro('AblNonconvexTried', sum(a['nonconvex_tried'] for a in abl))
    macro('AblNonconvexFalse', sum(a['nonconvex_false_keys'] for a in abl))
    for k in ['joins_as_all', 'no_faults', 'full']:
        for cls in HIDDEN:
            macro(f'Abl{k}{cls}', np.mean([a[k] for a in abl if a['cls'] == cls]), 'pct')
    w = d['wild_false_alarms']
    macro('WildFATeams', w['teams'])
    macro('WildFASlices', w['slices'])
    macro('WildFAFindings', w['findings'])
    macro('WildFAFalse', w['false'])
    macro('WildFARate', w['false'] / max(1, w['findings']), 'pct')
    macro('WildFASliceRate', w['slices_false'] / max(1, w['slices']), 'pct')
    if 'confirmed' in w:
        macro('WildFAConfirmed', w['confirmed'])
        macro('WildFAConfirmedFalse', w['confirmed_false'])
        macro('WildFATrueLost', w['true_lost'])
        macro('WildFALiftSeconds', w['lift_seconds'], '.1f')
        macro('WildNCSlices', w['nc_slices'])
        macro('WildNCFalseRate', w['nc_false'] / max(1, w['nc_findings']), 'pct')


# ------------------------------------------------------------------ running example
def rex():
    d = load('running_example')
    if not d:
        return
    for name, label in [('chain', 'Chain'), ('chain_repair_downstream', 'Down'), ('chain_repair_independent', 'Indep'),
                        ('forkjoin', 'Fj'), ('forkjoin_all', 'FjAll')]:
        r = d[name]
        macro(f'Rex{label}Convex', r['convex_slices'])
        macro(f'Rex{label}Agent', len(r['agent_level']))
        macro(f'Rex{label}Lint', len(r['lint']))
        macro(f'Rex{label}Smells', len(r['smells']))
        macro(f'Rex{label}Symptoms', len(r['symptoms']))
        if r['symptoms']:
            s = r['symptoms'][0]
            macro(f'Rex{label}Depth', s['depth'])
            macro(f'Rex{label}Minimal', len(s['minimal']))


def write_macros():
    lines = ['% Generated by scripts/process_results.py from results/*.json. Do not edit.']
    for k in sorted(MACROS):
        lines.append(f'\\newcommand{{\\{k}}}{{{MACROS[k]}}}')
    (OUT / 'results_macros.tex').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    (RES / 'macros.json').write_text(json.dumps(MACROS, indent=1, sort_keys=True) + '\n', encoding='utf-8')
    # the same macros, plus table bodies and plot code, as a marked block inside main.tex
    block = [BEGIN, '% Generated by scripts/process_results.py from results/*.json. Do not edit this block.']
    block += [f'\\newcommand{{\\{k}}}{{{MACROS[k]}}}' for k in sorted(MACROS)]
    for k in sorted(TABLES):
        block.append(f'\\newcommand{{\\{k}}}{{%\n{TABLES[k]}}}')
    for k in sorted(FIGS):
        block.append(f'\\newcommand{{\\{k}}}{{%\n{FIGS[k]}}}')
    block.append(END)
    main = OUT / 'main.tex'
    text = main.read_text(encoding='utf-8')
    if BEGIN in text and END in text:
        head, rest = text.split(BEGIN, 1)
        _, tail = rest.split(END, 1)
        main.write_text(head + '\n'.join(block) + tail, encoding='utf-8')
    else:
        print('main.tex has no generated block; skipped')
    print(len(MACROS), 'macros', len(TABLES), 'tables', len(FIGS), 'figures')


BEGIN = '% BEGIN GENERATED RESULTS'
END = '% END GENERATED RESULTS'


if __name__ == '__main__':
    for f in (rex, e1, e2, e4b, e8, teaser, e3, e5, e6, e7):
        f()
    write_macros()
