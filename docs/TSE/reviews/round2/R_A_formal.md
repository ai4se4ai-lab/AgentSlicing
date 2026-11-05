# Review of TSE submission (revision 1) "Agent Slicing: Localizing Blind Spots in Declared-Contract Models of Multi-Agent AI Teams"

**Reviewer A, second round**: formal methods and theory (assume-guarantee reasoning, contract theories, abstraction, program slicing, semantics of dataflow graphs)

## Summary

The paper models an LLM agent team as a DAG of agents and deterministic gates. Each component has requirements, guarantees and declared evidence. Nodes route by fork or switch, join by all, any or quorum, and agents depend on oracles that may fail, up to a budget f. An exact run semantics defines three kinds of symptom keys (assume, goal, robust). A *slice* is a convex node set, analyzed under a hybrid semantics H_σ in which outside nodes are taken at face value.

The revision answers the main round-1 objection, that H_σ is neither sound nor complete, by adding *confirmed findings* (Def. 7). A raw finding counts only if some run of T exhibits the key and that run, replayed on σ, exhibits it in H_σ as well. Depth, minimal confirming slices (MMS) and agent-level analysis are now defined over confirmed findings. The revision also makes the following changes:

- It derives per-exit slice contracts and defines exactness (Defs. 9–10 in the PDF).
- It restates T2(c) for a disjunctive exit.
- It adds a monotonicity theorem for confirmed findings (T5(c)).
- It restricts the old "fooling-set" argument to *view-disjunctive* analyses (T4(b)).
- It restates the complexity per key kind (T7).
- It extends incremental recertification to edge changes (T8).
- It adds a fault-aware must-analysis baseline (B6), whole-team explanation baselines (B2-dev, B2+shrink) and a mutation benchmark (E8).

I read the revised manuscript (22 pp.), Appendix A in full, the response matrix and the relevant parts of the artifact (`slicing/semantics.py`, `slicing/analysis.py`, `slicing/conformance.py`, `slicing/incremental.py`, `formal/prove.py`). I ran the test suite (38 passed) and wrote read-only scripts against the library. I did not run `formal/prove.py`.

The revision is a substantial and largely honest improvement. Several of my round-1 objections are fully resolved, and the paper is now much more careful about what H_σ approximates. However, I found one theorem whose stated corollary is false (T5(c), upward closure, for robust keys). The failure has a visible algorithmic consequence: shrinking returns a slice four times larger than the true depth. I also found that the implementation of confirmation is incomplete with respect to Def. 7, and that the conformance checks are scoped so they cannot see either problem. Several new results are correct but close to trivial (T2(c), T4(b)), and a central notion, depth, has no complexity result. Details follow.

## Assessment of how round-1 concerns were addressed

