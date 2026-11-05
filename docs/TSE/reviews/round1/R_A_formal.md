# Review of TSE submission "Agent Slicing: Contracts for Sub-Teams Expose and Localize Blind Spots in Multi-Agent AI Systems"

**Reviewer A**: formal methods and theory (assume-guarantee reasoning, contract theories, program slicing, semantics of dataflow graphs)

## Summary

The paper models a multi-agent LLM team as a DAG of agents (whose guarantees are conditional on their requirements and on their "oracle" not failing) and deterministic gates. Nodes can fork or switch, and joins can be `all`, `any` or quorum. An exact run semantics defines three kinds of symptom keys: `assume`, `goal` and `robust`. A *slice* is a convex node set. It is analyzed under a *hybrid semantics* H_σ: members behave exactly and every outside node is taken "at face value". Agent-level analysis is defined as the union of the singleton slices. The paper states eight theorems: T1 conservativity, T2 abstraction and partition composition, T3 soundness, T4 separation and a "fooling-set" lower bound, T5 localization, T6 overlap, T7 complexity and T8 incremental recertification. It defines *depth* as the size of the smallest manifesting slice. The evaluation uses injected defects in generated teams and nine hand-encoded published designs. Per-node proof steps are discharged with Z3, and the implementation is conformance-tested against brute-force oracles.

I read the full manuscript and Appendix A, and I examined the artifact (`slicing/`, `formal/prove.py`, `experiments/e1_conformance.py`, `tests/`). I ran the test suite (35 passed) and the SMT script (all 15 obligations behave as reported). I also wrote small read-only scripts against the library to check several stated results. Several central claims do not survive this check. T2(c) contradicts the paper's own definition of the derived guarantee. T7(a) is false for robust keys. T5(c) is vacuous, and that vacuity drives the headline localization comparison against the whole-team baseline. The separation result T4 is mostly true by construction of a particular hybrid semantics: a classical node-local must-analysis detects every hidden class in the benchmark. The hybrid semantics is neither an over- nor an under-approximation. As a result, "depth" and "minimal manifesting slice" can be determined by spurious witnesses, and agent-level analysis itself raises false alarms. Details follow.

## Strengths

1. **Clean, small calculus.** Monotone property sets and finite choices (switch, contributor set, failure set) make the questions decidable and the reasoning tractable. Lemma A (face value dominates) is stated and proved carefully, and it is the right technical lemma.
2. **Honest scoping in places.** The paper says explicitly that it does not claim any LLM satisfies a contract. It admits false alarms of strict sub-slices (T3c, T5e) with a concrete example, which I verified. It reports that exact whole-team checking is cheaper on switch-free teams, and it states what is and is not mechanized (Sec. IV-C, p. 9).
3. **Strong artifact.** The repository is small and readable. It regenerates every number and has an independent replay oracle and a model oracle. Using proof mutants to show that the SMT obligations are not vacuous is good practice. The authors' own log of a shared-misreading bug (switch with one successor) is commendable transparency.
4. **Relevant problem.** Static, contract-level reasoning about the composition of LLM agent pipelines, before any run, is timely and useful for SE.
5. **Correct observations.** The paper correctly identifies that exact slice contracts are relations rather than single (A, G) pairs. It also correctly shows that convex parts alone do not give sound compositional certification, and that an acyclic quotient is needed (T2d). These observations are correct (modulo Major 3) and well illustrated.

## Major concerns

### M1. The hybrid semantics is neither sound nor complete, so "depth", "hidden at agent level" and "minimal manifesting slice" are not semantic notions

Definition 5 (p. 5) makes every outside node "reached if some in-edge is delivered". That silently turns every outside `all`/quorum join into an `any` join for reachability. Every outside node also "always applies", which is optimistic about content. Every entry edge into a member carries the *union* of all outside predecessors' outputs. H_σ therefore over-approximates reachability and under-approximates missing facts. Its findings are neither "may" nor "must" information. The paper acknowledges false alarms for strict sub-slices (T3c), but it does not draw the consequences:

**(a) Agent-level analysis (B1) itself raises false alarms.** Here is a five-node, all-gate team that is clean (Sym(T) = ∅) and live, for which the singleton slicing reports a key. I verified it with the library:
```
IN(gua g) -> s ; s: switch gate, successors a and OUT ; a: gate, gua {x}
IN -> J ; a -> J ; J: gate, req {x}, join all ; J -> OUT ; OUT: join any, goals {g}
Sym(T) = {} ;  F({s}) = {(assume, J, x)}   (also F({IN,s}), F({s,a}), F({IN,s,a}))
```
In T, J is reached only when s routes to a, and then x is present. In H_{s}, J is outside and "reached" on IN's edge alone. Theorem T1 calls the singleton slicing "the per-agent assume-guarantee check with every other component at face value". No classical per-agent AG check would report J's requirement x as unmet when its predecessor a guarantees x on every path that reaches J. On 6,000 random wild teams I found 49 node-level cases where a singleton reports a key that is neither in Sym(T) nor subsumed by a stronger key of the same property.

**(b) Depth and MMS can be decided by spurious witnesses.** Take `conformance.wild_team(3573, n=6)`. The key (assume, n3, p3) is a true symptom of T, whose exact witness requires n1 to take only n0's contribution. Its minimal manifesting slices are nonetheless {n0} and {n1}, so its depth is 1 ("visible at agent level"). The witness for {n1} routes n1 to OUT and "reaches" the quorum-2 join n3 on one input, which is impossible in T. Meanwhile the slices {n1,n3}, {n1,n2,n3}, {n1,n3,OUT} and {n1,n2,n3,OUT} do *not* manifest this true key. The cause is that a member join whose predecessors are outside sees the union `env` on every entry edge, so its own contributor choice disappears.

**(c) Agent-level findings that are true are lost in larger slices.** The RQ1 answer (p. 9) says that "slice-level analysis recovers every agent-level finding (T4c)". That is not what T4(c) states (see M5), and it is false in general. In 6,000 wild teams I found 8 cases where a key in F({v}) ∩ Sym(T) is absent from F(σ) for a convex σ ∋ v, even allowing replacement by a stronger key. The example above is one of them.

*Required change.* State precisely what H_σ approximates, and prove it, for example as a product of a may-reachability and a must-content abstraction. Then either (i) redefine findings, depth and MMS over *lifted* findings only (keys whose witness extends to a run of T, which you can already decide by replay), so that depth becomes a semantic property of a symptom, or (ii) change the face-value rule so that outside joins respect their policies, using a three-valued "possibly reached" status, and re-prove Lemma A, T4 and T5. Re-run E2 to E7 under the corrected definitions. Remove "recovers every agent-level finding" unless it is proved.

### M2. Theorem T5(c) is vacuous, and that vacuity drives the localization result against the whole-team baseline

The contributing lineage L of a symptom node x always contains ι, because every reached node's lineage goes back to the input. Hence hull(L) = anc*(L) ∩ desc*(L) = anc*(x) ∩ N = anc*(x). Since every node lies on a path to ω (Def. 1), hull(L) = N for every goal or robust key. I confirmed this with `analysis.lineage_hull` on all 6,390 symptoms of 1,500 wild teams (4,832 assume, 1,519 goal, 39 robust): in every case the hull equals N for output keys and anc*(x) for assume keys. T5(c) therefore says only that the whole team (or the whole ancestor cone) manifests the key, which is T3(a). The corollary "depth(κ) ≤ size of the smallest such hull" is the trivial bound |anc*(x)|.

This matters for the evaluation. Baseline B2's localization is *defined* as this hull (Sec. IV-B, p. 9: "the most a whole-team counterexample says about location"). The headline "0.92 of the team vs 0.21" (abstract, RQ2) is therefore true by construction, not an empirical finding. It is also not what a whole-team counterexample says. A witness run names the switch choices, the contributor choices and the failed oracles, which is often a very small set. Standard counterexample-explanation techniques shrink it further, for example delta debugging on the witness's choices, minimal correction or unsatisfiable subsets over the choice and failure variables, or causality-based explanation.

