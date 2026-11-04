"""Turn results/*.json into statistics, LaTeX tables, figures and result macros.

Every number in the paper comes from here: docs/TSE/results_macros.tex (\\res... macros)
and docs/TSE/tables/*.tex; figures go to docs/TSE/figures/*.pdf. Do not hand-edit outputs.
"""
from __future__ import annotations

import json
import math
import re
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / 'results'
OUT = ROOT / 'docs/TSE'
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


def write_table(name, text):
    (OUT / 'tables' / f'{name}.tex').write_text(text + '\n', encoding='utf-8')


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
        macro('FoolingAllHold', 'all' if all(all(v.values()) for v in d['fooling'].values()) else 'not all')
        names = {'HN_equals_T': 'Exact semantics vs.\\ independent replay ($H_N=T$)',
                 'hybrid_vs_oracle': 'Hybrid semantics vs.\\ exhaustive replay (all slices $\\le 3$)',
                 'static_in_singletons': 'Lemma~\\ref{lem:face} at singletons ($F(\\emptyset)\\subseteq F(\\{v\\})$)',
                 'recovery': 'Recovery of agent-level findings (Thm.~\\ref{thm:sep}c)',
                 'witness_hull': 'Witness hull manifests (Thm.~\\ref{thm:loc}c)',
                 'whole_exact': 'Whole slice is exact (Thm.~\\ref{thm:sound}a)',
                 'quotient': 'Partition summaries compose (Thm.~\\ref{thm:abs}d)',
                 'incremental': 'Incremental $=$ full re-verification (Thm.~\\ref{thm:inc})',
                 'model_oracle': 'Run semantics vs.\\ all evidence models (Lemmas W, M)'}
        lines = []
        for k, label in names.items():
            lines.append(f"{label} & {w['checked'].get(k, 0):,} & {b['checked'].get(k, 0):,} & "
                         f"{w['mismatching_teams'].get(k, 0) + b['mismatching_teams'].get(k, 0)} \\\\".replace(',', '{,}'))
        write_table('conformance', '\n'.join(lines))
        macro('EOneSeconds', d['seconds'], '.0f')


# ------------------------------------------------------------------ E2 / E4
CHK = [('k1', 'B1 agent level'), ('SL', 'SL (combined)'), ('window2', 'window-2'), ('band1', 'band-1'),
       ('region', 'region'), ('goal', 'goal-directed'), ('B2', 'B2 whole team'), ('B3', 'B3 random'),
       ('B4', 'B4 lint'), ('B5', 'B5 smells')]
CLS_ORDER = ['A1', 'A2', 'A3', 'S1v', 'A4', 'S5', 'S2', 'S3', 'S4', 'S6a', 'S6b']


