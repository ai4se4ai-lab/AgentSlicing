# Review of "Agent Slicing: Contracts for Sub-Teams Expose and Localize Blind Spots in Multi-Agent AI Systems"

**Reviewer C.** I review from two angles: as a practitioner who builds LLM multi-agent systems for software engineering, and as a reader standing in for a software-engineering PhD student who is not a formal-methods specialist.

---

## Summary

The paper models a team of LLM agents and deterministic gates as a DAG with typed nodes:

- agents have conditional guarantees and a model "oracle" that may fail;
- gates are deterministic programs;
- nodes can fork, switch, or join under `all`, `any` or quorum policies;
- each node carries requirement, guarantee and declared-evidence property sets.

A *slice* is a convex (possibly disconnected) set of nodes. It is analyzed under a *hybrid semantics*: members behave exactly, and everything outside is taken "at face value". Singleton slices give agent-level analysis. The slice of all nodes is exact whole-team analysis.

The paper defines derived and declared slice contracts and a taxonomy of "blind spots" (A1–A4 visible at agent level; S1–S6b slice-level). A blind spot's *depth* is the size of its smallest manifesting slice. Eight theorems cover:

- conservativity (T1);
- abstraction and compositionality over acyclic quotients (T2);
- soundness (T3);
- separation from agent-level analysis (T4);
- localization (T5);
- merging of findings (T6);
- complexity (T7);
- incremental recertification (T8).

The evaluation is entirely simulated, and no LLM is called. It has four parts:

- **Conformance.** SMT checks of per-node proof steps and brute-force oracle conformance.
- **Synthetic benchmark.** 4,480 generated teams with injected gadget defects, used for detection and localization.
- **Published designs.** Encodings of nine published designs, with contracts declared by the authors.
- **Cost and evolution.** Scalability up to 5,011 nodes and incremental re-verification.

Headline claims:

- 45.5% of injected defects are hidden at agent level.
- Slicing finds all of them with no false alarms on clean and decoy teams.
- Slicing localizes to 0.21 of the team, against 0.92 for the whole-team checker.
- 7 of 9 published designs contain a defect that only slices reveal.

The formal core is careful, the artifact is unusually complete, and the authors are candid about scope ("does not claim that any language model satisfies a contract"). Still, I do not think the paper currently shows that this matters for people who build multi-agent systems. Five problems stand behind that judgment:

1. The headline percentages are properties of the benchmark design, not empirical findings.
2. The failure model ("an agent provides nothing") turns the dominant real-design finding (S6a) into a liveness observation, not a safety blind spot.
3. Several encodings of published designs are not faithful to the papers they cite, and the encoding protocol nearly guarantees the S6a finding.
4. The agent-level and whole-team baselines are weak relative to obvious alternatives, some of which the authors already implement.
5. The paper is very dense for its intended SE audience.

---

## Strengths

1. **A clear, useful question.** "Given the declared contracts of the parts, is the composition justified?" is the right engineering question for agent teams. The paper keeps it separate from "does the LLM satisfy its contract".
2. **Slicing a team graph is a good abstraction.** Convex sub-teams, hybrid face-value semantics, and depth as a measure of how hidden a defect is are intuitive once understood. Fig. 1 conveys the idea well. Treating agent-level and whole-team analysis as the two ends of one spectrum (T1, Theorem 3a) is elegant.
3. **Honest negative results.** Theorem 3c and Theorem 5e show that strict-sub-slice findings can be false alarms and that monotonicity fails. Section IV-E admits that exact whole-team checking is cheaper on switch-free teams. Section IV-G concedes that hidden-class detection is "close to guaranteed by construction" (p. 10, p. 14). This candour is welcome.
4. **Verifiability.** The paper reports:
   - a pre-registered experiment plan with logged deviations;
   - SMT obligations with proof mutants (Table III);
   - two independent oracles and 176,960 conformance comparisons (Table IV);
   - generated tables and macros;
   - a one-command replication package.

   I ran through `experiments/architectures.py` and `results/e3_architectures.json`, and the E3 numbers trace to the code.
