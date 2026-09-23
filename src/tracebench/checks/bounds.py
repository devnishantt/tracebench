from decimal import Decimal

from ..columns import ColumnSpec
from ..models import Finding
from ..values import parse_value
from .common import finding


def bound_checks(
    values: list[tuple[int, str | None]], column: ColumnSpec, sample_limit: int
) -> list[Finding]:
    result = []
    present = [(row, value) for row, value in values if value is not None]
    for lower, bound in [(True, column.minimum), (False, column.maximum)]:
        if bound is None:
            continue
        bad = []
        checked = 0
        for row, value in present:
            try:
                parsed = Decimal(str(parse_value(value, column.kind)))
            except (ValueError, ArithmeticError):
                continue  # Invalid semantic values are reported by value.type.
            checked += 1
            if (parsed < bound) if lower else (parsed > bound):
                bad.append(row)
        result.append(
            finding(
                "value.minimum" if lower else "value.maximum",
                column.name,
                bad,
                checked,
                f"Numeric values must be {'>=' if lower else '<='} {bound}",
                column.severity,
                sample_limit,
            )
        )
    for lower, length_bound in [(True, column.min_length), (False, column.max_length)]:
        if length_bound is not None:
            bad = [
                row
                for row, value in present
                if (len(value) < length_bound if lower else len(value) > length_bound)
            ]
            result.append(
                finding(
                    "value.min_length" if lower else "value.max_length",
                    column.name,
                    bad,
                    len(present),
                    f"Text length must be {'>=' if lower else '<='} {length_bound}",
                    column.severity,
                    sample_limit,
                )
            )
    return result
