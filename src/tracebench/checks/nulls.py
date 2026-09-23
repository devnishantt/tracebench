from ..columns import ColumnSpec
from ..models import Finding
from .common import finding


def null_checks(
    values: list[tuple[int, str | None]], column: ColumnSpec, sample_limit: int
) -> list[Finding]:
    nulls = [row for row, value in values if value is None]
    result = []
    if not column.nullable:
        result.append(
            finding(
                "value.null",
                column.name,
                nulls,
                len(values),
                "Null values are not allowed",
                column.severity,
                sample_limit,
            )
        )
    if column.max_null_fraction is not None:
        fraction = len(nulls) / len(values) if values else 0
        result.append(
            finding(
                "value.null_fraction",
                column.name,
                nulls if fraction > column.max_null_fraction else [],
                len(values),
                f"Null fraction must be at most {column.max_null_fraction}",
                column.severity,
                sample_limit,
            )
        )
    return result