5. **Sensitivity analysis for the encodings** (Table XI). Varying oracle assignment, fault budget and join policy is the right instinct. Too few papers that encode published systems do it.

---

## Major concerns

### M1. The headline numbers are artifacts of the benchmark design, but the abstract and introduction present them as findings.

Three of the headline numbers come straight from how the benchmark was built:

- **"45.5% of the defects are hidden at agent level."** Table XV shows the small benchmark injects exactly 140 teams for each of 11 defect classes. Five of those classes (S2, S3, S4, S6a, S6b) are hidden by definition (Theorem 4a). 5/11 = 45.45%. The number measures the authors' choice of class mix, not anything about multi-agent systems.
- **"Agent-level analysis finds 0.0% of the hidden ones and slice-level analysis finds 100.0%."** This follows from Theorem 4a and from exhaustive or goal-directed enumeration over gadgets of bounded size. The authors acknowledge this on p. 10 and p. 14.
- **"Detection saturates at slice size k = 4" (H3.2).** The injector uses gadgets with at most two intermediate hand-offs, so depth is at most 4 by construction (Table XV has no depth-5 entries). Saturation at k = 4 is an injector parameter.

The abstract and the main-results paragraph (p. 2) still lead with these numbers as if they were empirical frequencies. A practitioner would read "45.5% of defects are hidden" as "about half of real multi-agent defects are invisible to per-agent review". Nothing in the paper supports that.

**Required change:**
- Remove the hidden rate, the 0%/100% recall and the k = 4 saturation from the abstract and the main-results paragraph, or re-label them explicitly as consistency checks of the theory against the implementation.
- Lead with the measurements that are actually informative:
  - localization quality (Table VII);
  - false-alarm behaviour on unstructured teams (3.0%, which the abstract omits);
  - cost (Table XII);
  - recertification savings.
- Inject gadgets with longer hand-off chains (ℓ up to, say, 6), so that the k-sweep can show something that is not fixed in advance. Report how detection degrades with ℓ under each strategy.

### M2. The failure model makes the dominant real-world finding (S6a) a liveness/availability observation, not a hidden safety defect.

Section II and the threats section (p. 14) define a model failure as "provides nothing". A critical goal then becomes a `robust` symptom whenever its provider depends on any fallible agent's output.

Consider the running example's chain (p. 4). If DV fails, no tests exist, TS cannot apply, and `tests_pass` is absent. Downstream, the team simply does not claim `tests_pass`. A test gate with no input is *fail-closed*, and every practitioner would consider that the desired behaviour.

The same holds for MetaGPT ({QA, TestRun}), AgentCoder ({TestDesigner, Executor}), MapCoder ({Coding, SampleIO}) and Agentless ({ReproGen, ReproRun}) in Table X. Their "blind spot" is that if the LLM produces nothing, the tests do not pass.

The failure practitioners actually worry about in these designs is the commission failure:

- the test-writing agent produces weak, wrong or tautological tests;
- the gate passes;
- the team claims `tests_pass` on incorrect code.

The paper says this is "covered only insofar as downstream gates check it" (p. 14). In other words, it is not covered.

The abstract's motivating example, "a test gate that relies on tests written by a fallible agent", therefore promises a result about the dangerous case and delivers one about the benign case. Similarly, S4 (correlated evidence) is evaluated only as "two claimers fail together and provide nothing". The practically important case is two LLM reviewers sharing a model and both *wrongly approving*. Kim et al. (ICML 2025) show that this happens across providers too.

**Required change:**
- Extend the semantics with a commission (Byzantine-style) failure mode. A failed oracle may emit any subset of its guarantees without establishing them. Concretely: a failed agent's output is "claimed but unestablished", and a gate consuming unestablished input propagates the taint.
- Re-run E3 under that mode.
- Separately, distinguish symptoms where a goal is *silently claimed without being established* from those where it is *visibly absent*. Report them separately in Tables V and X.

