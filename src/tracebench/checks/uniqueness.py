from collections import Counter
from ..contracts import DatasetSpec
from ..dataset import Dataset
from ..models import Finding
from ..sql import identifier
from .common import finding

def unique_check(values: list[tuple[int, str | None]], column: str, severity: str, sample_limit: int) -> Finding:
    present = [(row, value) for row, value in values if value is not None]
    counts = Counter(value for _, value in present)
    rows = [row for row, value in present if counts[value] > 1]
    return finding('value.unique', column, rows, len(present), 'All non-null values must be unique; every row in a duplicate group is counted', severity, sample_limit)

def primary_key_checks(dataset: Dataset, spec: DatasetSpec) -> list[Finding]:
    if not spec.primary_key or any(name not in dataset.source.columns for name in spec.primary_key):
        return []
    columns = ','.join(identifier(name) for name in spec.primary_key)
    rows = dataset.connection.execute(f'SELECT "__tb_row", {columns} FROM data ORDER BY "__tb_row"').fetchall()
    keys = [tuple(row[1:]) for row in rows]
    counts = Counter(key for key in keys if None not in key)
    nulls = [row[0] for row in rows if None in row[1:]]
    duplicates = [row[0] for row in rows if None not in row[1:] and counts[tuple(row[1:])] > 1]
    label = ', '.join(spec.primary_key)
    return [finding('key.null', label, nulls, len(rows), 'Primary-key fields must be non-null', limit=spec.sample_limit), finding('key.unique', label, duplicates, len(rows), 'Composite primary keys must be unique', limit=spec.sample_limit)]
