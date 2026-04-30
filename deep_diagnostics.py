from __future__ import annotations

import socket
import ssl
import time

import core
import requests


SCHEMA_VERSION = 1

TEST_CATALOG = {
    "captive_portal": {
        "category": "local active",
        "duration_seconds": 5,
        "data_collected": ["HTTP status", "redirect presence", "safe connectivity endpoint response class"],
        "consent": "Check a safe connectivity endpoint to distinguish normal access from captive portal login or HTTP modification.",
    },
    "dns_integrity": {
        "category": "external active",
        "duration_seconds": 10,
        "data_collected": ["Domain tested", "local resolver answers", "trusted resolver answers", "confidence"],
        "consent": "Compare local DNS answers with a user-approved trusted resolver for a benign domain.",
    },
    "tls_inspection": {
        "category": "external active",
        "duration_seconds": 10,
        "data_collected": ["Host tested", "certificate issuer", "certificate subject", "validity window"],
        "consent": "Open a TLS connection to a benign endpoint and report certificate issuer evidence.",
    },
}


def consent_prompt(test_id):
    item = TEST_CATALOG.get(test_id)
    if not item:
        return None
    return {
        "schema_version": SCHEMA_VERSION,
        "test_id": test_id,
        "category": item["category"],
        "duration_seconds": item["duration_seconds"],
        "data_collected": list(item["data_collected"]),
        "consent": item["consent"],
        "cancellable": True,
    }


def diagnostic_result(test_id, status, evidence=None, recommendation="", confidence="low"):
    return {
        "schema_version": SCHEMA_VERSION,
        "test_id": str(test_id),
        "status": str(status),
        "confidence": str(confidence),
        "evidence": core.redact_value(evidence or {}),
        "recommendation": str(recommendation or ""),
        "timestamp": time.time(),
    }


def run_captive_portal_diagnostic(fetcher=None):
    result = core.detect_captive_portal(fetcher=fetcher)
    status = result.get("status", "unknown")
    if status == "open":
        recommendation = "Connectivity endpoint is reachable; investigate DNS, proxy, or target service next."
        confidence = "medium"
    elif status == "captive":
        recommendation = "Complete the network sign-in flow before applying DNS or proxy automation."
        confidence = "medium"
    else:
        recommendation = "Connectivity could not be classified; retry after confirming local adapter status."
        confidence = "low"
    return diagnostic_result(
        "captive_portal",
        status,
        {"detail": result.get("detail", "")},
        recommendation,
        confidence,
    )


def classify_dns_integrity(local_answers, trusted_answers):
    local_set = {str(item).lower() for item in (local_answers or []) if item}
    trusted_set = {str(item).lower() for item in (trusted_answers or []) if item}
    if not local_set and not trusted_set:
        return "inconclusive", "Neither resolver returned an answer.", "low"
    if not local_set and trusted_set:
        return "filtered", "Local resolver returned no answer while the trusted resolver did.", "medium"
    if local_set == trusted_set:
        return "normal", "Local and trusted resolver answers match.", "medium"
    if local_set and trusted_set and local_set.isdisjoint(trusted_set):
        return "mismatch", "Local and trusted resolver answers differ completely.", "medium"
    return "partial_mismatch", "Local and trusted resolver answers overlap but are not identical.", "low"


def run_dns_integrity_diagnostic(domain, local_resolver=None, trusted_resolver=None):
    domain = _safe_domain(domain)
    local_resolver = local_resolver or _resolve_system
    trusted_resolver = trusted_resolver or resolve_cloudflare_doh
    try:
        local_answers = local_resolver(domain)
    except Exception as exc:
        local_answers = []
        local_error = str(exc)
    else:
        local_error = ""
    try:
        trusted_answers = trusted_resolver(domain)
    except Exception as exc:
        trusted_answers = []
        trusted_error = str(exc)
    else:
        trusted_error = ""
    status, explanation, confidence = classify_dns_integrity(local_answers, trusted_answers)
    return diagnostic_result(
        "dns_integrity",
        status,
        {
            "domain": domain,
            "local_answers": sorted(local_answers),
            "trusted_answers": sorted(trusted_answers),
            "local_error": local_error,
            "trusted_error": trusted_error,
            "explanation": explanation,
        },
        "Treat this as evidence for troubleshooting, not proof of intent or attribution.",
        confidence,
    )


def classify_tls_certificate(cert, expected_issuer_keywords=None):
    expected_issuer_keywords = [item.lower() for item in (expected_issuer_keywords or [])]
    issuer = _name_tuple_to_text((cert or {}).get("issuer", ()))
    subject = _name_tuple_to_text((cert or {}).get("subject", ()))
    if not cert:
        return "unknown", "No certificate details were available.", "low"
    if expected_issuer_keywords and not any(keyword in issuer.lower() for keyword in expected_issuer_keywords):
        return "possible_inspection", "Certificate issuer did not match expected issuer hints.", "medium"
    return "normal", "Certificate issuer evidence is present and no mismatch rule fired.", "low"


def run_tls_inspection_diagnostic(host, expected_issuer_keywords=None, cert_fetcher=None):
    host = _safe_domain(host)
    cert_fetcher = cert_fetcher or _fetch_certificate
    try:
        cert = cert_fetcher(host)
        status, explanation, confidence = classify_tls_certificate(cert, expected_issuer_keywords)
        evidence = {
            "host": host,
            "issuer": _name_tuple_to_text(cert.get("issuer", ())),
            "subject": _name_tuple_to_text(cert.get("subject", ())),
            "not_before": cert.get("notBefore", ""),
            "not_after": cert.get("notAfter", ""),
            "explanation": explanation,
        }
    except Exception as exc:
        status = "unknown"
        confidence = "low"
        evidence = {"host": host, "error": str(exc)}
    return diagnostic_result(
        "tls_inspection",
        status,
        evidence,
        "Use issuer evidence to explain TLS interception; do not infer intent from this result alone.",
        confidence,
    )


def _resolve_system(domain):
    infos = socket.getaddrinfo(domain, None, proto=socket.IPPROTO_TCP)
    return sorted({info[4][0] for info in infos})


def resolve_cloudflare_doh(domain, record_type="A", session=None):
    """Resolve a benign user-approved domain through Cloudflare DoH JSON."""
    domain = _safe_domain(domain)
    session = session or requests.Session()
    response = session.get(
        "https://cloudflare-dns.com/dns-query",
        params={"name": domain, "type": str(record_type or "A").upper()},
        headers={"accept": "application/dns-json"},
        timeout=8,
    )
    response.raise_for_status()
    payload = response.json()
    answers = []
    for item in payload.get("Answer", []) or []:
        data = str(item.get("data") or "").strip()
        if data:
            answers.append(data.rstrip(".").lower())
    return sorted(set(answers))


def _fetch_certificate(host, port=443):
    context = ssl.create_default_context()
    with socket.create_connection((host, port), timeout=8) as sock:
        with context.wrap_socket(sock, server_hostname=host) as tls:
            return tls.getpeercert()


def _safe_domain(value):
    domain = str(value or "").strip().lower().rstrip(".")
    if not domain or len(domain) > 253 or "/" in domain or ":" in domain:
        raise ValueError("Diagnostic domain must be a plain hostname.")
    return domain


def _name_tuple_to_text(value):
    parts = []
    for group in value or ():
        for key, item in group:
            parts.append(f"{key}={item}")
    return ", ".join(parts)