| Round-1 concern | Status | Comment |
|---|---|---|
| M1. H_σ neither sound nor complete; depth/MMS not semantic; true AL findings lost in larger slices | **Partly resolved** | The approximation status is now stated honestly (p. 5), and confirmation by lifting makes assume/goal depth a semantic notion. My 5-node team is Example 1. I verified empirically that confirmed assume/goal findings are monotone (0 violations over all convex slice pairs of 400 wild teams). **For robust keys the problem persists**: confirmation of a robust key in σ still depends on whether a *spurious raw* goal key appears in F(σ) (Def. 6/hybrid). As a result, true robust findings, including agent-level A4 findings, are lost in larger slices (Major 1). |
| M2. T5(c) vacuous; B2 strawman | **Resolved** | The vacuous T5(c) is gone. B2-dev and B2+shrink are meaningful baselines, and the hull row is now labelled as a reference. |
| M3. T2(c) contradicts Def. 7; C2 encodes another definition; "exact" undefined | **Resolved, but the result is now trivial** | Per-exit guarantees and exactness are defined, and C2 is re-encoded over an uninterpreted sort. The restated T2(c) is correct. It now says only that a disjunctive guarantee cannot be written as one conjunctive (A, G) pair of property sets. That is a limit of the *set-pair contract format*, not of assume-guarantee contracts, and the abstract's "exact slice contracts are relations rather than assumption-guarantee pairs" overgeneralizes it (Major 5). |
| M4. T7(a) false for robust keys | **Resolved** | The per-kind statement is correct, and I checked both robust reductions on paper. D^p-completeness is left open, which is acceptable. The well-formedness condition no longer requires liveness. |
| M5. T4(c) only static; T4(b) only disjunctive; must-analysis missing | **Partly resolved** | B6 has been added and is discussed openly, which is good. T4(c) is now proved for assume/goal keys via monotonicity. T4(b) is restated and correct, but the class it covers is so narrow that it does not include the paper's own agent-level analysis (B1), nor B5 or B6 (Major 4). |
| M6. Proof gaps, informal notions | **Partly resolved** | Model class (Def. 4), global failure sets in T2, the restricted T2(b), the cyclic example with goals, the T8 edge case, and the demotion of T1/T6 are all done. Still open: the T4(a) families are underspecified, so their "depth exactly ℓ+2" claims cannot be checked (Major 6); Def. 7 leaves the replay choice undefined for member switches unreached in ρ; the proofs of T2(a) and T8(iv) remain sketches; emergent obligations X_σ are still prose ("the slice-level conditions that exclude these states"). |
| M7. Mechanization overstated | **Partly resolved** | The wording in §IV-C is now accurate ("one-step set identities; inductions on paper"), L6 is removed and decl is explained. But the contributions still claim "full paper proofs". The monotonicity conformance check *exempts* exactly the robust case that fails. The "independent" run oracle shares `analysis.hybrid_run` with the implementation, and the dead `conformance.lifts` (which ignores the witness) is still present (Major 3). |
| M8. Positioning (OCRA, AGREE, cut sets, CEGAR, circular AG, convex subgraphs) | **Largely resolved** | References are added and differences are stated. Kurshan's localization reduction is still not cited. The comparison with OCRA/AGREE does not address that their contracts are temporal formulas, for which T2(c) has no counterpart (Major 5). |
| Minor 1–22 | Mostly resolved | Remaining: dual numbering (Minor 1), Table 6 attributions (Minor 5), "localized at its node" for static keys is still an ad-hoc rule (Minor 6). |

## Strengths

1. **Confirmation by lifting is the right fix.** It turns depth and MMS for assume/goal keys into semantic notions, and the monotonicity proof for those keys (Lemma 4 applied twice) is correct and elegant. My exhaustive random check agrees.
2. **The hybrid semantics is described honestly.** It is stated explicitly to be neither a may- nor a must-approximation (p. 5), with a concrete false alarm (Example 1) and the raw non-monotonicity example of T5(d).
3. **The complexity results are now correct** (T7(a)), including the D^p upper bound and the NP- and coNP-hardness of robust keys. Both reductions are checked against SAT in E1.
4. **The baselines are much fairer.** The must-analysis B6 and the whole-team-plus-shrink baseline are exactly what was missing, and the paper reports openly where they match or beat slicing.
5. **T8 (incremental recertification of raw findings) appears correct.** I stress-tested it with 2,400 random node and edge changes on wild teams, using *all* convex slices rather than only those of size ≤ 3, and found 0 mismatches.
6. **The artifact remains exemplary** in size, readability and regenerability. The log of the two bugs found by conformance testing is commendable.

## Major concerns

### M1. T5(c) "confirming slices are closed upward" is false for robust keys; true agent-level findings are lost and shrinking fails

T5(c) proves monotonicity for assume and goal keys. For robust keys it proves only "κ ∈ C(σ') **or** the goal key of the same property is a raw finding of σ'". It then concludes, for every key: "Hence the confirming slices of a key are closed upward". The disjunct cannot be discharged. By Def. 6 (hybrid semantics), a raw robust key of σ' requires the goal key to be absent from F(σ'). Raw goal keys can be spurious, because outside all-joins are "reached" on one input (Example 1, T5(d)). A spurious raw goal key in a larger slice therefore *suppresses* a true robust key.

**Counterexample (verified with the library).**
- s is a switch gate routing to x or to OUT.
- y is an agent on oracle o that guarantees the critical goal g.
- x is a gate with an `any` join of s and y.
- OUT is an `all` join of s and x.
- IN feeds s and y, and f = 1.

```
build([('s','gate',[],[],None,'switch'), ('y','agent',[],['g'],'o'), ('x','gate',[],[],None,'fork','any')],
      [('IN','s'),('IN','y'),('s','x'),('s','OUT'),('y','x'),('x','OUT')], goals=['g'], critical=['g'], f=1)
Sym(T)            = {(robust, OUT, g)}
C({y})            = {(robust, OUT, g)}      # depth 1 (an A4 single point of failure)
C({x,y}), C({s,x}), C({s,x,y}) = {}         # raw finding is the spurious (goal, OUT, g)
C({s,x,y,OUT})    = {(robust, OUT, g)}
analysis.shrink(T, (robust,OUT,g))  ->  {s, x, y, OUT}   (size 4; the depth is 1)
```

