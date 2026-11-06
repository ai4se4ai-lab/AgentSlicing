# AgentSlicing

Python library and replication package for **Agent Slicing: Contracts for Sub-Teams
Expose and Localize Blind Spots in Multi-Agent AI Systems**. This repository
implements the approach and provides the experiments needed to reproduce the
results reported in the paper.

AgentSlicing checks whether a multi-agent workflow's **declared contracts and
orchestration justify its goals**. It can expose problems that checking each agent
alone misses: accepting only one of two required approvals, redundant reviewers
sharing a failure domain, or a deterministic check depending on a fallible producer.
It also identifies small groups of components that explain a finding.

The study uses formal models and simulated teams. No language model, API key,
external service, or GPU is required. Results are conditional on the contracts you
supply; they do not measure the quality or failure probability of real agents.

## Quick setup

The paper reports Linux and Python **3.12**, with 20 CPU cores. Use Python 3.12 to
match that environment; the dependency versions are pinned in
[requirements.txt](requirements.txt). Git is needed to clone the repository, GNU
Make provides the shortcuts below. LaTeX is not required to run the library or
reproduce the experimental results.

```bash
git clone https://github.com/ai4se4ai-lab/AgentSlicing.git
cd AgentSlicing
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
make test
```

Run commands from the repository root. The library is imported directly from this
checkout; there is no package installation step or console command. The examples
use `.venv/bin/python` so activating the environment is optional. Without Make,
run `.venv/bin/python -m pytest -q tests` to execute the tests.

## How the approach works

1. **Model the team.** Represent agents and deterministic gates as a directed
   acyclic graph. Each node declares requirements, guarantees, local evidence,
   routing, and a join policy. Agents also name their oracle (failure domain).
2. **Choose slices.** A slice is a nonempty convex set of nodes: if two members
   have a directed path between them, every node on that path must be included.
   Slices may be disconnected. Enumerate small slices or use window, region,
   band, and goal-directed strategies.
3. **Check hybrid behavior.** Members execute their contracts and policies;
   components outside the slice are interpreted at face value. The checker
   explores routing, contributing inputs, and oracle failures.
4. **Confirm and localize.** A raw slice finding can be spurious. Confirmation
   checks that it lifts to a whole-team run. Findings are grouped by symptom key,
   localized to inclusion-minimal confirming slices among those evaluated, and
   classified from their witnesses.
5. **Inspect or revise.** Repair contracts or orchestration and check again.
   Boundary summaries support composition; dependency analysis supports reuse of
   raw slice results after edits.

A symptom key is `(kind, node_id, property)`: `assume` denotes an unmet node
requirement, `goal` a missing fault-free output goal, and `robust` a critical goal
lost under the fault budget when it is not already a fault-free goal defect.
Depth is the size of the smallest confirming slice. A small candidate family can
find defects without finding every defect or the globally smallest explanation.

## Use the library: find and repair a release-policy defect

This example follows the paper's Team Specification Language appendix. A
writer forks to a reviewer and a security tester. The release gate accepts **any**
one approval, while the output requires **both**.

Save the following as `team.json` in the repository root:

```json
{
  "name": "release-on-one-approval",
  "input": ["spec"],
  "goals": ["reviewed", "sec_tested"],
  "critical": [],
  "fault_budget": 0,
  "nodes": [
    {"id": "Writer", "oracle": "writer_model",
     "req": ["spec"], "gua": ["code"]},
    {"id": "Reviewer", "oracle": "review_model",
     "req": ["code"], "gua": ["reviewed"]},
    {"id": "Tester", "oracle": "test_model",
     "req": ["code"], "gua": ["sec_tested"]},
    {"id": "Release", "kind": "gate", "join": "any"}
  ],
  "edges": [
    ["IN", "Writer"],
    ["Writer", "Reviewer"], ["Writer", "Tester"],
    ["Reviewer", "Release"], ["Tester", "Release"],
    ["Release", "OUT"]
  ]
}
```

Save this as `example.py`, then run `.venv/bin/python example.py`:

