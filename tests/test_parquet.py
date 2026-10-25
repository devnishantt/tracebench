from decimal import Decimal

import duckdb
import pytest

from tracebench.dataset import load_dataset
from tracebench.errors import InputError
from tracebench.limits import Limits
from tracebench.profile import profile


def parquet_file(tmp_path, query, name="input.parquet"):
    path = tmp_path / name
    connection = duckdb.connect(config={"threads": 1})
    try:
        connection.execute(f"COPY ({query}) TO ? (FORMAT PARQUET)", [str(path)])
    finally:
        connection.close()
    return path


def test_parquet_scalars_preserve_decimal_boolean_and_date_text(tmp_path):
    path = parquet_file(
        tmp_path,
        "SELECT 1 AS id, 1.23::DECIMAL(10,2) AS amount, true AS active, DATE '2026-10-01' AS day",
    )
    with load_dataset(path) as data:
        assert data.source.format == "parquet"
        assert data.values("amount") == [(1, str(Decimal("1.23")))]
        assert data.values("active") == [(1, "true")]
        assert data.values("day") == [(1, "2026-10-01")]
        assert profile(data).columns[1].inferred_kind == "number"


def test_parquet_row_budget_is_checked_before_full_materialization(tmp_path):
    path = parquet_file(tmp_path, "SELECT range AS id FROM range(10)")
    with pytest.raises(InputError, match="budget"):
        load_dataset(path, limits=Limits(max_rows=3))


def test_nested_parquet_columns_are_not_silently_flattened(tmp_path):
    path = parquet_file(tmp_path, "SELECT [1,2,3] AS nested")
    with pytest.raises(InputError, match="scalar"):
        load_dataset(path)


def test_parquet_header_only_snapshots_have_zero_rows(tmp_path):
    path = parquet_file(tmp_path, "SELECT 1 AS id WHERE false")
    with load_dataset(path) as data:
        assert data.source.rows == 0
        assert profile(data).columns[0].inferred_kind == "unknown"


def test_parquet_literal_paths_cannot_expand_into_globs(tmp_path):
    path = tmp_path / "part[01].parquet"
    path.write_bytes(b"not read because the filename is rejected first")
    with pytest.raises(InputError, match="glob"):
        load_dataset(path)
