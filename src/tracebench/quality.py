from .checks.allowed import allowed_check
from .checks.bounds import bound_checks
from .checks.nulls import null_checks
from .checks.patterns import pattern_check
from .checks.relations import relation_checks
from .checks.structure import row_count_checks, structure_checks
from .checks.types import type_check
from .checks.uniqueness import primary_key_checks, unique_check
from .contracts import DatasetSpec
from .dataset import Dataset
from .fingerprint import canonical_digest
from .models import QualityReport

def check(dataset: Dataset, spec: DatasetSpec) -> QualityReport:
    findings = [*structure_checks(dataset, spec), *row_count_checks(dataset, spec)]
    for column in spec.columns:
        if column.name not in dataset.source.columns:
            continue
        values = dataset.values(column.name)
        findings.extend(null_checks(values, column, spec.sample_limit))
        findings.append(type_check(values, column, spec.sample_limit))
        findings.extend(bound_checks(values, column, spec.sample_limit))
        findings.extend(allowed_check(values, column, spec.sample_limit))
        findings.extend(pattern_check(dataset, column, spec.sample_limit))
        if column.unique:
            findings.append(unique_check(values, column.name, column.severity, spec.sample_limit))
    findings.extend(primary_key_checks(dataset, spec))
    findings.extend(relation_checks(dataset, spec))
    errors = sum(f.failures > 0 and f.severity == 'error' for f in findings)
    warnings = sum(f.failures > 0 and f.severity == 'warning' for f in findings)
    report = QualityReport(source=dataset.source, contract_name=spec.name, contract_fingerprint=spec.fingerprint, findings=findings, passed=errors == 0, errors=errors, warnings=warnings)
    report.content_fingerprint = canonical_digest(report.model_dump(mode='json', exclude={'generated_at', 'content_fingerprint'}))
    return report
