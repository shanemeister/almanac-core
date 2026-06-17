"""The ATTEST leg (FRAMEWORK) — an append-only, tamper-evident attestation LEDGER.

Domain-agnostic [F]. Each attestation records the proposal, the grounded facts, which
gate proved it (id + version + rules file), the verdict, and — on refusal — the named
violated rule(s). Records are CHAINED: each entry carries the prior entry's hash, so the
whole log is a hash chain an auditor can re-verify offline, without re-running or trusting
any model. That re-checkability is the product claim.

The instance supplies proposal/facts as plain dicts (it knows their domain shape); the
framework assembles, hashes, chains, and can render a generic view.

Hashing: full SHA-256 hex over the canonical JSON of the record INCLUDING `prior_hash`
and the gate provenance, EXCLUDING the derived `entry_hash`/`attestation_id`. Canonical
form: sort_keys=True, compact separators, default=str.
"""

from __future__ import annotations

import hashlib
import json

from .gate import Verdict

# The first entry's prior_hash. 64 hex zeros = "no predecessor" (chain root).
GENESIS_HASH = "0" * 64


def _canonical(record: dict) -> bytes:
    """Canonical JSON of the hash PRE-IMAGE: the record minus its derived fields."""
    preimage = {k: v for k, v in record.items() if k not in ("entry_hash", "attestation_id")}
    return json.dumps(preimage, sort_keys=True, separators=(",", ":"), default=str).encode()


def _entry_hash(record: dict) -> str:
    """Full SHA-256 hex over the canonical pre-image (includes prior_hash + gate fields)."""
    return hashlib.sha256(_canonical(record)).hexdigest()


def build_attestation(
    *,
    proposal: dict,
    grounded_facts: dict,
    verdict: Verdict,
    gate_id: str,
    gate_version: str,
    mode: str = "shadow",
    rule_catalog: dict | None = None,
    prior_hash: str = GENESIS_HASH,
    timestamp: str | None = None,
) -> dict:
    """Assemble one tamper-evident, chained attestation record (domain-agnostic).

    proposal/grounded_facts — plain dicts (instance-shaped).
    verdict                 — the framework Verdict (permitted + named violations + rules_path).
    gate_id / gate_version  — provenance from the gate manifest (WHICH control proved it).
    mode                    — 'shadow' | 'live'.
    rule_catalog            — optional {rule_id: human label} of all rules the gate checks.
    prior_hash              — the previous entry's entry_hash (GENESIS_HASH for the first).
    timestamp              — optional ISO string (passed in; core stays deterministic).
    """
    record = {
        "mode": mode,
        "gate_id": gate_id,
        "gate_version": gate_version,
        "rules_path": verdict.rules_path,
        "rules_evaluated": rule_catalog or {},
        "proposal": proposal,
        "grounded_facts": grounded_facts,
        "verdict": "PERMITTED" if verdict.permitted else "REFUSED",
        "violations": [
            {"rule_id": v.rule_id, "rule": v.rule_name, "actual": v.actual, "limit": v.limit}
            for v in verdict.violations
        ],
        "prior_hash": prior_hash,
    }
    if timestamp is not None:
        record["timestamp"] = timestamp
    record["entry_hash"] = _entry_hash(record)
    record["attestation_id"] = record["entry_hash"][:16]  # short handle for humans
    return record


def append(log: list[dict], record_kwargs: dict) -> dict:
    """Append a new attestation to an ordered log, chaining it to the last entry.
    `record_kwargs` are the build_attestation args EXCEPT prior_hash (set from the log)."""
    prior = log[-1]["entry_hash"] if log else GENESIS_HASH
    rec = build_attestation(prior_hash=prior, **record_kwargs)
    log.append(rec)
    return rec


def verify(log: list[dict]) -> dict:
    """Re-verify the attestation chain offline — the paper's central claim.

    Recomputes each entry_hash from its canonical content and checks it matches the stored
    value, AND checks each entry's prior_hash equals the previous entry's entry_hash
    (from GENESIS). No model is re-run and nothing is trusted but the records themselves.

    Returns {"ok": True, "count": N} if intact, else
            {"ok": False, "broken_index": i, "reason": "..."} for the FIRST broken link.
    """
    expected_prior = GENESIS_HASH
    for i, entry in enumerate(log):
        recomputed = _entry_hash(entry)
        if recomputed != entry.get("entry_hash"):
            return {"ok": False, "broken_index": i,
                    "reason": "entry_hash mismatch (record content was altered)"}
        if entry.get("prior_hash") != expected_prior:
            return {"ok": False, "broken_index": i,
                    "reason": "prior_hash does not match the previous entry (chain broken/reordered)"}
        expected_prior = entry["entry_hash"]
    return {"ok": True, "count": len(log)}


def render(record: dict, *, headline: str | None = None) -> str:
    """Generic human-readable rendering. An instance may override with a domain view."""
    lines = [
        "─" * 68,
        f"  ATTESTATION  {record['attestation_id']}        [{record['mode']} mode]",
        f"  gate: {record['gate_id']} v{record['gate_version']}   prior: {record['prior_hash'][:12]}…",
        "─" * 68,
        f"  {headline or 'Proposal'}: {json.dumps(record['proposal'], default=str)}",
        "",
        f"  VERDICT  : {record['verdict']}   (proven against {record['rules_path']})",
    ]
    if record["verdict"] == "PERMITTED":
        for name in (record.get("rules_evaluated") or {}).values():
            lines.append(f"      ✓ {name}")
    else:
        for v in record["violations"]:
            lines.append(f"      ✗ {v['rule']}  (actual {v['actual']} vs limit {v['limit']})")
    lines.append(f"  entry_hash: {record['entry_hash']}")
    lines.append("─" * 68)
    return "\n".join(lines)