```python
import json
from slicing.model import Team
from slicing import analysis, semantics, slices

with open("team.json", encoding="utf-8") as stream:
    team = Team.from_json(json.load(stream))

errors = team.validate()
if errors:
    raise ValueError(errors)
unreachable = set(team.nodes) - semantics.live_nodes(team)
if unreachable:
    raise ValueError(f"Unreachable nodes: {sorted(unreachable)}")

exact = semantics.symptoms(team)
print("Exact symptoms:", sorted(exact))

report = analysis.check_confirmed(team, slices.exhaustive(team, 2))
for key, finding in sorted(report["findings"].items()):
    print(key, "slice:", team.nodes_of(finding["top"]),
          "class:", finding["class"])
print("Search statistics:", report["stats"])

assert set(report["findings"]) == set(exact)
repaired = team.replace("Release", join="all")
assert not semantics.symptoms(repaired)
print("Repaired team: no symptoms at fault budget 0")
```

The exact symptoms are:

```text
[('goal', 'OUT', 'reviewed'), ('goal', 'OUT', 'sec_tested')]
```

Each finding has a two-component explanation involving `Release` and one approval
branch. Changing the join to `all` makes both approvals contribute and removes
both symptoms at fault budget zero. `team.replace(...)` returns a new model.

### Model your own workflow

| Field | Meaning and defaults |
|---|---|
| `kind` | `agent` (default) or deterministic `gate` |
| `req`, `gua` | Atomic required and guaranteed properties; default `[]` |
| `decl` | Local evidence that can satisfy this node's requirements; never forwarded |
| `oracle` | Required agent failure-domain identifier; equal identifiers mean shared failure |
| `route` | `fork` (default): send to every successor; `switch`: choose one successor |
| `join` | `all` (default), `any`, or `quorum:q`; quorum must fit the in-degree |
| `input`, `goals` | Input facts and required output facts; default `[]` |
| `critical`, `fault_budget` | Goals to preserve under up to this many failed oracles; defaults `[]`, `0` |
| `output_join` | Join policy for an automatically created `OUT`; default `all` |

Property names have no implicit logical relationships. A reached node forwards
contributing input facts and adds guarantees only when its requirements hold and,
for an agent, its oracle has not failed. Failed or inapplicable nodes still forward
their contributing input. An `any` join may use just one delivered input; it does
not concatenate all available approvals.

`IN` and `OUT` are created as gates when omitted from `nodes`, but their **edges
must be supplied**. Explicit boundary nodes take precedence: put input facts in
`IN.gua` and ensure `OUT.req` equals `goals`. Use unique node identifiers, valid
kind/routing values, a nonnegative fault budget, and connect every node on a path
from input to output. Cycles and unknown edge endpoints are rejected on loading;
`validate()` checks further structural constraints. Also check `live_nodes()`:
structural validity alone does not establish reachability under routing policies.
Loops must be finitely unrolled; shared mutable state is outside this model.

To check robustness, mark selected goals as `critical`, raise `fault_budget`, and
assign oracle identifiers to match the intended shared failures. The release
repair above alone does not ensure robustness against failed reviewers.

### Larger teams and report interpretation

Replace exhaustive enumeration with a strategy family, for example:

```python
family = list(dict.fromkeys(
    slices.singleton(team)
    + slices.window(team, 2)
    + slices.region(team)
    + slices.goal_directed(team)
))
report = analysis.check_confirmed(
    team, family, max_runs=200_000, lift_runs=200_000, time_budget=60
)
print(report["stats"])
```

This is the combined SL family used by the experiments. `finding["minimal"]`
contains the remaining minimal evaluated explanations, `top` the highest-ranked
node mask, `witness` the hybrid witness, and `class` the diagnosed mechanism.
Convert masks with `team.nodes_of(...)`.

Inspect `stats["limited"]`, `stats["exhausted"]`, and `stats["timeout"]` for
unfinished searches; `unconfirmed` counts candidates that were not confirmed.
**An empty bounded report is not a safety certificate.** Exact
`semantics.symptoms(team)` explores the whole team and can raise
`semantics.RunLimit`. Safety certification requires complete whole-team checking
or complete composition of boundary summaries over a partition with an acyclic
quotient. Cost depends strongly on choice points, so exact checking and large
slices can be expensive even in small graphs.

