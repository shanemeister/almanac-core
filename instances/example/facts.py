"""The GROUND leg for the EXAMPLE instance — illustrative facts (not a real policy).

An abstract resource-allocation gate: a proposer wants to adjust an `allocation` to a
`unit`, and the gate proves the proposal against a few made-up limits. Numbers are toy
and round on purpose — they demonstrate the mechanism, they are not anyone's risk policy.

Clingo is integer-only, so values are scaled to milli-units (×1000) here, in one place.
"""

from __future__ import annotations

from dataclasses import dataclass

MILLI = 1000


@dataclass(frozen=True)
class Proposal:
    """What a proposer wants to do — it only proposes; a gate authorizes."""
    unit: str
    action: str           # increase | decrease | hold | release
    new_alloc: float      # resulting allocation after the action
    delta: float          # signed change (+ for increase)
    rationale: str = ""


@dataclass(frozen=True)
class UnitFacts:
    """Grounded facts about the unit + portfolio at proposal time (illustrative)."""
    unit: str
    current_alloc: float
    score: float          # a quality signal (can be negative)
    drawdown: float       # peak-to-current, negative (e.g. -0.5 == -50%)
    pool_total: float     # total resource pool
    other_alloc: float    # sum of allocations to OTHER units


# Illustrative limits — TOY VALUES, NOT A RISK POLICY. The point is the mechanism.
RULE_PARAMS = {
    "per_unit_cap": 2.0,            # max allocation per unit (toy units)
    "pool_cap_pct": 0.50,          # max total as a fraction of the pool
    "max_round_increase_pct": 0.20,  # max single-round increase as a fraction of current
    "score_floor": 0.0,            # don't increase a unit scoring below this
    "max_drawdown": -0.50,         # at/below → only decrease/release permitted
}


def _m(x: float) -> int:
    return int(round(x * MILLI))


def _q(unit: str) -> str:
    """Quote the unit id as an ASP string so any id grounds safely (a bare term with a
    hyphen is parsed as subtraction and silently fails — quoting prevents a false PERMIT)."""
    return '"' + str(unit).replace("\\", "\\\\").replace('"', '\\"') + '"'


def to_asp_facts(prop: Proposal, uf: UnitFacts) -> str:
    return "\n".join([
        f"proposal({_q(prop.unit)}, {prop.action}, {_m(prop.new_alloc)}, {_m(prop.delta)}).",
        f"current_alloc({_q(uf.unit)}, {_m(uf.current_alloc)}).",
        f"unit_score({_q(uf.unit)}, {_m(uf.score)}).",
        f"unit_drawdown({_q(uf.unit)}, {_m(uf.drawdown)}).",
        f"pool_total({_m(uf.pool_total)}).",
        f"total_other_alloc({_m(uf.other_alloc)}).",
        f"rule_param(per_unit_cap, {_m(RULE_PARAMS['per_unit_cap'])}).",
        f"rule_param(pool_cap_pct, {_m(RULE_PARAMS['pool_cap_pct'])}).",
        f"rule_param(max_round_increase_pct, {_m(RULE_PARAMS['max_round_increase_pct'])}).",
        f"rule_param(score_floor, {_m(RULE_PARAMS['score_floor'])}).",
        f"rule_param(max_drawdown, {_m(RULE_PARAMS['max_drawdown'])}).",
    ])


RULE_NAMES = {
    "r1_per_unit_cap": "Per-unit cap (allocation ≤ cap)",
    "r2_pool_cap": "Pool cap (total ≤ pool fraction)",
    "r3_round_delta": "Per-round delta (increase ≤ max fraction of current)",
    "r4_score_floor": "Score floor (no increase below the score floor)",
    "r5_drawdown_killswitch": "Drawdown kill-switch (≤ max → retreat only)",
}
