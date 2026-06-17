"""One-command reproduction for the proof-gate paper (public, toy instance).

    python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
    .venv/bin/python demo/run.py

Runs the proof spine on ILLUSTRATIVE facts (no real policy): a PERMIT and a REFUSE
through the categorical example gate, builds an append-only hash-chained attestation
ledger, re-verifies it offline with almanac.core.verify (the central claim), demonstrates
that tampering breaks the chain, captures the two sample certs to demo/artifacts/, and
reports the median gate-eval latency.
"""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import asdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from almanac.core import append, verify, render
from instances.example.facts import Proposal, UnitFacts, RULE_NAMES
from instances.example.gates import evaluate_example, gate_provenance

ART = os.path.join(os.path.dirname(os.path.abspath(__file__)), "artifacts")

PERMIT = (Proposal("unit-a", "increase", 1.10, 0.10, "modest add after positive signal"),
          UnitFacts("unit-a", 1.00, 0.018, -0.12, 8.00, 1.00))
REFUSE = (Proposal("unit-b", "increase", 1.50, 0.50, "add into a decline"),
          UnitFacts("unit-b", 1.00, -0.021, -0.55, 8.00, 1.10))


def attest(log, scenario):
    prop, uf = scenario
    v = evaluate_example(prop, uf)
    return append(log, dict(proposal=asdict(prop), grounded_facts=asdict(uf), verdict=v,
                            mode="shadow", rule_catalog=RULE_NAMES, **gate_provenance()))


def main() -> None:
    print("\nALMANAC proof spine — reproduction (illustrative facts, shadow mode)\n")
    log: list[dict] = []
    permit = attest(log, PERMIT); print(render(permit)); print()
    refuse = attest(log, REFUSE); print(render(refuse)); print()

    print("VERIFY (offline re-check, no model re-run):", verify(log))
    tampered = [dict(log[0]), dict(log[1])]; tampered[0]["verdict"] = "REFUSED"
    print("VERIFY after tampering with entry 0   :", verify(tampered))

    prop, uf = PERMIT
    t = []
    for _ in range(100):
        s = time.perf_counter(); evaluate_example(prop, uf); t.append((time.perf_counter() - s) * 1000)
    t.sort()
    print(f"\nGate-eval latency (n=100): median {t[len(t)//2]:.2f} ms (min {t[0]:.2f}, max {t[-1]:.2f})")

    os.makedirs(ART, exist_ok=True)
    json.dump(permit, open(os.path.join(ART, "attestation_permit.json"), "w"), indent=2)
    json.dump(refuse, open(os.path.join(ART, "attestation_refuse.json"), "w"), indent=2)
    json.dump(log, open(os.path.join(ART, "ledger.json"), "w"), indent=2)
    print(f"\nartifacts → demo/artifacts/{{attestation_permit,attestation_refuse,ledger}}.json")


if __name__ == "__main__":
    main()