Over all convex slice pairs σ ⊂ σ' of 400 random wild teams (n = 5), I found **674 pairs in 16 teams** where a confirmed robust key is lost in a superset. There were 0 such pairs for assume/goal keys.

Consequences:

- **(i)** The corollary of T5(c), the RQ1 answer ("monotone in the slice") and the Conclusion ("sound, monotone confirmed findings") are false as stated.
- **(ii)** The RQ1 answer "every confirmed agent-level finding is recovered by larger slices" is false for A4 findings. T4(c) itself is correctly restricted to assume/goal keys.
- **(iii)** For robust keys, depth is *not* a semantic property in the sense of p. 7, because whether σ confirms depends on a spurious finding of σ.
- **(iv)** Shrink's guarantee depends on upward closure. With upward closure, greedy single-node removal provably reaches an inclusion-minimal convex slice: some extremal node of σ \ τ can always be removed while keeping convexity. Without it, shrink can stall at a non-minimal slice, as above. The E8 claim that shrinking is exact for 100.0% of hidden symptoms therefore needs to be re-examined for robust keys.
- **(v)** The monotonicity conformance check (`conformance.check_team`, "confirmed_monotone") explicitly excuses this case, so the 0-mismatch claim does not test the stated corollary.

*Required change.* Redefine the robust condition of confirmed findings so that it does not depend on raw goal keys of σ. One option: κ = (robust, ω, φ) is confirmed by σ iff some run of T with |F| ≤ f misses φ, its σ-replay misses φ, and (goal, ω, φ) ∉ Sym(T), or ∉ the *confirmed* findings. Then re-prove T5(c) without the disjunct, re-check monotonicity without exemption, and re-run E2/E8 and the shrink results. Alternatively, restrict the corollary, the RQ1 answer, the conclusion and the shrink claims to assume/goal keys, and report how many robust keys are affected.

### M2. The implementation of confirmation is incomplete with respect to Def. 7; depth can be silently overestimated

The text (p. 5) says the implementation "explores all witnesses of a key, not only one". `semantics.findings` stores at most `cap = 64` witnesses per key, and `analysis.lift` fixes the member switch choices of one stored witness. A key whose only liftable witness is not among the first 64 is never confirmed. In addition, a lift search that exhausts its budget returns `lifted: False` (`exhausted: True`), and no experiment counts or reports this.

**Counterexample (verified).**
- Member switches s1..sK, each routing to a_i (to OUT) or b_i (to J).
- J is an `all`-join of b_1..b_K that requires p.
- s1 claims p but requires an unprovided q.
- σ = {s1..sK}, which is convex.

In T, J is reached only when every switch picks b_i. In H_σ it is reached whenever one does. For K = 7 there are 127 witnesses, and the liftable all-b witness comes last in DFS order.

```
K=3, 6:  confirmed_findings(σ) ∋ (assume, J, p)   = confirmed_oracle(σ)
K=7:     confirmed_findings(σ) = {(assume,s1,q)}   but confirmed_oracle(σ) ∋ (assume, J, p)
```

So C(σ) as implemented under-approximates Def. 7. Depth and MMS can then be overestimated, and a hidden defect can be missed by a slice that confirms it by definition. The conformance experiment compares against the run oracle only for slices of size ≤ 2 on teams of 3–7 inner nodes, so it cannot exercise this path. Yet the SL strategy's region and goal-directed hulls on the mixed topology contain many choice points (p. 13: 225 slices exceeded the run budget).

*Required change.* Either make lifting complete: search team runs directly for each key, with member switches free and the replay check as a filter (which also removes the dependence on recorded witnesses), or state the bound as part of the definition actually implemented. In every experiment, report the number of keys affected by the witness cap and by lift-budget exhaustion. Extend the run-oracle comparison to slices with more than 6 binary choice points.

### M3. The cost of confirmation changes what "agent-level" and "scales to thousands of agents" mean

By T7(a), reachability of a node and membership of an assume key are NP-complete. Confirming even a *static* key requires deciding whether its node is reached in some run of T (Algorithm 1, line 3). Confirming a singleton's dynamic finding requires a whole-team search. Consequently:

