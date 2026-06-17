"""Almanac·Example gate binding ([I]) — wire the example facts to the framework gate.

The framework does the proving; this instance supplies WHAT to prove (rendered facts),
the rules file, the human rule names, and how to de-scale the integer-milli terms for the
attestation. Adding a gate = a rules file + a fact renderer here; the framework is untouched.
"""

from __future__ import annotations

import os

import clingo
import yaml

from almanac.core import evaluate, Verdict
from .facts import Proposal, UnitFacts, RULE_NAMES, to_asp_facts, MILLI

_GATES_DIR = os.path.join(os.path.dirname(__file__), "gates")
EXAMPLE_GATE_LP = os.path.join(_GATES_DIR, "example_gate.lp")
EXAMPLE_GATE_REL = "instances/example/gates/example_gate.lp"  # repo-relative (no abs path in artifacts)
_MANIFEST = os.path.join(_GATES_DIR, "example.gate.yaml")


def gate_provenance() -> dict:
    with open(_MANIFEST) as f:
        m = yaml.safe_load(f)
    return {"gate_id": m["id"], "gate_version": m["version"]}


def _descale(sym: clingo.Symbol) -> object:
    if sym.type == clingo.SymbolType.Number:
        return sym.number / MILLI
    if sym.type == clingo.SymbolType.String:
        return sym.string
    return sym.name if sym.type == clingo.SymbolType.Function else str(sym)


def evaluate_example(prop: Proposal, uf: UnitFacts) -> Verdict:
    """Prove an example allocation proposal against the toy gate's 5 rules."""
    return evaluate(
        asp_facts=to_asp_facts(prop, uf),
        rules_path=EXAMPLE_GATE_LP,
        rules_label=EXAMPLE_GATE_REL,
        rule_names=RULE_NAMES,
        descale=_descale,
    )
