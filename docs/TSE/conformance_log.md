# Conformance and bug log

Every mismatch between the implementation, an oracle, or a theorem check is logged
here with its resolution (Phase 3 gate).

| # | Date | Found by | Symptom | Root cause | Resolution |
|---|---|---|---|---|---|
| 1 | 2026-11-04 | E1 pilot, check "F(∅) ⊆ F({v})" on random wild teams (23/300) | A static key at a node downstream of a single-successor `switch` vanished in the singleton slice of the switch | A `switch` with one successor was treated as choosing nothing, so it delivered on no edge. Every evaluator (enumerator, replay, model oracle) read the same `route` field and shared the convention, so they agreed with one another. | `Team` now normalizes a switch with < 2 successors to a fork. Re-run: 0 mismatches on 1,000 wild teams. Lesson recorded as a threat to validity: oracles that share the data model can share a misreading of it. |