For robust keys the statement is also inconsistent: the hull manifests "κ *or* the goal key of the same property". The depth bound for κ does not follow from that disjunction.

*Required change.* Drop T5(c) or restate it non-trivially, for example by excluding ι and pruning the lineage to nodes whose choice or failure is necessary for the symptom. Replace the B2 localization with a meaningful whole-team explanation baseline (at minimum, choice points and failed agents of a minimized witness) and re-run Table 9 and all localization claims in the abstract, introduction and RQ2.

### M3. Theorem T2(c) contradicts Definition 7, and its SMT "proof" encodes a different definition

Definition 7 (p. 5) defines G_σ(X) as an *intersection over all delivered exit edges*. For the slice of two independent members (m1: r1→g1, m2: r2→g2, each with its own exit), that gives G_σ(X) = (X ∪ g1[r1⊆X]) ∩ (X ∪ g2[r2⊆X]) = X. The single pair "assume ∅, guarantee nothing beyond the entry" is then exact, so T2(c) is false under the paper's own definition. The library agrees. `contracts.derived_contract` returns G_σ(X) = X for every X. `declared_valid(A={r1,r2}, G={g1,g2})` is False. The test suite asserts exactly this intersection behavior (`tests/test_slicing.py::test_derived_contract_is_conditional`). The SMT obligation C2 (`formal/prove.py`) instead encodes a *union* `g1[r1] ∪ g2[r2]`, which appears nowhere in the paper, and it checks only one 4-bit instance with environments 0..3. In addition, "exact" is never defined.

The underlying point, that per-exit or relational contracts are needed, is correct and worth keeping. It also exposes a weakness of Definition 7: intersecting over exits throws away exactly the per-exit information that makes contracts useful. Definitions 8 (validity) and T2(b) inherit the same weakness.

*Required change.* Define "exact contract". Either redefine G_σ as a per-exit vector (and propagate that change to Definitions 8 and 9 and T2(b)), or restate T2(c) for the definition actually used. Re-encode C2 so that it matches the paper's definition, and prove the general claim (any distinct r1, r2, g1, g2) rather than one bit-vector instance.

### M4. Theorem T7(a) is false for robust keys

T7(a) states that deciding κ ∈ Sym(T) is NP-complete, and the membership proof says "a run is a polynomial certificate". A robust key, however, requires (goal, ω, φ) ∉ Sym(T), which is a universally quantified (coNP) condition. Robust-key membership is coNP-hard. Extend the paper's own reduction with one agent A (oracle o, guaranteeing `tok`) placed after the variable gadgets. Make every clause gate also require `tok` and guarantee the critical goal c, and set f = 1. Failing o always loses c. In fault-free runs, c is missing iff the formula is satisfiable. Hence (robust, ω, c) ∈ Sym(T) iff the formula is UNSAT. I checked this with the library on 300 random 3-CNFs (231 SAT, 69 UNSAT) with zero disagreements. Robust-key membership is therefore in D^P and both NP-hard and coNP-hard, so it is not in NP unless NP = coNP. (The safety claim, coNP-complete, is correct, because "goal ∨ (¬goal ∧ R)" collapses to "goal ∨ R".) Relatedly, the well-formedness condition of Definition 1 ("every node is reached in some fault-free run") is NP-hard to check by the same reduction. That should be stated, because the theorems assume it.

*Required change.* Restate T7(a) per key kind: NP-complete for assume and goal keys, D^P membership plus NP- and coNP-hardness (ideally D^P-completeness) for robust keys. Give the proof, and note the complexity of checking Definition 1.

### M5. The separation result (T4) and the "fooling-set" lower bound are largely true by definition, and are weaker than claimed

