# Phase 0 map: what is reused, adapted, or new

This is an internal process note. The reference calculus implementation that we
studied is **not** named, linked, or cited anywhere in the paper, the code, or the
replication artifact (ground rule 2). It is referred to below only as "the
reference implementation" (RI) and "the reference manuscript" (RM).

## 1. Constructs of the reference calculus and where they live

| RM construct | RI location (role) | Fate in this project |
|---|---|---|
| Terms `deny / gate / guard / switch` over trees | `formal/calculus/core.py` (Z3 datatype), `reference.py` (tree interpreter) | **Replaced.** Agent teams are DAGs with fork, join (all/any/quorum), switch, agent, deterministic gate. Terms over trees cannot express concurrent fan-out or fan-in. |
| Model `M=(P,V,W,E,S)` | `core.py: wf_def / eval_def` | **Adapted.** Our model keeps `W` (switch choice), `E` (evidence realized at an invocation) and `S` (goals of the output); it adds contributor sets at joins and a failure set of oracles. Guard verdicts are dropped: acceptance happens when the output is reached. |
| Realization `Real(n)` (declared + provided facts hold at the invocation) | `wf_def` | **Kept in spirit.** Provided facts along the contributing lineage must hold at the invocation; declared evidence is local and is never inherited. |
| Conditional guarantees (`req(l) ⊆ E(n)` gives `scope`) | `wf_def` | **Kept.** A component's guarantee applies only when its requirements are realized and (for an LLM agent) its oracle has not failed. |
| Provided facts only from gates | `check_def` | **Generalized.** Facts are provided by any component whose contract applies (a deterministic gate always, an agent conditionally). This is needed for agent pipelines where the architect's design is the developer's input. |
| Safety from `(A,B)` | RM Def. "Safety" | **Adapted** to the output node and to critical goals under a fault budget. |
| Composition check `check(H,A,B)` + `ok` | `core.py`, `src/.../hsl/engine.py` | **Replaced** by (i) exact run-based semantics, (ii) the hybrid slice semantics, (iii) a must-analysis used only as a fast sound pre-check. |
| Soundness/completeness by structural induction, discharged as SMT obligations (one per constructor) | `formal/calculus/prove.py` | **Technique reused.** New obligations: per-node transfer steps (monotonicity, face-value domination, join minimality, fault monotonicity), each closed formula valid iff its negation is UNSAT; induction over topological order is applied on paper/by the script. |
| Proof mutants (show obligations depend on definitions) | `formal/calculus/mutate.py` | **Technique reused** with new mutants. |
| Brute-force model search as oracle | `reference.py: violating_model_exists` | **Technique reused**: our oracle enumerates all runs and, for tiny teams, all evidence/goal models. |
| Must-analysis in topological order (meet over paths) | RM Alg. 1 | **Reused as idea** for the fast pre-check and the clean-team generator; we show it is not exact with forks (correlated contributions). |
| Incremental recertification (affected routes = ancestors) | RM Cor. "Affected routes" | **Re-derived** for slices: a change invalidates slices by dependency class. |
| Complexity: coNP-completeness via CNF reduction | RM Thm. "Complexity" | **Re-derived** for teams (reduction uses switch diamonds and conditional providers). |
| Result macros with provenance (`scripts/make_macros.py`) | RI `scripts/` | **Pattern reused**: every number in the paper comes from `results/*.json` through `scripts/make_macros.py` into `docs/TSE/results_macros.tex`. |

## 2. Environment check

* Python 3.13, z3 4.x (`z3-solver 4.15`), numpy, scipy, pandas, matplotlib, networkx, hypothesis, pytest; MiKTeX `pdflatex`/`latexmk`.
* The RI's SMT proofs and core tests were run once to confirm the toolchain (result recorded in `docs/TSE/final_audit.md`).

## 3. Layout of the new work

```
slicing/            library: model, semantics, slices, analysis, generator, injector, contracts, incremental
formal/             SMT proof obligations (prove.py) and proof mutants (mutate.py)
experiments/        e1..e7 runners + run_all.py (one command)
scripts/            make_macros.py, make_figures.py, verify_refs.py
results/            raw json/csv, summaries, figures (pdf)
tests/              unit + property-based tests
docs/TSE/           main.tex, references.bib, formal_spec.md, experiment_plan.md, reviews/, final_audit.md
```

## 4. Decisions taken in Phase 0

1. No term syntax: the team is a typed DAG; the semantics is defined over runs of the DAG.
2. Guard verdicts disappear; "accept" means the output node is reached.
3. The paper and code use new names throughout (package `slicing`, spec format `TSL` = team slicing language).
4. `docs/TSE/work-is-under-review/` is excluded from the replication artifact.
