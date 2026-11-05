# Second-Round Review: "Agent Slicing: Localizing Blind Spots in Declared-Contract Models of Multi-Agent AI Teams"

**Reviewer B** (empirical software engineering: experimental design, benchmarks and ground truth, baselines, statistics, threats to validity, replication). Round 2.

Material examined: revised `docs/TSE/main.pdf` (22 pages) and `main.tex`; round-1 reviews and `response_matrix.md`; the artifact (`experiments/`, `slicing/`, `scripts/process_results.py`, `results/*.json`, `experiment_plan.md` with deviation log D1-D6, `conformance_log.md`). What I ran is listed under "Artifact check". Note that `main.tex` (21:21) is newer than `main.pdf` (18:36); the only diff against HEAD is one word in the introduction, so my comments apply to both.

---

## Summary

The revision keeps the formal core (teams as DAGs of agents and gates; convex slices under a hybrid semantics) and adds three main changes. (1) **Confirmation.** A slice finding counts only if its witness lifts to a run of the whole team, so confirmed findings are sound and monotone in the slice. (2) **New baselines.** These are a fault-aware global must-analysis (B6), the witness deviation set (B2-dev) and whole-team witness plus greedy slice shrinking (B2+shrink). (3) **New benchmarks.** A mutation benchmark (E8: 840 clean generated teams, each with 1-3 random engineering changes, symptoms decided by the exact semantics) and a hand-off-distance sweep (E4b: ℓ = 0..5, k ≤ 8). The injected benchmark (E2) is now presented as a per-class test, and prevalence claims based on it are gone.

New headline numbers (E8): 32.4% of 1,542 symptom keys are hidden at agent level. Confirmed agent-level analysis finds none of them. B6 finds all of them, but 45 of its 1,586 reported keys (2.8%) are false. Confirmed SL finds all keys with no false finding, and its top slice is an exact minimal slice for 91.4% of hidden keys. B2+shrink is exact for 100%, and the deviation set for 1.8%. In E3, 6 of 9 encoded designs have a finding that agent-level analysis misses.

The authors took the first round seriously. The new mutation benchmark, the must-analysis and shrink baselines, confirmation, censoring, the common denominators and the honest RQ3 verdict are real improvements, and the artifact is still exemplary. What remains is mainly a gap between the evidence and how it is framed:

- the abstract and conclusion make claims that the paper's own tables contradict;
- two headline results are true by definition or by construction;
- the new benchmark covers only teams of 8-12 nodes, and its headline rates change with team size;
- the method as claimed (confirmed SL) has no cost evaluation beyond toy sizes;
- the best localizer in the paper is a baseline, yet the conclusion reads as if slicing strategies were the winner.

---

## Assessment of round-1 concerns