**(a) T4(c) is only about static keys.** For a singleton {v}, every entry edge carries cone(v) (L7), so v's content is always its face-value content. The keys *located at v* in F({v}) are therefore exactly the static keys at v. I checked this on 21,000 nodes of 3,000 wild teams with zero exceptions. T4(c) thus reduces to "F(∅) ⊆ F(σ)". It says nothing about dynamic agent-level findings such as A4 robust keys, S5 bypass keys or S6b roots located downstream, and those findings *can* be lost (M1c). "Strictly more expressive" then holds only because the SL strategy explicitly includes the singleton family, which is a property of the strategy, not of slice-level analysis.

**(b) T4(b) holds only for disjunctive per-view predicates.** The proof (p. 16) assumes the unsafe team "must be flagged through some view", that is, the analysis flags a team iff some single view satisfies a predicate. For an analysis that is any function of the *set* of views, the argument fails: in the S4 instance, the view set of the unsafe team {(R1,o1),(R2,o1)} differs from both safe teams' view sets, and a two-view shared-oracle check (exactly what B5 does) separates them. "No analysis that decides from singleton views is both sound and free of false alarms" is therefore not proved as stated. "Fooling set" is also a misnomer: no crossing argument as in communication complexity is made. With views defined to exclude provenance and path information, the result is close to immediate.

**(c) A classical node-local analysis is not silent on these classes.** The claim "agent-level checks are silent on whole classes" depends on defining agent level as face-value *union*. Consider the authors' own linear-time must-analysis (`semantics.lower_bound`, a Kildall-style lower bound with intersection at `any`/quorum joins), extended by enumerating failure sets with |F| = min(f, |Orc|), which is polynomial for fixed f. On the small benchmark (7 topologies × 10 seeds) it detects the primary key of **420/420** hidden-class teams (S2, S3, S4, S5, S6a and S6b: 70/70 each). It raises no false key on clean, D2, D4 or D5 teams, and false keys only on decoy D6 (16/70 teams). This is the natural "agent-level" baseline from compositional dataflow analysis, and it is missing from the paper. Its existence undercuts the motivation that relational defects need multi-node slices to be *detected*. What slices add over it has to be argued (for example exactness and localization), not assumed.

*Required change.* Define precisely the class of analyses covered by T4(b), for example "a team is flagged iff ∃v. P(view(v))", and restate the theorem for that class. If you want a stronger lower bound, prove it for a non-trivial class (for instance node-local monotone transfer functions over a fixed finite per-node abstract domain), and justify why must-analysis falls outside it. Rename the "fooling set" argument. Add the must-analysis baseline (with failure enumeration) to E2 and E7. Restate T4(c) honestly and remove the "recovers every agent-level finding" claim, or prove it for dynamic keys under an explicit hypothesis.

### M6. Several proofs are sketches with gaps, and key notions are informal

- **Lemma W (p. 4, p. 15).** "Contract-respecting model" is defined only in prose. It is not said whether a model's output is E(v) ∪ gua or c(v) ∪ gua, whether reachability or contributor sets are constrained, or how robust keys are defined over models. As written, models differ from runs only by adding evidence, so the lemma is near-definitional. Either define the model class formally (it is the main justification for "all contract-respecting behaviours") or present Lemma W as a modelling choice.
- **T2(a), (b), (d) (p. 6, p. 16).** Beh_σ (Def. 9) is informal. The proof of (a) does not address that failure sets are *global*: a shared oracle across parts is exactly S4, so composition must fix one F for all parts, as `quotient_symptoms` does but the paper never says. Nor does it address that the robust-key condition "goal ∉ Sym(T)" is global and cannot be computed per part. The T2(b) statement leaves "otherwise behaves arbitrarily" and "delivers G^d on its exits" (all exits? any delivery pattern? may it halt?) undefined. Validity (Def. 8) is checked only with *all* entries delivered, yet in T entries can be partially delivered. The proof covers only goal keys, while the statement concludes "T is safe". The cyclic counterexample of T2(d), as written, has no goals, so by Definition 3 that team is *safe*; I verified that its symptoms are four assume keys only. It certifies an unsafe team only once x or y is a goal.
- **Robust keys in H_σ.** Definition 3 conditions robust keys on (goal) ∉ Sym(T), and Definition 5 says "keys of Definition 3 evaluated in H_σ". The implementation uses (goal) ∉ F(σ). The paper must say which one it means; the two give different findings.
- **Emergent obligations X_σ** (Def. 7, abstract, introduction) are listed in prose ("joint coverage, non-bypass, conditional backing, independence") but never defined, and no theorem mentions them. The taxonomy S1–S6 likewise has no formal definition. The classes are defined operationally by the injector gadgets and the `diagnose` heuristic, so the "100% diagnosis accuracy" (p. 11) is circular.
- **T8 (p. 8, p. 17).** The edge-change case is a single sentence, and the E1 conformance check never exercises it: `conformance.mutate` changes only node attributes. Strategies such as window, region and goal-directed also *re-generate* slices after an edge change, which the theorem does not cover.
- **T1, T5(b) and T6** are definitional or immediate and should not be counted as theorems ("eight theorems", p. 2).

