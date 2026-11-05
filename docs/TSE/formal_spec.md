# Formal specification: agent slicing (Phase 1 gate)

> **Status after two review rounds (2026-11-04).** The paper (`main.tex`, Section III and Appendix A)
> is now the authoritative statement. Main changes against this Phase-1 note: findings count only when
> *confirmed* by lifting a witness to a run of the team (Def. 7); depth and minimal slices are defined
> over confirmed findings, which are monotone in the slice (Thm 5c, incl. robust keys via
> unsuppressed robust candidates); derived guarantees are per exit and T2(c) concerns a disjunctive
> exit; T5(c) (witness hull) was removed as vacuous; T7 states complexity per key kind (robust keys
> in D^p, NP- and coNP-hard) and adds depth (NP-complete); T4(b) covers only view-disjunctive analyses;
> T1 and T6 are propositions; liveness is no longer part of Definition 1.


Status: definitions and theorem statements are final for the implementation; full
proofs are in the paper appendix (`main.tex`, Appendix A). Every definition has a
code counterpart, listed in brackets.

## 1. Teams

**Vocabulary.** A finite set of *properties* 𝒫 (facts about the work product or
its lineage, e.g. `design`, `tests_pass`). A team declares *goals* Φ ⊆ 𝒫 that every
released output must have, *critical goals* Φc ⊆ Φ, a *fault budget* f ∈ ℕ, and
*input facts* In ⊆ 𝒫. A finite set of *oracles* Orc names the reasoning engines
(e.g. one LLM deployment) that agents use.

**Definition 1 (Team).** `T = (N, E, ι, ω, κ, req, gua, decl, orc, rt, jn)` where
(N,E) is a finite DAG with unique source ι (input) and unique sink ω (output);
κ(n) ∈ {agent, gate} (ι, ω are gates); req(n), gua(n), decl(n) ⊆ 𝒫 are the
*requirements* (assumptions), *guarantees* and *declared evidence* of n;
orc(n) ∈ Orc for agents; rt(n) ∈ {fork, switch} (a fork delivers to all successors,
a switch to exactly one); jn(n) ∈ {all} ∪ {q ∈ ℕ≥1} for nodes with in-degree ≥ 2
(`any` = 1). Conventions: gua(ι)=In, req(ι)=∅; req(ω)=Φ, gua(ω)=∅.
[`slicing/model.py: Team, Node`]

Well-formedness: every node lies on an ι→ω path and is *live* (reached in some
fault-free run, Def. 2). [`Team.validate`, `semantics.live_nodes`]

## 2. Exact semantics

**Definition 2 (Run).** A run ρ = (W, C, F) chooses W(n) ∈ succ(n) for each switch,
a contributor set C(n) ⊆ in(n) for each node with in-degree ≥ 2, and a failure set
F ⊆ Orc with |F| ≤ f. A run is *fault-free* if F = ∅. Given ρ, in topological order:
* ι is reached; edge (u,v) is *delivered* iff u is reached and (rt(u)=fork or W(u)=v);
* v ≠ ι is reached iff its delivered in-edges D(v) satisfy jn(v)
  (all: D(v)=in(v); q: |D(v)| ≥ q), and then C(v) ⊆ D(v) with |C(v)| ≥ q
  (all: C(v)=in(v)); single in-edge: C(v)=D(v);
* content c(v) = ⋃_{(u,v)∈C(v)} o(u), with c(ι)=∅;
* v *applies* iff req(v) ⊆ c(v) ∪ decl(v) and (κ(v)=gate or orc(v) ∉ F);
* output o(v) = c(v) ∪ gua(v) if v applies, else c(v).
[`semantics.evaluate_run`]

Facts persist along the contributing lineage. Declared evidence is local: it
counts for applicability but never flows on. A guarantee is *conditional*: it holds
only when the component's requirements are realized and its oracle has not failed.

**Definition 3 (Symptoms, safety).** The symptoms Sym(T) are the keys
* (assume, v, p): some fault-free run reaches v ∉ {ω} with p ∈ req(v) ∖ (c(v) ∪ decl(v));
* (goal, ω, φ): some fault-free run reaches ω with φ ∈ Φ ∖ c(ω);
* (robust, ω, φ): (goal, ω, φ) ∉ Sym(T) and some run with |F| ≤ f reaches ω with
  φ ∈ Φc ∖ c(ω).

