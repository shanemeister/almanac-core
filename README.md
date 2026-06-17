# Almanac — proof-gated decisions for agentic ML lifecycles

**Almanac** is a governed ML-lifecycle framework: every *consequential* transition is gated
by a **machine-checkable proof**, and every decision is recorded in an **append-only,
tamper-evident attestation ledger** an auditor can re-verify offline — without re-running
or trusting any model.

> The LLM proposes. The ontology grounds. **The reasoner proves.** Governance attests.

This is the **public framework core** + an **illustrative instance**. It accompanies the
paper *(proof-gate paper, Fox River AI)* and reproduces its claims. Real deployments supply
their own private instance package; the framework core is domain-agnostic and untouched.

## Quick start

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python demo/run.py
```

You'll see, on illustrative facts:
- a **PERMIT** (a proposal clears the gate's declared rules), and a **REFUSE** with **named
  violations** (each rule + the actual value vs. the limit it crossed);
- both appended to a **SHA-256 hash chain** (`prior_hash` → `entry_hash`, from a 64-zero genesis);
- **`verify()`** re-checking the chain offline (`{ok: True}`);
- a **tamper check** — altering a stored record makes `verify()` report the first broken link;
- the median gate-eval latency.

## Architecture — the [F]/[I] boundary

- **`almanac/core/`** — the **framework** ([F], domain-agnostic):
  - `gate.evaluate(facts, rules)` — runs an ASP (Clingo) gate, returns a verdict with **named
    violations materialized as facts** (so a refusal carries its reasons, not just "no").
  - `attest.{build_attestation, append, verify, render}` — the hash-chained attestation ledger
    and the offline verifier.
  The core imports no instance. A future SMT reasoner implements the same `evaluate` contract.
- **`instances/example/`** — an **illustrative instance** ([I]): a toy resource-allocation
  gate (five abstract rules) showing how an instance plugs in — a fact schema, a rules file
  (`gates/example_gate.lp`), and a binding. **The numbers are pedagogical, not a policy.**

To build a real instance: add a sibling package under `instances/` with your fact schema,
your rules (`.lp`), and a binding. The framework core does not change.

## Scope (honest)

- **Running end-to-end:** the categorical eligibility gate, the attestation ledger, offline `verify()`.
- **Demonstrated by design, pending re-integration:** a *numeric* threshold gate via
  boolean-in-grounding (numeric comparisons evaluated at grounding, the solver reasons over
  booleans). Proven in an earlier prototype; not wired into this structure (different violation
  arity). The paper is scoped to the one gate that runs here.

## License

Code: **MIT** (`LICENSE`). The accompanying paper: **CC BY 4.0**.

## Citation

If you use this, please cite the paper (DOI on deposit) and this repository.
Byline: **Fox River AI**.
