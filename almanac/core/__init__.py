"""Almanac framework core ([F]) — domain-agnostic. The proof spine: gate (PROVE),
attest (ATTEST), and the contract/spine wiring. Knows nothing about any instance."""

from .gate import evaluate, Verdict, Violation
from .attest import build_attestation, append, verify, render, GENESIS_HASH

__all__ = [
    "evaluate", "Verdict", "Violation",
    "build_attestation", "append", "verify", "render", "GENESIS_HASH",
]
