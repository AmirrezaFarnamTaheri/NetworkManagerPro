from __future__ import annotations

import statistics


def metric_baseline(rows, field):
    values = [_to_float(row.get(field)) for row in rows or [] if row.get(field) is not None]
    if not values:
        return {"field": field, "count": 0, "mean": 0.0, "stdev": 0.0}
    mean = statistics.fmean(values)
    stdev = statistics.pstdev(values) if len(values) > 1 else 0.0
    return {"field": field, "count": len(values), "mean": mean, "stdev": stdev}


def detect_spike(rows, field, latest=None, z_threshold=3.0):
    baseline_rows = list(rows or [])
    latest_value = _to_float(latest if latest is not None else (baseline_rows[-1].get(field) if baseline_rows else 0))
    baseline = metric_baseline(baseline_rows[:-1] if latest is None else baseline_rows, field)
    if baseline["count"] < 3 or baseline["stdev"] == 0:
        return {
            "status": "insufficient_baseline",
            "confidence": "low",
            "evidence": {"field": field, "latest": latest_value, "baseline": baseline},
        }
    z_score = (latest_value - baseline["mean"]) / baseline["stdev"]
    status = "spike" if z_score >= float(z_threshold) else "normal"
    return {
        "status": status,
        "confidence": "medium" if status == "spike" else "low",
        "evidence": {
            "field": field,
            "latest": latest_value,
            "mean": baseline["mean"],
            "stdev": baseline["stdev"],
            "z_score": z_score,
            "threshold": float(z_threshold),
        },
        "recommendation": "Explain the finding and ask before applying any self-healing action.",
    }


def explain_anomalies(rows):
    findings = []
    for field in ("bytes_recv", "bytes_sent", "latency_ms"):
        finding = detect_spike(rows, field)
        if finding["status"] == "spike":
            findings.append(finding)
    return findings


def _to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
