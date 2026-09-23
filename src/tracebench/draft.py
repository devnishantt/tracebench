from typing import cast

from .columns import ColumnSpec, Kind
from .contracts import DatasetSpec
from .models import ProfileReport


def draft_contract(report: ProfileReport, name: str | None = None) -> DatasetSpec:
    columns = [
        ColumnSpec(
            name=column.name,
            kind=cast(
                Kind, "string" if column.inferred_kind == "unknown" else column.inferred_kind
            ),
            nullable=column.nulls > 0,
            unique=column.rows > 0 and column.nulls == 0 and column.distinct == column.rows,
        )
        for column in report.columns
    ]
    return DatasetSpec(
        name=name or report.source.filename.rsplit(".", 1)[0],
        columns=columns,
        min_rows=0 if report.source.rows == 0 else 1,
    )
