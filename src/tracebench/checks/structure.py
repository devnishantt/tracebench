from ..contracts import DatasetSpec
from ..dataset import Dataset
from ..models import Finding

def structure_checks(dataset: Dataset, spec: DatasetSpec) -> list[Finding]:
    observed = set(dataset.source.columns)
    declared = {column.name for column in spec.columns}
    result = []
    for column in spec.columns:
        result.append(Finding(code='column.required', column=column.name, severity=column.severity, failures=int(column.required and column.name not in observed), checked=1, message='Required column must exist' if column.required else 'Optional column may be absent'))
    if spec.extra_columns != 'allow':
        for name in sorted(observed - declared):
            result.append(Finding(code='column.unexpected', column=name, severity='warning' if spec.extra_columns == 'warn' else 'error', failures=1, checked=1, message='Column is not declared in the contract'))
    return result

def row_count_checks(dataset: Dataset, spec: DatasetSpec) -> list[Finding]:
    count = dataset.source.rows
    result = [Finding(code='rows.minimum', failures=int(count < spec.min_rows), checked=1, message=f'Row count must be at least {spec.min_rows}')]
    if spec.max_rows is not None:
        result.append(Finding(code='rows.maximum', failures=int(count > spec.max_rows), checked=1, message=f'Row count must be at most {spec.max_rows}'))
    return result
