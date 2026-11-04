# Agent-team foundation (informal design notes)

Reconstructed from the summary given in the project brief, because the original
file was not present in the repository. It is informal by design; Phase 1 turns it
into the calculus in `docs/TSE/formal_spec.md`.

* An **agent** is a contract-bearing component `(ID, Role, C=(A,G), I, O, T)`:
  assumptions `A`, guarantees `G`, input/output types `I,O`, tools `T`.
* A **team** is a directed graph of agents with typed handoffs. A team can be
  unsafe even though every agent meets its contract, because an assumption is relied
  on without being established upstream.
* **Declared vs realized evidence.** An agent's statement is not a fact unless an
  evidence-producing mechanism (deterministic check, trusted source, justified
  contract) establishes it.
* **Five blind-spot families:** responsibility coverage, assumption coverage,
  information flow, authority/evidence independence, interaction/delegation.
* **Goal:** a pre-execution verifier that returns either a compositional safety
  justification or a concrete counterexample.
* Known weaknesses of these notes: `Supported(A_i)` and handoffs are not
  path-sensitive, and nothing is said about fan-in.
