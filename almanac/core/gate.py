"""The PROOF leg (FRAMEWORK) — run a Clingo ASP gate over grounded facts and read back
a verdict that CARRIES ITS REASON.

Domain-agnostic: this is the [F] framework core. It knows nothing about any specific
instance. An instance supplies (a) the path to its gate's `.lp` rules and (b) a rendered
ASP fact block (its own grounding). The gate materializes `violation(...)` atoms so a
refusal names the clause(s) it broke — the raw material of an attestation. This is the
difference between a guardrail and an *attestable* guardrail.

The reasoner is pluggable (R-SPINE-4): ASP/Clingo is plugin #1. A future SMT plugin would
implement the same `evaluate(facts, rules) -> Verdict` contract.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Mapping

import clingo


@dataclass(frozen=True)
class Violation:
    rule_id: str                 # e.g. "r1_per_model_cap" (the violation/4 first arg)
    subject: str                 # the offending object/action (2nd arg)
    actual: object               # the offending value (3rd arg)
    limit: object                # the threshold it crossed (4th arg)
    rule_name: str = ""          # human label, resolved from the instance's name map


@dataclass(frozen=True)
class Verdict:
    permitted: bool
    violations: tuple[Violation, ...]
    asp_facts: str               # the exact fact block proven against (for the attestation)
    rules_path: str              # which rules file proved it (provenance)


def evaluate(
    asp_facts: str,
    rules_path: str,
    *,
    rule_names: Mapping[str, str] | None = None,
    descale: Callable[[clingo.Symbol], object] | None = None,
    rules_label: str | None = None,
) -> Verdict:
    """Prove a grounded ASP fact block against a gate's rules. Returns a Verdict with
    named violations.

    asp_facts   — the instance's rendered ASP facts (it did its own grounding/scaling).
    rules_path  — filesystem path to the gate's .lp program (used to LOAD it).
    rule_names  — optional {rule_id: human label} for the attestation.
    descale     — optional fn to convert a clingo term back to a domain value (e.g. undo
                  integer milli-scaling); defaults to a passthrough number/symbol reader.
    rules_label — optional provenance string RECORDED in the verdict (e.g. a repo-relative
                  path), so attestation artifacts don't leak an absolute local path.
                  Defaults to rules_path.
    """
    rule_names = rule_names or {}
    _term = descale or _default_term

    # Quiet clingo's grounding-info chatter (harmless "atom does not occur in any rule
    # head" notes for input predicates); a no-op logger keeps attestation output clean.
    ctl = clingo.Control(logger=lambda code, msg: None)
    ctl.load(rules_path)
    ctl.add("base", [], asp_facts)
    ctl.ground([("base", [])])

    permitted = False
    violations: list[Violation] = []

    def on_model(model: clingo.Model) -> None:
        nonlocal permitted, violations
        violations = []
        for atom in model.symbols(shown=True):
            if atom.name == "permitted":
                permitted = True
            elif atom.name == "violation" and len(atom.arguments) == 4:
                rid = atom.arguments[0].name
                violations.append(Violation(
                    rule_id=rid,
                    subject=_term_str(atom.arguments[1]),
                    actual=_term(atom.arguments[2]),
                    limit=_term(atom.arguments[3]),
                    rule_name=rule_names.get(rid, rid),
                ))

    ctl.solve(on_model=on_model)
    return Verdict(permitted=permitted, violations=tuple(violations),
                   asp_facts=asp_facts, rules_path=rules_label or rules_path)


def _term_str(sym: clingo.Symbol) -> str:
    if sym.type == clingo.SymbolType.String:
        return sym.string          # unwrap the quotes ("model-a" → model-a)
    if sym.type == clingo.SymbolType.Function:
        return sym.name
    return str(sym)


def _default_term(sym: clingo.Symbol) -> object:
    """Default term reader: numbers → int, strings unwrapped, functions → name."""
    if sym.type == clingo.SymbolType.Number:
        return sym.number
    if sym.type == clingo.SymbolType.String:
        return sym.string
    return sym.name if sym.type == clingo.SymbolType.Function else str(sym)
