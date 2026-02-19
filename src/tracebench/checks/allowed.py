from ..columns import ColumnSpec
from ..models import Finding
from .common import finding

def allowed_check(values: list[tuple[int, str | None]], column: ColumnSpec, sample_limit: int) -> list[Finding]:
    if column.allowed is None:
        return []
    allowed = set(column.allowed)
    present = [(row, value) for row, value in values if value is not None]
    return [finding('value.allowed', column.name, [row for row, value in present if value not in allowed], len(present), 'Values must belong to the declared allowed set', column.severity, sample_limit)]
