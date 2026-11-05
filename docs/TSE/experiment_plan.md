# Experiment plan (pre-registered before any experiment was run)

Frozen on 2026-11-04. Changes after this date are appended in the deviation log at
the end and are never edited into the body.

## Common setup

* All runs are CPU-only, deterministic given a seed; no LLM is called.
* ≥ 10 independent seeds per configuration (seeds 0..9 unless stated).
* Each result file records: seed list, configuration, git commit, Python and library
  versions, wall time.
* Teams come from `slicing/generator.py` (topologies: chain, tree, fork-join,
  layered, series-parallel, random DAG, mixed) and defects from
  `slicing/injector.py` (classes A1–A4, S1–S6b, plus clean and decoy teams).
* Ground truth (GT): the injected class, the root-cause node set R*, the injected
  symptom keys K* (verified to be in Sym(T) by the exact semantics), and, for teams
  with ≤ 16 nodes, the true minimal manifesting slices from exhaustive enumeration of
  convex slices up to size 6 (depth > 6 is recorded as "> 6").

## Checkers compared

B1 agent-level (singleton slices); B2 whole-team exact (verdict + one witness;
localization = hull of the witness lineage); B3 random convex slices matched in
number and size to the best strategy; B4 structural lint (set difference, counts
claimers for critical goals, no ancestry, no paths); slicing strategies: window-k,
band-w, region, goal-directed, exhaustive-k.

## Metrics

* Detection: a checker *detects* an injected defect iff it reports at least one key
  in K*. Recall, precision (reported keys that are in Sym(T) / all reported keys),
  F1.
* Hidden-blind-spot rate by depth: fraction of injected keys with depth ≥ 2.
* Localization: *exact* (top-ranked slice for a key ∈ GT MMS of that key);
  *precise* (top slice ⊆ hull(R*)); *hit* (top slice ∩ R* ≠ ∅); size ratio
  |slice|/|N|. Top-ranked slice = smallest manifesting slice of the family
  (ties: fewest choice points, then lexicographic).
* Witness length (nodes in the lineage hull) and explanation size (|slice| + number
  of mechanisms reported).
* False-alarm rate: on clean and decoy teams, fraction of teams with ≥ 1 reported
  key; per slice, fraction of findings not in Sym(T).
* Cost: wall time, peak memory (tracemalloc), slices examined, runs enumerated.
* Recertification: slices re-verified / all slices; time saved; agreement of the
  incremental result with full re-verification.

## Hypotheses, tests and decision rules

**RQ1.**
* H1.1: all SMT obligations are UNSAT (valid) under Z3; all proof mutants are killed.
* H1.2: zero mismatches between implementation and brute-force oracle (run vs model
  semantics, T1, T2, T3, T4c, T5c, T6, T8) on ≥ 20,000 random small teams.
* Decision: any mismatch is a bug in code or theory; it is fixed and logged, and the
  run is repeated. No statistical test.

**RQ2.**
* H2.1: on defect classes S2–S6, the best slicing strategy (k ≤ 4) has higher
  per-seed recall than B1. Test: one-sided Wilcoxon signed-rank on paired per-seed
  recall (10 pairs), Holm correction over classes; effect size Vargha–Delaney A12.
  Decision: supported if Holm-adjusted p < 0.05 and A12 ≥ 0.71.
* H2.2: exact localization of the slicing checker exceeds B2 and B3. Same test.
* H2.3: on clean and decoy teams, the slicing checker's team-level false-alarm rate
  is ≤ 5% (95% bootstrap CI upper bound reported). Decision: supported if the point
  estimate is ≤ 5%.
* Paired instance-level binary outcomes are also reported as exact McNemar tests.

**RQ3.**
* H3.1: region, band, window and goal-directed strategies scale polynomially; fitted
  log-log slope of time vs |N| ≤ 2 for |N| ∈ [10, 5000]. Whole-team exact checking
  and exhaustive-k enumeration show super-polynomial growth or time-outs (60 s/team).
* H3.2: detection saturates in k: the gain in recall from k to k+1 is < 1 percentage
  point for some k ≤ 4 (bootstrap CI reported).
* H3.3: incremental recertification re-verifies < 50% of slices on average for
  non-chain topologies and agrees with full re-verification in 100% of cases.
* Comparisons of strategies on runtime: Wilcoxon signed-rank on paired per-seed
  medians, Holm correction, A12.

**E7 sensitivity and ablation** (descriptive, with bootstrap CIs): contract density,
shared-oracle rate, join-policy mix; ablations (a) all joins treated as `all`,
(b) non-convex slices allowed, (c) no fault reasoning inside slices.

## Deviation log

| # | Date | Deviation | Reason | Effect |
|---|---|---|---|---|
| D1 | 2026-11-04 | Baseline B5 (pattern-based smell detector) added to E2/E3. | A reviewer-style objection: B4 is too weak to represent careful practice. | New column only; no hypothesis changed. |
| D2 | 2026-11-04 | E4 (slice-size sweep) is run inside the E2 runner on the small benchmark (exhaustive-k columns k1..k5). | Shares the exhaustive ground-truth enumeration. | None on metrics. |
| D3 | 2026-11-04 | E3 encodings corrected: ChatDev `Execute` and MapCoder `SampleIO` gates now require `code` (protocol P3: a role requires the artifacts it consumes). Found while writing the paper, before reporting. | The earlier encodings violated P3. | MapCoder changes from safe to S6a; ChatDev unchanged (S4). |
| D4 | 2026-11-04 | All experiments re-run from scratch on a Linux/aarch64 machine (20 cores, Python 3.12) instead of the Windows machine used for pilots. | Machine change between sessions. | Runtimes differ; all seeded outcomes are deterministic. The random 3-CNF sample of the reduction check differs from the pilot (379 vs 486 satisfiable formulas) (cause not established; the pilot result file does not record the generator version); disagreements are 0 in both, and the final numbers come from the re-run only. |

| D5 | 2026-11-04 | Revision after round-1 reviews: (a) slice findings are *confirmed* by lifting witnesses to runs of the team before they count (depth, minimal slices and agent level are defined over confirmed findings); (b) new baselines B6 (fault-aware must-analysis), B2-dev (witness deviation set) and B2+shrink (greedy slice minimization); (c) new experiments E4b (hand-off distance 0..5, k <= 8) and E8 (mutation benchmark with natural ground truth); (d) the pre-registered detection metric (any GT key) is reported next to the primary-key metric; ground truth uses k <= 6 for teams with <= 16 nodes as planned; (e) degenerate hypothesis tests (H2.1) replaced by exact counts; H2.2 Holm-corrected; E5 time-outs censored at the budget and detection over all teams; (f) E3 encodings revised for protocol consistency (MetaGPT/AgentCoder gates require code; ChatDev reviewer guarantees `reviewed`; Agentless selection after validation; MapCoder debugging consumes code; debate has one revision round); (g) E6 adds 80-node teams; E7 reports raw vs. confirmed false findings. | Round-1 reviews (docs/TSE/reviews/round1). | All numbers regenerated. H2.1 and H3.2 are now reported as consequences of the benchmark design, not as findings. |
| D6 | 2026-11-04 | Not done: second independent encoder for E3, validation against real executions or failure traces, crossing class with seed in E5, grounding the E6 change mix. | Out of scope for this study (no LLM runs). | Reported as threats to validity. |
