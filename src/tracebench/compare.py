from .drift_metrics import category_distance, mean_shift
from .drift_policy import DriftPolicy
from .errors import ArtifactError
from .fingerprint import canonical_digest
from .models import DriftMetric, DriftReport, ProfileReport

def compare(baseline: ProfileReport, candidate: ProfileReport, policy: DriftPolicy | None = None) -> DriftReport:
    policy = policy or DriftPolicy()
    if baseline.tool_version != candidate.tool_version:
        raise ArtifactError('Profile tool versions differ; regenerate both with the same version')
    metrics = []
    old, new = {c.name: c for c in baseline.columns}, {c.name: c for c in candidate.columns}
    for name in sorted(old.keys() - new.keys()):
        metrics.append(DriftMetric(column=name, metric='schema.removed', status='warn', message='Baseline column is missing from candidate'))
    for name in sorted(new.keys() - old.keys()):
        metrics.append(DriftMetric(column=name, metric='schema.added', status='warn', message='Candidate introduces a new column'))
    rows = baseline.source.rows
    if rows == 0:
        metrics.append(DriftMetric(column='*', metric='volume.relative_change', status='incomparable' if candidate.source.rows else 'pass', value=0 if not candidate.source.rows else None, message='Nonempty candidates cannot be normalized by a zero-row baseline'))
    else:
        value = abs(candidate.source.rows - rows) / rows
        metrics.append(DriftMetric(column='*', metric='volume.relative_change', value=value, threshold=policy.row_count_delta, status='warn' if value > policy.row_count_delta else 'pass', message='Absolute relative change in source record count'))
    for name in sorted(old.keys() & new.keys()):
        a, b = old[name], new[name]
        if a.inferred_kind != b.inferred_kind:
            metrics.append(DriftMetric(column=name, metric='schema.kind', status='warn', message=f'Inferred kind changed from {a.inferred_kind} to {b.inferred_kind}'))
        delta = abs(a.null_fraction - b.null_fraction)
        metrics.append(DriftMetric(column=name, metric='nulls.fraction_delta', value=delta, threshold=policy.null_fraction_delta, status='warn' if delta > policy.null_fraction_delta else 'pass', message='Absolute missing-value fraction difference'))
        numeric = {'integer', 'number'}
        if a.inferred_kind in numeric and b.inferred_kind in numeric:
            metrics.append(mean_shift(a, b, policy.mean_shift))
        elif a.inferred_kind == b.inferred_kind:
            metrics.append(category_distance(a, b, policy.category_distance))
        else:
            metrics.append(DriftMetric(column=name, metric='distribution', status='incomparable', message='Different semantic kinds cannot be compared as one distribution'))
    drifted = any(m.status == 'warn' or (m.status == 'incomparable' and policy.fail_on_incomparable) for m in metrics)
    report = DriftReport(baseline_fingerprint=baseline.content_fingerprint, candidate_fingerprint=candidate.content_fingerprint, metrics=metrics, drifted=drifted)
    report.content_fingerprint = canonical_digest(report.model_dump(mode='json', exclude={'generated_at', 'content_fingerprint'}))
    return report
