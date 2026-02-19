from ..columns import ColumnSpec
from ..models import Finding
from ..values import accepts
from .common import finding

def type_check(values: list[tuple[int, str | None]], column: ColumnSpec, sample_limit: int) -> Finding:
    present = [(row, value) for row, value in values if value is not None]
    bad = [row for row, value in present if not accepts(value, column.kind)]
    return finding('value.type', column.name, bad, len(present), f'Non-null values must satisfy {column.kind}', column.severity, sample_limit)