| R1 item | Status | Comment |
|---|---|---|
| M1(a) prevalence/saturation claims from injector parameters | **Resolved** | 45.5% and "saturates at k = 4" are gone from abstract, intro and answer boxes. E2 is labeled a per-class test, and the paper now says the B1/SL contrast "is a consequence of Theorem 4a ... not an independent finding". |
| M1(b) non-template benchmark | **Partly resolved** | E8 is the right kind of benchmark: random operators, ground truth from the exact semantics, class and depth not chosen. But teams have 8-12 nodes, the operator mix is uniform and chosen by the authors, 97/840 "mutated" teams received no change at all, and the headline rates depend on team size (Major 2). No hypotheses or decision rules were fixed for it (Major 6). |
| M1(c) gadget reuse of host properties, positions, interacting defects, wider d | **Partly resolved** | E4b widens ℓ to 0..5, and E8 allows up to three interacting changes. The E2 gadgets are unchanged (fresh properties, no host interaction), which is acceptable now that E2 is framed as a per-class test. E4b is not a measurement (Major 4). |
| M1(d) ground truth independent of the checker | **Partly resolved** | Symptom ground truth in E8 is the exact semantics, cross-checked against the replay oracle on all 840 teams (0 disagreements). Depth and minimal slices still come from the checker's own exhaustive confirmed slice enumeration. Confirmation is checked against the run oracle only on slices of size ≤ 2-3 of 3-7-node teams. This is stated in Threats, which is acceptable. Keys deeper than K are silently dropped from the hidden-key denominator (Major 2c). |
| M2 plan adherence | **Partly resolved** | The pre-registered metric is now reported next to the primary key (B1 20.0% on hidden classes, 100% on S6b). K = 6 is used as planned, Holm is applied to H2.2, D5/D6 are added, and "pre-registered" was dropped from the paper. However, the response matrix says F1, witness length and runtime Wilcoxon are "logged", and they are **not** in the deviation log. Explanation size, runs enumerated and the E7 join-policy-mix sensitivity are also not logged. `experiment_plan.md` is still headed "pre-registered before any experiment was run". Every deviation, the freeze date and the final runs all carry the same date (2026-11-04). The paper no longer reports a decision per pre-registered hypothesis (H2.3, H3.2 and H3.3 are not named). |
| M3 baselines | **Largely resolved** | B6, B2-dev and B2+shrink were added, with per-class localization (Table "loc_class") and B5/B6 columns in E3. The S4 weakness is reported. These baselines change the paper's story (Major 1, Major 3), and the text has not fully caught up with them. |
| M4 statistics | **Largely resolved** | Degenerate tests were replaced by counts and Clopper-Pearson bounds. The cluster bootstrap resamples hosts, E5 time-outs are censored at the budget, and detection is counted over all teams. Remaining: E8 rates carry no intervals and no host clustering, although each of 280 hosts is mutated three times (Minor 3). |
| M5 E3 protocol | **Partly resolved** | P3 is applied consistently, debate has a revision round, the ChatDev sentence is corrected, f = 0 is reported, and B5/B6 columns are added. Not done: a second encoder, an agreement statistic, a traceability table, and validation against traces. The abstract now makes a claim that the B6 column refutes (Major 1a). |
| M6 claims outrun evidence | **Resolved in title and scope; partly in abstract/conclusion** | The title and scope paragraph are properly rescoped to declared-contract models. The conclusion still generalizes ("about a third of the symptoms are hidden") beyond an 8-12-node synthetic benchmark (Major 2). |
| M7 RQ3 | **Largely resolved** | H3.1 is stated as not supported under the pre-registered rule, and the refinement is labeled exploratory. E6 extends to 80 nodes and reports that incremental re-verification is slower in 18.1% of changes. The E5 class/seed confounding is stated as a threat but not fixed. New factual errors appear in the RQ3 answer and the Discussion (Major 5). |
| Minors 1-19 | **Mostly resolved** | Precision levels, B1 column, naming, Holm, the exhaustive competitor row, CP bounds, survivorship wording, detected/all, float placement and diagnosis accuracy are fixed. |
| Artifact provenance | **Not resolved** | All result files still record commit `c223880` with `dirty_worktree: true`. The code is now committed (`b5ae7c8`), and I confirmed that E4b and E8 regenerate identically from it, but no clean-commit run, tag or DOI exists. |

---

## Strengths

1. **E8 is a real improvement.** Symptoms arise from operators rather than templates, and their class and depth are measured, not chosen. Ground truth is the exact semantics, and an independent oracle agrees on every team. The per-operator breakdown is informative: relaxing an `all` join produces hidden symptoms 66.3% of the time, against 17.6-34.9% for the other operators.
2. **Strong baselines, reported honestly.** The authors report that B6 detects every hidden key in linear time, that B2+shrink localizes better than SL (exact 100% vs 86.9-91.4%, Â12 = 0.96), and that whole-team checking is the cheapest method on switch-free teams. Few papers report baselines that beat their own method.
3. **Confirmation fixes the precision problem.** Raw SL produces 107 false keys out of 1,749 on E8 and 2.9% false keys on wild teams. Confirmation removes all of them. This is now the paper's clearest empirical contribution over B6.
4. **Better statistical practice.** Counts with exact bounds replace ceremonial tests. The paper adds a cluster bootstrap over hosts, censored slopes reported next to finished-only slopes, and detection over all teams.
5. **Exemplary replication.** The package is still one-command and deterministic. I regenerated E4b and E8 from committed code, and both are byte-identical at the row level (see Artifact check).

---

## Major concerns

### M1. The abstract and conclusion still contain claims that the paper's own data contradict, or that hold by definition

