from pathlib import Path

import duckdb

from .errors import InputError
from .jsonl_source import scalar
from .limits import Limits, headers


def read_parquet(path: Path, limits: Limits) -> tuple[list[str], list[list[str | None]]]:
    if any(character in str(path) for character in "*?[]"):
        raise InputError("Parquet filenames cannot contain glob metacharacters")
    connection = duckdb.connect(
        config={
            "threads": 1,
            "memory_limit": "128MB",
            "autoinstall_known_extensions": "false",
            "autoload_known_extensions": "false",
        }
    )
    try:
        # A resolved local filename is bound, never interpolated or treated as a glob.
        result = connection.execute(
            "SELECT * FROM read_parquet(?) LIMIT ?", [str(path), limits.max_rows + 1]
        )
        names = headers([column[0] for column in result.description], limits)
        rows: list[list[str | None]] = []
        while values := result.fetchmany(500):
            for row in values:
                limits.shape(len(rows) + 1, len(names))
                rows.append([scalar(value, limits) for value in row])
        return names, rows
    except duckdb.Error as exc:
        raise InputError(f"Cannot read Parquet: {type(exc).__name__}") from exc
    finally:
        connection.close()