Without this, the paper's central practical message ("a test gate that relies on LLM-written tests is a blind spot") is not supported by its own model.

### M3. Several encodings of published designs are unfaithful, and the encoding protocol nearly guarantees the S6a finding.

I checked `experiments/architectures.py` against the cited papers.

**Protocol bias.** P3 makes "the claim resting on executed tests" the critical goal, with f = 1. Under the omission failure model (M2), any gate whose input is produced by an LLM then yields an S6a `robust` key with depth 2. The finding "the recurring pattern is S6a" (p. 11) is therefore close to a consequence of P3, not a discovery about the designs.

It is also telling that 9 of 9 designs are unsafe under the documented configuration and 8 of 9 become safe with f = 0 (Table XI). The findings are about f = 1 combined with the critical-goal rule, not about the topologies.

**Design-specific problems:**

- **MapCoder.** In MapCoder (ACL 2024), the sample I/O come from the problem statement, not from an LLM. The Debugging agent is invoked when the sample tests *fail*, and it loops back over alternative plans. The encoding is a straight chain `Coding -> SampleIO -> Debugging`, where Debugging *requires* `samples_pass`, which inverts the control flow. The paper's sentence "MapCoder's sample input/output check ... certifies a critical property using tests or code written by an LLM agent" (p. 11) holds only in the trivial sense that any test run executes LLM-written code.
- **Agentless.** In Agentless (FSE 2025), patch validation runs regression and reproduction tests on the candidate patches, then re-ranks and majority-votes to select the final patch. The encoding places `Select` (an `any` join) *before* `Regression` and `ReproRun`. Agentless also samples several reproduction tests and keeps only those that fail on the original repository, which is an execution-based filter the encoding omits. Finally, Agentless's evaluation relies on SWE-bench's hidden tests, not on its own reproduction test, so `issue_fixed` as "the quality claim the design's evaluation relies on" (P3) is questionable.
- **Multi-agent debate.** Du et al. (ICML 2024) have agents read each other's answers over several rounds before the final answer. The encoding (three independent answerers, then a majority vote) is self-consistency or ensembling, not debate. The inter-agent exchange that defines debate is absent.
- **AutoGen.** AutoGen is a framework, not a design. The "group chat" with Manager/Coder/Critic/Merge/Executor is not traced to a specific documented application in the AutoGen paper. The S6b finding ("the manager routes to the critic, so the code never runs") comes from unrolling a multi-turn chat to a single turn (P4). In the real group chat the manager selects speakers repeatedly.
- **MetaGPT and AgentCoder.** In both, the test gate *requires only the tests*, not the code (`TestRun` requires `unit_tests`; `Executor` requires `tests`). A test executor obviously consumes both. This choice determines the minimal slice ({QA, TestRun}, {TestDesigner, Executor}) reported in Table X. The authors should explain it or fix it.
- **ChatDev.** Every ChatDev phase is a dual-agent chat (instructor and assistant) with "communicative dehallucination", and that is ChatDev's central mechanism. Each phase is encoded here as one agent. The LLM reviewer is declared to *guarantee* `correct`, a very strong contract that by itself manufactures the S4 redundancy with the tester.

**Inconsistent ChatDev result.** The text on p. 11 says that for ChatDev and debate "with distinct models (Table XI) the finding disappears". In `results/e3_architectures.json` the ChatDev `distinct` variant is still unsafe: S6a, depth 5, minimal slice {Coding, Complete, Review, Execute, Testing}. The table source `tables/arch_sensitivity.tex` says S6a, while the submitted PDF's Table XI says S4. The text is wrong for ChatDev in either version, and the PDF appears not to have been regenerated from the current results.

**Required change:**
- Fix the encodings above.
- For each design, give in an appendix:
  - the encoded graph;
  - a table mapping every node, edge, requirement, guarantee and join policy to a section, figure or code location of the cited paper or repository;
  - an explicit note of every deviation.
