from .categories import category_summary
from .dataset import Dataset
from .errors import InputError
from .fingerprint import canonical_digest
from .inference import infer_kind
from .models import ColumnProfile, ProfileReport
from .sql import identifier
from .statistics import numeric_summary


def profile(
    dataset: Dataset, *, category_limit: int = 50, include_values: bool = False
) -> ProfileReport:
    columns = []
    for name in dataset.source.columns:
        quoted = identifier(name)
        count_row = dataset.connection.execute(
            f"SELECT COUNT({quoted}), COUNT(DISTINCT {quoted}), MIN(LENGTH({quoted})), MAX(LENGTH({quoted})) FROM data"
        ).fetchone()
        if count_row is None:
            raise InputError("Profiling query returned no aggregate")
        count, distinct, min_length, max_length = count_row
        values = [value for _, value in dataset.values(name) if value is not None]
        kind = infer_kind(values)
        categories, truncated = category_summary(
            dataset, name, limit=category_limit, include_values=include_values
        )
        nulls = dataset.source.rows - count
        columns.append(
            ColumnProfile(
                name=name,
                inferred_kind=kind,
                rows=dataset.source.rows,
                nulls=nulls,
                distinct=distinct,
                null_fraction=nulls / dataset.source.rows if dataset.source.rows else 0,
                length_min=min_length,
                length_max=max_length,
                numeric=numeric_summary(values) if kind in ("integer", "number") else None,
                categories=categories,
                categories_truncated=truncated,
            )
        )
    report = ProfileReport(source=dataset.source, columns=columns)
    payload = report.model_dump(mode="json", exclude={"generated_at", "content_fingerprint"})
    report.content_fingerprint = canonical_digest(payload)
    return report