(a) **"6 [designs] contain a defect that only multi-agent slices reveal"** (abstract; RQ2 answer box). Table "Encoded Published Designs" shows that **B6 reports the key in all six** hidden-finding designs, and so does `resArchHiddenMust = 6`. B5 also reports it in five. A global must-analysis is not a multi-agent slice. The accurate statement is "a defect that agent-level analysis does not report". Slices add the *localization* of these defects, not their detection.

(b) **"agent-level analysis finds none of them"** (abstract, intro, RQ2 box, conclusion). In E8 a key is *hidden* iff its depth is ≥ 2. Depth is the size of the smallest *confirmed* slice in the exhaustive enumeration (`e8_mutation.py`: `depth = ... min(size(s) for s in gt[k]['minimal'])`), and that enumeration includes all singletons. Confirmed B1 is exactly the confirmed singleton family. So B1's hidden recall is 0% **by definition**: no data could have produced any other value. The paper admits this for E2 ("a consequence of Theorem 4a") but presents the identical tautology as an E8 finding. The informative numbers are the *share* of hidden keys (32.4%) and the 105 of 684 unclean teams (100 of them unsafe) that a confirmed agent-level check would declare clean. Raw B1, which is not definitionally tied to the ground truth, finds 1 of 500 hidden keys and reports 84 false keys.

(c) **"slices find them without false findings and name the few agents involved, which neither a whole-team witness nor a global must-analysis does"** (Conclusion). The paper's own best localizer is a whole-team witness shrunk slice by slice: 100% exact in E2 and E8, against 86.9% and 91.4% for SL, with Â12 = 0.96 in favor of shrinking. Detection without false findings is also achieved by the exact whole-team checker B2, which *is* the ground-truth semantics, on every E8 team (all of them have ≤ 12 nodes). Table "mutation" leaves B2's false/reported cell as "--" when it should read 0. The defensible claim is narrower. *Confirmed slice checking*, used either as a strategy family or as a shrinking procedure on top of a whole-team or must-analysis detection, gives sound findings and minimal localization. Whole-team witnesses without slices (the deviation set) and must-analysis do not. The Discussion says roughly this. The abstract and conclusion do not.

**Required.** Rephrase (a) as "agent-level analysis does not report". State in the abstract and the RQ2 box that the B1 = 0% result follows from the definition of depth, and report the team-level count (105 teams declared clean, 100 of them unsafe) instead. Rewrite the conclusion sentence to credit B2+shrink, and fill B2's row in Table "mutation" with 0 false keys.

### M2. The E8 benchmark is small, and its headline rates depend on team size

- **Size.** E8 teams have 6 or 10 inner nodes (8-12 nodes in total). That is smaller than the E2 small benchmark (7-21 nodes) and far below E5 (up to 5,011 nodes). The paper's own Threats paragraph says "teams in the conformance and mutation experiments are small". Yet the abstract reports "32.4%", "100%" and "91.4%" as properties of "teams with naturally arising defects", and the conclusion turns this into "about a third of the symptoms are hidden".
- **Size dependence in the shipped data.** Splitting the shipped E8 data by size: hidden share is 28.2% at 6 inner nodes and 36.4% at 10. SL exact localization is 96.7% at 6 and 87.5% at 10.
- **Size dependence beyond the shipped range.** I ran the authors' own `e8_mutation.run` from committed code, unchanged, in a scratch copy on new seeds (100-103, all 7 topologies, m ∈ {2, 3}, 56 teams per size):
  - **14 inner nodes (16 total):** hidden share 54/135 = 40%; SL exact 50/54 = 93%; shrink exact 54/54; B6 false 12/147.
  - **30 inner nodes (32 total, so K = 5):** hidden share 65/158 = 41%; **10 further keys (6.3%) have no confirming slice of size ≤ 5** (depth > K); SL exact drops to **45/65 = 69%**; shrink stays at 65/65; B6 false 1/159; slowest team 95 s.

  This exploratory sample is small, but it already shows that the 91.4% headline does not carry over to 32-node teams, and that the hidden share rises with size.
