# Conformance and bug log

Every mismatch between the implementation, an oracle, or a theorem check is logged
here with its resolution (Phase 3 gate).

| # | Date | Found by | Symptom | Root cause | Resolution |
|---|---|---|---|---|---|
| 1 | 2026-11-04 | E1 pilot, check "F(∅) ⊆ F({v})" on random wild teams (23/300) | A static key at a node downstream of a single-successor `switch` vanished in the singleton slice of the switch | A `switch` with one successor was treated as choosing nothing, so it delivered on no edge. Every evaluator (enumerator, replay, model oracle) read the same `route` field and shared the convention, so they agreed with one another. | `Team` now normalizes a switch with < 2 successors to a fork. Re-run: 0 mismatches on 1,000 wild teams. Lesson recorded as a threat to validity: oracles that share the data model can share a misreading of it. |
| 2 | 2026-11-04 | New run-enumeration oracle for confirmed findings (`conformance.confirmed_oracle`), 1,500 wild teams, all convex slices of size <= 3 | 22 then 1 of 43,048 slice comparisons disagreed: the lifting search missed liftable witnesses | Lifting fixed the witness's member contributor sets. In H_sigma all entry edges of a member carry the same environment, and the checker keeps only inclusion-minimal contributor choices (Lemma M), so the recorded witness can be a representative that does not lift while an equivalent or larger choice does. | Lifting now fixes only member switch choices, searches team runs freely, and verifies each candidate by replaying the run's own member choices in H_sigma (the oracle's definition). Re-run: 0 disagreements in 43,048 comparisons; added as E1 check `confirmed_vs_oracle` and property test. |
