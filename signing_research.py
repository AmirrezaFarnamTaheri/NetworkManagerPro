from __future__ import annotations


SIGNATURE_SCHEMA_VERSION = 1

CLASSICAL_ALGORITHMS = {"ed25519", "ecdsa-p256"}
POST_QUANTUM_RESEARCH_ALGORITHMS = {"ml-dsa-44", "ml-dsa-65", "slh-dsa-sha2-128s"}


def signature_metadata(algorithm, key_id, signature="", digest=""):
    return {
        "schema_version": SIGNATURE_SCHEMA_VERSION,
        "algorithm": str(algorithm or "").lower(),
        "key_id": str(key_id or ""),
        "signature": str(signature or ""),
        "digest": str(digest or ""),
    }


def validate_signature_metadata(metadata, allow_research=False):
    if not isinstance(metadata, dict):
        return False, "Signature metadata must be an object."
    if metadata.get("schema_version") != SIGNATURE_SCHEMA_VERSION:
        return False, "Unsupported signature metadata schema version."
    algorithm = str(metadata.get("algorithm") or "").lower()
    allowed = set(CLASSICAL_ALGORITHMS)
    if allow_research:
        allowed.update(POST_QUANTUM_RESEARCH_ALGORITHMS)
    if algorithm not in allowed:
        return False, "Unsupported or immature signature algorithm."
    if not metadata.get("key_id"):
        return False, "Signature metadata must include key_id."
    return True, ""


def algorithm_agility_plan():
    return {
        "schema_version": SIGNATURE_SCHEMA_VERSION,
        "production_algorithms": sorted(CLASSICAL_ALGORITHMS),
        "research_only_algorithms": sorted(POST_QUANTUM_RESEARCH_ALGORITHMS),
        "rule": "Post-quantum signatures remain research-only until library, tooling, and ecosystem support are mature.",
    }