- **(c) Deep keys are silently excluded.** `depth = None` keys are neither "depth 1" nor "hidden" in `process_results.py`, so they drop out of the hidden-key denominator and the localization metrics. The paper defines `resMutDepthDeep` but does not discuss it. The plan says depth > 6 "is recorded as '> 6'". The paper must count these keys as hidden with depth > K.
- **Planned vs. applied changes.** The paper says "each team then receives one to three random engineering changes". In fact **97 of the 840 teams received no change** (the drawn operator was inapplicable or produced an invalid team), and 216 received fewer than planned (`ops` length vs `m`). These teams are in the denominator "840". The prevalence figure also depends on the uniform operator mix (relax-join alone accounts for 339 of the 500 hidden keys).
- **No uncertainty.** Each host is reused for m = 1, 2, 3. A cluster bootstrap over the 277 hosts with unclean teams gives a hidden share of [28.9%, 36.2%] and SL exact of [87.5%, 94.6%]. Neither interval is reported.

**Required.**
- Extend E8 to at least 20-40-node teams, the range of the E2 medium benchmark. Report hidden share, SL/B2+shrink exact localization and B6 false rate as a function of size, with cluster-bootstrap intervals.
- Count depth > K keys as hidden and report them.
- Report applied operator counts, and exclude or separately report zero-change teams.
- Remove "about a third" from the conclusion, or qualify it with the operator mix and size range.
- Present the per-operator rates as the primary result, since they do not depend on the mix.

### M3. The method as claimed (confirmed SL) is never costed beyond toy sizes, and the cost comparison with the stronger pipelines is missing

- **Confirmation needs whole-team searches.** Confirmation (`analysis.lift`) is a search over runs of the *whole team* (budget 2·10^5 runs per witness, one or more lifts per raw finding). E5 explicitly "measures raw slice analysis; confirmation adds one lift search per finding". So every claim in the abstract about the confirmed method (no false findings, 91.4% exact) is supported only on teams of ≤ 21 nodes, and its scalability is unknown. On the mixed topology the whole-team checker already times out on 36 of 90 teams. A whole-team lift search could plausibly hit the same wall, which would make "needs no whole-team run" (Discussion) misleading.
- **No time comparison on E8.** E8 records no time at all. The paper's practical recommendation ("for diagnosis, the most precise localization ... came from a whole-team witness shrunk slice by slice"; "the combined strategy ... is cheaper per defect when many defects are present") has no cost data behind it. One relevant pipeline is never evaluated: **B6 detection (linear, recall 99.9-100%) followed by confirmed shrinking of each reported key.** It would remove B6's false keys (unconfirmable keys are discarded) and localize exactly, without enumerating any strategy family. If this pipeline matches SL on every metric at lower cost, that is an important finding for the paper's positioning.
- **Detection at scale.** In E5, B6 detects 90/90 mixed and 270/270 switch-free defects at 2.3 s and 1.2 s respectively at 5k nodes. SL detects 58/90 and 255/270. At scale, the detection story favors the baseline.

**Required.**
- Run E5 (or a subset up to the size where B2 still finishes) with confirmation switched on. Report lift time, lift budget exhaustions and confirmed detection over all teams.
- Record wall time and slice/lift counts in E8.
- Add the B6 + confirmed-shrink pipeline (and B2 + shrink where B2 finishes) as baselines in E5 and E8, and compare cost per key.

### M4. E4b demonstrates convexity; it does not measure it, and it does not test the "not team size" claim

All 600 E4b teams give depth exactly ℓ + 2 for S4/S6a/S6b and exactly 2 for S2/S3. There is zero variance in every (class, ℓ) cell. The gadget places ℓ relay nodes on the only path between the two interacting components, and every convex slice that contains both endpoints must contain all of them. So "depth = ℓ + 2" follows from Definition (convex slice) plus the gadget shape, much as the round-1 saturation result followed from `randint(0, 2)`. The experiment is a useful sanity check of the implementation, but "the depth needed is now a measurement" overstates it.

Moreover, E4b uses a single host size (5 inner nodes; team size co-varies with ℓ, from 10 to 22 nodes) and only two topologies (chain, fork-join). The claim "depth is set by the distance between the components whose relationship is wrong, *not by the size of the team*" (RQ3 box, Discussion) is therefore untested. The size of the team is not varied independently of ℓ.

