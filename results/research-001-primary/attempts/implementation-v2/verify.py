"""Bounded deterministic claim checks, independent of benchmark gold/scoring."""
from copy import deepcopy
import math
import re

FIELDS = ("unit", "measure", "geography", "population", "period_start", "period_end")


def same_value(actual, expected, unit):
    if type(expected) is bool:
        return type(actual) is bool and actual == expected
    if isinstance(expected, (int, float)):
        if type(actual) not in (int, float) or not math.isfinite(actual):
            return False
        tolerance = .005 if unit in ("percent", "ratio", "per_100000_population") else 0
        return abs(actual - expected) <= tolerance
    if isinstance(expected, list):
        return isinstance(actual, list) and sorted(actual) == sorted(expected)
    return actual == expected


def causal_assertions(text):
    sentences = re.split(r"[.!?\n]+", text or "")
    result = []
    for sentence in sentences:
        if re.search(r"\b(caused|causes|proves?|demonstrates? causality|treatment benefit|vaccine effectiveness is)\b", sentence, re.I):
            if not re.search(r"\b(no|not|cannot|can't|doesn't|does not|insufficient|without|unsupported|unwarranted)\b", sentence, re.I):
                result.append(sentence.strip())
    return result


def verify_draft(draft, recomputed_facts, store=None):
    """Correct only claims actually emitted; never fill missing claims with an oracle answer.

    recomputed_facts must be built afresh from the public source adapter or statistical
    artifacts, never the LLM prompt's returned facts or private benchmark gold.
    """
    wanted = {c["slot"]: c for c in recomputed_facts["claims"]}
    logs, checked, seen = [], [], set()
    if not isinstance(draft, dict) or not isinstance(draft.get("claims"), list):
        return {"item_id": recomputed_facts["item_id"], "status": "insufficient_data",
                "claims": [], "limitations": ["No parseable factual draft available"],
                "summary": "Generation failed; no verified answer.", "verification": []}
    for claim in draft["claims"]:
        if not isinstance(claim, dict):
            logs.append({"decision": "rejected", "reason": "Claim must be an object"})
            continue
        slot = claim.get("slot")
        if slot not in wanted or slot in seen:
            logs.append({"slot": slot, "decision": "rejected", "reason": "Unsupported or duplicate claim slot", "original": claim})
            continue
        seen.add(slot)
        fact = wanted[slot]
        errors = []
        if not same_value(claim.get("value"), fact["value"], fact["unit"]):
            errors.append("value_or_type")
        errors.extend(key for key in FIELDS if claim.get(key) != fact.get(key))
        citations = claim.get("citations", [])
        if not isinstance(citations, list) or not citations:
            errors.append("missing_citations")
        elif store is not None:
            if any(not store.valid_citation(c) for c in citations):
                errors.append("invalid_citation")
            else:
                for needed in fact["citations"]:
                    if not any(c["source_id"] == needed["source_id"] and c["line_start"] <= needed["line_end"]
                               and c["line_end"] >= needed["line_start"] for c in citations):
                        errors.append("citation_does_not_support_required_operand")
                        break
        else:
            expected_ids = {c.get("evidence_id") for c in fact["citations"]}
            if not expected_ids.issubset({c.get("evidence_id") for c in citations}):
                errors.append("incorrect_artifact_reference")
            elif any(not any(c.get("evidence_id") == wanted.get("evidence_id") and c.get("sha256") == wanted.get("sha256")
                             for c in citations) for wanted in fact["citations"]):
                errors.append("incorrect_artifact_hash")
        logs.append({"slot": slot, "decision": "corrected" if errors else "accepted", "errors": errors, "original": claim})
        checked.append(deepcopy(fact))
    status = recomputed_facts["status"] if checked else "insufficient_data"
    return {"item_id": recomputed_facts["item_id"], "status": status, "claims": checked,
            "limitations": recomputed_facts.get("limitations", []),
            "summary": "; ".join(f"{c['slot']}: {c['value']} {c['unit']}" for c in checked),
            "verification": logs, "missing_slots": sorted(wanted.keys() - seen),
            "original_status": draft.get("status"),
            "original_summary_causal_assertions": causal_assertions(draft.get("summary", "")),
            "verification_scope": "Supported by frozen inputs and bounded calculations, not underlying clinical truth"}
