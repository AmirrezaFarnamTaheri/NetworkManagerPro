import diagnostics
import deep_diagnostics


class FakeResponse:
    status_code = 200
    text = "Microsoft Connect Test"
    headers = {}


def test_consent_prompt_describes_scope_and_data():
    prompt = deep_diagnostics.consent_prompt("dns_integrity")

    assert prompt["schema_version"] == deep_diagnostics.SCHEMA_VERSION
    assert prompt["category"] == "external active"
    assert prompt["cancellable"] is True
    assert "local resolver answers" in prompt["data_collected"]


def test_dns_integrity_classification_and_result_schema():
    assert deep_diagnostics.classify_dns_integrity(["1.1.1.1"], ["1.1.1.1"])[0] == "normal"
    assert deep_diagnostics.classify_dns_integrity([], ["1.1.1.1"])[0] == "filtered"
    assert deep_diagnostics.classify_dns_integrity(["203.0.113.1"], ["1.1.1.1"])[0] == "mismatch"

    result = deep_diagnostics.run_dns_integrity_diagnostic(
        "example.test",
        local_resolver=lambda _domain: ["203.0.113.1"],
        trusted_resolver=lambda _domain: ["1.1.1.1"],
    )
    assert result["test_id"] == "dns_integrity"
    assert result["status"] == "mismatch"
    assert result["evidence"]["domain"] == "example.test"
    assert "recommendation" in result


def test_transparent_dns_proxy_diagnostic_reports_interception_evidence():
    assert deep_diagnostics.classify_transparent_dns_proxy(["203.0.113.10"], ["1.1.1.1"], "router dns")[0] == "possible_interception"

    result = deep_diagnostics.run_transparent_dns_proxy_diagnostic(
        "example.test",
        requested_resolver=lambda _domain: ["203.0.113.10"],
        trusted_resolver=lambda _domain: ["1.1.1.1"],
        requested_resolver_label="router dns",
    )

    assert result["test_id"] == "transparent_dns_proxy"
    assert result["status"] == "possible_interception"
    assert result["evidence"]["requested_resolver"] == "router dns"


def test_captive_portal_diagnostic_reuses_safe_classifier():
    result = deep_diagnostics.run_captive_portal_diagnostic(fetcher=lambda *args, **kwargs: FakeResponse())

    assert result["test_id"] == "captive_portal"
    assert result["status"] == "open"
    assert result["confidence"] == "medium"


def test_tls_certificate_classification_reports_issuer_evidence():
    cert = {
        "issuer": ((("organizationName", "Example CA"),),),
        "subject": ((("commonName", "example.test"),),),
        "notBefore": "Jan 1 00:00:00 2026 GMT",
        "notAfter": "Jan 1 00:00:00 2027 GMT",
    }
    status, _explanation, confidence = deep_diagnostics.classify_tls_certificate(cert, ["Example CA"])
    assert status == "normal"
    assert confidence == "low"

    result = deep_diagnostics.run_tls_inspection_diagnostic(
        "example.test",
        expected_issuer_keywords=["Other CA"],
        cert_fetcher=lambda _host: cert,
    )
    assert result["status"] == "possible_inspection"
    assert "Example CA" in result["evidence"]["issuer"]


def test_sni_filtering_diagnostic_classifies_tls_failures():
    status, explanation, confidence = deep_diagnostics.classify_sni_connection(False, error="tlsv1 alert unrecognized_name")
    assert status == "possible_sni_or_tls_filtering"
    assert confidence == "medium"
    assert "SNI" in explanation

    result = deep_diagnostics.run_sni_filtering_diagnostic(
        "example.test",
        cert_fetcher=lambda _host: (_ for _ in ()).throw(RuntimeError("tlsv1 alert unrecognized_name")),
    )
    assert result["test_id"] == "sni_filtering"
    assert result["status"] == "possible_sni_or_tls_filtering"


def test_diagnostics_summary_lists_deep_diagnostic_tests():
    summary = diagnostics.diagnostics_summary({}, None)

    assert summary["deep_diagnostics"]["schema_version"] == deep_diagnostics.SCHEMA_VERSION
    assert "dns_integrity" in summary["deep_diagnostics"]["available_tests"]
