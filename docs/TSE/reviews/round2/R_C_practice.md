# Second-Round Review of "Agent Slicing: Localizing Blind Spots in Declared-Contract Models of Multi-Agent AI Teams"

**Reviewer C (round 2).** I review from two angles: as a practitioner who builds LLM multi-agent systems for software engineering, and as a reader standing in for a software-engineering PhD student who is not a formal-methods specialist.

**Material read:**

- the revised PDF (22 pages) and `main.tex`;
- the three round-1 reviews and the authors' response matrix;
- `experiments/architectures.py`, `experiments/running_example.py`, and the result files under `results/`.

---

## Summary

The paper models a team of LLM agents and deterministic gates as a DAG. Nodes carry requirement, guarantee and declared-evidence sets, along with fork/switch routing, `all`/`any`/quorum joins, and a fault budget *f* over shared model "oracles". A *slice* is a convex set of nodes. It is analyzed exactly, and the rest of the team is taken at face value.

The main revision is the notion of a **confirmed finding**: a slice witness that lifts to a run of the whole team. Confirmed findings are sound and monotone under slice growth, and depth and minimal confirming slices are now defined over them. The revision also adds:

- **New baselines:**
  - a global fault-aware must-analysis (B6);
  - the whole-team witness deviation set (B2-dev);
  - whole-team witness plus greedy slice shrinking (B2+shrink).
- **New experiments:**
  - a mutation benchmark of 840 small teams with randomly applied "engineering changes" (E8);
  - a hand-off-distance sweep (E4b).
- **Revised E3 encodings and new text:** the encodings of nine published designs were revised, and the paper gains a notation table, a redesigned fork-join example and a "Using the findings" paragraph.

Headline claims:

- **Hidden defects:** 32.4% of mutation-induced symptoms are hidden at agent level.
- **Detection:** B6 finds 100% of the hidden symptoms but 2.8% of its findings are false. Confirmed slicing finds all of them with no false findings.
- **Localization:** the SL strategy returns an exact minimal slice in 91.4% of cases, and B2+shrink in 100%.
- **Published designs:** 6 of 9 encoded designs contain a defect that "only multi-agent slices reveal".

The revision is substantial and honest in many places. The formal story is now much sounder: confirmation plus monotonicity fixes the round-1 problem that raw slice findings were neither sound nor complete. Several of my round-1 concerns are resolved.

From the practitioner's side, however, the central weaknesses remain:

1. The failure model still cannot tell a gate that *fails closed* from one that *falsely certifies*, and this is exactly the distinction the paper's motivating example depends on.
2. The E3 protocol still makes nearly every design unsafe by construction, and the proposed repairs are partly artifacts of how gates were encoded.
3. The revised story now shows that the paper's own slicing strategies are dominated: on detection by a linear must-analysis plus confirmation, and on localization by "exact checker + shrink". The paper has not yet re-centred its contribution on that finding.
4. There is still no contact with a real framework, real orchestration code, or real execution traces.

---

## Assessment of round-1 concerns

