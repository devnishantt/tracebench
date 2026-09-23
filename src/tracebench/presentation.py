from typing import Any

from .artifacts import Report
from .models import DriftReport, ProfileReport


def presentation(report: Report) -> dict[str, Any]:
    if isinstance(report, ProfileReport):
        return {
            "kind": "Dataset profile",
            "title": report.source.filename,
            "status": "PROFILED",
            "status_class": "pass",
            "subtitle": "A reproducible snapshot of structure, completeness, and value distributions.",
            "metrics": [
                ("Records", report.source.rows),
                ("Columns", len(report.columns)),
                ("Missing cells", sum(c.nulls for c in report.columns)),
                ("Source bytes", report.source.bytes),
            ],
            "headers": ["Column", "Kind", "Missing", "Distinct", "Mean", "Length range"],
            "rows": [
                [
                    c.name,
                    c.inferred_kind,
                    f"{c.nulls} ({c.null_fraction:.1%})",
                    c.distinct,
                    c.numeric.get("mean") if c.numeric else "—",
                    f"{c.length_min}–{c.length_max}",
                ]
                for c in report.columns
            ],
            "source": report.source.sha256,
        }
    if isinstance(report, DriftReport):
        return {
            "kind": "Drift comparison",
            "title": "Know what changed.",
            "status": "ATTENTION" if report.drifted else "STABLE",
            "status_class": "warn" if report.drifted else "pass",
            "subtitle": "Heuristic changes in structure, volume, and distributions—not a statistical significance claim.",
            "metrics": [
                ("Metrics", len(report.metrics)),
                ("Warnings", sum(m.status == "warn" for m in report.metrics)),
                ("Incomparable", sum(m.status == "incomparable" for m in report.metrics)),
                ("Passing", sum(m.status == "pass" for m in report.metrics)),
            ],
            "headers": ["Column", "Metric", "State", "Value", "Threshold", "Interpretation"],
            "rows": [
                [
                    m.column,
                    m.metric,
                    m.status,
                    m.value if m.value is not None else "—",
                    m.threshold if m.threshold is not None else "—",
                    m.message,
                ]
                for m in report.metrics
            ],
            "source": report.baseline_fingerprint + " → " + report.candidate_fingerprint,
        }
    return {
        "kind": "Contract validation",
        "title": report.contract_name,
        "status": "PASSED" if report.passed else "FAILED",
        "status_class": "pass" if report.passed else "warn",
        "subtitle": "Explicit dataset expectations, with bounded row-number evidence and no raw failing values.",
        "metrics": [
            ("Records", report.source.rows),
            ("Checks", len(report.findings)),
            ("Failed error checks", report.errors),
            ("Failed warning checks", report.warnings),
        ],
        "headers": [
            "Rule",
            "Column",
            "Severity",
            "Failed / checked",
            "Sample record numbers",
            "Expectation",
        ],
        "rows": [
            [
                f.code,
                f.column or "Dataset",
                f.severity,
                f"{f.failures} / {f.checked}",
                ", ".join(str(row) for row in f.sample_rows) or "—",
                f.message,
            ]
            for f in report.findings
        ],
        "source": report.source.sha256,
    }