T is *safe* iff Sym(T) has no goal or robust key; *clean* iff Sym(T) = ∅.
[`semantics.symptoms`]

**Model semantics and Lemma W (worst case).** A model adds free evidence
E: N → 2^𝒫 with c(v) ∪ decl(v) ⊆ E(v) (realization) and lets v apply iff
req(v) ⊆ E(v) and its oracle has not failed; the output satisfies goal φ iff
φ ∈ E(ω). Content is monotone in E, so the minimal evidence E(v) = c(v) ∪ decl(v)
is the worst case: a goal can be missed in some contract-respecting model iff it is
missed in some run. [`oracle.model_violations` checks this by enumeration]

**Lemma H (halting).** Adding halts (a reached node delivering nothing) creates no
new symptom: any symptom of a halting run occurs in a non-halting run with smaller
contributor sets. So halts are omitted from runs.

**Lemma M (minimal choices).** Content is monotone in contributor sets and
antitone in F. For existence of a symptom it suffices to enumerate minimal
contributor sets (exactly q contributors) and maximal failure sets.
[`semantics` enumerates only these]

## 3. Slices and the hybrid semantics

**Definition 4 (Slice).** A slice is a nonempty σ ⊆ N that is *convex*: for
u, w ∈ σ every u→w path stays in σ. Connectedness is not required. Entry edges
In(σ) and exit edges Out(σ) cross the boundary. hull(S) = anc*(S) ∩ desc*(S) is the
smallest convex superset. [`slices.is_convex, hull`]

*Convexity lemma.* If σ is convex, no outside node is both a descendant and an
ancestor of σ; hence the outside predecessors of members have no member ancestor.

**Definition 5 (Hybrid semantics H_σ).** Members of σ behave exactly as in
Def. 2. Every outside node is *taken at face value*: it is reached iff it is ι or
some in-edge is delivered, all its delivered in-edges contribute, it always applies,
never fails, and delivers on all out-edges. Every entry edge into a member v is
always delivered and carries env_σ(v) = ⋃ o(u) over all outside predecessors u of v.
Runs of H_σ choose only member switches, member contributor sets and F ⊆ orc(σ).
Findings F(σ) := Sym(H_σ) (Def. 3 evaluated in H_σ at every node).
[`semantics.findings(team, sigma)`]

Special cases: H_N = T (no outside), so F(N) = Sym(T). H_∅ is the pure face-value
world: c(v) = cone(v) = In ∪ ⋃_{u∈anc(v)} gua(u).

**Definition 6 (Agent-level analysis AL).** AL = ⋃_{v∈N} F({v}), the findings of all
singleton slices. *Proposition 1 (characterization, as proved in the paper):* F(∅) ⊆ F({v}), and every
key of F({v}) ∖ F(∅) has a witness in which v does not apply or v is a switch (a join's
singleton sees the union of its inputs, so join policies never matter at agent level).
The earlier informal reading was: F({v}) consists of
(i) F(∅): requirements not claimed by any ancestor and goals not claimed by any
ancestor of ω; (ii) if v's own requirements are unmatched, the downstream
requirements and goals that only v claimed; (iii) if v is an agent, the critical
goals for which v is the only claimer (single point of failure).
[`analysis.agent_level`]

**Definition 7 (Depth, localization).** For a key κ: depth(κ) = 1 if κ ∈ F(∅),
else min{|σ| : κ ∈ F(σ)}. The minimal manifesting slices MMS(κ) are the
inclusion-minimal σ with κ ∈ F(σ) (and {v} when κ = (·, v, ·) ∈ F(∅)).
A blind spot is *hidden at agent level* iff its depth is ≥ 2.
[`analysis.localize`]

**Definition 8 (Slice contracts).** For σ and environment E (a property set given
to every entry edge):
* derived entry assumptions A_σ = {(v,p) : v∈σ, p∈req(v), some internal fault-free
  run of σ with empty environment leaves p ∉ c(v) ∪ decl(v)};