- (a) The baseline "agent-level analysis" AL(T) (Def. 8), against which "32.4% of symptoms are hidden" is measured, is itself an NP-hard *whole-team* computation. It is no longer the cheap, local per-agent AG check that the introduction motivates. The paper should say so where B1 is introduced and where the headline numbers appear. It should also add the natural cheap local baseline (the static keys F(∅) plus raw singletons), which is reported only as "B1 raw".
- (b) "Agent-level analysis finds none of them [the hidden symptoms]" (abstract, intro, RQ2 answer) is true by definition: hidden means that no singleton confirms the key (Def. 12). It should be presented as a definition, not as a result.
- (c) "Small slices scale to thousands of agents" (Main results) and the RQ3 answer refer to E5, which measures *raw* findings only (p. 13: "confirmation adds one lift search per finding"). Each lift search is worst-case whole-team checking, and whole-team checking is exactly what times out on mixed teams. The scalability claim does not cover the method the paper reports. Either measure confirmed analysis in E5 or confine the claim to raw analysis and state its consequences.
- (d) The same applies to T8. Incremental recertification is proved for raw findings, while confirmed findings must be re-lifted after every change. For a sound update, this includes raw findings that previously did not lift, because liftability depends on T. The 1.9× median speed-up therefore does not measure what a user of confirmed analysis would pay.

### M4. T4(b) is correct but does not cover any analysis in the paper; the separation story should be restated

A view (p. 7) is a node's contract, kind, oracle, policies and the set of properties its ancestors claim. A view-disjunctive analysis flags a team iff some node's view satisfies a fixed predicate. I agree with the proof. But:

- (a) The paper's own agent-level analysis is not view-disjunctive. F({v}) contains keys at *downstream* nodes, whose existence depends on successors, outside join policies and routing (Example 1; S5 is "visible at the switch"). Confirmation consults the whole team as well. So T4(b) does not say anything about B1, nor about B5 or B6, as the paper concedes for the latter two (p. 7).
- (b) Since the view excludes oracles of ancestors, successor structure and path information, the theorem holds essentially because the view is defined too coarsely to tell the teams apart. It is a remark about an information-poor abstraction rather than a separation theorem.

The abstract's "view-local agent checks cannot separate safe from unsafe teams on these defect classes" reads as a statement about agent-by-agent checking in general.

*Required change.* Either (i) prove a lower bound for a class that contains the paper's own singleton analysis, for example "flags iff some v has a key in F({v})" or any function of {F({v})}_v, or a class of node-local monotone transfer functions over a fixed per-node domain, as suggested in round 1; or (ii) demote T4(b) to a proposition and rephrase the abstract and RQ1 answer so they say exactly which class is excluded.

### M5. The central new notion, depth, lacks a complexity result; T2(c) and "relations rather than pairs" overstate the novelty

- (a) Deciding depth(κ) ≤ k is the paper's key question, yet T7 says nothing about it. For assume and goal keys it is in NP even with k part of the input: guess σ with |σ| ≤ k and a run ρ of T, then check convexity, ρ's key and the H_σ replay in polynomial time. It is NP-hard because depth(κ) ≤ |N| iff κ ∈ Sym(T). So it is NP-complete. For robust keys, the current definition mixes in the coNP condition on raw goal keys of σ (see M1). Computing an MMS, and the approximation quality of greedy shrink relative to the minimum (96.2% "minimum" in E8), deserve a statement. Please add these results. They also make clear that exhaustive-k is not the only exact method: a SAT/SMT encoding over (σ, ρ) is natural.
- (b) T2(c) (no exact single pair for a disjunctive exit) is a three-line observation. In contract theories where A and G are predicates, for example OCRA/AGREE with LTL, or any meta-theory with assertions instead of monotone property *sets*, the guarantee (r1 ∨ r2) → g is a single exact contract. The abstract's claim that "exact slice contracts are relations rather than assumption-guarantee pairs" should be restricted to *set-valued* (conjunctive) A/G pairs. The related-work paragraph should acknowledge that richer contract languages express it directly. Note also that C2 encodes the exit guarantee `g iff r1 ∨ r2` as an axiom. The link between this formula and G_{σ,e} of the two-member slice is a paper argument and is not mechanized; please say so.
- (c) Kurshan's localization reduction should be cited alongside CEGAR.

### M6. Remaining gaps in definitions and proofs

