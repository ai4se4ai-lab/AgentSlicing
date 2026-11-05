# Final report

## What was proved (paper proofs, Appendix A; some steps sketched)
- Lemmas: worst case (runs suffice for all contract-respecting models), minimal choices, convexity,
  face value dominates content.
- Prop. 1 (agent level = singleton slices; what it can see).
- Thm 2 slice abstraction: exact boundary behavior preserves symptoms (global failure set);
  declared contracts sound for f = 0 and all-or-none entry delivery; no exact single set-valued pair
  for a disjunctive exit; partition composition with acyclic quotient; cyclic counterexample.
- Thm 3 soundness: certification with N or a partition is exact; confirmed findings are symptoms;
  raw findings can be false alarms.
- Thm 4 separation: parametric families (S2, S3, S4, S6a, S6b) with depth 2 or ℓ+2; view-disjunctive
  analyses cannot be sound and free of false alarms on S2, S4, S6a; recovery of confirmed findings.
- Thm 5 localization: minimal confirming slices exist; uniqueness criterion; confirmed findings are
  monotone in the slice; raw findings are not.
- Prop. 6 overlap. Thm 7 complexity (assume/goal NP-complete; robust in D^p, NP- and coNP-hard;
  safety coNP-complete; reachability and depth NP-complete). Thm 8 incremental recertification.

## What was mechanized
- 14 Z3 obligations for per-node steps over an uninterpreted property sort (13 valid, 1 intended
  countermodel), 6 proof mutants all killed. Inductions are not mechanized.
- Bounded checks against brute-force oracles (model, replay, run oracles): 219,200 team-check pairs,
  0 mismatches; reductions checked against SAT on 500 formulas (0 disagreements each).

## What was measured
- E8 (mutation benchmark, 1,680 teams, 8–32 nodes): 36.1% of 3,863 symptoms have depth ≥ 2; for 210 of
  1,345 defective teams an agent-level check reports nothing. Must-analysis: 100% of hidden symptoms,
  3.2% false findings, symptom-node localization. Confirmed SL: 99.9%, 0 false (raw: 6.5% false).
  Exact localization: shrinking 99.2%, SL 86.3% (96.6% at 8 nodes → 77.7% at 32), deviation set 1.0%.
- E2 (injected, 4,480 teams), E4b (depth = ℓ+2, two host sizes), E3 (9 designs; 6 with a finding
  agent-level analysis does not report, under P3 and f = 1), E5 (to 5,011 nodes; H3.1 not supported),
  E6 (recertification 100% correct, 35.0% of slices re-verified on non-chain topologies, median 1.9×
  speed-up), E7 (raw false findings 2.9% on wild teams, 0 after confirmation; ablations).

## Deviations from the plan
D1–D8 in `experiment_plan.md`: added baseline B5; E4 inside E2; E3 encoding fixes; machine change;
round-1 revision (confirmation, B6/B2-dev/shrink, E4b, E8, statistics, E3 protocol, E6 sizes);
not done (second encoder, real traces, E5 class×seed, change-mix grounding); round-2 revision
(robust confirmation, complete lifting, E8 to 32 nodes, E4b host size, confirmed cost in E5);
omitted pre-registered analyses (F1, witness length, runtime tests, join-mix sensitivity).

## Claims weakened or dropped, and why
- "Slice analysis detects what agent level cannot" → detection does not need slices (whole team,
  must-analysis); the contribution is precise (confirmed) findings plus localization.
- Prevalence (45.5% hidden) and saturation at k = 4 from the injected benchmark: dropped (artifacts of
  the class mix and the injector); replaced by E8 and E4b.
- T5(c) witness-hull theorem: dropped (vacuous). T2(c), T7(a): corrected. "Recovery" restated for
  confirmed findings. T4(b) limited to view-disjunctive analyses.
- 0.92 vs 0.21 localization against the lineage hull: replaced by comparisons with the deviation set
  and shrinking (shrinking beats the strategies).
- E3 count removed from the abstract (depends on protocol P3 and f = 1; single encoder).
- H3.1 scalability: reported as not supported.

## Required from the authors before submission
Commit the work and re-run `make all` from a clean tagged commit (result files currently record a
dirty worktree on `c223880`); remove `docs/TSE/work-is-under-review/` and `phase0_map.md` from the
package; anonymize the artifact (git history shows the author); set the author block.