* derived guarantee G_σ(E) = ⋂ over internal fault-free runs and delivered exit
  edges (u,·) of o(u) when every entry carries E; robust guarantee G^f_σ(E) likewise
  over runs with |F| ≤ f;
* naive (agent-level) guarantee N_σ(E) = E ∪ ⋃_{m∈σ} gua(m) restricted to members
  that are ancestors of the exit;
* emergent obligations X_σ: the relational conditions whose violation makes
  G_σ(E) ⊊ N_σ(E) — join coverage (S2/S3), non-bypass (S5), conditional backing
  (S6b), oracle independence and robust backing (S4/S6a). The gap
  N_σ(E) ∖ G_σ(E) classified by mechanism is reported as X_σ violations.
* A declared contract (A^d, G^d) is *valid* iff G^d ⊆ G_σ(A^d) and every member
  requirement holds in every internal run when the entries carry A^d.
[`contracts.derived_contract, naive_contract, declared_valid`]

The derived contract is in general *not* a single pair (A,G): two independent
members give guarantees under different assumptions (see T2(c)). Its exact form is
the boundary relation Beh_σ: for each entry delivery pattern and entry contents (per
entry edge) and failure set, the set of possible (exit deliveries, exit contents,
internal symptoms).

**Definition 9 (Slicing).** A slicing is a family of slices. A *partition slicing*
partitions N and has an acyclic quotient (contracting each part leaves a DAG).
Convexity of the parts is necessary but not sufficient: {a,d}, {b,c} with a→b, c→d
are convex and the quotient has a cycle. [`slices.quotient_is_acyclic`]

## 4. Blind-spot classes

Agent-level classes (depth 1): A1 unowned goal; A2 missing provider; A3 ordering
(provider is not an ancestor); A4 single point of failure (critical goal with one
fallible claimer). S1 interface gap = A2/A3 or a provider in a different view
(property `p@view`).

Slice-level classes:
* S2 joint-coverage gap: a goal is claimed on some branches into an any/quorum join;
* S3 path-merge dilution: a fact is dropped at an any/quorum join and consumed later;
* S4 correlated evidence: claimers of a critical goal share an oracle;
* S5 bypass: a switch routes around the member that claims the property;
* S6a conditional collapse under faults: a gate's critical guarantee rests on a
  fallible agent's provision;
* S6b conditional chain: a goal rests on a chain of conditional guarantees whose root
  assumption is unmatched (the root is visible at agent level; the goal loss is not).

## 5. Theorems (statements)

**T1 Conservativity.** For every team, the singleton slicing reports exactly AL,
and AL is characterized by Prop. 1. Moreover F(∅) ⊆ F({v}) for all v.

**Lemma A (Face value dominates).** For σ ⊆ σ' and a run ρ' of H_σ' whose member
choices restrict to a run ρ of H_σ: every node reached in both has
c_{σ'}(v,ρ') ⊆ c_σ(v,ρ).

**T2 Slice abstraction.** (a) Replacing σ by a macro component whose behavior is
Beh_σ leaves Sym unchanged (keys at outside nodes and ω; member keys are reported
by the macro). (b) (f = 0) If a declared contract is valid and the team in which σ is
replaced by a component that delivers G^d whenever its entries carry A^d (and behaves
arbitrarily otherwise) is safe, then T is safe. [refined while writing the proof:
faults are handled only by the exact relation of (a)/(d)] (c) A single-pair (A,G) contract cannot be exact (counterexample:
two independent members). (d) For a partition slicing with acyclic quotient, Sym(T)
equals the symptoms of the quotient team of macros evaluated in topological order;
with a cyclic quotient, flat (A,G) macro contracts admit circular reasoning that is
unsound.

**T3 Soundness of slice-level checking.** (a) If the slice-level checker accepts with
a family containing N (or with the partition check of T2(d)), T is safe; every
returned counterexample is a run of T. (b) A finding κ ∈ F(σ) whose witness *lifts*
(some run of T agrees with it inside σ, delivers the entry edges it uses and reaches
the symptom node) is a symptom of T. (c) Without a lift, findings can be false
alarms (example: an outside switch makes two entries exclusive).