1. **Def. 7, replay.** "The run of H_σ that makes ρ's choices on σ" is undefined for member switches and member joins that are unreached in ρ but reached in H_σ, because H_σ over-approximates reachability. The implementation uses a default. Quantify existentially or universally over such choices, and check that T5(c) is unaffected. I believe it is, since Lemma 4 only needs agreement on nodes reached in the larger run, but the proof must say so.
2. **T4(a) families are underspecified.** For S4, "separated by ℓ agents on other oracles" is not enough. If an intermediate agent guarantees something r2 requires, failing that agent's oracle makes r2 not apply. That loses the critical goal with a single failure at depth 1 (A4), and the claimed "depth exactly ℓ+2" fails. S6a and S6b have the same issue. Give the families with their full contracts. The minimality argument must also show that no slice *avoiding* both interacting nodes confirms, which the proof does not address. The text says the families are checked for ℓ ≤ 5 only; the theorem quantifies over all ℓ.
3. **T2(b).** The replacement delivers "on any nonempty subset of its exits", but σ may deliver on no exit in a run, for example an all-join behind a member switch. Show that keys are monotone in exit delivery (I believe they are: more delivered edges only add reachability and contributor options), or allow the empty subset.
4. **T2(a), T2(d).** "Content is tracked symbolically ... (its flow)" is still the whole argument for why Beh_σ is a function of entry contents. Give Beh_σ as an explicit definition (domain, codomain, what is symbolic) and a proper induction. The appendix proof is a sketch, which contradicts "full paper proofs" in the contributions.
5. **T8 (iv), edge changes.** "Taking Y as stated ... covers every member whose behavior or environment can change" is asserted, not proved. Changing an edge changes convexity, env_σ for members below v, and the outside reachability rule ("reached if one in-edge is delivered"). Each case needs an argument. My stress test found no counterexample, but a test is not a proof.
6. **Emergent obligations X_σ** remain prose. Either define each obligation as a predicate over witnesses (route, drop, cond, fault) and state a theorem relating "X_σ holds" to the absence of the corresponding class, or call them terminology.

### M7. Claims about verification should match what is checked

- The contributions say "Results with full paper proofs". T2(a,d), T4(a) and T8 are proof sketches. Please write "proofs (some sketched)" or complete them.
- "Every theorem with a computational statement is checked against brute-force oracles": the monotonicity check exempts robust keys (M1), the confirmation oracle is compared only for |σ| ≤ 2 (M2), and T4(a) is checked only for ℓ ≤ 5.
- The "independent" run oracle (`conformance.confirmed_oracle`) and the hybrid oracle both call `analysis.hybrid_run`, the same replay code the checker uses for lifting. A misreading of H_σ in `hybrid_run` would be shared. The paper's threats section mentions shared data models. Please state this specific dependence, or re-implement the H_σ replay independently in the oracle.
- Remove or fix `conformance.lifts`. It still ignores its witness and returns `key in Sym(T)`, and its docstring says "T3(b)".

## Minor concerns

1. **Numbering (pp. 5–8, 18–19).** The PDF numbers theorems 1–6 but labels them in parentheses T2–T8, for example "Theorem 1 (Slice abstraction, T2)", "Theorem 5 (Complexity, T7)". Propositions are labelled T1 and T6. The text, the response matrix and the tables use the T-labels, and the response matrix cites "Def. 8–9" for what the PDF prints as Defs. 9–10. Round-1 minor 7 asked for one scheme. Please use the LaTeX numbers throughout and drop the T-labels.
2. **p. 5, Def. 7.** "A raw finding κ with witness ρ_σ lifts if ..." never uses ρ_σ. Confirmation is a property of (σ, κ). Rephrase.
3. **p. 7, T5(b).** Correct, but note that with M1 unresolved the MMS of a robust key need not be the set of minimal elements of an upward-closed family. "Ranked by size, then by number of choice points" is an implementation choice, not part of Def. 12.
4. **p. 7, Def. 12.** "A confirmed static key ... is localized at its node" is an ad-hoc override. By Def. 7, every singleton whose replay reaches the node confirms a static key, so the MMS would be all such singletons. State this and justify the override.
5. **Table 6.** L4 is listed as used in "T4c, T5d". T5(d) is a counterexample and uses no lemma; L4 is used in T5(c) and Lemma 1. L10 "Def. 3" and L11/L12/L13 "Def. 2" are definitions, not proofs that use them.
6. **p. 4, Def. 4.** State the model's output explicitly (c(v) ∪ gua(v), so extra evidence does not flow). With that, Lemma 1 (W) is near-definitional; say so.
7. **p. 8, T7(b).** The bound on R_σ counts minimal runs. The implementation also caps witnesses per key (M2) and per-slice runs (B = 200,000). Mention both, since they change the output and not only the cost.
8. **p. 8, T8.** "Stored findings are re-confirmed after each change (one lift search per finding)" must include stored *unconfirmed* raw findings, which may become liftable after a change outside their slice.
9. **p. 5, Example 1.** Good. Also give the raw-versus-confirmed agent-level false-alarm rate on E8 next to it (6.9% raw B1 per p. 11), since it shows the example is not pathological.
10. **p. 1, abstract.** "reported findings are never false alarms": add "relative to the declared-contract model". This holds by construction (T3(b)), not empirically.
11. **p. 16, Related work.** "A minimal confirming slice of a robust key is close to a minimal cut set." Make this precise or drop it. A cut set is a set of *failing* components; a confirming slice is a set of components analyzed *exactly*, and it includes non-failing switches and joins. Under M1, robust confirming slices are not even upward closed, unlike the supersets of cut sets.
12. **p. 8, Slicing strategies.** "Shrink ... yields a slice that is minimal under single removals." Add that, given upward closure, this equals inclusion-minimality, by the extremal-node argument in M1(iv). This is worth stating once M1 is fixed.

