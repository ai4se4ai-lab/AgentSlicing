# AgentSlicing

Replication package for *Agent Slicing: Contracts for Sub-Teams Expose and Localize
Blind Spots in Multi-Agent AI Systems* (manuscript in `docs/TSE/main.tex`).

The study is formal and simulated. No language model is called and no GPU is needed;
every experiment is a deterministic or seeded CPU script. Contracts are declared, not
measured: the results say whether a team composition is justified *given* its declared
contracts.

## Quick start

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
make test        # unit, property-based and conformance tests (< 1 s)
make quick       # proofs, mutants, tests, running example, E1, E3, post-processing (~10 s)
make all         # everything (E1-E8), then tables, figures and macros
make paper       # needs a TeX distribution with IEEEtran and pgfplots
```

`make all` took about 25 minutes on a 20-core Linux machine; almost all of it is E5
(teams up to 5,000 nodes with a 60 s budget per strategy and team). Logs go to
`results/logs/`, one per step.

## Layout

| Path | Content |
|---|---|
| `slicing/model.py` | Teams (Def. 1), JSON specification language (Appendix B) |
| `slicing/semantics.py` | Exact run semantics (Def. 2-3) and hybrid slice semantics (Def. 5) |
| `slicing/slices.py` | Convexity, hull, enumeration, strategies, acyclic-quotient test |
| `slicing/analysis.py` | Slice-level checker (Alg. 1), lifting and confirmed findings (Def. 7), localization, diagnosis, baselines B1, B2 (+deviation set, +shrink), B4, B5, B6 (must-analysis) |
| `slicing/contracts.py` | Derived/naive/declared slice contracts (Def. 7-8), partition summaries (Thm. 2d) |
| `slicing/incremental.py` | Incremental recertification (Thm. 8) |
| `slicing/oracle.py` | Model oracle: all contract-respecting models (Lemmas 1-2) |
| `slicing/conformance.py` | Replay oracle, run oracle for confirmed findings, and theorem checks used by E1 and the tests |
| `slicing/generator.py`, `slicing/injector.py` | Topology generator; ground-truth defect injector |
| `formal/prove.py`, `formal/mutate.py` | SMT proof obligations (Z3) and proof mutants |
| `experiments/` | `running_example.py`, `e1`...`e8` (E4b = `e4_depth_sweep.py`, E8 = `e8_mutation.py`), `architectures.py` (E3 encodings), `run_all.py` |
| `scripts/process_results.py` | Statistics, tables, figures, and the generated block of `main.tex` |
| `results/` | Raw results (JSON), each with commit, versions and wall time |
| `docs/TSE/` | Paper, bibliography, formal spec, pre-registered plan, reviews, audit |

Every number in the paper comes from `results/*.json` through
`scripts/process_results.py`, which rewrites the block between
`% BEGIN GENERATED RESULTS` and `% END GENERATED RESULTS` in `docs/TSE/main.tex`.
Do not edit that block by hand.

## Seeds

Generated teams use string seeds `f'{topology}/{size}/{seed}'` with `seed` in 0..9;
wild teams in E1 use seeds 0..19,999; the statistics use NumPy seed 20261104.

## Reviews and audit

`docs/TSE/experiment_plan.md` (plan and deviation log), `docs/TSE/conformance_log.md` (bugs found
by oracles), `docs/TSE/reviews/` (two review rounds and response matrices), `docs/TSE/final_audit.md`.