**Required.**
- Present E4b as a confirmation that the implementation respects the convexity argument, and give that argument as a proposition.
- To support the team-size claim, vary host size independently of ℓ (e.g. 5/20/40 inner nodes at fixed ℓ), or show the depth distribution of E8 keys against team size and against the graph distance between mutated nodes. The latter would make depth an actual measurement.

### M5. Factual errors in RQ3 and the Discussion

- **RQ3 answer box:** "Small slices (singleton, window-2, band) scale polynomially to 5,011 nodes and **never time out on mixed teams**." Table "scalability": band-1 times out on **4/90 mixed** teams, and its censored slope is 2.36 [2.17, 2.54], which is above the pre-registered 2.
- **Discussion:** "window-2 ... **never timed out**". Table "scalability": window-2 has 1/270 time-outs on switch-free teams.
- **Text vs. table on SL.** The E5 text says SL "times out on 32 teams" (mixed) and the box says the same. The RQ3 box also says whole-team checking times out on 36. Both match the table, but the box still calls the small strategies polynomial without the band-1 exception.
- **Statement:** "Each team then receives one to three random engineering changes". This is false for 97 teams (M2).

**Required.** Correct these statements. Have `process_results.py` generate the "never" claims from the data, or drop them.

### M6. E8 and E4b were designed after the first round, but nothing marks them as exploratory, and the plan record is incomplete

- **No a priori criteria.** E8 is now the primary evidence for RQ2 and the source of the abstract's numbers, but it has no hypotheses, decision rules or stopping criteria, and its design was fixed after the authors had seen the round-1 critique and their own results. That is legitimate, but the paper should say plainly that E8 and E4b are post hoc and exploratory, and that the only confirmatory analyses are those in the original plan.
- **Deviation log gaps.** The response matrix says the omission of F1, witness length and runtime Wilcoxon was "logged". It was not: D6 lists only the second encoder, trace validation, E5 crossing and the E6 change mix. Explanation size, runs enumerated and the E7 join-policy-mix sensitivity are also missing.
- **Hypothesis verdicts.** The paper no longer gives a verdict for H2.3, H3.2 and H3.3. H3.2 (saturation) is now meaningless, and D5 says so, but the reader needs a table listing each pre-registered hypothesis, its decision rule, and the outcome (supported / not supported / not evaluable by design / dropped).
- **Plan header.** `experiment_plan.md` still begins "pre-registered before any experiment was run", which contradicts the paper's corrected statement.

**Required.**
- Add a hypothesis-outcome table to the paper.
- Label E4b and E8 as exploratory.
- Complete the deviation log, and correct the plan's header.

### M7. E3 remains a single-encoder exercise, and its most visible claim is unsupported (see M1a)

The response declines a second encoder and a traceability table as "out of scope (no LLM runs)". Neither requires running an LLM: both concern how the published papers are read. The f = 0 column shows 8 of 9 designs safe, so the E3 findings are almost entirely the P3 + f = 1 question "does a critical claim rest on one model?". The single-encoder threat is now stated, which I appreciate. Still, the E3 count appears in the abstract.

**Required (one of the following):**
- (i) Add a second independent encoder for at least the six designs with hidden findings, with agreement on node, edge and contract, and a traceability table (node → source section) in the supplementary material.
- (ii) Remove the E3 count from the abstract and present E3 as illustrative case studies.

---

## Minor concerns

1. **Table "mutation".**
   - Give B2's false/reported value as 0/n rather than "--".
   - Add rows for B2-lineage, and for B3 if it was run.
   - The "Exact loc." column for B1-raw is "0.0" over n = 1, so print n.