## Scores (1 = poor, 5 = excellent)

| Criterion | Score | Justification |
|---|---|---|
| Novelty | 3 | Confirmed slice findings and depth as a semantic measure of how many components must be analyzed exactly are a reasonable, modestly new contribution over localization abstraction, CEGAR and hierarchical contracts. T2(c) and T4(b) add little, and the complexity of depth is missing. |
| Rigor | 3 | The round-1 errors (T2(c), T7(a), vacuous T5(c)) are fixed. A new false corollary (upward closure for robust keys) affects shrink and the RQ1 claims, and the implementation of confirmation does not match its definition. Several proofs remain sketches. |
| Relevance | 4 | Static compositional analysis of LLM agent pipelines is timely, and the mutation benchmark and B6 make the comparison meaningful. |
| Verifiability and Transparency | 3 | The artifact is excellent and regenerates everything. But the conformance checks are scoped so they miss both problems I found (robust exemption, |σ| ≤ 2 for the run oracle, witness cap), the oracles share replay code, and lift-budget exhaustion is never reported. |
| Presentation | 3 | Much clearer than round 1, with good notation and examples. The dual theorem numbering (Theorem 1 = "T2") is confusing, and some headline sentences restate definitions as findings. |

## Recommendation

**Major revision.** The revision fixes the most serious round-1 errors, and the notion of confirmed findings puts depth for assume and goal keys on a sound semantic footing. The formal core is not yet at TSE level of rigor, for three reasons:

1. The robust-key part of the central monotonicity theorem is false as stated, with a concrete counterexample that breaks shrinking (M1).
2. The implemented confirmation is incomplete with respect to its definition, so depth may be overestimated in exactly the choice-rich slices where it matters (M2).
3. The cost of confirmation undercuts the "agent-level" baseline and the scalability and incremental claims as currently worded (M3).

Each fix is well defined, and most are small: redefine robust confirmation, make lifting complete or report its bounds, state the complexity of depth, and restate T4(b) and the novelty claims. I expect a further revision could be acceptable.

### Reproduction notes (read-only, `.venv/bin/python`)

- **M1:** the 6-node team in M1 built with `slicing.model.build`. Compare `analysis.confirmed_findings(t, mask)` for {y}, {x,y}, {s,x,y}, {s,x,y,OUT}, and run `analysis.shrink(t, ('robust','OUT','g'))`. For the wild-team count, take every convex σ ⊂ σ' from `slices.exhaustive(t, |N|)` on `conformance.wild_team(seed, n=5)`, seeds 0–399.
- **M2:** the K-switch team in M2 (s1 requires q and guarantees p; J requires p). Compare `analysis.confirmed_findings` with `conformance.confirmed_oracle` for σ = {s1..sK}, K = 7.
- **T8 stress test:** `incremental.recertify` against `incremental.full` on all convex slices, 8 changes per team (alternating `conformance.mutate` and `edge_mutation`), wild-team seeds 0–299: 2,400 changes, 0 mismatches.