For additional APIs, see [contracts.py](slicing/contracts.py) for derived,
robust, and declared contracts and partition composition;
[analysis.py](slicing/analysis.py) for baselines and greedy shrinking; and
[incremental.py](slicing/incremental.py) for dependency-based recertification.
Incremental reuse concerns raw slice findings: confirmed findings must be checked
against the updated whole team again.

## Results reported in the paper

These are results for the declared models and benchmark distributions in the
paper, not estimates of defect prevalence in deployed systems.

| Evaluation | Reported result |
|---|---|
| E1: semantic conformance | 0 mismatches in 219,200 team-check pairs; all six proof mutants killed |
| E2: controlled injected defects | 4,480 teams; SL finds every primary key in the hidden classes S2, S3, S4, S6a, S6b, while confirmed singleton analysis finds none of those primary keys |
| E2: localization | On detected hidden defects in the small benchmark, SL has 86.9% exact localization versus 49.8% for matched random slices |
| E3: published-design encodings | 9 designs, 40 variants; 6 documented encodings have defects hidden from agent-level analysis |
| E8: random engineering changes | 1,680 teams and 3,863 symptom keys; 36.1% of keys hidden from confirmed agent-level analysis; SL has 99.9% recall, 86.3% exact localization, and no false findings |
| E5: scalability | Up to 5,000 inner nodes; topology and choice points govern cost, and a general polynomial-scaling claim is not supported |
| E6: incremental reuse | Agreement with full raw rechecking on all 1,967 changes; 36.0% of slices rechecked overall; median speed-up 1.9×, with incremental checking slower on 17.6% of changes |

The injected hidden-class separation follows from the constructed gadgets and
the paper's theorem. Whole-team detection followed by shrinking is a strong
baseline: slicing does not outperform it in exact localization. Confirmation
matters because raw slice reports can contain false findings. The paper provides
budgets, confidence intervals, baseline definitions, and validity limitations.

## Reproduce the results reported in the paper

### Prepare an output directory

Experiments replace their corresponding files in `results/`, and the driver
replaces stage logs. Preserve the bundled results or use a separate checkout for
comparison. Set `SLICING_OUT` before any command that includes postprocessing
to direct generated artifacts to a dedicated results directory:

```bash
export SLICING_OUT="$PWD/results/reproduced-paper"
mkdir -p "$SLICING_OUT"
printf '%s\n' '% BEGIN GENERATED RESULTS' '% END GENERATED RESULTS' > "$SLICING_OUT/main.tex"
```

The two markers initialize the output file expected by the postprocessor. It
will contain generated LaTeX definitions for comparing numerical results with
the paper; it is not a complete paper source. No manuscript files are needed.

### Quick validation or complete regeneration

After the setup above, choose the appropriate workflow:

```bash
# Proof obligations, proof mutants, tests, running example, E1, E3, summaries:
make quick

# All of the above plus every remaining experiment, then summaries:
make all
```

The quick run **does not rerun E2, E4b, or E5–E8**. Its summaries combine fresh
quick-run files with the bundled files for omitted stages. `make all` runs every
stage and is the complete data-regeneration workflow. Without Make, use
`.venv/bin/python experiments/run_all.py --quick` or
`.venv/bin/python experiments/run_all.py` with the same `SLICING_OUT` setting.

The driver runs stages in separate processes and stops at the first failure.
Read `results/logs/<stage>.log` for details. Most parallel stages use the detected
CPU count minus two workers; E5 explicitly uses ten workers. The full run is
substantially longer than quick validation, with scalability often dominating:
E5 uses a 60-second budget per strategy/team and sizes from 10 to 5,000 inner
nodes. Runtime and time-out coverage depend on hardware and system load.

### Rerun individual stages

Stage names accepted by `experiments/run_all.py` are:

| Stage | Purpose | Main output in `results/` |
|---|---|---|
| `proofs` | Z3 proof obligations | `proofs.json` |
| `mutants` | Changes that must break proof obligations | `proof_mutants.json` |
| `tests` | Unit and property-based tests | `logs/tests.log` |
| `running_example` | Paper's development/review/testing example and repairs | `running_example.json` |
| `e1_conformance` | Semantic oracles, theorem checks, hardness reductions | `e1_conformance.json` |
| `e2_detection` | Injected detection/localization and slice-size sweep (E4) | `e2_detection.json` |
| `e3_architectures` | Published-design encodings and sensitivity | `e3_architectures.json` |
| `e4_depth_sweep` | Hand-off distance, host size, and depth (E4b) | `e4_depth_sweep.json` |
| `e5_scalability` | Cost, recall, and time-outs by size/topology | `e5_scalability.json` |
| `e6_evolution` | Incremental versus full raw rechecking after edits | `e6_evolution.json` |
| `e7_ablation` | Sensitivity, ablation, and false findings | `e7_ablation.json` |
| `e8_mutation` | Random engineering changes and resulting symptoms | `e8_mutation.json` |
| `process` | Statistics, tables, figures, and result macros | `macros.json` plus files under `SLICING_OUT` |

For example, after preparing `SLICING_OUT`:

```bash
.venv/bin/python experiments/run_all.py e8_mutation process
```

This reruns E8 and combines its new results with the other available JSON files.
There is no separate E4 script: E2 includes the basic slice-size sweep, and
`e4_depth_sweep` implements the additional E4b study.

### Recompute summaries from bundled data

To audit the supplied measurements without rerunning experiments, prepare
`SLICING_OUT` as above and run:

```bash
.venv/bin/python scripts/process_results.py
```

The postprocessor reads `results/*.json` and writes:

- `results/macros.json`: numerical macro values for comparison with the paper.
- `$SLICING_OUT/results_macros.tex`: LaTeX result macros.
- `$SLICING_OUT/tables/*.tex` and `$SLICING_OUT/figures/*.pdf`: generated artifacts.
- The marked generated-results block in `$SLICING_OUT/main.tex`, including table
  bodies and plot definitions.

Compare the generated numerical values and raw measurements with the results
reported in the paper. The generated LaTeX artifacts support inspection and reuse
of the results; they do not require the paper source.

### Seeds, provenance, and comparison

Generated teams use string seeds `f'{topology}/{size}/{seed}'`; the standard
injected benchmark uses seeds 0–9, E1 wild teams use 0–19,999, and E8 uses seeds
0–19 with one to three changes per team. Additional seeds, search limits, and
parameter grids are fixed in the experiment sources. Statistical resampling uses
NumPy seed **20261104**.

Result files record provenance such as commit, dirty-worktree status, Python and
library versions, platform, CPU count, and timing. Compare findings, class counts,
recall/localization metrics, and statistical summaries with the paper and bundled
JSON. Byte-identical files are not expected: provenance and timing change, and
wall-time budgets can change which searches finish. Read time-out, run-limit,
and exhaustion indicators alongside reported coverage. Recomputing bundled data
checks the summaries; rerunning all experiments independently regenerates the data.

## Repository map

| Path | Contents |
|---|---|
| [`slicing/model.py`](slicing/model.py) | Team representation, JSON specification language, validation, revision |
| [`slicing/semantics.py`](slicing/semantics.py) | Exact runs, hybrid slice semantics, symptoms, liveness |
| [`slicing/slices.py`](slicing/slices.py) | Convex hulls, enumeration, candidate strategies, quotient checks |
| [`slicing/analysis.py`](slicing/analysis.py) | Confirmation, localization, diagnosis, shrinking, baselines |
| [`slicing/contracts.py`](slicing/contracts.py) | Slice contracts and boundary summaries |
| [`slicing/incremental.py`](slicing/incremental.py) | Dependency sets and raw-result reuse |
| [`slicing/oracle.py`](slicing/oracle.py), [`slicing/conformance.py`](slicing/conformance.py) | Model, replay, and run oracles |
| [`slicing/generator.py`](slicing/generator.py), [`slicing/injector.py`](slicing/injector.py) | Generated hosts and controlled defect gadgets |
| [`formal/`](formal/) | Z3 obligations and proof mutants |
| [`experiments/`](experiments/) | Experiment drivers, architecture encodings, mutation operators |
| [`tests/`](tests/) | Unit and property-based checks |
| [`scripts/process_results.py`](scripts/process_results.py) | Statistical summaries and generated paper artifacts |
| [`results/`](results/) | Bundled measurements, macros, and logs |