| # | Round-1 concern | Status | Comment |
|---|---|---|---|
| M1 | Headline numbers fixed by benchmark design | **Partly resolved** | The 45.5% prevalence and k = 4 saturation are gone from the abstract. E4b now *measures* depth = ℓ + 2, and the injected benchmark is honestly reframed as a per-class consistency test (p. 9, p. 11). This is good. The new headline, "32.4% hidden", is still a function of the authors' operator mix: Table VII shows that relaxing a join gives 66.3% hidden and removing an edge gives 17.6%, and the operators are applied uniformly. The teams have 6 or 10 inner nodes. Calling these "naturally arising defects" (abstract, p. 2) is not justified (Major 3). |
| M2 | Omission-only failure model; S6a is fail-closed liveness | **Not resolved** | The response re-reads properties as semantic claims, so that a failed oracle means "the property does not hold" (p. 3). This is a reinterpretation, not a model change. It still cannot distinguish a gate that rejects (goal visibly absent) from a gate that accepts on bad input (goal falsely claimed). See Major 1. |
| M3 | Unfaithful encodings; protocol guarantees S6a | **Partly resolved** | The following are fixed or improved: debate now has a revision round; MetaGPT and AgentCoder gates require code; Agentless validates before selecting; the ChatDev text is corrected; AutoGen is flagged as unrolling-dependent. The following are not done: an alternative critical-goal protocol, unrolling more than once, an independent encoder, a traceability table, and a figure of the encoded graphs. MapCoder and Agentless still omit the very execution-based checks that would mitigate the reported finding (Major 2). Under the documented configuration all 9 of 9 designs are still unsafe, and 8 of 9 are safe at f = 0, which is unchanged from round 1. |
| M4 | Weak baselines (must-analysis, minimization-based localization, diagnosis/FTA) | **Resolved, with consequences** | B6, B2-dev and B2+shrink were added, and Reiter and Ruijters & Stoelinga are cited. This is an exemplary response. The consequences for the paper's positioning, however, are not drawn (Major 4). |
| M5 | Practitioner relevance: contract acquisition, validation on traces, misdirected scale, actionability | **Mostly not resolved** | (a) Acquisition: one sentence on p. 16 ("A practitioner obtains contracts from ... prompts, tool schemas, orchestration code"), with no demonstration. (b) MAST/trace validation: deferred to future work. (c) Scale to 5,011 nodes: still unmotivated. (d) Actionability: there is a repair paragraph and one repaired example. That example is safe only because its test gate does not consume the code (Major 2). |
| M6 | Compositional certification (T2b) needs f = 0 | **Partly resolved** | The restriction is now in the theorem statement (Thm. 1(b), p. 6). It is still absent from the introduction and the conclusion, both of which advertise "compositional abstraction" without the caveat. Thm. 1(d) handles failures through boundary behaviours, but that gives the developer no contract they could write down. |
| M7 | Readability: notation table, overloading, fork-join example, worked computation | **Partly resolved** | Done: the notation table (Table I), the fork-join example (DV now forks code to both CR and ST), the overview subsection III-A, and the Table II naive-versus-derived contracts. Remaining: dual theorem numbering (new), lemma letters (W, M, A) still used in Table IV, new symbol overloads, a still unsplit Definition 6, no figure for Example 1 or Thm. 4(d), and no step-by-step slice computation (Minor 1–10). |
| Related work | Eight suggestions | **Partly resolved** | Added: Reiter, FTA, N-version programming, Knight & Leveson, Littlewood & Miller, OCRA/AGREE and CEGAR. This is good. Not added: GPTSwarm, AFlow, Kim et al. (ICML 2025) on correlated LLM errors, and Stoica et al. on specifications. The response says Kim et al. "could not be verified via our pipeline". It is in PMLR vol. 267 (https://proceedings.mlr.press/v267/kim25e.html), and it bears directly on the "use distinct models" repair the paper now recommends (Major 5). |
| Minor (36 items) | | **About half addressed** | Fixed: Fig. 3 axes; precision is now reported; degenerate Wilcoxon tests removed; appendix floats; the S1v naming; the "convex convex" duplication. Not fixed: arXiv citations of archival papers; the garbled "PĂsĂreanu"; the all-caps reference [57]; citation numbers before names in Table XII; no figure of the encoded graphs; no anonymized artifact link; all result files still record `"dirty_worktree": true`. |

---

## Strengths

1. **Confirmed findings are the right fix.** Example 1 and Thm. 4(c)/(d) make the approximation status explicit, and the paper now reports only witnesses that lift (Def. 7). Depth and minimal slices are then semantic (p. 7) rather than artifacts of face value. A PhD student can now follow why the singleton slice is "agent level" (Proposition 1) and why larger slices never lose a confirmed finding.
2. **Honest baselines and honest reporting of what they show.** The paper now says plainly that "Detection alone does not need slices" (p. 14). It reports that B6 detects 100% of hidden symptoms in linear time, that the whole-team checker is the cheapest method on switch-free teams (Table XIV), that H3.1 is not supported, and that incremental re-verification is slower in 18.1% of changes. Few papers in this area are this candid.
3. **E4b turns a design parameter into a measurement.** Depth = ℓ + 2 for S4/S6a/S6b and depth = 2 for joins (Fig. 3, Table XVIII) is a clean, useful result. "How large should slices be?" (p. 16) is the most actionable sentence in the paper.
4. **The redesigned running example works.** The chain and fork-join examples (Fig. 2) are now coherent, and Table II shows naive versus derived contracts. The "repair that fails" (a downstream test generator moves the depth from 3 to 4) is a nice touch, although see Major 2.
5. **Verifiability is again excellent.** The paper provides: three independent oracles; 219,200 team-check pairs with no mismatches; logged real bugs found by conformance testing (p. 10–11); proof mutants; and generated macros for every number. I could trace the E3 table to `experiments/architectures.py`.

---

## Major concerns

### Major 1. The failure model still conflates "the gate rejects" with "the gate certifies wrongly", which undermines the motivating example and the E3 conclusions.

The authors' answer to my round-1 M2 is the paragraph on p. 3:

> "When an agent's model fails ... the property it claims does not hold. A downstream test runner that requires tests then cannot establish tests_pass, even if it executes and reports success. So the model covers errors of commission."

This redefines the property; it does not model commission. The output of the analysis is still a single kind of symptom, "the critical property is missing at ω". That symptom does not say whether the team **visibly lacks** the claim or **silently presents it as established**. To a practitioner these are opposite situations:

- **Fail-closed (benign).** Consider MapCoder in the authors' own encoding (`SampleIO` gate requires `code`, critical `samples_pass`). The sample I/O come from the problem statement (the authors themselves note this, p. 13 and `architectures.py`). If the Coding agent's model "fails", the sample tests fail, the gate reports failure, and nobody believes `samples_pass`. The paper still reports a hidden S6a robust key at depth 2 (Table XII). This is the gate doing its job, not a blind spot.
- **Fail-open (dangerous).** Consider MetaGPT or AgentCoder. The LLM writes weak tests, the runner reports green, and the team ships with a claimed but false `tests_pass`. This is the case named in the abstract ("a test gate whose tests were written by a fallible agent").

The model assigns both cases the same class (S6a), the same depth and the same minimal slice. It therefore cannot support the abstract's message: it does not tell the user *which* gate is a false certifier.

This matters for actionability. A practitioner who receives "S6a, {Coding, SampleIO}" for MapCoder would be told to "back the gate's input with an independent source" (p. 13). In MapCoder that input is the code under test, so the advice is meaningless.

**Required changes:**

- **(a) Model the gate's observable verdict separately from the semantic property.** For example, a gate guarantees a *claim* c̃ whenever it applies, and the semantic property c only when its inputs' semantic properties hold. Report "claimed but unestablished" separately from "visibly missing". This is a small extension of Def. 2 and Def. 3 (one extra bit per property), and it is the single change that would make the paper relevant to how practitioners reason about test gates.
- **(b) Rerun E3 and the running example with it.** Report which S6a findings are fail-open (MetaGPT, AgentCoder, Agentless) and which are fail-closed (MapCoder, ChatDev's `Execute`→`runs`).
- **(c) Alternatively, if (a) is not done,** remove "a test gate whose tests were written by a fallible agent" from the abstract as a motivating defect. In addition, state in Section II-C and in the threats section that a robust key does not distinguish false certification from rejection.

### Major 2. E3 is still close to tautological under P3 with f = 1, and the recommended repair is an encoding artifact.

1. **The protocol makes 9/9 designs unsafe.** P3 makes the claim resting on executed tests critical, with f = 1 and one shared backbone. Under this protocol any design whose critical claim is downstream of *any* LLM output is unsafe. Table XIII confirms that every design is unsafe in the "doc.", "shared" and "distinct" columns, and that 8 of 9 become safe at f = 0. The finding is "the critical claim depends on an LLM". A practitioner can read that off the architecture diagram; no analysis is needed. The informative content of E3 is therefore only the *class and minimal slice*, and those are determined by encoding choices. Round-1 M3 asked for an alternative critical-goal protocol, which was not done.

2. **The "independent source" repair works only because the running example's test gate ignores the code.** In `running_example.py`, `TS` requires only `tests`, not `code` (line 18). The "independent test designer on another model makes the chain safe (0 symptoms)" (p. 13) therefore holds only because the gate never consumes DV's code. Yet the response matrix states that, for E3, P3 was made consistent so that "gates require code", and in E3 MetaGPT's `TestRun` and AgentCoder's `Executor` now do require `code`.

   If the running example were encoded consistently, DV's failure would still lose `tests_pass` after the repair, and the chain would remain unsafe. The same holds for AgentCoder: the text says the repair is "as AgentCoder does for its tests but not for its code" (p. 13). An independent source for *the code under test* is N-version programming, not a design tweak.

   As modeled, then, the S6a pattern in E3 has no practical repair other than f = 0. That again points to Major 1.

3. **Omitted mitigations manufacture findings.**
   - **Agentless.** Agentless executes each generated reproduction test on the *original* repository and keeps only tests that reproduce the issue, then normalizes and votes. This is a deterministic, execution-based check of the LLM-written test. `architectures.py` omits it, and `ReproGen` feeds `Validate1/2` directly, which yields the reported S6a {ReproGen, Validate1, Validate2}. Encoding the filter as a gate between `ReproGen` and the validators is the faithful choice, and it may change the class.
   - **MapCoder.** Debugging is invoked only when the sample tests fail; this is a switch on the gate's verdict. The encoding runs Debugging unconditionally and invents a goal `debugged` for it.
   - **ChatDev.** Each phase is still a single agent, although ChatDev's central mechanism is the instructor/assistant dual-agent chat.
   - **AutoGen.** The encoding is still not traced to a documented application, and the authors concede that the finding depends on a single unrolling.

4. **Traceability and independence are still missing.** There is no figure of the nine encoded graphs, no node-to-source table, no second encoder, and no unrolling beyond one round. The threats section acknowledges this, but acknowledgement is not mitigation. For a TSE paper whose only contact with real systems is E3, this is a key gap.

**Required changes:**

- **(a) Make the running example consistent with P3.** Either `TS` requires `code`, or the paper justifies why a test runner does not consume the code. Then re-derive the repair claim.
- **(b) Report E3 under at least one alternative critical-goal rule.** For example, critical = the design's *final* artifact claim, or a critical goal chosen by a second encoder. Also report under two-round unrolling for the iterative designs, and say which findings survive.
- **(c) Encode Agentless's reproduction-test filter and MapCoder's conditional debugging,** or justify their omission explicitly in the table.
- **(d) Add an appendix figure of the nine encoded graphs and a traceability table.** The table should map each node and edge to a section, figure or code location in the source. Have at least one design re-encoded by someone outside the author team and report agreement.

### Major 3. The new headline (32.4% hidden, "naturally arising defects") repeats the round-1 problem in a weaker form.

The mutation benchmark is a clear improvement: depth and class are no longer chosen by the injector. But:

- The teams are produced by the authors' generator in 7 topologies, with 6 or 10 inner nodes and contracts drawn from a must-bound.
- The seven change operators are the authors' choice and are applied uniformly.
- The hidden share varies from 17.6% to 66.3% by operator (Table VII).

"32.4% hidden" is therefore a property of this operator mix, not of how multi-agent teams evolve. "Naturally arising" (abstract and p. 2) suggests defects found in real systems; "randomly mutated synthetic teams" is the accurate description.

The abstract and the RQ2 answer also state the number with no qualifier, exactly as the round-1 45.5% was stated. A practitioner reading the abstract will take "a third of multi-agent defects are invisible to per-agent review" as an empirical claim.

**Required changes:**

- Replace "naturally arising" with "mutation-induced" or "produced by random changes to generated teams".
- Qualify 32.4% in the abstract and introduction as conditional on the operator set. Better, lead with the per-operator range from Table VII.
- Report the hidden share separately for 6- and 10-node teams, and justify the uniform operator mix, or weight the operators by an argument about which changes are common in practice. For example, prompt edits and model swaps are far more frequent in practice than "gate to agent".

### Major 4. The revised evidence shows that slicing *strategies* are dominated; the paper should re-centre its contribution accordingly.

The new baselines produce three results:

- **Detection.** B6 (linear, global) finds 100% of hidden symptoms (Table VI). Its only defect is 2.8% false findings, and confirmation (Def. 7) could equally be applied to B6's witnesses.
- **Localization.** B2+shrink is exact in 100% of mutation cases and in 100% of injected hidden cases (Tables VI, IX, X). SL is exact in 91.4% and 86.9% respectively, and only 34.3% on S4. The Discussion (p. 16) itself recommends "a whole-team witness shrunk slice by slice" for diagnosis.
- **Cost.** On switch-free teams, B2 is cheapest (Table XIV). On mixed teams, SL times out on 32 of 90 teams.

So the practically best pipeline the paper supports is: **exact whole-team check (or must-analysis) → confirm → shrink to a minimal confirming slice.** The slicing strategies (window, band, region, goal-directed, SL), which the contribution list, Fig. 1 and much of Section III present as the method, are not needed for this.

The genuinely novel and valuable parts are the following, and none of them depends on choosing a slicing strategy:

- confirmed findings and their monotonicity;
- depth as a semantic measure, with depth = ℓ + 2;
- the minimal confirming slice as an explanation;
- the emergent-obligation classification.

The current narrative (title, abstract, contributions, RQ3 "how do slicing strategy and slice size trade...") still sells strategies.

**Required changes:**

- Restructure the contribution statement and the abstract around the pipeline the evidence supports: a detector, then confirmation, then shrinking to a minimal confirming slice with an obligation class.
- Present strategies as one way to generate candidates, useful mainly when no whole-team check is affordable (choice-rich teams). Show *that* regime explicitly. On mixed teams B2 also times out on 36 of 90 teams; does shrinking from a B6 witness work there?
- Apply confirmation to B6 and report "B6 + confirm + shrink" as a row in Tables VI, IX and XIV. If that row matches SL+shrink at linear cost, say so. It would be the most useful practical result in the paper.

### Major 5. Practitioner relevance is still argued rather than demonstrated.

Round-1 M5 asked for at least one of (a) contract extraction from a real framework or (b) validation against execution traces (MAST). Neither was done, and both are deferred to future work (p. 17). The "Using the findings" paragraph claims that contracts can be obtained "from prompts, tool schemas, orchestration code", but gives no example.

My concrete minimum for a TSE practitioner audience:

1. **One real system, end to end.** Take one open-source multi-agent SE pipeline whose orchestration is code (a LangGraph `StateGraph`, a MetaGPT role set, or the Agentless repository). Extract the graph mechanically, and declare contracts from its schemas and prompts. Show the confirmed findings and the minimal slices, and say whether the maintainers' issue tracker or the published failure analysis mentions the corresponding failure.
2. **One small trace check.** Pick 20–50 annotated MAST traces of ChatDev or MetaGPT that are labeled with inter-agent failure modes. Report whether the minimal confirming slices of the encoded design contain the agents that MAST attributes the failure to. Even a negative result would be informative.
3. **Scale.** E5 goes to 5,011 nodes, while every real design in the paper has 5–9 nodes. Either motivate thousand-node teams with a citation or an example, or replace the headline scalability claim with realistic choice-rich teams of 10–50 nodes with loops unrolled 2–3 times. That is where a practitioner would hit the cost wall (Table XIV, mixed).
4. **Correlated errors.** The repair "suggests distinct models for redundant claimers" (p. 16), and the Table XIII "distinct" column, assume that distinct providers fail independently. Kim et al., "Correlated errors in large language models," ICML 2025 (PMLR 267:30038–30066), report substantial error correlation *across* providers. The paper already cites Knight & Leveson for the classical version of this point. Add Kim et al. and qualify the "distinct models" repair and the f-budget-per-oracle model accordingly.

---

## Minor concerns

### Presentation and readability

1. **Dual theorem numbering (new, pp. 2–8, 13, 17–18).** Theorems are numbered 1–6 but carry legacy tags: "Theorem 1 (Slice abstraction, T2)", "Theorem 2 (Soundness, T3)", "Proposition 1 (T1)", "Theorem 4 (Localization, T5)", "Theorem 6 (..., T8)". The text then mixes the two schemes. The contributions list says "(T2) ... (T3) ... (T8), together with two propositions (T1, T6)". The RQ1 answer box says "T3b, T5c, T4a, T2d, T2c", while Table V says "Thm. 3c, Thm. 2b, Thm. 4c, Thm 1d". For example, "(T4a)" in the RQ1 box means Theorem 3(a). This is the single most confusing thing in the revision for a non-specialist. Drop the T-tags entirely.
2. **Lemma letters persist.** Lemmas are numbered 1–4 in the text but tagged "(Worst case, W)", "(Minimal choices, M)" and "(Face value dominates content, A)". Table IV's "Used in" column says "Lemma A, M", "Lemma W", "T4c, T5d, Lemma M". The response matrix says these were unified (A-m7); they were not.
3. **New and remaining symbol overloads.**
   - *N*: the node set, and also N_σ,e the naive guarantee (Def. 9, Table II "Naive N_σ").
   - *A*: A_σ entry assumptions, A^d declared assumptions, classes A1–A4, and Lemma tag A.
   - *S*: classes S1–S6 and the slice family 𝒮 in Algorithm 1.
   - *F*: the failure set F, and the raw findings ℱ(σ).

   Rename the naive guarantee (for example ν_σ,e) and the classes (for example "agent-visible V1–V5" and "hidden H1–H6").
4. **"Model" and "oracle" each have three meanings.**
   - "Model" means the language model (p. 1), the contract-respecting *model* of Def. 4 (p. 4), and the "model oracle" (p. 9).
   - "Oracle" means an agent's LLM backbone, orc(n), and also the three ground-truth checkers ("model oracle", "replay oracle", "run oracle", p. 9).

   A reader meets "the model oracle enumerates contract-respecting models" two pages after "an agent's model (its oracle)". Call Def. 4 an "evidence-extended run", call orc(n) the agent's "backbone", and call the ground-truth checkers "reference checkers".
5. **Notation table (Table I, p. 3)** omits the following, all of which a reader needs on pp. 5–7:
   - hull, convexity, entry and exit edges;
   - env_σ;
   - A_σ, G_σ,e, G^f_σ,e and N_σ,e;
   - Beh_σ;
   - "view" and "view-disjunctive";
   - the claimer states route/drop/cond/fault;
   - X (environment).

   Add them, or split the table into "team" and "slice" notation.
6. **Definition 6 (p. 5)** still packs four assumptions into one sentence: "Every outside node is reached if it is ι or at least one in-edge is delivered (whatever its policy), all its delivered in-edges contribute, it always applies, and it delivers to all successors." This was round-1 minor 12. Split it into an itemized list, and annotate Fig. 2(a) with what face value means for RA and AR when σ = {DV, SR, TS}.
7. **The emergent-obligations paragraph (p. 6)** introduces route/drop/cond/fault, four obligations and the class mapping in one paragraph. Table III then relies on it. Give a 4×2 mini-table (claimer state → obligation that excludes it → class).
8. **Example 1 (p. 5) and the Thm. 4(d) example (p. 8)** are prose-only switch/gate constructions. Each needs a three-node figure (round-1 minor 18). Without one, the key insight of the revision, that raw findings can be false and confirmation fixes them, is the hardest passage in the paper to follow.
9. **No step-by-step computation.** There is still no walk-through of Algorithm 1 on {DV, SR, TS}. Table II gives the result but not the derivation. Showing the one run with F = {g} where TS does not apply, and how it lifts, would take a quarter column.
10. **Fig. 2(b), p. 4.** The label "→reviewed" above CR overlaps the panel title "(b) fork-join: release on first approval". Panel (a) is set much smaller than (b), and the guarantee labels under the nodes ("tests →tests_pass") are hard to read at print size.
11. **Table II, p. 6.** "same as above" in the CR, RG row and "G: same" are ambiguous: same as which column? The ST, RG row says derived "G: nothing", but the text says that the naive guarantee contains `sec_tested` and the derived one does not. "Nothing" (beyond the entries) should be stated as such in the header, which it partly is; consider explicit sets.
12. **p. 3, Def. 2.** "v applies if req(v) ⊆ c(v) ∪ decl(v) and v is a gate or orc(v) ∉ F" is clear. But "contributor set" still lacks the one-line intuition "the inputs a join actually uses" (round-1 minor 6).
13. **Section III-I, p. 8.** The sentence "The analogy with program slicing is loose: only goal-directed slices have a slicing criterion, and we prove no projection property for them" is honest. Given it, reconsider whether "slicing" in the title helps an SE reader, who will expect Weiser-style projection.
14. **Answer boxes (pp. 11, 13, 14)** are dense paragraphs of numbers. The RQ2 box has 9 percentages. Limit each box to 3–4 claims.

### Claims and scoping

15. **Abstract: "6 contain a defect that only multi-agent slices reveal".** Table XII shows that B6, a global must-analysis that is not a slice, reports the key for all 9 designs, and B5 reports it for 5 of the 6 hidden ones. The accurate claim is "that agent-level analysis does not report". Fix the abstract, the RQ2 box (p. 13) and the conclusion.
16. **Abstract, "reported findings are never false alarms".** This is true *relative to the declared-contract model*. Because the abstract is read by practitioners, add "of the model".
17. **Introduction and Conclusion** advertise "compositional abstraction over acyclic partitions" without saying that the contract-level rule (Thm. 1(b)) holds only for f = 0, and that robust keys are decided only after composing boundary behaviours (round-1 M6).
18. **p. 13, "The repair is to back the gate's input with an independent source".** See Major 2. As phrased, this suggests independently sourcing the code under test.
19. **p. 16, "Using the findings".** "A practitioner obtains contracts from the artifacts each role reads and writes (prompts, tool schemas, orchestration code)" is an unsupported claim. Either show it once or rephrase it as an expectation.
20. **p. 16, related work: "None of these works reasons about sub-teams as contracts before execution."** GPTSwarm (Zhuge et al., ICML 2024) and AFlow (Zhang et al., ICLR 2025) model agent teams as graphs and optimize sub-graphs before deployment. Stoica et al. (arXiv:2412.05299) argue for specifications of LLM components. Cite them and soften the sentence. These are not "not needed for the claims": they are the closest LLM-side work on teams-as-graphs and on where contracts would come from.
21. **p. 12, protocol P1–P4** is now typeset as a list, which is good. P3's "goals are the quality claims the design's evaluation relies on" is still questionable for Agentless. Its evaluation relies on SWE-bench hidden tests, not on the reproduction test, so `issue_fixed` certified by `Validate1/2` is not the claim its evaluation relies on.
22. **Table XII.** Citation numbers still precede design names ("[1] MetaGPT"; round-1 minor 26). The "Key" column shows only "the most informative finding", chosen by the authors. State the selection rule, or list all confirmed hidden keys per design in an appendix.
23. **Table XIII.** "S5/S6b" and "S3/S6b" entries are unexplained. Does the slash mean two findings, or ambiguity?
24. **p. 13, ChatDev.** The `Testing` agent claims `correct` on its own, which makes ChatDev an A4 by construction. ChatDev's tester reads the execution feedback from `Execute`, so `correct` arguably rests on the gate as well. Explain the choice.

### Experiments

25. **Table VI, p. 11.** B2 + shrink and B2 deviation show "–" for false/reported. Say that they are exact by construction, or give the numbers.
26. **E8 sizes.** 6 and 10 inner nodes only. Report whether the 32.4% and the 91.4% change between the two sizes.
27. **Table XIV / Fig. 4.** Time-outs are now censored and stated, which is good. Mark the censored points in Fig. 4 itself; the plateaus at 60 s on the right panel look like measurements.
28. **E6, p. 14.** The incremental re-verification result (median 1.9×; slower in 18.1% of changes) is honest, but it undercuts "a change invalidates only a computable set of slices" as a practical selling point in the abstract. Scope it there.

### References and artifact

29. Several references still cite arXiv although archival versions exist:
    - MetaGPT [1] (ICLR 2024);
    - ChatDev [2] (ACL 2024);
    - AutoGen [9] (COLM 2024);
    - SWE-bench [10] (ICLR 2024);
    - AgentBench [11] (ICLR 2024);
    - MAGIS [5] (NeurIPS 2024);
    - MapCoder [38] (ACL 2024);
    - Du et al. [40] (ICML 2024);
    - MoA [41] (ICLR 2025);
    - CAMEL [42] (NeurIPS 2023).

    Check also whether Cemri et al. [19] (MAST) now has an archival version.
30. [48] still has the garbled author name "PĂsĂreanu", and [57] is still in all caps. Both were flagged in round 1.
31. There is still no anonymized link to the replication package. Every result file I checked (`results/e1`–`e8`, `running_example.json`) still records `"dirty_worktree": true`. The response says this "is not fixable without committing". It is fixable: commit, rerun `make`, and regenerate the PDF before resubmission.

---

## Scores (1 = poor, 5 = excellent)

| Criterion | Score | Justification |
|---|---|---|
| Novelty | 3 | Confirmed findings, semantic depth and minimal confirming slices with obligation classes are a genuine and now well-founded contribution. The underlying ideas are close to classical minimal conflict sets, minimal cut sets and CEGAR plus delta debugging, and the paper now positions itself against these honestly. The strategies themselves are shown to be dominated (Major 4). |
| Rigor | 3 | The formal side is much improved: sound, monotone confirmation and corrected complexity. The empirical side still has an un-distinguished fail-closed/fail-open failure model (Major 1), a near-tautological E3 protocol with an inconsistent repair claim (Major 2), and an operator-dependent headline (Major 3). |
| Relevance | 2 | The question matters to practitioners, but there is still no real framework, no real orchestration code, no traces, and no demonstrated contract acquisition. The main actionable advice (an independent source for the gate's input; distinct models) is either an encoding artifact or unqualified by evidence on correlated LLM errors. |
| Verifiability & Transparency | 4 | Exemplary oracles, conformance testing, logged bugs and deviation log. Marked down for no artifact link and a dirty worktree in every result file, both raised in round 1. |
| Presentation | 3 | Clearly better: notation table, overview, coherent running example, honest discussion. Still dense on pp. 5–8. Dual theorem numbering and leftover lemma letters are actively confusing, "model" and "oracle" are overloaded, the key examples have no figures, and the narrative still sells strategies that the evidence demotes. |

## Recommendation

**Major revision.**

The authors responded seriously to the formal and baseline criticisms, and the paper is now technically sounder and more honest. The remaining issues, however, are the ones a practitioner would hit first:

- The failure model cannot tell a gate that rejects from one that falsely certifies, which is the distinction the paper's own motivating example depends on.
- The published-design study still answers "does the critical claim depend on an LLM?" with an unavoidable yes. Its recommended repair works only because the running example's test gate ignores the code.
- The best pipeline the paper's evidence supports is detector, then confirmation, then shrinking, not the slicing strategies the paper foregrounds.
- There is still no contact with a real system.

None of these needs a new theory. They need a small extension of the symptom definition, a consistent and traced re-encoding, a re-centred narrative, and one end-to-end case study on real orchestration code or traces.