**T4 Separation.** (a) For each class S2–S6 there is a parametric family of teams
(chains for S4, S6a, S6b; fork-join for S2, S3; switch regions for S5) with AL = ∅
(or, for S6b, AL without the goal key) that are unsafe or unclean, and with a slice of
size ≤ 2 (S2–S5) or the hull of provider and consumer (S6) that manifests the key.
(b) Fooling sets: for S2, S4, S5, S6a there are safe teams whose singleton *views*
(own contract, oracle, policy, and the set of properties claimed upstream) cover
every singleton view of the unsafe team; so no conjunction of predicates on singleton
views is both sound and free of false alarms. (c) Recovery: every AL finding at v is
in F(σ) for every slice σ ∋ v (live teams).

**T5 Localization.** (a) If κ ∈ Sym(T), MMS(κ) is nonempty. (b) MMS(κ) need not be a
singleton set (S2 with two branches has two minimal slices); it is unique iff the
intersection of the minimal manifesting slices manifests κ. (c) For every witness
run of κ in T, the hull of its contributing lineage to the symptom node manifests κ
(for a robust key: κ or the stronger goal key of the same property; refined while
writing the proof, the alternative never occurred in E1),
so depth(κ) ≤ the smallest witness-hull size. (d) Monotonicity: if κ ∈ F(σ) and its
witness lifts to H_σ' (σ ⊆ σ'), then κ ∈ F(σ'); in particular when σ'∖σ contains no
switch and no all/quorum join. (e) Monotonicity fails in general (counterexample with
an outside switch).

**T6 Overlap and cover.** Keys are slice-independent, so findings from overlapping
slices merge by key without double counting; a slice never certifies the absence of a
key, so findings cannot contradict. The minimal manifesting slices of a family are
the inclusion-minimal manifesting members. A family detects every key of depth ≤ k
whose MMS member is contained in one of its slices with a lifting witness.

**T7 Complexity.** (a) Deciding κ ∈ Sym(T) is NP-complete (safety coNP-complete),
already without forks and with f = 0 (reduction from CNF-SAT). (b) Evaluating F(σ)
takes O(R_σ·(|N|+|E|)·⌈|𝒫|/w⌉), R_σ = number of internal minimal runs, which is
polynomial when the number of member choice points and |orc(σ)|^f are bounded.
(c) A DAG can have 2^Θ(|N|) convex subsets; all convex subsets of size ≤ k can be
enumerated in O(|N|^k) hull tests. (d) Singleton, window, band and region strategies
produce O(|N|) slices, computable in O(|N|·(|N|+|E|)) total.

**T8 Incremental recertification.** Let δ change node a. The findings of σ are
unchanged unless σ ∩ Dep(a, δ) ≠ ∅ where Dep = {a} for changes of oracle, kind, route
or join policy; {a} ∪ anc(a) for changes of req(a) or decl(a); and
{a} ∪ anc(a) ∪ desc(a) for changes of gua(a). An edge change (u,v) is treated as a
change of both endpoints with the old and new ancestor relations, and slices that
lose convexity are dropped.

## 6. Running example

*Chain.* RA → AR → DV → SR → TS → ω with f = 1 and critical goal `tests_pass`.
RA, AR, DV, SR are agents on the same LLM oracle `g`; TS is a deterministic test
runner (gate) with req {tests}, gua {tests_pass}; DV provides {code, tests}.
AL: every requirement is claimed upstream, every goal is claimed, the critical goal
is claimed by a gate → no finding. Slice {DV, SR, TS}: if `g` fails, DV does not
provide `tests`, so TS does not apply and `tests_pass` is missing: key
(robust, ω, tests_pass), depth 3, class S6a. Repair: an independent deterministic
coverage gate between DV and TS.

*Fork-join.* RA forks to AR and TM (threat modeler); AR → DV, TM → ST (security
tester); DV, ST → RG (release gate) → ω, with RG `any` ("release on first approval").
Goals `implemented` (DV) and `sec_tested` (ST). AL: silent. Slices {ST, RG} and
{DV, RG} manifest (goal, ω, implemented) / (goal, ω, sec_tested): S2, depth 2, two
minimal slices (T5b). The band {DV, ST} does not manifest it (RG outside is taken at
face value).
