# Review of TSE submission "Agent Slicing: Contracts for Sub-Teams Expose and Localize Blind Spots in Multi-Agent AI Systems"

**Reviewer B** (empirical software engineering: experimental design, benchmarks and ground truth, baselines, statistics, threats to validity, replication)

---

## Summary

The paper models a multi-agent LLM team as a DAG of agents (whose guarantees hold only if their "oracle", the underlying model, does not fail) and deterministic gates, with fork/switch routing and all/any/quorum joins. It defines *slices* (convex node sets) analyzed under a hybrid semantics in which nodes outside the slice are taken at face value, derives slice contracts, and proves eight theorems (conservativity, abstraction over partitions with an acyclic quotient, soundness, separation, localization, overlap, complexity, incremental recertification). A blind spot's *depth* is the size of its smallest manifesting slice. The empirical part has three RQs: RQ1 (formal foundation), checked with 15 Z3 obligations, 6 proof mutants and brute-force conformance on 20,000 random small teams; RQ2 (detection and localization), checked on 4,480 generated teams with one injected defect each (11 defect classes, 4 decoy classes, clean teams) against five baselines (B1 agent level, B2 exact whole-team checker, B3 random convex slices, B4 lint, B5 smell detector), plus encodings of nine published designs (E3); and RQ3 (cost, slice size, evolution), with scalability up to 5,011 nodes (E5), a slice-size sweep (E4), 1,311 evolution steps (E6), and sensitivity/ablation (E7). Headline numbers: 45.5% of injected defects are hidden at agent level; B1 finds 0% of them and SL finds 100%; B2 detects all of them too but its explanation covers 0.92 of the team against 0.21 for SL; SL returns an exact minimal slice in 86.9% of cases; 7 of 9 encoded designs have a defect only slices reveal.

The formal contribution looks substantial, and the artifact is unusually clean and reproducible. (I leave a detailed check of the proofs to the formal-methods reviewer.) The empirical part is a different matter. Most of its quantitative results are fixed by how the benchmark was built: the class mix, the gadget shapes, the gadget depth parameter, and a ground truth computed with the same slicing machinery under evaluation. The statistical tests are applied to outcomes that are deterministic per class. The localization baseline is a weak version of what a whole-team checker could provide. The E3 findings follow largely from the encoding protocol. Several departures from the pre-registered plan are not logged, and one of them changes a headline result. Below I describe each problem and the change I need.

---

## Strengths

1. **Exemplary replication package.** One command regenerates every number, table and figure. Result files record environment and seeds, and the paper's numeric block is generated rather than typed. I re-ran parts of the pipeline and got identical outcomes (see Artifact check). That is well above the TSE norm.
2. **Independent oracles for the semantics.** A model oracle that enumerates all contract-respecting evidence assignments and a replay oracle that shares no code with the checker's enumerator are good practice. Proof mutants show the SMT obligations are not vacuous.
3. **Honesty in places.** The authors admit that H2.1 is "close to guaranteed by construction" (p. 10), that topology uniformity is "partly an artifact of injection" (p. 11), that H3.1 is only partly supported, and that the whole-team checker is cheaper on switch-free teams. They also report a 3.0% false-finding rate on unstructured teams. These admissions are welcome. The problem is that the abstract, the introduction and the RQ answer boxes do not carry the same caveats.
4. **Decoys and ablations.** Including decoys (safe teams that look suspicious) and semantic ablations (joins treated as `all`, no fault reasoning) is the right instinct for showing that each part of the semantics matters.
5. **The research question is relevant.** Whether a composition of fallible agents justifies the team's claims before any run is a timely SE question.

---

## Major concerns

### M1. The benchmark fixes the RQ2/RQ3 results by construction, and the ground truth is computed by the method under test

The core quantitative claims (45.5% hidden, B1 = 0%, SL = 100%, saturation at k = 4, topology invariance) follow directly from the generator and injector code:

- **Host teams cannot interact with the defect.** `slicing/generator.py::assign` draws every requirement from a sound must-analysis lower bound and creates hosts with **no critical goals** (`Team(..., goals, (), ...)`). All symptoms therefore come from the injected gadget. `slicing/injector.py` builds each gadget from **fresh property names** (`crit`, `tests_pass`, `merged_fact`, `reviewed`, `rev0..2`, `shared_llm`), mostly in a "release stage" bridge in front of OUT. A gadget therefore never shares a property with its host, so detection reduces to finding a fixed template inside an inert host. This explains why Table IX gives identical numbers for every topology (region = 40.0% on all seven; B5 = 80.0% on all seven).
- **The hidden rate is the class mix.** 45.5% is exactly 5/11: the benchmark injects 11 defect classes in equal numbers, 5 of which are hidden by construction (700/1540 in `results/e2_detection.json`). Likewise, "recall 54.5% at k = 1" (p. 11) is 6/11. These numbers say nothing about how often blind spots occur. Yet the abstract and the RQ2 answer present 45.5% as a finding.
- **Saturation at k = 4 comes from the injector parameter.** The injector draws the hand-off length as `d = rng.randint(0, 2)`, and the S4/S6a/S6b gadgets have depth d + 2 (≤ 4). Table XV shows exactly this: depth 2/3/4 counts of about 1/3 each, nothing at depth 5. So "detection saturates at k = 4" (H3.2, the abstract's "Detection saturates at slice size k = 4", and the RQ3 answer) restates `randint(0, 2)`. Window-2 recall on S4/S6a/S6b (34.6/28.2/34.6%) is simply the share of d = 0 draws.
- **The ground truth comes from the method being evaluated.** In `experiments/e2_detection.py`, depth, the "true minimal manifesting slices" (`gt_mms`) and therefore the localization metric "exact" all come from `fam_findings(sl.exhaustive(t, 5))`, i.e., from the same hybrid-semantics slice checker (`sem.findings`) that SL uses. "Exhaustive-k is exact by definition" (p. 11) is true because the yardstick is exhaustive-k. The only independent support is the E1 conformance check of hybrid vs. replay semantics, and that check covers slices of size ≤ 3 on teams of 3-7 inner nodes. The plan also promised that GT keys would be verified "by the exact semantics". That holds for the symptom keys (`gt_ok`), but not for depth or minimal slices.
- **One fixed shape per class.** The mechanism diagnosis that "matches the injected class in 100.0%" (p. 11) is a rule-based classifier evaluated on 11 hand-written gadget shapes. B2's diagnosis also assigns the correct class to all hidden cases in the raw data (I checked S2-S6b). The metric does not discriminate between methods.

To gauge how much this matters, I ran a small exploratory check in memory (no files changed). On 1,500 of the authors' own random "wild" teams (`conformance.wild_team`, 5-7 inner nodes), with symptoms arising naturally rather than injected, 1,476 teams were unsafe with 7,309 symptom keys. Of these keys, **86.9% have depth 1** and 12.6% have depth ≥ 2; only **28 of 1,476 unsafe teams (1.9%)** have *only* hidden keys. On these teams the SL family found all keys, but **6.7% of its reported keys were not symptoms of the team**. The paper reports "precision 100%" on the benchmark. Wild teams are no more realistic than the benchmark, but they show that the 45.5% / 100% precision picture is a property of the injected benchmark.

**Required changes.**
(a) Remove prevalence claims (45.5%, "saturates at k = 4") from the abstract, introduction and RQ answer boxes, or state explicitly that they are parameters of the benchmark design.
(b) Add a non-template benchmark: naturally occurring symptoms in random teams of realistic size, and *mutation-based* defects (random contract, join, routing and oracle mutations of host teams) whose class and depth are not chosen by the experimenter. Report the resulting depth distribution and the recall, precision and localization of every checker on it.
(c) In the injected benchmark, let gadgets reuse host properties, place them at random positions (not only a release stage before OUT), allow multiple and interacting defects per team, and draw gadget depth from a wider range (e.g. d ∈ {0..6}), so that saturation becomes a measurement.
(d) Compute ground-truth depth and minimal manifesting slices with the independent replay oracle (or at least cross-check a large sample against it), and state clearly which ground-truth parts are independent of the checker.

### M2. The plan was not followed, one undeclared change alters a headline result, and the pre-registration cannot be verified

I compared `docs/TSE/experiment_plan.md` with the paper and the code:

1. **The detection metric changed.** The plan states: "a checker *detects* an injected defect iff it reports at least one key in K\*". The paper (Sec. IV-B, Metrics) uses "the defect's primary symptom key". For S6b the injector records two GT keys, and the primary is the goal key. In the raw data, **B1 reports a ground-truth key (the `assume` key) on 280/280 S6b teams.** Under the pre-registered metric, B1's S6b recall is 100%, not 0%. The claims "agent-level analysis finds 0.0% of the hidden ones" (abstract) and "B1 finds none of them" are therefore true only under the changed metric. The paper half-acknowledges this in the S6b row of Table II, but the change is not in the deviation log. E5 (`experiments/e5_scalability.py`) uses the *any-key* definition, so the two experiments are also inconsistent with each other.
2. **The H2.1 class set changed.** The plan tests "defect classes S2-S6", which includes S5. The injector's own `HIDDEN` tuple includes S5, but `scripts/process_results.py` excludes it. With S5, SL = B1 = 100%, and H2.1 is not supported for that class.
3. **The ground-truth scope changed.** The plan says "exhaustive enumeration of convex slices up to size 6 for teams with ≤ 16 nodes". The code uses K = 5 on all small teams, which have up to 21 nodes.
4. **H2.2 is not Holm-corrected.** The plan says "same test" (Wilcoxon with Holm). `process_results.py` reports unadjusted p for the two H2.2 comparisons. With 10 seeds the minimum one-sided p is 0.00098, so the Holm-adjusted value is about 0.002, not "< 0.001" as printed (p. 10).
5. **Pre-registered analyses are missing.** These include F1, witness length, explanation size, peak memory (recorded in E5 as `peak_mb` but never reported), runs enumerated, the RQ3 runtime comparisons ("Wilcoxon signed-rank on paired per-seed medians, Holm, A12"), and the E7 "join-policy mix" sensitivity (the paper varies gates, oracles and requirement density instead).
6. **The E3 encodings changed after results were seen and in the favorable direction (D3).** MapCoder went from safe to S6a "while writing the paper", which raises the headline count "7 of 9". The fix is defensible under P3, but P3 is still applied inconsistently (MetaGPT's `TestRun` and AgentCoder's `Executor` do not require `code`; see M5).
7. **The pre-registration cannot be verified.** The plan was committed in the same commit as the results (`c223880 "INIT"`, which already contains `results/e2_detection.json`). The plan's freeze date equals the date of every deviation and of the final runs. D4 mentions "pilots" on another machine whose result files exist, which contradicts "written before any experiment ran" (p. 8). Section IV-G summarizes only the B5 deviation.

**Required changes.** Report all results under the pre-registered detection metric, and present the primary-key metric as a secondary, declared deviation. Include S5 in the H2.1 analysis or log its exclusion. Apply Holm to H2.2. Report the missing pre-registered metrics or log their omission. Make the deviation log complete (items 1-5 above), and summarize all deviations (D1-D4 plus the new ones) in the paper. Either provide independently timestamped evidence of the freeze (e.g. an OSF registration or a signed tag predating the result files) or stop calling the plan "pre-registered" and "written before any experiment ran".

### M3. The baselines are weak, and the localization comparison is against a strawman

The paper says the value of slicing is localization, not detection (since B2 detects everything and B3 random slices detect 98.6%). That makes the localization baseline decisive, and B2's localization is the weakest reasonable choice:

- B2 localizes to the **hull of the witness's contributing lineage** (`analysis.lineage_hull`). For a defect gadget placed just before OUT, that hull is essentially every ancestor of OUT, hence 0.92 of the team and 0% precision. The paper calls this "the most a whole-team counterexample says about location" (p. 8). That is not accurate. A witness explicitly names the failed oracles F, the switch choices and the quorum contributor sets. Counterexample explanation and minimization are long-standing techniques in model checking (e.g. error explanation via distance metrics, causality-based counterexample explanation, delta debugging over counterexamples). Moreover, **Theorem 5c of the paper itself states that the lineage hull manifests κ**. A greedy one-node-at-a-time shrink of that hull (ddmin over a manifesting slice) needs O(|hull|) slice checks and would return an inclusion-minimal manifesting slice by construction.
- B3 is matched in number and size to SL and already detects 98.6% of hidden defects (Table V). This shows the detection gain over *random* slicing is about 1.4 points.
- Per class, localization is not uniformly strong. On **S4, SL's exact rate is 34.3%, against 29.9% for B3 random** (my recomputation from `e2_detection.json`). The aggregate 86.9% hides this because S2/S3/S5/S6a/S6b sit at 100%.
- B5 is evaluated against decoys built as near-copies of the hidden gadgets, so its 76.5% decoy alarm rate is partly built in. In E3, **B5 flags the very key reported as "only slices reveal" in 6 of the 7 designs** (`smell: true` in `results/e3_architectures.json` for MetaGPT, ChatDev, AgentCoder, MapCoder, Debate and Agentless). This undercuts the E3 claim (see M5).

**Required changes.** Add at least (i) B2 + counterexample minimization (shrink the lineage hull while it still manifests κ; report the number of slice checks and the time) and (ii) B2 + witness-difference localization (the hull of failed oracles, deviating switch choices, partial quorum joins and the symptom node). Also consider a practical pipeline: B2 for detection, then slicing restricted to the witness hull. Report localization per class with CIs. Report B4 and B5 in Table X. Discuss and compare with contract-based architecture analysis tools (e.g. AGREE/OCRA-style compositional analysis) and with common-cause failure / fault-tree analysis for S4.

### M4. The statistics are ceremonial: tests on deterministic 0%/100% outcomes, the wrong unit of replication, and censored scalability fits

- **Table VI.** Each hidden class has SL = 100% and B1 = 0% on every seed. The Wilcoxon test then returns its floor p = 1/1024 for any effect size, Holm multiplies by 5 to give 0.005, A12 = 1.00, and McNemar gives 280/0. None of these numbers carries information beyond "the outcome is deterministic". The seeds are not the source of variation: the outcome depends on the class template, not on the seed. The paper notes the floor in Conclusion validity, but still presents H2.1 as "supported" by the test.
- **Bootstrap CIs.** CIs of [100, 100] and [0, 0] (Tables VII, VIII) are degenerate. The localization CI in Table VII resamples *teams* as if i.i.d., although the teams share seeds, hosts and templates (each seed/topology host is reused for 16 classes).
- **E5 slopes are fitted only on runs that did not time out** (`process_results.py`: `if not x['timeout']`). This is right-censored data, so the slopes are biased downward. That matters exactly where H3.1 is judged against the threshold of 2 (SL free: 1.86 [1.76, 1.96] with 14/270 time-outs). "s @5k" is likewise a median over survivors only.
- **E5 detection rates use different denominators.** For B2 on mixed teams, `det` excludes timed-out teams (54/54 = "100.0%"), while SL is computed over all 90 teams (82/90 = 91.1%). On the 54 teams B2 finishes, SL also detects 54/54. Over all 90 teams SL detects 82 and B2 detects 54. Table XII and the text ("the whole-team checker detects every defect on the teams it finishes") therefore present a comparison that is unfair to slicing, and they miss the fact that SL finds 28 defects on teams where B2 gives no verdict. At the same time, SL's "detection" on timed-out teams counts partial results, and slices that exceed the per-slice run budget are silently skipped (`limited > 0` on 41/90 mixed teams). Neither is reported.

**Required changes.** Replace the hypothesis tests on deterministic outcomes with exact counts and a clear statement that the outcomes are determined by the construction. Keep inferential statistics only where there is real variation (localization, cost), and use a resampling unit that matches the design (cluster bootstrap over hosts/seeds). For E5, treat time-outs as censored observations (e.g. fit with the time-out set to the budget and also with a censored-regression model, and report both). Report detection over a common denominator with time-outs as failures. Report skipped (`limited`) slices.

### M5. The E3 findings on published designs follow largely from the encoding protocol

- **One team encoded all nine designs.** There is no second encoder, no agreement measure, and no node-by-node traceability to the source papers. The paper says, correctly, that the contracts are "hypotheses, not measurements". But the abstract presents the outcome ("7 contain a defect that only slices reveal") as a finding about published designs.
- **Protocol P3 with f = 1 manufactures S6a.** Any deterministic gate that consumes an LLM-written artifact and certifies a critical goal is S6a by definition. Under the documented configuration **all 9 designs are unsafe**, and with f = 0 **8 of 9 are safe** (Table XI). The robustness findings are thus the statement "a critical claim that depends on one LLM output is not robust to that LLM failing", which follows directly from P3 and f = 1.
- **P3 is applied inconsistently.** The D3 fix made ChatDev's `Execute` and MapCoder's `SampleIO` require `code`, but MetaGPT's `TestRun` and AgentCoder's `Executor` still require only the tests. I re-ran both with `code` added (in memory): the class is unchanged (S6a), but AgentCoder's minimal slices change from {TestDesigner, Executor} to two minimal slices, {Programmer, Executor} and {TestDesigner, Executor}, so Table X would change.
- **Questionable encodings.** "Multi-agent debate" [42] is a multi-round protocol in which agents read and revise against each other's answers. It is encoded as three independent parallel answerers plus a majority vote, i.e., self-consistency/voting. Under this encoding S4 is the only possible outcome on a shared model.
- **The text contradicts Table XI.** Section IV-D (p. 11) says that for ChatDev and debate, "with distinct models (Table XI) the finding disappears". Table XI and `results/e3_architectures.json` show that for ChatDev with distinct oracles the team **remains unsafe** (S6a, depth 5, minimal slice {Coding, Complete, Review, Execute, Testing}).
- **The smell detector reveals most of these findings** (M3). The contrast is "slices vs. agent level", not "slices vs. anything else".

**Required changes.** Use at least two independent encoders with an agreement statistic, and publish a traceability table (node, edge, contract and its source sentence or section). Fix the P3 inconsistencies and the debate encoding (or rename it "voting"). Correct the ChatDev sentence. Report B4/B5 on E3. Rephrase the abstract claim as conditional on f = 1 and P3. Ideally, validate a few findings against observed behavior, e.g. by mapping S6a/S4 predictions to failure categories in the public multi-agent failure traces of Cemri et al. [19], or by fault-injection runs of 2-3 open-source pipelines.

### M6. The claims about "multi-agent AI systems" outrun the evidence

No language model is ever run. Properties are Boolean atoms, contracts are declared by the authors, and benchmark teams are synthetic. The title and abstract claim that slicing "exposes and localizes blind spots in multi-agent AI systems", and RQ2 asks "how many blind spots does slice-level analysis reveal". As far as the evidence goes, RQ2 is answered for the authors' formal model populated with the authors' gadgets. The construct-validity paragraph acknowledges this but does not bound the claims. There is also no evidence on usefulness: whether minimal manifesting slices help an engineer, or correspond to where real multi-agent failures originate.

**Required change.** Either (a) add an empirical link to real systems: a small study that runs fault-injected executions of encoded pipelines and checks whether observed failure propagation matches the predicted minimal slices, or a mapping study against a public failure-trace dataset; or (b) rescope the title, abstract, RQs and answer boxes to "declared-contract models of agent teams", with the generated-benchmark numbers presented as properties of the benchmark.

### M7. RQ3 evidence is mixed, and the conclusions are stated more favorably than the data support

- H3.1 as pre-registered has two parts. Part 1 is that region/window/band/goal-directed strategies have slope ≤ 2. It **fails on mixed teams** for region (2.96), goal-directed (2.75) and SL (3.01). Part 2 is that "whole-team exact checking shows super-polynomial growth or time-outs". It **fails on switch-free teams**, where B2 has slope 1.13 and takes 0.02 s at 5,000 nodes while SL takes 28.65 s (three orders of magnitude slower). The paper reports "partly supported" but then rescues the result with a post-hoc condition ("polynomial when slices have few choice points"). By the pre-registered decision rule, H3.1 is not supported.
- E6 uses teams of only 20-40 nodes. The incremental speed-up has a median of 1.8×, and **in 19% of changes incremental re-verification is slower than full re-verification** (my recomputation from `e6_evolution.json`). H3.3 is stated in terms of the share of slices re-verified, which is not cost. The 36.7% average depends on a change mix chosen by the authors, uniform over seven change kinds, without empirical grounding. Edge changes re-verify 85%.
- E5 rotates the injected class with the seed (`CLS[seed % 4]`), so class and seed are confounded, and S5/S6b are absent.

**Required change.** State H3.1 as not supported under the pre-registered rule and keep the post-hoc refinement as exploratory. Evaluate E6 on larger teams and report time-based savings (including the share of changes where incremental is slower). Ground the change mix (e.g. on version histories of open-source agent configurations) or report results per change kind only. Fully cross class with seed in E5.

---

## Minor concerns

1. **Abstract / p. 2 "Main results".** The abstract says "with no false alarm on clean and decoy teams" but omits the 3.0% false-finding rate on unstructured teams (and 9.1% of slices reporting a false key). Both should be in the abstract.
2. **Table V (p. 10).** The B1 column is computed from the `k1` checker, which exists only on the small benchmark. The SL and other columns pool small and medium. The caption says "small and medium benchmark", so the denominators differ within the table, and the abstract's "agent-level ... 0.0%" (`resRecallHiddenkOne`) is small-only. Use `singleton` for B1 on both, or state the split.
3. **Table V / Table II naming.** The class is "S1v" in Tables V and XV and "S1" in Table II and the text. Make it consistent.
4. **p. 10, H2.2.** "Wilcoxon p < 0.001" is unadjusted (see M2.4). Also, A12 = 1.00 against B2 is trivial because B2's exact rate is 0 by design.
5. **p. 9, E1.** "1,120 small benchmark teams": the small benchmark has 2,240 teams. Say which subset and why.
6. **p. 9, "176,960 comparisons".** This counts team × check, not independent tests. Also, the conformance oracles were run only on teams of 3-7 inner nodes (model oracle on 8,000 tiny teams). State that conformance on larger teams is untested.
7. **p. 11, Table VII.** "Exhaustive k ≤ 5" at 100% is the ground truth itself and should not appear as a competitor row. Add per-class rows (see M3).
8. **p. 11, Table VIII.** Report counts and Clopper-Pearson upper bounds rather than degenerate bootstrap intervals (the pre-registered H2.3 asks for a 95% upper bound).
9. **p. 12, Fig. 3.** The S2 and S3 curves coincide and are hard to tell apart. The "95% bootstrap CIs over seeds" are degenerate for S2/S3.
10. **p. 13, Fig. 4 and Table XII.** "B2 drawn only where at least half of the teams finish" and "s @5k" are survivorship statistics. Say so in the caption.
11. **p. 13, Table XII.** Add a column for "detected / all teams" (see M4).
12. **p. 14, Table XIV.** The non-convex ablation found 0 false keys on 29,675 slices, so convexity is not needed for soundness on this benchmark. The paper says so. Also test it on wild teams, where false alarms actually occur.
13. **p. 17-18, Appendix C.** "Additional Tables" is an empty heading, and Tables XV-XVIII float into the reference list. Fix the float placement.
14. **Table XVII.** The caption explains ">4e5" but no cell uses it.
15. **Sec. IV-B, Metrics.** Define precision at key level and at team level separately. "Precision 100.0% over 5,503 reported keys" holds only on the injected benchmark (see M1).
16. **Sec. IV-G Threats.** Add: ground truth computed by the method under test; benchmark parameters determining prevalence and saturation; single encoder for E3; the metric change; censoring in E5.
17. **Related work.** Add counterexample explanation/minimization in model checking, contract-based architecture analysis (AGREE, OCRA), and common-cause failure analysis in fault trees. These are the closest competitors for localization and for S4.
18. **Diagnosis accuracy "100.0%" (p. 11).** This is non-discriminating (B2's diagnosis is also correct on all hidden cases). Drop it or evaluate it on non-template defects.
19. **E7 sensitivity (Table XVIII).** It varies host parameters while the gadget is fixed, so invariance is expected (M1). Varying gadget parameters would be informative.

---

## Artifact check

**Environment.** Repository at `/home/majid/Documents/PROJECTS/AgentSlicing`, `.venv` with Python 3.12.3 on Linux/aarch64, 20 cores.

**What I ran**

| Command | Result |
|---|---|
| `.venv/bin/python -m pytest -q tests` | 35 passed in 0.37 s |
| `.venv/bin/python experiments/run_all.py --quick` | proofs, mutants, tests, running example, E1, E3 and process all "ok", 10.9 s wall. Rewritten outputs were identical to the shipped ones except timing fields and one generated macro (`\resProofSeconds` 0.02 → 0.01, which also changes `main.tex`'s generated block). I restored the original files afterwards. |
| E2, E6, E7 re-run in a scratch copy of the code (outside the repo) | `e2_detection.json`, `e6_evolution.json` and `e7_ablation.json` are **identical** to the shipped files once timing/env fields are ignored. E2 takes about 3 s, E6/E7 about 1 s each. |
| Recomputation from raw JSON (independent script) | see below |
| In-memory exploratory checks (no files written) | E3 P3-consistency variants (M5); natural-symptom depth on 1,500 wild teams (M1) |

**Numbers verified against `results/*.json` (all match the paper):**
45.5% hidden (700/1,540); SL precision (5,503 keys, 0 false); Table VII (SL exact 86.9%, size 2.8, ratio 0.21; B2 ratio 0.92, size 12.4; B3 exact 49.8%, ratio 0.34; window-2 n = 416; region n = 280); medium benchmark (SL 0.088 / 87.0%, B2 0.888 / 28.2 vs 2.7 nodes); Table VIII (B5 6.1% clean / 76.5% decoy, all others 0); B5 hidden recall 80.0%; Table IX (region 40.0%, B3 97.5-100%); Table X/XI rows; E5 (max 5,011 nodes; SL detection 96.7% free / 91.1% mixed; time-outs 14/270, 30/90, B2 36/90; exhaustive-3 run on 200, skipped on 160); E6 (1,311 changes, 100% agreement, 36.7% non-chain, 45.8% chain, median speed-up 1.8×); E7 (17,244/573,242 = 3.0%; 12,763/140,625 = 9.1%; 3,240 sensitivity teams; 29,675 non-convex slices, 0 false keys); E1 (20,000 wild, 1,120 bench, 8,000 model-oracle teams, 0 mismatches; 379/500 satisfiable, 0 disagreements).

**Discrepancies and issues found:**
1. Under the pre-registered detection metric, B1 detects 280/280 S6b teams (M2.1).
2. The ChatDev text contradicts Table XI and the JSON (M5).
3. H2.2 p-values are unadjusted, against the plan (M2.4).
4. Table V's B1 column is small-benchmark only (Minor 2).
5. E5's B2 detection excludes time-outs, and slopes are fitted on non-censored points only (M4).
6. In E6, incremental is slower than full re-verification in 19% of changes (M7).
7. SL exact localization on S4 is 34.3% vs. 29.9% for random slices (M3).
8. Every result file has `"dirty_worktree": true` and records commit `c223880`, which does **not** contain the code that produced the results: `experiments/architectures.py` and `scripts/process_results.py` are modified, and `experiments/run_all.py`, `experiments/running_example.py`, the E5-E7 results and `requirements.txt` are untracked. Please tag a clean commit and archive it with a DOI (Zenodo/Software Heritage).
9. Repository hygiene: compiled `__pycache__/*.cpython-313.pyc` files are committed although the study uses Python 3.12. The initial commit contains an unrelated manuscript directory under `docs/TSE/`. Git metadata reveals the authors' identity, which conflicts with "Anonymous Authors" if double-anonymous review is intended.
10. The pre-registered plan and the results were committed together (M2.7).
11. Exploratory (mine, not the authors'): on 1,500 random wild teams, 86.9% of natural symptom keys have depth 1, only 1.9% of unsafe teams have exclusively hidden keys, and the SL family's reported keys are 6.7% false.

Overall, the artifact is **reproducible**: everything I re-ran matches exactly. The issues are with what the experiments measure, not with whether they can be re-run.

---

## Scores (1 = poor, 5 = excellent)

| Criterion | Score | Justification |
|---|---|---|
| (i) Novelty | 3 | Slices as first-class contracts with a hybrid semantics and a depth notion is a new angle for multi-agent teams. It builds on well-known assume-guarantee, slicing and common-cause concepts, and the empirical novelty is limited by the synthetic setting. |
| (ii) Rigor | 2 | The formal and conformance work is careful. The empirical evaluation has ground truth from the method under test, outcomes fixed by benchmark construction, a strawman localization baseline, ceremonial statistics, censored fits, and unlogged deviations from the plan. |
| (iii) Relevance | 3 | The question matters for SE practice, but no evidence links the findings to real LLM teams, and the E3 results follow from the protocol. |
| (iv) Verifiability & Transparency | 4 | An exemplary one-command, deterministic package that reproduced exactly. Points lost for the dirty-worktree provenance, the unverifiable pre-registration and the incomplete deviation log. |
| (v) Presentation | 3 | Clearly written and dense. Abstract and answer boxes overstate the results relative to the caveats in the body. There are text/table contradictions (ChatDev), inconsistent denominators, and float/appendix layout problems. |

---

## Recommendation

**Major revision.**

The theory and the artifact are strong enough to merit revision rather than rejection. In its current form, however, the empirical evaluation cannot support the headline claims: they come from the benchmark design rather than from measurement. A revision must (1) add a non-template, mutation-based or naturally occurring defect benchmark with ground truth independent of the slicing checker, and drop the prevalence and saturation claims that come from injector parameters; (2) restore the pre-registered detection metric and analyses and complete the deviation log; (3) add credible localization baselines (B2 + counterexample minimization, witness-difference localization) and per-class results; (4) replace the tests on deterministic outcomes with descriptive counts and handle censoring in E5; and (5) put E3 on a validated, multi-encoder footing, or rescope the claims about published and real systems.
