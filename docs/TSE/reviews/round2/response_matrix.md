# Round 2: response matrix

Reviews: `R_A_formal.md`, `R_B_empirical.md`, `R_C_practice.md` (all: major revision). Reviewed
version: `submitted_main.tex.txt`. Below, each required change, the action, and where it is.

## Reviewer A (formal)

| # | Required change | Action | Where |
|---|---|---|---|
| A1 | T5(c) false for robust keys (spurious raw goal key hides a true robust finding); shrink returns size 4 for a depth-1 key | Fixed at the root: confirmation uses *unsuppressed* robust candidates (Def. 5 note, Def. 7); T5(c) now states and proves full monotonicity without an escape clause; the reviewer's team is a regression test (shrink returns {y}); conformance monotonicity check no longer exempts robust keys (0 violations). E2/E8/E4b re-run. | Def. 5, 7; Thm 5c and proof; `semantics.findings(robust_always)`, tests |
| A2 | Lifting incomplete (64-witness cap, silent budget) | Lifting now falls back to a direct search over all runs of T with replay verification (complete up to budget); budget exhaustion is counted and reported (E5). Reviewer's 7-switch team is a regression test and an E1 check (K = 2..8); E1 oracle comparison widened to slices of size ≤ 3. | §III-C text, `analysis.confirm`, E1 |
| A3 | Claims ignoring confirmation cost; "agent level finds none" definitional; E5 unconfirmed only | Scope paragraph, RQ1 answer and conclusion say confirmation needs a whole-team search and is not local; "by definition of depth" stated in intro and RQ2 answer, with the team-level count as the measured result; E5 now measures confirmed SL on teams ≤ 200 nodes. Cheap local baseline = B1-raw and B6 (both reported). | §I, §IV-C, §IV-E |
| A4 | Complexity of depth; narrow T4(b); "relations vs pairs" only for set-valued pairs | T7(a) adds: deciding depth ≤ k is NP-complete for assume/goal keys (proof in App. A). T4(b) wording narrowed in RQ1 answer and abstract (abstract no longer mentions it); "set-valued pairs" stated and predicate contracts (OCRA/AGREE) acknowledged. | Thm 7a, App. A, §V |
| A5 | Proof gaps; verification claims | Def. 7 now defines the replay at members the team run does not reach; T4(a) proof states the intermediate nodes' contracts and the case of slices avoiding both interacting nodes; T2(b) allows zero exit delivery; contributions say "paper proofs, some steps sketched"; shared replay function disclosed; dead `conformance.lifts` removed; one numbering scheme (propositions share the theorem counter: Prop. 1, Thms 2–5, Prop. 6, Thms 7–8; lemma letters removed, proofs table relabelled). Not done: Kurshan citation (CEGAR cited). | §III, App. A, `formal/prove.py` |

## Reviewer B (empirical)

| # | Required change | Action | Where |
|---|---|---|---|
| B1 | Claims contradicted by data or definitional | "only multi-agent slices reveal" → "agent-level analysis does not report (the must-analysis does)"; definitional nature stated, team-level count added; conclusion no longer says no baseline names the agents (shrinking is credited); timeout claims replaced by counts from the data; E8 mutations retried until applied. | Abstract, §I, RQ answers, Discussion, Conclusion |
| B2 | Scale E8, size dependence, deep keys, CIs | E8 extended to 20 and 30 inner nodes (8–32 nodes); per-size table with cluster-bootstrap CIs; deep keys counted as hidden and reported; "about a third" removed; size dependence stated in abstract and answers. | §IV-D, Table (mutation by size) |
| B3 | Cost of confirmed method; pipeline baselines | E8 records per-checker timings and shrink time; E5 measures confirmed SL to 200 nodes; the detect–confirm–shrink pipeline is reported (B6 + confirmation + shrinking) and recommended. | §IV-D, §IV-E, Discussion |
| B4 | Reframe E4b | Stated that depth = ℓ+2 follows from gadget shape and convexity (Thm 4a) and that E4b confirms the implementation; host size now varied (5 and 12 inner nodes) to test independence from team size. | §IV-E |
| B5 | Plan record; E3 basis; clean commit | Table of planned hypotheses and outcomes; E4b/E8 labelled exploratory; omitted analyses logged (D8); plan header corrected; E3 removed from the abstract. Not done: second encoder and traceability table (threats); clean tagged commit and DOI (requires the authors to commit; see final report). | §IV-B, experiment_plan.md |

## Reviewer C (practice, clarity)

| # | Required change | Action | Where |
|---|---|---|---|
| C1 | Separate "gate rejects" from "gate falsely certifies" | Not modelled; the paper now states explicitly what a robust symptom means and does not mean (partial correctness), discusses MapCoder's fail-closed sample check, and lists the distinction as future work; the abstract no longer uses the test-gate finding as evidence. | §II-A, §IV-D, Conclusion |
| C2 | E3 non-tautological; repair consistency | E3 removed from the abstract; P3 + f = 1 dependence stated; running-example property `tests_pass` reads "checked by adequate tests", so TS requires only `tests` (repair consistent within the example). Not done: alternative critical-goal rule, 2–3 unrollings, traceability figure, independent re-encoding (threats). | §IV-D, Threats |
| C3 | Re-centre contribution on evidence | Detect–confirm–shrink pipeline presented as the recommended use; strategies as candidate generators for choice-rich teams. | §I, Discussion |
| C4 | Overclaims | "naturally arising" → "induced by random engineering changes"; operator and size dependence stated; f = 0 limit of declared-contract composition in Scope and Conclusion; "never false alarms with respect to the model". | Abstract, §I, Conclusion |
| C5 | Real case; scale motivation; Kim et al. | E5 scale justified (where methods break; realistic range covered by E8). Not done: mechanical extraction from a real codebase and MAST traces (future work). Kim et al. (ICML 2025) could not be verified through our reference pipeline and is not cited. | §IV-E, Conclusion |
| C-minor | Numbering, lemma letters, Fig. 2(b) overlap, bib errors, archival versions | Numbering unified; lemma letters removed; Fig. 2(b) title moved; Păsăreanu and van der Aalst entries fixed; ChatDev, MapCoder, MAGIS now cite their ACL/NeurIPS versions (DOIs verified). | |