def seed_rates(rows, checker, field, cond=lambda r: True):
    by = defaultdict(list)
    for r in rows:
        if checker in r['checkers'] and cond(r):
            v = r['checkers'][checker].get(field)
            if v is not None:
                by[r['seed']].append(bool(v))
    return {s: np.mean(v) for s, v in by.items()}


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
    defect = [r for r in rows if r['cls'] in CLS_ORDER]
    # recall table (all teams, small+medium; k-family columns are small only)
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
    # hidden rate: fraction of injected defects (small benchmark) whose primary key has depth >= 2
    dep_all = [r['depth'] for r in small if r['cls'] in CLS_ORDER and r.get('depth')]
    macro('HiddenRate', np.mean([x >= 2 for x in dep_all]), 'pct')
    macro('HiddenRateSlice', np.mean([r['depth'] >= 2 for r in small if r['cls'] in HIDDEN and r.get('depth')]), 'pct')
    for c in ['k1', 'SL', 'B2', 'B3', 'B4', 'B5', 'goal', 'region']:
        hid = [r['checkers'][c]['primary_detected'] for r in rows if r['cls'] in HIDDEN and c in r['checkers']]
        macro(f'RecallHidden{c}', np.mean(hid), 'pct')
        allc = [r['checkers'][c]['primary_detected'] for r in defect if c in r['checkers']]
        macro(f'RecallAll{c}', np.mean(allc), 'pct')
    # statistics H2.1: per class, per-seed recall SL vs B1 (small + medium)
    stat_lines, ps, keep = [], [], []
    for cls in HIDDEN:
        rs = [r for r in rows if r['cls'] == cls]
        a = seed_rates(rs, 'SL', 'primary_detected')
        b = seed_rates(rs, 'k1', 'primary_detected', lambda r: True)
        b = {s: v for s, v in b.items()} or {s: 0.0 for s in a}
        # medium rows have no k1 column: use singleton strategy as the agent-level checker
        b2 = seed_rates(rs, 'singleton', 'primary_detected')
        seeds = sorted(a)
        x = [a[s] for s in seeds]
        y = [b2[s] for s in seeds]
        p = wilcoxon_greater(x, y)
        ps.append(p)
        b01, b10, pm = mcnemar([r['checkers']['SL']['primary_detected'] for r in rs], [r['checkers']['singleton']['primary_detected'] for r in rs])
        keep.append((cls, np.mean(x), np.mean(y), p, a12(x, y), b10, b01, pm, len(rs)))
    adj = holm(np.array(ps))
    for (cls, mx, my, p, eff, b10, b01, pm, n), pa in zip(keep, adj):
        stat_lines.append(f"{cls} & {n} & {pct(mx)} & {pct(my)} & {'$<$0.001' if pa < 0.001 else f'{pa:.3f}'} & {eff:.2f} & {b10}/{b01} & "
                          f"{'$<$0.001' if pm < 0.001 else f'{pm:.3f}'} \\\\")
    write_table('stats_recall', '\n'.join(stat_lines))
    macro('HTwoOneMaxP', max(adj), 'p')
    macro('HTwoOneMinAtwelve', min(k[4] for k in keep), '.2f')
    # localization (small benchmark, hidden classes, detected)
    loc_lines = []
    exact_seed = {}
    for c, label in [('k5', 'exhaustive $k\\le5$'), ('SL', 'SL (combined)'), ('goal', 'goal-directed'), ('region', 'region'),
                     ('window2', 'window-2'), ('B2', 'B2 whole team'), ('B3', 'B3 random')]:
        rs = [r for r in small if r['cls'] in HIDDEN and c in r['checkers'] and r['checkers'][c].get('primary_detected')]
        ex = [bool(r['checkers'][c].get('exact')) for r in rs]
        pr = [bool(r['checkers'][c].get('precise')) for r in rs]
        hit = [bool(r['checkers'][c].get('hit')) for r in rs]
        sr = [r['checkers'][c]['size_ratio'] for r in rs]
        ts = [r['checkers'][c]['top_size'] for r in rs]
        m, lo, hi = boot_ci(ex)
        loc_lines.append(f"{label} & {len(rs)} & {pct(m)} [{pct(lo)}, {pct(hi)}] & {pct(np.mean(pr))} & {pct(np.mean(hit))} & "
                         f"{np.mean(ts):.1f} & {np.mean(sr):.2f} \\\\")
        exact_seed[c] = seed_rates([r for r in small if r['cls'] in HIDDEN], c, 'exact',
                                   lambda r, c=c: r['checkers'].get(c, {}).get('primary_detected'))
        macro(f'LocExact{c}', m, 'pct')
        macro(f'LocPrecise{c}', np.mean(pr), 'pct')
        macro(f'LocRatio{c}', np.mean(sr), '.2f')
        macro(f'LocSize{c}', np.mean(ts), '.1f')
    write_table('localization', '\n'.join(loc_lines))
    for other in ['B2', 'B3']:
        seeds = sorted(set(exact_seed['SL']) & set(exact_seed[other]))
        x = [exact_seed['SL'][s] for s in seeds]
        y = [exact_seed[other][s] for s in seeds]
        macro(f'HTwoTwoP{other}', wilcoxon_greater(x, y), 'p')
        macro(f'HTwoTwoA{other}', a12(x, y), '.2f')
    # medium localization
    for c in ['SL', 'B2', 'B3', 'goal']:
        rs = [r for r in medium if r['cls'] in HIDDEN and c in r['checkers'] and r['checkers'][c].get('primary_detected')]
        if rs:
            macro(f'MedPrecise{c}', np.mean([bool(r['checkers'][c].get('precise')) for r in rs]), 'pct')
            macro(f'MedRatio{c}', np.mean([r['checkers'][c]['size_ratio'] for r in rs]), '.3f')
            macro(f'MedSize{c}', np.mean([r['checkers'][c]['top_size'] for r in rs]), '.1f')
    # false alarms on clean + decoys (all sizes)
    fa_lines = []
    for c, label in CHK:
        for grp, cls in [('clean', ['clean']), ('decoy', ['D2', 'D4', 'D5', 'D6'])]:
            v = [bool(r['checkers'][c]['alarm']) for r in rows if r['cls'] in cls and c in r['checkers']]
            if v:
                m, lo, hi = boot_ci(v)
                macro(f'Alarm{grp}{c}', m, 'pct')
                macro(f'AlarmHi{grp}{c}', hi, 'pct')
        v1 = [bool(r['checkers'][c]['alarm']) for r in rows if r['cls'] == 'clean' and c in r['checkers']]
        v2 = [bool(r['checkers'][c]['alarm']) for r in rows if r['cls'] in ('D2', 'D4', 'D5', 'D6') and c in r['checkers']]
        if v1:
            fa_lines.append(f"{label} & {pct(np.mean(v1))} & {pct(np.mean(v2))} \\\\")
    write_table('alarms', '\n'.join(fa_lines))
    macro('CleanTeams', sum(r['cls'] == 'clean' for r in rows))
    macro('DecoyTeams', sum(r['cls'] in ('D2', 'D4', 'D5', 'D6') for r in rows))
    fk = sum(r['checkers']['SL']['false_keys'] for r in rows)
    tk = sum(r['checkers']['SL']['reported'] for r in rows)
    macro('SLFalseKeys', fk)
    macro('SLReportedKeys', tk)
    macro('SLPrecision', 1 - fk / max(1, tk), 'pct')
    # diagnosis accuracy (SL, hidden + S5 classes)
    acc = [r['checkers']['SL'].get('cls') == r['cls'] for r in rows if r['cls'] in HIDDEN + ['S5'] and r['checkers']['SL'].get('primary_detected')]
    macro('DiagnosisAccuracy', np.mean(acc), 'pct')
    # per-topology recall on hidden classes
    topo_lines = []
    for topo in ['chain', 'tree', 'forkjoin', 'layered', 'sp', 'random', 'mixed']:
        rs = [r for r in rows if r['topo'] == topo and r['cls'] in HIDDEN]
        cells = [pct(np.mean([r['checkers'][c]['primary_detected'] for r in rs if c in r['checkers']])) for c in ['singleton', 'SL', 'region', 'goal', 'B3', 'B5']]
        sr = [r['checkers']['SL']['size_ratio'] for r in rs if r['checkers']['SL'].get('primary_detected')]
        topo_lines.append(f"{topo} & {len(rs)} & " + ' & '.join(cells) + f" & {np.mean(sr):.2f} \\\\")
    write_table('topology', '\n'.join(topo_lines))
    # E4: recall by k (small), per class with per-seed bootstrap CI
    p = plt()
    fig, ax = p.subplots(figsize=(3.45, 2.3))
    ks = list(range(1, d['K'] + 1))
    sweep_lines = []
    for i, cls in enumerate(HIDDEN):
        means, lows, highs = [], [], []
        for k in ks:
            sr = seed_rates([r for r in small if r['cls'] == cls], f'k{k}', 'primary_detected')
            m, lo, hi = boot_ci(list(sr.values()))
            means.append(m); lows.append(lo); highs.append(hi)
        ax.fill_between(ks, lows, highs, color=COLORS[i], alpha=0.12, linewidth=0)
        ax.plot(ks, means, STYLES[i], color=COLORS[i], marker=MARKERS[i], markersize=4, label=cls)
        sweep_lines.append(f"{cls} & " + ' & '.join(pct(m) for m in means) + ' \\\\')
    allk = []
    for k in ks:
        sr = seed_rates([r for r in small if r['cls'] in CLS_ORDER], f'k{k}', 'primary_detected')
        allk.append(boot_ci(list(sr.values())))
    ax.plot(ks, [a[0] for a in allk], '-', color='#3d3d3a', linewidth=2.2, label='all classes')
    ax.set_xlabel('maximum slice size $k$ (exhaustive convex slices)')
    ax.set_ylabel('recall (primary symptom)')
    ax.set_xticks(ks)
    ax.set_ylim(-0.03, 1.05)
    ax.legend(loc='lower right', ncol=2, fontsize=7)
    fig.tight_layout()
    fig.savefig(OUT / 'figures/k_sweep.pdf')
    p.close(fig)
    sweep_lines.append('all classes & ' + ' & '.join(pct(a[0]) for a in allk) + ' \\\\')
    write_table('k_sweep', '\n'.join(sweep_lines))
    for k, a in zip(ks, allk):
        macro(f'RecallK{k}', a[0], 'pct')
    gains = [allk[i + 1][0] - allk[i][0] for i in range(len(ks) - 1)]
    sat = next((ks[i] for i, g in enumerate(gains) if g < 0.01), None)
    macro('SaturationK', sat if sat is not None else 'none')
    for k in ks:
        alarms = [bool(r['checkers'][f'k{k}']['alarm']) for r in small if r['cls'] in ('clean', 'D2', 'D4', 'D5', 'D6')]
        macro(f'AlarmK{k}', np.mean(alarms), 'pct')
        macro(f'SlicesK{k}', np.mean([r['checkers'][f'k{k}']['slices'] for r in small]), '.0f')
    # depth histogram per class
    dep_lines = []
    for cls in CLS_ORDER:
        dep = [r['depth'] for r in small if r['cls'] == cls and r.get('depth')]
        cnt = [sum(1 for x in dep if x == k) for k in range(1, 6)]
        dep_lines.append(f"{cls} & " + ' & '.join(str(c) for c in cnt) + ' \\\\')
    write_table('depth', '\n'.join(dep_lines))
    SUMMARY['e2'] = {'hidden_rate': MACROS[mname('HiddenRate')]}


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
    for r in doc:
        if r['symptoms']:
            s = min(r['symptoms'], key=lambda s: (s['agent_level'], s['depth'] or 99))
            sl_ = ', '.join(s['minimal'][0]) if s['minimal'] else '--'
            key = f"{s['key'][0]}: \\textsf{{{s['key'][2].replace('_', '\\_')}}}"
            lines.append(f"\\cite{{{r['source']}}} {r['design']} & {r['nodes']} & {key} & {s['class']} & {s['depth']} & "
                         f"{{\\footnotesize {sl_}}} & {'yes' if s['agent_level'] else 'no'} \\\\")
        else:
            lines.append(f"\\cite{{{r['source']}}} {r['design']} & {r['nodes']} & none & -- & -- & -- & -- \\\\")
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
    strats = ['singleton', 'window2', 'band1', 'region', 'goal', 'SL']
    labels = {'singleton': 'singleton (B1)', 'window2': 'window-2', 'band1': 'band-1', 'region': 'region', 'goal': 'goal-directed', 'SL': 'SL (combined)'}
    sizes = sorted({r['n'] for r in rows})
    macro('ScaleMaxNodes', max(r['nodes'] for r in rows))
    macro('ScaleTeams', len(rows))
    macro('ScaleBudget', d['budget'], '.0f')
    p = plt()
    fig, axes = p.subplots(1, 2, figsize=(7.0, 2.4), sharey=True)
    slope_lines = []
    for ai, topo_set in enumerate([['layered', 'sp', 'random'], ['mixed']]):
        ax = axes[ai]
        for i, s in enumerate(strats + ['whole']):
            xs, med, lo, hi = [], [], [], []
            for n in sizes:
                rs = [r for r in rows if r['n'] == n and r['topo'] in topo_set]
                if s == 'whole':
                    v = [r['whole']['seconds'] for r in rs if not r['whole']['timeout']]
                    if len(v) < len(rs) / 2:
                        continue
                else:
                    v = [r['strategies'][s]['seconds'] for r in rs if not r['strategies'][s]['timeout']]
                    if len(v) < len(rs) / 2:
                        continue
                xs.append(np.mean([r['nodes'] for r in rs]))
                med.append(np.median(v)); lo.append(np.quantile(v, 0.25)); hi.append(np.quantile(v, 0.75))
            col = COLORS[i % 7] if s != 'whole' else '#3d3d3a'
            if xs:
                ax.fill_between(xs, lo, hi, color=col, alpha=0.12, linewidth=0)
                ax.plot(xs, med, STYLES[i % 7], color=col, marker=MARKERS[i % 7], markersize=3.5,
                        label=labels.get(s, 'B2 whole team (exact)'))
        ax.set_xscale('log'); ax.set_yscale('log')
        ax.set_xlabel('team size (nodes)')
        ax.set_title('switch-free topologies' if ai == 0 else 'mixed (switches + any-joins)', fontsize=8)
    axes[0].set_ylabel('wall time per team (s), median, IQR band')
    axes[1].legend(fontsize=6.5, loc='upper left')
    fig.tight_layout()
    fig.savefig(OUT / 'figures/scalability.pdf')
    p.close(fig)
    for s in strats + ['whole']:
        for grp, topo_set in [('free', ['layered', 'sp', 'random']), ('mixed', ['mixed'])]:
            pts = []
            for r in rows:
                if r['topo'] not in topo_set or r['n'] < 50:
                    continue
                x = r['whole'] if s == 'whole' else r['strategies'][s]
                if not x['timeout'] and x['seconds'] > 0:
                    pts.append((math.log(r['nodes']), math.log(x['seconds'])))
            if len(pts) < 5:
                slope = (math.nan, math.nan, math.nan)
            else:
                P = np.array(pts)
                sl = np.polyfit(P[:, 0], P[:, 1], 1)[0]
                bs = []
                for _ in range(2000):
                    i = RNG.integers(0, len(P), len(P))
                    bs.append(np.polyfit(P[i, 0], P[i, 1], 1)[0])
                slope = (sl, np.quantile(bs, 0.025), np.quantile(bs, 0.975))
            tos = [r for r in rows if r['topo'] in topo_set]
            tout = sum((r['whole'] if s == 'whole' else r['strategies'][s])['timeout'] for r in tos)
            big = [r for r in tos if r['n'] == max(sizes)]
            tbig = [(r['whole'] if s == 'whole' else r['strategies'][s]) for r in big]
            med_big = np.median([x['seconds'] for x in tbig if not x['timeout']]) if any(not x['timeout'] for x in tbig) else math.nan
            det = [x.get('detected') for x in ((r['whole'] if s == 'whole' else r['strategies'][s]) for r in tos)]
            det = [bool(v) for v in det if v is not None]
            slope_lines.append(f"{labels.get(s, 'B2 whole team (exact)')} & {grp} & "
                               f"{'--' if math.isnan(slope[0]) else f'{slope[0]:.2f} [{slope[1]:.2f}, {slope[2]:.2f}]'} & "
                               f"{'--' if math.isnan(med_big) else f'{med_big:.2f}'} & {tout}/{len(tos)} & {pct(np.mean(det)) if det else '--'} \\\\")
            if not math.isnan(slope[0]):
                macro(f'Slope{s}{grp}', slope[0], '.2f')
                macro(f'SlopeHi{s}{grp}', slope[2], '.2f')
            macro(f'Timeouts{s}{grp}', tout)
            macro(f'Detect{s}{grp}', np.mean(det) if det else 0.0, 'pct')
            if not math.isnan(med_big):
                macro(f'TimeBig{s}{grp}', med_big, '.2f')
    write_table('scalability', '\n'.join(slope_lines))
    ex = [r['exhaustive3'] for r in rows]
    macro('ExhSkipped', sum(1 for x in ex if x.get('skipped')))
    macro('ExhTimeout', sum(1 for x in ex if x.get('timeout')))
    macro('ExhRun', sum(1 for x in ex if not x.get('skipped')))
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
    for i, grp in enumerate([['chain'], ['tree', 'forkjoin', 'layered', 'sp', 'random', 'mixed']]):
        ys = [np.mean([c['redone'] / c['total'] for t, c in ch if c['change'] == k and t in grp] or [np.nan]) for k in present]
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


def write_macros():
    lines = ['% Generated by scripts/process_results.py from results/*.json. Do not edit.']
    for k in sorted(MACROS):
        lines.append(f'\\newcommand{{\\{k}}}{{{MACROS[k]}}}')
    (OUT / 'results_macros.tex').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    (RES / 'macros.json').write_text(json.dumps(MACROS, indent=1, sort_keys=True) + '\n', encoding='utf-8')
    print(len(MACROS), 'macros')


if __name__ == '__main__':
    for f in (e1, e2, e3, e5, e6, e7):
        f()
    write_macros()