2. **Table "mutation_by_op".** Teams carry up to three operators, so the rows are not disjoint, and one hidden key is attributed to every operator in its team. Add a single-operator subset (m = 1 with one applied change, 211 teams) for a clean attribution.
3. **E8 intervals.** Report cluster-bootstrap CIs for every E8 rate (hidden share, exact localization, B6 false rate), clustering on host (topology, n, seed).
4. **B6 false findings are concentrated.** The 45 false B6 keys occur in 28 of 684 unclean teams. State this at team level as well, and characterize which structures cause them (switch-induced unreachability?). On my 32-node sample B6's false rate fell to 1/159, so "2.8%" is also size-dependent.
5. **H2.2 effect sizes.** Â12 = 1.00 against B2-lineage and B2-dev is trivial, because both have exact = 0% by construction. Report Â12 against B3 and against B2+shrink, which has a negative effect for SL. These are the informative ones.
6. **Localization "precise" for region = 100% while "exact" = 0%.** Explain this in the text: region slices contain the root cause but never equal a minimal slice.
7. **"Exact" depends on K.** On teams > 16 nodes, K = 5, so a top slice of size 6 that is in fact minimal would count as not exact. State how such cases are scored.
8. **E5 class/seed confounding** is acknowledged but trivially fixable, since E5 runs in minutes. Cross class with seed.
9. **E6.** Report time saved per change kind, not just the share of slices saved. A median speed-up of 1.9× with 18.1% slower cases is the cost result that matters to practitioners.
10. **Abstract: "reports 2.8% false findings".** This is a key-level rate on 8-12-node teams. Say so, or give the team-level rate (28/684 teams).
11. **Intro "Main results".** "Small slices scale to thousands of agents" refers to raw (unconfirmed) slices. Say so.
12. **Threats.** Add: confirmed analysis unevaluated at scale (M3); E8 size range and operator mix (M2); E8/E4b post hoc (M6); depth > K keys excluded (M2c).
13. **PDF/tex out of sync.** `main.tex` is newer than `main.pdf`. Rebuild before resubmission.

---

## Artifact check

**Environment.** `.venv` Python 3.12, Linux/aarch64, 20 cores. Repository HEAD `b5ae7c8`; working tree differs from HEAD only in `README.md` and one word of `main.tex`.

**What I ran (all read-only with respect to the repository):**

| Command | Result |
|---|---|
| `.venv/bin/python -m pytest -q tests` | 38 passed in 1.2 s |
| `git archive HEAD` of `slicing/ experiments/ tests/` into a scratch copy; ran `e4_depth_sweep.py` and `e8_mutation.py` there | Row data **identical** to shipped `results/e4_depth_sweep.json` and `results/e8_mutation.json` (E4b 1.8 s, E8 0.7 s wall) |
| Independent recomputation script over `results/e8_mutation.json` | All E8 macros match: 840 teams, 684 unclean, 638 unsafe, 1,542 keys, depth histogram 1042/414/49/17/13/7, 500 hidden (32.4%), 233 teams with hidden, 105 hidden-only; B1 0/500; B1-raw 1/500, 84 false; SL 500/500, 0/1,642 false, exact 457/500 = 91.4%; SL-raw 107/1,749 false; B6 500/500, 45/1,586 false; B5 359/500, 544/998 false; B4 0/500, 22/691; shrink exact 500/500, minimum 481/500, median 13 checks (mean 13.7); deviation set exact 9/500 = 1.8%; replay oracle 840/840 agree |
| Recomputation over `results/e4_depth_sweep.json` | Depth = ℓ + 2 (S4/S6a/S6b) and 2 (S2/S3) in all 600 teams, zero variance per cell; teams have 10-22 nodes, host fixed at 5 inner nodes |
| Exploratory: authors' `e8_mutation.run` on new seeds at 14 and 30 inner nodes (56 teams each) in the scratch copy | 16 nodes: hidden 40%, SL exact 93%, shrink 100%, B6 false 12/147. 32 nodes: hidden 41% plus 6.3% of keys deeper than K = 5 (all detected by SL and B6, none by B1); SL exact **69%**; shrink 100%; B6 false 1/159; max 95 s per team |
| Cluster bootstrap over hosts (E8) | Hidden share [28.9, 36.2]%, SL exact [87.5, 94.6]% |
| Spot checks of tables against macros/JSON | Tables "mutation", "mutation_by_op", "localization", "loc_class", "recall", "scalability", "architectures", "arch_sensitivity" and "alarms" match the macros |