- Have the encodings checked by someone outside the author team. Ideally this means the original authors; at minimum, an independent encoder, with agreement reported.
- Report E3 also under a protocol in which the critical goal is not chosen by the "rests on executed tests" rule. Show which findings survive.
- Where a design is iterative (AgentCoder, MapCoder, ChatDev, AutoGen, Self-collaboration), unroll it at least two or three times and report whether the finding persists. Otherwise drop findings that are artifacts of one-step unrolling.
- Correct the ChatDev sentence and regenerate Table XI.

### M4. The baselines are weaker than obvious alternatives, including one the authors already implement.

Three better baselines are missing:

- **Must-analysis.** The generator assigns contracts from "a sound lower bound on the node's content (a must-analysis ...)" (p. 8). A path-sensitive must-analysis over the team graph treats `any`/quorum joins as intersection and switches as a meet. It runs in linear time and would flag S2, S3 and S5 directly. A fault-aware variant (drop each oracle's guarantees in turn, which is f·|Orc| linear passes) would flag S4 and S6a. It may raise false alarms, because Table III's C1 shows it is not exact, but that is precisely what should be measured. Without it, the strict-expressiveness result (T4) is shown only against a strawman agent-level check that ignores ancestry. The paper's own B4 lint "ignores ancestry and paths".
- **Whole-team checking plus minimization.** The localization claim (0.21 vs 0.92 of the team) compares slicing with B2's "hull of the witness's contributing lineage". That is the least a whole-team checker can do. The standard alternatives are:
  - delta debugging over the set of nodes kept exact versus taken at face value;
  - minimal-unsatisfiable-core extraction;
  - consistency-based diagnosis (Reiter 1987), which computes minimal conflict sets.

  Each of these yields minimal component sets from a whole-team checker. Minimal manifesting slices are also conceptually very close to minimal cut sets in fault-tree analysis.
- **A checklist baseline.** B5 already shows that a pattern-based smell detector reaches 80% recall on hidden classes. Its 76.5% decoy false-alarm rate depends entirely on the decoys the authors designed.

**Required change:**
- Add a fault-aware must-analysis baseline and a "whole-team checker + ddmin/MUS over face-value nodes" localization baseline to Tables V, VII, VIII and XII.
- Discuss the relationship to model-based diagnosis and fault-tree minimal cut sets (see Missing related work).
- If slicing still wins on localization quality or cost, the contribution is much stronger. If it does not, the paper's positioning has to change.

### M5. Practitioner relevance: where do the contracts come from, and do findings matter on real systems?

The approach assumes contracts over atomic, Boolean properties (`design`, `tests_pass`, `sec_tested`), declared by hand. The paper never says how a team would obtain them or what they would do with a finding. Specifically:

- **(a) No contract-acquisition story.** Real frameworks expose much of the needed structure in machine-readable form:
  - LangGraph's `StateGraph` has nodes, edges and conditional edges, which map almost one-to-one to fork, switch and join;
  - MetaGPT roles declare `_watch` subscriptions and the action output types they publish;
  - CrewAI tasks declare `context` dependencies and `expected_output`.

  An extractor from even one framework, applied to a sample of open-source projects, would turn E3 from "our encodings of papers" into "real systems".
- **(b) No validation against executions.** Cemri et al. [19] released annotated failure traces of ChatDev, MetaGPT and others (the MAST dataset). Checking whether slice findings predict, or at least are consistent with, the annotated inter-agent failures would give the first evidence that slices matter in practice. The future-work section lists this. For a TSE paper on a practical problem, at least a small-scale validation is needed now.
- **(c) Scale is misdirected.** E5 scales to 5,011 nodes, but the designs the paper targets have 5–9 nodes (Table X), where exhaustive enumeration of all convex slices is trivial. Either motivate where teams of hundreds or thousands of agents occur, or redirect the scalability study toward realistic sizes with loops and many choice points.
- **(d) Actionability.** For each E3 finding, state the concrete design change it suggests and re-check the fixed design. Examples: use a distinct model for the test writer; require `all` at the release gate; add a gate that checks test adequacy. That is what a practitioner would act on.

**Required change:** Add (a) or (b), preferably both at small scale, plus (d). Rewrite (c) or justify it.

### M6. Compositional certification does not cover the paper's headline finding type.

Theorem 2(b), the compositional use of declared contracts, requires f = 0. Yet almost every E3 finding is a `robust` key that exists only for f ≥ 1 (Table XI: "With f = 0, every design except the AutoGen encoding is safe"). So the practically central use case, a team building with declared slice contracts that must be robust to a model failure, has no compositional certification rule. Theorem 2(d) covers partitions via boundary behaviours, but that is not a contract-level rule a team could write down.

**Required change:**
- State this limitation prominently in the introduction and conclusion.
- Either extend 2(b) to f > 0, for example by making declared contracts fault-indexed (A, G, G^f), or explain why that is not possible.

### M7. Presentation is too dense for the stated SE audience, and the running example has gaps.

The paper introduces about 11 definitions, 5 lemmas, a proposition and 8 multi-part theorems in 8 pages, often in single sentences with stacked symbols. A PhD student outside formal methods will struggle with Definitions 2, 5 and 7, which carry the core of the approach. Specific problems are listed in the minor concerns. The main ones:

- **Symbol overloading.**
  - *A*: Lemma 5's tag, the declared assumption A^d, the entry assumptions A_σ, and classes A1–A4.
  - *S*: the slice family 𝒮, S_0, and classes S1–S6b.
  - *f* (fault budget), *F* (failure set), and the calligraphic findings ℱ.
  - Lemma tags W, M, H, A, whose letters are never explained, used alongside numeric references.
- **Terms used before definition.** "Face value", "convex", "content", "oracle" and "evidence" appear in the abstract and introduction long before they are defined.
- **Incoherent fork-join example.** The security tester (ST) receives no code (there is no DV→ST edge), so "code that was not security tested" (p. 4) does not describe anything ST could have done. TM's guarantee (`threat_mod.`) appears only in Table I. A release gate with `any` ("release on the first approval") is also an unrealistic design choice and reads as a strawman. Give the example a realistic motivation, for example a "fast path" where either a human-approved or an automatically-tested change may ship.
- **No worked example of a computation.** No worked example shows Algorithm 1 or Definition 7 on the running example step by step. Table I lists results without showing how they were obtained.

**Required change:**
- Add a notation table.
- Introduce every symbol in words at first use.
- Remove the overloaded letters.
- Fix the running example.
- Walk through one complete slice computation (Definitions 5 and 7, Algorithm 1) on {DV, SR, TS}.
- Move the complexity proofs, Theorem 6 and Theorem 8 details to the appendix to make room.

---

## Minor concerns

1. **Abstract.**
   - "A slice is a convex, possibly disconnected, set of agents": "convex" means nothing to most SE readers here. Say "a set of agents such that every hand-off path between two members stays inside the set".
   - "Depth at least two means invisible at agent level" is fine.
   - "with no false alarm on clean and decoy teams" should add that slice findings include 3.0% false alarms on unstructured teams (p. 13).
2. **p. 1.** "Applied naively at the level of single agents, however, it is not path-sensitive." Classical A-G reasoning is not "naive" per se. The issue is the face-value composition rule. Rephrase so as not to set up a strawman.
3. **p. 2, Contributions.** The list says "seven slicing strategies"; Sec. III-I says "We compare eight strategies". Reconcile the two.
4. **p. 2, main results.** "the combined slicing strategy finds all of them" should name SL and say what it is combines (singleton ∪ window-2 ∪ region ∪ goal-directed) on first use.
5. **p. 3, Definition 1.**
   - `decl(n)` is "declared evidence", but the reason for having both `req` and `decl` is clear only after Definition 2. Give a one-line intuition with an example such as "I read the specification".
   - "agents may share an oracle" should say explicitly that an oracle is an LLM backbone (model/provider/version), since S4 rests on this.
6. **p. 3, Definition 2.**
   - "a contributor set C(n) for each node with several predecessors": state in words that C(n) is "the inputs the join actually uses".
   - Step 3's parenthetical "(for all, or a single in-edge, C(v) = D(v))" is hard to parse.
7. **p. 3, Definition 3.** The `robust` key is defined as "(goal, ω, φ) ∉ Sym(T), and some run with |F| ≤ f reaches ω with φ ∈ Φ_c \ c(ω)". Add one sentence explaining why the goal key must be absent, namely to avoid double counting.
8. **p. 4, Section II-D.** "for example, an agent may happen to see a fact that nobody guarantees": this sentence motivates evidence but is confusing. Give a concrete example.
9. **p. 4.** Lemma tags "(Worst case, W)", "(Minimal choices, M)", "(Halting, H)" and later "(Face value dominates, A)" are used in Table III ("Lemma A, M", "Lemma W", "Lemma H") and Table IV ("Lemmas W, M"), while the text uses numbers. Use one scheme.
10. **p. 4, Chain example.** The text says the goal is `sec_reviewed`, while Fig. 2 and Table I use `sec_rev.`. The text says the robust guarantee "loses tests, code and tests_pass", while Table I says G^f is "nothing" for {DV, SR, TS}, which also loses `sec_rev.`. Make them consistent.
11. **p. 5, Definition 4.** The hull is defined as anc*(S) ∩ desc*(S). This is correct for convex closure, but give the {RA, DV} → {RA, AR, DV} example *before* the definition, not after.
12. **p. 5, Definition 5.** This is the most important definition and the hardest to read. The phrase "Every outside node is reached if ι or some in-edge is delivered; all its delivered in-edges contribute; it always applies and delivers to all successors" packs three distinct assumptions into one clause. Split it into a list, and illustrate it with Fig. 2(a).
13. **p. 5, Definition 7.**
    - "an environment X ⊆ 𝒫 carried by every entry edge" assumes all entry edges carry the same X. Say whether per-edge environments are handled, since Theorem 2c says contracts are relations.
    - The emergent-obligation bullet lists four obligations in one sentence. Give each a name and a one-line example.
14. **p. 6, Table I.**
    - "same" in the "Entry carries" column for {DV, RG} is ambiguous.
    - The ellipsis "…, code, tests" for {SR, TS} should be spelled out.
    - `threat_mod.` is never introduced.
15. **p. 6, Theorem 2(d).** The cyclic-quotient counterexample with {a, d} and {b, c} is described only in the proof idea. A small figure would help.
16. **p. 6, Algorithm 1.**
    - Line 4 enumerates failure sets for every slice even when σ contains no agent. Say so, or guard it.
    - Line 13's ranking "by size, then by number of choice points" is not motivated.
17. **p. 7, Table II.**
    - S1 is listed as visible at agent level ("yes"), yet named as a slice-level class. Table V uses "S1v", which is never defined.
    - Explain why S1 and S5 are "S" classes.
18. **p. 7, Part (c) example.** The false-alarm example (switch s, provider y, gate x) needs a figure. In prose it is very hard to follow.
19. **p. 8, Section III-I.** "Random draws convex convex slices": the word "convex" is duplicated.
20. **p. 8, Benchmark.** "Goal-related defects are inserted as a release stage before the output; fact-related defects are inserted on a random edge, with a fresh consumer." This means every defect is a local gadget attached to a clean host. The by-topology uniformity in Table IX (p. 11) is then expected, and the authors say so. Consider dropping Table IX or moving it to the appendix.
21. **p. 9, Baselines.** B5 was added after the plan was frozen. Report its pre-registration status in Table V's caption as well.
22. **p. 10, Table V.** Precision is mentioned in text (100.0% over 5,503 keys) but is not in any table. Add a precision row or column.
23. **p. 10, Table VI.** Reporting Wilcoxon p-values and Â12 = 1.00 for a comparison that the paper itself says is guaranteed by Theorem 4 adds no information. Drop Table VI or reduce it to one sentence.
24. **p. 11, Table VII.** Precision for B2 is 0.0 and Hit is 100.0. Explain the column semantics in the caption. Also, the 280 vs 416 vs 687 values in column n (detected cases) mean the strategies are compared on different subsets; say how this affects the comparison.
25. **p. 11, protocol P1–P4.** These are numbered like a list but typeset as a hanging paragraph that runs into the next section. P4 ("Iterative loops are unrolled once") deserves its own justification, given M3.
26. **p. 12, Table X.**
    - The citation numbers precede the design names ("[1] MetaGPT"), which is unusual. Put the citation after the name.
    - Table X does not show the encoded graphs. Add a figure with the nine encoded graphs, even small ones.
27. **p. 12, Fig. 3.**
    - The S3 curve hides S2 at k ≥ 2.
    - The legend is below the axis and separated from the plot.
    - The x-axis starts at k = 1 with a line drawn from 0, which suggests a measurement at k = 0.
28. **p. 13, Fig. 4.** In the right panel several strategies stop at around 10³ nodes without a marker for time-outs. Mark where the budget was exceeded.
29. **p. 13, E7.** "If the analysis treats every join as all, S2 and S3 are no longer detected": state that this is an ablation of the *analysis*, with the team semantics unchanged. Table XIV's caption suggests otherwise.
30. **p. 14, "Slices versus failure attribution."** This is the most interesting practitioner bridge in the paper and deserves more than three sentences (see M5b).
31. **p. 14, Threats.** Include the bias from authors choosing both the gadget class mix and the encoding protocol (M1, M3).
32. **p. 15, Related work.**
    - "None of these works reason about sub-teams as contracts before execution" is plausible but should be softened. Graph-based agent frameworks (GPTSwarm, AFlow) optimize sub-graphs before deployment.
    - MAGIS and CAMEL are cited but not encoded. Explain why. MAGIS in particular is an SE multi-agent design with a natural QA gate.
33. **p. 17, Appendix C.** The "Additional Tables" heading is empty, and Tables XV–XVIII float to p. 18, after the references. Place them inside the appendix.
34. **References.**
    - Several cite arXiv versions although archival versions exist: MetaGPT (ICLR 2024), ChatDev (ACL 2024), MapCoder (ACL 2024), Du et al. debate (ICML 2024), Mixture-of-Agents (ICLR 2025), AutoGen (COLM 2024).
    - [46] has a garbled author name ("PÄÅreanu").
    - [51]'s title is in all caps.
    - [27] has mismatched quotes.
35. **Artifact availability.** The paper refers several times to "the replication package" but gives no (anonymized) link. TSE reviewers need one to check claims. Also, `results/e3_architectures.json` records `"dirty_worktree": true`. The submitted results should come from a clean, tagged commit.
36. **Consistency of PDF and sources.** As noted in M3, Table XI in the PDF disagrees with the generated `tables/arch_sensitivity.tex` and the JSON results for ChatDev/distinct. Regenerate the PDF and check all numbers once more.

---

## Missing related work

I verified that each of these items exists.

1. **R. Reiter**, "A theory of diagnosis from first principles," *Artificial Intelligence*, vol. 32, no. 1, pp. 57–95, 1987. DOI: 10.1016/0004-3702(87)90062-2.
   - *Why:* consistency-based diagnosis computes minimal conflict sets and diagnoses of components from a system description. This is the closest classical analogue to "minimal manifesting slices" and a natural localization baseline (M4).
2. **E. Ruijters and M. Stoelinga**, "Fault tree analysis: A survey of the state-of-the-art in modeling, analysis and tools," *Computer Science Review*, vols. 15–16, pp. 29–62, 2015. DOI: 10.1016/j.cosrev.2015.03.001.
   - *Why:* minimal cut sets and common-cause failures correspond to S4/S6a and to "depth". The paper should position against FTA.
3. **E. Kim, A. Garg, K. Peng, and N. Garg**, "Correlated errors in large language models," in *Proc. 42nd ICML*, PMLR vol. 267, pp. 30038–30066, 2025. arXiv:2506.07962. URL: https://proceedings.mlr.press/v267/kim25e.html
   - *Why:* this is empirical evidence that LLM errors correlate even across providers. It directly bears on S4 and on the claim (p. 11, Table XI) that distinct models remove the debate finding.
4. **A. Smit, N. Grinsztajn, P. Duckworth, T. D. Barrett, and A. Pretorius**, "Should we be going MAD? A look at multi-agent debate strategies for LLMs," in *Proc. 41st ICML*, PMLR vol. 235, pp. 45883–45905, 2024. URL: https://proceedings.mlr.press/v235/smit24a.html
   - *Why:* debate protocols and their relation to self-consistency and ensembling, which is relevant to the debate encoding (M3).
5. **M. Zhuge, W. Wang, L. Kirsch, F. Faccio, D. Khizbullin, and J. Schmidhuber**, "GPTSwarm: Language agents as optimizable graphs," in *Proc. 41st ICML*, PMLR vol. 235, pp. 62743–62767, 2024. URL: https://proceedings.mlr.press/v235/zhuge24a.html
   - *Why:* models agent teams explicitly as computational graphs and optimizes their connectivity before deployment. This is the closest "team as graph" prior work in the LLM literature.
6. **J. Zhang et al.**, "AFlow: Automating agentic workflow generation," in *Proc. ICLR*, 2025. arXiv:2410.10762. URL: https://arxiv.org/abs/2410.10762
   - *Why:* agentic workflows as code-represented graphs of LLM nodes. Automated topology search raises exactly the question the paper asks: is a generated composition justified?
7. **I. Stoica et al.**, "Specifications: The missing link to making the development of LLM systems an engineering discipline," arXiv:2412.05299, 2024. URL: https://arxiv.org/abs/2412.05299
   - *Why:* argues for specifications and contracts for LLM components, which is the direct motivation for the paper's contract-based stance and its acquisition problem (M5a).
8. **J. Liu, K. Wang, Y. Chen, X. Peng, Z. Chen, L. Zhang, and Y. Lou**, "Large language model-based agents for software engineering: A survey," arXiv:2409.02977, 2024 (v2 2025). URL: https://arxiv.org/abs/2409.02977
   - *Why:* a comprehensive SE-specific survey of agent designs (124 papers in v2). It complements [6]–[8] and would help justify the choice of nine designs.

---

## Scores (1 = poor, 5 = excellent)

| Criterion | Score | Justification |
|---|---|---|
| (i) Novelty | 3 | Slicing agent teams with hybrid face-value semantics and depth is a fresh framing. The underlying ideas (A-G contracts, convex/SESE regions, minimal conflict sets, minimal cut sets) are classical, and that relationship is under-discussed. |
| (ii) Rigor | 3 | The formal core is careful and mechanically cross-checked. The empirical claims, however, are largely by construction (M1), the failure model omits commission failures (M2), and the baselines are weak (M4). |
| (iii) Relevance | 2 | The question matters to practitioners. The answer rests on hand-declared Boolean contracts, unfaithful encodings, and no contact with real executions or framework code (M3, M5). |
| (iv) Verifiability & Transparency | 4 | Exemplary package, pre-registration and conformance testing. Marked down for no anonymized link, a dirty-worktree result file, and a PDF/table mismatch. |
| (v) Presentation | 2 | Very dense for TSE's SE readership. Overloaded symbols, terms used before definition, an incoherent fork-join example, and appendix tables after the references. |

## Recommendation

**Major revision.**

The formalism and the artifact are a solid base, and the slicing idea could become a useful design-review tool for multi-agent SE systems. The paper as submitted, however, overstates what its experiments show:

- the headline numbers are fixed by benchmark design;
- the real-design findings follow largely from the encoding protocol and an omission-only failure model;
- several published designs are encoded unfaithfully.

A revision that makes the following changes would be a strong TSE paper:

- adds commission failures;
- repairs and independently checks the encodings;
- compares against a fault-aware must-analysis and minimization-based localization;
- demonstrates the approach on at least one real framework or execution-trace dataset;
- substantially improves readability.