*Required change.* Give complete proofs for Lemma W, Lemma A, T2(a), (b) and (d), T4(a) (for all ℓ and m, including the claim that smaller slices do *not* manifest, which the text uses as "S4, S6 need k = ℓ+2"), T5 and T8, with all quantifiers and side conditions explicit. The calculus is small enough that mechanizing it in Coq, Isabelle or Lean is realistic. If you claim proofs, I strongly encourage it, given that M2 to M4 slipped through. Define emergent obligations and the classes formally, or demote them to informal terminology.

### M7. The mechanization and testing claims overstate the assurance they provide

The abstract and contributions say the theorems' "per-node steps are discharged by an SMT solver" and that "every theorem is checked against brute-force oracles … with zero mismatches". In fact:

- The SMT obligations are one-step Boolean set identities. L6 is a tautology: u and w are defined by the same formula and then asserted equal. L7, L9 and C1 are immediate. L12 and L13 concern declared evidence, which is *semantically redundant*: applies(v) ⇔ (req(v) \ decl(v)) ⊆ c(v), and keys are req \ (c ∪ decl), so replacing req(v) by req(v) \ decl(v) eliminates `decl` entirely. The obligations cannot catch the errors in M2 to M4, which live in the inductions, in the definitions and in the definition–encoding gap (C2).
- Several theorems are not checked at all: T2(b), the general T4(b), T7, and the edge-change case of T8. The check for T5(c) is vacuous (M2), and the check for T4(c) only tests static keys (M5a). Conformance teams have 3 to 7 inner nodes with slices of size ≤ 3 (≤ 2 on benchmark teams), and only one witness per key is checked for T5(c), whereas the theorem quantifies over every witness.
- `conformance.lifts` (the T3b check) ignores the witness and only tests membership of the key in Sym(T).

*Required change.* Rephrase the abstract, the contributions and the RQ1 answer to say exactly what each check establishes. Either remove `decl` from the calculus or explain why it is not syntactic sugar. List per theorem whether it has a paper proof, a mechanized proof or a bounded check, and at what bound.

### M8. Novelty relative to contract theories, compositional safety analysis and abstraction needs proper positioning

The paper's claimed novelty (p. 15) has three parts: the choice of *which* sub-structures to treat as components, the hybrid semantics, and slice size as a measure of hiddenness. Closely related work is missing:

- **Hierarchical contract-based design and contract refinement checking** over component hierarchies (OCRA, Cimatti & Tonetta; AGREE/AADL, Cofer et al.). Choosing a decomposition and checking refinement level by level is their core use case.
- **Contract-based fault-tree generation and minimal cut sets** (Bozzano, Cimatti, Mattarei, Tonetta and colleagues). A minimal manifesting slice for a robust key is closely related to a minimal cut set, S4 is textbook common-cause failure, and S6a is a dependent failure.
- **Localization abstraction and abstraction refinement** (Kurshan's localization reduction; CEGAR). Analyzing some components precisely and abstracting the rest is exactly this. So is selective path-sensitivity in dataflow analysis, and the must-analysis of M5c is the canonical node-local baseline.
- **Soundness conditions for circular AG reasoning** (McMillan; Namjoshi & Trefler). The acyclic-quotient condition is a special case.
- **Convex subgraph enumeration** (e.g., instruction-set extension work by Pozzi, Atasu, Ienne; Bonzini & Pozzi). This literature is directly relevant to T7(c) and (d).

The analogy to program slicing is loose. Apart from the goal-directed strategy, a "slice" here is a convex sub-DAG without a slicing criterion, and Weiser-style semantic guarantees (slice-preserving projection of behavior) have no counterpart.

*Required change.* Add a related-work comparison against the works above, state precisely what is new relative to each, and consider renaming the concept or making the slicing analogy precise, for example by proving a projection property for goal-directed slices.

## Minor concerns

1. **p. 3, Def. 3.** A run in which ω is never reached (a deadlock caused by an `all` join behind a switch, or an unmet quorum) produces no symptom. Safety is therefore partial correctness, and a team that never releases is "safe". Lemma H and T3(c) depend on this. Discuss it, or add a liveness key.
2. **p. 3, Def. 3.** Under faults only critical goals at ω are checked. An agent acting without its requirements because an upstream model failed is not a symptom. Justify this asymmetry.
3. **p. 3, Def. 2 step 3.** For `all` joins, C(v) = D(v), but the rule also requires all in-edges to be delivered. Say "C(v) = all in-edges". Also state what a quorum q > |pred(v)| means (the code rejects it; the paper does not).
4. **p. 4, Lemma M.** The lemma uses |F| = min(f, |Orc|), while Algorithm 1 uses orc(σ). Note that failing outside oracles has no effect in H_σ. Also note that the lemma's last sentence, about keeping inclusion-minimal content values, is an implementation optimization and not part of the lemma.
5. **p. 5, Def. 5.** Say explicitly that each entry edge carries the union of *all* outside predecessors' outputs, and that a member join therefore cannot choose among its entry edges. This is the mechanism behind M1(b). Also say how ι or ω as members are treated.
6. **p. 5, Prop. 1.** Witnesses of dynamic agent-level keys also rely on outside joins being "reached on one input" (M1a). The proposition's characterization ("v does not apply or routes away") is correct, but the resulting keys need not be symptoms. Say so.
7. **pp. 4–5 and 15–17.** Lemma labels are inconsistent: the text uses W, M, H, A, the PDF numbers them Lemmas 1–5, and Table 6 refers to "Lemma A, M". Use one scheme.
8. **p. 6, Table 1.** The "Entry carries" column for {DV, RG} ("same") is not the same entry set as for {ST, RG}. List entries per edge.
9. **p. 6, Theorem 2(d).** State that the partition must cover ι and ω, and say how parts containing them are handled.
10. **p. 7, Def. 10.** For static keys, MMS is undefined: every singleton manifests them. Define MMS for depth-1 keys as well.
11. **p. 7, T5(b).** The intersection of minimal slices may be empty, and the empty set is not a slice. Say so.
12. **p. 7, T4(a).** "Number of branches" is a parameter only for S2 and S3. For S4 the family is a chain. In the text the "parallel reviewers" case of S4 has depth 2, not ℓ+2, so the statement should cover both.
13. **p. 8, T7(b).** The bound ignores the cost of propagating to outside descendants per run, and the cost of the minimality filtering of contributor sets (quadratic in the number of options).
14. **p. 8, T8.** Given minor 1 and M7, `decl` changes are just `req` changes. After edge changes, slicing strategies produce new slices; state how they are handled.
15. **p. 9, Table 6.** C1 is attributed to "T7 / must-analysis", but T7 does not use it.
16. **p. 13, ablation.** Non-convex slices produced no false keys in 29,675 trials, and convexity inflates explanations (SR in the running-example MMS, p. 4). The case for convexity rests only on T2. Say this plainly and consider reporting non-convex minimal sets as well.
17. **p. 14, Discussion.** Partition certification (T2d) is recommended for choice-rich teams, but its cost is never measured. `quotient_symptoms` enumerates all combinations of part outcomes. Either evaluate it in E5 or remove the recommendation.
18. **p. 10, H2.1.** As the authors note, this test is guaranteed by construction. Move it out of the hypothesis-testing frame.
19. **Abstract and p. 2.** "With no false alarm on clean and decoy teams" is an empirical statement about the generated benchmark. Add that the theory admits false alarms even at agent level (M1a).
20. **pp. 1 and 9.** "Fooling-set argument" should be renamed (M5b).
21. **p. 16, Proof of T2(c).** It refers to "4-bit vectors"; see M3.
22. **p. 9, Implementation.** The model oracle enumerates "evidence assignments between the realized minimum and that minimum plus every relevant property", which is a bounded subset of models. State the bound in Lemma W's validation.

## Scores (1 = poor, 5 = excellent)

| Criterion | Score | Justification |
|---|---|---|
| Novelty | 2 | Convex sub-structures analyzed with the rest abstracted is close to hierarchical AG contracts, localization abstraction and cut-set analysis; the separation is largely by construction, and the key related work is missing. |
| Rigor | 2 | Concrete errors (T2c vs Def. 7, T7a for robust keys), a vacuous theorem (T5c), a fooling-set argument that only covers disjunctive analyses, an approximation status of H_σ that is never characterized, and sketch-level proofs of the compositional results. |
| Relevance | 4 | Static compositional reasoning about LLM agent teams matters to SE; the encodings of published designs are a useful start. |
| Verifiability and Transparency | 3 | An excellent, runnable artifact with oracles and mutants, but several "checks" are vacuous or narrower than claimed, and the mechanization claims are overstated. |
| Presentation | 3 | Well written and well illustrated, but the theorem inventory is inflated, labels are inconsistent, central notions (emergent obligations, classes) are informal, and the proofs are too compressed to check. |

## Recommendation

**Major revision.** The modeling idea is reasonable and the artifact is unusually good. However, the formal core, which is the paper's main claim to TSE-level rigor, has errors and vacuities that change the conclusions. The approximation status of H_σ has to be fixed (M1), because otherwise depth and localization are not semantic notions. The localization advantage over the whole-team baseline is an artifact of a vacuous hull (M2). T2(c) and T7(a) are incorrect as stated (M3, M4). The separation story has to be re-argued against a proper node-local baseline (M5). A revision must also correct the proofs and the mechanization claims (M6, M7) and position the work against hierarchical contract-based design, contract-based fault-tree and cut-set analysis, and abstraction refinement (M8).

### Reproduction notes for the authors

All checks used the library read-only, with `.venv/bin/python`:

- **M1(a):** the 5-node team above, built with `slicing.model.build`. Compare `semantics.symptoms(t)` with `semantics.findings(t, t.nbit['s'])`.
- **M1(b, c):** `conformance.wild_team(3573, n=6)`, key `('assume','n3','p3')`. Enumerate `slices.exhaustive(t, |N|)` and test membership in `semantics.findings`.
- **M2:** for each `(k, w)` in `semantics.symptoms(t)` with a witness, compare `analysis.lineage_hull(t, k, w)` with the full mask (output keys) or `t.anc[x] | t.nbit[x]` (assume keys).
- **M3:** `contracts.derived_contract` on `build([('m1','agent',['r1'],['g1']),('m2','agent',['r2'],['g2'])], [('IN','m1'),('IN','m2'),('m1','OUT'),('m2','OUT')])` returns G_σ(X) = X for all X.
- **M4:** the `cnf_team` construction of `experiments/e1_conformance.py`, extended with an agent `A` (oracle `o`, gua `tok`) after the variable gadgets, clause gates requiring `tok` and guaranteeing critical goal `c`, and f = 1. `('robust','OUT','c') ∈ Sym` iff UNSAT (300/300 formulas).
- **M5(c):** `semantics.lower_bound`, applied with the guarantees of failed-oracle agents removed for each |F| = min(f, |Orc|), over the 7×10 small-benchmark teams per class. Recall 70/70 for each of S2, S3, S4, S5, S6a, S6b; false keys only on D6 (16/70).