**Discrepancies and issues:**
1. The abstract and RQ2 box ("only multi-agent slices reveal") contradict the B6 column of Table "architectures" (6/6 "yes") (M1a).
2. B1 = 0% on hidden E8 keys holds by definition of depth (M1b).
3. The conclusion's "neither a whole-team witness ..." contradicts B2+shrink = 100% exact (M1c).
4. 97/840 E8 teams have no applied change, and 216 have fewer than planned. The text says every team receives 1-3 changes (M2).
5. Depth-None keys are excluded from E8 metrics. There are none at 8-12 nodes, but 6.3% at 32 nodes (M2c).
6. The RQ3 box says band-1 never times out on mixed teams; the table shows 4/90. The Discussion says window-2 never timed out; the table shows 1/270 (M5).
7. E5 runs raw SL only, so confirmed SL has no cost data beyond 21 nodes (M3).
8. F1, witness length, explanation size, runtime Wilcoxon and the join-policy-mix sensitivity are not in the deviation log, despite the response matrix (M6).
9. Provenance: every result file still records commit `c223880` with `dirty_worktree: true`. The code is now committed (`b5ae7c8`), and E4b/E8 reproduce from it, but the authors should re-run `run_all.py` on a clean tagged commit and archive it with a DOI.
10. `main.pdf` is older than `main.tex`.

Overall the artifact remains **fully reproducible**. Every number I checked matches. The problems are in interpretation and scope, not in the computations.

---

## Scores (1 = poor, 5 = excellent)

| Criterion | Score | Justification |
|---|---|---|
| Novelty | 3 | Confirmed slices, depth and minimal confirming slices are a new and coherent angle. The strongest localizer (witness + shrink) is close to delta debugging and CEGAR-style localization, which the paper now cites. |
| Rigor | 3 (was 2) | Much improved: natural-defect benchmark, strong baselines, confirmation, censoring, proper bootstrap. It is held back by definitional headline results, a toy-size main benchmark whose rates shift with size, unevaluated cost of the confirmed method, and post hoc experiments presented as confirmatory. |
| Relevance | 3 | Relevant SE question. Evidence is limited to declared-contract models (now stated). E3 rests on a single encoder. |
| Verifiability & Transparency | 4 | Deterministic, one-command, reproduced exactly. Points lost for dirty-worktree provenance, an incomplete deviation log and the missing hypothesis-outcome table. |
| Presentation | 3 | Body text is careful and candid. The abstract, RQ boxes and conclusion still overstate relative to the tables, and there are factual "never" statements contradicted by the tables. |

---

## Recommendation

**Major revision.** The direction is right, and most round-1 concerns have been addressed in substance. However, the abstract and conclusion still make claims that the paper's own tables contradict or that hold by definition. The new primary benchmark covers only 8-12-node teams, and its headline numbers move with size. The confirmed method that the abstract advertises has no cost evaluation at scale. Most fixes are framing corrections, plus two bounded experiments (E8 at larger sizes; confirmed SL and B6 + shrink in E5/E8 with timing). I expect to recommend acceptance if these are done well.

### Top required changes
1. **Fix the claims contradicted by the data or true by definition** (M1, M5). Replace "only multi-agent slices reveal" (B6 detects 6/6) with "agent-level analysis does not report". State that B1 = 0% on hidden keys follows from the definition of depth, and use the team-level count instead. Credit B2+shrink in the conclusion. Correct the "never time out" statements for band-1 and window-2, and the "each team receives 1-3 changes" statement.
2. **Scale E8 and report size dependence** (M2). Use 20-40-node teams and report hidden share, exact localization and B6 false rate by size with cluster-bootstrap CIs. Count depth > K keys as hidden. Report applied changes and treat zero-change teams separately. Drop "about a third" or qualify it.
3. **Cost the confirmed method and the competing pipelines** (M3). Run E5 (and record E8 times) with confirmation enabled. Add B6 + confirmed shrink, and B2 + shrink where B2 finishes, and compare cost per key and detection over all teams.
4. **Reframe E4b and test the team-size claim** (M4). Present depth = ℓ + 2 as a consequence of convexity and the gadget shape. Vary host size independently of ℓ, or relate E8 depth to team size and to the distance between mutated nodes.
5. **Complete the plan record and the E3 basis** (M6, M7). Add a hypothesis-outcome table, label E8/E4b as exploratory, and log the omitted analyses (F1, witness length, explanation size, runtime tests, join-mix sensitivity). Correct the plan header. Either add a second encoder with agreement and traceability for E3, or remove the E3 count from the abstract. Re-run on a clean tagged commit and archive it with a DOI.
